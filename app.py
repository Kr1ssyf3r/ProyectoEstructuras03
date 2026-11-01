
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

# ============================================================
# REPOSITORIOS
# ============================================================

from repositories.usuario_repository import UsuarioRepository
from repositories.token_repository import TokenRepository


# ============================================================
# SERVICIOS
# ============================================================

from services.usuario_service import UsuarioService
from services.recuperacion_service import RecuperacionService
from services.correo_service import CorreoService


# ============================================================
# CONTROLADORES
# ============================================================

from controllers.amistades_routes import registrar_rutas_amistades


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
    """Muestra el login o redirige al feed si ya hay sesión."""

    if session.get("usuario_id"):
        return redirect(url_for("inicio_feed"))

    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    """Autentica al estudiante y lo lleva al feed."""

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

        # NUEVO: después del login vamos al feed.
        return redirect(url_for("inicio_feed"))

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
    """Muestra el perfil personal del estudiante."""

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
    """Permite actualizar los datos personales."""

    if request.method == "POST":

        nombre = request.form.get("nombre", "")
        nombre_usuario = request.form.get(
            "nombre_usuario", ""
        )
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
    """Cierra la sesión del usuario actual."""

    session.clear()

    return redirect(url_for("inicio"))


# ============================================================
# REGISTRO DE USUARIOS
# ============================================================

@app.route("/registro", methods=["GET", "POST"])
def registro():
    """Registra nuevos estudiantes."""

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
    """Solicita un enlace para recuperar la contraseña."""

    if request.method == "POST":

        correo = request.form.get(
            "correo", ""
        ).strip().lower()

        if not correo:

            return render_template(
                "recuperar.html",
                error="Debes introducir tu correo electrónico."
            )

        usuario = usuario_repository.buscar_por_correo(correo)

        if usuario is None:

            return render_template(
                "recuperar.html",
                error="No existe una cuenta asociada a ese correo."
            )

        try:

            token = recuperacion_service.generar_token(
                usuario.id
            )

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

        except Exception:

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
    """Permite establecer una nueva contraseña."""

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
# INTEGRACIÓN DEL MÓDULO DE AMISTADES
# ============================================================

# Registrar una sola vez las rutas de amistades.
#
# Este controlador utiliza:
# - UsuarioService
# - AmistadService
# - GrafoAmistades
# - GestorSolicitudes
# - AmistadRepository
#
# También crea las rutas para:
# - Ver amigos
# - Buscar estudiantes
# - Enviar solicitudes
# - Aceptar solicitudes
# - Rechazar solicitudes
# - Cancelar solicitudes
# - Eliminar amistades

amistad_service = registrar_rutas_amistades(
    app,
    usuario_service,
    requiere_sesion
)


# ============================================================
# PANTALLA PRINCIPAL - FEED SOCIAL UNA
# ============================================================

@app.route("/inicio", methods=["GET"])
@requiere_sesion
def inicio_feed(usuario):
    """
    Página principal de Social UNA.

    Integra las recomendaciones de amistad y prepara
    el espacio para las publicaciones de los estudiantes.
    """

    # =========================================
    # RECOMENDACIONES DE AMISTAD
    # =========================================

    recomendaciones = amistad_service.recomendaciones(
        usuario.id,
        limite=5
    )

    # =========================================
    # SOLICITUDES RECIBIDAS
    # =========================================

    solicitudes_recibidas = (
        amistad_service.obtener_solicitudes_recibidas(
            usuario.id
        )
    )

    cantidad_solicitudes = len(solicitudes_recibidas)

    # =========================================
    # PUBLICACIONES
    # =========================================

    # Provisional: sustituiremos esta lista cuando
    # se integre el servicio real de publicaciones.
    publicaciones = []

    # =========================================
    # RENDERIZAR LA PÁGINA
    # =========================================

    return render_template(
        "inicio.html",
        usuario=usuario,
        recomendaciones=recomendaciones,
        cantidad_solicitudes=cantidad_solicitudes,
        publicaciones=publicaciones
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
