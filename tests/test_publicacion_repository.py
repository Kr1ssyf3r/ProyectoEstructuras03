from datetime import datetime

import pytest

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


def test_guardar_no_deja_archivos_temporales(tmp_path):
    repositorio = PublicacionRepository(str(tmp_path / "publicaciones.json"))

    repositorio.guardar([Publicacion("id-1", "autor-1", "Hola")])

    assert [archivo.name for archivo in tmp_path.iterdir()] == ["publicaciones.json"]


def test_si_falla_el_guardado_el_archivo_original_queda_intacto(tmp_path, monkeypatch):
    repositorio = PublicacionRepository(str(tmp_path / "publicaciones.json"))
    repositorio.guardar([Publicacion("id-1", "autor-1", "Original")])

    # Se simula un fallo a mitad de la escritura
    def escritura_que_falla(*args, **kwargs):
        raise OSError("fallo simulado")

    monkeypatch.setattr("repositories.publicacion_repository.json.dump", escritura_que_falla)

    with pytest.raises(OSError):
        repositorio.guardar([Publicacion("id-2", "autor-1", "Nuevo")])

    monkeypatch.undo()
    cargadas = repositorio.cargar()
    assert len(cargadas) == 1
    assert cargadas[0].contenido == "Original"
    assert [archivo.name for archivo in tmp_path.iterdir()] == ["publicaciones.json"]