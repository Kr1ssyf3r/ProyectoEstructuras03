"""Factoría de aplicación Flask e integración de los módulos."""
import os

from flask import Flask

from controllers.amistades_routes import crear_amistades_blueprint
from controllers.autenticacion_routes import autenticacion_bp
from controllers.feed_routes import crear_feed_blueprint
from controllers.historias_routes import crear_historias_blueprint
from controllers.inicio_routes import inicio_bp
from controllers.perfil_routes import perfil_bp
from controllers.publicaciones_routes import crear_publicaciones_blueprint
from repositories.reaccion_repository import ReaccionRepository
from repositories.token_repository import TokenRepository
from repositories.usuario_repository import UsuarioRepository
from services.amistadService import AmistadService
from services.busquedaService import BusquedaService
from services.correo_service import CorreoService
from services.feed_service import FeedService
from services.historiaService import HistoriaService
from services.multimediaService import MultimediaService
from services.publicacion_service import PublicacionService
from services.reaccion_service import ReaccionService
from services.recuperacion_service import RecuperacionService
from services.usuario_service import UsuarioService

#carpetas donde se guardan los archivos subidos. Se usa ruta absoluta porque
#send_from_directory resuelve las relativas respecto a la app y no al directorio de ejecucion
CARPETA_PUBLICACIONES = os.path.abspath("data/uploads")
CARPETA_HISTORIAS = os.path.abspath("data/historias_media")

#las historias aceptan videos mas livianos que las publicaciones
MAX_VIDEO_HISTORIA = 10 * 1024 * 1024


def _crear_aplicacion(test_config):
    """Crea la app Flask con su configuracion basica."""
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config.update(
        SECRET_KEY=os.environ.get(
            "SECRET_KEY",
            "clave-temporal-social-una-desarrollo",
        )
    )

    if test_config:
        app.config.update(test_config)

    return app


def _construir_servicios():
    """Construye las dependencias UNA sola vez, en orden: cada una solo usa las anteriores."""

    #---------- base: usuarios ----------
    usuario_repository = UsuarioRepository()
    usuario_service = UsuarioService(repositorio=usuario_repository)

    #---------- autenticacion ----------
    token_repository = TokenRepository()
    recuperacion_service = RecuperacionService(
        token_repository=token_repository,
        usuario_service=usuario_service,
    )
    correo_service = CorreoService()

    #---------- red de amistades ----------
    amistad_service = AmistadService(usuario_service=usuario_service)

    #BusquedaService se suscribe a usuario_service al crearse, por eso debe usar esa misma instancia
    busqueda_service = BusquedaService(usuario_service, amistad_service)

    #---------- multimedia: una instancia por carpeta y limites ----------
    multimedia_publicaciones = MultimediaService(carpeta_media=CARPETA_PUBLICACIONES)
    multimedia_historias = MultimediaService(
        carpeta_media=CARPETA_HISTORIAS,
        max_video=MAX_VIDEO_HISTORIA,
    )

    #---------- publicaciones y reacciones ----------
    publicacion_service = PublicacionService(
        usuario_service=usuario_service,
        multimedia_service=multimedia_publicaciones,
    )

    reaccion_repository = ReaccionRepository()
    reaccion_service = ReaccionService(
        usuario_service=usuario_service,
        repositorio=reaccion_repository,
        publicacion_existe=lambda id_publicacion: (
            publicacion_service.obtener_publicacion(id_publicacion) is not None
        ),
    )

    feed_service = FeedService(
        amistad_service=amistad_service,
        publicacion_service=publicacion_service,
        reaccion_service=reaccion_service,
    )

    #---------- historias ----------
    historia_service = HistoriaService(
        usuario_service,
        amistad_service,
        multimedia_historias,
    )

    return {
        "usuario_repository": usuario_repository,
        "token_repository": token_repository,
        "usuario_service": usuario_service,
        "recuperacion_service": recuperacion_service,
        "correo_service": correo_service,
        "amistad_service": amistad_service,
        "busqueda_service": busqueda_service,
        "publicacion_service": publicacion_service,
        "reaccion_service": reaccion_service,
        "feed_service": feed_service,
        "historia_service": historia_service,
    }


def _registrar_blueprints(app, servicios):
    """Registra los Blueprints de cada modulo."""
    app.register_blueprint(autenticacion_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(inicio_bp)

    app.register_blueprint(
        crear_amistades_blueprint(
            servicios["usuario_service"],
            servicios["amistad_service"],
            servicios["busqueda_service"],
        )
    )
    app.register_blueprint(
        crear_publicaciones_blueprint(servicios["publicacion_service"])
    )
    app.register_blueprint(crear_feed_blueprint(servicios["reaccion_service"]))

    historias_bp = crear_historias_blueprint(
        servicios["historia_service"],
        CARPETA_HISTORIAS,
    )
    app.register_blueprint(historias_bp)

    #el template usa {{ csrf_historias() }}, igual que con csrf_publicaciones
    app.jinja_env.globals["csrf_historias"] = historias_bp.csrf_token


def create_app(test_config=None):
    """Crea y configura una instancia independiente de Social UNA."""
    app = _crear_aplicacion(test_config)
    servicios = _construir_servicios()

    app.extensions["social_una"] = servicios

    _registrar_blueprints(app, servicios)

    return app