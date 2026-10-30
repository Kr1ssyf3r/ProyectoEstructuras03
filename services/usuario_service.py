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

    def registrar_usuario(
        self,
        nombre,
        nombre_usuario,
        correo,
        contrasena,
        confirmar_contrasena
    ):
        """Valida y registra un nuevo usuario."""

        campos = [
            (nombre, "nombre"),
            (nombre_usuario, "nombre de usuario"),
            (correo, "correo"),
            (contrasena, "contraseña"),
            (confirmar_contrasena, "confirmación de contraseña")
        ]

        for valor, campo in campos:
            self._validar_cadena(valor, campo)

        nombre = nombre.strip()
        nombre_usuario = nombre_usuario.strip()
        correo = correo.strip().lower()

        if any(caracter.isspace() for caracter in nombre_usuario):
            raise ValueError(
                "El nombre de usuario no puede contener espacios."
            )

        if len(contrasena) < self.LONGITUD_MINIMA_CONTRASENA:
            raise ValueError(
                f"La contraseña debe tener al menos "
                f"{self.LONGITUD_MINIMA_CONTRASENA} caracteres."
            )

        if contrasena != confirmar_contrasena:
            raise ValueError("Las contraseñas no coinciden.")

        if self.repositorio.buscar_por_nombre(nombre_usuario):
            raise ValueError(
                "Ese nombre de usuario ya está registrado."
            )

        if self.repositorio.buscar_por_correo(correo):
            raise ValueError("Ese correo ya está registrado.")

        usuario = Usuario(
            id=str(uuid.uuid4()),
            nombre=nombre,
            usuario=nombre_usuario,
            correo=correo,
            contrasena_hash=self._generar_hash(contrasena)
        )

        self.repositorio.guardar(usuario)

        return usuario
