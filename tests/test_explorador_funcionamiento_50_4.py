"""M50.4: contratos reales del estudio M49.5 y su ampliación al motor C."""
import json
import math
import unittest
from unittest.mock import patch

from configuraciones_modo_c_50_3 import configuraciones_verificadas_50_3
from estudios_parametricos_49_5 import (calcular_estudio_49_5,
    configurar_estudio_49_5, _diagnostico_fallo_c_50_4)
from turborreactor_web import simular_turborreactor, valores_turborreactor


class Explorador50_4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.diseno = next(c['entradas'] for c in configuraciones_verificadas_50_3()
                          if c['id'] == 'diseno')

    def test_diseno_y_comparacion_directa_del_modo_c(self):
        d = calcular_estudio_49_5(self.diseno, {
            'tipo':'mapa', 'mach_inicio':0, 'mach_fin':.4, 'mach_puntos':2,
            'T3_inicio':1600, 'T3_fin':1650, 'T3_puntos':2})
        self.assertEqual(d['resumen']['total'], 4)
        self.assertEqual(d['resumen']['validos']+d['resumen']['sin_solucion'], 4)
        self.assertEqual(d['modo'], 'acoplado')
        self.assertEqual(d['puntos'][0]['clasificacion'], 'convergencia_verificada')
        self.assertEqual(d['puntos'][0]['estado'], 'valido')
        self.assertEqual(d['puntos'][0]['iteraciones'], 0)
        for p in d['puntos']:
            if p['estado'] != 'valido':
                self.assertIsNone(p['rpm'])
                self.assertIsNone(p['caudal_aire'])
                continue
            directo = simular_turborreactor(p['entradas'])
            motor = directo['motor_acoplado']
            self.assertTrue(motor['disponible'])
            self.assertLessEqual(motor['norma_residual'], 2e-7)
            self.assertAlmostEqual(p['rpm'], motor['rpm'], places=5)
            self.assertAlmostEqual(p['caudal_aire'], motor['caudal_aire'], places=6)
            self.assertAlmostEqual(p['relacion_compresion'], motor['compresor_mapa']['rp'], places=7)
            self.assertAlmostEqual(p['rendimiento_compresor'], motor['compresor_mapa']['eta'], places=7)
            self.assertAlmostEqual(p['rline'], motor['compresor_mapa']['rline'], places=7)
            self.assertAlmostEqual(p['empuje_N'], directo['prestaciones_absolutas']['empuje_neto'], places=5)
            self.assertTrue(math.isfinite(p['norma_residual']))
            self.assertGreater(p['caudal_corregido'], 0)
            self.assertGreater(p['rpm_corregidas'], 0)
        self.assertEqual(sum(d['resumen']['por_clasificacion'].values()), 4)
        self.assertIsNotNone(json.dumps(d, allow_nan=False))

    def test_constantes_y_entradas_completas_por_celda(self):
        base = dict(self.diseno)
        d = calcular_estudio_49_5(base, {
            'tipo':'mapa', 'mach_inicio':0, 'mach_fin':.4, 'mach_puntos':2,
            'T3_inicio':1550, 'T3_fin':1650, 'T3_puntos':3})
        self.assertEqual(base, self.diseno)
        for clave in ('area_garganta_fija','area_salida_fija','tipo_tobera',
                      'eta_n','pi_d','delta_pct','modo_ambiente'):
            self.assertEqual(d['constantes'][clave],base[clave])
            self.assertTrue(all(p['entradas'][clave]==base[clave] for p in d['puntos']))
        self.assertEqual(d['puntos'][0]['T3'], 1550)
        self.assertEqual(d['puntos'][2]['T3'], 1600)
        self.assertEqual(d['puntos'][0]['mach'], 0)
        self.assertEqual(d['puntos'][1]['mach'], .4)

    def test_fallos_clasificados_con_prudencia_y_nulos(self):
        ejemplos=[
            ('Fuera del dominio del mapa HPC', 'fuera_mapa','sin_solucion'),
            ('Sin descenso del residuo en línea de búsqueda.',
             'sin_convergencia_numerica','fallo_numerico'),
            ('Tobera no dispone de una solución física de salida.',
             'modelo_no_resuelto','sin_solucion'),
            ('El campo Mach debe ser finito.', 'entrada_fuera_dominio','fuera_dominio'),
            ('Razón desconocida del modelo', 'causa_indeterminada','sin_solucion'),
        ]
        for mensaje,clase,estado in ejemplos:
            with self.subTest(mensaje=mensaje), patch(
                'estudios_parametricos_49_5.simular_turborreactor',
                side_effect=ValueError(mensaje)):
                d=calcular_estudio_49_5(self.diseno, {
                    'tipo':'mach','mach_inicio':0,'mach_fin':.2,'mach_puntos':2})
                for p in d['puntos']:
                    self.assertEqual((p['clasificacion'],p['estado']),(clase,estado))
                    self.assertIsNone(p['TSFC'])
                    self.assertTrue(all(p[k] is None for k in
                        ('caudal_aire','caudal_corregido','rpm','rpm_corregidas',
                         'relacion_compresion','rendimiento_compresor',
                         'rline','iteraciones','norma_residual')))

    def test_resultado_c_no_verificado_no_es_aceptado(self):
        falso={'tobera':{'resuelto':True},'motor_acoplado':{'disponible':False},
               'prestaciones':{'empuje_especifico_neto':123}}
        with patch('estudios_parametricos_49_5.simular_turborreactor',return_value=falso):
            d=calcular_estudio_49_5(self.diseno, {
                'tipo':'mach','mach_inicio':0,'mach_fin':.2,'mach_puntos':2})
        self.assertEqual(d['resumen']['validos'],0)
        self.assertEqual(d['puntos'][0]['clasificacion'],'sin_convergencia_numerica')

    def test_malla_limitada_al_costo_m49_5(self):
        a={'tipo':'mapa','mach_inicio':0,'mach_fin':.9,'mach_puntos':6,
           'T3_inicio':1400,'T3_fin':1800,'T3_puntos':6}
        self.assertEqual(len(configurar_estudio_49_5(a,'acoplado')['y']),6)
        with self.assertRaises(ValueError):
            configurar_estudio_49_5({**a,'mach_puntos':7},'acoplado')
        with self.assertRaises(ValueError):
            configurar_estudio_49_5({**a,'T3_puntos':6.5},'acoplado')

    def test_endpoint_existente_devuelve_resultados_ampliados(self):
        try:
            from web_app import app
        except ModuleNotFoundError as exc:
            if exc.name == 'flask':
                self.skipTest('Flask no disponible para prueba HTTP.')
            raise
        configuracion = {'tipo':'mapa', 'mach_inicio':0, 'mach_fin':.4,
                         'mach_puntos':2, 'T3_inicio':1600, 'T3_fin':1650,
                         'T3_puntos':2}
        respuesta = app.test_client().post('/api/turborreactor/estudio',
                    json={'parametros':self.diseno, 'estudio':configuracion})
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.get_json()
        self.assertTrue(datos['ok'])
        self.assertEqual(datos['estudio']['modo'], 'acoplado')
        self.assertIn('rpm_corregidas', datos['estudio']['puntos'][0])
        self.assertIn('entradas', datos['estudio']['puntos'][0])

    def test_a_b_no_exigen_diagnosticos_del_modo_c(self):
        base=valores_turborreactor()
        for modo,otros in (('impuesto',{'gasto_masico_aire':'20'}),
                            ('fijo',{'area_garganta_fija':self.diseno['area_garganta_fija']})):
            with self.subTest(modo=modo):
                v={**base,'modo_caudal':modo,**otros}
                d=calcular_estudio_49_5(v,{'tipo':'mach','mach_inicio':0,
                                          'mach_fin':.2,'mach_puntos':2})
                self.assertEqual(d['modo'],modo)
                self.assertTrue(all('empuje_especifico' in p for p in d['puntos']))
                self.assertTrue(all('clasificacion' not in p for p in d['puntos']))


if __name__ == '__main__':
    unittest.main()
