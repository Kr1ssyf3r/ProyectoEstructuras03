"""Rutas HTTP del perfil del estudiante."""
from flask import Blueprint, current_app, redirect, render_template, request, url_for

from controllers.decorators import requiere_sesion


perfil_bp = Blueprint("perfil", __name__)


@perfil_bp.get("/perfil")
@requiere_sesion
def perfil(usuario):
    """Muestra el perfil personal del estudiante."""
    return render_template("perfil.html", usuario=usuario)


@perfil_bp.route("/perfil/editar", methods=["GET", "POST"])
@requiere_sesion
def editar_perfil(usuario):
    """Permite actualizar los datos personales."""
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        nombre_usuario = request.form.get("nombre_usuario", "")
        correo = request.form.get("correo", "")

        try:
            current_app.extensions["social_una"]["usuario_service"].actualizar_perfil(
                id_usuario=usuario.id,
                nombre=nombre,
                nombre_usuario=nombre_usuario,
                correo=correo,
            )
            return redirect(url_for("perfil.perfil"))
        except ValueError as error:
            return render_template(
                "editar_perfil.html",
                usuario=usuario,
                error=str(error),
            )

    return render_template("editar_perfil.html", usuario=usuario)
