"""Pruebas Flask.test_client del modelo cp(T); requieren Flask y Jinja2."""
import unittest

from web_app import app
from ciclo_cp_variable import resolver_ciclo
from optimizacion_cp_variable import estudiar_cp_variable

BASE={'T1':'288.15','T3':'1600','rp':'10','p1':'100',
      'eta_c':'0.85','eta_t':'0.90','delta':'0.05'}

class IntegracionWebCPVariable(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()

    def test_get_nueva_seccion_y_navegacion_historica(self):
        r=self.client.get('/modelo-cp-variable')
        self.assertEqual(r.status_code,200)
        self.assertIn(b'Modelo cp(T)',r.data)
        self.assertIn(b'href="/"',r.data)
        self.assertEqual(self.client.get('/').status_code,200)

    def test_caso_base_y_resultados_reales(self):
        p=resolver_ciclo(288.15,1600,10,100,.85,.9,.05)
        r=self.client.post('/modelo-cp-variable',data=BASE)
        self.assertEqual(r.status_code,200)
        texto=r.get_data(as_text=True)
        self.assertIn(f'{p["trabajo_neto"]:.3f}',texto)
        self.assertIn(f'{100*p["rendimiento"]:.3f}',texto)
        self.assertIn(f'{p["T2s"]:.3f}',texto)
        self.assertIn('kJ/kg',texto)
        self.assertIn('Esquemático',texto)

    def test_optimización_de_ambos_objetivos(self):
        e=estudiar_cp_variable(288.15,1600,100,.85,.9,.05)
        texto=self.client.post('/modelo-cp-variable',data=BASE).get_data(as_text=True)
        for key in ('A','B'):
            self.assertIn(f'{e[key]["rp"]:.6f}',texto)
        self.assertIn('fronteras excluidas',texto)

    def test_errores_numericos_y_de_entradas_sin_traceback(self):
        for cambio in ({'rp':'nan'},{'T3':'inf'},{'eta_c':'0'},{'T1':'1900','rp':'5'}):
            with self.subTest(cambio=cambio):
                r=self.client.post('/modelo-cp-variable',data={**BASE,**cambio})
                self.assertEqual(r.status_code,400)
                self.assertNotIn(b'Traceback',r.data)
                self.assertNotIn(b'Trabajo neto</',r.data)

    def test_no_motor_sin_rendimiento_ficticio(self):
        r=self.client.post('/modelo-cp-variable',data={**BASE,'rp':'1','delta':'0'})
        self.assertEqual(r.status_code,200)
        self.assertIn(b'no motor',r.data)
        self.assertIn(b'No aplicable',r.data)

    def test_sin_dominio_no_optimiza(self):
        r=self.client.post('/modelo-cp-variable',data={**BASE,'T3':'288.15','rp':'1','delta':'0'})
        self.assertEqual(r.status_code,200)
        self.assertIn(b'No existe dominio motor',r.data)

if __name__=='__main__': unittest.main()
