"""Integración M43: organización pedagógica y continuidad de formularios."""

from collections import Counter
from html.parser import HTMLParser
import unittest

from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor
from web_app import app


APARTADOS = ('configuracion', 'resultados', 'estaciones', 'graficas',
             'sensibilidad', 'mapa')


class _Estructura(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.tabs = []
        self.forms = []
        self.controls = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if a.get('role') == 'tab':
            self.tabs.append(a)
        if tag == 'form':
            self.forms.append(a)
        if tag in ('button', 'input', 'select'):
            self.controls.append((tag, a))


class InterfazEducativa43(unittest.TestCase):
    def setUp(self):
        self.valores = dict(DEFAULTS_TURBO)

    def _html(self, data=None):
        with app.test_client() as cliente:
            respuesta = (cliente.get('/turborreactor') if data is None else
                         cliente.post('/turborreactor', data=data))
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.get_data(as_text=True)

    def test_seis_apartados_con_dos_vistas_y_sin_ids_repetidos(self):
        html = self._html()
        analizador = _Estructura()
        analizador.feed(html)
        self.assertEqual([nombre for nombre, n in Counter(analizador.ids).items()
                          if n != 1], [])
        # Las 12 pestañas educativas se complementan con las cuatro del visor
        # interactivo (T–s, Mach, presión y geometría) introducidas en 49.3.
        educativas = [t for t in analizador.tabs if 'aria-controls' in t]
        graficas = [t.get('data-plot-tab') for t in analizador.tabs
                    if 'data-plot-tab' in t]
        self.assertEqual(len(educativas), 12)
        self.assertEqual(set(graficas), {'ts', 'mach', 'presion', 'geometria'})
        self.assertEqual(len(analizador.tabs), 16)
        self.assertNotIn('id="fundamentos"', html)
        self.assertNotIn('href="#fundamentos"', html)
        for seccion in APARTADOS:
            self.assertIn('data-edu-tabs="%s"' % seccion, html)
            for vista in ('uso', 'teoria'):
                ident = 'turbo-%s-vista-%s' % (seccion, vista)
                self.assertIn(ident, analizador.ids)
                self.assertTrue(any(t.get('aria-controls') == ident
                                    for t in analizador.tabs))
        self.assertIn('Fundamentos teóricos y procesos', html)
        self.assertIn('Uso y configuración', html)

    def test_boton_unico_y_adaptacion_automatica(self):
        self.valores.update(tipo_tobera='convergente_divergente', epsilon='1.5')
        html = self._html(self.valores)
        self.assertEqual(html.count('>Simular turborreactor →</button>'), 1)
        self.assertNotIn('>Calcular geometría adaptada', html)
        self.assertIn('Calculadora de adaptación geométrica', html)
        self.assertIsNotNone(simular_turborreactor(self.valores)['tobera'])

    def test_formularios_y_diagnostico_choque_siguen_visibles(self):
        self.valores.update(tipo_tobera='convergente_divergente', epsilon='6')
        html = self._html(self.valores)
        self.assertIn('Choque normal interno', html)
        self.assertIn('Entropía generada', html)
        p = _Estructura()
        p.feed(html)
        self.assertEqual(len(p.forms), 3)
        for campo in ('tipo_tobera', 'eta_n', 'epsilon', 'sens_parametro',
                      'mapa_tipo', 'mapa_nx', 'mapa_ny'):
            self.assertTrue(any(a.get('name') == campo for _, a in p.controls),
                            campo)

    def test_estudios_post_siguen_mostrando_datos(self):
        self.valores.update(accion='sensibilidad', sens_parametro='rp',
                            sens_min='9', sens_max='11', sens_n='3')
        self.assertIn('Puntos evaluados y diagnóstico físico',
                      self._html(self.valores))
        self.valores.update(accion='mapa', mapa_tipo='rp_T3',
                            mapa_nx='2', mapa_ny='2', mapa_rp_min='9',
                            mapa_rp_max='11', mapa_T3_min='1500',
                            mapa_T3_max='1600')
        self.assertIn('Tabla completa de configuraciones',
                      self._html(self.valores))

    def test_teoria_cubre_magnitudes_y_limites_sin_resultado(self):
        html = self._html()
        for texto in ('Fbruto', 'TSFC=3600f/Fs', 'h(Tₜ0)', 'ηm',
                      'bloqueo', 'viscos', 'caudal', 'OFAT', 'Pareto',
                      'validación'):
            self.assertIn(texto, html)


if __name__ == '__main__':
    unittest.main()
