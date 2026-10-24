"""Fase 2G: verificaciones termodinámicas independientes de 2B/2A."""

from copy import deepcopy
from math import log
import unittest

from ciclo_cp_variable import resolver_ciclo
from propiedades_aire import P_REF, R_AIRE, h, s, s0
from segunda_ley_cp_variable import analizar_segunda_ley_cp_variable as analizar


class SegundaLeyCPTermodinamica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = resolver_ciclo(288.15, 1600., 10., 100., .85, .90, .05)

    def setUp(self):
        self.e = analizar(self.c, 288.15, 100.)

    def test_referencia_numerica_2g_y_primera_ley(self):
        self.assertAlmostEqual(self.c['trabajo_neto'], 402.0707979682794, places=6)
        self.assertAlmostEqual(100*self.c['rendimiento'], 34.89342809411874, places=6)
        self.assertAlmostEqual(self.e['suma_turbomaquinas'], 47.789352054279746, places=7)
        self.assertEqual(self.e['estado'], 'motor')

    def test_entropias_con_formulacion_independiente(self):
        for i, (T, p) in enumerate(zip(self.c['temperaturas'], self.c['presiones'])):
            esperado = s0(T)-(R_AIRE/1000)*log(p/P_REF)
            with self.subTest(estado=i+1):
                self.assertAlmostEqual(self.e['entropias'][i], esperado, places=11)

    def test_generaciones_y_generacion_no_negativa(self):
        e = self.e
        self.assertAlmostEqual(e['generacion'][0], 0.08253534692326198, places=10)
        self.assertAlmostEqual(e['generacion'][1], 0.08331352364512168, places=10)
        self.assertGreaterEqual(min(e['generacion']), 0)
        self.assertEqual(e['diagnosticos'], ())

    def test_reversible_en_compresor(self):
        c = resolver_ciclo(288.15, 1600, 10, 100, 1., .90, .05)
        self.assertLess(abs(analizar(c)['generacion'][0]), 1e-10)

    def test_reversible_en_turbina(self):
        c = resolver_ciclo(288.15, 1600, 10, 100, .85, 1., .05)
        self.assertLess(abs(analizar(c)['generacion'][1]), 1e-10)

    def test_exergia_ambiental_y_estados(self):
        e=self.e
        self.assertAlmostEqual(e['exergias'][0], 0., places=10)
        self.assertAlmostEqual(e['exergias'][1], 292.452988905012, places=7)
        self.assertAlmostEqual(e['exergias'][2], 1118.335756262333, places=7)
        self.assertAlmostEqual(e['exergias'][3], 376.0226173347617, places=7)
        for i,(hi,si) in enumerate(zip(self.c['entalpias'],self.c['entropias'])):
            self.assertAlmostEqual(e['exergias'][i],hi-h(288.15)-288.15*(si-s(288.15,100)),places=9)

    def test_gouy_stodola_y_doble_balance_independiente(self):
        e=self.e
        for j,(origen,destino,trabajo) in enumerate(((0,1,self.c['trabajo_compresor']),
                                                     (2,3,self.c['trabajo_turbina']))):
            sgen=(self.c['entropias'][destino]-self.c['entropias'][origen])
            gouy=288.15*sgen
            balance=(trabajo-(e['exergias'][destino]-e['exergias'][origen])
                     if j==0 else e['exergias'][origen]-e['exergias'][destino]-trabajo)
            with self.subTest(componente=j):
                self.assertAlmostEqual(e['destruccion'][j],gouy,places=8)
                self.assertAlmostEqual(e['balances_exergia'][j],balance,places=8)
                self.assertLess(abs(e['residuos_balances'][j]),1e-8)

    def test_presion_ambiente_desplaza_exergias_pero_no_diferencias(self):
        e2=analizar(self.c,288.15,120.)
        cambio=e2['exergias'][0]-self.e['exergias'][0]
        self.assertNotAlmostEqual(cambio,0,places=6)
        for a,b in zip(self.e['exergias'],e2['exergias']):
            self.assertAlmostEqual(b-a,cambio,places=8)
        for key in ('destruccion','balances_exergia','residuos_balances'):
            for a,b in zip(self.e[key],e2[key]):
                self.assertAlmostEqual(a,b,places=8)

    def test_temperatura_ambiente_modifica_destrucciones_linealmente(self):
        e2=analizar(self.c,300,100)
        for a,b in zip(self.e['destruccion'],e2['destruccion']):
            self.assertAlmostEqual(b/a,300/288.15,places=9)
        self.assertNotAlmostEqual(e2['exergias'][2],self.e['exergias'][2],places=5)

    def test_rendimientos_exergeticos_adimensionales_y_parciales(self):
        self.assertAlmostEqual(self.e['eta_ex_compresor'],0.9247947921033953,places=9)
        self.assertAlmostEqual(self.e['eta_ex_turbina'],0.9676594814514197,places=9)
        self.assertAlmostEqual(sum(self.e['aportaciones_porcentaje']),100,places=10)
        self.assertNotIn('eta_global',self.e)

    def test_ciclo_degenerado_sin_eficiencias(self):
        c=resolver_ciclo(288.15,1600,1,100,.85,.9,0)
        e=analizar(c)
        self.assertEqual(e['estado'],'no_motor')
        self.assertIsNone(e['eta_ex_compresor'])
        self.assertIsNone(e['eta_ex_turbina'])
        self.assertEqual(e['aportaciones_porcentaje'],(None,None))

    def test_negativos_pequenos_no_ocultados_si_son_significativos(self):
        falso=deepcopy(self.c)
        ss=list(falso['entropias']);ss[1]=ss[0]-1e-5
        falso['entropias']=tuple(ss)
        e=analizar(falso)
        self.assertLess(e['generacion'][0],0)
        self.assertEqual(e['estado'],'inconsistente')
        self.assertIsNone(e['eta_ex_compresor'])
        self.assertTrue(e['diagnosticos'])

    def test_redondeo_reversible_se_normaliza_solo_en_banda(self):
        c=deepcopy(self.c)
        ss=list(c['entropias']);ss[1]=ss[0]-2e-11
        c['entropias']=tuple(ss)
        e=analizar(c)
        self.assertEqual(e['generacion'][0],0)
        self.assertAlmostEqual(e['generacion_bruta'][0],-2e-11,delta=1e-14)

    def test_ambiente_y_contrato_invalidos(self):
        for T0,p0 in ((199,100),(2001,100),(288,0),(288,-1),
                      (float('nan'),100),(288,float('inf')),(True,100),('288',100),
                      (288,10**1000)):
            with self.subTest(T0=T0,p0=p0),self.assertRaises(ValueError):
                analizar(self.c,T0,p0)
        with self.assertRaises(ValueError):
            analizar({'temperaturas':[]})


if __name__=='__main__':
    unittest.main()
