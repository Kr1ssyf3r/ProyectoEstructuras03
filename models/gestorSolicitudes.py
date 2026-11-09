from models.solicitudAmistad import SolicitudAmistad
#gestor de las solicitudes de amistad, se encarga de almacenar y gestionar las solicitudes de amistad

class GestorSolicitudes:
    #uso de dos diccionarios para almacenar las solicitudes de amistad, uno para almacenar las solicitudes por id de solicitud
    #y otro para almacenar las solicitudes por pareja de usuarios (id_emisor, id_receptor) para evitar duplicados y para poder buscar si existe una solicitud entre dos usuarios sin importar el orden.
    def __init__(self):
        #uso de diccionarios por eficiencia y evitar duplicados
        self._solicitudes: dict[str, SolicitudAmistad] = {} #diccionario que guarda el id de la soli y objetos solicitud de amistad (tiene toda la info de como es una soli)

        # Índice sin dirección: impide A→B y B→A simultáneamente.
        #indice auxiliar de la clase, su objetivo es comprobar rápidamente si ya existe una solicitud pendiente entre dos estudiantes.
        #frozenset es la version inmutable del set(), se necesita porque un set normal no es hashable y no puede ser llave de un diccionario
        #como frozenset((A,B)) == frozenset((B,A)), el orden no importa y por eso no pueden existir A->B y B->A al mismo tiempo
        self._por_pareja: dict[frozenset[str], str] = {} #guarda el num de solicitud


    def agregar_solicitud(self, solicitud: SolicitudAmistad) -> bool:
        pareja = frozenset((solicitud.id_emisor, solicitud.id_receptor))#se le pasa una soli  y se guarda en el diccionario auxiliar de pareja

        if (solicitud.id_solicitud in self._solicitudes or pareja in self._por_pareja):
            return False #comprobar si ya existe la solicitud en el diccionario de solicitudes o si ya existe una solicitud entre los dos usuarios en el diccionario de parejas

        self._solicitudes[solicitud.id_solicitud] = solicitud #si pasa la validacion, se agrega la soli a solicitudes, es decir idSoli-Solicitud
        self._por_pareja[pareja] = solicitud.id_solicitud #aqui se crea el indice por pareja , se guarda la pareja con frozenset y el id de la soli
        return True

    def buscar_solicitud(self, id_solicitud: str) -> SolicitudAmistad | None:
        return self._solicitudes.get(id_solicitud) #busca una solicitud de amistad por su id y se busca en el diccionario dicha soli(retorna el objeto de solicitudAmistad)

    def existe_solicitud(self, id1: str, id2: str) -> bool:
        return frozenset((id1, id2)) in self._por_pareja    #este es un booleano que verifica si 2 usuarios tienen una solicitud , se usa por pareja porque para comprobar si existe una un set que tenga esos dos ids dentro de por_pareja

    #(CAMBIO) metodo publico nuevo que retorna todas las solicitudes guardadas.
    #antes el service tenia que entrar directo a gestor._solicitudes (atributo privado) y eso rompe el encapsulamiento,
    #ahora el service solo llama a listar() y el gestor decide como entregar los datos
    #retorna una lista nueva (copia) para que desde fuera no puedan modificar el diccionario original
    def listar(self) -> list[SolicitudAmistad]:
        return list(self._solicitudes.values())


    #O(n) siendo N la cantidad de solicitudes que hayan
    def obtener_recibidas(self, id_usuario: str) -> list[SolicitudAmistad]: #se le pasa un id de usuario
        return [                                        #retorna una lista de solicitudes de amistad que ha recibido ese usuario
            s for s in self._solicitudes.values()
            if s.id_receptor == id_usuario]



    #O(n) siendo N la cantidad de solicitudes que hayan
    def obtener_enviadas(self, id_usuario: str) -> list[SolicitudAmistad]:
        return [                      #lo mismo que la anterior , retorna las solicitudes de amistad que ha enviado un usuario
            s for s in self._solicitudes.values()
            if s.id_emisor == id_usuario]  #busca las que el id emisor sea igual al id que le enviamos



    def eliminar_solicitud(self, id_solicitud: str) -> SolicitudAmistad | None:  #se le pasa el id de solicitud a eliminar
        solicitud = self._solicitudes.pop(id_solicitud, None) #se guarda la solicitud que se va a eliminar en una variable

        #si la soli no es None entonces procede a eliminarla del diccionario de parejas, para que no quede un indice huérfano
        if solicitud is not None:
            pareja = frozenset((solicitud.id_emisor,solicitud.id_receptor)) #una vez se sabe que soli se va a sacar se obtienen ambos ids y se guarda en (pareja, que es la pareja de usuarios)

            #(CAMBIO) antes era self._por_pareja.pop(pareja) sin valor por defecto, y si el indice se desincronizaba
            #por algun motivo lanzaba KeyError y la eliminacion se quedaba a medias.
            #ahora con pop(pareja, None) si la pareja no esta simplemente no hace nada y la limpieza termina bien
            self._por_pareja.pop(pareja, None)#y se saca esa pareja de usuarios del diccionario de parejas, para que no quede un indice huérfano, es decir que quede una pareja de usuarios sin una solicitud asociada
        return solicitud #retorna la solicitud eliminada


    #este metodo se usa para eliminar todas las solicitudes de amistad que tenga un usuario
    #esto en caso de eliminar la cuenta de un usuario, para que no queden solicitudes huérfanas en el sistema o en caso de suspender la cuenta
    def eliminar_solicitudes_usuario(self, id_usuario: str) -> int:
        #se arma primero la lista de ids y despues se elimina, para no modificar el diccionario mientras se recorre
        ids = [
            s.id_solicitud
            for s in self._solicitudes.values()
            if id_usuario in (s.id_emisor, s.id_receptor)]

        for id_solicitud in ids:
            self.eliminar_solicitud(id_solicitud)

        return len(ids) #retorna la cantidad de solicitudes eliminadas

    def exportar(self) -> list[dict]:
        return [s.to_dict() for s in self._solicitudes.values()]

    @classmethod
    def desde_datos(cls, datos: list[dict]):
        if not isinstance(datos, list):
            raise ValueError("Las solicitudes deben ser una lista.")

        gestor = cls()

        for dato in datos:
            #(CAMBIO) aqui no hace falta capturar TypeError, porque from_dict (en SolicitudAmistad) ahora valida
            #las claves y el tipo del dato, asi que si el JSON esta mal formado siempre sale un ValueError
            solicitud = SolicitudAmistad.from_dict(dato)

            if not gestor.agregar_solicitud(solicitud):
                raise ValueError("Solicitud duplicada en los datos persistidos.")

        return gestor