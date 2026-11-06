import pytest
from models.reaccion import Reaccion
from repositories.reaccion_repository import ReaccionRepository

@pytest.fixture
def reaccion():
    return Reaccion("1", "1", "me_gusta", "2023-10-10T12:00:00")

def test_crear_reaccion(reaccion):
    assert reaccion.usuario_id == "1"
    assert reaccion.publicacion_id == "1"
    assert reaccion.tipo == "me_gusta"
    assert reaccion.fecha == "2023-10-10T12:00:00"

def test_reaccion_to_dict_y_from_dict_recuperan_la_misma_reaccion(reaccion):
    dict_reaccion = reaccion.to_dict()
    reaccion_recuperada = Reaccion.from_dict(dict_reaccion)
    assert reaccion_recuperada.to_dict() == dict_reaccion
    
def test_reaccion_tipo_invalido():
    with pytest.raises(ValueError) as excinfo:
        Reaccion("1", "1", "tipo_invalido", "2023-10-10T12:00:00")
    assert "no es válido" in str(excinfo.value)

def test_reaccion_fecha_invalida():
    with pytest.raises(ValueError) as excinfo:
        Reaccion("1", "1", "me_gusta", "fecha_invalida")
    assert "debe estar en formato ISO 8601" in str(excinfo.value)
@pytest.fixture
def reaccion_valida():
    return Reaccion("1", "1", "me_gusta", "2023-10-10T12:00:00")


def test_to_dict_devuelve_campos_correctos(reaccion_valida):
    dato = reaccion_valida.to_dict()
    assert dato["usuario_id"] == "1"
    assert dato["publicacion_id"] == "1"
    assert dato["tipo"] == "me_gusta"
    assert dato["fecha"] == "2023-10-10T12:00:00"


def test_from_dict_recupera_la_misma_reaccion(reaccion_valida):
    dato = reaccion_valida.to_dict()
    reaccion_recuperada = Reaccion.from_dict(dato)
    assert reaccion_recuperada.to_dict() == dato



@pytest.mark.parametrize(
    "usuario_id, publicacion_id, tipo, fecha",
    [
        ("", "", "", ""),
        ("1", "", "", ""),
        ("", "1", "", ""),
        ("", "", "me_gusta", ""),
        ("", "", "", "2023-10-10T12:00:00"),
    ],
)
def test_datos_vacios_parametrizada(usuario_id, publicacion_id, tipo, fecha):
    """Verifica que los campos vacíos lance ValueError y se mantengan vacíos."""
    with pytest.raises(ValueError):
        Reaccion(usuario_id, publicacion_id, tipo, fecha)


@pytest.mark.parametrize(
    "usuario_id, publicacion_id, tipo, fecha",
    [
        (1, "1", "me_gusta", "2023-10-10T12:00:00"),
        ("1", 1, "me_gusta", "2023-10-10T12:00:00"),
        ("1", "1", 1, "2023-10-10T12:00:00"),
        ("1", "1", "me_gusta", 1),
        ("1", None, "me_gusta", "2023-10-10T12:00:00"),
        ("1", "1", None, "2023-10-10T12:00:00"),
        ("1", "1", "me_gusta", None),
    ],
)
def test_tipo_no_string_lanza_tipo_error(usuario_id, publicacion_id, tipo, fecha):
    with pytest.raises(TypeError):
        Reaccion(usuario_id, publicacion_id, tipo, fecha)

@pytest.mark.parametrize(
    "tipo",
    [
        "me_gusta_extra",
        "like",
        "heart",
        "dislike",
        "follow",
    ],
)
def test_tipo_invalido_lanza_value_error(tipo):
    with pytest.raises(ValueError) as excinfo:
        Reaccion("1", "1", tipo, "2023-10-10T12:00:00")
    assert "no es válido" in str(excinfo.value)

@pytest.mark.parametrize(
    "fecha",
    [
        "2023/10/10",
        "10-10-2023",
        "2023-13-01T12:00:00",  # mes fuera de rango
        "2023-10-10T25:00:00",  # hora fuera de rango
    ],
)
def test_fecha_invalida_lanza_value_error(fecha):
    with pytest.raises(ValueError) as excinfo:
        Reaccion("1", "1", "me_gusta", fecha)
    assert "ISO 8601" in str(excinfo.value)

def test_to_dict_devuelve_campos_correctos(reaccion_valida):
    dato = reaccion_valida.to_dict()
    assert dato["usuario_id"] == "1"
    assert dato["publicacion_id"] == "1"
    assert dato["tipo"] == "me_gusta"
    assert dato["fecha"] == "2023-10-10T12:00:00"


def test_from_dict_recupera_la_misma_reaccion(reaccion_valida):
    dato = reaccion_valida.to_dict()
    reaccion_recuperada = Reaccion.from_dict(dato)
    assert reaccion_recuperada.to_dict() == dato

def test_from_dict_con_campos_faltantes_usa_valores_por_defecto():
    dato = {
        "usuario_id": "1",
        "publicacion_id": "1",
        # tipo y fecha no están
    }
    reaccion = Reaccion.from_dict(dato)
    assert reaccion.usuario_id == "1"
    assert reaccion.publicacion_id == "1"
    assert reaccion.tipo == "me_gusta"
    # fecha usará el valor por defecto generado en el modelo
    from datetime import datetime
    datetime.fromisoformat(reaccion.fecha)
