import os
import re
import unicodedata
import uuid

from models.publicacion import Publicacion
from repositories.publicacion_repository import PublicacionRepository

MAX_LONGITUD = 500   # máximo de caracteres por publicación

# Archivos permitidos en una publicación
EXTENSIONES_IMAGEN = {"jpg", "jpeg", "png", "gif", "webp"}
EXTENSIONES_VIDEO = {"mp4", "webm"}
MAX_IMAGEN = 5 * 1024 * 1024     # 5 MB
MAX_VIDEO = 25 * 1024 * 1024     # 25 MB

# Palabras que no se permiten (en minúscula y sin tildes). Agregá las que quieran.
PALABRAS_PROHIBIDAS = {"idiota", "estupido", "imbecil"}


def _sin_tildes(texto):
    # "estúpido" -> "estupido", para comparar sin importar las tildes
    normal = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normal if unicodedata.category(c) != "Mn")


class PublicacionService:
    def __init__(self, usuario_service, repositorio=None, carpeta_media="data/uploads"):
        self.usuario_service = usuario_service
        self.repositorio = repositorio or PublicacionRepository()
        self.carpeta_media = carpeta_media    # aquí se guardan las fotos y videos

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

    def _procesar_archivo(self, archivo):
        # Valida la foto o video y lo guarda con un nombre único.
        # Devuelve (nombre_guardado, tipo), o (None, None) si no se subió nada.
        if archivo is None or not archivo.filename:
            return None, None

        extension = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else ""
        if extension in EXTENSIONES_IMAGEN:
            tipo, limite = "imagen", MAX_IMAGEN
        elif extension in EXTENSIONES_VIDEO:
            tipo, limite = "video", MAX_VIDEO
        else:
            raise ValueError("Formato no permitido. Usa jpg, png, gif, webp, mp4 o webm.")

        # Mide el tamaño: se va al final del archivo y ve en qué posición quedó
        archivo.stream.seek(0, os.SEEK_END)
        tamano = archivo.stream.tell()
        archivo.stream.seek(0)
        if tamano > limite:
            raise ValueError(f"El archivo es muy grande (máximo {limite // (1024 * 1024)} MB).")

        os.makedirs(self.carpeta_media, exist_ok=True)
        nombre = f"{uuid.uuid4()}.{extension}"   # nombre único: nadie puede pisar otro archivo
        archivo.save(os.path.join(self.carpeta_media, nombre))
        return nombre, tipo

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
        contenido = self._validar_contenido(contenido, permitir_vacio=tiene_archivo)
        # Si hay foto o video, se valida y se guarda (después del texto, para no guardar archivos de más)
        nombre_archivo, tipo_archivo = self._procesar_archivo(archivo)
        # uuid4 genera un id único que nunca se repite, aunque se borren publicaciones
        nueva = Publicacion(str(uuid.uuid4()), autor_id, contenido,
                            archivo=nombre_archivo, tipo_archivo=tipo_archivo)
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
            nuevo_contenido, permitir_vacio=bool(publicacion.archivo)
        )
        self._guardar()
        return publicacion

    def eliminar_publicacion(self, id_publicacion, usuario_id):
        publicacion = self.obtener_publicacion(id_publicacion)
        if publicacion is None:
            raise ValueError("La publicación no existe.")
        if publicacion.autor_id != usuario_id:
            raise ValueError("Solo puedes eliminar tus propias publicaciones.")
        # Se quita de los dos diccionarios
        del self.publicaciones_por_id[id_publicacion]
        self.ids_por_usuario[usuario_id].discard(id_publicacion)
        # Si tenía foto o video, también se borra el archivo del disco
        if publicacion.archivo:
            ruta = os.path.join(self.carpeta_media, publicacion.archivo)
            if os.path.exists(ruta):
                os.remove(ruta)
        self._guardar()