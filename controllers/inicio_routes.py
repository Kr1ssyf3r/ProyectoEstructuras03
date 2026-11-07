"""Rutas HTTP de la pantalla principal y el feed."""
from flask import Blueprint, current_app, render_template

from controllers.decorators import requiere_sesion


inicio_bp = Blueprint("inicio", __name__)

# Cantidad máxima de publicaciones que se muestran en el feed.
LIMITE_FEED = 20


@inicio_bp.get("/inicio")
@requiere_sesion
def inicio_feed(usuario):
    """Muestra recomendaciones, amistades y solicitudes pendientes."""
    servicios = current_app.extensions["social_una"]
    amistad_service = servicios["amistad_service"]
    feed_service = servicios["feed_service"]

    recomendaciones = amistad_service.recomendaciones(usuario.id, limite=5)
    amigos_comunes_por_usuario = {}

    for candidato, cantidad in recomendaciones:
        amigos_comunes_por_usuario[candidato.id] = amistad_service.amigos_en_comun(
            usuario.id,
            candidato.id,
        )

    solicitudes_recibidas = amistad_service.obtener_solicitudes_recibidas(usuario.id)
    cantidad_solicitudes = len(solicitudes_recibidas)

    tarjetas = feed_service.construir_feed(usuario, limite=LIMITE_FEED)

    return render_template(
        "inicio.html",
        usuario=usuario,
        recomendaciones=recomendaciones,
        amigos_comunes_por_usuario=amigos_comunes_por_usuario,
        cantidad_solicitudes=cantidad_solicitudes,
        tarjetas=tarjetas,
    )
