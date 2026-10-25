"""Milestone 31: datos OFAT, porcentajes, fronteras e integración Flask."""
import unittest
from xml.etree import ElementTree
from cp_variable_web import DEFAULTS, preparar_sensibilidad
from graficas_sensibilidad_cp import svg_variaciones_relativas, svg_temperaturas_caracteristicas
from sensibilidad_cp_variable import barrido_cp_variable
from web_app import app

FORM = {**{k:str(v) for k,v in DEFAULTS.items()}, 'accion':'sensibilidad',
        'sens_cp_parametro':'T3','sens_cp_minimo':'1450',
        'sens_cp_maximo':'1750','sens_cp_muestras':'7'}


class GraficasSensibilidad31(unittest.TestCase):
    def test_variaciones_finitas_con_valores_de_muestras(self):
        e=barrido_cp_variable(DEFAULTS,'T3',1450,1750,7)
        svg, aviso=svg_variaciones_relativas(e)
        self.assertEqual(aviso,'')
        raiz=ElementTree.fromstring(svg)
        puntos=[c.attrib for c in raiz.iter() if c.tag.endswith('circle')]
        self.assertEqual(len(puntos),14)
        base=e['referencia']['ciclo']
        for fila in e['filas']:
            x=100*(fila['x']-DEFAULTS['T3'])/DEFAULTS['T3']
            valores=[p for p in puntos if abs(float(p['data-x'])-x)<1e-8]
            self.assertEqual(len(valores),2)
            esperado={'ΔW/W0':100*(fila['operativas']['trabajo_neto']-base['trabajo_neto'])/base['trabajo_neto'],
                     'Δη/η0':100*(fila['operativas']['rendimiento']-base['rendimiento'])/base['rendimiento']}
            for p in valores:
                self.assertAlmostEqual(float(p['data-valor']),esperado[p['data-serie']],places=8)
        self.assertIn('Variación finita',svg)
        self.assertIn('data-referencia="0"',svg)

    def test_delta_cero_da_diagnostico_sin_division_infinita(self):
        e=barrido_cp_variable({**DEFAULTS,'delta':0},'delta',0,.1,5)
        svg, aviso=svg_variaciones_relativas(e)
        self.assertIsNone(svg)
        self.assertIn('es cero',aviso)

    def test_no_motor_referencia_no_publica_porcentajes(self):
        e=barrido_cp_variable({**DEFAULTS,'rp':1,'delta':0},'rp',1,4,5)
        svg, aviso=svg_variaciones_relativas(e)
        self.assertIsNone(svg)
        self.assertIn('no es motor',aviso)

    def test_huecos_no_se_unen(self):
        e=barrido_cp_variable(DEFAULTS,'rp',.5,3,6)
        svg, _=svg_variaciones_relativas(e)
        if svg:
            raiz=ElementTree.fromstring(svg)
            puntos=[n for n in raiz.iter() if n.tag.endswith('circle')]
            self.assertEqual(len(puntos),2*e['conteos'].get('motor',0))
            self.assertNotIn('nan',svg.lower())

    def test_temperaturas_son_estados_calculados_y_solo_motor(self):
        e=barrido_cp_variable(DEFAULTS,'eta_t',.7,1,7)
        svg=svg_temperaturas_caracteristicas(e)
        raiz=ElementTree.fromstring(svg)
        puntos=[n.attrib for n in raiz.iter() if n.tag.endswith('circle')]
        for fila in e['filas']:
            for clave in ('T2','T4'):
                coinciden=[p for p in puntos if p['data-serie']==clave
                           and abs(float(p['data-x'])-fila['x'])<1e-8]
                if fila['operativas']:
                    self.assertEqual(len(coinciden),1)
                    self.assertAlmostEqual(float(coinciden[0]['data-valor']),
                                           fila['operativas'][clave],places=8)
                else:
                    self.assertFalse(coinciden)
        self.assertIn('[K]',svg)

    def test_web_cinco_graficas_y_sin_calculos_ajenos(self):
        r=app.test_client().post('/',data=FORM)
        self.assertEqual(r.status_code,200)
        html=r.get_data(as_text=True)
        self.assertIn('Variaciones relativas',html)
        self.assertIn('Temperaturas características',html)
        self.assertIn('data-plot-viewer="cp-sensibilidad"',html)
        self.assertGreaterEqual(html.count('data-serie='),14)

    def test_web_delta_cero_muestra_diagnostico(self):
        r=app.test_client().post('/',data={**FORM,'delta':'0',
                                            'sens_cp_parametro':'delta',
                                            'sens_cp_minimo':'0',
                                            'sens_cp_maximo':'0.1'})
        self.assertEqual(r.status_code,200)
        self.assertIn('parámetro de referencia es cero',r.get_data(as_text=True))
