"""Verificación M42.A: balances independientes y referencia analítica perfecta."""

import math
import unittest

from ciclo_cp_variable import EstadoFueraDeRango
from propiedades_aire import R_AIRE, gamma, h, s
from tobera_cp_variable import resolver_tobera_convergente
from tobera_convergente_divergente_cp import (
    relacion_areas_adaptada, resolver_tobera_convergente_divergente,
)


TT, PT = 1200., 500.
P_ADAPTADA = 70.


def _relacion_area_perfecta(mach, g):
    """Referencia de libro sin funciones del solucionador de producción."""
    return (1/mach)*((2/(g+1))*(1+(g-1)*mach*mach/2))**(
        (g+1)/(2*(g-1)))


class ConvergenteDivergente42A(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.epsilon = relacion_areas_adaptada(TT, PT, P_ADAPTADA)

    def test_salida_adaptada_y_mach(self):
        r = resolver_tobera_convergente_divergente(TT,PT,70,self.epsilon)
        self.assertTrue(r['resuelto'])
        self.assertEqual(r['adaptacion'],'adaptada')
        self.assertAlmostEqual(r['presion_salida'],70,places=7)
        self.assertGreater(r['mach_salida'],1)
        self.assertAlmostEqual(r['mach_garganta'],1,places=8)
        self.assertGreater(self.epsilon,1)

    def test_subexpandida(self):
        r = resolver_tobera_convergente_divergente(TT,PT,40,self.epsilon)
        self.assertTrue(r['resuelto'])
        self.assertEqual(r['adaptacion'],'subexpandida')
        self.assertGreater(r['empuje_especifico_presion'],0)
        self.assertGreater(r['presion_salida'],r['presion_ambiente'])

    def test_sobreexpandida_ideal_y_limitaciones(self):
        r = resolver_tobera_convergente_divergente(TT,PT,140,self.epsilon)
        self.assertTrue(r['resuelto'])
        self.assertEqual(r['adaptacion'],'sobreexpandida')
        self.assertEqual(r['regimen'],'supersonico_sobreexpandido_ideal')
        self.assertLess(r['empuje_especifico_presion'],0)
        self.assertIn('separación',r['diagnostico'])

    def test_zona_de_choque_sin_empuje_ficticio(self):
        r = resolver_tobera_convergente_divergente(TT,PT,400,self.epsilon)
        self.assertFalse(r['resuelto'])
        self.assertIn('choque',r['regimen'])
        for clave in ('mach_salida','presion_salida','empuje_especifico_total',
                      'diferencia_presiones','residuo_masa'):
            self.assertIsNone(r[clave])
        self.assertGreater(r['umbral_choque_salida_aproximado'],0)

    def test_choque_conserva_garganta_conocida_sin_fingir_salida(self):
        r = resolver_tobera_convergente_divergente(TT, PT, 400, self.epsilon)
        r_ref = resolver_tobera_convergente_divergente(TT, PT, 70, self.epsilon)
        self.assertFalse(r['resuelto'])
        for clave in ('temperatura_garganta', 'presion_garganta',
                      'densidad_garganta', 'velocidad_garganta', 'mach_garganta'):
            self.assertIsNotNone(r[clave])
            self.assertAlmostEqual(r[clave], r_ref[clave], places=8)
        self.assertAlmostEqual(r['mach_garganta'], 1, places=8)
        for clave in ('velocidad_salida','temperatura_salida','densidad_salida',
                      'presion_salida','empuje_especifico_total',
                      'residuo_masa','residuo_energia_garganta',
                      'residuo_entropia_garganta'):
            self.assertIsNone(r[clave])

    def test_frontera_aproximada_choque_y_advertencia(self):
        base = resolver_tobera_convergente_divergente(TT, PT, 140, self.epsilon)
        umbral = base['umbral_choque_salida_aproximado']
        self.assertGreater(umbral, 140)
        debajo = resolver_tobera_convergente_divergente(TT, PT, umbral*(1-2e-6),
                                                        self.epsilon)
        encima = resolver_tobera_convergente_divergente(TT, PT, umbral*(1+2e-6),
                                                        self.epsilon)
        self.assertTrue(debajo['resuelto'])
        self.assertEqual(debajo['regimen'], 'supersonico_sobreexpandido_ideal')
        self.assertIn('gamma local', debajo['diagnostico'])
        self.assertFalse(encima['resuelto'])
        self.assertIn('choque', encima['regimen'])
        self.assertIsNone(encima['empuje_especifico_total'])
        self.assertAlmostEqual(encima['mach_garganta'], 1, places=8)
        self.assertAlmostEqual(debajo['umbral_choque_salida_aproximado'], umbral)

    def test_subsonica_no_bloqueada(self):
        r = resolver_tobera_convergente_divergente(TT,PT,480,self.epsilon)
        self.assertEqual(r['regimen'],'subsonico_no_bloqueado')
        self.assertLess(r['mach_garganta'],1)
        self.assertLess(r['mach_salida'],r['mach_garganta'])
        self.assertAlmostEqual(r['presion_salida'],480,places=7)
        self.assertAlmostEqual(r['empuje_especifico_presion'],0,places=7)

    def test_masa_energia_entropia_y_unidades(self):
        for pamb in (40,70,140,480):
            with self.subTest(pamb=pamb):
                r = resolver_tobera_convergente_divergente(TT,PT,pamb,self.epsilon)
                self.assertLess(abs(r['residuo_masa']),1e-8)
                self.assertLess(abs(r['residuo_energia_garganta']),1e-8)
                self.assertLess(abs(r['residuo_energia_salida']),1e-8)
                self.assertLess(abs(r['residuo_entropia_garganta']),1e-10)
                self.assertLess(abs(r['residuo_entropia_salida']),1e-10)
                self.assertAlmostEqual(r['flujo_masico_por_area_garganta'],
                    self.epsilon*r['flujo_masico_por_area_salida'],places=7)
                self.assertAlmostEqual(r['densidad_salida']*r['velocidad_salida'],
                                       r['flujo_masico_por_area_salida'],places=8)
                self.assertAlmostEqual(r['velocidad_salida']**2,
                    2000*(h(TT)-h(r['temperatura_salida'])),places=6)
                self.assertAlmostEqual(s(TT,PT),
                    s(r['temperatura_salida'],r['presion_salida']),places=9)
                presion = (r['presion_salida']-pamb)*1000*r['area_salida_por_caudal']
                self.assertAlmostEqual(presion,r['empuje_especifico_presion'],places=8)
                self.assertAlmostEqual(r['empuje_especifico_total'],
                    r['empuje_especifico_momento']+presion,places=8)

    def test_relacion_areas_y_convergencia(self):
        for e in (1.1,1.3,self.epsilon,2.,2.4):
            with self.subTest(e=e):
                r = resolver_tobera_convergente_divergente(TT,PT,20,e)
                self.assertAlmostEqual(r['flujo_masico_por_area_garganta']/
                    r['flujo_masico_por_area_salida'],e,places=7)

    def test_relacion_adaptada_reconstruye_salida(self):
        for p in (50.,70.,100.,150.):
            with self.subTest(p=p):
                e = relacion_areas_adaptada(TT,PT,p)
                r = resolver_tobera_convergente_divergente(TT,PT,p,e)
                self.assertEqual(r['adaptacion'],'adaptada')
                self.assertAlmostEqual(r['presion_salida'],p,places=6)

    def test_frente_de_bloqueo_continuidad(self):
        # Búsqueda externa para identificar el límite (sin llamar a auxiliares).
        lo, hi = 300.,499.
        for _ in range(55):
            m = (lo+hi)/2
            r = resolver_tobera_convergente_divergente(TT,PT,m,self.epsilon)
            if r['regimen']=='subsonico_no_bloqueado':
                hi=m
            else:
                lo=m
        r1=resolver_tobera_convergente_divergente(TT,PT,hi+1e-4,self.epsilon)
        r2=resolver_tobera_convergente_divergente(TT,PT,hi+1e-3,self.epsilon)
        self.assertEqual(r1['regimen'],'subsonico_no_bloqueado')
        self.assertLess(r2['mach_garganta'],r1['mach_garganta'])
        self.assertLess(1-r1['mach_garganta'],.02)

    def test_comparacion_gamma_constante_independiente(self):
        # A Tt moderada cp(T) cambia poco; nunca exigir igualdad exacta.
        r=resolver_tobera_convergente_divergente(600,500,40,1.5)
        g=gamma(600)
        # Ecuaciones analíticas con gamma congelada; referencia distinta.
        pcrit_perfecta=(2/(g+1))**(g/(g-1))
        self.assertLess(abs(r['presion_critica']/500-pcrit_perfecta),.025)
        # Invertir INDEPENDIENTEMENTE A/A*=1.5 por bisección con gamma constante.
        bajo, alto = 1., 5.
        for _ in range(80):
            medio=(bajo+alto)/2
            if _relacion_area_perfecta(medio,g) < 1.5:
                bajo=medio
            else:
                alto=medio
        mach_perfecto=(bajo+alto)/2
        diferencia_relativa=abs(r['mach_salida']-mach_perfecto)/mach_perfecto
        # 3 % admite la diferencia cp(T) frente a cp fijo en el tramo 600 K.
        # No se interpreta como incertidumbre experimental ni igualdad exacta.
        self.assertLess(diferencia_relativa,.03)

    def test_convergente_historica_preservada(self):
        r=resolver_tobera_convergente(1200,500,40,1)
        self.assertEqual(r['regimen'],'bloqueado')
        self.assertAlmostEqual(r['mach_salida'],1,places=8)
        self.assertAlmostEqual(r['presion_critica'],
            resolver_tobera_convergente_divergente(1200,500,40,1.5)['presion_critica'],places=6)

    def test_area_unidad_limite_convergente(self):
        r=resolver_tobera_convergente_divergente(1200,500,40,1)
        original=resolver_tobera_convergente(1200,500,40,1)
        self.assertAlmostEqual(r['mach_salida'],1,places=8)
        self.assertAlmostEqual(r['presion_salida'],original['presion_salida'],places=7)

    def test_inverso_rechaza_rama_subsonica(self):
        with self.assertRaises(ValueError):
            relacion_areas_adaptada(TT,PT,490)

    def test_entradas_invalidas(self):
        for args in ((1200,500,40,.9),(200,500,40,1.5),
                     (2001,500,40,1.5),(1200,500,500,1.5),
                     (1200,40,50,1.5),(1200,500,0,1.5),
                     (1200,500,40,math.inf),(1200,500,40,True),
                     (1200,500,40,math.nan),('1200',500,40,1.5)):
            with self.subTest(args=args),self.assertRaises(ValueError):
                resolver_tobera_convergente_divergente(*args)

    def test_enteros_enormes_rechazados_con_valueerror(self):
        base = [1200,500,40,1.5]
        for indice in range(4):
            args=base.copy()
            args[indice]=10**10000
            with self.subTest(indice=indice),self.assertRaises(ValueError):
                resolver_tobera_convergente_divergente(*args)
        for indice in range(3):
            args=[1200,500,40]
            args[indice]=10**10000
            with self.subTest(inverso_indice=indice),self.assertRaises(ValueError):
                relacion_areas_adaptada(*args)

    def test_dominio_termico_extremo(self):
        with self.assertRaises(EstadoFueraDeRango):
            resolver_tobera_convergente_divergente(1200,500,.001,2.)
        with self.assertRaises(EstadoFueraDeRango):
            relacion_areas_adaptada(1200,500,.001)

    def test_sin_estado_critico_en_dominio(self):
        r=resolver_tobera_convergente_divergente(230,105,104,1.05)
        self.assertTrue(r['resuelto'])
        self.assertIsNone(r['presion_critica'])
        self.assertLess(r['mach_garganta'],1)


if __name__=='__main__':
    unittest.main()
