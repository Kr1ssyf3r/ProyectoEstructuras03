"""Pruebas de la pantalla de Inicio con el feed (controllers/inicio_routes.py)."""
from datetime import datetime, timedelta

import pytest

from application import create_app


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


def crear_usuario(servicios, nombre, nombre_usuario):
    return servicios["usuario_service"].registrar_usuario(
        nombre=nombre,
        nombre_usuario=nombre_usuario,
        correo=f"{nombre_usuario}@example.com",
        contrasena="Clave1234!",
        confirmar_contrasena="Clave1234!",
    )


def hacer_amigos(servicios, emisor, receptor):
    amistades = servicios["amistad_service"]
    solicitud = amistades.enviar_solicitud(emisor.id, receptor.id)
    amistades.aceptar_solicitud(solicitud.id_solicitud, receptor.id)


def cliente_de(app, usuario):
    """Cliente de pruebas con la sesión de ese usuario ya iniciada."""

    cliente = app.test_client()

    with cliente.session_transaction() as sesion:
        sesion["usuario_id"] = usuario.id

    return cliente


def texto_de(respuesta):
    """HTML de la respuesta con los espacios y saltos de línea normalizados."""

    return " ".join(respuesta.get_data(as_text=True).split())


@pytest.fixture
def ana(servicios):
    return crear_usuario(servicios, "Ana Uno", "anauno")


@pytest.fixture
def luis(servicios, ana):
    luis = crear_usuario(servicios, "Luis Dos", "luisdos")
    hacer_amigos(servicios, ana, luis)
    return luis


@pytest.fixture
def eva(servicios):
    return crear_usuario(servicios, "Eva Tres", "evatres")


def test_feed_muestra_publicaciones_propias_y_de_amigos(
    app, servicios, ana, luis
):
    publicaciones = servicios["publicacion_service"]
    publicaciones.crear_publicacion(ana.id, "texto de ana")
    publicaciones.crear_publicacion(luis.id, "texto de luis")

    respuesta = cliente_de(app, ana).get("/inicio")
    pagina = texto_de(respuesta)

    assert respuesta.status_code == 200
    assert "texto de ana" in pagina
    assert "texto de luis" in pagina


def test_feed_no_muestra_publicaciones_de_desconocidos(
    app, servicios, ana, eva
):
    servicios["publicacion_service"].crear_publicacion(eva.id, "texto de eva")

    pagina = texto_de(cliente_de(app, ana).get("/inicio"))

    assert "texto de eva" not in pagina


def test_feed_ordena_de_la_mas_reciente_a_la_mas_antigua(
    app, servicios, ana, luis
):
    publicaciones = servicios["publicacion_service"]
    antigua = publicaciones.crear_publicacion(ana.id, "texto antiguo")
    reciente = publicaciones.crear_publicacion(luis.id, "texto reciente")

    # Se fijan las fechas a mano para que el orden no dependa del reloj.
    ahora = datetime(2026, 11, 1, 12, 0, 0)
    antigua.fecha = ahora - timedelta(hours=2)
    reciente.fecha = ahora

    pagina = texto_de(cliente_de(app, ana).get("/inicio"))

    assert pagina.index("texto reciente") < pagina.index("texto antiguo")


def test_boton_refleja_el_me_gusta_del_usuario_y_el_conteo(
    app, servicios, ana, luis
):
    publicaciones = servicios["publicacion_service"]
    con_like = publicaciones.crear_publicacion(luis.id, "con like")
    publicaciones.crear_publicacion(luis.id, "sin like")

    servicios["reaccion_service"].dar_me_gusta(ana.id, con_like.id)

    pagina = texto_de(cliente_de(app, ana).get("/inicio"))

    assert "Quitar me gusta · 1" in pagina
    assert "Me gusta · 0" in pagina


def test_feed_vacio_muestra_el_mensaje(app, eva):
    pagina = texto_de(cliente_de(app, eva).get("/inicio"))

    assert "Todavía no hay publicaciones" in pagina


def test_el_contenido_de_las_publicaciones_se_escapa(app, servicios, ana):
    publicacion = servicios["publicacion_service"].crear_publicacion(
        ana.id, "texto inofensivo"
    )
    # El servicio rechaza HTML al crear; se fuerza aquí para comprobar que la
    # plantilla lo escapa de todas formas (segunda barrera contra XSS).
    publicacion.contenido = "<b>negrita</b>"

    html = cliente_de(app, ana).get("/inicio").get_data(as_text=True)

    assert "&lt;b&gt;negrita&lt;/b&gt;" in html
    assert "<b>negrita</b>" not in html


def test_inicio_sin_sesion_redirige(app):
    respuesta = app.test_client().get("/inicio")

    assert respuesta.status_code == 302