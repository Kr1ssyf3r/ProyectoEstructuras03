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
