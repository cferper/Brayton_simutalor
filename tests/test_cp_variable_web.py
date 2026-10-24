"""Verificación Flask de la interfaz unificada en /, sin rutas cp(T) separadas."""
import unittest
from unittest.mock import patch

from web_app import app
from ciclo_cp_variable import resolver_ciclo
from optimizacion_cp_variable import estudiar_cp_variable

BASE = {'T1':'288.15','T3':'1600','rp':'10','p1':'100',
        'eta_c':'0.85','eta_t':'0.90','delta':'0.05','accion':'normal'}


class IntegracionWebCPVariable(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_dashboard_original_con_siete_entradas(self):
        respuesta = self.client.get('/')
        texto = respuesta.get_data(as_text=True)
        self.assertEqual(respuesta.status_code, 200)
        for seccion in ('simulacion','resultados','optimizacion','sensibilidad',
                        'mapa','segunda_ley','informes','ayuda'):
            self.assertIn(f'href="#{seccion}"', texto)
        self.assertEqual(texto.count('type="number"'), 10)  # siete físicas + tres OFAT
        self.assertEqual(texto.count('name="sens_cp_parametro"'), 1)
        self.assertNotIn('name="cp"', texto)
        self.assertNotIn('name="gamma"', texto)
        self.assertNotIn('/modelo-cp-variable', texto)

    def test_caso_base_coincide_con_solucionador_2b(self):
        p = resolver_ciclo(288.15,1600,10,100,.85,.9,.05)
        respuesta = self.client.post('/', data=BASE)
        self.assertEqual(respuesta.status_code, 200)
        texto = respuesta.get_data(as_text=True)
        self.assertIn(f'{p["trabajo_neto"]:.3f}', texto)
        self.assertIn(f'{100*p["rendimiento"]:.3f}', texto)
        self.assertIn(f'{p["T2s"]:.3f}', texto)
        self.assertIn('cp [J/(kg·K)]', texto)
        self.assertIn('Esquemático', texto)

    def test_optimos_de_2c_sin_duplicar(self):
        estudio = estudiar_cp_variable(288.15,1600,100,.85,.9,.05)
        texto = self.client.post('/', data={**BASE,'accion':'optimizar'}).get_data(as_text=True)
        for clave in ('A','B'):
            self.assertIn(f'{estudio[clave]["rp"]:.6f}', texto)
        self.assertIn('Fronteras excluidas', texto)
        self.assertEqual(texto.count('Máximo interior alcanzado'), 2)

    def test_supremo_reversible_no_se_anuncia_como_maximo_alcanzado(self):
        respuesta = self.client.post('/', data={**BASE, 'eta_c':'1',
                                                'eta_t':'1', 'delta':'0',
                                                'accion':'optimizar'})
        self.assertEqual(respuesta.status_code, 200)
        texto = respuesta.get_data(as_text=True)
        self.assertIn('Supremo en frontera abierta', texto)
        self.assertIn('No es un punto operativo', texto)

    def test_errores_de_entrada_y_fuera_de_rango(self):
        for valores in ({'rp':'nan'},{'T3':'inf'},{'eta_c':'0'},{'T1':'1900','rp':'5'}):
            with self.subTest(valores=valores):
                respuesta = self.client.post('/', data={**BASE,**valores})
                self.assertEqual(respuesta.status_code, 400)
                self.assertNotIn('Traceback', respuesta.get_data(as_text=True))
                self.assertNotIn('data-kpi=', respuesta.get_data(as_text=True))

    def test_no_motor_no_atribuye_rendimiento(self):
        respuesta = self.client.post('/',data={**BASE,'rp':'1','delta':'0'})
        self.assertEqual(respuesta.status_code,200)
        self.assertIn('Ciclo calculable, no motor', respuesta.get_data(as_text=True))
        self.assertIn('No aplicable', respuesta.get_data(as_text=True))

    def test_ausencia_de_dominio_motor(self):
        respuesta = self.client.post('/',data={**BASE,'T3':'288.15','rp':'1','delta':'0'})
        self.assertEqual(respuesta.status_code,200)
        self.assertIn('No existe dominio motor',respuesta.get_data(as_text=True))

    def test_operaciones_pendientes_no_se_ejecutan(self):
        with patch('web_app.preparar_resultados') as ejecutar:
            for accion in ('mapa','segunda_ley','desconocida'):
                with self.subTest(accion=accion):
                    respuesta = self.client.post('/',data={**BASE,'accion':accion})
                    self.assertEqual(respuesta.status_code,400)
                    self.assertIn('aún no está adaptado',respuesta.get_data(as_text=True))
            ejecutar.assert_not_called()
        respuesta = self.client.get('/').get_data(as_text=True)
        for titulo in ('Sensibilidad','Mapa de diseño','Segunda ley'):
            self.assertIn(titulo,respuesta)
        self.assertEqual(respuesta.count('Funcionalidad desactivada temporalmente'),2)

    def test_ruta_y_plantilla_antiguas_no_son_accesibles(self):
        self.assertEqual(self.client.get('/modelo-cp-variable').status_code,404)
        self.assertEqual(self.client.post('/modelo-cp-variable',data=BASE).status_code,404)
        with self.client.get('/static/dashboard.js') as recurso:
            self.assertEqual(recurso.status_code,200)

    def test_no_genera_informes_ni_calcula_al_navegar(self):
        with patch('web_app.preparar_resultados') as preparar:
            self.assertEqual(self.client.get('/').status_code,200)
            preparar.assert_not_called()

if __name__=='__main__':
    unittest.main()
