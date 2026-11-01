"""
amigos_view.py - Rutas del módulo Amigos.

Pantalla de relleno que simula el módulo de un compañero y sirve de ejemplo
de cómo se conecta un módulo: un Blueprint propio, registrado en app.py.
TODO: el dueño del módulo reemplaza el contenido de prueba por el real.

Nota: este archivo NO debe importar "app" (provocaría un import circular).
"""
from flask import Blueprint, render_template

amigos_bp = Blueprint('amigos', __name__)


@amigos_bp.route("/amigos")
def amigos():
    """Muestra la pantalla de amigos (plantilla templates/amigos.html)."""
    return render_template("amigos.html")
