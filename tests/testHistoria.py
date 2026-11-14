import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.historia import Historia
from repositories.historiaRepository import HistoriaRepository

repo = HistoriaRepository("data/historias_prueba.json")

h1 = Historia("usuario1", "foto.png", "imagen")
h2 = Historia(
    "usuario2", "clip.mp4", "video",
    fecha_creacion=datetime.now() - timedelta(hours=30)   #ya expirada
)

repo.guardar([h1, h2])
cargadas = repo.cargar()

for h in cargadas:
    print(h.autor_id, h.archivo, "vigente:", h.esta_vigente())