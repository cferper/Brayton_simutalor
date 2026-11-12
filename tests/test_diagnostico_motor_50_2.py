"""M50.2 — caudal y giro corregidos, mapa educativo y contrato web."""
import unittest

from diagnostico_motor_50_2 import diagnosticar_motor_50_2, svg_mapa_compresor_50_2
from mapas_turbomaquinaria_47 import flujo_corregido, giro_corregido
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor, preparar_vista_turborreactor
try:
    from web_app import app
except ImportError as exc:
    if exc.name not in ("flask", "jinja2", "werkzeug"):
        raise
    app = None


class DiagnosticoMotor50_2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valores = dict(DEFAULTS_TURBO)
        cls.a = simular_turborreactor(dict(cls.valores))
        cls.fijo = simular_turborreactor({**cls.valores,'modo_caudal':'fijo',
                'area_garganta_fija':'0.04734811643457149',
                'area_salida_fija':'0.04734811643457149'})
        cls.c = simular_turborreactor({**cls.valores,'modo_caudal':'acoplado'})

    def test_a_sin_caudal_no_inventa_absolutos_ni_rpm(self):
        d=diagnosticar_motor_50_2(self.a)
        self.assertIsNone(d['caudal_corregido_kg_s'])
        self.assertIsNone(d['giro_corregido_rpm'])
        self.assertIsNone(d['punto_compresor'])
        self.assertIsNone(d['curvas_compresor'])

    def test_a_con_caudal_deriva_correccion_pero_no_giro(self):
        r=simular_turborreactor({**self.valores,'gasto_masico_aire':'20'})
        d=diagnosticar_motor_50_2(r)
        c=r['compresor']
        self.assertAlmostEqual(d['caudal_corregido_kg_s'],flujo_corregido(20,c['T1'],c['p1']))
        self.assertIsNone(d['giro_corregido_rpm'])
        self.assertEqual(d['dominio'].startswith('No aplicable'),True)

    def test_b_caudal_corregido_pero_sin_punto_mapa(self):
        d=diagnosticar_motor_50_2(self.fijo)
        c=self.fijo['compresor']
        ma=self.fijo['prestaciones_absolutas']['gasto_masico_aire']
        self.assertAlmostEqual(d['caudal_corregido_kg_s'],flujo_corregido(ma,c['T1'],c['p1']))
        self.assertIsNone(d['giro_corregido_rpm'])
        self.assertIsNone(d['punto_compresor'])
        self.assertEqual(svg_mapa_compresor_50_2(d),'')

    def test_c_utiliza_estacion_total_y_punto_resuelto(self):
        d=diagnosticar_motor_50_2(self.c)
        motor=self.c['motor_acoplado'];comp=self.c['compresor']
        punto=d['punto_compresor']
        self.assertAlmostEqual(d['giro_corregido_rpm'],giro_corregido(motor['rpm'],comp['T1']))
        self.assertAlmostEqual(d['caudal_corregido_kg_s'],motor['compresor_mapa']['caudal_corregido'])
        self.assertAlmostEqual(punto['relacion_compresion'],motor['compresor_mapa']['rp'])
        self.assertAlmostEqual(punto['giro_mapa'],motor['compresor_mapa']['giro_mapa'])
        self.assertEqual(len(d['curvas_compresor']),13)
        self.assertGreater(len(d['curvas_compresor'][0]['puntos']),1)
        self.assertIn('Dentro del dominio',d['dominio'])

    def test_mapas_son_escalados_y_marcadores_realmente_calculados(self):
        d=diagnosticar_motor_50_2(self.c)
        svg=svg_mapa_compresor_50_2(d)
        self.assertIn('<svg',svg)
        self.assertIn('Punto C actual',svg)
        self.assertIn('data-plot-info=',svg)
        self.assertIn('Sin margen de surge',svg)
        self.assertNotIn('margen de bombeo: ',svg.lower())
        self.assertEqual(len(d['curvas_compresor']),13)
        self.assertEqual(d['curvas_compresor'][0]['puntos'][0]['rline'],1.0)

    def test_rpm_invalida_y_caudal_ausente_no_se_inventan(self):
        r=dict(self.c)
        r['motor_acoplado']={**self.c['motor_acoplado'],'rpm':None}
        d=diagnosticar_motor_50_2(r)
        self.assertIsNone(d['giro_corregido_rpm'])
        self.assertIsNone(d['punto_compresor'])
        self.assertEqual(svg_mapa_compresor_50_2(d),'')
        r2={**self.a,'prestaciones_absolutas':{}}
        self.assertIsNone(diagnosticar_motor_50_2(r2)['caudal_corregido_kg_s'])

    @unittest.skipIf(app is None, "Flask no está instalado en el entorno de ejecución")
    def test_api_presenta_un_solo_punto_y_panel_exclusivo_interactivo(self):
        with app.test_client() as cliente:
            pagina=cliente.get('/turborreactor/interactivo').get_data(as_text=True)
            clasico=cliente.get('/turborreactor').get_data(as_text=True)
            self.assertIn('id="turbo-diagnostic-50-2"',pagina)
            self.assertIn('diagnostico_motor_50_2.js',pagina)
            self.assertNotIn('id="turbo-diagnostic-50-2"',clasico)
            respuesta=cliente.post('/api/turborreactor/simular',json=self.valores)
            self.assertEqual(respuesta.status_code,200)
            datos=respuesta.get_json()
        self.assertTrue(datos['ok'])
        self.assertIn('diagnostico_50_2',datos)
        self.assertIsNone(datos['diagnostico_50_2']['giro_real_rpm'])
        self.assertIn('svg_mapa_compresor_50_2',datos['svg'])
        self.assertEqual(datos['svg']['svg_mapa_compresor_50_2'],'')

    @unittest.skipIf(app is None, "Flask no está instalado en el entorno de ejecución")
    def test_api_modo_c_mapa_coherente_y_error_422(self):
        with app.test_client() as cliente:
            ok=cliente.post('/api/turborreactor/simular',json={**self.valores,'modo_caudal':'acoplado'})
            mal=cliente.post('/api/turborreactor/simular',json={**self.valores,'mach':'1.5'})
        self.assertEqual(ok.status_code,200)
        datos=ok.get_json()
        self.assertEqual(datos['diagnostico_50_2']['modo'],'acoplado')
        self.assertIn('<svg',datos['svg']['svg_mapa_compresor_50_2'])
        self.assertEqual(mal.status_code,422)
        self.assertFalse(mal.get_json()['ok'])
        self.assertNotIn('diagnostico_50_2',mal.get_json())


if __name__=='__main__': unittest.main()
