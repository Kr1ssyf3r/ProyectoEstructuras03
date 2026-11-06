import pytest
from datetime import datetime, timedelta

from models.usuario import Usuario
from services.feed_service import FeedService
from services.publicacion_service import PublicacionService
from services.reaccion_service import ReaccionService
from repositories.publicacion_repository import PublicacionRepository
from repositories.reaccion_repository import ReaccionRepository

U1 = "11111111-1111-4111-8111-111111111111"
U2 = "22222222-2222-4222-8222-222222222222"
U3 = "33333333-3333-4333-8333-333333333333"
U4 = "44444444-4444-4444-8444-444444444444"
U99 = "99999999-9999-4999-8999-999999999999"


class AmistadServiceFalso:
    def __init__(self, amigos_por_usuario):
        self._amigos_por_usuario = amigos_por_usuario

    def amigos(self, usuario_id):
        return [
            _crear_usuario(amigo_id)
            for amigo_id in self._amigos_por_usuario.get(usuario_id, [])
        ]


class UsuariosFalsos:
    def __init__(self, ids):
        self.ids = set(ids)

    def obtener_usuario(self, id_usuario):
        return _crear_usuario(id_usuario) if id_usuario in self.ids else None


def _crear_usuario(id_usuario):
    return Usuario(
        id=id_usuario,
        nombre=f"usuario_{id_usuario}",
        usuario=id_usuario,
        correo=f"{id_usuario}@ejemplo.com",
        contrasena_hash="hash",
    )


def _crear_fecha(dias_antes):
    return (datetime.now() - timedelta(days=dias_antes)).isoformat()


def _cargar_datos_temporales(tmp_path):
    repositorio_publicacion = PublicacionRepository(
        ruta=tmp_path / "publicaciones.json"
    )
    publicacion_service = PublicacionService(
        usuario_service=UsuariosFalsos([U1, U2, U3, U4]),
        repositorio=repositorio_publicacion,
    )

    repositorio_reaccion = ReaccionRepository(
        ruta_archivo=tmp_path / "reacciones.json"
    )
    reaccion_service = ReaccionService(
        usuario_service=UsuariosFalsos([U1, U2]),
        repositorio=repositorio_reaccion,
    )

    return publicacion_service, reaccion_service


def _crear_feed(usuario, amistad_service, publicacion_service, reaccion_service):
    return FeedService(
        amistad_service=amistad_service,
        publicacion_service=publicacion_service,
        reaccion_service=reaccion_service,
    ).construir_feed(usuario)


def _crear_publicacion_y_fijar_fecha(publicacion_service, autor_id, contenido, dias_antes):
    publicacion = publicacion_service.crear_publicacion(autor_id, contenido)
    publicacion.fecha = _crear_fecha(dias_antes)
    return publicacion


def test_feed_incluye_tus_publicaciones_y_amigos_no_otros(tmp_path):
    publicacion_service, reaccion_service = _cargar_datos_temporales(tmp_path)

    _crear_publicacion_y_fijar_fecha(publicacion_service, U1, "mi publicación", 3)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U2, "amigo dice hola", 2)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U3, "no debería aparecer", 1)

    amistad = AmistadServiceFalso(amigos_por_usuario={U1: [U2]})
    feed = _crear_feed(
        _crear_usuario(U1),
        amistad,
        publicacion_service,
        reaccion_service,
    )

    autores_feed = {p.autor_id for p in [t.publicacion for t in feed]}

    assert autores_feed == {U1, U2}


def test_feed_esta_ordenado_reciente_a_antiguo_mezclando_autores(tmp_path):
    publicacion_service, reaccion_service = _cargar_datos_temporales(tmp_path)

    _crear_publicacion_y_fijar_fecha(publicacion_service, U1, "primera", 5)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U2, "segunda", 4)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U1, "tercera", 3)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U2, "cuarta", 2)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U3, "nada", 1)

    amistad = AmistadServiceFalso(amigos_por_usuario={U1: [U2]})
    feed = _crear_feed(
        _crear_usuario(U1),
        amistad,
        publicacion_service,
        reaccion_service,
    )

    fechas = [t.publicacion.fecha for t in feed]

    assert fechas == sorted(fechas, reverse=True)


