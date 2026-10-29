"""Verificación focalizada de caudal en geometría fija, milestone 47.1."""

import math
import unittest

from caudal_tobera_geometria_fija import (caudal_desde_estado_tobera,
                                          resolver_caudal_tobera_fija)
from propiedades_aire import R_AIRE
from tobera_convergente_divergente_cp import resolver_tobera_convergente_divergente
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor


class CaudalFijo47(unittest.TestCase):
    def cd(self, presion, ag=0.01):
        return resolver_caudal_tobera_fija(1200, 500, presion, ag,
            area_salida=1.5*ag, tipo_tobera="convergente_divergente")

    def test_referencia_analitica_caloricamente_perfecta_bloqueo(self):
        # Referencia independiente gas perfecto (aproximada por cp(T), no igualdad).
        gamma = 1.33
        R = R_AIRE
        G_referencia = 500000 * math.sqrt(gamma/(R*1200)) * (
            2/(gamma+1))**((gamma+1)/(2*(gamma-1)))
        r = self.cd(50)
        self.assertTrue(r["garganta_bloqueada"])
        self.assertLess(abs(r["gasto_masico_gases"]/.01-G_referencia)/G_referencia, .04)

    def test_subsonico_no_bloqueado_y_transicion(self):
        sub = self.cd(490)
        crit = self.cd(350)
        self.assertEqual(sub["regimen"], "subsonico_no_bloqueado")
        self.assertFalse(sub["garganta_bloqueada"])
        self.assertLess(sub["gasto_masico_gases"], crit["gasto_masico_gases"])
        self.assertTrue(crit["garganta_bloqueada"])
        self.assertLess(sub["mach_salida"], 1)
        self.assertAlmostEqual(sub["presion_salida"], 490, places=4)

    def test_continuidad_y_escalado_lineal(self):
        for p in (50, 350, 490):
            with self.subTest(p=p):
                r = self.cd(p)
                self.assertLess(abs(r["residuo_continuidad"]), 2e-6*r["gasto_masico_gases"])
                doble = self.cd(p, .02)
                self.assertAlmostEqual(doble["gasto_masico_gases"], 2*r["gasto_masico_gases"], places=9)

    def test_choque_normal_interno_y_salida(self):
        choque = resolver_tobera_convergente_divergente(1200,500,350,1.5)
        self.assertEqual(choque["regimen"], "choque_normal_interno")
        r = self.cd(350)
        self.assertAlmostEqual(r["gasto_masico_gases"],
                               choque["flujo_masico_por_area_garganta"]*.01)
        p_salida = choque["umbral_choque_salida_aproximado"]
        s = self.cd(p_salida)
        self.assertTrue(s["disponible"])
        self.assertTrue(s["garganta_bloqueada"])

    def test_convergente_bloqueada_y_no_bloqueada(self):
        bloqueada = resolver_caudal_tobera_fija(1200,500,100,.01,eta_n=.95)
        abierta = resolver_caudal_tobera_fija(1200,500,490,.01,eta_n=.95)
        self.assertTrue(bloqueada["garganta_bloqueada"])
        self.assertFalse(abierta["garganta_bloqueada"])
        self.assertLess(abierta["gasto_masico_gases"],bloqueada["gasto_masico_gases"])

    def test_dosado_separa_aire_gas_y_combustible(self):
        n = resolver_tobera_convergente_divergente(1200,500,350,1.5)
        r = caudal_desde_estado_tobera(n,"convergente_divergente",.01,.015,dosado=.025)
        self.assertAlmostEqual(r["gasto_masico_gases"],
                               r["gasto_masico_aire"]+r["gasto_masico_combustible"])
        self.assertAlmostEqual(r["gasto_masico_combustible"],.025*r["gasto_masico_aire"])

    def test_geometrias_invalidas_y_sin_solucion(self):
        for ag, ae in ((0,.015),(-1,.015),(float('nan'),.015),(.01,.009)):
            with self.subTest(ag=ag,ae=ae),self.assertRaises(ValueError):
                resolver_caudal_tobera_fija(1200,500,350,ag,area_salida=ae,
                                           tipo_tobera="convergente_divergente")
        r = caudal_desde_estado_tobera(None,"convergente",.01,.01)
        self.assertFalse(r["disponible"])
        self.assertIsNone(r["gasto_masico_gases"])

    def test_compatibilidad_web_modo_impuesto_y_fijo(self):
        valores = dict(DEFAULTS_TURBO)
        valores["gasto_masico_aire"] = "20"
        antiguo = simular_turborreactor(valores)
        self.assertAlmostEqual(antiguo["prestaciones_absolutas"]["gasto_masico_aire"],20)
        area = antiguo["dimensionamiento_tobera"]["area_garganta"]
        valores.update(modo_caudal="fijo", gasto_masico_aire="",
                       area_garganta_fija=str(area))
        nuevo = simular_turborreactor(valores)
        self.assertAlmostEqual(nuevo["prestaciones_absolutas"]["gasto_masico_aire"],20,places=7)
        self.assertAlmostEqual(nuevo["prestaciones_absolutas"]["empuje_neto"],
                               antiguo["prestaciones_absolutas"]["empuje_neto"],places=6)
        self.assertEqual(nuevo["modo_caudal"],"fijo")
        valores["gasto_masico_aire"]="30"
        with self.assertRaisesRegex(ValueError,"resultado"):
            simular_turborreactor(valores)

    def test_web_cd_modo_fijo(self):
        # Caso estático M37/M42 con margen, expansión C-D resuelta y empuje positivo.
        valores = dict(DEFAULTS_TURBO)
        valores.update(tipo_tobera="convergente_divergente",modo_caudal="fijo",
                       area_garganta_fija="0.01",area_salida_fija="0.015")
        r = simular_turborreactor(valores)
        self.assertEqual(r["modo_caudal"], "fijo")
        self.assertTrue(r["caudal_geometria_fija"]["disponible"])
        self.assertTrue(r["dimensionamiento_tobera"]["disponible"])
        self.assertAlmostEqual(r["dimensionamiento_tobera"]["area_garganta"],.01,places=7)
        self.assertAlmostEqual(r["dimensionamiento_tobera"]["area_salida"],.015,places=7)
        c = r["caudal_geometria_fija"]
        a = r["prestaciones_absolutas"]
        self.assertGreater(c["gasto_masico_gases"],c["gasto_masico_aire"])
        self.assertAlmostEqual(a["gasto_masico_aire"]+a["gasto_masico_combustible"],a["gasto_masico_gases"])
        self.assertAlmostEqual(a["gasto_masico_gases"],c["gasto_masico_gases"])
        self.assertGreater(a["empuje_neto"],0)


if __name__ == "__main__":
    unittest.main()
