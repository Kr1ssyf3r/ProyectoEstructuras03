import pytest

from models.reaccion import Reaccion
from services.reaccion_service import ReaccionService


class UsuariosFalsos:
    def __init__(self, ids):
        self.ids = set(ids)

    def obtener_usuario(self, id_usuario):
        if id_usuario in self.ids and id_usuario != "desconocido":
            return object()
        return None


class RepositorioReaccionesFalso:
    def __init__(self):
        self._datos = {}

    def agregar(self, reaccion):
        clave = (reaccion.usuario_id, reaccion.publicacion_id)
        if clave in self._datos:
            return False
        self._datos[clave] = reaccion
        return True

    def eliminar(self, usuario_id, publicacion_id):
        clave = (usuario_id, publicacion_id)
        if clave in self._datos:
            del self._datos[clave]
            return True
        return False

    def existe(self, usuario_id, publicacion_id):
        return (usuario_id, publicacion_id) in self._datos

    def contar(self, publicacion_id):
        return sum(
            1 for (usuario_id, pid) in self._datos
            if pid == publicacion_id
        )

    def publicaciones_de(self, usuario_id):
        return frozenset(
            pid for (uid, pid) in self._datos
            if uid == usuario_id
        )


class RepositorioConContador:
    def __init__(self):
        self.reacciones = {}

    def agregar(self, reaccion):
        clave = (reaccion.usuario_id, reaccion.publicacion_id)
        if clave in self.reacciones:
            return False
        self.reacciones[clave] = reaccion
        return True

    def eliminar(self, usuario_id, publicacion_id):
        clave = (usuario_id, publicacion_id)
        if clave in self.reacciones:
            del self.reacciones[clave]
            return True
        return False

    def existe(self, usuario_id, publicacion_id):
        return (usuario_id, publicacion_id) in self.reacciones

    def contar(self, publicacion_id):
        return sum(
            1 for (usuario_id, pid) in self.reacciones
            if pid == publicacion_id
        )

    def publicaciones_de(self, usuario_id):
        return frozenset(
            pid for (uid, pid) in self.reacciones
            if uid == usuario_id
        )


@pytest.fixture
def rbac():
    usuario_service = UsuariosFalsos(["u1"])
    repos = RepositorioReaccionesFalso()
    return ReaccionService(usuario_service, repositorio=repos)


@pytest.fixture
def rbac_contador():
    repos = RepositorioConContador()
    usuario_service = UsuariosFalsos(["u1"])
    return ReaccionService(usuario_service, repositorio=repos)


@pytest.fixture
def rbac_falso_publicacion():
    usuario_service = UsuariosFalsos(["u1"])
    repos = RepositorioReaccionesFalso()
    publicacion_existe = lambda pid: pid == "p1"
    return ReaccionService(usuario_service, repositorio=repos, publicacion_existe=publicacion_existe)


@pytest.fixture
def rbac_sin_validacion_publicacion():
    usuario_service = UsuariosFalsos(["u1"])
    repos = RepositorioReaccionesFalso()
    return ReaccionService(usuario_service, repositorio=repos)


def test_dar_me_gusta_retorna_true_y_se_rechaza_el_segundo(rbac):
    assert rbac.dar_me_gusta("u1", "p1") is True
    assert rbac.dar_me_gusta("u1", "p1") is False


def test_dar_me_gusta_usuario_inexistente_lanza_value_error(rbac):
    with pytest.raises(ValueError, match="usuario no existe"):
        rbac.dar_me_gusta("desconocido", "p1")


def test_dar_me_gusta_usuario_inexistente_no_deja_nada_guardado(rbac):
    rbac.dar_me_gusta("u1", "p1")

    with pytest.raises(ValueError):
        rbac.dar_me_gusta("desconocido", "p1")

    assert rbac.repositorio.existe("u1", "p1") is True


def test_quitar_me_gusta_que_no_existe_devuelve_false(rbac):
    assert rbac.quitar_me_gusta("u1", "p2") is False


def test_alternar_devuelve_true_false_true_y_contar_acompana(rbac_contador):
    assert rbac_contador.alternar_me_gusta("u1", "p1") is True
    assert rbac_contador.alternar_me_gusta("u1", "p1") is False
    assert rbac_contador.alternar_me_gusta("u1", "p1") is True

    assert rbac_contador.contar_me_gusta("p1") == 1


def test_dar_me_gusta_a_publicacion_inexistente_lanza_value_error(rbac_falso_publicacion):
    with pytest.raises(ValueError, match=r"publicaci[óo]n no existe"):
        rbac_falso_publicacion.dar_me_gusta("u1", "p2")


def test_dar_me_gusta_sin_publicacion_existe_acepta_cualquier_publicacion(rbac_sin_validacion_publicacion):
    assert rbac_sin_validacion_publicacion.dar_me_gusta("u1", "p2") is True
    assert rbac_sin_validacion_publicacion.dar_me_gusta("u1", "p99") is True


def test_publicaciones_con_me_gusta_devuelve_resultados_correctos(rbac):
    assert rbac.publicaciones_con_me_gusta("u1") == frozenset()
    rbac.dar_me_gusta("u1", "p1")
    rbac.dar_me_gusta("u1", "p2")

    rbac_contador = ReaccionService(
        UsuariosFalsos(["u1", "u2"]),
        repositorio=RepositorioConContador(),
    )
    rbac_contador.dar_me_gusta("u1", "p1")
    rbac_contador.dar_me_gusta("u1", "p2")
    rbac_contador.dar_me_gusta("u2", "p1")

    assert rbac_contador.publicaciones_con_me_gusta("u1") == frozenset({"p1", "p2"})
    assert rbac_contador.publicaciones_con_me_gusta("u2") == frozenset({"p1"})


def test_publicaciones_con_me_gusta_devuelve_conjunto_vacio(rbac):
    assert rbac.publicaciones_con_me_gusta("u1") == frozenset()
