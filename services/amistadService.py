from models.grafoAmistades import GrafoAmistades
from models.gestorSolicitudes import GestorSolicitudes
from models.solicitudAmistad import SolicitudAmistad
from repositories.amistadRepository import AmistadRepository

#(CAMBIO) el service solo coordina el grafo, el gestor y el repository, y aplica las reglas que ninguno de los tres puede garantizar solo
#(que el usuario exista, que no se mande solicitud entre amigos, quien puede aceptar/rechazar/cancelar y que todo se guarde de forma atomica).
#ya no hace busquedas de usuarios (buscar_estudiantes se saco, eso le toca a UsuarioService o al controlador)
#solo LEE de usuario_service (listar_usuarios y obtener_usuario), nunca lo modifica, y usuario_service no debe conocer a este service

class AmistadService:
    def __init__(self, usuario_service, repositorio=None):
        self.usuario_service = usuario_service

        self.repositorio = (
            repositorio
            if repositorio is not None
            else AmistadRepository()
        )

        self.grafo = GrafoAmistades()
        self.gestor = GestorSolicitudes()

        self.inicializar_red()

    def _usuarios(self):
        """Obtiene todos los usuarios registrados."""
        return self.usuario_service.listar_usuarios()

    def _exigir_usuario(self, id_usuario):
        if self.usuario_service.obtener_usuario(id_usuario) is None:
            raise ValueError("El estudiante no existe.")

    #(CAMBIO) helper nuevo, antes aceptar, rechazar y cancelar repetian el mismo bloque para buscar la solicitud
    def _exigir_solicitud(self, id_solicitud):
        solicitud = self.gestor.buscar_solicitud(id_solicitud)

        if solicitud is None:
            raise ValueError("La solicitud ya no existe.")

        return solicitud

    #(CAMBIO) helper nuevo, convierte ids en objetos Usuario y descarta los None
    #(un id que ya no existe en usuario_service), asi las consultas nunca devuelven None en la lista
    def _a_usuarios(self, ids):
        usuarios = (self.usuario_service.obtener_usuario(i) for i in ids)
        return [u for u in usuarios if u is not None]

    def inicializar_red(self):
        """Reconstruye las amistades y solicitudes guardadas."""
        datos = self.repositorio.cargar()

        grafo = GrafoAmistades.desde_datos(datos["amistades"])
        gestor = GestorSolicitudes.desde_datos(datos["solicitudes"])

        ids_validos = {u.id for u in self._usuarios()}
        hubo_limpieza = False

        #(CAMBIO) antes si el JSON mencionaba a un usuario que ya no existe se lanzaba ValueError y la app no arrancaba.
        #usuarios y relaciones viven en archivos distintos y no se pueden escribir juntos de forma atomica,
        #asi que ahora se limpian los huerfanos y se sigue. Primero las amistades de usuarios inexistentes
        for id_usuario in set(grafo.exportar()) - ids_validos:
            grafo.eliminar_usuario(id_usuario)
            hubo_limpieza = True

        #(CAMBIO) ahora se usa gestor.listar() en vez de gestor._solicitudes (atributo privado).
        #se elimina toda solicitud con un usuario inexistente o entre usuarios que ya son amigos
        for solicitud in gestor.listar():
            if (
                solicitud.id_emisor not in ids_validos
                or solicitud.id_receptor not in ids_validos
                or grafo.son_amigos(solicitud.id_emisor, solicitud.id_receptor)
            ):
                gestor.eliminar_solicitud(solicitud.id_solicitud)
                hubo_limpieza = True

        # Incorporar los usuarios que todavía no tienen amigos.
        for id_usuario in ids_validos:
            grafo.agregar_usuario(id_usuario)

        self.grafo = grafo
        self.gestor = gestor

        #(CAMBIO) si se limpio algo, se guarda el resultado para que el archivo quede consistente
        if hubo_limpieza:
            self.repositorio.guardar(
                self.grafo.exportar(),
                self.gestor.exportar()
            )

    #(CAMBIO) se invirtio la logica. Antes se ejecutaba la accion sobre self.grafo y, si fallaba, se restauraba una copia,
    #lo que dejaba el estado vivo a medias durante la ejecucion. Ahora la accion trabaja sobre COPIAS (recibe grafo y gestor
    #como parametros), se guarda en disco, y solo si todo salio bien se reemplaza el estado real.
    #si algo falla no hay nada que revertir porque self.grafo y self.gestor nunca se tocaron
    def _aplicar_y_guardar(self, accion):
        """Aplica la accion sobre copias y solo confirma si el guardado funciona."""

        grafo = GrafoAmistades.desde_datos(self.grafo.exportar())
        gestor = GestorSolicitudes.desde_datos(self.gestor.exportar())

        resultado = accion(grafo, gestor)

        self.repositorio.guardar(
            grafo.exportar(),
            gestor.exportar()
        )

        self.grafo = grafo
        self.gestor = gestor

        return resultado

    def enviar_solicitud(self, id_emisor, id_receptor):
        """Envía una solicitud de amistad."""

        self._exigir_usuario(id_emisor)
        self._exigir_usuario(id_receptor)

        if id_emisor == id_receptor:
            raise ValueError(
                "No podés enviarte solicitudes a vos mismo."
            )

        if self.grafo.son_amigos(id_emisor, id_receptor):
            raise ValueError("Ya son amigos.")

        #existe_solicitud no distingue el orden (frozenset), asi que tambien cubre el caso B->A
        if self.gestor.existe_solicitud(id_emisor, id_receptor):
            raise ValueError(
                "Ya existe una solicitud pendiente entre ambos."
            )

        def accion(grafo, gestor):
            #(CAMBIO) se agregan al grafo por demanda, asi no hace falta que alguien avise cuando se registra un usuario nuevo
            grafo.agregar_usuario(id_emisor)
            grafo.agregar_usuario(id_receptor)

            solicitud = SolicitudAmistad(
                id_emisor=id_emisor,
                id_receptor=id_receptor
            )

            gestor.agregar_solicitud(solicitud)

            return solicitud

        return self._aplicar_y_guardar(accion)

    def aceptar_solicitud(self, id_solicitud, id_receptor):
        """Acepta una solicitud y crea una amistad bidireccional."""

        solicitud = self._exigir_solicitud(id_solicitud)

        if solicitud.id_receptor != id_receptor:
            raise PermissionError(
                "Solo el destinatario puede aceptar."
            )

        self._exigir_usuario(solicitud.id_emisor)
        self._exigir_usuario(id_receptor)

        def accion(grafo, gestor):
            grafo.agregar_usuario(solicitud.id_emisor)
            grafo.agregar_usuario(solicitud.id_receptor)

            grafo.agregar_amistad(
                solicitud.id_emisor,
                solicitud.id_receptor
            )

            gestor.eliminar_solicitud(id_solicitud)
            return True

        return self._aplicar_y_guardar(accion)

    def rechazar_solicitud(self, id_solicitud, id_receptor):
        """Rechaza una solicitud pendiente."""

        solicitud = self._exigir_solicitud(id_solicitud)

        if solicitud.id_receptor != id_receptor:
            raise PermissionError(
                "Solo el destinatario puede rechazar."
            )

        return bool(
            self._aplicar_y_guardar(
                lambda grafo, gestor: gestor.eliminar_solicitud(id_solicitud)
            )
        )

    def cancelar_solicitud(self, id_solicitud, id_emisor):
        """Cancela una solicitud enviada."""

        solicitud = self._exigir_solicitud(id_solicitud)

        if solicitud.id_emisor != id_emisor:
            raise PermissionError(
                "Solo el emisor puede cancelar."
            )

        return bool(
            self._aplicar_y_guardar(
                lambda grafo, gestor: gestor.eliminar_solicitud(id_solicitud)
            )
        )

    def eliminar_amistad(self, id_usuario, id_amigo):
        """Elimina una relación de amistad."""

        self._exigir_usuario(id_usuario)
        self._exigir_usuario(id_amigo)

        if not self.grafo.son_amigos(id_usuario, id_amigo):
            raise ValueError("No existe esta amistad.")

        return self._aplicar_y_guardar(
            lambda grafo, gestor: grafo.eliminar_amistad(id_usuario, id_amigo)
        )

    #(CAMBIO) metodo nuevo que reemplaza la parte de estado de buscar_estudiantes.
    #quien arme la busqueda (controlador o UsuarioService) filtra los usuarios por nombre
    #y le pregunta a este metodo en que estado esta cada resultado respecto al usuario actual
    def estado_entre(self, id1, id2):
        """Devuelve 'amigos', 'pendiente' o 'disponible' entre dos usuarios."""

        self._exigir_usuario(id1)
        self._exigir_usuario(id2)

        if self.grafo.son_amigos(id1, id2):
            return "amigos"

        if self.gestor.existe_solicitud(id1, id2):
            return "pendiente"

        return "disponible"

    #(CAMBIO) ya no exige que el usuario exista en usuario_service, porque se llama justo cuando el usuario se esta borrando.
    #el orden correcto desde la capa superior es: primero este metodo y despues borrar el usuario en UsuarioService,
    #asi lo peor que puede pasar si algo falla es un usuario sin amistades, y no amistades apuntando a alguien inexistente
    def eliminar_usuario_de_red(self, id_usuario):
        """Elimina vértice, amistades y solicitudes de un usuario."""

        def accion(grafo, gestor):
            eliminado = grafo.eliminar_usuario(id_usuario)
            gestor.eliminar_solicitudes_usuario(id_usuario)
            return eliminado

        return self._aplicar_y_guardar(accion)

    def obtener_amigos(self, id_usuario):
        """Devuelve los objetos Usuario de los amigos."""

        self._exigir_usuario(id_usuario)

        if not self.grafo.existe_usuario(id_usuario):
            return []

        return self._a_usuarios(
            sorted(self.grafo.obtener_amigos(id_usuario))
        )

    def obtener_solicitudes_recibidas(self, id_usuario):
        """Consulta las solicitudes recibidas."""

        self._exigir_usuario(id_usuario)

        return self.gestor.obtener_recibidas(id_usuario)

    def obtener_solicitudes_enviadas(self, id_usuario):
        """Consulta las solicitudes enviadas."""

        self._exigir_usuario(id_usuario)

        return self.gestor.obtener_enviadas(id_usuario)

    def amigos_en_comun(self, id1, id2):
        """Obtiene los estudiantes amigos de ambos usuarios."""

        self._exigir_usuario(id1)
        self._exigir_usuario(id2)

        if (
            not self.grafo.existe_usuario(id1)
            or not self.grafo.existe_usuario(id2)
        ):
            return []

        return self._a_usuarios(
            sorted(self.grafo.amigos_en_comun(id1, id2))
        )

    def recomendaciones(self, id_usuario, limite=10):
        """Recomienda estudiantes según amigos en común."""

        self._exigir_usuario(id_usuario)

        if not self.grafo.existe_usuario(id_usuario):
            return []

        resultado = []

        for id_candidato, puntuacion in self.grafo.recomendar_amigos(
            id_usuario,
            limite
        ):
            #no se recomienda a quien ya tiene una solicitud pendiente
            if self.gestor.existe_solicitud(id_usuario, id_candidato):
                continue

            candidato = self.usuario_service.obtener_usuario(id_candidato)

            #(CAMBIO) se descartan los candidatos que ya no existen en usuario_service
            if candidato is not None:
                resultado.append((candidato, puntuacion))

        return resultado