import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from models.token_recuperacion import TokenRecuperacion


class RecuperacionService:
    """
    Gestiona las solicitudes de recuperación de contraseñas.

    Se encarga de generar tokens seguros, validar su vigencia
    y coordinar el cambio de contraseña de los usuarios.
    """

    MINUTOS_EXPIRACION = 30

    def __init__(
        self,
        token_repository,
        usuario_service,
        minutos_expiracion=MINUTOS_EXPIRACION
    ):
        self.token_repository = token_repository
        self.usuario_service = usuario_service

        if (
            not isinstance(minutos_expiracion, int)
            or isinstance(minutos_expiracion, bool)
            or minutos_expiracion <= 0
        ):
            raise ValueError(
                "Los minutos de expiración deben ser un entero positivo."
            )

        self.minutos_expiracion = minutos_expiracion

    @staticmethod
    def generar_hash(token):
        """Genera el hash SHA-256 de un token."""

        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    def generar_token(self, usuario_id):
        """
        Genera un token de recuperación para un usuario.

        Guarda únicamente el hash y devuelve el token original
        para que posteriormente pueda enviarse por correo.
        """

        if not isinstance(usuario_id, str) or not usuario_id.strip():
            raise ValueError("El ID del usuario es obligatorio.")

        # Comprobar que el usuario exista.
        usuario = self.usuario_service.obtener_usuario(usuario_id)

        if usuario is None:
            raise ValueError("No se encontró el usuario.")

        # Generar un token aleatorio.
        token_original = secrets.token_urlsafe(32)

        # Calcular su hash para almacenarlo de forma segura.
        token_hash = self.generar_hash(token_original)

        # Establecer las fechas de creación y expiración.
        ahora = datetime.now(timezone.utc)
        expiracion = ahora + timedelta(
            minutes=self.minutos_expiracion
        )

        token = TokenRecuperacion(
            id=str(uuid4()),
            usuario_id=usuario_id,
            token_hash=token_hash,
            fecha_creacion=ahora.isoformat(),
            fecha_expiracion=expiracion.isoformat(),
            usado=False
        )

        # Guardar el nuevo token.
        self.token_repository.guardar(token)

        return token_original

    def validar_token(self, token_original):
        """
        Comprueba si un token existe, está vigente
        y todavía no ha sido utilizado.

        Retorna el objeto TokenRecuperacion si es válido.
        En caso contrario, retorna None.
        """

        if (
            not isinstance(token_original, str)
            or not token_original
        ):
            return None

        # Buscar utilizando el hash, nunca el token original.
        token_hash = self.generar_hash(token_original)

        token = self.token_repository.buscar_por_hash(token_hash)

        if token is None or token.usado:
            return None

        # Comprobar la fecha de expiración.
        ahora = datetime.now(timezone.utc)

        expiracion = datetime.fromisoformat(
            token.fecha_expiracion
        )

        if ahora >= expiracion:
            return None

        # Comprobar que el usuario todavía exista.
        usuario = self.usuario_service.obtener_usuario(
            token.usuario_id
        )

        if usuario is None:
            return None

        return token

    def invalidar_tokens_usuario(self, usuario_id):
        """Invalida todos los tokens activos de un usuario."""

        tokens = self.token_repository.obtener_por_usuario(
            usuario_id
        )

        for token in tokens:
            if not token.usado:
                token.usado = True
                self.token_repository.guardar(token)

    def restablecer_contrasena(
        self,
        token_original,
        nueva_contrasena,
        confirmar_contrasena
    ):
        """
        Valida el token y actualiza la contraseña del usuario.

        Después de completar el cambio, invalida los tokens
        de recuperación asociados al usuario.
        """

        token = self.validar_token(token_original)

        if token is None:
            raise ValueError(
                "El enlace de recuperación no es válido o ha expirado."
            )

        if not isinstance(nueva_contrasena, str):
            raise ValueError("La contraseña debe ser texto.")

        if not isinstance(confirmar_contrasena, str):
            raise ValueError(
                "La confirmación de contraseña debe ser texto."
            )

        if nueva_contrasena != confirmar_contrasena:
            raise ValueError("Las contraseñas no coinciden.")

        # Delegar la actualización al servicio de usuarios.
        self.usuario_service.restablecer_contrasena(
            token.usuario_id,
            nueva_contrasena
        )

        # Invalidar el token utilizado y cualquier otro pendiente.
        self.invalidar_tokens_usuario(token.usuario_id)

        return True