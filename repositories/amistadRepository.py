"""Persistencia de amistades, solicitudes y bloqueos en un único JSON."""

import json
import os
import tempfile
from pathlib import Path


class AmistadRepository:

    def __init__(self, ruta_archivo="data/relaciones.json"):
        self.ruta_archivo = Path(ruta_archivo)

    def cargar(self) -> dict:
        """Recupera las relaciones del archivo JSON."""

        if not self.ruta_archivo.exists():
            return {
                "version": 1,
                "amistades": {},
                "solicitudes": [],
                "bloqueos": {}
            }

        # (CAMBIO) Captura errores de lectura y los convierte en ValueError.
        try:
            with self.ruta_archivo.open(
                "r",
                encoding="utf-8"
            ) as archivo:
                datos = json.load(archivo)

        except OSError as error:
            raise ValueError(
                f"No se pudo leer el archivo de relaciones: {error}"
            ) from error

        if (
            not isinstance(datos, dict)
            or datos.get("version") != 1
        ):
            raise ValueError(
                "Formato de relaciones no compatible."
            )

        if (
            not isinstance(datos.get("amistades"), dict)
            or not isinstance(datos.get("solicitudes"), list)
        ):
            raise ValueError("Archivo de relaciones incompleto.")

        # ---------------------------------------
        # APARTADO DE BLOQUEOS
        # ---------------------------------------

        # Compatibilidad con JSON anteriores que no contienen bloqueos.
        if "bloqueos" not in datos:
            datos["bloqueos"] = {}

        if not isinstance(datos["bloqueos"], dict):
            raise ValueError("Archivo de bloqueos inválido.")

        return datos

    # ---------------------------------------
    # APARTADO DE BLOQUEOS
    # ---------------------------------------

    def guardar(
        self,
        amistades: dict,
        solicitudes: list,
        bloqueos: dict
    ) -> None:
        """
        Guarda amistades, solicitudes y bloqueos
        en un único archivo JSON mediante escritura atómica.
        """

        datos = {
            "version": 1,
            "amistades": amistades,
            "solicitudes": solicitudes,
            "bloqueos": bloqueos
        }

        carpeta = self.ruta_archivo.resolve().parent
        carpeta.mkdir(parents=True, exist_ok=True)

        temporal = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=carpeta,
                prefix="relaciones_",
                suffix=".tmp",
                delete=False
            ) as archivo:

                temporal = archivo.name

                json.dump(
                    datos,
                    archivo,
                    ensure_ascii=False,
                    indent=2
                )

                archivo.flush()
                os.fsync(archivo.fileno())

            # Escritura atómica:
            # Se reemplaza el JSON original por el temporal.
            os.replace(temporal, self.ruta_archivo)
            temporal = None

        finally:
            if temporal and os.path.exists(temporal):
                os.unlink(temporal)