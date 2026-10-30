
import webbrowser
from threading import Timer

from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/", methods=["GET"])
def inicio():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    nombre_usuario = request.form.get("nombre_usuario", "")
    contrasena = request.form.get("contrasena", "")

    return render_template(
        "login.html",
        error="La autenticación todavía no está configurada."
    )


@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":
        return render_template(
            "registro.html",
            error="El registro todavía no está conectado."
        )

    return render_template("registro.html")

if __name__ == "__main__":
    Timer(
        1,
        lambda: webbrowser.open("http://127.0.0.1:5000/")
    ).start()

    app.run(debug=True, use_reloader=False)
