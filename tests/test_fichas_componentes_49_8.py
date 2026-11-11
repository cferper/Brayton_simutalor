"""M49.8: datos de fichas coherentes con el solucionador, sin estáticas inventadas."""

import unittest

from turborreactor_web import (fichas_componentes_49_8, simular_turborreactor,
                               valores_turborreactor)
from acoplamiento_motor_mapa_47 import punto_diseno_47
from web_app import app


def campo(fichas, pieza, etiqueta):
    return next(f for f in fichas[pieza] if f['etiqueta'] == etiqueta)


class Fichas49_8(unittest.TestCase):
    def test_seis_componentes_y_procedencia(self):
        r=simular_turborreactor(valores_turborreactor())
        f=fichas_componentes_49_8(r)
        self.assertEqual(set(f), {'difusor','compresor','camara','turbina','eje','tobera'})
        for pieza in f.values():
            self.assertTrue(all('origen' in dato and 'unidad' in dato and 'clase' in dato for dato in pieza))
        self.assertEqual(campo(f,'compresor','Temperatura total de salida')['valor'],r['compresor']['T2'])
        self.assertEqual(campo(f,'compresor','Temperatura total de salida')['clase'],'total')
        self.assertEqual(campo(f,'camara','Temperatura total de salida (T3 interna)')['valor'],r['combustor']['T3'])
        self.assertEqual(campo(f,'turbina','Trabajo extraído')['valor'],r['turbina']['trabajo_turbina_por_kg_aire'])
        self.assertEqual(campo(f,'tobera','Temperatura estática de salida')['valor'],r['tobera']['temperatura_salida'])
        self.assertEqual(campo(f,'tobera','Temperatura estática de salida')['clase'],'estatica')
        self.assertIsNone(campo(f,'eje','Régimen de giro (solo C)')['valor'])

    def test_api_contiene_fichas_sin_modificar_estaciones(self):
        with app.test_client() as client:
            respuesta=client.post('/api/turborreactor/simular',data=valores_turborreactor())
        self.assertEqual(respuesta.status_code,200)
        datos=respuesta.get_json()
        self.assertTrue(datos['ok'])
        self.assertIn('componentes',datos)
        self.assertEqual(len(datos['estaciones']),6)
        self.assertEqual(datos['componentes']['tobera'][0]['clase'],'total')

    def test_no_genera_estaticas_internas_ni_caudal_absoluto_ficticio(self):
        r=simular_turborreactor(valores_turborreactor())
        f=fichas_componentes_49_8(r)
        for pieza in ('compresor','camara','turbina'):
            self.assertTrue(all(d['clase']!='estatica' for d in f[pieza]))
        self.assertIsNone(campo(f,'camara','Caudal de combustible')['valor'])
        self.assertIsNone(campo(f,'eje','Potencia transmitida')['valor'])

    def test_modalidades_a_b_c_y_rpm_solo_c(self):
        ref=punto_diseno_47()
        parametros=valores_turborreactor()
        parametros.update(gasto_masico_aire='20')
        a=fichas_componentes_49_8(simular_turborreactor(parametros))
        self.assertIsNotNone(campo(a,'camara','Caudal de combustible')['valor'])
        parametros.update(modo_caudal='fijo',gasto_masico_aire='',
                          area_garganta_fija=str(ref['area_garganta_diseno']))
        b=fichas_componentes_49_8(simular_turborreactor(parametros))
        self.assertIsNone(campo(b,'eje','Régimen de giro (solo C)')['valor'])
        parametros['modo_caudal']='acoplado'
        c=fichas_componentes_49_8(simular_turborreactor(parametros))
        self.assertGreater(campo(c,'eje','Régimen de giro (solo C)')['valor'],0)

    def test_tobera_cd_solo_expone_estaticas_resueltas(self):
        parametros=valores_turborreactor()
        parametros.update(tipo_tobera='convergente_divergente',epsilon='1.5')
        r=simular_turborreactor(parametros)
        f=fichas_componentes_49_8(r)
        self.assertEqual(campo(f,'tobera','Temperatura estática de garganta')['valor'],
                         r['tobera'].get('temperatura_garganta'))
        self.assertEqual(campo(f,'tobera','Mach de salida')['valor'],
                         r['tobera'].get('mach_salida'))

    def test_tobera_sin_solucion_no_rompe_la_ficha(self):
        r=simular_turborreactor(valores_turborreactor())
        r['tobera']=None
        f=fichas_componentes_49_8(r)
        self.assertIsNone(campo(f,'tobera','Temperatura total de entrada')['valor'])
        self.assertIsNone(campo(f,'tobera','Temperatura estática de salida')['valor'])


if __name__=='__main__':
    unittest.main()
