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
