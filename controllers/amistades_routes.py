"""Blueprint del módulo de amistades."""
import hmac
import secrets

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from controllers.decorators import requiere_sesion


def crear_amistades_blueprint(usuario_service, amistad_service,busqueda_service):#ahora recibe busqueda_service para poder pasarle a amistad_service y que este pueda usarlo para filtrar usuarios bloqueados en el autocompletar
    """Construye el Blueprint de amistades con sus dependencias."""
    bp = Blueprint("amistades", __name__)

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
        destino = (
            url_for('amistades.amigos', q=q)
            if q
            else url_for('amistades.amigos')
        )
        return redirect(f'{destino}#{tab}')

    @bp.get('/amigos')
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

        # Obtener los nombres de los amigos en común, para mostrar en la sección de recomendaciones
        recomendaciones_detalladas = []
        if not q:
            for candidato, cantidad in amistad_service.recomendaciones(
                usuario.id,
                limite=10
            ):
                amigos_comunes = amistad_service.amigos_en_comun(
                    usuario.id,
                    candidato.id
                )

                recomendaciones_detalladas.append({
                    "usuario": candidato,
                    "cantidad": cantidad,
                    "amigos_comunes": amigos_comunes
                })

        return render_template(
            'amigos.html',
            amigos=amistad_service.obtener_amigos(usuario.id),
            recibidas=recibidas,
            enviadas=enviadas,
            resultados=resultados,
            recomendaciones=recomendaciones_detalladas,
            # Usuarios que la cuenta activa tiene bloqueados.
            bloqueados=amistad_service.obtener_usuarios_bloqueados(usuario.id),
            q=q,
            csrf_token=csrf_token(),
        )

    @bp.post('/amigos/solicitar/<id_receptor>')
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

    @bp.post('/amigos/aceptar/<id_solicitud>')
    @requiere_sesion
    def amigos_aceptar(usuario, id_solicitud):
        validar_csrf()
        try:
            amistad_service.aceptar_solicitud(id_solicitud, usuario.id)
            flash('Solicitud aceptada.', 'success')
        except (ValueError, PermissionError) as exc:
            flash(str(exc), 'error')
        return volver('solicitudes')

    @bp.post('/amigos/rechazar/<id_solicitud>')
    @requiere_sesion
    def amigos_rechazar(usuario, id_solicitud):
        validar_csrf()
        try:
            amistad_service.rechazar_solicitud(id_solicitud, usuario.id)
            flash('Solicitud rechazada.', 'success')
        except (ValueError, PermissionError) as exc:
            flash(str(exc), 'error')
        return volver('solicitudes')

    @bp.post('/amigos/cancelar/<id_solicitud>')
    @requiere_sesion
    def amigos_cancelar(usuario, id_solicitud):
        validar_csrf()
        try:
            amistad_service.cancelar_solicitud(id_solicitud, usuario.id)
            flash('Solicitud cancelada.', 'success')
        except (ValueError, PermissionError) as exc:
            flash(str(exc), 'error')
        return volver('solicitudes')

    @bp.post('/amigos/eliminar/<id_amigo>')
    @requiere_sesion
    def amigos_eliminar(usuario, id_amigo):
        validar_csrf()
        try:
            amistad_service.eliminar_amistad(usuario.id, id_amigo)
            flash('Amistad eliminada.', 'success')
        except ValueError as exc:
            flash(str(exc), 'error')
        return volver('amigos')


    # ---------------------------------------
    # APARTADO DE BLOQUEOS
    # ---------------------------------------
    @bp.post('/amigos/bloquear/<id_bloqueado>')
    @requiere_sesion
    def amigos_bloquear(usuario, id_bloqueado):
        #validamos el token csrf para evitar que otra pagina pueda
        #enviar formularios de bloqueo sin autorizacion del usuario
        validar_csrf()

        #obtenemos la busqueda para regresar al mismo apartado
        #si el bloqueo se hizo desde los resultados del buscador
        q = request.form.get('q', '').strip()[:100]

        try:
            #el service registra el bloqueo y elimina cualquier
            #amistad o solicitud pendiente entre ambos usuarios
            amistad_service.bloquear_usuario(usuario.id, id_bloqueado)
            flash('Usuario bloqueado correctamente.', 'success')

        except ValueError as exc:
            flash(str(exc), 'error')

        return volver('descubrir', q)

    @bp.post('/amigos/desbloquear/<id_bloqueado>')
    @requiere_sesion
    def amigos_desbloquear(usuario, id_bloqueado):
        #validamos el token csrf antes de modificar los bloqueos
        validar_csrf()

        try:
            #solamente elimina el bloqueo que realizo el usuario activo
            #no restaura amistades ni solicitudes anteriores
            amistad_service.desbloquear_usuario(usuario.id, id_bloqueado)
            flash('Usuario desbloqueado correctamente.', 'success')

        except ValueError as exc:
            flash(str(exc), 'error')

        return volver('bloqueados')

    
    # ============================================================
    # API - NOTIFICACIONES DE SOLICITUDES DE AMISTAD
    # ============================================================

    @bp.get("/api/amistades/notificaciones")
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

    # ============================================================
    # API - AUTOCOMPLETAR BUSQUEDA (TRIE)
    # ============================================================
    @bp.get('/amigos/autocompletar')
    @requiere_sesion
    def amigos_autocompletar(usuario):
        """Devuelve sugerencias de usuarios segun el prefijo escrito."""
        #se corta a 100 caracteres igual que la busqueda normal de /amigos
        q = request.args.get('q', '').strip()[:100]

        #la ruta solo traduce HTTP: toda la logica (Trie, filtro de bloqueos) vive en BusquedaService
        return jsonify(busqueda_service.autocompletar(usuario.id, q))
    
    return bp
