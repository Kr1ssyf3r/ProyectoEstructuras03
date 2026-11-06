import heapq
from dataclasses import dataclass
from itertools import islice

from models.publicacion import Publicacion
from models.usuario import Usuario


@dataclass(frozen=True)
class TarjetaFeed:
    """Una puplicacion lista para pintar en el feed."""

    publicacion: Publicacion
    usuario: Usuario
    cantidad_me_gusta: int
    yo_di_me_gusta: bool


class FeedService:
    """Construye el feed del estudiante: sus publicaciones y las de sus amigos"""

    def __init__(
        self,
        amistad_service,
        publicacion_service,
        reaccion_service,
        usuario_service=None,
    ):
        self.amistad_service = amistad_service
        self.publicacion_service = publicacion_service
        self.reaccion_service = reaccion_service
        self.usuario_service = usuario_service

    def _autores_visibles(self, usuario):
        """Devuelve {id: Usuario} con el propio usuario y sus amigos."""

        autores = {usuario.id: usuario}

        for amigo in self.amistad_service.amigos(usuario.id):
            autores[amigo.id] = amigo

        return autores

    def _armar_tarjetas(self, usuario, autores, limite):
        """Mezcla las publicaciones de los autores y arma las tarjetas."""

        # Cada lista llega ya ordenada de la mas reciente a la mas antigua. Se mezclan con heapq.merge.
        listas = [
            self.publicacion_service.obtener_publicaciones_usuario(autor_id)
            for autor_id in autores
        ]

        mezcla = heapq.merge(*listas, key=lambda p: p.fecha, reverse=True)

        if limite is not None:
            mezcla = islice(mezcla, limite)

        return [
            TarjetaFeed(
                publicacion=publicacion,
                usuario=autores[publicacion.autor_id],
                cantidad_me_gusta=self.reaccion_service.contar_me_gusta(publicacion.id),
                yo_di_me_gusta=self.reaccion_service.ya_dio_me_gusta(usuario.id, publicacion.id)
            )
            for publicacion in mezcla
        ]

    def construir_feed(self, usuario, limite=None):
        """Feed del usuario: de la publicación más reciente a la más antigua."""

        if self.usuario_service is not None and self.usuario_service.obtener_usuario(usuario.id) is None:
            raise ValueError("No se encontró el usuario")

        autores = self._autores_visibles(usuario)

        return self._armar_tarjetas(usuario, autores, limite)

    def filtrar_por_autor(self, usuario, autor_id, limite=None):
        """Publicaciones de un solo autor (el propio usuario o un amigo)."""

        autores = self._autores_visibles(usuario)

        if autor_id not in autores:
            raise ValueError(
                "Solo puedes ver publicaciones tuyas o de tus amigos."
            )

        return self._armar_tarjetas(
            usuario, {autor_id: autores[autor_id]}, limite
        )