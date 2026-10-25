"""Verificación del vuelo cp(T) y sus interfaces; sin validación experimental."""

import math
import unittest
from unittest.mock import patch

from acoplamiento_turbomaquinaria_cp import resolver_acoplamiento
from tobera_cp_variable import resolver_nucleo_con_tobera
from vuelo_cp_variable import (atmosfera_estandar, calcular_remanso,
                               aplicar_difusor, resolver_turborreactor_vuelo)
from propiedades_aire import R_AIRE, gamma, h, s
from ciclo_cp_variable import EstadoFueraDeRango


BASE = dict(mach=0., rp=10, eta_c=.85, T3=1600, delta=.04,
            eta_t=.9, eta_m=.98, eta_n=.95, pi_d=1., T_amb=288.15,
            p_amb=100.)


class PruebasVuelo36(unittest.TestCase):
    def resolver(self, **cambios):
        return resolver_turborreactor_vuelo(**(BASE | cambios))

    def test_isa_nivel_mar_y_referencia_independiente(self):
        r = atmosfera_estandar(0)
        self.assertEqual(r['temperatura'], 288.15)
        self.assertEqual(r['presion'], 101.325)
        self.assertAlmostEqual(r['densidad'], 1.225, delta=.002)

    def test_isa_continuidad_11km_y_20km(self):
        a = atmosfera_estandar(10999.999)
        b = atmosfera_estandar(11000)
        c = atmosfera_estandar(11000.001)
        self.assertLess(abs(a['temperatura']-c['temperatura']), 1e-5)
        self.assertLess(abs(a['presion']-c['presion']), 1e-4)
        self.assertAlmostEqual(b['temperatura'], 216.65, places=8)
        self.assertAlmostEqual(b['presion'], 22.632, delta=.01)
        self.assertAlmostEqual(atmosfera_estandar(20000)['temperatura'], 216.65)
        self.assertAlmostEqual(atmosfera_estandar(20000)['presion'], 5.475, delta=.02)

    def test_remanso_energia_entropia_unidades(self):
        r = calcular_remanso(288.15, 100., .7)
        self.assertAlmostEqual(r['velocidad_vuelo'], .7*math.sqrt(
            gamma(288.15)*R_AIRE*288.15), places=8)
        self.assertAlmostEqual(h(r['temperatura_remanso'])-h(288.15),
                               r['velocidad_vuelo']**2/2000, places=8)
        self.assertAlmostEqual(s(r['temperatura_remanso'], r['presion_remanso']),
                               s(288.15,100), places=8)

    def test_comparacion_analitica_gas_perfecto_aproximada(self):
        M = .4
        r = calcular_remanso(288.15, 100., M)
        g = gamma(288.15)
        T_anal = 288.15*(1+(g-1)*M*M/2)
        p_anal = 100*(T_anal/288.15)**(g/(g-1))
        self.assertLess(abs(r['temperatura_remanso']/T_anal-1), .005)
        self.assertLess(abs(r['presion_remanso']/p_anal-1), .005)

    def test_difusor_sin_calor_y_con_perdida(self):
        remanso = calcular_remanso(288.15, 100, .65)
        d = aplicar_difusor(remanso,.93)
        self.assertEqual(d['temperatura_remanso'], remanso['temperatura_remanso'])
        self.assertAlmostEqual(d['presion_remanso'],.93*remanso['presion_remanso'])

    def test_limite_estatico_milestone35(self):
        actual = self.resolver()
        anterior = resolver_nucleo_con_tobera(288.15,100,10,.85,1600,.04,.9,.98,.95)
        self.assertEqual(actual['remanso']['velocidad_vuelo'],0.)
        self.assertAlmostEqual(actual['nucleo']['presiones'][3],anterior['nucleo']['presiones'][3])
        self.assertAlmostEqual(actual['tobera']['velocidad_salida'],anterior['tobera']['velocidad_salida'])
        self.assertAlmostEqual(actual['empuje_especifico_neto'],
                               anterior['tobera']['empuje_especifico_total'])

    def test_vuelo_empate_y_referencia_estatica(self):
        r = self.resolver(mach=.7, pi_d=.97)
        self.assertAlmostEqual(r['nucleo']['presiones'][0],r['difusor']['presion_remanso'])
        self.assertAlmostEqual(r['tobera']['presion_ambiente'],100)
        self.assertAlmostEqual(r['nucleo']['relacion_salida_ambiente'],
                               r['nucleo']['presiones'][3]/100)
        self.assertEqual(r['nucleo']['presion_referencia_diagnostico'],100)
        self.assertAlmostEqual(r['empuje_especifico_neto'],
                               r['empuje_especifico_momento']-r['resistencia_entrada']+
                               r['empuje_especifico_presion'])
        self.assertAlmostEqual(r['resistencia_entrada'],r['remanso']['velocidad_vuelo'])
        self.assertLess(r['empuje_especifico_neto'],r['tobera']['empuje_especifico_total'])

    def test_no_fuerza_empuje_positivo(self):
        r = self.resolver(mach=.5,rp=3,T3=850,pi_d=.6)
        self.assertLess(r['empuje_especifico_neto'],0)
        self.assertFalse(r['empuje_neto_positivo'])
        self.assertEqual(r['diagnostico'],'empuje_no_positivo')

    def test_sin_margen_es_indefinido(self):
        r = self.resolver(mach=0,rp=2,T3=650,pi_d=.5)
        self.assertLess(r['nucleo']['presiones'][3],r['ambiente']['presion'])
        self.assertEqual(r['diagnostico'],'sin_expansion_disponible')
        self.assertIsNone(r['tobera'])
        self.assertIsNone(r['empuje_especifico_neto'])
        self.assertIsNone(r['empuje_neto_positivo'])

    def test_isa_completa_a_altitud(self):
        r = resolver_turborreactor_vuelo(.5,10,.85,1600,.04,.9,.98,
                                        eta_n=.95,pi_d=.98,altitud_geopotencial=10000)
        self.assertEqual(r['origen_ambiente'],'ISA')
        self.assertEqual(r['ambiente']['altitud_geopotencial'],10000)
        self.assertGreater(r['difusor']['presion_remanso'],0)

    def test_invocacion_unica_nucleo(self):
        with patch('vuelo_cp_variable.resolver_acoplamiento',wraps=resolver_acoplamiento) as spy:
            self.resolver(mach=.4)
            self.assertEqual(spy.call_count,1)

    def test_invalidos_y_dominio(self):
        for cambios in ({'mach':1},{'mach':-.1},{'mach':True},
                        {'pi_d':0},{'pi_d':1.1},{'T_amb':199},
                        {'p_amb':0},{'T_amb':None},{'T3':float('nan')}):
            with self.subTest(cambios=cambios),self.assertRaises(ValueError):
                self.resolver(**cambios)
        for z in (-1,20001,float('inf'),True):
            with self.subTest(z=z),self.assertRaises(ValueError):
                atmosfera_estandar(z)
        with self.assertRaises(ValueError):
            resolver_turborreactor_vuelo(.1,10,.85,1600,.04,.9,.98,
                                        altitud_geopotencial=1000,T_amb=280)
        with self.assertRaises(EstadoFueraDeRango):
            calcular_remanso(1999,100,.99)


if __name__=='__main__':
    unittest.main()
