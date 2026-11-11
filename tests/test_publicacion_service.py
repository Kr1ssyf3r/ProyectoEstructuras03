import io
import os
from datetime import datetime

import pytest

from repositories.usuario_repository import UsuarioRepository
from repositories.publicacion_repository import PublicacionRepository
from services.usuario_service import UsuarioService
from services.publicacion_service import PublicacionService


class ArchivoFalso:
    """Imita un archivo subido desde el formulario (tiene filename, stream y save)."""

    def __init__(self, nombre, contenido=b"datos"):
        self.filename = nombre
        self.stream = io.BytesIO(contenido)

    def save(self, ruta):
        with open(ruta, "wb") as destino:
            destino.write(self.stream.read())


@pytest.fixture
def servicios(tmp_path):
    """Prepara servicios nuevos (y archivos temporales) para cada prueba."""

    usuario_service = UsuarioService(
        repositorio=UsuarioRepository(ruta_archivo=str(tmp_path / "usuarios.json"))
    )
    ruta_json = str(tmp_path / "publicaciones.json")
    carpeta_media = str(tmp_path / "uploads")

    publicacion_service = PublicacionService(
        usuario_service,
        repositorio=PublicacionRepository(ruta_json),
        carpeta_media=carpeta_media,
    )
    ana = usuario_service.registrar_usuario(
        nombre="Ana Mora",
        nombre_usuario="ana",
        correo="ana@correo.com",
        contrasena="Contrasena123",
        confirmar_contrasena="Contrasena123",
    )
    beto = usuario_service.registrar_usuario(
        nombre="Beto Solis",
        nombre_usuario="beto",
        correo="beto@correo.com",
        contrasena="Contrasena123",
        confirmar_contrasena="Contrasena123",
    )
    return {
        "servicio": publicacion_service,
        "usuario": ana,
        "otro": beto,
        "ruta_json": ruta_json,
        "carpeta_media": carpeta_media,
        "usuario_service": usuario_service,
    }


# ---------- Crear ----------

def test_crear_publicacion(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]

    publicacion = servicio.crear_publicacion(usuario.id, "Mi primera publicación")

    assert publicacion.contenido == "Mi primera publicación"
    assert publicacion.autor_id == usuario.id
    assert servicio.obtener_publicacion(publicacion.id) is publicacion


def test_no_permite_publicacion_vacia(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]

    with pytest.raises(ValueError):
        servicio.crear_publicacion(usuario.id, "   ")


def test_no_permite_mas_de_500_caracteres(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]

    # 500 exactos sí se permiten
    servicio.crear_publicacion(usuario.id, "a" * 500)

    # 501 no
    with pytest.raises(ValueError):
        servicio.crear_publicacion(usuario.id, "a" * 501)


def test_no_permite_usuario_inexistente(servicios):
    servicio = servicios["servicio"]

    with pytest.raises(ValueError):
        servicio.crear_publicacion("id-que-no-existe", "Hola")


def test_rechaza_etiquetas_html(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]

    with pytest.raises(ValueError):
        servicio.crear_publicacion(usuario.id, "<script>alert(1)</script>")


def test_rechaza_palabras_prohibidas(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]

    with pytest.raises(ValueError):
        servicio.crear_publicacion(usuario.id, "eres un ESTÚPIDO")


def test_los_ids_son_unicos(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]

    primera = servicio.crear_publicacion(usuario.id, "Una")
    servicio.eliminar_publicacion(primera.id, usuario.id)
    segunda = servicio.crear_publicacion(usuario.id, "Dos")

    # Un id borrado nunca se vuelve a usar
    assert segunda.id != primera.id


# ---------- Consultar ----------

def test_obtener_publicaciones_de_un_usuario(servicios):
    servicio = servicios["servicio"]
    ana = servicios["usuario"]
    beto = servicios["otro"]

    servicio.crear_publicacion(ana.id, "De Ana 1")
    servicio.crear_publicacion(ana.id, "De Ana 2")
    servicio.crear_publicacion(beto.id, "De Beto")

    textos_ana = [p.contenido for p in servicio.obtener_publicaciones_usuario(ana.id)]

    assert len(textos_ana) == 2
    assert "De Beto" not in textos_ana


def test_usuario_sin_publicaciones_devuelve_lista_vacia(servicios):
    servicio = servicios["servicio"]

    assert servicio.obtener_publicaciones_usuario(servicios["usuario"].id) == []


