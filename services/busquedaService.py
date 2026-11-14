from models.Trie import Trie

#El Trie solo conoce textos e ids,
#aqui se decide que textos se indexan, se filtran los resultados y se reacciona a altas y cambios de usuarios.
#los JSON siguen siendo la fuente de verdad, el Trie es solo un indice en memoria armado a partir de ellos

class BusquedaService:
    def __init__(self, usuario_service, amistad_service=None):
        self.usuario_service = usuario_service
        self.amistad_service = amistad_service
        self.trie = Trie()

        #al arrancar se arma el arbol con todos los usuarios guardados
        self.reconstruir()

        #se apunta como oyente para enterarse cuando alguien se registra o cambia su perfil, es decir
        #hago que la clase este dentro de la lista de oyentes de usuarioService
        usuario_service.suscribir(self) 

    @staticmethod
    def _textos(usuario):
        """Cada palabra del nombre mas el @usuario."""
        #asi "Wellintong Naranjo Corella" se encuentra escribiendo "wel", "nar" o "cor"
        return [*usuario.nombre.split(), usuario.usuario]

    def indexar(self, usuario):
        for texto in self._textos(usuario):
            self.trie.insertar(texto, usuario.id)

    def quitar(self, usuario):
        for texto in self._textos(usuario):
            self.trie.eliminar(texto, usuario.id)

    def reconstruir(self):
        """Arma el arbol desde cero con los usuarios de los JSON."""
        self.trie = Trie()

        for usuario in self.usuario_service.listar_usuarios():
            self.indexar(usuario)

    # ---------------------------------------
    # AVISOS QUE MANDA UsuarioService
    # ---------------------------------------
    def usuario_registrado(self, usuario):
        self.indexar(usuario)

    def usuario_actualizado(self, anterior, nuevo):
        #primero se quitan los textos viejos y luego se insertan los nuevos
        self.quitar(anterior)
        self.indexar(nuevo)

    # ---------------------------------------
    # CONSULTA
    # ---------------------------------------
    def autocompletar(self, id_actual, prefijo, limite=8):
        """Devuelve hasta `limite` sugerencias para el usuario actual."""
        prefijo = prefijo.strip()

        if not prefijo:
            return []

        resultado = []

        #se piden mas ids de los necesarios porque algunos se van a descartar en el filtro
        for id_usuario in self.trie.buscar_prefijo(prefijo, limite + 10):
            if id_usuario == id_actual:
                continue

            usuario = self.usuario_service.obtener_usuario(id_usuario)

            #cuenta borrada: se ignora
            if usuario is None:
                continue

            #si hay bloqueo en cualquier direccion no se sugiere
            if self.amistad_service and self.amistad_service.hay_bloqueo_entre(id_actual, id_usuario):
                continue

            resultado.append({
                "id": usuario.id,
                "nombre": usuario.nombre,
                "usuario": usuario.usuario,
            })

            if len(resultado) >= limite:
                break

        return resultado