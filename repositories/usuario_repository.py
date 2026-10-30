import json
import os
import tempfile
from pathlib import Path

from models.usuario import Usuario


class UsuarioRepository:

    def __init__(self, ruta_archivo="data/usuarios.json"):
        self.ruta_archivo = Path(ruta_archivo)

        self.usuarios_por_id = {}
        self.usuarios_por_nombre = {}
        self.usuarios_por_correo = {}

        self.cargar_usuarios()

    def cargar_usuarios(self):
        """Carga los usuarios y reconstruye los índices desde cero."""

        self.ruta_archivo.parent.mkdir(parents=True, exist_ok=True)

        if not self.ruta_archivo.exists():
            self.ruta_archivo.write_text("[]", encoding="utf-8")

        with open(self.ruta_archivo, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        if not isinstance(datos, list):
            raise ValueError("El archivo de usuarios debe contener una lista.")

        # Diccionarios temporales para evitar cargas parciales.
        usuarios_por_id = {}
        usuarios_por_nombre = {}
        usuarios_por_correo = {}

        for registro in datos:
            usuario = Usuario.from_dict(registro)

            id_usuario = usuario.id
            nombre_usuario = usuario.usuario.lower()
            correo = usuario.correo.lower()

            if id_usuario in usuarios_por_id:
                raise ValueError(f"ID duplicado: {id_usuario}")

            if nombre_usuario in usuarios_por_nombre:
                raise ValueError(
                    f"Nombre de usuario duplicado: {nombre_usuario}"
                )

            if correo in usuarios_por_correo:
                raise ValueError(f"Correo duplicado: {correo}")

            usuarios_por_id[id_usuario] = usuario
            usuarios_por_nombre[nombre_usuario] = usuario
            usuarios_por_correo[correo] = usuario

        # Se reemplazan los índices únicamente si toda la carga fue válida.
        self.usuarios_por_id = usuarios_por_id
        self.usuarios_por_nombre = usuarios_por_nombre
        self.usuarios_por_correo = usuarios_por_correo

    def guardar_usuarios(self):
        """Guarda todos los usuarios utilizando un archivo temporal."""

        datos = [
            usuario.to_dict()
            for usuario in self.usuarios_por_id.values()
        ]

        archivo_temporal = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.ruta_archivo.parent,
                suffix=".tmp",
                delete=False
            ) as archivo:
                archivo_temporal = archivo.name

                json.dump(datos, archivo, ensure_ascii=False, indent=4)
                archivo.flush()
                os.fsync(archivo.fileno())

            os.replace(archivo_temporal, self.ruta_archivo)

        finally:
            if (
                archivo_temporal is not None
                and os.path.exists(archivo_temporal)
            ):
                os.remove(archivo_temporal)

    def _agregar_a_indices(self, usuario):
        """Agrega un usuario a los tres índices."""

        self.usuarios_por_id[usuario.id] = usuario
        self.usuarios_por_nombre[usuario.usuario.lower()] = usuario
        self.usuarios_por_correo[usuario.correo.lower()] = usuario

    def _quitar_de_indices(self, usuario):
        """Elimina un usuario de todos los índices."""

        self.usuarios_por_id.pop(usuario.id, None)

        # Eliminar las claves asociadas al ID del usuario.
        for nombre, registrado in list(
            self.usuarios_por_nombre.items()
        ):
            if registrado.id == usuario.id:
                del self.usuarios_por_nombre[nombre]

        for correo, registrado in list(
            self.usuarios_por_correo.items()
        ):
            if registrado.id == usuario.id:
                del self.usuarios_por_correo[correo]

    def guardar(self, usuario):
        """Registra un usuario y actualiza la persistencia."""

        if usuario.id in self.usuarios_por_id:
            raise ValueError("Ya existe un usuario con ese ID.")

        if usuario.usuario.lower() in self.usuarios_por_nombre:
            raise ValueError("Ese nombre de usuario ya está registrado.")

        if usuario.correo.lower() in self.usuarios_por_correo:
            raise ValueError("Ese correo ya está registrado.")

        self._agregar_a_indices(usuario)

        try:
            self.guardar_usuarios()
        except Exception:
            self._quitar_de_indices(usuario)
            raise

        return usuario

    def buscar_por_id(self, id_usuario):
        """Busca un usuario por su ID."""

        return self.usuarios_por_id.get(id_usuario)

    def buscar_por_nombre(self, nombre_usuario):
        """Busca un usuario por su nombre de usuario."""

        if not isinstance(nombre_usuario, str):
            return None

        return self.usuarios_por_nombre.get(nombre_usuario.lower())

    def buscar_por_correo(self, correo):
        """Busca un usuario por su correo electrónico."""

        if not isinstance(correo, str):
            return None

        return self.usuarios_por_correo.get(correo.lower())

    def obtener_todos(self):
        """Devuelve una lista con todos los usuarios."""

        return list(self.usuarios_por_id.values())

    def eliminar(self, id_usuario):
        """Elimina un usuario y actualiza la persistencia."""

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

    
    def actualizar(self, usuario):
        """Actualiza un usuario existente y su persistencia."""

        usuario_anterior = self.buscar_por_id(usuario.id)

        if usuario_anterior is None:
            raise ValueError("No existe un usuario con ese ID.")

        # Comprobar que el nombre de usuario no pertenezca a otro usuario.
        usuario_existente = self.buscar_por_nombre(usuario.usuario)

        if (
            usuario_existente is not None
            and usuario_existente.id != usuario.id
        ):
            raise ValueError("Ese nombre de usuario ya está registrado.")

        # Comprobar que el correo no pertenezca a otro usuario.
        correo_existente = self.buscar_por_correo(usuario.correo)

        if (
            correo_existente is not None
            and correo_existente.id != usuario.id
        ):
            raise ValueError("Ese correo ya está registrado.")

        # Quitar los datos anteriores de los índices.
        self._quitar_de_indices(usuario_anterior)

        # Registrar los datos actualizados.
        self._agregar_a_indices(usuario)

        try:
            self.guardar_usuarios()

        except Exception:
            # Restaurar los datos anteriores si falla la persistencia.
            self._quitar_de_indices(usuario)
            self._agregar_a_indices(usuario_anterior)
            raise

        return usuario
