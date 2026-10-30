
import pytest

from repositories.usuario_repository import UsuarioRepository
from services.usuario_service import UsuarioService


@pytest.fixture
def servicio(tmp_path, monkeypatch):
    monkeypatch.setattr(UsuarioService, "ITERACIONES_HASH", 1000)

    repositorio = UsuarioRepository(tmp_path / "usuarios.json")
    return UsuarioService(repositorio)


@pytest.fixture
def usuario_registrado(servicio):
    return servicio.registrar_usuario(
        nombre="Jose Quesada",
        nombre_usuario="akemi",
        correo="akemi@example.com",
        contrasena="Contrasena123",
        confirmar_contrasena="Contrasena123"
    )


def test_registrar_usuario_correctamente(servicio):
    usuario = servicio.registrar_usuario(
        "Jose Quesada",
        "akemi",
        "akemi@example.com",
        "Contrasena123",
        "Contrasena123"
    )

    assert usuario.nombre == "Jose Quesada"
    assert usuario.usuario == "akemi"
    assert usuario.correo == "akemi@example.com"
    assert usuario.id is not None


def test_registrar_usuario_guarda_hash_y_no_contrasena(
    servicio, usuario_registrado
):
    assert usuario_registrado.contrasena_hash != "Contrasena123"
    assert usuario_registrado.contrasena_hash.startswith("pbkdf2_sha256$")


def test_registrar_usuario_normaliza_datos(servicio):
    usuario = servicio.registrar_usuario(
        "  Jose Quesada  ",
        "  Akemi  ",
        "  AKEMI@EXAMPLE.COM  ",
        "Contrasena123",
        "Contrasena123"
    )

    assert usuario.nombre == "Jose Quesada"
    assert usuario.usuario == "Akemi"
    assert usuario.correo == "akemi@example.com"


def test_rechazar_campos_vacios(servicio):
    with pytest.raises(ValueError):
        servicio.registrar_usuario(
            "",
            "akemi",
            "akemi@example.com",
            "Contrasena123",
            "Contrasena123"
        )


def test_rechazar_nombre_usuario_con_espacios(servicio):
    with pytest.raises(ValueError, match="espacios"):
        servicio.registrar_usuario(
            "Jose Quesada",
            "akemi quesada",
            "akemi@example.com",
            "Contrasena123",
            "Contrasena123"
        )


def test_rechazar_contrasena_corta(servicio):
    with pytest.raises(ValueError, match="8 caracteres"):
        servicio.registrar_usuario(
            "Jose Quesada",
            "akemi",
            "akemi@example.com",
            "1234567",
            "1234567"
        )


def test_rechazar_contrasenas_diferentes(servicio):
    with pytest.raises(ValueError, match="no coinciden"):
        servicio.registrar_usuario(
            "Jose Quesada",
            "akemi",
            "akemi@example.com",
            "Contrasena123",
            "OtraContrasena123"
        )


def test_rechazar_nombre_usuario_duplicado(
    servicio, usuario_registrado
):
    with pytest.raises(ValueError, match="nombre de usuario"):
        servicio.registrar_usuario(
            "Otro nombre",
            "AKEMI",
            "otro@example.com",
            "Contrasena123",
            "Contrasena123"
        )


def test_rechazar_correo_duplicado(servicio, usuario_registrado):
    with pytest.raises(ValueError, match="correo"):
        servicio.registrar_usuario(
            "Otro nombre",
            "otro_usuario",
            "AKEMI@example.com",
            "Contrasena123",
            "Contrasena123"
        )


def test_validar_credenciales_correctas(
    servicio, usuario_registrado
):
    resultado = servicio.validar_credenciales(
        "akemi",
        "Contrasena123"
    )

    assert resultado == usuario_registrado


def test_rechazar_contrasena_incorrecta(
    servicio, usuario_registrado
):
    resultado = servicio.validar_credenciales(
        "akemi",
        "ContrasenaIncorrecta"
    )

    assert resultado is None


def test_rechazar_usuario_inexistente(servicio):
    resultado = servicio.validar_credenciales(
        "inexistente",
        "Contrasena123"
    )

    assert resultado is None


def test_iniciar_sesion_correctamente(
    servicio, usuario_registrado
):
    resultado = servicio.iniciar_sesion(
        "akemi",
        "Contrasena123"
    )

    assert resultado == usuario_registrado
    assert servicio.obtener_usuario_activo() == usuario_registrado


def test_no_iniciar_sesion_con_credenciales_incorrectas(
    servicio, usuario_registrado
):
    with pytest.raises(ValueError, match="incorrectos"):
        servicio.iniciar_sesion(
            "akemi",
            "ContrasenaIncorrecta"
        )

    assert servicio.obtener_usuario_activo() is None


def test_cerrar_sesion(servicio, usuario_registrado):
    servicio.iniciar_sesion("akemi", "Contrasena123")

    servicio.cerrar_sesion()

    assert servicio.obtener_usuario_activo() is None


def test_obtener_usuario_por_id(servicio, usuario_registrado):
    resultado = servicio.obtener_usuario(usuario_registrado.id)

    assert resultado == usuario_registrado


def test_hash_diferente_para_misma_contrasena(servicio):
    hash1 = servicio._generar_hash("Contrasena123")
    hash2 = servicio._generar_hash("Contrasena123")

    assert hash1 != hash2


def test_verificar_hash_correcto(servicio):
    hash_contrasena = servicio._generar_hash("Contrasena123")

    assert servicio._verificar_contrasena(
        "Contrasena123",
        hash_contrasena
    ) is True


def test_verificar_hash_incorrecto(servicio):
    hash_contrasena = servicio._generar_hash("Contrasena123")

    assert servicio._verificar_contrasena(
        "OtraContrasena123",
        hash_contrasena
    ) is False


def test_rechazar_hash_malformado(servicio):
    assert servicio._verificar_contrasena(
        "Contrasena123",
        "hash_invalido"
    ) is False
