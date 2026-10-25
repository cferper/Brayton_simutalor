"""Verificación del acoplamiento monoeje: no es validación experimental."""
import math
import unittest

from acoplamiento_turbomaquinaria_cp import resolver_acoplamiento
from ciclo_cp_variable import EstadoFueraDeRango
from propiedades_aire import R_AIRE, h, s, s0


BASE = (288.15, 100.0, 10.0, 0.85, 1600.0, 0.04, 0.9, 0.98)


class PruebasAcoplamiento(unittest.TestCase):
    def resolver(self, **cambios):
        claves = ('T_amb', 'p_amb', 'rp', 'eta_c', 'T3', 'delta', 'eta_t', 'eta_m')
        datos = dict(zip(claves, BASE))
        datos.update(cambios)
        return resolver_acoplamiento(**datos)

    def test_cierre_eje_y_energias(self):
        r = self.resolver()
        self.assertAlmostEqual(r['rendimiento_mecanico'] * r['trabajo_turbina'],
                               r['trabajo_compresor'], places=8)
        self.assertAlmostEqual(r['residuo_eje'], 0, places=8)
        H = r['entalpias']
        self.assertAlmostEqual(r['trabajo_compresor'], H[1]-H[0], places=8)
        self.assertAlmostEqual(r['trabajo_turbina'], H[2]-H[3], places=8)
        self.assertAlmostEqual(r['calor_aportado'], H[2]-H[1], places=8)

    def test_ideal_y_potencia_cero(self):
        r = self.resolver(eta_c=1, eta_t=1, eta_m=1, delta=0)
        self.assertAlmostEqual(r['T2s'], r['temperaturas'][1], places=8)
        self.assertAlmostEqual(r['T4s'], r['temperaturas'][3], places=8)
        self.assertAlmostEqual(r['trabajo_turbina'], r['trabajo_compresor'], places=8)
        self.assertAlmostEqual(r['entropias'][1], r['entropias'][0], places=9)
        self.assertAlmostEqual(r['entropias'][3], r['entropias'][2], places=9)

    def test_eficiencia_mecanica(self):
        a, b = self.resolver(eta_m=1), self.resolver(eta_m=.9)
        self.assertAlmostEqual(a['trabajo_compresor'], b['trabajo_compresor'], places=9)
        self.assertGreater(b['trabajo_turbina'], a['trabajo_turbina'])
        self.assertLess(b['presiones'][3], a['presiones'][3])

    def test_eficiencia_turbina(self):
        a, b = self.resolver(eta_t=1), self.resolver(eta_t=.8)
        self.assertAlmostEqual(a['temperaturas'][3], b['temperaturas'][3], places=9)
        self.assertLess(b['T4s'], a['T4s'])
        self.assertLess(b['presiones'][3], a['presiones'][3])

    def test_presiones_entropia_y_margen(self):
        r = self.resolver()
        self.assertTrue(all(math.isfinite(p) and p > 0 for p in r['presiones']))
        self.assertLess(r['presiones'][3], r['presiones'][2])
        self.assertAlmostEqual(s(r['T4s'], r['presiones'][3]),
                               s(r['temperaturas'][2], r['presiones'][2]), places=9)
        self.assertAlmostEqual(r['relacion_salida_ambiente'],
                               r['presiones'][3] / r['presiones'][0], places=12)
        self.assertIn(r['diagnostico_tobera'], ('con_margen', 'sin_margen', 'limite'))

    def test_presion_analitica_gas_ideal(self):
        # Identidad independiente de la inversión logarítmica del solucionador.
        r = self.resolver()
        esperado = r['presiones'][2] * math.exp(
            (s0(r['T4s']) - s0(r['temperaturas'][2])) / (R_AIRE/1000))
        self.assertAlmostEqual(r['presiones'][3], esperado, places=9)

    def test_referencia_calorico_constante(self):
        # En el límite cp constante la compresión ideal cumple T2s/T1=rp^((gamma-1)/gamma).
        # cp(T) real no coincide exactamente: comparar con tolerancia física holgada.
        r = self.resolver(rp=2, eta_c=1)
        aproximacion = BASE[0] * 2**((1.4-1)/1.4)
        self.assertLess(abs(r['T2s']-aproximacion)/aproximacion, .03)

    def test_dominio_e_imposibles(self):
        for cambio in ({'eta_m': 0}, {'eta_t': 1.1}, {'eta_c': True},
                       {'rp': 1}, {'delta': 1}, {'p_amb': 0},
                       {'T_amb': 199}, {'T3': float('nan')}, {'T3': 320}):
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                self.resolver(**cambio)
        with self.assertRaises(EstadoFueraDeRango):
            self.resolver(eta_m=.1)

    def test_diagnosticos_ambos_lados(self):
        con = self.resolver(rp=3, T3=1800, eta_c=1, eta_t=1, eta_m=1, delta=0)
        sin = self.resolver(rp=15, T3=900, eta_c=.85, eta_t=.85, eta_m=.9)
        self.assertEqual(con['diagnostico_tobera'], 'con_margen')
        self.assertEqual(sin['diagnostico_tobera'], 'sin_margen')


if __name__ == '__main__':
    unittest.main()
