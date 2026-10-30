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

    @staticmethod
    def _generar_hash(contrasena):
        """Genera un hash seguro de la contraseña."""

        salt = secrets.token_bytes(UsuarioService.LONGITUD_SALT)

        hash_contrasena = hashlib.pbkdf2_hmac(
            "sha256",
            contrasena.encode("utf-8"),
            salt,
            UsuarioService.ITERACIONES_HASH
        )

        return (
            f"pbkdf2_sha256$"
            f"{UsuarioService.ITERACIONES_HASH}$"
            f"{salt.hex()}$"
            f"{hash_contrasena.hex()}"
        )

    @staticmethod
    def _verificar_contrasena(contrasena, contrasena_hash):
        """Comprueba si una contraseña coincide con su hash."""

        if not isinstance(contrasena, str):
            return False

        if not isinstance(contrasena_hash, str):
            return False

        try:
            algoritmo, iteraciones, salt, hash_original = (
                contrasena_hash.split("$")
            )

            if algoritmo != "pbkdf2_sha256":
                return False

            iteraciones = int(iteraciones)

            if iteraciones != UsuarioService.ITERACIONES_HASH:
                return False

            salt = bytes.fromhex(salt)
            hash_original = bytes.fromhex(hash_original)

            if len(salt) != UsuarioService.LONGITUD_SALT:
                return False

            hash_nuevo = hashlib.pbkdf2_hmac(
                "sha256",
                contrasena.encode("utf-8"),
                salt,
                iteraciones
            )

            return hmac.compare_digest(hash_nuevo, hash_original)

        except (ValueError, TypeError, AttributeError, OverflowError):
            return False
