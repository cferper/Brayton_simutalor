"""Verificación científica acotada del mapa rp–T3 de aire cp(T)."""

from math import isclose
import unittest
from unittest.mock import patch

from ciclo_cp_variable import ErrorNumericoCiclo, resolver_ciclo
from cp_variable_web import DEFAULTS
from mapa_diseno_cp_variable import calcular_mapa_cp_variable
from optimizacion_cp_variable import estudiar_cp_variable


class MapaDisenoVariableCP(unittest.TestCase):
    def test_malla_y_orientacion_de_los_ejes(self):
        m=calcular_mapa_cp_variable(DEFAULTS,2,32,1200,1800,5,7)
        self.assertEqual(len(m['filas']),7)
        self.assertTrue(all(len(f)==5 for f in m['filas']))
        self.assertEqual(m['rps'][0],2)
        self.assertEqual(m['rps'][-1],32)
        self.assertAlmostEqual(m['rps'][1]/m['rps'][0],m['rps'][2]/m['rps'][1],places=12)
        self.assertEqual(m['T3s'],[1200,1300,1400,1500,1600,1700,1800])
        for j,row in enumerate(m['filas']):
            for i,c in enumerate(row):
                self.assertEqual((c['rp'],c['T3']),(m['rps'][i],m['T3s'][j]))
        self.assertEqual(sum(m['conteos'].values()),35)

    def test_coincidencia_con_fase_2b_para_celdas(self):
        m=calcular_mapa_cp_variable(DEFAULTS,10,20,1500,1700,5,5)
        for j,i in ((0,0),(2,0),(2,2),(4,4)):
            with self.subTest(j=j,i=i):
                c=m['filas'][j][i]
                p=resolver_ciclo(**{**DEFAULTS,'rp':c['rp'],'T3':c['T3']})
                self.assertEqual(c['estado'],'motor' if p['viable'] else 'no_motor')
                for clave in ('trabajo_compresor','trabajo_turbina','trabajo_neto',
                              'calor_aportado','calor_rechazado','rendimiento'):
                    self.assertAlmostEqual(c['datos'][clave],p[clave],places=9)
                self.assertEqual(c['datos']['temperaturas'],p['temperaturas'])
                self.assertAlmostEqual(c['datos']['residuo_primera_ley'],0,delta=1e-8)

    def test_caso_base_y_entradas_no_mutadas(self):
        valores=DEFAULTS.copy()
        m=calcular_mapa_cp_variable(valores,10,20,1500,1700,5,5)
        base=m['filas'][2][0]
        self.assertEqual((base['rp'],base['T3']),(10,1600))
        self.assertEqual(base['estado'],'motor')
        self.assertAlmostEqual(base['operativas']['trabajo_neto'],402.071,places=3)
        self.assertAlmostEqual(100*base['operativas']['rendimiento'],34.893,places=3)
        self.assertEqual(valores,DEFAULTS)
        self.assertEqual(m['fijos'],{k:DEFAULTS[k] for k in ('T1','p1','eta_c','eta_t','delta')})

    def test_no_motor_y_mask_sin_ceros_artificiales(self):
        m=calcular_mapa_cp_variable(DEFAULTS,.5,2.0,1200,1800,7,5)
        no_motor=[c for row in m['filas'] for c in row if c['estado']=='no_motor']
        self.assertTrue(no_motor)
        for c in no_motor:
            self.assertIsNone(c['operativas'])
            self.assertTrue(c['motivo'])
            self.assertIsNotNone(c['datos'])
        motor=[c for row in m['filas'] for c in row if c['estado']=='motor']
        self.assertTrue(motor)
        self.assertTrue(all(c['operativas']['rendimiento'] is not None for c in motor))

    def test_estados_termicos_fuera_de_correlacion_y_entradas_invalidas(self):
        m=calcular_mapa_cp_variable({**DEFAULTS,'T1':1900},2,20,1500,1950,5,5)
        self.assertGreater(m['conteos'].get('fuera_rango',0),0)
        m=calcular_mapa_cp_variable(DEFAULTS,2,8,1900,2300,5,5)
        self.assertGreater(m['conteos'].get('entrada_invalida',0),0)
        for c in (c for f in m['filas'] for c in f if c['estado']=='entrada_invalida'):
            self.assertIsNone(c['datos'])
            self.assertIsNone(c['operativas'])

    def test_error_numerico_no_hace_punto_motor(self):
        with patch('mapa_diseno_cp_variable.resolver_ciclo',side_effect=ErrorNumericoCiclo('sin convergencia')):
            m=calcular_mapa_cp_variable(DEFAULTS,1.1,10,1200,1600,5,5)
        self.assertEqual(m['conteos'],{'error_numerico':25})
        self.assertIsNone(m['mejores_malla']['trabajo_neto'])

    def test_dominio_sin_ningun_motor(self):
        m=calcular_mapa_cp_variable(DEFAULTS,1.1,20,210,215,5,5)
        self.assertEqual(m['conteos'].get('motor',0),0)
        self.assertIsNone(m['mejores_malla']['trabajo_neto'])
        self.assertIsNone(m['mejores_malla']['rendimiento'])

    def test_mejores_solo_motores_y_no_optimos_exactos(self):
        m=calcular_mapa_cp_variable(DEFAULTS,8,30,1450,1650,7,5)
        for clave in ('trabajo_neto','rendimiento'):
            p=m['mejores_malla'][clave]
            self.assertEqual(p['estado'],'motor')
            self.assertGreaterEqual(p['operativas'][clave],
                                    max(c['operativas'][clave] for f in m['filas'] for c in f
                                        if c['operativas'] is not None))
        ref=estudiar_cp_variable(DEFAULTS['T1'],1600,DEFAULTS['p1'],
                                 DEFAULTS['eta_c'],DEFAULTS['eta_t'],DEFAULTS['delta'])
        rp_muestras=m['rps']
        self.assertFalse(any(isclose(x,ref['A']['rp'],rel_tol=1e-9) for x in rp_muestras))
        self.assertNotEqual(m['mejores_malla']['trabajo_neto']['T3'],1600)

    def test_rechaza_dominio_y_resolucion_incorrectos(self):
        variantes=((0,80,1200,1800,5,5),(2,2,1200,1800,5,5),
                   (2,1001,1200,1800,5,5),(2,8,1700,1600,5,5),
                   (2,8,1200,3001,5,5),(2,8,1200,1800,4,5),
                   (2,8,1200,1800,51,52),(2,8,1200,1800,5.5,5),
                   (2,8,float('nan'),1800,5,5))
        for argumentos in variantes:
            with self.subTest(argumentos=argumentos),self.assertRaises(ValueError):
                calcular_mapa_cp_variable(DEFAULTS,*argumentos)

    def test_fijos_invalidos_rechazados_por_solver(self):
        with self.assertRaises(ValueError):
            calcular_mapa_cp_variable({**DEFAULTS,'eta_t':0},1.1,20,1200,1800,5,5)


if __name__=='__main__':
    unittest.main()
