"""Factoría de aplicación Flask e integración de los módulos."""
import os

from flask import Flask

from controllers.autenticacion_routes import autenticacion_bp
from controllers.inicio_routes import inicio_bp
from controllers.perfil_routes import perfil_bp
from controllers.amistades_routes import crear_amistades_blueprint
from controllers.publicaciones_routes import crear_publicaciones_blueprint
from services.publicacion_service import PublicacionService
from repositories.token_repository import TokenRepository
from repositories.usuario_repository import UsuarioRepository
from services.amistadService import AmistadService
from services.correo_service import CorreoService
from services.recuperacion_service import RecuperacionService
from services.usuario_service import UsuarioService


def create_app(test_config=None):
    """Crea y configura una instancia independiente de Social UNA."""
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

    # Construir las dependencias una sola vez y compartirlas con los módulos.
    usuario_repository = UsuarioRepository()
    token_repository = TokenRepository()

    usuario_service = UsuarioService(repositorio=usuario_repository)
    recuperacion_service = RecuperacionService(
        token_repository=token_repository,
        usuario_service=usuario_service,
    )
    correo_service = CorreoService()
    amistad_service = AmistadService(usuario_service=usuario_service)
    publicacion_service = PublicacionService()

    app.extensions["social_una"] = {
        "usuario_repository": usuario_repository,
        "token_repository": token_repository,
        "usuario_service": usuario_service,
        "recuperacion_service": recuperacion_service,
        "correo_service": correo_service,
        "amistad_service": amistad_service,
        "publicacion_service": publicacion_service,
    }

    # Registrar los Blueprints de cada módulo.
    app.register_blueprint(autenticacion_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(inicio_bp)
    app.register_blueprint(
        crear_amistades_blueprint(usuario_service, amistad_service)
    )
    app.register_blueprint(
        crear_publicaciones_blueprint(publicacion_service, usuario_service)
    )

    return app
