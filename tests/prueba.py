import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)   # para que Python encuentre models, services, etc.
os.chdir(RAIZ)             # para que data/ se cree en la raíz del proyecto

from services.publicacion_service import PublicacionService

s = PublicacionService()
s.crear_publicacion("abc", "Mi primera publicación")
print(s.obtener_publicaciones_usuario("abc"))