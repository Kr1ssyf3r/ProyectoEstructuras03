from datetime import datetime

from models.publicacion import Publicacion
from repositories.publicacion_repository import PublicacionRepository


def test_cargar_archivo_inexistente_devuelve_lista_vacia(tmp_path):
    repositorio = PublicacionRepository(str(tmp_path / "publicaciones.json"))

    assert repositorio.cargar() == []


def test_guardar_y_cargar_conserva_los_datos(tmp_path):
    repositorio = PublicacionRepository(str(tmp_path / "publicaciones.json"))
    original = Publicacion(
        "id-1", "autor-1", "Hola mundo", datetime(2026, 11, 8, 10, 30),
        archivo="foto.png", tipo_archivo="imagen",
    )

    repositorio.guardar([original])
    cargadas = repositorio.cargar()

    assert len(cargadas) == 1
    assert cargadas[0].id == "id-1"
    assert cargadas[0].autor_id == "autor-1"
    assert cargadas[0].contenido == "Hola mundo"
    assert cargadas[0].fecha == datetime(2026, 11, 8, 10, 30)
    assert cargadas[0].archivo == "foto.png"
    assert cargadas[0].tipo_archivo == "imagen"


def test_guardar_crea_la_carpeta_si_no_existe(tmp_path):
    ruta = tmp_path / "carpeta_nueva" / "publicaciones.json"
    repositorio = PublicacionRepository(str(ruta))

    repositorio.guardar([])

    assert ruta.exists()


def test_cargar_publicaciones_viejas_sin_foto(tmp_path):
    # Publicaciones guardadas antes de existir los campos de foto y video
    ruta = tmp_path / "publicaciones.json"
    ruta.write_text(
        '[{"id": "1", "autor_id": "a", "contenido": "x", "fecha": "2026-11-02T20:00:00"}]',
        encoding="utf-8",
    )

    cargadas = PublicacionRepository(str(ruta)).cargar()

    assert cargadas[0].archivo is None
    assert cargadas[0].tipo_archivo is None