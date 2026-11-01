"""
perfil_view.py - Rutas del módulo Perfil.

Pantalla de relleno que simula el módulo de un compañero y sirve de ejemplo
de cómo se conecta un módulo: un Blueprint propio, registrado en app.py.
TODO: el dueño del módulo reemplaza el contenido de prueba por el real.

Nota: este archivo NO debe importar "app" (provocaría un import circular).
"""
from flask import Blueprint, render_template

perfil_bp = Blueprint('perfil', __name__)


@perfil_bp.route("/perfil")
def perfil():
    """Muestra la pantalla de perfil (plantilla templates/perfil.html)."""
    return render_template("perfil.html")
