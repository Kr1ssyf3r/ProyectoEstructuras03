"""
app.py - Punto de entrada de Social UNA (ventana principal y navegación).

Qué hace este archivo:
- Crea la aplicación Flask.
- Registra los Blueprints de cada módulo (cada módulo define sus rutas en views/).
- Define la ruta de inicio ("/") y arranca el servidor de desarrollo.

Para agregar un módulo nuevo, ver la "Guía de integración de módulos".
Solo el Integrante 4 edita este archivo.
"""
from flask import Flask, render_template
from views.feed_view import feed_bp
from views.perfil_view import perfil_bp
from views.amigos_view import amigos_bp

# Crea la aplicación. __name__ le permite a Flask encontrar las carpetas
# "templates" y "static" que están junto a este archivo.
app = Flask(__name__)

# Registro de módulos: cada línea "enchufa" las rutas de un Blueprint.
# Sin su línea register_blueprint, Flask no conoce las rutas de ese módulo.
# Se mantienen juntas para ver de un vistazo qué módulos están conectados.
app.register_blueprint(feed_bp)
app.register_blueprint(perfil_bp)
app.register_blueprint(amigos_bp)


# Pantalla de inicio. La ruta "/" vive aquí (y no en un Blueprint) porque
# pertenece a la ventana principal.
@app.route("/")
def bienvenido():
    # TODO: "nombre" todavía no se usa en inicio.html. Cuando exista el login,
    # este valor debe venir del usuario que inició sesión.
    return render_template("inicio.html", nombre="Usuario")


# Solo arranca el servidor si este archivo se ejecuta directamente
# (python app.py) y no cuando otro archivo lo importa.
# debug=True reinicia el servidor al guardar cambios y muestra errores
# detallados; es solo para desarrollo.
if __name__ == "__main__":
    app.run(debug=True)
