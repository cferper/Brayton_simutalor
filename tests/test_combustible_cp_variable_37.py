"""Milestone 37: balances, integraciones, dominios y límites matemáticos."""

import math
import unittest

from combustible_cp_variable import resolver_turborreactor_con_combustible as resolver
from propiedades_aire import h, s
from vuelo_cp_variable import resolver_turborreactor_vuelo


BASE = dict(rp=10, eta_c=.85, T3=1600, delta=.04, eta_t=.9,
            eta_m=.98, eta_n=.95, eta_b=.99, PCI=43000)
ESTATICO = dict(mach=0, pi_d=1, T_amb=288.15, p_amb=100)
VUELO = dict(mach=.7, pi_d=.97, T_amb=288.15, p_amb=100)


def caso(**cambios):
    args = dict(BASE, **ESTATICO)
    args.update(cambios)
    return resolver(**args)


class CombustibleCP37(unittest.TestCase):
    def test_balance_energetico_combustor_independiente(self):
        c = caso()["combustor"]
        self.assertAlmostEqual(c["h2"] + c["f"]*c["eta_b"]*c["PCI"],
                               (1+c["f"])*c["h3"], places=8)
        self.assertAlmostEqual(c["residuo_energia"], 0, places=8)

    def test_f_positivo_finito(self):
        c = caso()["combustor"]
        self.assertGreater(c["f"], 0)
        self.assertTrue(math.isfinite(c["f"]))
        self.assertEqual(c["factor_masico"], 1+c["f"])

    def test_pci_superior_reduce_f(self):
        self.assertLess(caso(PCI=46000)["combustor"]["f"],
                        caso(PCI=40000)["combustor"]["f"])

    def test_eta_b_inferior_aumenta_f(self):
        self.assertGreater(caso(eta_b=.8)["combustor"]["f"],
                           caso(eta_b=1)["combustor"]["f"])

    def test_balance_eje_con_aumento_de_masa(self):
        o = caso()
        c, b, t = o["compresor"], o["combustor"], o["turbina"]
        self.assertAlmostEqual(.98*b["factor_masico"]*(b["h3"]-t["h4"]),
                               c["trabajo_compresor"], places=7)
        self.assertAlmostEqual(t["residuo_eje"], 0, places=7)

    def test_rendimiento_isentropico_turbina(self):
        o = caso()
        t, c = o["turbina"], o["combustor"]
        self.assertAlmostEqual((c["h3"]-t["h4"])/(c["h3"]-t["h4s"]),
                               BASE["eta_t"], places=9)

    def test_entropia_turbina_isentropica(self):
        o = caso()
        t, b = o["turbina"], o["combustor"]
        self.assertAlmostEqual(s(t["T4s"], t["p4"]), s(b["T3"], b["p3"]), places=9)

    def test_integracion_tobera_y_energia(self):
        o = caso()
        t, n = o["turbina"], o["tobera"]
        self.assertEqual(n["temperatura_remanso"], t["T4"])
        self.assertEqual(n["presion_remanso"], t["p4"])
        self.assertAlmostEqual(2000*(h(t["T4"])-h(n["temperatura_salida"])),
                               n["velocidad_salida"]**2, places=6)

    def test_empuje_salida_y_presion_multiplicados(self):
        o = caso()
        f, n, p = o["combustor"]["f"], o["tobera"], o["prestaciones"]
        self.assertAlmostEqual(p["empuje_especifico_salida"], (1+f)*n["velocidad_salida"])
        esperado = (1+f)*1000*(n["presion_salida"]-o["ambiente"]["presion"])/(
            n["densidad_salida"]*n["velocidad_salida"])
        self.assertAlmostEqual(p["empuje_especifico_presion"], esperado)

    def test_tsfc_unidades(self):
        o = caso()
        f, p = o["combustor"]["f"], o["prestaciones"]
        self.assertAlmostEqual(p["TSFC_kg_N_s"], f/p["empuje_especifico_neto"])
        self.assertAlmostEqual(p["TSFC_kg_N_h"], p["TSFC_kg_N_s"]*3600)

    def test_vuelo_y_altitud(self):
        v = resolver(**dict(BASE, **VUELO))
        altura = resolver(**dict(BASE, mach=.5, pi_d=.98, altitud_geopotencial=10000))
        self.assertGreater(v["prestaciones"]["resistencia_entrada"], 0)
        self.assertAlmostEqual(v["prestaciones"]["empuje_especifico_neto"],
                               v["prestaciones"]["empuje_especifico_bruto"]-
                               v["remanso"]["velocidad_vuelo"])
        self.assertAlmostEqual(altura["ambiente"]["temperatura"], 223.15)
        self.assertGreater(altura["prestaciones"]["TSFC_kg_N_h"], 0)

    def test_parametros_invalidos(self):
        for modificacion in (dict(eta_b=0), dict(eta_b=1.1), dict(PCI=0),
                             dict(PCI=float("nan")), dict(PCI=1000),
                             dict(T3=300), dict(T3=2001), dict(eta_n=False),
                             dict(rp=1), dict(mach=1), dict(pi_d=0)):
            with self.subTest(modificacion=modificacion):
                with self.assertRaises((ValueError, ArithmeticError)):
                    caso(**modificacion)

    def test_limite_f_a_cero_vs_modelo_anterior(self):
        # PCI artificialmente grande: prueba matemática, no combustible real.
        nuevo = caso(PCI=1e12)
        anterior = resolver_turborreactor_vuelo(
            0, 10, .85, 1600, .04, .9, .98, eta_n=.95,
            pi_d=1, T_amb=288.15, p_amb=100)
        self.assertLess(nuevo["combustor"]["f"], 1e-8)
        self.assertAlmostEqual(nuevo["turbina"]["T4"],
                               anterior["nucleo"]["temperaturas"][3], places=5)
        self.assertAlmostEqual(nuevo["turbina"]["p4"],
                               anterior["nucleo"]["presiones"][3], places=4)
        self.assertAlmostEqual(nuevo["prestaciones"]["empuje_especifico_neto"],
                               anterior["empuje_especifico_neto"], places=4)

    def test_referencia_analitica_gas_caloricamente_perfecto(self):
        # Compara orden de magnitud con T2 ideal de gas perfecto gamma=1,4,
        # cp=1,0045 kJ/(kg K); NO igualdad exacta para cp(T).
        o = caso(eta_c=1)
        t2_aprox = 288.15*10**(.4/1.4)
        self.assertLess(abs(o["compresor"]["T2"]-t2_aprox)/t2_aprox, .025)
        h2_aprox = 1.0045*(t2_aprox-298.15)
        h3_aprox = 1.0045*(1600-298.15)
        f_aprox = (h3_aprox-h2_aprox)/(.99*43000-h3_aprox)
        self.assertLess(abs(o["combustor"]["f"]-f_aprox)/f_aprox, .2)

    def test_no_modifica_simuladores_antiguos(self):
        antes = resolver_turborreactor_vuelo(
            0, 10, .85, 1600, .04, .9, .98, eta_n=.95,
            pi_d=1, T_amb=288.15, p_amb=100)
        caso()
        despues = resolver_turborreactor_vuelo(
            0, 10, .85, 1600, .04, .9, .98, eta_n=.95,
            pi_d=1, T_amb=288.15, p_amb=100)
        self.assertEqual(antes, despues)


if __name__ == "__main__":
    unittest.main()
