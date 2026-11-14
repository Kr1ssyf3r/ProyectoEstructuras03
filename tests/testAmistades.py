import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from repositories.usuario_repository import UsuarioRepository
from repositories.amistadRepository import AmistadRepository
from services.usuario_service import UsuarioService   # ajustá al nombre real de tu archivo
from services.amistadService import AmistadService


class TestIntegracion(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

        self.usuarios = UsuarioService(
            UsuarioRepository(self.dir / "usuarios.json")
        )
        self.amistades = AmistadService(
            self.usuarios,
            AmistadRepository(self.dir / "relaciones.json")
        )

        self.ana = self._registrar("Ana", "ana")
        self.beto = self._registrar("Beto", "beto")
        self.carla = self._registrar("Carla", "carla")

    def _registrar(self, nombre, usuario):
        return self.usuarios.registrar_usuario(
            nombre, usuario, f"{usuario}@mail.com", "clave1234", "clave1234"
        )

    def test_flujo_completo(self):
        soli = self.amistades.enviar_solicitud(self.ana.id, self.beto.id)
        self.assertEqual(
            self.amistades.estado_entre(self.ana.id, self.beto.id), "pendiente"
        )

        self.amistades.aceptar_solicitud(soli.id_solicitud, self.beto.id)
        amigos = self.amistades.obtener_amigos(self.ana.id)
        self.assertEqual([u.nombre for u in amigos], ["Beto"])

    def test_recomendacion_entre_usuarios_reales(self):
        for x, y in ((self.ana, self.beto), (self.beto, self.carla)):
            s = self.amistades.enviar_solicitud(x.id, y.id)
            self.amistades.aceptar_solicitud(s.id_solicitud, y.id)

        recs = self.amistades.recomendaciones(self.ana.id)
        self.assertEqual([(u.nombre, p) for u, p in recs], [("Carla", 1)])

    def test_cambiar_perfil_no_rompe_la_amistad(self):
        s = self.amistades.enviar_solicitud(self.ana.id, self.beto.id)
        self.amistades.aceptar_solicitud(s.id_solicitud, self.beto.id)

        self.usuarios.actualizar_perfil(
            self.ana.id, "Ana Maria", "anamaria", "ana@mail.com"
        )
        amigos = self.amistades.obtener_amigos(self.beto.id)
        self.assertEqual([u.nombre for u in amigos], ["Ana Maria"])

    def test_reiniciar_conserva_todo(self):
        s = self.amistades.enviar_solicitud(self.ana.id, self.beto.id)
        self.amistades.aceptar_solicitud(s.id_solicitud, self.beto.id)

        usuarios2 = UsuarioService(UsuarioRepository(self.dir / "usuarios.json"))
        amistades2 = AmistadService(
            usuarios2, AmistadRepository(self.dir / "relaciones.json")
        )
        self.assertEqual(len(amistades2.obtener_amigos(self.ana.id)), 1)

    def test_usuario_borrado_se_limpia_al_arrancar(self):
        s = self.amistades.enviar_solicitud(self.ana.id, self.beto.id)
        self.amistades.aceptar_solicitud(s.id_solicitud, self.beto.id)

        # se borra el usuario directo en el repository (simula inconsistencia)
        self.usuarios.repositorio.eliminar(self.ana.id)

        amistades2 = AmistadService(
            self.usuarios, AmistadRepository(self.dir / "relaciones.json")
        )
        self.assertEqual(amistades2.obtener_amigos(self.beto.id), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)