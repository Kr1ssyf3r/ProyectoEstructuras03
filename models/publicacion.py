"""
MODELO: la clase Publicacion.

Un "modelo" solo describe cómo es un dato. No lee archivos, no valida reglas
del negocio y no sabe nada de ventanas. Una Publicacion es solo esto:
quién la escribió, qué dice y cuándo.
"""

from datetime import datetime


class Publicacion:
    def __init__(self, id, autor_id, contenido, fecha=None, archivo=None, tipo_archivo=None):
        self.id = id                        # número único de la publicación
        self.autor_id = autor_id            # id del Usuario (el mismo id que usa el integrante 1)
        self.contenido = contenido          # el texto que escribió
        self.fecha = fecha or datetime.now()  # momento de creación; sirve para ordenar
        self.archivo = archivo              # nombre del archivo subido (foto o video), o None
        self.tipo_archivo = tipo_archivo    # "imagen", "video" o None

    def to_dict(self):
        """
        Convierte la publicación en un diccionario simple para guardarla en JSON.
        JSON no entiende objetos datetime, por eso la fecha se guarda como texto.
        """
        fecha = self.fecha
        fecha_str = fecha if isinstance(fecha, str) else fecha.isoformat()
        return {
            "id": self.id,
            "autor_id": self.autor_id,
            "contenido": self.contenido,
            "fecha": fecha_str,
            "archivo": self.archivo,
            "tipo_archivo": self.tipo_archivo,
        }

    @classmethod
    def from_dict(cls, datos):
        """Lo contrario: arma una Publicacion a partir de un diccionario leído del JSON."""
        return cls(
            id=datos["id"],
            autor_id=datos["autor_id"],
            contenido=datos["contenido"],
            fecha=datetime.fromisoformat(datos["fecha"]),  # texto -> datetime
            archivo=datos.get("archivo"),            # .get: las publicaciones viejas no lo traen
            tipo_archivo=datos.get("tipo_archivo"),
        )

    def __repr__(self):
        return f"Publicacion(id={self.id}, autor_id={self.autor_id}, fecha={self.fecha:%Y-%m-%d %H:%M})"