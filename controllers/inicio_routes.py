"""Rutas HTTP de la pantalla principal y el feed."""
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from controllers.decorators import requiere_sesion


inicio_bp = Blueprint("inicio", __name__)

# Cantidad máxima de publicaciones que se muestran en el feed.
LIMITE_FEED = 20


@inicio_bp.get("/inicio")
@requiere_sesion
def inicio_feed(usuario):
    """Muestra el feed, recomendaciones, amistades y solicitudes pendientes."""
    servicios = current_app.extensions["social_una"]
    amistad_service = servicios["amistad_service"]
    feed_service = servicios["feed_service"]
    usuario_service = servicios["usuario_service"]

    # Parámetro opcional ?autor=<id>: ver solo las publicaciones de una persona.
    autor_id = request.args.get("autor", "").strip()[:100]
    autor_filtrado = None

    if autor_id:
        try:
            tarjetas = feed_service.filtrar_por_autor(
                usuario, autor_id, limite=LIMITE_FEED
            )
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("inicio.inicio_feed"))

        autor_filtrado = usuario_service.obtener_usuario(autor_id)
    else:
        tarjetas = feed_service.construir_feed(usuario, limite=LIMITE_FEED)

    recomendaciones = amistad_service.recomendaciones(usuario.id, limite=5)
    amigos_comunes_por_usuario = {}

    for candidato, cantidad in recomendaciones:
        amigos_comunes_por_usuario[candidato.id] = amistad_service.amigos_en_comun(
            usuario.id,
            candidato.id,
        )

    solicitudes_recibidas = amistad_service.obtener_solicitudes_recibidas(usuario.id)
    cantidad_solicitudes = len(solicitudes_recibidas)

    return render_template(
        "inicio.html",
        usuario=usuario,
        recomendaciones=recomendaciones,
        amigos_comunes_por_usuario=amigos_comunes_por_usuario,
        cantidad_solicitudes=cantidad_solicitudes,
        tarjetas=tarjetas,
        autor_filtrado=autor_filtrado,
    )
