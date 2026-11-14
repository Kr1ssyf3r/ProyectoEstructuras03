import json
import os
import tempfile
from pathlib import Path

from models.historia import Historia


class HistoriaRepository:
    """Lee y escribe las historias en un archivo JSON."""

    def __init__(self, ruta_archivo="data/historias.json"):
        self.ruta_archivo = Path(ruta_archivo)

    def cargar(self):
        """Devuelve la lista de objetos Historia guardados."""
        self.ruta_archivo.parent.mkdir(parents=True, exist_ok=True)

        #si el archivo no existe todavia se crea con una lista vacia
        if not self.ruta_archivo.exists():
            self.ruta_archivo.write_text("[]", encoding="utf-8")

        with open(self.ruta_archivo, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        if not isinstance(datos, list):
            raise ValueError("El archivo de historias debe contener una lista.")

        return [Historia.from_dict(registro) for registro in datos]

    def guardar(self, historias):
        """Guarda la lista completa usando un archivo temporal."""
        datos = [historia.to_dict() for historia in historias]
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

            #os.replace es atomico: o queda el archivo viejo o queda el nuevo completo
            os.replace(archivo_temporal, self.ruta_archivo)

        finally:
            if archivo_temporal is not None and os.path.exists(archivo_temporal):
                os.remove(archivo_temporal)