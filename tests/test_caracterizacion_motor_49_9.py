"""M49.9: identidades, unidades, disponibilidad y contrato API."""

from copy import deepcopy
from math import isfinite
import unittest

from acoplamiento_motor_mapa_47 import punto_diseno_47
from caracterizacion_motor_49_9 import caracterizar_motor_49_9
from turborreactor_web import simular_turborreactor, valores_turborreactor
from web_app import app


def indicador(panel, clave):
    return next(i for grupo in panel.values() for i in grupo if i['id'] == clave)


class Caracterizacion49_9(unittest.TestCase):
    def setUp(self):
        self.r = simular_turborreactor(valores_turborreactor())
        self.panel = caracterizar_motor_49_9(self.r)

    def test_tres_familias_unidades_y_estados(self):
        self.assertEqual(set(self.panel), {'funcionamiento','consumo','rendimientos'})
        self.assertEqual(indicador(self.panel,'tit')['valor'],self.r['combustor']['T3'])
        self.assertEqual(indicador(self.panel,'tit')['unidad'],'K')
        self.assertEqual(indicador(self.panel,'eta_th')['estado'],'no_disponible')
        self.assertIsNone(indicador(self.panel,'eta_p')['valor'])
        self.assertIsNone(indicador(self.panel,'eta_o')['valor'])
        self.assertIsNone(indicador(self.panel,'rpm')['valor'])

    def test_relaciones_de_presion_tienen_estaciones_distintas(self):
        p=self.panel
        self.assertAlmostEqual(indicador(p,'rp')['valor'],self.r['compresor']['p2']/self.r['compresor']['p1'])
        self.assertAlmostEqual(indicador(p,'tpr')['valor'],self.r['combustor']['p3']/self.r['turbina']['p4'])
        self.assertAlmostEqual(indicador(p,'npr')['valor'],self.r['tobera']['presion_remanso']/self.r['ambiente']['presion'])
        self.assertAlmostEqual(indicador(p,'epr')['valor'],self.r['turbina']['p4']/self.r['compresor']['p1'])
        vuelo=valores_turborreactor();vuelo['mach']='0.7'
        p_vuelo=caracterizar_motor_49_9(simular_turborreactor(vuelo))
        self.assertNotAlmostEqual(indicador(p_vuelo,'epr')['valor'],indicador(p_vuelo,'npr')['valor'])

    def test_caudal_y_empuje_absoluto_a_b_c(self):
        self.assertIsNone(indicador(self.panel,'fn')['valor'])
        a=valores_turborreactor();a['gasto_masico_aire']='20'
        panel=caracterizar_motor_49_9(simular_turborreactor(a))
        self.assertAlmostEqual(indicador(panel,'fn')['valor'],indicador(panel,'fs')['valor']*20)
        self.assertAlmostEqual(indicador(panel,'peje')['valor'],indicador(panel,'weje')['valor']*20)
        self.assertAlmostEqual(indicador(panel,'mf')['valor']/indicador(panel,'ma')['valor'],indicador(panel,'f')['valor'])
        ref=punto_diseno_47()
        a.update(modo_caudal='fijo',gasto_masico_aire='',area_garganta_fija=str(ref['area_garganta_diseno']))
        b=caracterizar_motor_49_9(simular_turborreactor(a))
        self.assertIsNotNone(indicador(b,'ma')['valor'])
        self.assertIsNone(indicador(b,'rpm')['valor'])
        a['modo_caudal']='acoplado'
        c=caracterizar_motor_49_9(simular_turborreactor(a))
        self.assertGreater(indicador(c,'rpm')['valor'],0)

    def test_empuje_no_positivo_o_tobera_no_resuelta(self):
        r=deepcopy(self.r)
        r['prestaciones']['empuje_especifico_neto']=-10.0
        r['prestaciones']['TSFC_kg_N_h']=999.0
        self.assertIsNone(indicador(caracterizar_motor_49_9(r),'tsfc')['valor'])
        r['tobera']=None
        panel=caracterizar_motor_49_9(r)
        self.assertIsNone(indicador(panel,'npr')['valor'])
        self.assertIsNone(indicador(panel,'ve')['valor'])

    def test_api_sin_nan_y_contrato_compatibilidad(self):
        with app.test_client() as cliente:
            res=cliente.post('/api/turborreactor/simular',data=valores_turborreactor())
            mal=valores_turborreactor();mal['T3']='200'
            error=cliente.post('/api/turborreactor/simular',data=mal)
        self.assertEqual(res.status_code,200)
        self.assertEqual(error.status_code,422)
        self.assertNotIn('caracterizacion',error.get_json())
        data=res.get_json()
        self.assertIn('componentes',data)
        self.assertIn('caracterizacion',data)
        for familia in data['caracterizacion'].values():
            for item in familia:
                valor=item['valor']
                self.assertTrue(valor is None or isinstance(valor,str) or isfinite(valor))


if __name__ == '__main__':
    unittest.main()
