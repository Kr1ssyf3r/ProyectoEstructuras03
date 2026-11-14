import os

from models.historia import Historia
from repositories.historiaRepository import HistoriaRepository

#el service coordina el modelo, el repositorio y el multimedia, y aplica la regla de visibilidad:
#una historia la ve su autor o un amigo del autor, siempre que siga vigente y no haya bloqueo entre ambos.
#solo LEE de usuario_service y amistad_service, nunca los modifica.
#la visibilidad se calcula en cada consulta y no se guarda en la historia, asi si alguien elimina una
#amistad o bloquea, deja de ver esas historias al instante

class HistoriaService:
    def __init__(self, usuario_service, amistad_service, multimedia_service, repositorio=None):
        self.usuario_service = usuario_service
        self.amistad_service = amistad_service
        self.multimedia_service = multimedia_service
        self.repositorio = repositorio or HistoriaRepository()

        #diccionario 1: id de la historia -> objeto Historia
        self.historias_por_id = {}

        #diccionario 2: id del autor -> set con los ids de SUS historias
        self.ids_por_autor = {}

        for historia in self.repositorio.cargar():
            self._indexar(historia)

    # ---------------------------------------
    # METODOS INTERNOS
    # ---------------------------------------
    def _indexar(self, historia):
        self.historias_por_id[historia.id] = historia
        self.ids_por_autor.setdefault(historia.autor_id, set()).add(historia.id)

    def _desindexar(self, historia):
        self.historias_por_id.pop(historia.id, None)
        self.ids_por_autor.get(historia.autor_id, set()).discard(historia.id)

    def _guardar(self):
        self.repositorio.guardar(list(self.historias_por_id.values()))

    def _ids_amigos(self, id_usuario):
        """Set con los ids de los amigos del usuario."""
        #obtener_amigos devuelve objetos Usuario, aqui solo interesan los ids
        return {amigo.id for amigo in self.amistad_service.obtener_amigos(id_usuario)}

    def obtener_historia(self, id_historia):
        return self.historias_por_id.get(id_historia)

    def obtener_por_archivo(self, nombre_archivo):
        """Busca la historia a la que pertenece un archivo."""
        #recorre todas, para un proyecto de este tamano es suficiente
        for historia in self.historias_por_id.values():
            if historia.archivo == nombre_archivo:
                return historia

        return None
    # ---------------------------------------
    # VISIBILIDAD
    # ---------------------------------------
    def puede_ver(self, id_usuario, historia, ids_amigos=None, ahora=None):
        """Regla unica de visibilidad, la usan la lista y la ruta que sirve el archivo."""

        #1) debe seguir vigente
        if not historia.esta_vigente(ahora):
            return False

        #2) el autor siempre ve sus propias historias
        if historia.autor_id == id_usuario:
            return True

        #3) si hay bloqueo en cualquier direccion no se ve
        if self.amistad_service.hay_bloqueo_entre(id_usuario, historia.autor_id):
            return False

        #4) solo los amigos del autor la ven. ids_amigos se puede pasar ya calculado
        #para no consultar el grafo una vez por cada historia
        if ids_amigos is None:
            ids_amigos = self._ids_amigos(id_usuario)

        return historia.autor_id in ids_amigos

    def historias_visibles(self, id_usuario, ahora=None):
        """Historias que el usuario puede ver, agrupadas por autor.

        Devuelve una lista de {"autor": Usuario, "historias": [Historia]}:
        primero el propio usuario y luego sus amigos, con la historia mas reciente primero.
        """

        #---------- PASO 1: quienes pueden ser autores visibles ----------

        #set con los ids de los amigos. Se calcula UNA sola vez aqui y se reutiliza abajo,
        #para no preguntarle al grafo por cada historia
        ids_amigos = self._ids_amigos(id_usuario)

        #lista donde se van acumulando los grupos: uno por cada autor que tenga historias visibles
        grupos = []

        #---------- PASO 2: revisar autor por autor ----------

        #los autores posibles son el propio usuario mas sus amigos. El * expande el set de amigos
        #en elementos sueltos, asi queda un solo set: {yo, amigo1, amigo2, ...}
        for id_autor in {id_usuario, *ids_amigos}:

            #se convierte el id en un objeto Usuario para poder mostrar su nombre en la barra de historias
            autor = self.usuario_service.obtener_usuario(id_autor)

            #cuenta borrada: el id sigue en el grafo pero el usuario ya no existe, se ignora
            if autor is None:
                continue

            #lista por comprension: se queda solo con las historias de este autor que pasan puede_ver.
            #ids_por_autor.get(id_autor, set()) devuelve el set de ids de sus historias, o un set vacio
            #si nunca ha publicado (asi el for no falla)
            historias = [
                self.historias_por_id[i]
                for i in self.ids_por_autor.get(id_autor, set())
                if self.puede_ver(id_usuario, self.historias_por_id[i], ids_amigos, ahora)
            ]

            #si ninguna paso el filtro (todas vencidas, por ejemplo) este autor no aparece en la barra
            if not historias:
                continue

            #dentro de un autor se ordenan de la mas vieja a la mas nueva, como en un visor de historias
            historias.sort(key=lambda h: h.fecha_creacion)

            #se agrega el grupo de este autor
            grupos.append({"autor": autor, "historias": historias})

        #---------- PASO 3: ordenar los grupos ----------

        #sort con una tupla como clave: Python compara primero el elemento 1 y solo si empatan, el 2.
        #1) g["autor"].id != id_usuario  -> False (0) para el propio usuario, True (1) para los demas,
        #   asi el propio usuario queda primero
        #2) -timestamp de la historia mas nueva del grupo (historias[-1], porque estan de vieja a nueva).
        #   El signo menos invierte el orden: la que tiene el numero mas grande (mas reciente) queda primero
        grupos.sort(key=lambda g: (
            g["autor"].id != id_usuario,
            -g["historias"][-1].fecha_creacion.timestamp()
        ))

        return grupos

    # ---------------------------------------
    # CREAR Y ELIMINAR
    # ---------------------------------------
    def crear_historia(self, autor_id, archivo):
        """Guarda el archivo y registra la historia."""

        if self.usuario_service.obtener_usuario(autor_id) is None:
            raise ValueError("El usuario no existe.")

        #a diferencia de una publicacion, una historia no puede ir sin archivo
        if archivo is None or not archivo.filename:
            raise ValueError("La historia necesita una foto o un video.")

        #MultimediaService valida formato y tamano, y lanza ValueError si algo no cumple
        nombre_archivo, tipo_archivo = self.multimedia_service.guardar_archivo(archivo)#aqui se le pasa los bytes reales de un archivo , foto o video , y el metodo valida y guarda en la carpeta de medios y devuelve el nombre del archivo guardado y su tipo ("imagen" o "video")

        historia = Historia(autor_id, nombre_archivo, tipo_archivo)#nombre del archivo generado por uuid y tipo de archivo ("imagen" o "video")

        self._indexar(historia)#se agrega la historia a los diccionarios internos para poder buscarla por id y por autor

        try:
            self._guardar()
        except Exception:
            #si falla el guardado no debe quedar ni la historia ni un archivo huerfano
            self._desindexar(historia)
            self.multimedia_service.eliminar_archivo(nombre_archivo)
            raise

        return historia

    def eliminar_historia(self, id_historia, id_usuario):
        """Solo el autor puede borrar su historia."""

        historia = self.obtener_historia(id_historia)

        if historia is None:
            raise ValueError("La historia no existe.")

        if historia.autor_id != id_usuario:
            raise ValueError("Solo puedes eliminar tus propias historias.")

        self._desindexar(historia)

        try:
            self._guardar()
        except Exception:
            self._indexar(historia)
            raise

        #el archivo se borra al final, cuando ya se confirmo que el JSON quedo guardado
        self.multimedia_service.eliminar_archivo(historia.archivo)

        return True