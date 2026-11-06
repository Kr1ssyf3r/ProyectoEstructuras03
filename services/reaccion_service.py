from models.reaccion import Reaccion
from repositories.reaccion_repository import ReaccionRepository


class ReaccionService:
    """Reglas de negocio para dar, quitar y consultar "Me gusta"."""

    def __init__(
        self,
        usuario_service,
        repositorio=None,
        publicacion_existe=None
    ):
        self.usuario_service = usuario_service

        self.repositorio = (
            repositorio
            if repositorio is not None
            else ReaccionRepository()
        )

        # Función opcional (id_publicacion -> bool) que aportará el módulo
        # de publicaciones. Si es None, todavía no se valida la publicación.
        self.publicacion_existe = publicacion_existe

    def _exigir_usuario(self, usuario_id):
        if self.usuario_service.obtener_usuario(usuario_id) is None:
            raise ValueError("El usuario no existe.")

    def _exigir_publicacion(self, publicacion_id):
        if (
            self.publicacion_existe is not None
            and not self.publicacion_existe(publicacion_id)
        ):
            raise ValueError("La publicación no existe.")

    def dar_me_gusta(self, usuario_id, publicacion_id):
        """Da "Me gusta". Devuelve True si lo dio, False si ya lo había dado."""

        self._exigir_usuario(usuario_id)
        self._exigir_publicacion(publicacion_id)

        return self.repositorio.agregar(
            Reaccion(usuario_id, publicacion_id)
        )

    def quitar_me_gusta(self, usuario_id, publicacion_id):
        """Quita "Me gusta". Devuelve True si lo quitó, False si no existía."""

        self._exigir_usuario(usuario_id)

        return self.repositorio.eliminar(usuario_id, publicacion_id)

    def alternar_me_gusta(self, usuario_id, publicacion_id):
        """Da o quita el "Me gusta". Devuelve True si queda dado."""

        if self.repositorio.existe(usuario_id, publicacion_id):
            self.quitar_me_gusta(usuario_id, publicacion_id)
            return False

        self.dar_me_gusta(usuario_id, publicacion_id)
        return True

    def ya_dio_me_gusta(self, usuario_id, publicacion_id):
        return self.repositorio.existe(usuario_id, publicacion_id)

    def contar_me_gusta(self, publicacion_id):
        return self.repositorio.contar(publicacion_id)

    def publicaciones_con_me_gusta(self, usuario_id):
        return self.repositorio.publicaciones_de(usuario_id)
