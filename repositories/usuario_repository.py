import json
import os
import tempfile

from models.usuario import Usuario


class UsuarioRepository:
    """
    Administra el almacenamiento y recuperación de usuarios.

    Utiliza diccionarios como tablas hash para realizar
    búsquedas rápidas y un archivo JSON para persistencia.
    """

    def __init__(self, ruta_archivo="data/usuarios.json"):
        self.ruta_archivo = ruta_archivo

        self.usuarios_por_id = {}
        self.usuarios_por_nombre = {}
        self.usuarios_por_correo = {}

        if not os.path.exists(self.ruta_archivo):
            self.guardar_usuarios()

        self.cargar_usuarios()

    def cargar_usuarios(self):
        """Carga los usuarios desde el archivo JSON."""

        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)

            if not isinstance(datos, list):
                raise ValueError(
                    "El contenido del archivo JSON no es válido."
                )

            for registro in datos:
                usuario = Usuario.from_dict(registro)

                if (
                    usuario.id in self.usuarios_por_id
                    or usuario.usuario.lower() in self.usuarios_por_nombre
                    or usuario.correo.lower() in self.usuarios_por_correo
                ):
                    raise ValueError(
                        "El archivo contiene usuarios duplicados."
                    )

                self._agregar_a_indices(usuario)

        except (json.JSONDecodeError, TypeError, KeyError) as error:
            raise ValueError(
                "El archivo de usuarios contiene datos inválidos."
            ) from error

    def guardar_usuarios(self):
        """Guarda los usuarios mediante un archivo temporal."""

        carpeta = os.path.dirname(os.path.abspath(self.ruta_archivo))
        os.makedirs(carpeta, exist_ok=True)

        datos = [
            usuario.to_dict()
            for usuario in self.usuarios_por_id.values()
        ]

        ruta_temporal = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=carpeta,
                suffix=".tmp",
                delete=False
            ) as archivo:
                ruta_temporal = archivo.name

                json.dump(datos, archivo, indent=4, ensure_ascii=False)
                archivo.flush()
                os.fsync(archivo.fileno())

            os.replace(ruta_temporal, self.ruta_archivo)
            ruta_temporal = None

        finally:
            if ruta_temporal and os.path.exists(ruta_temporal):
                os.remove(ruta_temporal)

    def _agregar_a_indices(self, usuario):
        """Agrega un usuario a las tablas hash."""

        self.usuarios_por_id[usuario.id] = usuario
        self.usuarios_por_nombre[usuario.usuario.lower()] = usuario
        self.usuarios_por_correo[usuario.correo.lower()] = usuario

    def _quitar_de_indices(self, usuario):
        """Elimina un usuario de las tablas hash."""

        del self.usuarios_por_id[usuario.id]
        del self.usuarios_por_nombre[usuario.usuario.lower()]
        del self.usuarios_por_correo[usuario.correo.lower()]

    def guardar(self, usuario):
        """Registra un usuario en memoria y lo guarda en JSON."""

        if usuario.id in self.usuarios_por_id:
            raise ValueError("El ID del usuario ya está registrado.")

        if usuario.usuario.lower() in self.usuarios_por_nombre:
            raise ValueError("El nombre de usuario ya está registrado.")

        if usuario.correo.lower() in self.usuarios_por_correo:
            raise ValueError("El correo electrónico ya está registrado.")

        self._agregar_a_indices(usuario)

        try:
            self.guardar_usuarios()
        except Exception:
            self._quitar_de_indices(usuario)
            raise

    def buscar_por_id(self, id_usuario):
        """Busca un usuario mediante su identificador."""

        return self.usuarios_por_id.get(id_usuario)

    def buscar_por_nombre(self, nombre_usuario):
        """Busca un usuario mediante su nombre de usuario."""

        return self.usuarios_por_nombre.get(nombre_usuario.lower())

    def buscar_por_correo(self, correo):
        """Busca un usuario mediante su correo electrónico."""

        return self.usuarios_por_correo.get(correo.lower())

    def obtener_todos(self):
        """Devuelve todos los usuarios registrados."""

        return list(self.usuarios_por_id.values())

    def eliminar(self, id_usuario):
        """Elimina un usuario de las tablas hash y del JSON."""

        usuario = self.buscar_por_id(id_usuario)

        if usuario is None:
            return False

        self._quitar_de_indices(usuario)

        try:
            self.guardar_usuarios()
        except Exception:
            self._agregar_a_indices(usuario)
            raise

        return True