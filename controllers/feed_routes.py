"""Blueprint del feed: reacciones ("Me gusta") a las publicaciones."""
from flask import Blueprint, flash, redirect, url_for

from controllers.csrf import obtener_token, validar_token
from controllers.decorators import requiere_sesion

# Clave de sesión donde se guarda el token CSRF de este módulo.
CLAVE_CSRF = "csrf_feed"


def crear_feed_blueprint(reaccion_service):
    """Construye el Blueprint del feed con sus dependencias."""

    bp = Blueprint("feed", __name__)

    @bp.app_context_processor
    def inyectar_csrf():
        # Deja csrf_feed() disponible en cualquier plantilla.
        return {"csrf_feed": lambda: obtener_token(CLAVE_CSRF)}

    @bp.post("/feed/me-gusta/<id_publicacion>")
    @requiere_sesion
    def alternar_me_gusta(usuario, id_publicacion):
        """Da o quita el Me gusta del usuario a una publicación."""

        validar_token(CLAVE_CSRF)

        try:
            reaccion_service.alternar_me_gusta(usuario.id, id_publicacion)
        except ValueError as error:
            flash(str(error), "error")

        return redirect(
            url_for("inicio.inicio_feed", _anchor=f"post-{id_publicacion}")
        )

    return bp