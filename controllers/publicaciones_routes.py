"""Blueprint del módulo de publicaciones."""
from flask import Blueprint, render_template

from controllers.decorators import requiere_sesion


def crear_publicaciones_blueprint(publicacion_service, usuario_service):
    bp = Blueprint("publicaciones", __name__)

    @bp.get("/publicaciones")
    @requiere_sesion
    def muro(usuario):
        #Pide al servicio las publicaciones de este usuario
        publicaciones = publicacion_service.obtener_publicaciones_usuario(usuario.id)
        return render_template(
            "publicaciones.html",
            usuario=usuario,
            publicaciones=publicaciones,
        )

    return bp