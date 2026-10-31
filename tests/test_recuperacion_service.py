import pytest

from datetime import datetime, timedelta, timezone

from repositories.usuario_repository import UsuarioRepository
from repositories.token_repository import TokenRepository
from services.usuario_service import UsuarioService
from services.recuperacion_service import RecuperacionService


@pytest.fixture
def servicios(tmp_path):
    """Prepara los repositorios y servicios para cada prueba."""

    ruta_usuarios = tmp_path / "usuarios.json"
    ruta_tokens = tmp_path / "tokens_recuperacion.json"

    usuario_repository = UsuarioRepository(
        ruta_archivo=str(ruta_usuarios)
    )

    usuario_service = UsuarioService(
        repositorio=usuario_repository
    )

    token_repository = TokenRepository(
        ruta=str(ruta_tokens)
    )

    recuperacion_service = RecuperacionService(
        token_repository=token_repository,
        usuario_service=usuario_service
    )

    usuario = usuario_service.registrar_usuario(
        nombre="Usuario de Prueba",
        nombre_usuario="usuario_prueba",
        correo="prueba@correo.com",
        contrasena="Contrasena123",
        confirmar_contrasena="Contrasena123"
    )

    return {
        "usuario": usuario,
        "usuario_repository": usuario_repository,
        "usuario_service": usuario_service,
        "token_repository": token_repository,
        "recuperacion_service": recuperacion_service
    }


def test_generar_token_recuperacion(servicios):
    """Comprueba que se genere y almacene un token válido."""

    recuperacion = servicios["recuperacion_service"]
    token_repository = servicios["token_repository"]
    usuario = servicios["usuario"]

    token_original = recuperacion.generar_token(usuario.id)

    assert isinstance(token_original, str)
    assert len(token_original) > 0

    token_hash = recuperacion.generar_hash(token_original)

    token_guardado = token_repository.buscar_por_hash(token_hash)

    assert token_guardado is not None
    assert token_guardado.usuario_id == usuario.id
    assert token_guardado.usado is False
    assert token_guardado.token_hash != token_original


def test_validar_token_correcto(servicios):
    """Comprueba que un token recién generado sea válido."""

    recuperacion = servicios["recuperacion_service"]
    usuario = servicios["usuario"]

    token_original = recuperacion.generar_token(usuario.id)

    token = recuperacion.validar_token(token_original)

    assert token is not None
    assert token.usuario_id == usuario.id


def test_rechazar_token_inexistente(servicios):
    """Comprueba que se rechace un token que no existe."""

    recuperacion = servicios["recuperacion_service"]

    assert recuperacion.validar_token("token_inexistente") is None


def test_rechazar_token_expirado(servicios):
    """Comprueba que se rechace un token cuya vigencia terminó."""

    recuperacion = servicios["recuperacion_service"]
    token_repository = servicios["token_repository"]
    usuario = servicios["usuario"]

    token_original = recuperacion.generar_token(usuario.id)

    token_hash = recuperacion.generar_hash(token_original)
    token = token_repository.buscar_por_hash(token_hash)

    # Establecer una fecha de expiración en el pasado.
    fecha_pasada = datetime.now(timezone.utc) - timedelta(minutes=1)
    token.fecha_expiracion = fecha_pasada.isoformat()

    token_repository.guardar(token)

    assert recuperacion.validar_token(token_original) is None


def test_rechazar_token_utilizado(servicios):
    """Comprueba que un token utilizado no pueda volver a validarse."""

    recuperacion = servicios["recuperacion_service"]
    token_repository = servicios["token_repository"]
    usuario = servicios["usuario"]

    token_original = recuperacion.generar_token(usuario.id)

    token_hash = recuperacion.generar_hash(token_original)
    token = token_repository.buscar_por_hash(token_hash)

    token.usado = True
    token_repository.guardar(token)

    assert recuperacion.validar_token(token_original) is None


def test_invalidar_tokens_anteriores(servicios):
    """Comprueba que una nueva solicitud invalide los tokens anteriores."""

    recuperacion = servicios["recuperacion_service"]
    token_repository = servicios["token_repository"]
    usuario = servicios["usuario"]

    primer_token = recuperacion.generar_token(usuario.id)

    segundo_token = recuperacion.generar_token(usuario.id)

    assert recuperacion.validar_token(primer_token) is None
    assert recuperacion.validar_token(segundo_token) is not None

    tokens = token_repository.obtener_por_usuario(usuario.id)

    assert len(tokens) == 2
    assert all(token.usado for token in tokens if token.token_hash ==
               recuperacion.generar_hash(primer_token))
    assert any(not token.usado for token in tokens)


def test_restaurar_contrasena_correctamente(servicios):
    """Comprueba que se pueda cambiar la contraseña con un token válido."""

    recuperacion = servicios["recuperacion_service"]
    usuario_service = servicios["usuario_service"]
    usuario = servicios["usuario"]

    token_original = recuperacion.generar_token(usuario.id)

    resultado = recuperacion.restablecer_contrasena(
        token_original,
        "NuevaContrasena123",
        "NuevaContrasena123"
    )

    assert resultado is True

    # La contraseña anterior ya no debe funcionar.
    assert usuario_service.validar_credenciales(
        "usuario_prueba",
        "Contrasena123"
    ) is None

    # La contraseña nueva debe funcionar.
    usuario_actualizado = usuario_service.validar_credenciales(
        "usuario_prueba",
        "NuevaContrasena123"
    )

    assert usuario_actualizado is not None
    assert usuario_actualizado.id == usuario.id


def test_token_no_puede_reutilizarse(servicios):
    """Comprueba que el token no pueda utilizarse dos veces."""

    recuperacion = servicios["recuperacion_service"]
    usuario = servicios["usuario"]

    token_original = recuperacion.generar_token(usuario.id)

    recuperacion.restablecer_contrasena(
        token_original,
        "NuevaContrasena123",
        "NuevaContrasena123"
    )

    with pytest.raises(ValueError):
        recuperacion.restablecer_contrasena(
            token_original,
            "OtraContrasena123",
            "OtraContrasena123"
        )


def test_rechazar_contrasenas_diferentes(servicios):
    """Comprueba que se rechacen contraseñas que no coinciden."""

    recuperacion = servicios["recuperacion_service"]
    usuario = servicios["usuario"]

    token_original = recuperacion.generar_token(usuario.id)

    with pytest.raises(ValueError, match="no coinciden"):
        recuperacion.restablecer_contrasena(
            token_original,
            "NuevaContrasena123",
            "OtraContrasena123"
        )

    # El token debe seguir disponible porque no se completó el cambio.
    assert recuperacion.validar_token(token_original) is not None


def test_rechazar_contrasena_corta(servicios):
    """Comprueba que se respete la longitud mínima de contraseña."""

    recuperacion = servicios["recuperacion_service"]
    usuario = servicios["usuario"]

    token_original = recuperacion.generar_token(usuario.id)

    with pytest.raises(ValueError, match="al menos"):
        recuperacion.restablecer_contrasena(
            token_original,
            "123",
            "123"
        )

    assert recuperacion.validar_token(token_original) is not None


def test_rechazar_usuario_inexistente(servicios):
    """Comprueba que no se generen tokens para usuarios inexistentes."""

    recuperacion = servicios["recuperacion_service"]

    with pytest.raises(ValueError, match="No se encontró"):
        recuperacion.generar_token(
            "00000000-0000-4000-8000-000000000000"
        )