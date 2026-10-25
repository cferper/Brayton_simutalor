"""Verifica presentación educativa cp(T) sin recalcular ni cambiar física."""

import re
import unittest
from html import unescape
from pathlib import Path

from ciclo_cp_variable import resolver_ciclo
from educacion_cp_variable import AYUDAS_CP, AYUDAS_MAPA, CONTENIDOS, construir_educacion_cp
from web_app import app


BASE = {'T1': '288.15', 'T3': '1600', 'rp': '10', 'p1': '100',
        'eta_c': '0.85', 'eta_t': '0.9', 'delta': '0.05'}
ROOT = Path(__file__).resolve().parents[1]
SECCIONES = ('simulacion', 'resultados', 'optimizacion', 'sensibilidad',
             'mapa', 'segunda_ley', 'informes', 'ayuda')


class RevisionEducativaCP(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def _post(self, accion, **extra):
        result = self.client.post('/', data={**BASE, 'accion': accion, **extra})
        self.assertEqual(result.status_code, 200)
        return result.get_data(as_text=True)

    def test_ocho_secciones_con_dos_vistas_educativas(self):
        html = self.client.get('/').get_data(as_text=True)
        for seccion in SECCIONES:
            with self.subTest(seccion=seccion):
                self.assertIn(f'data-edu-tabs="{seccion}"', html)
                self.assertIn(f'id="{seccion}"', html)
        self.assertEqual(html.count('Fundamentos y procedimiento</button>'), 8)
        self.assertEqual(html.count('Qué vamos a hacer'), 8)
        self.assertEqual(html.count('edu-deep-grid'), 8)

    def test_contenidos_extensos_con_ocho_bloques_cientificos(self):
        datos = construir_educacion_cp()
        self.assertEqual(set(datos), set(SECCIONES))
        for nombre, bloques in CONTENIDOS.items():
            with self.subTest(seccion=nombre):
                cientifico = nombre not in ('informes', 'ayuda')
                esperados = 8 if cientifico else 5
                self.assertEqual(len(bloques['fundamentos']), esperados)
                self.assertEqual(datos[nombre]['fundamentos'].count('edu-deep-block'), esperados)
                texto = unescape(re.sub(r'<[^>]*>', ' ',
                                       ' '.join(t for _, t in bloques['fundamentos'])))
                palabras = len(re.findall(r'\w+', texto))
                self.assertGreaterEqual(palabras, 400 if cientifico else 200)
                self.assertLessEqual(len(re.findall(r'\w+', re.sub(r'<[^>]*>', ' ', bloques['uso']))), 120)
                self.assertGreaterEqual(datos[nombre]['fundamentos'].count('<p'),
                                        6 if cientifico else 4)
        self.assertIn('h₂−h₁', CONTENIDOS['resultados']['fundamentos'][2][1])
        self.assertIn('Gouy–Stodola', CONTENIDOS['segunda_ley']['fundamentos'][4][1])
        self.assertIn('supremo', CONTENIDOS['optimizacion']['fundamentos'][5][1])

    def test_teoria_ampliada_aparece_en_html_sin_cargar_uso(self):
        html = self.client.get('/').get_data(as_text=True)
        for texto in ('Qué es un ciclo Brayton', 'Balances de las turbomáquinas',
                      'Gouy–Stodola', 'sensibilidad normalizada', 'malla bidimensional',
                      'estado muerto', 'validación'):
            self.assertIn(texto.lower(), html.lower())
        self.assertGreaterEqual(html.count('class="edu-equation"'), 6)
        self.assertEqual(html.count('class="edu-deep-grid"'), 8)

    def test_siete_ayudas_y_seis_mapa_sin_repetir_modelos(self):
        html = self.client.get('/').get_data(as_text=True)
        self.assertEqual(len(AYUDAS_CP), 7)
        self.assertEqual(len(AYUDAS_MAPA), 6)
        for campo in AYUDAS_CP:
            self.assertIn(f'aria-describedby="{campo}-ayuda"', html)
            self.assertIn(f'id="{campo}-ayuda"', html)
        for campo in AYUDAS_MAPA:
            self.assertIn(f'id="mapa_cp_{campo}-ayuda"', html)
        self.assertNotIn('name="gamma"', html)
        self.assertNotIn('/modelo-cp-variable', html)

    def test_resultados_y_conclusion_coinciden_con_solucionador(self):
        calculo = resolver_ciclo(288.15, 1600, 10, 100, .85, .9, .05)
        html = self._post('normal')
        self.assertIn(f'{calculo["trabajo_neto"]:.3f}', html)
        self.assertIn(f'{100 * calculo["rendimiento"]:.2f}', html)
        self.assertIn('Qué hemos aprendido de este caso', html)
        self.assertIn('data-plot-viewer="cp-resultados"', html)
        self.assertIn('Esquemático:', html)

    def test_optimizacion_con_maximos_o_supremos_y_svg_ampliable(self):
        html = self._post('optimizar')
        self.assertIn('data-plot-viewer="cp-optimizacion"', html)
        self.assertIn('Qué hemos aprendido', html)
        self.assertIn('Máximo interior alcanzado', html)
        self.assertIn('class="cp-figure"', html)

    def test_sensibilidad_tres_curvas_con_contexto_fisico(self):
        html = self._post('sensibilidad', sens_cp_parametro='T3',
                          sens_cp_minimo='1350', sens_cp_maximo='1750',
                          sens_cp_muestras='5')
        self.assertIn('data-plot-viewer="cp-sensibilidad"', html)
        self.assertIn('Línea vertical discontinua', html)
        self.assertIn('De 5 evaluaciones', html)
        self.assertGreaterEqual(html.count('class="cp-figure"'), 3)

    def test_mapa_cinco_graficas_y_malla_interpretada(self):
        html = self._post('mapa', mapa_cp_rp_min='1.1', mapa_cp_rp_max='45',
                          mapa_cp_T3_min='1300', mapa_cp_T3_max='1700',
                          mapa_cp_n_rp='5', mapa_cp_n_T3='5')
        self.assertIn('data-plot-viewer="cp-mapa"', html)
        self.assertIn('25 celdas', html)
        self.assertEqual(html.count('class="cp-figure"'), 5)
        for titulo in ('Mapa A · Trabajo neto', 'Mapa B · Rendimiento térmico',
                       'Mapa de viabilidad', 'Cortes · Trabajo neto',
                       'Cortes · Rendimiento'):
            self.assertIn(titulo, html)
        self.assertIn('Mejores puntos muestreados', html)

    def test_exergia_muestra_alcance_parcial_y_svg(self):
        html = self._post('segunda_ley', T0='288.15', p0='100')
        self.assertIn('data-plot-viewer="cp-segunda-ley"', html)
        self.assertIn('Qué hemos aprendido e interpretación', html)
        self.assertIn('exclusivamente a las dos turbomáquinas', html)

    def test_informes_historicos_no_se_confunden_con_cp(self):
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('data-edu-tabs="informes"', html)
        self.assertIn('Historial de gas perfecto', html)
        self.assertIn('no son resultados cp(T)', html)
        self.assertIn('todavía no genera nuevos informes HTML', html)

    def test_visor_svg_y_imagen_sin_perder_teclado(self):
        script = (ROOT / 'static/dashboard.js').read_text(encoding='utf-8')
        html = self.client.get('/').get_data(as_text=True)
        for expresion in ('img, svg', 'cloneNode(true)', 'showModal()',
                          "opener?.focus()", "dialog.close()", "ArrowRight"):
            self.assertIn(expresion, script)
        self.assertIn('class="chart-vector" hidden', html)
        self.assertIn('aria-label="Cerrar gráfica ampliada"', html)
        self.assertIn('class="chart-dialog"', html)

    def test_galeria_responsive_y_svg_cabida_en_tarjeta(self):
        css = (ROOT / 'static/style.css').read_text(encoding='utf-8')
        self.assertRegex(css, r'\.cp-gallery \.plot-grid\s*\{grid-template-columns:repeat\(2,')
        self.assertRegex(css, r'@media\(max-width:760px\)[\s\S]*\.cp-gallery \.plot-grid\{grid-template-columns:minmax\(0,1fr\)\}')
        self.assertIn('.chart-dialog .chart-vector svg', css)
        self.assertIn('.cp-figure .cp-plot svg', css)
        self.assertIn('.edu-deep-grid{display:grid;grid-template-columns:minmax(0,1fr)', css)
        self.assertIn('.edu-deep-block .edu-equation', css)

    def test_una_sola_plantilla_principal(self):
        self.assertEqual([p.name for p in (ROOT / 'templates').glob('*.html')], ['index.html'])
        self.assertIn('class="cp-gallery"', (ROOT / 'templates/index.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
