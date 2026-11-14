"""Milestone 50.7: contratos de DOM, integración y sintaxis Jinja, sin motor real."""
from pathlib import Path
import unittest
from jinja2 import Environment

BASE = Path(__file__).resolve().parents[1]
HTML = (BASE / 'templates/turborreactor.html').read_text(encoding='utf8')
CSS = (BASE / 'static/turborreactor.css').read_text(encoding='utf8')
JS = (BASE / 'static/espacios_ingenieria_50_7.js').read_text(encoding='utf8')
NAV = (BASE / 'static/navegacion_superior_50_5.js').read_text(encoding='utf8')


class EspaciosIngenieria50_7(unittest.TestCase):
    def test_plantilla_compila(self):
        Environment().parse(HTML)

    def test_cuatro_espacios_y_siete_nombres_estables(self):
        for clave in ('motor','termodinamica','tobera','turbomaquinas'):
            self.assertIn(f"('{clave}',", HTML)
            self.assertIn("'" + clave + "'", JS)
        self.assertIn("'comparador'", NAV)
        self.assertEqual(HTML.count('data-workspace-view="{{ clave }}"'), 1)

    def test_unico_formulario_y_unica_galeria(self):
        for ident in ('turbo-form','turbo-live','turbo-diagnostic-50-2',
                      'estaciones','graficas','turbo-characterization-list'):
            self.assertEqual(HTML.count(f'id="{ident}"'), 1, ident)
        self.assertIn("documento.getElementById('turbo-live')", JS)
        self.assertNotIn('cloneNode', JS)

    def test_selecciones_reutilizan_controlador_m48(self):
        for key in ('ts','temperaturas','presiones','trabajos','balance',
                    'mach','presion','temperatura_tobera','velocidad_tobera','geometria'):
            self.assertIn("'"+key+"'", JS)
            self.assertIn(f'data-plot-panel="{key}"', HTML) if key in ('ts','mach','presion','geometria') else None
        self.assertIn('original?.click()', JS)
        self.assertNotIn('fetch(', JS)
        self.assertEqual(JS.count('dispatchEvent('), 1)
        self.assertIn(".dispatchEvent(new Event('click',{bubbles:true}))", JS)

    def test_50_5_es_unico_propietario_del_visor(self):
        self.assertIn('destinoVisor50_7?.(espacio)', NAV)
        self.assertIn('ventana.activarEspacioIngenieria50_7?.(espacio)', NAV)
        self.assertIn('paneles[espacio]).appendChild(live)', NAV)
        self.assertIn('ventana.destinoVisor50_7=espacio', JS)
        self.assertIn("anexar('turbomaquinas','.turbo-characterization')", NAV)

    def test_aislamiento_de_rutas_y_regresion_50_6(self):
        self.assertIn("filename='panel_simulacion_50_6.js'", HTML)
        self.assertIn("filename='espacios_ingenieria_50_7.js'", HTML)
        self.assertLess(HTML.index("filename='panel_simulacion_50_6.js'"),
                        HTML.index("filename='espacios_ingenieria_50_7.js'"))
        self.assertIn("{% if interfaz=='interactivo' %}<script src=", HTML)
        self.assertIn('turbo-50-6-ready', CSS)
        self.assertIn('body[data-interfaz="interactivo"].turbo-50-7-ready', CSS)

    def test_turbomaquinas_sin_fisica_ficticia(self):
        for texto in ('No hay visor de mapa HPT', 'Rline', 'modo C',
                      'no disponibles', 'NASA T-MATS'):
            self.assertIn(texto, JS)
        self.assertNotIn('surge_margin', JS)
        self.assertNotIn('resolver_motor_acoplado', JS)

    def test_accesibilidad_y_responsive(self):
        for token in ('aria-pressed','aria-label','addEventListener(\'keydown\'',
                      'ArrowRight','ArrowLeft','Home','End','focus()'):
            self.assertIn(token, JS)
        for token in ('max-width:820px','max-width:500px','overflow-x:auto',
                      '.turbo-ing57-content[hidden]'):
            self.assertIn(token, CSS)

    def test_ninguna_api_nueva_ni_nuevos_formularios(self):
        self.assertNotIn('/api/', JS)
        self.assertNotIn('createElement(\'form\')', JS)
        self.assertEqual(HTML.count('id="turbo-form"'), 1)


if __name__ == '__main__':
    unittest.main()
