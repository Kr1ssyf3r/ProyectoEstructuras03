import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Usuario:
    """
    Representa a un estudiante registrado en Social UNA.

    Atributos:
        id: Identificador único del usuario (UUID).
        nombre: Nombre completo del estudiante.
        usuario: Nombre de usuario para iniciar sesión.
        correo: Correo electrónico del estudiante.
        contrasena_hash: Hash seguro de la contraseña.
        fecha_registro: Fecha y hora de registro.
    """

    id: str
    nombre: str
    usuario: str
    correo: str
    contrasena_hash: str
    fecha_registro: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    def __post_init__(self):
        """Valida los atributos básicos del usuario."""

        atributos = {
            "ID": self.id,
            "nombre": self.nombre,
            "usuario": self.usuario,
            "correo": self.correo,
            "hash de contraseña": self.contrasena_hash,
            "fecha de registro": self.fecha_registro
        }

        # Validar tipos y campos vacíos.
        for nombre, valor in atributos.items():

            if not isinstance(valor, str):
                raise TypeError(
                    f"El campo {nombre} debe ser texto."
                )

            if not valor.strip():
                raise ValueError(
                    f"El campo {nombre} no puede estar vacío."
                )

        # Validar el formato básico del correo electrónico.
        patron_correo = (
            r"^[a-zA-Z0-9_%+-]+(?:\.[a-zA-Z0-9_%+-]+)*"
            r"@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+"
            r"[a-zA-Z]{2,}$"
        )

        if not re.fullmatch(patron_correo, self.correo):
            raise ValueError("El correo electrónico no es válido.")

        # Validar el formato de la fecha.
        try:
            datetime.fromisoformat(self.fecha_registro)
        except ValueError:
            raise ValueError("La fecha de registro no es válida.")

    def to_dict(self) -> dict:
        """Convierte el usuario en un diccionario para guardarlo en JSON."""

        return {
            "id": self.id,
            "nombre": self.nombre,
            "usuario": self.usuario,
            "correo": self.correo,
            "contrasena_hash": self.contrasena_hash,
            "fecha_registro": self.fecha_registro
        }
