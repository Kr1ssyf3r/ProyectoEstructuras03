from datetime import datetime

class Publicacion:
    def __init__(self, id, autor_id, contenido, fecha=None):
        self.id = id                          # numero unico de cada publicacion
        self.autor_id = autor_id              # id del autor de cada publicacion
        self.contenido = contenido            # el texto de la publicacion
        self.fecha = fecha or datetime.now()  # si no se da una fecha, se registra al momento

    def to_dict(self):
        # Convierte la publicacion en un diccionario.
        # Ayuda a guardarlo en JSON; la fecha se guarda como texto.
        return {
            "id": self.id,                   
            "autor_id": self.autor_id,        
            "contenido": self.contenido,      
            "fecha": self.fecha.isoformat(),  #ej. "2026-11-01T20:33:45"
        }

    @classmethod
    def from_dict(cls, datos):
        # Lo contrario: recibe el diccionario leido del JSON y arma la publicacion.
        return cls(
            id=datos["id"],
            autor_id=datos["autor_id"],
            contenido=datos["contenido"],
            fecha=datetime.fromisoformat(datos["fecha"]),  # pasa de texto a datetime
        )

    def __repr__(self):                       
        return f"Publicacion(id={self.id}, autor_id={self.autor_id})"