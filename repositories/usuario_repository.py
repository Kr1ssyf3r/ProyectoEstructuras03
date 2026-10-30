import json
import os

from models.usuario import Usuario


class UsuarioRepository:
    """
    Administra el almacenamiento y recuperación de usuarios.

    Utiliza diccionarios como tablas hash para realizar
    búsquedas rápidas y un archivo JSON para persistencia.
    """

    def __init__(self, ruta_archivo="data/usuarios.json"):
        self.ruta_archivo = ruta_archivo

        # Tablas hash para consultar usuarios.
        self.usuarios_por_id = {}
        self.usuarios_por_nombre = {}
        self.usuarios_por_correo = {}

        # Crear el archivo JSON si no existe.
        if not os.path.exists(self.ruta_archivo):
            self.guardar_usuarios()

        # Cargar los usuarios almacenados.
        self.cargar_usuarios()

    def cargar_usuarios(self):
        """Carga los usuarios desde el archivo JSON."""

        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)

            if not isinstance(datos, list):
                raise ValueError("El contenido del archivo JSON no es válido.")

            for registro in datos:
                usuario = Usuario.from_dict(registro)
                self._agregar_a_indices(usuario)

        except (json.JSONDecodeError, TypeError, KeyError):
            raise ValueError("El archivo de usuarios contiene datos inválidos.")

    def guardar_usuarios(self):
        """Guarda todos los usuarios en el archivo JSON."""

        # Crear la carpeta si no existe.
        carpeta = os.path.dirname(self.ruta_archivo)

        if carpeta:
            os.makedirs(carpeta, exist_ok=True)

        # Convertir los usuarios a diccionarios.
        datos = [
            usuario.to_dict()
            for usuario in self.usuarios_por_id.values()
        ]

        # Guardar los datos en formato JSON.
        with open(self.ruta_archivo, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=4, ensure_ascii=False)

    def _agregar_a_indices(self, usuario):
        """Agrega un usuario a las tablas hash."""

        self.usuarios_por_id[usuario.id] = usuario
        self.usuarios_por_nombre[usuario.usuario.lower()] = usuario
        self.usuarios_por_correo[usuario.correo.lower()] = usuario

    def guardar(self, usuario):
        """Registra un usuario en memoria y lo guarda en JSON."""

        if usuario.id in self.usuarios_por_id:
            raise ValueError("El ID del usuario ya está registrado.")

        if usuario.usuario.lower() in self.usuarios_por_nombre:
            raise ValueError("El nombre de usuario ya está registrado.")

        if usuario.correo.lower() in self.usuarios_por_correo:
            raise ValueError("El correo electrónico ya está registrado.")

        self._agregar_a_indices(usuario)
        self.guardar_usuarios()

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
        """Devuelve la lista de todos los usuarios registrados."""

        return list(self.usuarios_por_id.values())

    def eliminar(self, id_usuario):
        """Elimina un usuario de las tablas hash y del JSON."""

        usuario = self.buscar_por_id(id_usuario)

        if usuario is None:
            return False

        del self.usuarios_por_id[usuario.id]
        del self.usuarios_por_nombre[usuario.usuario.lower()]
        del self.usuarios_por_correo[usuario.correo.lower()]

        self.guardar_usuarios()

        return True