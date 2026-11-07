"""Pruebas de la pantalla de Inicio con el feed (controllers/inicio_routes.py)."""
from datetime import datetime, timedelta

import pytest
import re

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

def test_inicio_tiene_boton_para_actualizar_el_feed(app, ana):
    html = cliente_de(app, ana).get("/inicio").get_data(as_text=True)

    boton = re.search(r"<a[^>]*btn-actualizar[^>]*>", html)

    assert boton is not None
    assert 'href="/inicio"' in boton.group(0)


def test_publicacion_nueva_aparece_al_actualizar(app, servicios, ana, luis):
    cliente = cliente_de(app, ana)

    assert "publicación nueva" not in texto_de(cliente.get("/inicio"))

    servicios["publicacion_service"].crear_publicacion(
        luis.id, "publicación nueva"
    )

    assert "publicación nueva" in texto_de(cliente.get("/inicio"))

def test_filtro_muestra_solo_las_publicaciones_del_autor(
    app, servicios, ana, luis
):
    publicaciones = servicios["publicacion_service"]
    publicaciones.crear_publicacion(ana.id, "texto de ana")
    publicaciones.crear_publicacion(luis.id, "texto de luis")

    pagina = texto_de(cliente_de(app, ana).get(f"/inicio?autor={luis.id}"))

    assert "texto de luis" in pagina
    assert "texto de ana" not in pagina
    assert "Mostrando solo las publicaciones de" in pagina
    assert "Ver todas" in pagina


def test_filtro_por_uno_mismo_muestra_solo_lo_propio(
    app, servicios, ana, luis
):
    publicaciones = servicios["publicacion_service"]
    publicaciones.crear_publicacion(ana.id, "texto de ana")
    publicaciones.crear_publicacion(luis.id, "texto de luis")

    pagina = texto_de(cliente_de(app, ana).get(f"/inicio?autor={ana.id}"))

    assert "texto de ana" in pagina
    assert "texto de luis" not in pagina


def test_filtro_por_un_desconocido_avisa_y_muestra_el_feed_normal(
    app, servicios, ana, luis, eva
):
    publicaciones = servicios["publicacion_service"]
    publicaciones.crear_publicacion(luis.id, "texto de luis")
    publicaciones.crear_publicacion(eva.id, "texto de eva")
    cliente = cliente_de(app, ana)

    respuesta = cliente.get(f"/inicio?autor={eva.id}")

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/inicio")

    pagina = texto_de(cliente.get("/inicio"))

    assert "Solo puedes ver publicaciones tuyas o de tus amigos." in pagina
    assert "texto de eva" not in pagina
    assert "texto de luis" in pagina


def test_filtro_con_un_autor_inexistente_redirige(app, ana):
    respuesta = cliente_de(app, ana).get("/inicio?autor=no-existe")

    assert respuesta.status_code == 302


def test_boton_actualizar_conserva_el_filtro(app, ana, luis):
    html = cliente_de(app, ana).get(f"/inicio?autor={luis.id}").get_data(
        as_text=True
    )

    boton = re.search(r"<a[^>]*btn-actualizar[^>]*>", html)

    assert boton is not None
    assert f"autor={luis.id}" in boton.group(0)


def test_filtro_sin_publicaciones_muestra_el_mensaje_del_autor(
    app, ana, luis
):
    pagina = texto_de(cliente_de(app, ana).get(f"/inicio?autor={luis.id}"))

    assert "Luis Dos todavía no ha publicado" in pagina


def test_el_nombre_del_autor_enlaza_al_filtro(app, servicios, ana, luis):
    servicios["publicacion_service"].crear_publicacion(luis.id, "hola")

    html = cliente_de(app, ana).get("/inicio").get_data(as_text=True)

    assert f'href="/inicio?autor={luis.id}"' in html


def test_los_errores_del_me_gusta_se_muestran_en_inicio(app, ana):
    cliente = cliente_de(app, ana)

    with cliente.session_transaction() as sesion:
        sesion["csrf_feed"] = "token-de-prueba"

    cliente.post(
        "/feed/me-gusta/no-existe", data={"csrf_token": "token-de-prueba"}
    )

    pagina = texto_de(cliente.get("/inicio"))

    assert "La publicación no existe." in pagina