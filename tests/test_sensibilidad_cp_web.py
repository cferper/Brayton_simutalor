"""Contratos Flask y SVG de Sensibilidad cp(T) dentro del único index.html."""
import unittest
from unittest.mock import patch

from web_app import app
from cp_variable_web import DEFAULTS

BASE={key:str(value) for key,value in DEFAULTS.items()}
FORM={**BASE,'accion':'sensibilidad','sens_cp_parametro':'T3',
      'sens_cp_minimo':'1200','sens_cp_maximo':'1750','sens_cp_muestras':'21'}


class IntegracionSensibilidadCP(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()

    def test_aparece_en_index_misma_navegacion_y_no_ejecuta_get(self):
        with patch('web_app.preparar_sensibilidad') as preparar:
            response=self.client.get('/')
            self.assertEqual(response.status_code,200)
            preparar.assert_not_called()
        texto=response.get_data(as_text=True)
        self.assertIn('id="sensibilidad"',texto)
        self.assertIn('name="sens_cp_parametro"',texto)
        self.assertNotIn('/modelo-cp-variable',texto)
        self.assertNotIn('name="cp"',texto)
        self.assertNotIn('Funcionalidad desactivada temporalmente',texto)

    def test_post_muestra_graficas_locales_y_estados(self):
        response=self.client.post('/',data=FORM)
        self.assertEqual(response.status_code,200)
        texto=response.get_data(as_text=True)
        self.assertIn('data-initial-section="sensibilidad"',texto)
        self.assertIn('S = (x/Y)',texto)
        self.assertIn('Trabajo neto [kJ/kg]',texto)
        self.assertIn('Rendimiento térmico [%]',texto)
        self.assertIn('Línea vertical discontinua',texto)
        self.assertGreaterEqual(texto.count('<svg'),3)
        self.assertIn('Paso estable',texto)

    def test_post_reutiliza_resolver_y_no_optimizador(self):
        with patch('web_app.preparar_resultados') as normal:
            r=self.client.post('/',data=FORM)
            self.assertEqual(r.status_code,200)
            normal.assert_not_called()

    def test_rango_fuera_estado_no_contamina_graficas(self):
        r=self.client.post('/',data={**FORM,'sens_cp_parametro':'T1',
                                     'sens_cp_minimo':'300','sens_cp_maximo':'1900'})
        self.assertEqual(r.status_code,200)
        t=r.get_data(as_text=True)
        self.assertIn('Fuera de 200–2000 K:',t)
        self.assertIn('Fuera de rango',t)

    def test_punto_no_motor_no_publica_rendimiento(self):
        r=self.client.post('/',data={**FORM,'sens_cp_parametro':'rp',
                                     'sens_cp_minimo':'0.5','sens_cp_maximo':'2'})
        self.assertEqual(r.status_code,200)
        t=r.get_data(as_text=True)
        self.assertIn('No motor',t)
        self.assertIn('huecos = no motor',t)

    def test_error_muestra_sensibilidad_sin_traceback_ni_graficas(self):
        for changes in ({'sens_cp_minimo':'20','sens_cp_maximo':'2'},
                        {'sens_cp_muestras':'202'},
                        {'sens_cp_muestras':'4.5'},
                        {'sens_cp_parametro':'__dict__'},
                        {'sens_cp_minimo':'nan'}):
            with self.subTest(changes=changes):
                response=self.client.post('/',data={**FORM,**changes})
                self.assertEqual(response.status_code,400)
                texto=response.get_data(as_text=True)
                self.assertIn('data-initial-section="sensibilidad"',texto)
                self.assertNotIn('Traceback',texto)
                self.assertNotIn('Resumen de puntos evaluados',texto)


if __name__=='__main__':
    unittest.main()
