import hashlib
import hmac
import secrets
import uuid

from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository


class UsuarioService:

    ITERACIONES_HASH = 600_000
    LONGITUD_SALT = 16
    LONGITUD_MINIMA_CONTRASENA = 8

    def __init__(self, repositorio=None):
        self.repositorio = (
            repositorio
            if repositorio is not None
            else UsuarioRepository()
        )
        self.usuario_activo = None

    @staticmethod
    def _validar_cadena(valor, nombre_campo):
        """Comprueba que un campo sea texto y no esté vacío."""

        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"El campo {nombre_campo} es obligatorio.")
