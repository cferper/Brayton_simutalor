"""M50.3: verificación con solucionador de producción, sin simular datos."""
import unittest
from copy import deepcopy
from acoplamiento_motor_mapa_47 import punto_diseno_47
from configuraciones_modo_c_50_3 import (configuraciones_verificadas_50_3,
                                           diagnosticar_fallo_50_3)
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor


class ConfiguracionesModoC503(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.casos = configuraciones_verificadas_50_3()
        cls.ref = punto_diseno_47()

    def test_seis_casos_completos_y_unicos(self):
        self.assertEqual(len(self.casos), 6)
        self.assertEqual(len({c['id'] for c in self.casos}), len(self.casos))
        for caso in self.casos:
            self.assertEqual(set(caso['entradas']), set(DEFAULTS_TURBO))
            self.assertEqual(caso['entradas']['modo_caudal'], 'acoplado')
            self.assertEqual(caso['entradas']['gasto_masico_aire'], '')
            self.assertAlmostEqual(float(caso['entradas']['area_garganta_fija']),
                                   self.ref['area_garganta_diseno'])

    def test_todos_convergen_con_el_solucionador_real(self):
        for caso in self.casos:
            with self.subTest(caso=caso['id']):
                resultado = simular_turborreactor(deepcopy(caso['entradas']))
                acoplado = resultado['motor_acoplado']
                self.assertTrue(acoplado['disponible'])
                self.assertLessEqual(acoplado['norma_residual'], 2e-7)
                self.assertGreater(resultado['prestaciones_absolutas']['empuje_neto'], 0)
                self.assertAlmostEqual(acoplado['residuo_masa_tobera'], 0, places=5)
                self.assertAlmostEqual(acoplado['residuo_masa_turbina'], 0, places=5)

    def test_diseno_reproduce_referencia_y_dosificador(self):
        d = self.casos[0]['entradas']
        self.assertEqual(d['tipo_tobera'], 'convergente')
        self.assertEqual(d['area_garganta_fija'], d['area_salida_fija'])
        resultado = simular_turborreactor(d)
        self.assertAlmostEqual(resultado['motor_acoplado']['rpm'], 20000)
        self.assertAlmostEqual(resultado['prestaciones_absolutas']['gasto_masico_aire'], 20)
        self.assertAlmostEqual(resultado['compresor']['p2'] / resultado['compresor']['p1'], 10)

    def test_cd_conserva_area_salida_pertinente(self):
        caso = next(c for c in self.casos if c['id'] == 'cd12')['entradas']
        self.assertAlmostEqual(float(caso['area_salida_fija']) / float(caso['area_garganta_fija']), 1.2)
        self.assertEqual(caso['tipo_tobera'], 'convergente_divergente')

    def test_sin_contaminacion_entre_casos(self):
        original = self.casos[0]['entradas']['mach']
        mutable = deepcopy(self.casos[0]); mutable['entradas']['mach'] = '0.9'
        self.assertEqual(self.casos[0]['entradas']['mach'], original)
        self.assertEqual(self.casos[1]['entradas']['mach'], '0.4')

    def test_clasificacion_con_evidencias_y_sin_afirmar_surges(self):
        ejemplos = {
            'No convergió el balance simultáneo.': 'numerico',
            'Sin descenso del residuo en línea de búsqueda.': 'numerico',
            'Fuera del dominio del mapa [0.5,1.1]': 'mapa',
            'La geometría prescrita no cierra la continuidad del motor.': 'restricciones',
            'La tobera no dispone de una solución física de salida para estas condiciones.': 'modelo',
            'El área de garganta debe ser positiva.': 'entradas',
            'Situación desconocida.': 'indeterminado',
        }
        for texto, esperado in ejemplos.items():
            with self.subTest(texto=texto):
                d = diagnosticar_fallo_50_3(texto)
                self.assertEqual(d['codigo'], esperado)
                self.assertNotIn('surge', d['resumen'].lower())
                self.assertIn('no demuestra', d['recomendacion'])

    def test_api_http_cuando_flask_disponible(self):
        try:
            from web_app import app
        except ModuleNotFoundError as exc:
            if exc.name == 'flask':
                self.skipTest('Flask no instalado: contrato HTTP pendiente de Windows')
            raise
        cliente = app.test_client()
        caso = self.casos[0]['entradas']
        bien = cliente.post('/api/turborreactor/simular', json=caso)
        self.assertEqual(bien.status_code, 200)
        self.assertTrue(bien.get_json()['ok'])
        mal = {**caso, 'area_garganta_fija': str(self.ref['area_garganta_diseno']*1.1)}
        fallo = cliente.post('/api/turborreactor/simular', json=mal)
        self.assertEqual(fallo.status_code, 422)
        cuerpo = fallo.get_json()
        self.assertFalse(cuerpo['ok'])
        self.assertEqual(cuerpo['error']['diagnostico_50_3']['codigo'], 'numerico')
        self.assertIn('no demuestra', cuerpo['error']['diagnostico_50_3']['recomendacion'])

    def test_fallo_no_genera_prestaciones_falsas(self):
        # El motor no devuelve un estado de empuje para el área incompatible.
        from acoplamiento_motor_mapa_47 import resolver_motor_acoplado
        fallido = resolver_motor_acoplado(referencia=self.ref,
                   area_garganta=self.ref['area_garganta_diseno']*1.1)
        self.assertFalse(fallido['disponible'])
        self.assertNotIn('empuje_absoluto', fallido)


if __name__ == '__main__':
    unittest.main()
