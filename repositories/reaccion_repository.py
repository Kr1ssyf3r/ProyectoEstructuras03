import json
import os
import tempfile
from pathlib import Path

from models.reaccion import Reaccion


class ReaccionRepository:
    """Guarda las reacciones en memoria y en data/reacciones.json"""

    def __init__(self, ruta_archivo="data/reacciones.json"):
        self.ruta_archivo = Path(ruta_archivo)

        #Fuente de verdad: (usuario_id, publicacion_id) -> Reaccion
        self.reacciones = {}

        #indices derivados (se pueden reconstruir desde self.reacciones)
        self.likes_por_publicacion = {}  # publicacion_id -> set de usuario_id
        self.likes_por_usuario = {}  # usuario_id -> set de publicacion_id

        self.cargar_reacciones()

    def cargar_reacciones(self):
        """Carga las reacciones y reconstruye los índices desde cero."""

        self.ruta_archivo.parent.mkdir(parents=True, exist_ok=True)

        if not self.ruta_archivo.exists():
            self.ruta_archivo.write_text("[]", encoding="utf-8")

        with open(self.ruta_archivo, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        if not isinstance(datos, list):
            raise ValueError("El archivo de reacciones debe contener una lista.")

        # Diccionario temporal para evitar cargas parciales.
        reacciones_temp = {}

        for registro in datos:
            reaccion = Reaccion.from_dict(registro)
            clave = (reaccion.usuario_id, reaccion.publicacion_id)

            if clave in reacciones_temp:
                raise ValueError(
                    f"Reacción duplicada: usuario {reaccion.usuario_id}, publicación {reaccion.publicacion_id}"
                )

            reacciones_temp[clave] = reaccion

        # Si todo está bien, reemplazar la fuente de verdad y reconstruir índices.
        self.reacciones = reacciones_temp
        self._reconstruir_indices()

    def guardar_reacciones(self):
        """Guarda todaslas reacciones usando un archivo temporal"""

        datos = [
            reaccion.to_dict()
            for reaccion in self.reacciones.values()
        ]

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
            if(
                archivo_temporal is not None
                and os.path.exists(archivo_temporal)
            ):
                os.remove(archivo_temporal)

    def _reconstruir_indices(self):
        """Recosntruye los dos indices apartir de self.reacciones"""

        self.likes_por_publicacion = {}
        self.likes_por_usuario = {}

        for reaccion in self.reacciones.values():
            self._agregar_a_indices(reaccion)

    def _agregar_a_indices(self, reaccion):
        """Agrega una reaccion a los dos indices"""

        self.likes_por_publicacion.setdefault(
            reaccion.publicacion_id, set()
        ).add(reaccion.usuario_id)

        self.likes_por_usuario.setdefault(
            reaccion.usuario_id, set()
        ).add(reaccion.publicacion_id)

    def _quitar_de_indices(self, reaccion):
        """Elimina una reaccion de los dos indices"""

        ususarios = self.likes_por_publicacion.get(reaccion.publicacion_id)
        if ususarios is not None:
            ususarios.discard(reaccion.usuario_id)
            if not ususarios:
                del self.likes_por_publicacion[reaccion.publicacion_id]

        publicaciones = self.likes_por_usuario.get(reaccion.usuario_id)
        if publicaciones is not None:
            publicaciones.discard(reaccion.publicacion_id)
            if not publicaciones:
                del self.likes_por_usuario[reaccion.usuario_id]

    def agregar(self, reaccion):
        """Agrega una reaccion. Devuelve True si se agrego, False si ya existia"""

        clave = (reaccion.usuario_id, reaccion.publicacion_id)

        if clave in self.reacciones:
            return False  # Ya existia

        self.reacciones[clave] = reaccion
        self._agregar_a_indices(reaccion)

        try:
            self.guardar_reacciones()
        except Exception:
            # Si falla la persistencia, revertir cambios en memoria.
            del self.reacciones[clave]
            self._quitar_de_indices(reaccion)
            raise

        return True

    def eliminar(self, usuario_id, publicacion_id):
        """Elimina una reaccion. Devuelve True si se elimino, False si no existia"""

        clave = (usuario_id, publicacion_id)
        reaccion = self.reacciones.pop(clave, None)

        if reaccion is None:
            return False  # No existia

        self._quitar_de_indices(reaccion)

        try:
            self.guardar_reacciones()
        except Exception:
            # Si falla la persistencia, revertir cambios en memoria.
            self.reacciones[clave] = reaccion
            self._agregar_a_indices(reaccion)
            raise

        return True

    def existe(self, usuario_id, publicacion_id):
        """Indica si el ususario ya reacciono a la publicacion. Devuelve True o False"""

        return (usuario_id, publicacion_id) in self.reacciones

    def contar(self, publicacion_id):
        """Devuelve el numero de reacciones a una publicacion"""

        return len(self.likes_por_publicacion.get(publicacion_id, set()))

    def publicaciones_de(self, usuario_id):
        """Publicaciones a las que reacciono el usuario (copia de solo lectura)."""

        return frozenset(self.likes_por_usuario.get(usuario_id, ()))