"""Contratos focalizados M50.8. No reemplazan una prueba con Flask/Chromium."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def leer(nombre):
    return (ROOT / nombre).read_text(encoding='utf-8')


class Analisis50_8(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = leer('templates/turborreactor.html')
        cls.css = leer('static/turborreactor.css')
        cls.js = leer('static/estudios_comparador_50_8.js')

    def test_navegacion_prevista_y_ruta_clasica_preservada(self):
        self.assertIn("{% if interfaz=='interactivo' %}<script src=", self.html)
        self.assertIn("filename='estudios_comparador_50_8.js'", self.html)
        self.assertIn("filename='navegacion_superior_50_5.js'", self.html)
        self.assertIn("filename='espacios_ingenieria_50_7.js'", self.html)
        self.assertIn("data-interfaz=\"{{ interfaz }}\"", self.html)

    def test_un_solo_formulario_y_laboratorio(self):
        self.assertEqual(self.html.count('id="turbo-form"'), 1)
        self.assertEqual(self.html.count('id="turbo-study49-form"'), 1)
        self.assertEqual(self.html.count('class="turbo-lab50"'), 1)
        self.assertEqual(self.html.count('id="estudio49"'), 1)
        self.assertIn('id="study49-apply"', self.html)
        self.assertIn('data-lab-action="save"', self.html)

    def test_49_5_50_4_y_comparador_siguen_siendo_unicos(self):
        explorador = leer('static/estudios_parametricos_49_5.js')
        motor = leer('static/turborreactor_interactivo.js')
        lab = leer('static/laboratorio_comparativo_50_1.js') if (ROOT/'static/laboratorio_comparativo_50_1.js').exists() else ''
        self.assertIn("'/api/turborreactor/estudio'", explorador)
        self.assertIn('brayton:aplicar-estudio-50-4', explorador)
        self.assertIn('brayton:aplicar-estudio-50-4', motor)
        self.assertIn('aplicarPunto50_4(', motor)
        self.assertIn('documento.querySelector(\'[data-study49-view="punto"]\')?.click()', motor)
        if lab:
            self.assertIn('let referencia=null', lab)
            self.assertIn('function guardar()', lab)
        self.assertNotIn('fetch(', self.js)
        self.assertNotIn('XMLHttpRequest', self.js)

    def test_tres_vistas_estudios_y_comparador(self):
        for nombre in ['barridos', 'mapa', 'clasicos', 'prestaciones', 'graficas', 'condiciones']:
            self.assertIn("'"+nombre+"'", self.js)
        for id in ('estudio49', 'sensibilidad', 'mapa', 'turbo-lab50'):
            self.assertIn(id, self.js)
        self.assertIn('turbo-ana58-info', self.js)
        self.assertIn('appendChild(estudio)', self.js)
        self.assertIn('classList.add(\'turbo-50-8-ready\')', self.js)

    def test_seleccion_estado_y_celda_sin_calculo(self):
        self.assertIn('elegirEstudios', self.js)
        self.assertIn('confirm(', self.js)
        self.assertIn('aviso.hidden=false', self.js)
        self.assertIn('botonAplicar.disabled=true', self.js)
        self.assertIn("forma.addEventListener('input'", self.js)
        self.assertIn("formMotor?.addEventListener('input'", self.js)
        self.assertIn("controladorNavegacion50_5.navegar(id)", self.js)

    def test_distribucion_responsive_y_foco(self):
        self.assertIn('.turbo-study49-grid', self.css)
        self.assertIn('.turbo-ana58-info', self.css)
        self.assertIn('.turbo-ana58-lab-tab:focus-visible', self.css)
        self.assertIn('max-width:820px', self.css)
        self.assertIn('grid-template-columns:minmax(0,1fr)', self.css)
        self.assertIn("setAttribute('role','tablist')", self.js)
        self.assertIn("'ArrowRight'", self.js)

    def test_sintaxis_jinja_js(self):
        from jinja2 import Environment
        Environment().parse(self.html)
        js = ROOT/'static/estudios_comparador_50_8.js'
        p = subprocess.run(['node', '--check', str(js)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_regresion_js_dom(self):
        p = subprocess.run(['node', str(ROOT/'tests/js/test_estudios_comparador_50_8.cjs')],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('71 verificaciones correctas', p.stdout)


if __name__ == '__main__':
    unittest.main()
