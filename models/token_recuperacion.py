from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class TokenRecuperacion:
    """
    Representa un token para restablecer la contraseña de un usuario.
    """

    id: str
    usuario_id: str
    token_hash: str
    fecha_creacion: str
    fecha_expiracion: str
    usado: bool = False

    def __post_init__(self):
        """Valida los atributos básicos del token."""

        atributos = {
            "ID": self.id,
            "ID del usuario": self.usuario_id,
            "Hash del token": self.token_hash,
            "Fecha de creación": self.fecha_creacion,
            "Fecha de expiración": self.fecha_expiracion
        }

        # Validar que los atributos sean cadenas no vacías.
        for nombre, valor in atributos.items():
            if not isinstance(valor, str):
                raise TypeError(
                    f"El campo {nombre} debe ser texto."
                )

            if not valor.strip():
                raise ValueError(
                    f"El campo {nombre} no puede estar vacío."
                )

        # Validar los identificadores UUID.
        try:
            UUID(self.id)
            UUID(self.usuario_id)
        except ValueError:
            raise ValueError("Los identificadores deben ser UUID válidos.")

        # Validar que el hash tenga formato hexadecimal SHA-256.
        if len(self.token_hash) != 64:
            raise ValueError("El hash del token debe tener 64 caracteres.")

        try:
            int(self.token_hash, 16)
        except ValueError:
            raise ValueError("El hash del token debe ser hexadecimal.")

        # Validar las fechas y comprobar que tengan zona horaria.
        try:
            creacion = datetime.fromisoformat(self.fecha_creacion)
            expiracion = datetime.fromisoformat(self.fecha_expiracion)
        except ValueError:
            raise ValueError("Las fechas del token no son válidas.")

        if creacion.tzinfo is None or expiracion.tzinfo is None:
            raise ValueError("Las fechas deben incluir zona horaria.")

        if expiracion <= creacion:
            raise ValueError(
                "La fecha de expiración debe ser posterior a la creación."
            )

        # Validar el estado de uso.
        if not isinstance(self.usado, bool):
            raise TypeError("El campo usado debe ser booleano.")

    def to_dict(self) -> dict:
        """Convierte el token en un diccionario para guardarlo en JSON."""

        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "token_hash": self.token_hash,
            "fecha_creacion": self.fecha_creacion,
            "fecha_expiracion": self.fecha_expiracion,
            "usado": self.usado
        }

    @classmethod
    def from_dict(cls, datos: dict):
        """Construye un token a partir de un diccionario."""

        return cls(
            id=datos["id"],
            usuario_id=datos["usuario_id"],
            token_hash=datos["token_hash"],
            fecha_creacion=datos["fecha_creacion"],
            fecha_expiracion=datos["fecha_expiracion"],
            usado=datos["usado"]
        )
