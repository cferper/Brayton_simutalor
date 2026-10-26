"""Verificación 42.C con conservación y gas perfecto independiente."""

import math
import unittest

from choque_normal_cp import resolver_choque_normal
from propiedades_aire import gamma, h, s
from tobera_convergente_divergente_cp import (
    _salida_area, _salida_tras_choque, _sonico,
    resolver_tobera_convergente_divergente)


class ChoqueNormal42C(unittest.TestCase):
    def test_conservaciones_y_segunda_ley(self):
        t0, p0 = 1200., 500.
        c = _sonico(t0,p0)
        antes = _salida_area(t0,p0,c,1.5,supersonica=True)
        r = resolver_choque_normal(antes['T'],antes['p'],antes['V'])
        self.assertGreater(r['M1'],1)
        self.assertLess(r['M2'],1)
        self.assertGreater(r['generacion_entropia'],0)
        self.assertGreater(r['perdida_presion_total'],0)
        self.assertAlmostEqual(r['pt1'],p0,places=5)
        self.assertAlmostEqual(r['Tt'],t0,places=7)
        self.assertLess(abs(r['residuos']['masa']),1e-6)
        self.assertLess(abs(r['residuos']['momento']),1e-6)
        self.assertLess(abs(r['residuos']['energia']),1e-7)

    def test_referencia_gamma_constante_independiente(self):
        # Relaciones clásicas de salto a gamma fijo como contraste, no producción.
        antes = _salida_area(600.,500.,_sonico(600.,500.),1.5,supersonica=True)
        r = resolver_choque_normal(antes['T'],antes['p'],antes['V'])
        g = gamma(antes['T'])
        m1 = r['M1']
        p2p1 = 1+2*g/(g+1)*(m1*m1-1)
        m2 = math.sqrt((1+(g-1)*m1*m1/2)/(g*m1*m1-(g-1)/2))
        self.assertAlmostEqual(r['p2']/r['p1'],p2p1,delta=.02*p2p1)
        self.assertAlmostEqual(r['M2'],m2,delta=.02*m2)

    def test_contrapresion_y_area_choque(self):
        for pb in (315., 330., 350., 390., 400.):
            with self.subTest(pb=pb):
                r = resolver_tobera_convergente_divergente(1200.,500.,pb,1.5)
                self.assertEqual(r['regimen'],'choque_normal_interno')
                self.assertTrue(r['resuelto'])
                self.assertTrue(1 < r['relacion_areas_choque'] < 1.5)
                self.assertAlmostEqual(r['presion_salida'],pb,delta=1e-5)
                self.assertLess(abs(r['residuo_masa']),1e-6)
                self.assertLess(abs(r['choque_normal']['residuo_masa_geometrica']),1e-6)

    def test_frontera_choque_salida_y_transicion_subsonica(self):
        r = resolver_tobera_convergente_divergente(1200.,500.,100.,1.5)
        ps = r['umbral_choque_salida_aproximado']
        choque = resolver_tobera_convergente_divergente(1200.,500.,ps,1.5)
        self.assertEqual(choque['regimen'],'choque_normal_salida')
        self.assertAlmostEqual(choque['relacion_areas_choque'],1.5,places=8)
        self.assertAlmostEqual(choque['presion_salida'],ps,places=6)
        sub = resolver_tobera_convergente_divergente(1200.,500.,480.,1.5)
        self.assertEqual(sub['regimen'],'subsonico_no_bloqueado')
        limite = resolver_tobera_convergente_divergente(1200.,500.,1.,1.)
        self.assertEqual(limite['regimen'],'supersonico_ideal')

    def test_validacion_choque(self):
        for v in (0., -1., float('nan'), float('inf'), True):
            with self.subTest(v=v),self.assertRaises(ValueError):
                resolver_choque_normal(600.,100.,v)
        with self.assertRaises(ValueError):
            resolver_choque_normal(600.,100.,100.)

    def test_areas_casi_uno_y_fronteras(self):
        c = _sonico(1200.,500.)
        for epsilon in (1.0001,1.001,1.01,1.5):
            with self.subTest(epsilon=epsilon):
                pmax = _salida_area(1200.,500.,c,epsilon,supersonica=False)['p']
                pmin = _salida_tras_choque(1200.,500.,c,epsilon,epsilon)[0]['p']
                self.assertGreater(pmax,pmin)
                p = (pmax+pmin)/2
                r = resolver_tobera_convergente_divergente(1200.,500.,p,epsilon)
                self.assertEqual(r['regimen'],'choque_normal_interno')
                self.assertAlmostEqual(r['presion_salida'],p,delta=1e-5)
                self.assertGreater(r['relacion_areas_choque'],1)
                self.assertLess(r['relacion_areas_choque'],epsilon)

    def test_movimiento_choque_con_contrapresion(self):
        posiciones=[]
        for pb in (315.,330.,350.,390.,400.):
            posiciones.append(resolver_tobera_convergente_divergente(
                1200.,500.,pb,1.5)['relacion_areas_choque'])
        self.assertEqual(posiciones,sorted(posiciones,reverse=True))

    def test_limites_termicos_y_rechazo_numerico(self):
        with self.assertRaises(ValueError):
            resolver_choque_normal(200.,100.,-1.)
        with self.assertRaises(ValueError):
            resolver_choque_normal(2000.,100.,900.)

    def test_tolerancias_choque_normal(self):
        u = _salida_area(1200.,500.,_sonico(1200.,500.),1.5,supersonica=True)
        referencias=[]
        for tol in (1e-6,1e-8,1e-10):
            with self.subTest(tolerancia=tol):
                r = resolver_choque_normal(u['T'],u['p'],u['V'],tolerancia=tol)
                referencias.append(r['p2'])
                self.assertLess(abs(r['residuos']['masa']),max(1e-6,20*tol*u['G']))
        self.assertLess(max(referencias)-min(referencias),1e-5)

    def test_entropia_fisica_no_es_residuo_numerico(self):
        r = resolver_tobera_convergente_divergente(1200.,500.,350.,1.5)
        self.assertEqual(r['regimen'],'choque_normal_interno')
        self.assertAlmostEqual(r['choque_normal']['generacion_entropia'],
                               .04750418564,delta=1e-7)
        self.assertAlmostEqual(r['residuo_entropia_salida'],0.,delta=1e-8)
        self.assertAlmostEqual(s(r['temperatura_salida'],r['presion_salida'])-
                               s(1200.,500.),r['choque_normal']['generacion_entropia'],
                               delta=1e-8)

    def test_fronteras_casi_degeneradas_epsilon_uno(self):
        t,p=1200.,500.
        critico=_sonico(t,p)
        for epsilon in (1.000001,1.00001,1.0001,1.001):
            with self.subTest(epsilon=epsilon):
                p_bloqueo=_salida_area(t,p,critico,epsilon,supersonica=False)['p']
                sup=_salida_area(t,p,critico,epsilon,supersonica=True)
                p_choque=resolver_choque_normal(sup['T'],sup['p'],sup['V'])['p2']
                ancho=p_bloqueo-p_choque
                self.assertGreater(ancho,0)
                for fraccion in (.1,.5,.9):
                    pb=p_choque+fraccion*ancho
                    r=resolver_tobera_convergente_divergente(t,p,pb,epsilon)
                    self.assertEqual(r['regimen'],'choque_normal_interno')
                    self.assertAlmostEqual(r['presion_salida'],pb,
                                           delta=max(1e-6,ancho*1e-3))
                por_encima=resolver_tobera_convergente_divergente(
                    t,p,p_bloqueo+ancho*.1,epsilon)
                self.assertEqual(por_encima['regimen'],'subsonico_no_bloqueado')
                por_debajo=resolver_tobera_convergente_divergente(
                    t,p,p_choque-ancho*.1,epsilon)
                self.assertTrue(por_debajo['regimen'].startswith('supersonico'))


if __name__ == '__main__':
    unittest.main()
