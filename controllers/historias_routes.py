"""Blueprint del modulo de historias."""
import hmac
import secrets

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    request,
    send_from_directory,
    session,
    url_for,
)

from controllers.decorators import requiere_sesion


def crear_historias_blueprint(historia_service, carpeta_media):
    """Construye el Blueprint de historias con sus dependencias."""
    bp = Blueprint("historias", __name__)

    def csrf_token():
        if 'csrf_historias' not in session:
            session['csrf_historias'] = secrets.token_urlsafe(32)
        return session['csrf_historias']

    def validar_csrf():
        esperado = session.get('csrf_historias', '')
        recibido = request.form.get('csrf_token', '')
        if not esperado or not hmac.compare_digest(esperado, recibido):
            abort(400, description='Formulario invalido o expirado.')

    #---------- SUBIR ----------
    @bp.post('/historias/crear')
    @requiere_sesion
    def crear(usuario):
        validar_csrf()

        #"archivo" es la clave del formulario: llega como FileStorage
        archivo = request.files.get('archivo')

        try:
            historia_service.crear_historia(usuario.id, archivo)
            flash('Historia publicada.', 'success')
        except ValueError as exc:
            flash(str(exc), 'error')

        return redirect(url_for('inicio.inicio_feed'))

    #---------- SERVIR EL ARCHIVO ----------
    @bp.get('/historias/archivo/<nombre>')
    @requiere_sesion
    def archivo(usuario, nombre):
        historia = historia_service.obtener_por_archivo(nombre)

        #misma regla de visibilidad que la lista: si no puede verla, 404
        #(404 y no 403, para no confirmar que el archivo existe)
        if historia is None or not historia_service.puede_ver(usuario.id, historia):
            abort(404)

        return send_from_directory(carpeta_media, nombre)

    #---------- ELIMINAR ----------
    @bp.post('/historias/eliminar/<id_historia>')
    @requiere_sesion
    def eliminar(usuario, id_historia):
        validar_csrf()

        try:
            historia_service.eliminar_historia(id_historia, usuario.id)
            flash('Historia eliminada.', 'success')
        except ValueError as exc:
            flash(str(exc), 'error')

        return redirect(url_for('inicio.inicio_feed'))

    #expone el token para que los templates lo usen: {{ csrf_historias() }}
    bp.csrf_token = csrf_token

    return bp