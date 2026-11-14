#clase que se encarga de administrar los archivos multimedia (imágenes y videos) en la aplicación. 
#Se encarga de guardar y eliminar archivos, así como de validar su tipo y tamaño.
#esta resposabilidad se separa de la clase Publicacion para mantener un diseño limpio y modular, 
#siguiendo el principio de responsabilidad única. asi no se duplica la logica de manejo de archivos al 
#implementar cosas como las historias 
import os
import uuid


class MultimediaService:
    BYTES_POR_MB = 1024 * 1024

    def __init__(self,carpeta_media,extensiones_imagen=None,extensiones_video=None,max_imagen=5 * BYTES_POR_MB,max_video=25 * BYTES_POR_MB):
        self.carpeta_media = carpeta_media

        self.extensiones_imagen = extensiones_imagen or {
            "jpg", "jpeg", "png", "gif", "webp"
        }

        self.extensiones_video = extensiones_video or {
            "mp4", "webm"
        }

        self.max_imagen = max_imagen
        self.max_video = max_video

    # ---------------------------------------
    # METODOS INTERNOS
    # ---------------------------------------

    @staticmethod
    def _obtener_extension(nombre_archivo):
        """Devuelve la extension en minusculas, o '' si no tiene."""
        #rsplit corta por el ULTIMO punto, asi "mi.foto.final.PNG" da "png"
        if "." not in nombre_archivo:
            return ""

        return nombre_archivo.rsplit(".", 1)[-1].lower()

    def _clasificar(self, extension):
        """Devuelve (tipo, limite en bytes) segun la extension."""
        if extension in self.extensiones_imagen:
            return "imagen", self.max_imagen

        if extension in self.extensiones_video:
            return "video", self.max_video

        raise ValueError("El formato del archivo no está permitido.")

    @staticmethod
    def _medir_tamano(archivo):
        """Devuelve el peso del archivo en bytes sin leerlo completo."""
        #se salta al final, la posicion actual es el total de bytes, y se vuelve al inicio
        archivo.stream.seek(0, os.SEEK_END)
        tamano = archivo.stream.tell()

        #el seek(0) final es obligatorio: si no, save() empezaria a leer desde el final y guardaria un archivo vacio
        archivo.stream.seek(0)

        return tamano

    def _validar_tamano(self, archivo, limite):
        """Lanza ValueError si el archivo supera el limite."""
        if self._medir_tamano(archivo) > limite:
            maximo_mb = limite // self.BYTES_POR_MB
            raise ValueError(
                f"El archivo es muy grande (máximo {maximo_mb} MB)."
            )

    def _ruta_de(self, nombre_archivo):
        """Ruta completa de un archivo dentro de la carpeta de medios."""
        return os.path.join(self.carpeta_media, nombre_archivo)

    # ---------------------------------------
    # METODOS PUBLICOS
    # ---------------------------------------

    #en estos metodos constantemente se trabaja con los "archivos" reales , un FileStorage, que es la representacion de la foto o video
    #en bytes de la ram , solo con el save del final se copian para guardaros en la ruta de imagenes 
    def guardar_archivo(self, archivo):
        """Valida y guarda el archivo. Devuelve (nombre, tipo) o (None, None)."""

        #una publicacion solo de texto no trae archivo, se devuelven dos None
        #para que quien llama pueda hacer "nombre, tipo = ..." sin errores
        if archivo is None or not archivo.filename:
            return None, None

        #archivo es un FileStorage: representa la foto o video que envio el navegador.
        #la extension, el tipo y el tamano se validan sin leer el contenido (solo el nombre y la posicion del stream)
        extension = self._obtener_extension(archivo.filename)
        tipo, limite = self._clasificar(extension)
        self._validar_tamano(archivo, limite)

        os.makedirs(self.carpeta_media, exist_ok=True)

        #nunca se usa el nombre original del usuario: evita choques (dos "foto.png")
        #y nombres raros como "../../app.py"
        nombre = f"{uuid.uuid4()}.{extension}"
        
        #los bytes se escriben en disco con ESE nombre , es decir uuid.png/mp4 
        archivo.save(self._ruta_de(nombre))

        return nombre, tipo  #retorna el nombre del archivo guardado y su tipo ("imagen" o "video")

    def eliminar_archivo(self, nombre_archivo):
        """Borra un archivo de la carpeta de medios si existe."""
        if not nombre_archivo:
            return

        # Evita que se intente eliminar un archivo fuera de la carpeta.
        #basename deja solo el nombre final, si es distinto al original traia una ruta
        if os.path.basename(nombre_archivo) != nombre_archivo:
            raise ValueError("Nombre de archivo no válido.")

        ruta = self._ruta_de(nombre_archivo)

        if os.path.exists(ruta):
            os.remove(ruta)