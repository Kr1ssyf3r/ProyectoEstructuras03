#grafo de las amistades de los usuarios, representado como un diccionario de adyacencia.

#uso de set() porque es mas eficiente para verificar si un usuario es amigo de otro, y para evitar duplicados. (temasd de bigO)

class GrafoAmistades:
    def __init__(self):
        #la lista de adyacencia es un diccionario que contiene el uuid de un usuario (que es un string) y cada usuario tiene su lista de amigos como un set de strings (uuid de los amigos).
        self._adyacencia: dict[str, set[str]] = {} #declaraciond de la estructura de datos que representa el grafo de amistades, empieza el dic vacio


    #metodo para agregar un usuario al grafo, si el usuario ya existe, retorna False, si no existe, lo agrega y retorna True.
    #ademas de este usuario empieza con un set vacio, nuevamente el set es para evitar duplicados y para que sea mas eficiente verificar si un usuario es amigo de otro.
    def agregar_usuario(self, id_usuario: str) -> bool:
        if id_usuario in self._adyacencia:
            return False
        self._adyacencia[id_usuario] = set() 
        return True

    #bool simple que verifica si un usuario existe en el grafo, retorna True si existe, False si no existe.
    def existe_usuario(self, id_usuario: str) -> bool:
        return id_usuario in self._adyacencia


    #metodo que agrega amistades , como tal este no se va a encargar de hacerlo direcamente porque primero va la solicitud de amistad
    #que eso es un modelo por aparte que viene tipo (id del solicitante)->(id del solicitado) , ese tipo de solis vienen en un diccionario
    #una vez aceptada obtiene el id del solicitante y el id del solicitado y se llama a este metodo para agregar la amistad
    #una vez obtenidos se actualizan ambos sets de amigos de cada usuario porque es una amistad bidireccional 
    def agregar_amistad(self, id1: str, id2: str) -> bool:
        #verificaciones sencillas
        if id1 == id2:
            raise ValueError("No se permite una amistad consigo mismo.")
        if not self.existe_usuario(id1) or not self.existe_usuario(id2):
            raise ValueError("Ambos usuarios deben existir en el grafo.")
        #verifica si ya son amigos, si ya lo son retorna False, si no lo son agrega la amistad y retorna True
        if id2 in self._adyacencia[id1]:
            return False
        #agrega la amistad bidireccionalmente
        self._adyacencia[id1].add(id2)
        self._adyacencia[id2].add(id1)
        return True


    #elimina la amistad entre dos usuarios
    #a como los amigos son bidireccionales las eliminaciones tambien lo son
    def eliminar_amistad(self, id1: str, id2: str) -> bool:
        #verificaciones sencillas, si alguno de los dos usuarios no existe en el grafo,
        # si no son amigos retorna False, si son amigos elimina la amistad y retorna True
        if id1 not in self._adyacencia or id2 not in self._adyacencia:
            return False
        if id2 not in self._adyacencia[id1]:
            return False
        #eliminacion bidireccional de la amistad
        self._adyacencia[id1].remove(id2)
        self._adyacencia[id2].remove(id1)
        return True

    #elimina un usuario del grafo, y elimina todas las amistades que tenia ese usuario
    def eliminar_usuario(self, id_usuario: str) -> bool:
        #si no existe en el grafo
        if id_usuario not in self._adyacencia:
            return False
        
        #eliminacion de cada uno de sus amigos de la lista de adyacencia del usuario que se va a eliminar, aqui viene la utilidad del set() 
        # porque es mas eficiente eliminar un elemento de un set que de una lista, y ademas no hay duplicados
        for amigo in self._adyacencia[id_usuario]:
            self._adyacencia[amigo].remove(id_usuario)
        #se elimina el usuario del grafo
        del self._adyacencia[id_usuario]
        return True

    #funcion que verifica si dos usuarios son amigos, retorna True si lo son, False si no lo son
    def son_amigos(self, id1: str, id2: str) -> bool:
        #verifica si el id2 esta en el set de amigos del id1, es decir , busca el id1 en la lista de adyacencia
        #si no lo encuentra retorna el set(),en caso de si comprueba si hay una arista con id2 
        return id2 in self._adyacencia.get(id1, set())

    #obtiene los amigos de un usuario, (es decir sus aristas) y lo retorna como un set de strings (uuid de los amigos)
    def obtener_amigos(self, id_usuario: str) -> set[str]:
        if id_usuario not in self._adyacencia:
            raise ValueError("El usuario no pertenece al grafo.")
        #retorna una copia del set de amigos del usuario, para evitar que se modifique el set original desde fuera de la clase
        return self._adyacencia[id_usuario].copy()

    #funcion que obtiene los amigos en comun entre dos usuarios, se le pasa los ids a comparar 
    #y retona los uuids de los amigos que tienen en comun
    def amigos_en_comun(self, id1: str, id2: str) -> set[str]:
        #obtiene los amigos de ambos ids y retona la interseccion de ambos sets
        return self.obtener_amigos(id1) & self.obtener_amigos(id2)

    #obtiene la cantidad de amigos basicamente si el nodo tiene 5 aristas retorna 5 , es decir 5 amigos 
    def obtener_grado(self, id_usuario: str) -> int:
        return len(self.obtener_amigos(id_usuario))


    #funcion que recomienda amigos a un usuario, basandose en los amigos en comun que tiene con otros usuarios,
    #retorna una lista de tuplas (id_candidato, numero_en_comun)
    def recomendar_amigos(self, id_usuario: str, limite: int = 10) -> list[tuple[str, int]]:
        """Sugerencias por amigos en común: (id_candidato, número_en_común)."""
        if limite < 0:
            raise ValueError("El límite no puede ser negativo.")
        directos = self.obtener_amigos(id_usuario)
        puntuaciones: dict[str, int] = {}
        for amigo in directos:
            for candidato in self._adyacencia[amigo]:
                if candidato != id_usuario and candidato not in directos:
                    puntuaciones[candidato] = puntuaciones.get(candidato, 0) + 1
        return sorted(puntuaciones.items(),key=lambda x: (-x[1], x[0]))[:limite]

    #metodo para la persistencia del grafo, convierte el grafo a un formato compatible con JSON, es decir un diccionario de listas de strings
    def exportar(self) -> dict[str, list[str]]:
        """Convierte el grafo a un formato compatible con JSON."""
        return {usuario: sorted(amigos)for usuario, amigos in self._adyacencia.items()}

    #JSON no permite sets (que es lo que usamos , es decir un diccionario que tiene 3: {1,2,3} ) ,
    #por eso se convierte a listas de strings (uuid de los amigos) para poder guardarlo en un archivo JSON
    @classmethod
    def desde_datos(cls, datos: dict[str, list[str]]):
        """Reconstruye y valida simetría, ausencia de lazos y de duplicados."""
        if not isinstance(datos, dict):
            raise ValueError("Las amistades deben ser un diccionario.")

        grafo = cls()
        for usuario in datos:
            if not isinstance(usuario, str) or not usuario:
                raise ValueError("UUID de vértice inválido.")
            grafo.agregar_usuario(usuario)

        for usuario, vecinos in datos.items():
            if not isinstance(vecinos, list) or len(vecinos) != len(set(vecinos)):
                raise ValueError("Lista de amistades inválida o duplicada.")
            for amigo in vecinos:
                if not isinstance(amigo, str) or amigo not in datos or amigo == usuario:
                    raise ValueError("Amistad con usuario inexistente o consigo mismo.")
                if usuario not in datos[amigo]:
                    raise ValueError("Las amistades guardadas no son bidireccionales.")
                grafo.agregar_amistad(usuario, amigo)

        return grafo