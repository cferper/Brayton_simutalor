"""Milestone 48.1: rutas y equivalencia del POST tradicional con la API.

No prueba interacción automática JS; ésta pertenece al milestone 48.2.
"""

import unittest

from web_app import app
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor
from acoplamiento_motor_mapa_47 import punto_diseno_47
from cp_variable_web import DEFAULTS


class NavegacionApi48(unittest.TestCase):
    def setUp(self):
        self.cliente = app.test_client()

    def api(self, datos, *, json=False):
        return (self.cliente.post('/api/turborreactor/simular', json=datos)
                if json else self.cliente.post('/api/turborreactor/simular', data=datos))

    def test_portada_redirige_al_turborreactor(self):
        r = self.cliente.get('/', follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.headers['Location'].endswith('/turborreactor/interactivo'))
        self.assertEqual(self.cliente.get('/turborreactor').status_code, 200)

    def test_brayton_independiente_y_formulario_post(self):
        r = self.cliente.get('/brayton')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Ciclo Brayton', r.get_data(as_text=True))
        entrada = {**DEFAULTS, 'accion':'normal'}
        self.assertEqual(self.cliente.post('/brayton', data=entrada).status_code, 200)
        self.assertEqual(self.cliente.post('/brayton', data={**entrada,'T3':''}).status_code, 400)

    def test_api_a_equivalencia_y_pagina_jinja(self):
        datos = dict(DEFAULTS_TURBO, gasto_masico_aire='20')
        antiguo = simular_turborreactor(datos)
        r = self.api(datos, json=True)
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertTrue(j['ok'])
        self.assertEqual(j['modo'], 'impuesto')
        self.assertAlmostEqual(j['magnitudes']['empuje_especifico_neto'],
                               antiguo['prestaciones']['empuje_especifico_neto'])
        self.assertAlmostEqual(j['magnitudes']['empuje_absoluto_N'],
                               antiguo['prestaciones_absolutas']['empuje_neto'])
        self.assertEqual(len(j['estaciones']) > 5, True)
        self.assertIn('<svg',j['svg']['svg_empuje'])
        self.assertIn('id="resultados"',j['html_documento'])
        self.assertIn('id="estaciones"',j['html_documento'])
        self.assertIn('id="graficas"',j['html_documento'])
        self.assertEqual(self.cliente.post('/turborreactor', data=datos).status_code, 200)

    def test_api_b_geometria_fija_equivalencia(self):
        base = simular_turborreactor(dict(DEFAULTS_TURBO,gasto_masico_aire='20'))
        ag=base['dimensionamiento_tobera']['area_garganta']
        datos = dict(DEFAULTS_TURBO, modo_caudal='fijo', area_garganta_fija=str(ag))
        antiguo = simular_turborreactor(datos)
        r=self.api(datos)
        self.assertEqual(r.status_code,200)
        self.assertAlmostEqual(r.get_json()['magnitudes']['gasto_masico_aire_kg_s'],
                               antiguo['prestaciones_absolutas']['gasto_masico_aire'],places=7)
        self.assertAlmostEqual(r.get_json()['magnitudes']['gasto_masico_gases_kg_s'],
                               antiguo['prestaciones_absolutas']['gasto_masico_gases'],places=7)

    def test_api_c_diseno_y_vuelo(self):
        datos=dict(DEFAULTS_TURBO, modo_caudal='acoplado')
        r=self.api(datos)
        self.assertEqual(r.status_code,200)
        j=r.get_json()
        self.assertAlmostEqual(j['magnitudes']['rpm_eje'],20000)
        self.assertAlmostEqual(j['magnitudes']['gasto_masico_aire_kg_s'],20)
        self.assertAlmostEqual(j['magnitudes']['empuje_absoluto_N'],
                               simular_turborreactor(datos)['prestaciones_absolutas']['empuje_neto'])
        r_vuelo=self.api({**datos,'mach':'0.4'})
        self.assertEqual(r_vuelo.status_code,200)
        self.assertNotAlmostEqual(r_vuelo.get_json()['magnitudes']['rpm_eje'],20000)

    def test_api_no_inventa_salida_fuera_de_mapa(self):
        area=punto_diseno_47()['area_garganta_diseno']*1.1
        datos=dict(DEFAULTS_TURBO,modo_caudal='acoplado',area_garganta_fija=str(area))
        r=self.api(datos)
        self.assertEqual(r.status_code,422)
        self.assertFalse(r.get_json()['ok'])
        self.assertNotIn('magnitudes',r.get_json())

    def test_api_rechaza_imposicion_incompatible_y_valores_invalidos(self):
        datos=dict(DEFAULTS_TURBO,modo_caudal='acoplado',gasto_masico_aire='21')
        self.assertEqual(self.api(datos).status_code,422)
        self.assertEqual(self.api({**DEFAULTS_TURBO,'T3':'invalido'}).status_code,422)
        self.assertEqual(self.api({**DEFAULTS_TURBO,'gasto_masico_aire':'nan'}).status_code,422)

    def test_api_formato_y_estudios_independientes(self):
        self.assertEqual(self.api(['lista'],json=True).status_code,400)
        self.assertEqual(self.api({'campo_extra':'x'},json=True).status_code,400)
        self.assertEqual(self.api({'accion':'sensibilidad'},json=True).status_code,400)
        self.assertEqual(self.cliente.post('/api/turborreactor/simular', data='texto',
                         content_type='text/plain').status_code,415)


if __name__ == '__main__':
    unittest.main()
