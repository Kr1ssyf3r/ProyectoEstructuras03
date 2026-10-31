
import os
import webbrowser

from threading import Timer
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    url_for,
    redirect,
    session
)

from repositories.usuario_repository import UsuarioRepository
from repositories.token_repository import TokenRepository

from services.usuario_service import UsuarioService
from services.recuperacion_service import RecuperacionService
from services.correo_service import CorreoService


# ============================================================
# CONFIGURACIÓN DE FLASK
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "clave-temporal-social-una-desarrollo"
)


# ============================================================
# INICIALIZACIÓN DE REPOSITORIOS Y SERVICIOS
# ============================================================

usuario_repository = UsuarioRepository()
token_repository = TokenRepository()

usuario_service = UsuarioService(
    repositorio=usuario_repository
)

recuperacion_service = RecuperacionService(
    token_repository=token_repository,
    usuario_service=usuario_service
)

correo_service = CorreoService()


# ============================================================
# VALIDACIÓN DE SESIÓN
# ============================================================

def requiere_sesion(funcion):
    """Comprueba que exista un usuario autenticado."""

    @wraps(funcion)
    def funcion_protegida(*args, **kwargs):

        usuario_id = session.get("usuario_id")

        if not usuario_id:
            return redirect(url_for("inicio"))

        usuario = usuario_service.obtener_usuario(usuario_id)

        if usuario is None:
            session.clear()
            return redirect(url_for("inicio"))

        return funcion(usuario, *args, **kwargs)

    return funcion_protegida


# ============================================================
# INICIO DE SESIÓN
# ============================================================

@app.route("/", methods=["GET"])
def inicio():

    if session.get("usuario_id"):
        return redirect(url_for("perfil"))

    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():

    nombre_usuario = request.form.get(
        "nombre_usuario", ""
    ).strip()

    contrasena = request.form.get(
        "contrasena", ""
    )

    try:

        usuario = usuario_service.iniciar_sesion(
            nombre_usuario=nombre_usuario,
            contrasena=contrasena
        )

        session.clear()
        session["usuario_id"] = usuario.id

        return redirect(url_for("perfil"))

    except ValueError as error:

        return render_template(
            "login.html",
            error=str(error)
        )


# ============================================================
# PERFIL DEL USUARIO
# ============================================================

@app.route("/perfil", methods=["GET"])
@requiere_sesion
def perfil(usuario):

    return render_template(
        "perfil.html",
        usuario=usuario
    )


# ============================================================
# EDICIÓN DEL PERFIL
# ============================================================

@app.route("/perfil/editar", methods=["GET", "POST"])
@requiere_sesion
def editar_perfil(usuario):

    if request.method == "POST":

        nombre = request.form.get("nombre", "")
        nombre_usuario = request.form.get("nombre_usuario", "")
        correo = request.form.get("correo", "")

        try:

            usuario_service.actualizar_perfil(
                id_usuario=usuario.id,
                nombre=nombre,
                nombre_usuario=nombre_usuario,
                correo=correo
            )

            return redirect(url_for("perfil"))

        except ValueError as error:

            return render_template(
                "editar_perfil.html",
                usuario=usuario,
                error=str(error)
            )

    return render_template(
        "editar_perfil.html",
        usuario=usuario
    )


# ============================================================
# CIERRE DE SESIÓN
# ============================================================

@app.route("/logout", methods=["GET"])
def logout():

    session.clear()

    return redirect(url_for("inicio"))


