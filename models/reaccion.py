from dataclasses import dataclass, field
from datetime import datetime

# Tipos de reacción permitidos. Es un conjunto: preguntar
# "x in TIPOS_VALIDOS" es rápido y no admite repetidos.
TIPOS_VALIDOS = {"me_gusta"}


@dataclass
class Reaccion:
    usuario_id: str
    publicacion_id: str
    tipo: str = "me_gusta"
    fecha: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    def __post_init__(self):
        """Valida los atributos básicos de la reacción."""

        atributos = {
            "ID del usuario": self.usuario_id,
            "ID de la publicación": self.publicacion_id,
            "tipo": self.tipo,
            "fecha": self.fecha
        }

        # Validar tipos y campos vacíos antes de validar valores semánticos.
        for nombre, valor in atributos.items():

            if not isinstance(valor, str):
                raise TypeError(
                    f"El campo {nombre} debe ser texto."
                )

            if not valor.strip():
                raise ValueError(
                    f"El campo {nombre} no puede estar vacío."
                )

        # Validar que el tipo de reacción sea válido.
        if self.tipo not in TIPOS_VALIDOS:
            raise ValueError(
                f"El tipo de reacción '{self.tipo}' no es válido. "
                f"Tipos válidos: {', '.join(TIPOS_VALIDOS)}."
            )

        # Validar el formato de la fecha.
        try:
            datetime.fromisoformat(self.fecha)
        except ValueError:
            raise ValueError("La fecha debe estar en formato ISO 8601.")

    def to_dict(self) -> dict:
        """Convierte la reacción a un diccionario."""
        return {
            "usuario_id": self.usuario_id,
            "publicacion_id": self.publicacion_id,
            "tipo": self.tipo,
            "fecha": self.fecha
        }


    @classmethod
    def from_dict(cls, data: dict) -> "Reaccion":
        """Crea una instancia de Reaccion a partir de un diccionario."""
        return cls(
            usuario_id=data["usuario_id"],
            publicacion_id=data["publicacion_id"],
            tipo=data.get("tipo", "me_gusta"),
            fecha=data.get("fecha", datetime.now().isoformat(timespec="seconds"))
        )