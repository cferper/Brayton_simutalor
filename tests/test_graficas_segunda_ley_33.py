"""Milestone 33: barras firmadas, entropía, balances y web cp(T)."""
from copy import deepcopy
import unittest
from xml.etree import ElementTree

from cp_variable_web import DEFAULTS, preparar_segunda_ley
from graficas_segunda_ley_cp import (svg_exergias_estados,
                                    svg_generacion_entropia, svg_balances_exergia)
from segunda_ley_cp_variable import analizar_segunda_ley_cp_variable
from ciclo_cp_variable import resolver_ciclo
from web_app import app


def barras(svg):
    return [n.attrib for n in ElementTree.fromstring(svg).iter()
            if n.tag.endswith('rect') and 'data-rol' in n.attrib]


class GraficasSegundaLey33(unittest.TestCase):
    def setUp(self):
        self.ciclo=resolver_ciclo(**DEFAULTS)
        self.e=analizar_segunda_ley_cp_variable(self.ciclo)

    def test_exergias_conservan_cuatro_estados_y_ambiente(self):
        svg=svg_exergias_estados(self.e)
        bs=barras(svg)
        self.assertEqual(len(bs),4)
        for i,b in enumerate(bs):
            self.assertEqual(b['data-rol'],f'Estado {i+1}')
            self.assertAlmostEqual(float(b['data-valor']),self.e['exergias'][i],places=7)
        self.assertIn('288.150 K',svg)
        self.assertIn('100.000 kPa',svg)
        self.assertIn('solo exergía física',svg)

    def test_generacion_corresponde_2g_y_unidades(self):
        svg=svg_generacion_entropia(self.e)
        bs=barras(svg)
        self.assertEqual(len(bs),2)
        for b,v in zip(bs,self.e['generacion']):
            self.assertAlmostEqual(float(b['data-valor']),v,places=9)
        self.assertIn('kJ/(kg·K)',svg)

    def test_balances_cada_termino_conserva_valor_y_residuo(self):
        svg=svg_balances_exergia(self.ciclo,self.e)
        raiz=ElementTree.fromstring(svg)
        self.assertAlmostEqual(float(raiz.attrib['data-residuo-c']),
                               self.e['residuos_balances'][0],delta=1e-9)
        self.assertAlmostEqual(float(raiz.attrib['data-residuo-t']),
                               self.e['residuos_balances'][1],delta=1e-9)
        bs={b['data-rol']:float(b['data-valor']) for b in barras(svg)}
        e1,e2,e3,e4=self.e['exergias']
        esperados={
            'Compresor · wc':self.ciclo['trabajo_compresor'],
            'Compresor · e2−e1':e2-e1,
            'Compresor · eD,c':self.e['destruccion'][0],
            'Turbina · e3−e4':e3-e4,
            'Turbina · wt':self.ciclo['trabajo_turbina'],
            'Turbina · eD,t':self.e['destruccion'][1],
        }
        self.assertEqual(set(bs),set(esperados))
        for rol,v in esperados.items():
            self.assertAlmostEqual(bs[rol],v,places=7)

    def test_valor_firmado_no_se_transforma_en_positivo(self):
        alterado={**self.e, 'exergias':(1.0,-8.0,24.0,30.0)}
        bs=barras(svg_exergias_estados(alterado))
        negativo=bs[1]
        self.assertEqual(float(negativo['data-valor']),-8.0)
        self.assertLess(float(negativo['x']),355)
        self.assertGreater(float(negativo['width']),0)

    def test_inconsistencia_no_se_dibuja_como_balance_valido(self):
        e={**self.e,'estado':'inconsistente'}
        self.assertIsNone(svg_exergias_estados(e))
        self.assertIsNone(svg_generacion_entropia(e))
        self.assertIsNone(svg_balances_exergia(self.ciclo,e))
        e2={**self.e,'generacion':(-.1,.1)}
        self.assertIsNone(svg_generacion_entropia(e2))

    def test_no_motor_mantiene_estados_sin_rendimientos_inventados(self):
        ciclo=resolver_ciclo(**{**DEFAULTS,'rp':1,'delta':0})
        e=analizar_segunda_ley_cp_variable(ciclo)
        self.assertEqual(e['estado'],'no_motor')
        self.assertIsNotNone(svg_exergias_estados(e))
        self.assertIsNotNone(svg_generacion_entropia(e))
        self.assertIsNone(e['eta_ex_compresor'])
        self.assertIsNone(e['eta_ex_turbina'])

    def test_referencia_ambiental_cambia_barras_no_estados(self):
        d1=preparar_segunda_ley(DEFAULTS,T0=288.15,p0=100)
        d2=preparar_segunda_ley(DEFAULTS,T0=300,p0=120)
        self.assertEqual(d1['ciclo']['temperaturas'],d2['ciclo']['temperaturas'])
        self.assertNotEqual(d1['estudio']['exergias'],d2['estudio']['exergias'])
        self.assertIn('300.000 K',d2['svg_estados'])

    def test_integracion_web_cuatro_figuras_y_visor(self):
        form={**{k:str(v) for k,v in DEFAULTS.items()},
              'accion':'segunda_ley','T0':'288.15','p0':'100'}
        r=app.test_client().post('/',data=form)
        self.assertEqual(r.status_code,200)
        t=r.get_data(as_text=True)
        for nombre in ('Exergía destruida','Exergía física de los cuatro estados',
                       'Generación de entropía','Balances exergéticos'):
            self.assertIn(nombre,t)
        self.assertEqual(t.count('class="cp-figure"'),4)
        self.assertIn('data-plot-viewer="cp-segunda-ley"',t)
        self.assertIn('no es la destrucción total',t.lower())