# ============================================================
# REGISTRO DE USUARIOS
# ============================================================

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form.get("nombre", "")

        nombre_usuario = request.form.get(
            "nombre_usuario", ""
        )

        correo = request.form.get("correo", "")

        contrasena = request.form.get(
            "contrasena", ""
        )

        confirmar_contrasena = request.form.get(
            "confirmar_contrasena", ""
        )

        try:

            usuario = usuario_service.registrar_usuario(
                nombre=nombre,
                nombre_usuario=nombre_usuario,
                correo=correo,
                contrasena=contrasena,
                confirmar_contrasena=confirmar_contrasena
            )

            # Enviar correo de bienvenida.
            try:

                correo_service.enviar_bienvenida(
                    destinatario=usuario.correo,
                    nombre=usuario.nombre
                )

                mensaje = (
                    "¡Tu cuenta se creó correctamente! "
                    "Te enviamos un correo de bienvenida."
                )

            except Exception:
                app.logger.exception(
                    "No se pudo enviar el correo de bienvenida."
                )

                mensaje = (
                    "Tu cuenta se creó correctamente, "
                    "pero no pudimos enviar el correo de bienvenida."
                )

            return render_template(
                "login.html",
                mensaje=mensaje
            )

        except ValueError as error:

            return render_template(
                "registro.html",
                error=str(error)
            )

    return render_template("registro.html")


# ============================================================
# RECUPERACIÓN DE CONTRASEÑA
# ============================================================

@app.route("/recuperar", methods=["GET", "POST"])
def solicitar_recuperacion():

    if request.method == "POST":

        correo = request.form.get(
            "correo", ""
        ).strip().lower()

        if not correo:

            return render_template(
                "recuperar.html",
                error="Debes introducir tu correo electrónico."
            )

        # Buscar al usuario mediante su correo.
        usuario = usuario_repository.buscar_por_correo(correo)

        if usuario is None:

            return render_template(
                "recuperar.html",
                error="No existe una cuenta asociada a ese correo."
            )

        try:

            # Generar un token de recuperación.
            token = recuperacion_service.generar_token(
                usuario.id
            )

            # Crear el enlace para restablecer la contraseña.
            enlace = url_for(
                "restablecer_contrasena",
                token=token,
                _external=True
            )

            correo_service.enviar_recuperacion(
                destinatario=usuario.correo,
                enlace=enlace
            )

            return render_template(
                "recuperar.html",
                mensaje=(
                    "Si la cuenta existe y el correo pudo enviarse, "
                    "recibirás un enlace de recuperación. "
                    "Revisa también tu carpeta de spam."
                )
            )

        except (ValueError, OSError, Exception):

            app.logger.exception(
                "No se pudo procesar la recuperación de contraseña."
            )

            return render_template(
                "recuperar.html",
                error=(
                    "No se pudo enviar el correo de recuperación. "
                    "Inténtalo nuevamente."
                )
            )

    return render_template("recuperar.html")


# ============================================================
# RESTABLECIMIENTO DE CONTRASEÑA
# ============================================================

@app.route("/restablecer/<token>", methods=["GET", "POST"])
def restablecer_contrasena(token):

    # Comprobar que el token sea válido.
    token_validado = recuperacion_service.validar_token(token)

    if token_validado is None:

        return render_template(
            "restablecer.html",
            token_invalido=True,
            error=(
                "El enlace no es válido, "
                "ya fue utilizado o ha expirado."
            )
        )

    if request.method == "POST":

        nueva_contrasena = request.form.get(
            "contrasena", ""
        )

        confirmar_contrasena = request.form.get(
            "confirmar_contrasena", ""
        )

        try:

            recuperacion_service.restablecer_contrasena(
                token_original=token,
                nueva_contrasena=nueva_contrasena,
                confirmar_contrasena=confirmar_contrasena
            )

            return render_template(
                "restablecer.html",
                exito="Tu contraseña se actualizó correctamente.",
                completado=True
            )

        except ValueError as error:

            return render_template(
                "restablecer.html",
                error=str(error),
                token=token
            )

    return render_template(
        "restablecer.html",
        token=token
    )


# ============================================================
# EJECUCIÓN DE LA APLICACIÓN
# ============================================================

if __name__ == "__main__":

    Timer(
        1,
        lambda: webbrowser.open(
            "http://127.0.0.1:5000/"
        )
    ).start()

    app.run(
        debug=True,
        use_reloader=False
    )
