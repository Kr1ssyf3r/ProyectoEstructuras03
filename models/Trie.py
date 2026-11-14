import unicodedata #sirve para la normalizacion de los nombres de usuario, para que no importe si tienen tildes o mayusculas, se busca todo en minusculas y sin tildes

from models.nodoTrie import NodoTrie #nodos individuales del arbol de prefijos


class Trie:
    """Arbol de prefijos para autocompletar nombres."""

    def __init__(self):
        #la raiz no representa ninguna letra, solo es el punto de partida de todos los caminos
        self.raiz = NodoTrie()

        #contador de nodos creados (sin contar la raiz), sirve para mostrar el tamano del arbol en la exposicion
        self.total_nodos = 0



    # ---------------------------------------
    # NORMALIZACION
    # ---------------------------------------
    @staticmethod
    def normalizar(texto):
        """Pasa a minusculas y quita las tildes: 'José' queda como 'jose'."""

        #1) casefold pasa todo a minusculas
        minusculas = texto.casefold()

        #2) NFD separa cada letra acentuada en dos caracteres: la letra base y el acento suelto
        #(la é pasa a ser 'e' + un acento aparte)
        descompuesto = unicodedata.normalize("NFD", minusculas)

        #3) los acentos sueltos tienen categoria "Mn" (marca de combinacion), se descartan y quedan las letras base
        letras = []
        for caracter in descompuesto:
            if unicodedata.category(caracter) != "Mn":
                letras.append(caracter)

        #retorna el texto normalizado como un solo string, sin tildes y en minusculas.
        #se usa join porque el ciclo deja las letras separadas en una lista, y join las pega de nuevo en un string
        return "".join(letras)

    
    # ---------------------------------------
    # INSERTAR
    # ---------------------------------------
    def insertar(self, texto, id_usuario):
        """Agrega una palabra al arbol, creando solo los tramos que no existan.""" #existe la rama k-e-v-i-n, entonces para ingresar kenan se reutiliza k-e y se añade de hijo de e, n-a-n mientras que sigue mantienedo de hijo tambien a v-i-n

        nodo = self.raiz

        for letra in self.normalizar(texto): #llama al texto ingresado ya normalizado 
            
            #si el camino ya existe se reutiliza, si no, se crea
            if not nodo.tiene_hijo(letra):
                nodo.agregar_hijo(letra)
                self.total_nodos += 1

            #se baja un nivel, ya sea por el nodo nuevo o por el que ya estaba
            nodo = nodo.obtener_hijo(letra)

        #al terminar la palabra se pone la banderita en el ultimo nodo
        nodo.marcar_fin(id_usuario)#ya aqui se termina de ingresar el nombre completo de un usuario 

    # ---------------------------------------
    # BUSCAR
    # ---------------------------------------
    #metodo privado que baja por el arbol hasta el nodo donde termina el prefijo , basicamente es una funcion auxiliar de buscar_prefijo
    def _nodo_del_prefijo(self, prefijo):
        """Baja por el prefijo letra a letra y devuelve el nodo donde termina."""

        nodo = self.raiz

        for letra in self.normalizar(prefijo):
            nodo = nodo.obtener_hijo(letra)

            #si una letra no existe, nadie empieza con ese prefijo
            if nodo is None:
                return None

        return nodo

    def buscar_prefijo(self, prefijo, limite=8):
        """Devuelve los ids de los usuarios cuya palabra empieza con el prefijo."""

        inicio = self._nodo_del_prefijo(prefijo) #retorna el nodo donde termina el prefijo de forma recursiva 

        if inicio is None:
            return []

        resultado = []

        #DFS iterativo: la pila guarda los nodos que faltan por visitar
        pila = [inicio]

        while pila and len(resultado) < limite:
            nodo = pila.pop()

            #se recogen los ids de la banderita de este nodo, sin repetir
            for id_usuario in sorted(nodo.ids_usuarios):
                if id_usuario not in resultado:
                    resultado.append(id_usuario)

            #se agregan los hijos a la pila. La pila saca primero el ultimo que entro,
            #por eso se meten en orden inverso, asi se visita primero la 'a' y al final la 'z'
            for letra in sorted(nodo.hijos, reverse=True):
                pila.append(nodo.obtener_hijo(letra))

        return resultado

    # ---------------------------------------
    # ELIMINAR
    # ---------------------------------------
    def eliminar(self, texto, id_usuario):
        """Quita la banderita de un usuario en una palabra."""

        nodo = self._nodo_del_prefijo(texto)

        #solo se quita la banderita, los nodos se quedan porque otras palabras pueden compartir ese camino.
        #las ramas vacias son inofensivas, nunca producen resultados
        if nodo is not None:
            nodo.quitar_fin(id_usuario)