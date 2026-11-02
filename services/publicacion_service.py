from models.publicacion import Publicacion
from repositories.publicacion_repository import PublicacionRepository

MAX_LONGITUD = 500   #máximo de caracteres por publicación


class PublicacionService:
    def __init__(self, repositorio=None):
        self.repositorio = repositorio or PublicacionRepository()

        #Lista en memoria con todas las publicaciones (se llena desde el archivo)
        self.publicaciones = self.repositorio.cargar()

        #El próximo id es el más alto que exista + 1
        self._siguiente_id = 1
        for p in self.publicaciones:
            if p.id >= self._siguiente_id:
                self._siguiente_id = p.id + 1

    # ---------- Reglas internas (lógica) ----------

    def _validar_contenido(self, contenido):
        #Quita espacios sobrantes y revisa las reglas
        contenido = (contenido or "").strip()
        if not contenido:
            raise ValueError("La publicación no puede estar vacía.")
        if len(contenido) > MAX_LONGITUD:
            raise ValueError(f"La publicación no puede superar {MAX_LONGITUD} caracteres.")
        return contenido

    def _guardar(self):
        #Se llama después de cada cambio para que nada se pierda al cerrar
        self.repositorio.guardar(self.publicaciones)

    def obtener_publicacion(self, id_publicacion):
        #Devuelve la publicación con ese id, o None si no existe
        for p in self.publicaciones:
            if p.id == id_publicacion:
                return p
        return None

    # ---------- Métodos que usan las pantallas y los demás módulos ----------

    def crear_publicacion(self, autor_id, contenido):
        contenido = self._validar_contenido(contenido)
        nueva = Publicacion(self._siguiente_id, autor_id, contenido)
        self._siguiente_id += 1
        self.publicaciones.append(nueva)
        self._guardar()
        return nueva

    def obtener_publicaciones_usuario(self, autor_id):
        #Junta solo las publicaciones de ese autor
        propias = []
        for p in self.publicaciones:
            if p.autor_id == autor_id:
                propias.append(p)
        #Ordena de la más reciente a la más antigua (si la fecha es igual, desempata el id)
        return sorted(propias, key=lambda p: (p.fecha, p.id), reverse=True)

    def editar_publicacion(self, id_publicacion, usuario_id, nuevo_contenido):
        publicacion = self.obtener_publicacion(id_publicacion)
        if publicacion is None:
            raise ValueError("La publicación no existe.")
        if publicacion.autor_id != usuario_id:
            raise ValueError("Solo puedes editar tus propias publicaciones.")
        publicacion.contenido = self._validar_contenido(nuevo_contenido)
        self._guardar()
        return publicacion

    def eliminar_publicacion(self, id_publicacion, usuario_id):
        publicacion = self.obtener_publicacion(id_publicacion)
        if publicacion is None:
            raise ValueError("La publicación no existe.")
        if publicacion.autor_id != usuario_id:
            raise ValueError("Solo puedes eliminar tus propias publicaciones.")
        self.publicaciones.remove(publicacion)
        self._guardar()