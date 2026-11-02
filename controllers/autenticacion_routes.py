"""Rutas HTTP relacionadas con autenticación y recuperación de cuenta."""
from flask import Blueprint, current_app, redirect, render_template, request, session, url_for


autenticacion_bp = Blueprint("autenticacion", __name__)


def _servicios():
    return current_app.extensions["social_una"]


@autenticacion_bp.get("/")
def inicio():
    """Muestra el login o redirige al feed si ya hay sesión."""
    if session.get("usuario_id"):
        return redirect(url_for("inicio.inicio_feed"))
    return render_template("login.html")


@autenticacion_bp.post("/login")
def login():
    """Autentica al estudiante y lo lleva al feed."""
    servicios = _servicios()
    nombre_usuario = request.form.get("nombre_usuario", "").strip()
    contrasena = request.form.get("contrasena", "")

    try:
        usuario = servicios["usuario_service"].iniciar_sesion(
            nombre_usuario=nombre_usuario,
            contrasena=contrasena,
        )
        session.clear()
        session["usuario_id"] = usuario.id
        return redirect(url_for("inicio.inicio_feed"))
    except ValueError as error:
        return render_template("login.html", error=str(error))


@autenticacion_bp.get("/logout")
def logout():
    """Cierra la sesión del usuario actual."""
    session.clear()
    return redirect(url_for("autenticacion.inicio"))


@autenticacion_bp.route("/registro", methods=["GET", "POST"])
def registro():
    """Registra nuevos estudiantes."""
    if request.method == "POST":
        servicios = _servicios()
        nombre = request.form.get("nombre", "")
        nombre_usuario = request.form.get("nombre_usuario", "")
        correo = request.form.get("correo", "")
        contrasena = request.form.get("contrasena", "")
        confirmar_contrasena = request.form.get("confirmar_contrasena", "")

        try:
            usuario = servicios["usuario_service"].registrar_usuario(
                nombre=nombre,
                nombre_usuario=nombre_usuario,
                correo=correo,
                contrasena=contrasena,
                confirmar_contrasena=confirmar_contrasena,
            )

            try:
                servicios["correo_service"].enviar_bienvenida(
                    destinatario=usuario.correo,
                    nombre=usuario.nombre,
                )
                mensaje = (
                    "¡Tu cuenta se creó correctamente! "
                    "Te enviamos un correo de bienvenida."
                )
            except Exception:
                current_app.logger.exception(
                    "No se pudo enviar el correo de bienvenida."
                )
                mensaje = (
                    "Tu cuenta se creó correctamente, "
                    "pero no pudimos enviar el correo de bienvenida."
                )

            return render_template("login.html", mensaje=mensaje)
        except ValueError as error:
            return render_template("registro.html", error=str(error))

    return render_template("registro.html")


@autenticacion_bp.route("/recuperar", methods=["GET", "POST"])
def solicitar_recuperacion():
    """Solicita un enlace para recuperar la contraseña."""
    if request.method == "POST":
        servicios = _servicios()
        correo = request.form.get("correo", "").strip().lower()

        if not correo:
            return render_template(
                "recuperar.html",
                error="Debes introducir tu correo electrónico.",
            )

        usuario = servicios["usuario_repository"].buscar_por_correo(correo)
        if usuario is None:
            return render_template(
                "recuperar.html",
                error="No existe una cuenta asociada a ese correo.",
            )

        try:
            token = servicios["recuperacion_service"].generar_token(usuario.id)
            enlace = url_for(
                "autenticacion.restablecer_contrasena",
                token=token,
                _external=True,
            )
            servicios["correo_service"].enviar_recuperacion(
                destinatario=usuario.correo,
                enlace=enlace,
            )
            return render_template(
                "recuperar.html",
                mensaje=(
                    "Si la cuenta existe y el correo pudo enviarse, "
                    "recibirás un enlace de recuperación. "
                    "Revisa también tu carpeta de spam."
                ),
            )
        except Exception:
            current_app.logger.exception(
                "No se pudo procesar la recuperación de contraseña."
            )
            return render_template(
                "recuperar.html",
                error=(
                    "No se pudo enviar el correo de recuperación. "
                    "Inténtalo nuevamente."
                ),
            )

    return render_template("recuperar.html")


@autenticacion_bp.route("/restablecer/<token>", methods=["GET", "POST"])
def restablecer_contrasena(token):
    """Permite establecer una nueva contraseña."""
    recuperacion_service = _servicios()["recuperacion_service"]
    token_validado = recuperacion_service.validar_token(token)

    if token_validado is None:
        return render_template(
            "restablecer.html",
            token_invalido=True,
            error=(
                "El enlace no es válido, "
                "ya fue utilizado o ha expirado."
            ),
        )

    if request.method == "POST":
        nueva_contrasena = request.form.get("contrasena", "")
        confirmar_contrasena = request.form.get("confirmar_contrasena", "")

        try:
            recuperacion_service.restablecer_contrasena(
                token_original=token,
                nueva_contrasena=nueva_contrasena,
                confirmar_contrasena=confirmar_contrasena,
            )
            return render_template(
                "restablecer.html",
                exito="Tu contraseña se actualizó correctamente.",
                completado=True,
            )
        except ValueError as error:
            return render_template(
                "restablecer.html",
                error=str(error),
                token=token,
            )

    return render_template("restablecer.html", token=token)
