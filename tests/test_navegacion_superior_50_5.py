"""M50.5: contratos HTML/CSS/JS de navegación sin cargar física ni Flask.

Son verificaciones estáticas; no sustituyen una prueba visual con navegador.
"""
from pathlib import Path
import unittest

from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'templates' / 'turborreactor.html'
CSS = ROOT / 'static' / 'turborreactor.css'
JS = ROOT / 'static' / 'navegacion_superior_50_5.js'


class Navegacion50_5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML.read_text(encoding='utf-8')
        cls.css = CSS.read_text(encoding='utf-8')
        cls.js = JS.read_text(encoding='utf-8')

    def test_plantilla_sintaxis_jinja(self):
        Environment().parse(self.html)

    def test_exactamente_siete_espacios_declarados(self):
        for clave in ('simulacion','motor','termodinamica','tobera',
                      'turbomaquinas','estudios','comparador'):
            self.assertIn(f"('{clave}',", self.html)
        self.assertEqual(self.html.count("data-workspace-view=\"{{ clave }}\""), 1)
        self.assertIn('id="turbo-work-nav50"', self.html)

    def test_aislamiento_ruta_interactiva(self):
        self.assertIn("{% if interfaz=='interactivo' %}<script src=", self.html)
        self.assertIn("filename='navegacion_superior_50_5.js'", self.html)
        self.assertIn("{% if interfaz=='interactivo' %}\n<div class=\"turbo-work-header50\"", self.html)
        self.assertIn('body[data-interfaz="interactivo"].turbo-50-5-ready', self.css)

    def test_unico_formulario_y_puntos_de_anclaje(self):
        self.assertEqual(self.html.count('id="turbo-form"'), 1)
        for id_ in ['turbo-live','estudio49','configuracion','resultados',
                    'estaciones','graficas','sensibilidad','mapa','turbo-diagnostic-50-2']:
            self.assertEqual(self.html.count(f'id="{id_}"'), 1, id_)

    def test_conservacion_controladores(self):
        for name in ['turborreactor_interactivo.js','laboratorio_comparativo_50_1.js',
                     'diagnostico_motor_50_2.js','configuraciones_modo_c_50_3.js',
                     'estudios_parametricos_49_5.js']:
            self.assertIn(f"filename='{name}'", self.html)
        self.assertNotIn('fetch(', self.js)
        self.assertNotIn('controlador.cambiar(', self.js)

    def test_estado_compartido_e_historial(self):
        for literal in ['data-estado','MutationObserver','history.pushState',
                        'popstate','hashchange',"form.addEventListener('input'",
                        'aria-current','fragmento50_5']:
            self.assertIn(literal, self.js)

    def test_responsive_y_mejora_progresiva(self):
        self.assertIn('overflow-x:auto', self.css)
        self.assertIn('position:sticky', self.css)
        self.assertIn('@media (max-width:390px)', self.css)
        self.assertIn('.turbo-work-header50{display:none}', self.css)
        self.assertIn('turbo-50-5-ready', self.js)


if __name__ == '__main__':
    unittest.main()
