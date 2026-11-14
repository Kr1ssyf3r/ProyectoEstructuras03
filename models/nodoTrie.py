#CLASE QUE REPRESENTA UN NODO DEL ARBOL TRIE 
#CADA NODO ES UNA LETRA DEL NOMBRE DE UN USUARIO, ESTE SE EXTRAE DE LOS USUARIOS REGISTRADOS EN EL SISTEMA 
#CADA QUE SE INCIA EL SISTEMA O SE REGISTRA UN NUEVO USUARIO, SE CREA EL ARBOL TRIE CON LOS NOMBRES DE USUARIO PARA PODER BUSCAR AMIGOS POR NOMBRE DE USUARIO
#ADEMAS DE ESO SI YA HAY UNA RUTA PREESTABLECIADA NO SE CREAN NUEVOS NODOS SINO QUE SE REUTILIZAN LOS YA EXISTENTES 
#ES DECIR MARIA Y MARIANA REUTILIZAN LA RAMA QUE VA DE M-A-R-I-A(EN A TERMINA UNA)- AGREGA A-N-A Y TERMINA MARIANA 

class NodoTrie:
    #__slots__ le dice a python que el nodo SOLO va a tener estos dos atributos.
    #asi no crea un diccionario interno por cada nodo y se ahorra memoria,
    #lo cual se nota cuando el arbol tiene muchos nodos. No tiene que ver con duplicados
    __slots__ = ("hijos", "ids_usuarios")

    def __init__(self):

        #los hijos se guardan como letra -> NodoTrie.
        #el nodo no guarda su propia letra, la letra es la clave con la que su padre lo tiene
        self.hijos = {} #los hijos que tiene cada nodo del arbol basicamente 

        #la "banderita" de fin de palabra. En vez de un True/False guarda los ids de los usuarios
        #cuya palabra termina en este nodo. Es un set para que un mismo id no se repita
        #(y porque dos usuarios distintos pueden tener la misma palabra, por ejemplo dos "Ana")
        self.ids_usuarios = set() # se guarda el id del usuario al final, si hay varios kenan entonces esos id se guardan en el set, y al set no permitir duplicados nos aseguramos que sean diferentes cuentas con un mismo nombre 

    def tiene_hijo(self, letra):
        """Indica si ya existe un camino hacia esa letra."""
        return letra in self.hijos

    def obtener_hijo(self, letra):
        """Devuelve el hijo de esa letra, o None si no existe."""
        return self.hijos.get(letra)

    def agregar_hijo(self, letra):
        """Crea el hijo de esa letra y lo devuelve."""
        nuevo = NodoTrie()
        self.hijos[letra] = nuevo
        return nuevo

    def marcar_fin(self, id_usuario):
        """Pone la banderita: una palabra de este usuario termina aqui."""
        self.ids_usuarios.add(id_usuario) #se usa al final para cuando ya se tiene el nombre completo el ultimo nodo guarde el id de su usuario en su set 

    def quitar_fin(self, id_usuario):
        """Quita la banderita de este usuario (discard no falla si no estaba)."""
        self.ids_usuarios.discard(id_usuario) #saca el id del set , si no estaba no pasa nada , esto en caso de eliminacion de cuentas o asi 