import json
import pytest

from repositories.reaccion_repository import ReaccionRepository
from models.reaccion import Reaccion


@pytest.fixture
def repositorio(tmp_path):
    ruta = tmp_path / "data" / "reacciones.json"
    return ReaccionRepository(ruta_archivo=ruta)


def _crear_reaccion(usuario_id="1", publicacion_id="1", tipo="me_gusta"):
    return Reaccion(usuario_id, publicacion_id, tipo, "2023-10-10T12:00:00")


def test_agregar_una_reaccion_y_existe(repositorio):
    reaccion = _crear_reaccion()
    assert repositorio.agregar(reaccion) is True
    assert repositorio.existe("1", "1") is True
    assert repositorio.contar("1") == 1


def test_agregar_reaccion_misma_clave_no_duplica(repositorio):
    reaccion = _crear_reaccion()
    assert repositorio.agregar(reaccion) is True
    assert repositorio.contar("1") == 1

    repeticion = _crear_reaccion()
    assert repositorio.agregar(reaccion) is False
    assert repositorio.contar("1") == 1


def test_eliminar_que_no_existe_devuelve_false_y_no_cambia_repositorio(repositorio):
    reaccion = _crear_reaccion()
    repositorio.agregar(reaccion)

    resultado = repositorio.eliminar("2", "999")

    assert resultado is False
    assert repositorio.existe("1", "1") is True
    assert repositorio.contar("1") == 1


def test_eliminar_existente_elimina_y_baja_contador(repositorio):
    reaccion = _crear_reaccion()
    repositorio.agregar(reaccion)

    resultado = repositorio.eliminar("1", "1")

    assert resultado is True
    assert repositorio.existe("1", "1") is False
    assert repositorio.contar("1") == 0


def test_publicaciones_de_usuario_sin_likes_devuelve_conjunto_vacio(repositorio):
    reaccion = _crear_reaccion(usuario_id="1", publicacion_id="1")
    repositorio.agregar(reaccion)

    publicaciones = repositorio.publicaciones_de("2")

    assert publicaciones == frozenset()


def test_carga_repositorio_desde_archivo_json_con_pareja_repetida_lanza_value_error(tmp_path):
    ruta = tmp_path / "data" / "reacciones.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)

    pareja_repetida = [
        {
            "usuario_id": "1",
            "publicacion_id": "1",
            "tipo": "me_gusta",
            "fecha": "2023-10-10T12:00:00",
        },
        {
            "usuario_id": "1",
            "publicacion_id": "1",
            "tipo": "me_gusta",
            "fecha": "2023-10-10T13:00:00",
        },
    ]

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(pareja_repetida, archivo, ensure_ascii=False, indent=4)

    with pytest.raises(ValueError) as excinfo:
        ReaccionRepository(ruta_archivo=ruta)

    assert "duplicada" in str(excinfo.value)
    assert "1" in str(excinfo.value)


def test_rollback_cuando_guardar_reacciones_falla(monkeypatch, tmp_path):
    ruta = tmp_path / "data" / "reacciones.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)

    repo = ReaccionRepository(ruta_archivo=ruta)

    def _guardar_fallida():
        raise OSError("Fallo en persistencia")

    monkeypatch.setattr(repo, "guardar_reacciones", _guardar_fallida)

    reaccion = _crear_reaccion()
    with pytest.raises(OSError):
        repo.agregar(reaccion)

    assert repo.existe("1", "1") is False
    assert repo.contar("1") == 0


def test_rollback_cuando_guardar_reacciones_falla_al_eliminar(monkeypatch, tmp_path):
    ruta = tmp_path / "data" / "reacciones.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)

    repo = ReaccionRepository(ruta_archivo=ruta)

    reaccion = _crear_reaccion()
    repo.agregar(reaccion)

    def _guardar_fallida():
        raise OSError("Fallo en persistencia")

    monkeypatch.setattr(repo, "guardar_reacciones", _guardar_fallida)

    with pytest.raises(OSError):
        repo.eliminar("1", "1")

    assert repo.existe("1", "1") is True
    assert repo.contar("1") == 1


def test_los_datos_persiten_entre_repositorios(tmp_path):
    ruta = tmp_path / "reacciones.json"

    primero = ReaccionRepository(ruta)
    primero.agregar(Reaccion("ana", "p1"))

    segundo = ReaccionRepository(ruta)

    assert segundo.existe("ana", "p1")
