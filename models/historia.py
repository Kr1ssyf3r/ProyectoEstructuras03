from datetime import datetime, timedelta
import uuid

#duracion por defecto de una historia, pasado este tiempo deja de mostrarse
HORAS_VIGENCIA = 24

class Historia:
    """Una historia: un archivo (imagen o video) que expira."""
    def __init__(self,autor_id,archivo,tipo_archivo,id=None,fecha_creacion=None,fecha_expiracion=None):
        self.id = id or str(uuid.uuid4())#generador de id aleatorio, para que no se repita aunque se borren historias
        self.autor_id = autor_id #id del usuario que subió la historia

        #solo se guarda el nombre del archivo, el archivo real vive en la carpeta de medios
        self.archivo = archivo
        self.tipo_archivo = tipo_archivo #solo "imagen" o "video"

        self.fecha_creacion = fecha_creacion or datetime.now()

        #si no se indica, expira HORAS_VIGENCIA horas despues de crearse
        self.fecha_expiracion = fecha_expiracion or (self.fecha_creacion + timedelta(hours=HORAS_VIGENCIA))

    def esta_vigente(self, ahora=None):
        """True si la historia todavia no ha expirado."""
        ahora = ahora or datetime.now()
        return ahora < self.fecha_expiracion

    # ---------------------------------------
    # CONVERSION A JSON
    # ---------------------------------------
    def to_dict(self):
        #las fechas se guardan como texto ISO porque JSON no tiene tipo fecha
        return {
            "id": self.id,
            "autor_id": self.autor_id,
            "archivo": self.archivo,
            "tipo_archivo": self.tipo_archivo,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "fecha_expiracion": self.fecha_expiracion.isoformat(),
        }

    @classmethod
    def from_dict(cls, datos):
        return cls(
            autor_id=datos["autor_id"],
            archivo=datos["archivo"],
            tipo_archivo=datos["tipo_archivo"],
            id=datos["id"],
            fecha_creacion=datetime.fromisoformat(datos["fecha_creacion"]),
            fecha_expiracion=datetime.fromisoformat(datos["fecha_expiracion"]),
        )