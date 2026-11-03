"""Decoradores compartidos por los controladores HTTP."""
from functools import wraps

from flask import current_app, redirect, session, url_for


def requiere_sesion(funcion):
    """Comprueba que exista un usuario autenticado antes de continuar."""

    @wraps(funcion)
    def funcion_protegida(*args, **kwargs):
        servicios = current_app.extensions["social_una"]
        usuario_id = session.get("usuario_id")

        if not usuario_id:
            return redirect(url_for("autenticacion.inicio"))

        usuario = servicios["usuario_service"].obtener_usuario(usuario_id)

        if usuario is None:
            session.clear()
            return redirect(url_for("autenticacion.inicio"))

        return funcion(usuario, *args, **kwargs)

    return funcion_protegida