def test_feed_contadores_y_yo_di_me_gusta_reflejan_likes(tmp_path):
    publicacion_service, reaccion_service = _cargar_datos_temporales(tmp_path)

    p1 = _crear_publicacion_y_fijar_fecha(publicacion_service, U1, "publicación 1", 5)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U2, "publicación 2", 4)

    reaccion_service.dar_me_gusta(U1, p1.id)
    reaccion_service.dar_me_gusta(U2, p1.id)

    amistad = AmistadServiceFalso(amigos_por_usuario={U1: [U2]})
    feed = _crear_feed(
        _crear_usuario(U1),
        amistad,
        publicacion_service,
        reaccion_service,
    )

    tarjeta_p1 = next(t for t in feed if t.publicacion.id == p1.id)

    assert tarjeta_p1.cantidad_me_gusta == 2
    assert tarjeta_p1.yo_di_me_gusta is True

    tarjeta_p2 = next(t for t in feed if t.publicacion.id != p1.id)

    assert tarjeta_p2.cantidad_me_gusta == 0
    assert tarjeta_p2.yo_di_me_gusta is False



def test_feed_l_imite_n_devuelve_solo_las_n_primeras(tmp_path):
    publicacion_service, reaccion_service = _cargar_datos_temporales(tmp_path)

    _crear_publicacion_y_fijar_fecha(publicacion_service, U1, "a", 5)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U2, "b", 4)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U1, "c", 3)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U2, "d", 2)

    amistad = AmistadServiceFalso(amigos_por_usuario={U1: [U2]})
    feed_service = FeedService(
        amistad_service=amistad,
        publicacion_service=publicacion_service,
        reaccion_service=reaccion_service,
    )

    feed_con_limite = feed_service.construir_feed(_crear_usuario(U1), limite=2)

    assert len(feed_con_limite) == 2


def test_feed_l_imite_0_devuelve_una_lista_vacia(tmp_path):
    publicacion_service, reaccion_service = _cargar_datos_temporales(tmp_path)

    _crear_publicacion_y_fijar_fecha(publicacion_service, U1, "a", 5)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U2, "b", 4)

    amistad = AmistadServiceFalso(amigos_por_usuario={U1: [U2]})
    feed_service = FeedService(
        amistad_service=amistad,
        publicacion_service=publicacion_service,
        reaccion_service=reaccion_service,
    )

    resultado = feed_service.construir_feed(_crear_usuario(U1), limite=0)

    assert resultado == []


def test_feed_usuario_sin_amigos_y_sin_publicaciones_devuelve_una_lista_vacia(tmp_path):
    publicacion_service, reaccion_service = _cargar_datos_temporales(tmp_path)

    amistad = AmistadServiceFalso(amigos_por_usuario={U1: []})
    feed_service = FeedService(
        amistad_service=amistad,
        publicacion_service=publicacion_service,
        reaccion_service=reaccion_service,
    )

    resultado = feed_service.construir_feed(_crear_usuario(U1))

    assert resultado == []


def test_filtrar_por_autor_solo_devuelve_ese_autor(tmp_path):
    publicacion_service, reaccion_service = _cargar_datos_temporales(tmp_path)

    _crear_publicacion_y_fijar_fecha(publicacion_service, U1, "a", 5)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U2, "b", 4)
    _crear_publicacion_y_fijar_fecha(publicacion_service, U3, "c", 3)

    amistad = AmistadServiceFalso(amigos_por_usuario={U1: [U2]})
    feed_service = FeedService(
        amistad_service=amistad,
        publicacion_service=publicacion_service,
        reaccion_service=reaccion_service,
    )

    filtradas = feed_service.filtrar_por_autor(_crear_usuario(U1), autor_id=U1)

    assert {t.publicacion.autor_id for t in filtradas} == {U1}

    with pytest.raises(ValueError, match="Solo puedes ver publicaciones tuyas o de tus amigos"):
        feed_service.filtrar_por_autor(_crear_usuario(U1), autor_id=U3)


def test_construir_feed_usuario_inexistente_lanza_value_error(tmp_path):
    publicacion_service, reaccion_service = _cargar_datos_temporales(tmp_path)

    amistad = AmistadServiceFalso(amigos_por_usuario={U1: []})
    feed_service = FeedService(
        amistad_service=amistad,
        publicacion_service=publicacion_service,
        reaccion_service=reaccion_service,
        usuario_service=UsuariosFalsos([U1]),
    )

    with pytest.raises(ValueError, match="No se encontró el usuario"):
        feed_service.construir_feed(_crear_usuario(U99))

