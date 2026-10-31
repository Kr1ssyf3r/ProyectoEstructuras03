"""Persistencia de amistades y solicitudes en un único JSON."""
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
                "solicitudes": []
            }

        #(CAMBIO) antes solo se abria el archivo y si fallaba la lectura (permisos, archivo bloqueado)
        #salia un OSError que el resto del programa no esperaba. Ahora se captura y se convierte en ValueError
        #para que todos los errores de carga sean del mismo tipo.
        #JSONDecodeError y UnicodeDecodeError ya heredan de ValueError, por eso no hace falta capturarlos aparte
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

        return datos

    #(CAMBIO) antes guardar(grafo, gestor) llamaba a grafo.exportar() y gestor.exportar() por dentro,
    #lo que hacia que el repository conociera como son esas clases. Ahora recibe los datos ya exportados
    #(un dict y una lista), asi solo se encarga de escribir en disco y es mas facil de probar con datos simples
    def guardar(self, amistades: dict, solicitudes: list) -> None:
        """Guarda amistades y solicitudes mediante un archivo temporal."""

        datos = {
            "version": 1,
            "amistades": amistades,
            "solicitudes": solicitudes
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

            #escritura atomica: el archivo temporal reemplaza al original de una sola vez,
            #asi si el programa se cae a mitad de escribir no queda un JSON corrupto
            os.replace(temporal, self.ruta_archivo)
            temporal = None

        finally:
            if temporal and os.path.exists(temporal):
                os.unlink(temporal)