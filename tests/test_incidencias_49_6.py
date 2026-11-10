"""Regresión de visibilidad y transmisión del modo C, sin cambiar la física."""
import unittest
from unittest.mock import patch
from web_app import app
from acoplamiento_motor_mapa_47 import punto_diseno_47, resolver_motor_acoplado
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor


class Incidencias49_6(unittest.TestCase):
    def test_panel_y_controles_parametricos_presentes(self):
        html = app.test_client().get('/turborreactor/interactivo').get_data(as_text=True)
        for identificador in ('estudio49', 'turbo-study49-form', 'study49-tipo',
                              'study49-metrica', 'study49-save', 'study49-chart'):
            self.assertIn('id="'+identificador+'"', html)
        for herramienta in ('svg', 'png', 'csv'):
            self.assertIn('data-study49-tool="'+herramienta+'"', html)

    def test_referencias_c_y_cierres(self):
        for mach, t3, rpm, caudal in ((0,1600,20000,20),
                (.4,1600,20139.258658424602,21.289608196879307),
                (0,1550,19820.93827927391,19.35824005064698)):
            with self.subTest(mach=mach,T3=t3):
                r=simular_turborreactor(dict(DEFAULTS_TURBO,modo_caudal='acoplado',
                    mach=str(mach),T3=str(t3)))['motor_acoplado']
                self.assertAlmostEqual(r['rpm'],rpm,places=6)
                self.assertAlmostEqual(r['caudal_aire'],caudal,places=6)
                self.assertLess(r['norma_residual'],2e-7)
                self.assertLess(abs(r['residuo_masa_turbina']),1e-5)
                self.assertLess(abs(r['residuo_masa_tobera']),1e-5)
                self.assertLess(abs(r['residuo_potencia']),1.)

    def test_http_transmite_mach_t3_y_geometria(self):
        ag=punto_diseno_47()['area_garganta_diseno']
        v=dict(DEFAULTS_TURBO,modo_caudal='acoplado',mach='0.838',T3='1704',
            tipo_tobera='convergente_divergente',area_garganta_fija=str(ag),
            area_salida_fija=str(1.5*ag))
        with patch('turborreactor_web.resolver_motor_acoplado',wraps=resolver_motor_acoplado) as solver:
            respuesta=app.test_client().post('/api/turborreactor/simular',data=v)
        self.assertEqual(respuesta.status_code,200)
        parametros=solver.call_args.kwargs
        self.assertEqual(parametros['mach'],.838)
        self.assertEqual(parametros['T3'],1704)
        self.assertAlmostEqual(parametros['epsilon'],1.5)
        self.assertEqual(parametros['area_garganta'],ag)

    def test_fallo_numerico_sin_resultados_inventados(self):
        ag=punto_diseno_47()['area_garganta_diseno']*1.1
        respuesta=app.test_client().post('/api/turborreactor/simular',data=dict(
            DEFAULTS_TURBO,modo_caudal='acoplado',mach='0.838',T3='1704',
            tipo_tobera='convergente_divergente',area_garganta_fija=str(ag),
            area_salida_fija=str(1.5*ag)))
        self.assertEqual(respuesta.status_code,422)
        datos=respuesta.get_json()
        self.assertFalse(datos['ok'])
        self.assertNotIn('magnitudes',datos)
        self.assertIn('no demuestra',datos['error']['mensaje'])
        self.assertIn('Sin descenso',datos['error']['mensaje'])
