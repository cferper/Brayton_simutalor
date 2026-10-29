"""Milestone 49.1: navegación por tres vistas con una sola física/API."""

import unittest

from web_app import app
from turborreactor_web import DEFAULTS_TURBO


class SeparacionInterfaz49(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_portada_y_tres_destinos(self):
        respuesta = self.client.get('/')
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta.headers['Location'].endswith('/turborreactor/interactivo'))
        for ruta, titulo in (('/turborreactor/interactivo', 'Banco de ensayos interactivo'),
                             ('/turborreactor', 'Turborreactor clásico'),
                             ('/brayton', 'Brayton Simulator')):
            with self.subTest(ruta=ruta):
                html = self.client.get(ruta).get_data(as_text=True)
                self.assertIn(titulo, html)
                self.assertIn('/turborreactor/interactivo', html)
                self.assertIn('/turborreactor', html)
                self.assertIn('/brayton', html)

    def test_banco_conserva_controles_y_modo_real(self):
        html = self.client.get('/turborreactor/interactivo').get_data(as_text=True)
        for fragmento in ('id="turbo-live"', 'id="mach_deslizador"',
                          'id="T3_deslizador"', 'name="modo_caudal"',
                          'value="impuesto"', 'value="fijo"', 'value="acoplado"',
                          'data-simulacion-inicial="pendiente"',
                          'turborreactor_interactivo.js'):
            self.assertIn(fragmento, html)
        self.assertIn('data-interfaz="interactivo"', html)
        self.assertIn('action="/turborreactor/interactivo"', html)

    def test_clasico_conserva_secciones_y_post(self):
        html = self.client.get('/turborreactor').get_data(as_text=True)
        for seccion in ('resultados', 'estaciones', 'graficas', 'sensibilidad', 'mapa'):
            self.assertIn('id="'+seccion+'"', html)
        self.assertIn('data-interfaz="clasico"', html)
        self.assertIn('action="/turborreactor"', html)
        self.assertEqual(self.client.post('/turborreactor', data=dict(DEFAULTS_TURBO,
                               gasto_masico_aire='20')).status_code, 200)

    def test_api_compartida_modos(self):
        caso_impuesto = dict(DEFAULTS_TURBO, gasto_masico_aire='20')
        base = self.client.post('/api/turborreactor/simular', data=caso_impuesto)
        self.assertEqual(base.status_code, 200)
        caudal = base.get_json()['magnitudes']['gasto_masico_aire_kg_s']
        self.assertIsNotNone(base.get_json()['magnitudes']['empuje_especifico_neto'])
        for modo in ('impuesto', 'fijo', 'acoplado'):
            datos = dict(DEFAULTS_TURBO, modo_caudal=modo)
            if modo == 'impuesto':
                datos['gasto_masico_aire'] = '20'
            if modo == 'fijo':
                from turborreactor_web import simular_turborreactor
                dimension = simular_turborreactor(caso_impuesto)['dimensionamiento_tobera']
                # La garganta prescribe el caudal, no un valor artificial de aire.
                datos['area_garganta_fija'] = str(dimension['area_garganta'])
            with self.subTest(modo=modo):
                respuesta = self.client.post('/api/turborreactor/simular', data=datos)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.get_json()['modo'], modo)
        self.assertIsNotNone(caudal)


if __name__ == '__main__':
    unittest.main()
