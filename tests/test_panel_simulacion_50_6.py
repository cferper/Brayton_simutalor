"""M50.6: contrato estático HTML/CSS y Jinja; no reemplaza navegación real."""
from pathlib import Path
import unittest

from jinja2 import Environment

BASE = Path(__file__).resolve().parents[1]
HTML = (BASE / 'templates/turborreactor.html').read_text(encoding='utf8')
CSS = (BASE / 'static/turborreactor.css').read_text(encoding='utf8')
JS = (BASE / 'static/panel_simulacion_50_6.js').read_text(encoding='utf8')
OLDNAV = (BASE / 'static/navegacion_superior_50_5.js').read_text(encoding='utf8')


class PanelSimulacion50_6(unittest.TestCase):
    def test_plantilla_compila(self):
        Environment().parse(HTML)

    def test_unico_formulario_e_identidades(self):
        self.assertEqual(HTML.count('id="turbo-form"'), 1)
        for ident in ('turbo-live','turbo-bank-advanced-toggle',
                      'turbo-bank-advanced-fields','modo_caudal',
                      'turbo-c-example','turbo-reset-design-geometry'):
            self.assertEqual(HTML.count(f'id="{ident}"'), 1, ident)

    def test_no_rompe_navegacion_50_5(self):
        self.assertIn("filename='navegacion_superior_50_5.js'", HTML)
        self.assertIn('id="turbo-work-nav50"', HTML)
        self.assertIn("const ESPACIOS=['simulacion','motor','termodinamica'", OLDNAV)
        self.assertIn("filename='panel_simulacion_50_6.js'", HTML)
        self.assertIn("{% if interfaz=='interactivo' %}<script src=", HTML)
        self.assertLess(HTML.index("filename='navegacion_superior_50_5.js'"),
                        HTML.index("filename='panel_simulacion_50_6.js'"))

    def test_preservacion_controles_modo_y_slider(self):
        self.assertIn('id="{{ nombre }}"', HTML)
        self.assertIn("nombre in ('mach','T3')", HTML)
        for token in ('data-bank-mode="impuesto"','data-bank-mode="fijo"',
                      'data-bank-mode="acoplado"','data-turbo-slider="{{ nombre }}"',
                      'data-c-reset','data-c-example',
                      "nombre == 'gasto_masico_aire'"):
            self.assertIn(token, HTML)
        for token in ("documento.getElementById('mach')", "documento.getElementById('T3')",
                      "documento.getElementById('gasto_masico_aire')",'.turbo-nozzle-config'):
            self.assertIn(token, JS)

    def test_reutiliza_visualizaciones_y_estado(self):
        for token in ('data-live-card="{{ clave }}"', 'data-live-plot="ts"',
                      'data-plot-tab="ts"','data-plot-action="svg"',
                      'data-plot-action="png"','id="turbo-live-status"'):
            self.assertIn(token, HTML)
        self.assertNotIn('fetch(', JS)
        self.assertNotIn('controlador.cambiar(', JS)
        self.assertNotIn('dispatchEvent(', JS)

    def test_panel_avanzado_y_css_responsive(self):
        self.assertIn('turbo-bank-show-advanced', CSS)
        self.assertIn('aria-controls', JS)
        self.assertIn('turbo-sim-primary56', JS)
        for width in ('max-width:1100px','max-width:600px','max-width:390px'):
            self.assertIn(width, CSS)
        self.assertIn('turbo-live-plot-viewer{display:block!important', CSS)

    def test_no_modifica_otros_modelos(self):
        self.assertEqual(HTML.count('id="turbo-form"'), 1)
        self.assertIn('if(documento.body?.dataset.interfaz!==\'interactivo\')return null;', JS)
        self.assertIn('turbo-50-6-ready', CSS)


if __name__ == '__main__':
    unittest.main()
