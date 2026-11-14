
import re
import unicodedata
import uuid

from models.publicacion import Publicacion
from repositories.publicacion_repository import PublicacionRepository

#se agrega el servicio de multimedia encargado de manejar los archivos multimedia (imágenes y videos) para centralizar la lógica de manejo de archivos y evitar duplicación de código.
from services.multimediaService import MultimediaService

MAX_LONGITUD = 500   # máximo de caracteres por publicación

# Palabras que no se permiten (en minúscula y sin tildes). Agregá las que quieran.
PALABRAS_PROHIBIDAS = {"idiota", "estupido", "imbecil"}


def _sin_tildes(texto):
    # "estúpido" -> "estupido", para comparar sin importar las tildes
    normal = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normal if unicodedata.category(c) != "Mn")


class PublicacionService:
    def __init__(self,usuario_service,repositorio=None,carpeta_media="data/uploads",multimedia_service=None):
        self.usuario_service = usuario_service
        self.repositorio = repositorio or PublicacionRepository()

        # Se utiliza MultimediaService para centralizar el manejo de imágenes y videos.
        # Si no se recibe una instancia, se crea una con la carpeta indicada.
        # Esto permite que otros servicios, como HistoriaService, reutilicen esta lógica.
        self.multimedia_service = multimedia_service or MultimediaService(
            carpeta_media=carpeta_media
        )

        # Diccionario 1: id de la publicación -> objeto Publicacion completo
        self.publicaciones_por_id = {}

        # Diccionario 2: id del usuario -> set con los ids de SUS publicaciones
        self.ids_por_usuario = {}

        for p in self.repositorio.cargar():
            self._indexar(p)

    # ---------- Reglas internas ----------

    def _indexar(self, publicacion):
        # Anota la publicación en los dos diccionarios
        self.publicaciones_por_id[publicacion.id] = publicacion
        self.ids_por_usuario.setdefault(publicacion.autor_id, set()).add(publicacion.id)

    def _validar_contenido(self, contenido, permitir_vacio=False):
        # Quita espacios sobrantes y revisa las reglas.
        # permitir_vacio=True se usa cuando la publicación lleva foto o video.
        contenido = (contenido or "").strip()
        
        if not contenido:
            if permitir_vacio:
                return ""
            raise ValueError("La publicación no puede estar vacía.")

        if len(contenido) > MAX_LONGITUD:
            raise ValueError(f"La publicación no puede superar {MAX_LONGITUD} caracteres.")

        # Evita código malicioso (XSS): no se permiten etiquetas HTML como <script>
        if re.search(r"<\s*/?\s*[a-zA-Z!]", contenido):
            raise ValueError("La publicación no puede contener etiquetas HTML.")

        # Palabras inapropiadas
        palabras = re.findall(r"\w+", _sin_tildes(contenido.casefold()))

        if any(palabra in PALABRAS_PROHIBIDAS for palabra in palabras):
            raise ValueError("La publicación contiene palabras inapropiadas.")

        return contenido

    def _guardar(self):
        # Se llama después de cada cambio para que nada se pierda al cerrar
        self.repositorio.guardar(list(self.publicaciones_por_id.values()))

    def obtener_publicacion(self, id_publicacion):
        # Devuelve la publicación con ese id, o None si no existe (búsqueda directa)
        return self.publicaciones_por_id.get(id_publicacion)

    # ---------- Métodos que usan las pantallas y los demás módulos ----------

    def crear_publicacion(self, autor_id, contenido, archivo=None):
        # Primero comprobamos que el usuario exista de verdad
        if self.usuario_service.obtener_usuario(autor_id) is None:
            raise ValueError("El usuario no existe.")

        # El texto puede ir vacío solo si se sube una foto o video
        tiene_archivo = archivo is not None and bool(archivo.filename)

        contenido = self._validar_contenido(
            contenido,
            permitir_vacio=tiene_archivo
        )

        # Si hay foto o video, MultimediaService se encarga de validarlo y guardarlo.
        # De esta forma no repetimos la lógica de manejo de archivos en otros servicios.
        nombre_archivo, tipo_archivo = self.multimedia_service.guardar_archivo(
            archivo
        )

        # uuid4 genera un id único que nunca se repite, aunque se borren publicaciones
        nueva = Publicacion(
            str(uuid.uuid4()),
            autor_id,
            contenido,
            archivo=nombre_archivo,
            tipo_archivo=tipo_archivo
        )

        self._indexar(nueva)
        self._guardar()

        return nueva

    def obtener_publicaciones_usuario(self, autor_id):
        # Con el diccionario 2 sacamos los ids de ese usuario sin recorrer todo
        ids = self.ids_por_usuario.get(autor_id, set())

        propias = [self.publicaciones_por_id[i] for i in ids]

        # Ordena de la más reciente a la más antigua
        return sorted(propias, key=lambda p: p.fecha, reverse=True)

    def editar_publicacion(self, id_publicacion, usuario_id, nuevo_contenido):
        publicacion = self.obtener_publicacion(id_publicacion)

        if publicacion is None:
            raise ValueError("La publicación no existe.")

        if publicacion.autor_id != usuario_id:
            raise ValueError("Solo puedes editar tus propias publicaciones.")

        publicacion.contenido = self._validar_contenido(
            nuevo_contenido,
            permitir_vacio=bool(publicacion.archivo)
        )

        self._guardar()

        return publicacion

    def eliminar_publicacion(self, id_publicacion, usuario_id):
        publicacion = self.obtener_publicacion(id_publicacion)

        if publicacion is None:
            raise ValueError("La publicación no existe.")

        if publicacion.autor_id != usuario_id:
            raise ValueError("Solo puedes eliminar tus propias publicaciones.")

        # Se quita la publicación de los dos diccionarios
        del self.publicaciones_por_id[id_publicacion]
        self.ids_por_usuario[usuario_id].discard(id_publicacion)

        # Si tenía foto o video, MultimediaService se encarga de eliminarlo del disco.
        # Así centralizamos tanto el almacenamiento como la eliminación de archivos.
        self.multimedia_service.eliminar_archivo(publicacion.archivo)

        self._guardar()
