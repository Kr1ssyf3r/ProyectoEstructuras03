"""Rutas de amistades para integrarse sin reemplazar app.py."""
import hmac
import secrets

from flask import (abort,flash,jsonify,redirect,render_template,request,session,url_for)
from services.amistadService import AmistadService


def registrar_rutas_amistades(app, usuario_service, requiere_sesion):
    amistad_service = AmistadService(usuario_service=usuario_service)

    def csrf_token():
        if 'csrf_amigos' not in session:
            session['csrf_amigos'] = secrets.token_urlsafe(32)
        return session['csrf_amigos']

    def validar_csrf():
        esperado = session.get('csrf_amigos', '')
        recibido = request.form.get('csrf_token', '')
        if not esperado or not hmac.compare_digest(esperado, recibido):
            abort(400, description='Formulario inválido o expirado.')

    def volver(tab, q=''):
        destino = url_for('amigos', q=q) if q else url_for('amigos')
        return redirect(f'{destino}#{tab}')

    @app.get('/amigos')
    @requiere_sesion
    def amigos(usuario):
        q = request.args.get('q', '').strip()[:100]
        resultados = []
        if q:
            busqueda = q.casefold()
            for candidato in usuario_service.listar_usuarios():
                if candidato.id == usuario.id:
                    continue
                if busqueda not in candidato.nombre.casefold() and busqueda not in candidato.usuario.casefold():
                    continue
                resultados.append({
                    'usuario': candidato,
                    'estado': amistad_service.estado_entre(usuario.id, candidato.id),
                })
            resultados.sort(key=lambda item: (item['usuario'].nombre.casefold(), item['usuario'].id))

        recibidas = []
        for solicitud in amistad_service.obtener_solicitudes_recibidas(usuario.id):
            emisor = usuario_service.obtener_usuario(solicitud.id_emisor)
            if emisor is not None:
                recibidas.append({'solicitud': solicitud, 'usuario': emisor})

        enviadas = []
        for solicitud in amistad_service.obtener_solicitudes_enviadas(usuario.id):
            receptor = usuario_service.obtener_usuario(solicitud.id_receptor)
            if receptor is not None:
                enviadas.append({'solicitud': solicitud, 'usuario': receptor})

        return render_template(
            'amigos.html',
            amigos=amistad_service.obtener_amigos(usuario.id),
            recibidas=recibidas,
            enviadas=enviadas,
            resultados=resultados,
            recomendaciones=amistad_service.recomendaciones(usuario.id, limite=10) if not q else [],
            q=q,
            csrf_token=csrf_token(),
        )

    @app.post('/amigos/solicitar/<id_receptor>')
    @requiere_sesion
    def amigos_solicitar(usuario, id_receptor):
        validar_csrf()
        q = request.form.get('q', '').strip()[:100]
        try:
            amistad_service.enviar_solicitud(usuario.id, id_receptor)
            flash('Solicitud enviada correctamente.', 'success')
        except ValueError as exc:
            flash(str(exc), 'error')
        return volver('descubrir', q)

    @app.post('/amigos/aceptar/<id_solicitud>')
    @requiere_sesion
    def amigos_aceptar(usuario, id_solicitud):
        validar_csrf()
        try:
            amistad_service.aceptar_solicitud(id_solicitud, usuario.id)
            flash('Solicitud aceptada.', 'success')
        except (ValueError, PermissionError) as exc:
            flash(str(exc), 'error')
        return volver('solicitudes')

    @app.post('/amigos/rechazar/<id_solicitud>')
    @requiere_sesion
    def amigos_rechazar(usuario, id_solicitud):
        validar_csrf()
        try:
            amistad_service.rechazar_solicitud(id_solicitud, usuario.id)
            flash('Solicitud rechazada.', 'success')
        except (ValueError, PermissionError) as exc:
            flash(str(exc), 'error')
        return volver('solicitudes')

    @app.post('/amigos/cancelar/<id_solicitud>')
    @requiere_sesion
    def amigos_cancelar(usuario, id_solicitud):
        validar_csrf()
        try:
            amistad_service.cancelar_solicitud(id_solicitud, usuario.id)
            flash('Solicitud cancelada.', 'success')
        except (ValueError, PermissionError) as exc:
            flash(str(exc), 'error')
        return volver('solicitudes')

    @app.post('/amigos/eliminar/<id_amigo>')
    @requiere_sesion
    def amigos_eliminar(usuario, id_amigo):
        validar_csrf()
        try:
            amistad_service.eliminar_amistad(usuario.id, id_amigo)
            flash('Amistad eliminada.', 'success')
        except ValueError as exc:
            flash(str(exc), 'error')
        return volver('amigos')

    
    # ============================================================
    # API - NOTIFICACIONES DE SOLICITUDES DE AMISTAD
    # ============================================================

    @app.get("/api/amistades/notificaciones")
    @requiere_sesion
    def notificaciones_amistades(usuario):
        """
        Devuelve la cantidad de solicitudes pendientes
        recibidas por el estudiante autenticado.

        No modifica el grafo ni las solicitudes.
        """

        recibidas = amistad_service.obtener_solicitudes_recibidas(
            usuario.id
        )

        return jsonify({
            "cantidad": len(recibidas)
        })

    return amistad_service
