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

    def validar_credenciales(self, nombre_usuario, contrasena):
        """Comprueba las credenciales y devuelve el usuario si son válidas."""

        if not isinstance(nombre_usuario, str):
            return None

        if not isinstance(contrasena, str):
            return None

        if not nombre_usuario.strip() or not contrasena.strip():
            return None

        usuario = self.repositorio.buscar_por_nombre(
            nombre_usuario.strip()
        )

        if usuario is None:
            return None

        if not self._verificar_contrasena(
            contrasena,
            usuario.contrasena_hash
        ):
            return None

        return usuario

    def iniciar_sesion(self, nombre_usuario, contrasena):
        """Inicia la sesión de un usuario."""

        usuario = self.validar_credenciales(
            nombre_usuario,
            contrasena
        )

        if usuario is None:
            raise ValueError(
                "Nombre de usuario o contraseña incorrectos."
            )

        self.usuario_activo = usuario

        return usuario

    def cerrar_sesion(self):
        """Cierra la sesión actual."""

        self.usuario_activo = None

    def obtener_usuario(self, id_usuario):
        """Obtiene un usuario mediante su ID."""

        return self.repositorio.buscar_por_id(id_usuario)

    def obtener_usuario_activo(self):
        """Devuelve el usuario que tiene la sesión iniciada."""

        return self.usuario_activo

    
    def restablecer_contrasena(self, id_usuario, nueva_contrasena):
        """Actualiza la contraseña de un usuario mediante su ID."""

        self._validar_cadena(
            nueva_contrasena,
            "contraseña"
        )

        if len(nueva_contrasena) < self.LONGITUD_MINIMA_CONTRASENA:
            raise ValueError(
                f"La contraseña debe tener al menos "
                f"{self.LONGITUD_MINIMA_CONTRASENA} caracteres."
            )

        usuario = self.repositorio.buscar_por_id(id_usuario)

        if usuario is None:
            raise ValueError("No se encontró el usuario.")

        # Generar un nuevo hash con un salt aleatorio.
        usuario.contrasena_hash = self._generar_hash(nueva_contrasena)

        # Persistir la actualización del usuario.
        self.repositorio.actualizar(usuario)

        return usuario

    def actualizar_perfil(
            self,
            id_usuario,
            nombre,
            nombre_usuario,
            correo
        ):
            """Actualiza los datos personales de un usuario."""

            campos = [
                (nombre, "nombre"),
                (nombre_usuario, "nombre de usuario"),
                (correo, "correo")
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

            if "@" not in correo or "." not in correo.split("@")[-1]:
                raise ValueError("El correo electrónico no es válido.")

            usuario_anterior = self.repositorio.buscar_por_id(id_usuario)

            if usuario_anterior is None:
                raise ValueError("No se encontró el usuario.")

            usuario_existente = self.repositorio.buscar_por_nombre(
                nombre_usuario
            )

            if (
                usuario_existente is not None
                and usuario_existente.id != id_usuario
            ):
                raise ValueError(
                    "Ese nombre de usuario ya está registrado."
                )

            correo_existente = self.repositorio.buscar_por_correo(correo)

            if (
                correo_existente is not None
                and correo_existente.id != id_usuario
            ):
                raise ValueError(
                    "Ese correo electrónico ya está registrado."
                )

            # Crear un objeto nuevo para conservar los datos anteriores
            # mientras el repositorio actualiza sus índices.
            usuario_actualizado = Usuario(
                id=usuario_anterior.id,
                nombre=nombre,
                usuario=nombre_usuario,
                correo=correo,
                contrasena_hash=usuario_anterior.contrasena_hash,
                fecha_registro=usuario_anterior.fecha_registro
            )

            self.repositorio.actualizar(usuario_actualizado)

            return usuario_actualizado