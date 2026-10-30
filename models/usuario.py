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
