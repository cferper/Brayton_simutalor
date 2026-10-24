"""Fase 2E: OFAT cp(T), clasificación física y diferencias finitas."""
import unittest
from unittest.mock import patch

from ciclo_cp_variable import ErrorNumericoCiclo, resolver_ciclo
from cp_variable_web import DEFAULTS
from sensibilidad_cp_variable import barrido_cp_variable, sensibilidad_local


class SensibilidadCPVariable(unittest.TestCase):
    def test_caso_base_fase_2b_y_conservacion_de_entradas(self):
        inicial = DEFAULTS.copy()
        estudio = barrido_cp_variable(inicial, 'rp', 5, 55, 11)
        self.assertEqual(inicial, DEFAULTS)
        referencia = estudio['referencia']['ciclo']
        directo = resolver_ciclo(**DEFAULTS)
        self.assertAlmostEqual(referencia['trabajo_neto'], directo['trabajo_neto'], places=10)
        self.assertAlmostEqual(referencia['trabajo_neto'], 402.071, places=3)
        self.assertAlmostEqual(100*referencia['rendimiento'], 34.893, places=3)

    def test_malla_contiene_extremos_y_compara_con_resolver_2b(self):
        e = barrido_cp_variable(DEFAULTS, 'T3', 1400, 1700, 5)
        self.assertEqual([p['x'] for p in e['filas']], [1400,1475,1550,1625,1700])
        for fila in e['filas']:
            with self.subTest(T3=fila['x']):
                directo = resolver_ciclo(**{**DEFAULTS,'T3':fila['x']})
                self.assertEqual(fila['estado'], 'motor' if directo['viable'] else 'no_motor')
                for key in ('trabajo_compresor','trabajo_turbina','trabajo_neto','calor_aportado'):
                    self.assertAlmostEqual(fila['magnitudes'][key], directo[key], places=10)
                self.assertAlmostEqual(fila['residuo_primera_ley'], 0, delta=1e-7)

    def test_clasifica_no_motor_sin_curvas_operativas(self):
        e = barrido_cp_variable(DEFAULTS, 'rp', .5, 3, 6)
        self.assertIn('no_motor', [f['estado'] for f in e['filas']])
        for f in e['filas']:
            if f['estado'] != 'motor':
                self.assertIsNone(f['operativas'])
                self.assertTrue(f['motivo'])

    def test_estados_fuera_rango_y_no_extrapolacion(self):
        e = barrido_cp_variable(DEFAULTS, 'T1', 300, 1900, 9)
        fuera = [f for f in e['filas'] if f['estado'] == 'fuera_rango']
        self.assertTrue(fuera)
        self.assertTrue(all(f['magnitudes'] is None and f['operativas'] is None for f in fuera))

    def test_entradas_invalidas_en_muestras_y_en_configuracion(self):
        e = barrido_cp_variable(DEFAULTS, 'eta_c', .8, 1.2, 5)
        self.assertGreater(e['conteos'].get('entrada_invalida',0),0)
        with patch('sensibilidad_cp_variable.resolver_ciclo', side_effect=ErrorNumericoCiclo('sin convergencia')):
            fallo = barrido_cp_variable(DEFAULTS,'rp',4,8,3)
        self.assertEqual(fallo['conteos'],{'error_numerico':3})
        self.assertTrue(all(f['operativas'] is None for f in fallo['filas']))
        for argumentos in [('incognito',2,3,5),('rp',2,2,5),('rp',3,2,5),
                           ('rp',2,5,2),('rp',2,5,202),('rp',float('nan'),5,5)]:
            with self.subTest(argumentos=argumentos), self.assertRaises(ValueError):
                barrido_cp_variable(DEFAULTS,*argumentos)

    def test_p1_absoluta_no_cambia_prestaciones_en_este_modelo(self):
        e = barrido_cp_variable(DEFAULTS, 'p1', 80, 120, 9)
        self.assertEqual(e['conteos'], {'motor': 9})
        base = e['filas'][0]['operativas']
        for fila in e['filas'][1:]:
            self.assertAlmostEqual(fila['operativas']['trabajo_neto'],base['trabajo_neto'],places=7)
            self.assertAlmostEqual(fila['operativas']['rendimiento'],base['rendimiento'],places=9)
        self.assertAlmostEqual(e['local']['trabajo_neto']['valor'],0,delta=1e-7)
        self.assertAlmostEqual(e['local']['rendimiento']['valor'],0,delta=1e-7)

    def test_sensibilidad_local_paso_y_definicion(self):
        s1=sensibilidad_local(DEFAULTS,'T3',paso_relativo=.001)
        s2=sensibilidad_local(DEFAULTS,'T3',paso_relativo=.0005)
        for key in ('trabajo_neto','rendimiento'):
            self.assertEqual(s1[key]['estado'],'disponible')
            self.assertEqual(s2[key]['estado'],'disponible')
            self.assertAlmostEqual(s1[key]['valor'],s2[key]['valor'],delta=2e-4)
            self.assertEqual(s1[key]['esquema'],'central')

    def test_sensibilidad_unilateral_en_eta_igual_a_uno(self):
        caso={**DEFAULTS,'eta_c':1.0}
        s=sensibilidad_local(caso,'eta_c')
        self.assertEqual(s['trabajo_neto']['estado'],'disponible')
        self.assertEqual(s['trabajo_neto']['esquema'],'atrás')

    def test_sensibilidad_no_definida_para_cero_o_no_motor(self):
        for case,key in [({**DEFAULTS,'delta':0},'delta'),
                         ({**DEFAULTS,'rp':1,'delta':0},'rp')]:
            with self.subTest(case=case):
                s=sensibilidad_local(case,key)
                self.assertTrue(all(v['estado']=='no_disponible' for v in s.values()))

    def test_tendencias_rp_y_objetivos_distintos(self):
        e=barrido_cp_variable(DEFAULTS,'rp',10,50,41)
        f={round(p['x']):p for p in e['filas']}
        self.assertGreater(f[16]['operativas']['trabajo_neto'],f[10]['operativas']['trabajo_neto'])
        self.assertGreater(f[16]['operativas']['trabajo_neto'],f[47]['operativas']['trabajo_neto'])
        self.assertGreater(f[47]['operativas']['rendimiento'],f[16]['operativas']['rendimiento'])
        # El máximo de una malla no demuestra la existencia/ubicación de un óptimo continuo.
        self.assertTrue(all(fila['operativas'] is None or fila['operativas']['rendimiento']>0
                            for fila in e['filas']))


if __name__ == '__main__':
    unittest.main()
