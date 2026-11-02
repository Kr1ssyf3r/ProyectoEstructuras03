
import json
import uuid

import pytest

from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository


@pytest.fixture
def repositorio(tmp_path):
    ruta = tmp_path / "usuarios.json"
    return UsuarioRepository(ruta)


@pytest.fixture
def usuario():
    return Usuario(
        id=str(uuid.uuid4()),
        nombre="Jose Quesada",
        usuario="akemi",
        correo="akemi@example.com",
        contrasena_hash="hash_de_prueba"
    )


def test_crear_archivo_json_si_no_existe(tmp_path):
    ruta = tmp_path / "usuarios.json"

    UsuarioRepository(ruta)

    assert ruta.exists()
    assert json.loads(ruta.read_text(encoding="utf-8")) == []


def test_guardar_usuario(repositorio, usuario):
    resultado = repositorio.guardar(usuario)

    assert resultado == usuario
    assert repositorio.buscar_por_id(usuario.id) == usuario
    assert repositorio.buscar_por_nombre("akemi") == usuario
    assert repositorio.buscar_por_correo("akemi@example.com") == usuario


def test_no_permitir_id_duplicado(repositorio, usuario):
    repositorio.guardar(usuario)

    duplicado = Usuario(
        id=usuario.id,
        nombre="Otro nombre",
        usuario="otro_usuario",
        correo="otro@example.com",
        contrasena_hash="otro_hash"
    )

    with pytest.raises(ValueError, match="ID"):
        repositorio.guardar(duplicado)


def test_no_permitir_nombre_usuario_duplicado(repositorio, usuario):
    repositorio.guardar(usuario)

    duplicado = Usuario(
        id=str(uuid.uuid4()),
        nombre="Otro nombre",
        usuario="AKEMI",
        correo="otro@example.com",
        contrasena_hash="otro_hash"
    )

    with pytest.raises(ValueError, match="nombre de usuario"):
        repositorio.guardar(duplicado)


def test_no_permitir_correo_duplicado(repositorio, usuario):
    repositorio.guardar(usuario)

    duplicado = Usuario(
        id=str(uuid.uuid4()),
        nombre="Otro nombre",
        usuario="otro_usuario",
        correo="AKEMI@example.com",
        contrasena_hash="otro_hash"
    )

    with pytest.raises(ValueError, match="correo"):
        repositorio.guardar(duplicado)


def test_buscar_usuario_inexistente(repositorio):
    assert repositorio.buscar_por_id("inexistente") is None
    assert repositorio.buscar_por_nombre("inexistente") is None
    assert repositorio.buscar_por_correo("inexistente@example.com") is None


def test_busqueda_por_nombre_no_distingue_mayusculas(repositorio, usuario):
    repositorio.guardar(usuario)

    assert repositorio.buscar_por_nombre("AKEMI") == usuario


def test_busqueda_por_correo_no_distingue_mayusculas(repositorio, usuario):
    repositorio.guardar(usuario)

    assert repositorio.buscar_por_correo("AKEMI@EXAMPLE.COM") == usuario


def test_obtener_todos(repositorio, usuario):
    repositorio.guardar(usuario)

    usuarios = repositorio.obtener_todos()

    assert len(usuarios) == 1
    assert usuarios[0] == usuario


def test_eliminar_usuario(repositorio, usuario):
    repositorio.guardar(usuario)

    resultado = repositorio.eliminar(usuario.id)

    assert resultado is True
    assert repositorio.buscar_por_id(usuario.id) is None
    assert repositorio.buscar_por_nombre("akemi") is None
    assert repositorio.buscar_por_correo("akemi@example.com") is None


def test_eliminar_usuario_inexistente(repositorio):
    assert repositorio.eliminar("inexistente") is False


def test_persistencia_al_recrear_repositorio(tmp_path, usuario):
    ruta = tmp_path / "usuarios.json"

    primer_repositorio = UsuarioRepository(ruta)
    primer_repositorio.guardar(usuario)

    segundo_repositorio = UsuarioRepository(ruta)

    assert segundo_repositorio.buscar_por_id(usuario.id) == usuario


def test_cargar_archivo_con_formato_invalido(tmp_path):
    ruta = tmp_path / "usuarios.json"
    ruta.write_text('{"usuario": "akemi"}', encoding="utf-8")

    with pytest.raises(ValueError, match="lista"):
        UsuarioRepository(ruta)


def test_cargar_archivo_json_danado(tmp_path):
    ruta = tmp_path / "usuarios.json"
    ruta.write_text("{json invalido", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        UsuarioRepository(ruta)


def test_cargar_usuarios_no_duplica_indices(repositorio, usuario):
    repositorio.guardar(usuario)

    repositorio.cargar_usuarios()
    repositorio.cargar_usuarios()

    assert len(repositorio.obtener_todos()) == 1
    assert repositorio.buscar_por_nombre("akemi") == usuario


def test_recuperar_indices_si_falla_el_guardado(
    repositorio, usuario, monkeypatch
):
    def simular_error():
        raise OSError("Error de escritura")

    monkeypatch.setattr(repositorio, "guardar_usuarios", simular_error)

    with pytest.raises(OSError):
        repositorio.guardar(usuario)

    assert repositorio.buscar_por_id(usuario.id) is None
    assert repositorio.buscar_por_nombre("akemi") is None
    assert repositorio.buscar_por_correo("akemi@example.com") is None
