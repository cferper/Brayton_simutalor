"""Controles estructurales del M49.3 sin depender del servidor Flask."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InterfazBanco49_3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "templates/turborreactor.html").read_text(encoding="utf-8")
        cls.js = (ROOT / "static/turborreactor_interactivo.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "static/turborreactor.css").read_text(encoding="utf-8")

    def test_modos_visibles_sin_duplicar_campo(self):
        self.assertEqual(self.html.count('name="modo_caudal"'), 1)
        for modo in ("impuesto", "fijo", "acoplado"):
            self.assertIn(f'data-bank-mode="{modo}"', self.html)
        self.assertIn("selectorModo.value=b.dataset.bankMode", self.js)
        self.assertIn("dispatchEvent(new Event('change'", self.js)

    def test_parametros_y_avanzados(self):
        self.assertIn('id="turbo-bank-advanced-toggle"', self.html)
        self.assertIn('aria-expanded="false"', self.html)
        self.assertIn('turbo-bank-show-advanced', self.js)
        self.assertIn('data-bank-mode="fijo"', self.css)
        self.assertIn('data-bank-mode="acoplado"', self.css)
        self.assertIn('data-bank-mode="impuesto"', self.css)

    def test_tres_rutas_y_modo_clasico_conservados(self):
        source = (ROOT / "web_app.py").read_text(encoding="utf-8")
        for route in ('/turborreactor/interactivo', '/turborreactor', '/brayton'):
            self.assertIn(route, source)
        self.assertIn('data-interfaz="interactivo"', self.css)
        self.assertEqual(self.html.count('id="turbo-form"'), 1)

    def test_galeria_ts_prioritario_y_sin_calcular_al_cambiar(self):
        for clave in ('ts', 'mach', 'presion', 'geometria'):
            self.assertIn(f'data-plot-tab="{clave}"', self.html)
            self.assertIn(f'data-live-plot="{clave}"', self.html)
        self.assertIn("activarGrafica('ts')", self.js)
        self.assertIn("b.addEventListener('click',()=>activarGrafica", self.js)
        self.assertIn("dibujar('ts',svg.svg_ts)", self.js)
        self.assertIn('reconciliarPestañas()', self.js)

    def test_disponibilidad_sin_ceros_artificiales(self):
        self.assertIn('data-live-card="{{ clave }}"', self.html)
        self.assertIn('tarjeta.hidden=!disponible', self.js)
        self.assertIn("datos.modo==='impuesto'", self.js)
        self.assertIn("datos.modo!=='acoplado'", self.js)
        self.assertIn('mostrarTodos(', self.js)
        self.assertIn('onError:error=>', self.js)


if __name__ == "__main__":
    unittest.main()
