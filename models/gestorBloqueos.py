# ---------------------------------------
# APARTADO DE BLOQUEOS
# ---------------------------------------
class GestorBloqueos:
    """Bloqueos dirigidos: que A haya bloqueao a B no implica que B haya bloqueado a A."""

    def __init__(self):
        self._bloqueos: dict[str, set[str]] = {}#es igual que una soli en estructura, un diccionario que tiene como llave el id del emisor y como valor un set con la lista de bloqueados

    def bloquear(self, emisor: str, receptor: str) -> bool:
        #validacion para no bloquear vacio o a uno mismo
        if not emisor or not receptor or emisor == receptor:
            raise ValueError("No puedes bloquearte a ti mismo.")
        
        destino = self._bloqueos.setdefault(emisor, set())#se añade el emisor y si set de bloqueados
       #si el receptor ya esta en el set de bloqueados del emisor, retorna False
        if receptor in destino:
            return False
        #si el receptor no esta en el set de bloqueados del emisor, se agrega
        destino.add(receptor)#destinos es una referencia de los bloqueados del emisor entonces si se agrega al original
        return True

    def desbloquear(self, emisor: str, receptor: str) -> bool:
        destino = self._bloqueos.get(emisor) #obtiene el emisor y su ser de bloqueados
        if not destino or receptor not in destino:
            return False
        destino.remove(receptor) #remueve de su "lista" de bloqueados al receptor
        if not destino:
            del self._bloqueos[emisor] #si el set de bloqueados del emisor queda vacio, se elimina la llave del diccionario
        return True

    #funcion que verifica si un usuario ha bloqueado a otro
    def ha_bloqueado(self, emisor: str, receptor: str) -> bool:
        return receptor in self._bloqueos.get(emisor, set())

    #funcion que verifica si existe un bloqueo entre dos usuarios
    def existe_bloqueo_entre(self, id1: str, id2: str) -> bool:
        return self.ha_bloqueado(id1, id2) or self.ha_bloqueado(id2, id1)

    #funcion que retorna todos los usuarios bloqueados por un usuario, se usa copy para que no se pueda modificar
    def obtener_bloqueados(self, emisor: str) -> set[str]:
        return self._bloqueos.get(emisor, set()).copy()

    #metodo que elimina a un usuario de la lista de bloqueos, tanto como emisor como receptor, se usa para cuando un usuario se elimina de la plataforma
    def eliminar_usuario(self, usuario: str) -> None:
        self._bloqueos.pop(usuario, None)
        for emisor in list(self._bloqueos):
            self._bloqueos[emisor].discard(usuario)
            if not self._bloqueos[emisor]:
                del self._bloqueos[emisor]


    #-------------------------------------------------------------------------------
    # METODOS DE PERSISTENCIA
    #-------------------------------------------------------------------------------
    def exportar(self) -> dict[str, list[str]]:
        return {u: sorted(ids) for u, ids in sorted(self._bloqueos.items()) if ids}

    @classmethod
    def desde_datos(cls, datos):
        if not isinstance(datos, dict):
            raise ValueError("Los bloqueos deben ser un diccionario.")
        gestor = cls()
        for emisor, receptores in datos.items():
            if not isinstance(emisor, str) or not emisor:
                raise ValueError("Emisor de bloqueo inválido.")
            if not isinstance(receptores, list) or any(not isinstance(i, str) or not i for i in receptores):
                raise ValueError("Lista de bloqueos inválida.")
            if len(receptores) != len(set(receptores)) or emisor in receptores:
                raise ValueError("Bloqueos duplicados o hacia uno mismo.")
            for receptor in receptores:
                gestor.bloquear(emisor, receptor)
        return gestor
