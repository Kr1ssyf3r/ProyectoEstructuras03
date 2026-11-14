"""Blueprint del módulo de publicaciones."""
import hmac
import os
import secrets

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from controllers.decorators import requiere_sesion


def crear_publicaciones_blueprint(publicacion_service):
    bp = Blueprint("publicaciones", __name__)

    def csrf_token():
        # Un código secreto por sesión, para que otra página no pueda
        # enviar formularios en nombre del usuario.
        if "csrf_publicaciones" not in session:
            session["csrf_publicaciones"] = secrets.token_urlsafe(32)
        return session["csrf_publicaciones"]

    def validar_csrf():
        esperado = session.get("csrf_publicaciones", "")
        recibido = request.form.get("csrf_token", "")
        if not esperado or not hmac.compare_digest(esperado, recibido):
            abort(400, description="Formulario inválido o expirado.")

    @bp.app_context_processor
    def inyectar_csrf():
        # Deja csrf_publicaciones() disponible en cualquier template (la usa Inicio)
        return {"csrf_publicaciones": csrf_token}

    @bp.get("/publicaciones")
    @requiere_sesion
    def muro(usuario):
        publicaciones = publicacion_service.obtener_publicaciones_usuario(usuario.id)
        # Si la dirección trae ?editar=3, esa tarjeta se muestra como formulario
        editando = request.args.get("editar")
        return render_template(
            "publicaciones.html",
            usuario=usuario,
            publicaciones=publicaciones,
            editando=editando,
            csrf_token=csrf_token(),
        )

    @bp.post("/publicaciones/crear")
    @requiere_sesion
    def crear(usuario):
        validar_csrf()
        try:
            publicacion_service.crear_publicacion(
                usuario.id,
                request.form.get("contenido", ""),
                request.files.get("archivo"),
            )
            flash("Publicación creada.", "success")
        except ValueError as error:
            flash(str(error), "error")
        return redirect(url_for("publicaciones.muro"))

    @bp.get("/publicaciones/media/<nombre>")
    @requiere_sesion
    def media(usuario, nombre):
        # Entrega la foto o video guardado (solo a usuarios con sesión).
        # La carpeta ahora vive en MultimediaService, no en PublicacionService.
        carpeta = os.path.abspath(publicacion_service.multimedia_service.carpeta_media)
        return send_from_directory(carpeta, nombre)

    @bp.post("/publicaciones/<id_publicacion>/editar")
    @requiere_sesion
    def editar(usuario, id_publicacion):
        validar_csrf()
        try:
            publicacion_service.editar_publicacion(
                id_publicacion, usuario.id, request.form.get("contenido", "")
            )
            flash("Publicación actualizada.", "success")
        except ValueError as error:
            flash(str(error), "error")
            # Volvemos al modo edición para que pueda corregir el texto
            return redirect(url_for("publicaciones.muro", editar=id_publicacion))
        return redirect(url_for("publicaciones.muro"))

    @bp.post("/publicaciones/<id_publicacion>/eliminar")
    @requiere_sesion
    def eliminar(usuario, id_publicacion):
        validar_csrf()
        try:
            publicacion_service.eliminar_publicacion(id_publicacion, usuario.id)
            flash("Publicación eliminada.", "success")
        except ValueError as error:
            flash(str(error), "error")
        return redirect(url_for("publicaciones.muro"))

    return bp