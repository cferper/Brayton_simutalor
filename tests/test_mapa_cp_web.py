"""Integración Flask de los dos mapas en index.html sin nuevas rutas."""

import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from cp_variable_web import DEFAULTS, preparar_mapa, svg_mapa_cp_variable
from web_app import app

BASE={k:str(v) for k,v in DEFAULTS.items()}
FORM={**BASE,'accion':'mapa','mapa_cp_rp_min':'1.1',
      'mapa_cp_rp_max':'80','mapa_cp_T3_min':'1200',
      'mapa_cp_T3_max':'1800','mapa_cp_n_rp':'9','mapa_cp_n_T3':'9'}


class IntegracionMapaVariableCP(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()

    def test_dashboard_get_sin_calcular(self):
        with patch('web_app.preparar_mapa') as preparar:
            r=self.client.get('/')
            preparar.assert_not_called()
        self.assertEqual(r.status_code,200)
        t=r.get_data(as_text=True)
        self.assertIn('id="mapa"',t)
        self.assertIn('name="mapa_cp_n_T3"',t)
        self.assertEqual(t.count('type="number"'),18)
        self.assertNotIn('Funcionalidad desactivada temporalmente',t)
        self.assertNotIn('/modelo-cp-variable',t)

    def test_dos_mapas_unidades_mascaras_y_tooltips(self):
        r=self.client.post('/',data=FORM)
        self.assertEqual(r.status_code,200)
        t=r.get_data(as_text=True)
        self.assertIn('data-initial-section="mapa"',t)
        for texto in ('Mapa A · Trabajo neto [kJ/kg]','Mapa B · Rendimiento térmico [%]',
                      'rp [−] (escala logarítmica)','T3 [K]','Mejores puntos muestreados',
                      'Fuera de rango','Pasa el cursor'):
            self.assertIn(texto,t)
        self.assertGreaterEqual(t.count('<svg'),3)
        self.assertIn('Cada celda: una evaluación cp(T)',t)
        self.assertIn('óptimo continuo 2C',t)

    def test_mapa_no_llama_simulacion_normal_ni_sensibilidad(self):
        with patch('web_app.preparar_resultados') as normal,patch('web_app.preparar_sensibilidad') as ofat:
            self.assertEqual(self.client.post('/',data=FORM).status_code,200)
            normal.assert_not_called()
            ofat.assert_not_called()

    def test_sin_motor_no_dibuja_colores_ficticios(self):
        r=self.client.post('/',data={**FORM,'mapa_cp_T3_min':'210',
                                     'mapa_cp_T3_max':'215','mapa_cp_n_rp':'5','mapa_cp_n_T3':'5'})
        self.assertEqual(r.status_code,200)
        t=r.get_data(as_text=True)
        self.assertIn('No hay puntos motores en el dominio solicitado',t)
        self.assertNotIn('Mapa A · Trabajo neto [kJ/kg]',t)
        self.assertNotIn('Mapa B · Rendimiento térmico [%]',t)

    def test_errores_400_retorna_a_mapa_y_conserva_formulario(self):
        variantes=({'mapa_cp_rp_min':'80','mapa_cp_rp_max':'1'},
                   {'mapa_cp_n_rp':'52'},{'mapa_cp_n_T3':'4.5'},
                   {'mapa_cp_T3_min':'nan'},{'mapa_cp_T3_max':'3001'})
        for change in variantes:
            with self.subTest(change=change):
                r=self.client.post('/',data={**FORM,**change})
                self.assertEqual(r.status_code,400)
                t=r.get_data(as_text=True)
                self.assertIn('data-initial-section="mapa"',t)
                self.assertNotIn('Traceback',t)
                self.assertNotIn('Resumen de la malla',t)

    def test_muestras_y_referencia_no_se_confunden(self):
        estudio=preparar_mapa(DEFAULTS,10,20,1500,1700,5,5)
        self.assertIsNotNone(estudio['mejores_malla']['trabajo_neto'])
        self.assertAlmostEqual(estudio['optimos_referencia']['A']['rp'],15.877934,places=5)
        self.assertAlmostEqual(estudio['optimos_referencia']['B']['rp'],46.819105,places=5)
        # B queda fuera de la ventana: no se marca como una celda inventada.
        svg=svg_mapa_cp_variable(estudio,'trabajo_neto',estudio['optimos_referencia'])
        self.assertIn('A: óptimo continuo 2C',svg)
        self.assertNotIn('B: óptimo continuo 2C',svg)
        elemento=ElementTree.fromstring(svg)
        self.assertTrue(elemento.tag.endswith('svg'))
        self.assertGreaterEqual(len(elemento.findall('rect')),25)


if __name__=='__main__':
    unittest.main()