def test_orden_de_la_mas_reciente_a_la_mas_antigua(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]

    primera = servicio.crear_publicacion(usuario.id, "Primera")
    segunda = servicio.crear_publicacion(usuario.id, "Segunda")
    tercera = servicio.crear_publicacion(usuario.id, "Tercera")

    # Fechas fijas para que la prueba no dependa del reloj
    primera.fecha = datetime(2026, 1, 1, 10, 0)
    segunda.fecha = datetime(2026, 1, 1, 11, 0)
    tercera.fecha = datetime(2026, 1, 1, 12, 0)

    textos = [p.contenido for p in servicio.obtener_publicaciones_usuario(usuario.id)]

    assert textos == ["Tercera", "Segunda", "Primera"]


# ---------- Editar ----------

def test_editar_publicacion_propia(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]
    publicacion = servicio.crear_publicacion(usuario.id, "Texto original")

    servicio.editar_publicacion(publicacion.id, usuario.id, "Texto nuevo")

    assert servicio.obtener_publicacion(publicacion.id).contenido == "Texto nuevo"


def test_no_permite_editar_publicacion_ajena(servicios):
    servicio = servicios["servicio"]
    ana = servicios["usuario"]
    beto = servicios["otro"]
    publicacion = servicio.crear_publicacion(ana.id, "Texto de Ana")

    with pytest.raises(ValueError):
        servicio.editar_publicacion(publicacion.id, beto.id, "Hackeado")

    assert servicio.obtener_publicacion(publicacion.id).contenido == "Texto de Ana"


def test_no_permite_editar_dejando_el_texto_vacio(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]
    publicacion = servicio.crear_publicacion(usuario.id, "Texto")

    with pytest.raises(ValueError):
        servicio.editar_publicacion(publicacion.id, usuario.id, "  ")


# ---------- Eliminar ----------

def test_eliminar_publicacion_propia(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]
    publicacion = servicio.crear_publicacion(usuario.id, "Para borrar")

    servicio.eliminar_publicacion(publicacion.id, usuario.id)

    assert servicio.obtener_publicacion(publicacion.id) is None
    assert servicio.obtener_publicaciones_usuario(usuario.id) == []


def test_no_permite_eliminar_publicacion_ajena(servicios):
    servicio = servicios["servicio"]
    ana = servicios["usuario"]
    beto = servicios["otro"]
    publicacion = servicio.crear_publicacion(ana.id, "De Ana")

    with pytest.raises(ValueError):
        servicio.eliminar_publicacion(publicacion.id, beto.id)

    assert servicio.obtener_publicacion(publicacion.id) is not None


def test_eliminar_publicacion_que_no_existe(servicios):
    servicio = servicios["servicio"]

    with pytest.raises(ValueError):
        servicio.eliminar_publicacion("no-existe", servicios["usuario"].id)


# ---------- Fotos y videos ----------

def test_rechaza_formato_de_archivo_no_permitido(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]

    with pytest.raises(ValueError):
        servicio.crear_publicacion(usuario.id, "Hola", ArchivoFalso("virus.exe"))


def test_guarda_foto_y_la_borra_al_eliminar(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]

    publicacion = servicio.crear_publicacion(usuario.id, "Con foto", ArchivoFalso("foto.png"))
    ruta = os.path.join(servicios["carpeta_media"], publicacion.archivo)

    assert publicacion.tipo_archivo == "imagen"
    assert os.path.exists(ruta)

    servicio.eliminar_publicacion(publicacion.id, usuario.id)

    assert not os.path.exists(ruta)


def test_se_puede_publicar_solo_con_foto_sin_texto(servicios):
    servicio = servicios["servicio"]
    usuario = servicios["usuario"]

    publicacion = servicio.crear_publicacion(usuario.id, "", ArchivoFalso("foto.jpg"))

    assert publicacion.contenido == ""
    assert publicacion.archivo is not None


# ---------- Persistencia ----------

def test_las_publicaciones_se_guardan_y_se_cargan_al_reiniciar(servicios):
    servicio = servicios["servicio"]
    ana = servicios["usuario"]
    beto = servicios["otro"]
    servicio.crear_publicacion(ana.id, "De Ana 1")
    servicio.crear_publicacion(ana.id, "De Ana 2")
    servicio.crear_publicacion(beto.id, "De Beto")

    # Un servicio nuevo, leyendo el mismo archivo JSON, simula reiniciar la app
    reiniciado = PublicacionService(
        servicios["usuario_service"],
        repositorio=PublicacionRepository(servicios["ruta_json"]),
        carpeta_media=servicios["carpeta_media"],
    )

    assert len(reiniciado.obtener_publicaciones_usuario(ana.id)) == 2
    assert len(reiniciado.obtener_publicaciones_usuario(beto.id)) == 1
    # Los dos diccionarios se reconstruyen
    assert len(reiniciado.publicaciones_por_id) == 3
    assert len(reiniciado.ids_por_usuario[ana.id]) == 2