"""
feed_view.py - Rutas del módulo Feed (Integrante 4).

Define el Blueprint "feed_bp" con la pantalla del feed general.
El Blueprint se registra en app.py con app.register_blueprint(feed_bp).

Nota: este archivo NO debe importar "app" (provocaría un import circular).
"""
from flask import Blueprint, render_template

# El primer valor ('feed') es el nombre interno del Blueprint.
feed_bp = Blueprint('feed', __name__)


@feed_bp.route("/feed")
def feed():
    """Muestra la pantalla del feed (plantilla templates/feed.html)."""
    # TODO: cuando exista feed_service, pasar aquí las publicaciones del feed.
    return render_template("feed.html")
