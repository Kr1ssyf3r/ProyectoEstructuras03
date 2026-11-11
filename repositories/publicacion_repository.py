import json
import os
import tempfile

from models.publicacion import Publicacion

class PublicacionRepository:
    def __init__(self, ruta= "data/publicaciones.json"):
        self.ruta = ruta

    def guardar(self, publicaciones):
        #Crea la carpeta data si todavía no existe
        carpeta = os.path.dirname(self.ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)

        #Convertir cada publicación a diccionario
        datos = []
        for p in publicaciones:
            datos.append(p.to_dict())

        #Escritura segura: primero se escribe en un archivo temporal...
        descriptor, ruta_temporal = tempfile.mkstemp(dir=carpeta or ".", suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
            #...y solo si todo salió bien, reemplaza al archivo original de un solo paso
            os.replace(ruta_temporal, self.ruta)
        except Exception:
            #Si algo falla, borra el temporal y el archivo original queda intacto
            if os.path.exists(ruta_temporal):
                os.remove(ruta_temporal)
            raise

    def cargar(self):
        #Si el archivo no existe, devuelve una lista vacía
        if not os.path.exists(self.ruta):
            return []

        #Lee el contenido del archivo JSON y lo convierte en una lista de objetos Publicacion
        with open(self.ruta, "r", encoding="utf-8") as archivo:
            contenido = archivo.read().strip()
        if not contenido:
            return []
        datos = json.loads(contenido)

        publicaciones = []
        for d in datos:
            publicaciones.append(Publicacion.from_dict(d))

        return publicaciones