"""Pruebas de la ruta de "Me gusta" del feed (controllers/feed_routes.py)."""
import pytest

from application import create_app

TOKEN = "token-de-prueba"


@pytest.fixture
def app(tmp_path, monkeypatch):
    # Los repositorios guardan rutas relativas ("data/..."): trabajar dentro de
    # una carpeta temporal evita tocar los datos reales.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GMAIL_USER", "prueba@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "clave-de-prueba")

    return create_app({"TESTING": True})


@pytest.fixture
def servicios(app):
    return app.extensions["social_una"]


@pytest.fixture
def usuario(servicios):
    return servicios["usuario_service"].registrar_usuario(
        nombre="Ana Uno",
        nombre_usuario="anauno",
        correo="ana@example.com",
        contrasena="Clave1234!",
        confirmar_contrasena="Clave1234!",
    )


@pytest.fixture
def publicacion(servicios, usuario):
    return servicios["publicacion_service"].crear_publicacion(
        usuario.id, "hola"
    )


@pytest.fixture
def cliente(app, usuario):
    """Cliente con la sesión iniciada y un token CSRF conocido."""

    cliente = app.test_client()

    with cliente.session_transaction() as sesion:
        sesion["usuario_id"] = usuario.id
        sesion["csrf_feed"] = TOKEN

    return cliente


def url_me_gusta(publicacion_id):
    return f"/feed/me-gusta/{publicacion_id}"


def test_post_sin_token_devuelve_400(cliente, servicios, usuario, publicacion):
    respuesta = cliente.post(url_me_gusta(publicacion.id))

    assert respuesta.status_code == 400
    assert not servicios["reaccion_service"].ya_dio_me_gusta(
        usuario.id, publicacion.id
    )


def test_post_token_incorrecto_devuelve_400(
    cliente, servicios, usuario, publicacion
):
    respuesta = cliente.post(
        url_me_gusta(publicacion.id), data={"csrf_token": "otro-token"}
    )

    assert respuesta.status_code == 400
    assert not servicios["reaccion_service"].ya_dio_me_gusta(
        usuario.id, publicacion.id
    )


def test_post_token_valido_da_like_y_segundo_post_lo_quita(
    cliente, servicios, usuario, publicacion
):
    reacciones = servicios["reaccion_service"]

    primera = cliente.post(
        url_me_gusta(publicacion.id), data={"csrf_token": TOKEN}
    )

    assert primera.status_code == 302
    assert primera.headers["Location"].endswith(f"#post-{publicacion.id}")
    assert reacciones.contar_me_gusta(publicacion.id) == 1
    assert reacciones.ya_dio_me_gusta(usuario.id, publicacion.id)

    segunda = cliente.post(
        url_me_gusta(publicacion.id), data={"csrf_token": TOKEN}
    )

    assert segunda.status_code == 302
    assert reacciones.contar_me_gusta(publicacion.id) == 0
    assert not reacciones.ya_dio_me_gusta(usuario.id, publicacion.id)


def test_publicacion_inexistente_no_deja_nada_guardado(
    cliente, servicios, usuario
):
    reacciones = servicios["reaccion_service"]

    respuesta = cliente.post(
        url_me_gusta("no-existe"), data={"csrf_token": TOKEN}
    )

    assert respuesta.status_code == 302
    assert reacciones.contar_me_gusta("no-existe") == 0
    assert not reacciones.ya_dio_me_gusta(usuario.id, "no-existe")


def test_sin_sesion_redirige_al_inicio_de_sesion(app, publicacion):
    cliente_anonimo = app.test_client()

    respuesta = cliente_anonimo.post(
        url_me_gusta(publicacion.id), data={"csrf_token": TOKEN}
    )

    assert respuesta.status_code == 302
    assert "/feed/me-gusta" not in respuesta.headers["Location"]


def test_get_no_esta_permitido(cliente, publicacion):
    respuesta = cliente.get(url_me_gusta(publicacion.id))

    assert respuesta.status_code == 405