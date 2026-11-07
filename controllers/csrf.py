"""Utilidades CSRF compartidas por los controladores."""

import hmac
import secrets

from flask import abort, request, session


def obtener_token(clave_session="csrf_token"):
    """Devuelve el token CSRF de la sesión, generándolo si no existe."""
    if clave_session not in session:
        session[clave_session] = secrets.token_urlsafe(32)

    return session[clave_session]

def validar_token(clave_session="csrf_token"):
    """Aborta con 400 si el token del formulario no coincide con el de la sesion."""
    esperado = session.get(clave_session, "")
    recibido = request.form.get("csrf_token", "")

    if not esperado or not hmac.compare_digest(esperado, recibido):
        abort(400, "Formulario invalido o expirado.")