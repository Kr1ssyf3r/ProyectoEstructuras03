from models.grafoAmistades import GrafoAmistades
# ---------------------------------------
# APARTADO DE BLOQUEOS
# ---------------------------------------
from models.gestorBloqueos import GestorBloqueos
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

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
        #se agrega una tercera estructura, el diccionario de sets que guarda a quien bloqueo cada usuario
        self.bloqueos = GestorBloqueos()

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

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
        #se recuperan los bloqueos guardados, si el json es viejo se utiliza un diccionario vacio
        bloqueos = GestorBloqueos.desde_datos(datos.get("bloqueos", {}))

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

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
        #se recorren los bloqueos guardados para quitar referencias a usuarios que ya no existen
        #y tambien corregir amistades o solicitudes que no deberian existir entre usuarios bloqueados
        for emisor, receptores in bloqueos.exportar().items():
            for receptor in receptores:
                if emisor not in ids_validos or receptor not in ids_validos:
                    bloqueos.desbloquear(emisor, receptor)
                    hubo_limpieza = True
                    continue

                #si dos usuarios estan bloqueados no pueden seguir siendo amigos
                if grafo.eliminar_amistad(emisor, receptor):
                    hubo_limpieza = True

                #tampoco pueden mantener solicitudes pendientes en ninguna direccion
                for solicitud in gestor.listar():
                    if {solicitud.id_emisor, solicitud.id_receptor} == {emisor, receptor}:
                        gestor.eliminar_solicitud(solicitud.id_solicitud)
                        hubo_limpieza = True

        # Incorporar los usuarios que todavía no tienen amigos.
        for id_usuario in ids_validos:
            grafo.agregar_usuario(id_usuario)

        self.grafo = grafo
        self.gestor = gestor

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
        self.bloqueos = bloqueos

        #(CAMBIO) si se limpio algo, se guarda el resultado para que el archivo quede consistente
        if hubo_limpieza:
            self.repositorio.guardar(
                self.grafo.exportar(),
                self.gestor.exportar(),
                self.bloqueos.exportar()
            )

    #(CAMBIO) se invirtio la logica. Antes se ejecutaba la accion sobre self.grafo y, si fallaba, se restauraba una copia,
    #lo que dejaba el estado vivo a medias durante la ejecucion. Ahora la accion trabaja sobre COPIAS (recibe grafo y gestor
    #como parametros), se guarda en disco, y solo si todo salio bien se reemplaza el estado real.
    #si algo falla no hay nada que revertir porque self.grafo y self.gestor nunca se tocaron
    def _aplicar_y_guardar(self, accion):
        """Aplica la accion sobre copias y solo confirma si el guardado funciona."""

        grafo = GrafoAmistades.desde_datos(self.grafo.exportar())
        gestor = GestorSolicitudes.desde_datos(self.gestor.exportar())

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
        #se hace una copia tambien de los bloqueos, para no alterar los datos reales si falla el guardado
        bloqueos = GestorBloqueos.desde_datos(self.bloqueos.exportar())

        #ahora todas las acciones reciben tres estructuras, incluso cuando solo modifican una
        resultado = accion(grafo, gestor, bloqueos)

        self.repositorio.guardar(
            grafo.exportar(),
            gestor.exportar(),
            bloqueos.exportar()
        )

        self.grafo = grafo
        self.gestor = gestor

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
        #el gestor de bloqueos real se actualiza solo despues de guardar bien el JSON
        self.bloqueos = bloqueos

        return resultado

    def enviar_solicitud(self, id_emisor, id_receptor):
        """Envía una solicitud de amistad."""

        self._exigir_usuario(id_emisor)
        self._exigir_usuario(id_receptor)

        if id_emisor == id_receptor:
            raise ValueError(
                "No podés enviarte solicitudes a vos mismo."
            )

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
        #si cualquiera de los dos bloqueo al otro, no se permite una nueva solicitud
        if self.bloqueos.existe_bloqueo_entre(id_emisor, id_receptor):
            raise ValueError("No se puede enviar esta solicitud.")

        if self.grafo.son_amigos(id_emisor, id_receptor):
            raise ValueError("Ya son amigos.")

        #existe_solicitud no distingue el orden (frozenset), asi que tambien cubre el caso B->A
        if self.gestor.existe_solicitud(id_emisor, id_receptor):
            raise ValueError(
                "Ya existe una solicitud pendiente entre ambos."
            )

        def accion(grafo, gestor, bloqueos):
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

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
        #se verifica tambien al aceptar por si existiera alguna solicitud antigua incompatible
        if self.bloqueos.existe_bloqueo_entre(solicitud.id_emisor, id_receptor):
            raise ValueError("No se puede aceptar esta solicitud.")

        def accion(grafo, gestor, bloqueos):
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
                lambda grafo, gestor, bloqueos: gestor.eliminar_solicitud(id_solicitud)
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
                lambda grafo, gestor, bloqueos: gestor.eliminar_solicitud(id_solicitud)
            )
        )

    def eliminar_amistad(self, id_usuario, id_amigo):
        """Elimina una relación de amistad."""

        self._exigir_usuario(id_usuario)
        self._exigir_usuario(id_amigo)

        if not self.grafo.son_amigos(id_usuario, id_amigo):
            raise ValueError("No existe esta amistad.")

        return self._aplicar_y_guardar(
            lambda grafo, gestor, bloqueos: grafo.eliminar_amistad(id_usuario, id_amigo)
        )

    #(CAMBIO) metodo nuevo que reemplaza la parte de estado de buscar_estudiantes.
    #quien arme la busqueda (controlador o UsuarioService) filtra los usuarios por nombre
    #y le pregunta a este metodo en que estado esta cada resultado respecto al usuario actual
    def estado_entre(self, id1, id2):
        """Devuelve 'amigos', 'pendiente' o 'disponible' entre dos usuarios."""

        self._exigir_usuario(id1)
        self._exigir_usuario(id2)

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
        #se consulta primero el bloqueo para no presentar la opcion de agregar amigo
        if self.bloqueos.existe_bloqueo_entre(id1, id2):
            return "bloqueado"

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

        def accion(grafo, gestor, bloqueos):
            eliminado = grafo.eliminar_usuario(id_usuario)
            gestor.eliminar_solicitudes_usuario(id_usuario)
        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
            #al borrar una cuenta se quitan tanto los bloqueos que hizo como los que recibio
            bloqueos.eliminar_usuario(id_usuario)
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

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
        #si existe un bloqueo entre ambos, no se muestran sus conexiones compartidas
        if self.bloqueos.existe_bloqueo_entre(id1, id2):
            return []

        return self._a_usuarios(
            sorted(self.grafo.amigos_en_comun(id1, id2))
        )

    def recomendaciones(self, id_usuario, limite=10):
        """Recomienda estudiantes según amigos en común."""

        self._exigir_usuario(id_usuario)

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
        #se valida el limite antes de buscar candidatos, asi nunca se devuelve mas de lo solicitado
        if limite < 0:
            raise ValueError("El límite no puede ser negativo.")
        if limite == 0:
            return []

        if not self.grafo.existe_usuario(id_usuario):
            return []

        resultado = []

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------
        #se piden todos los candidatos del grafo y se filtran despues, porque si pedimos solo 10
        #y esos 10 estan bloqueados o tienen solicitudes pendientes perderiamos recomendaciones validas
        cantidad_candidatos = len(self.grafo.exportar())
        for id_candidato, puntuacion in self.grafo.recomendar_amigos(
            id_usuario,
            cantidad_candidatos
        ):
            # ---------------------------------------
            # APARTADO DE BLOQUEOS
            # ---------------------------------------
            #no se muestra en recomendaciones a alguien que nos bloqueo o a quien bloqueamos
            if self.bloqueos.existe_bloqueo_entre(id_usuario, id_candidato):
                continue

            #no se recomienda a quien ya tiene una solicitud pendiente
            if self.gestor.existe_solicitud(id_usuario, id_candidato):
                continue

            candidato = self.usuario_service.obtener_usuario(id_candidato)

            #(CAMBIO) se descartan los candidatos que ya no existen en usuario_service
            if candidato is not None:
                resultado.append((candidato, puntuacion))

            # ---------------------------------------
            # APARTADO DE BLOQUEOS
            # ---------------------------------------
            #cuando completamos el limite se deja de buscar, para no devolver candidatos de mas
            if len(resultado) >= limite:
                break

        return resultado

    # ---------------------------------------
    # APARTADO DE BLOQUEOS
    # ---------------------------------------
    def bloquear_usuario(self, id_usuario, id_bloqueado):
        """Bloquea al estudiante, elimina la amistad y las solicitudes pendientes."""
        #primero se comprueba que ambos usuarios existan en el sistema
        self._exigir_usuario(id_usuario)
        self._exigir_usuario(id_bloqueado)

        #no se puede bloquear uno mismo ni registrar dos veces el mismo bloqueo
        if id_usuario == id_bloqueado:
            raise ValueError("No podés bloquearte a vos mismo.")
        if self.bloqueos.ha_bloqueado(id_usuario, id_bloqueado):
            raise ValueError("Ya bloqueaste a este usuario.")

        def accion(grafo, gestor, bloqueos):
            #se registra el bloqueo en la copia, todavia no modifica el estado real
            bloqueos.bloquear(id_usuario, id_bloqueado)

            #si eran amigos se elimina la amistad bidireccional del grafo
            grafo.eliminar_amistad(id_usuario, id_bloqueado)

            #se eliminan las solicitudes que tengan entre ambos, no importa quien las envio
            for solicitud in gestor.listar():
                if {solicitud.id_emisor, solicitud.id_receptor} == {id_usuario, id_bloqueado}:
                    gestor.eliminar_solicitud(solicitud.id_solicitud)

            return True

        #se guardan las tres estructuras al mismo tiempo usando el metodo que ya teniamos
        return self._aplicar_y_guardar(accion)

    # ---------------------------------------
    # APARTADO DE BLOQUEOS
    # ---------------------------------------
    def desbloquear_usuario(self, id_usuario, id_bloqueado):
        """Elimina un bloqueo, sin restaurar la amistad anterior."""
        self._exigir_usuario(id_usuario)
        self._exigir_usuario(id_bloqueado)

        #solo el usuario que hizo el bloqueo puede quitarlo
        if not self.bloqueos.ha_bloqueado(id_usuario, id_bloqueado):
            raise ValueError("No bloqueaste a este usuario.")

        #desbloquear no vuelve a agregar la amistad, solo elimina el bloqueo del set
        return self._aplicar_y_guardar(
            lambda grafo, gestor, bloqueos: bloqueos.desbloquear(id_usuario, id_bloqueado)
        )

    # ---------------------------------------
    # APARTADO DE BLOQUEOS
    # ---------------------------------------
    def obtener_usuarios_bloqueados(self, id_usuario):
        """Devuelve los objetos Usuario de las cuentas que bloqueó el estudiante."""
        self._exigir_usuario(id_usuario)

        #el gestor devuelve ids y aqui se convierten a objetos Usuario para mostrar sus nombres
        return sorted(
            self._a_usuarios(self.bloqueos.obtener_bloqueados(id_usuario)),
            key=lambda usuario: (usuario.nombre.casefold(), usuario.id)
        )

    # ---------------------------------------
    # APARTADO DE BLOQUEOS
    # ---------------------------------------
    def ha_bloqueado(self, id_usuario, id_otro):
        """Consulta si el primer usuario bloqueo al segundo, sin revisar la direccion contraria."""
        self._exigir_usuario(id_usuario)
        self._exigir_usuario(id_otro)

        #a diferencia de existe_bloqueo_entre, aqui importa quien realizo el bloqueo
        return self.bloqueos.ha_bloqueado(id_usuario, id_otro)
