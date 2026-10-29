"""Acoplamiento estacionario: incógnitas, convergencia y límites de mapas."""

import unittest

from acoplamiento_motor_mapa_47 import punto_diseno_47, resolver_motor_acoplado
from propiedades_aire import h
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor, preparar_vista_turborreactor


class Acoplamiento47(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref=punto_diseno_47()

    def test_diseno_potencia_masa_presion(self):
        r=resolver_motor_acoplado(referencia=self.ref)
        self.assertTrue(r["disponible"])
        self.assertEqual(r["iteraciones"],0)
        self.assertAlmostEqual(r["rpm"],20000)
        self.assertAlmostEqual(r["caudal_aire"],20)
        self.assertAlmostEqual(r["compresor_mapa"]["rp"],10)
        self.assertAlmostEqual(r["turbina_mapa"]["eta"],.9)
        self.assertLess(abs(r["residuo_masa_turbina"]),1e-8)
        self.assertLess(abs(r["residuo_masa_tobera"]),1e-8)
        self.assertLess(abs(r["residuo_potencia"]),1e-5)

    def test_vuelo_y_ambiente(self):
        base=resolver_motor_acoplado(referencia=self.ref)
        vuelo=resolver_motor_acoplado(referencia=self.ref,mach=.4)
        bajo=resolver_motor_acoplado(referencia=self.ref,p_amb=95)
        for r in (base,vuelo,bajo):
            self.assertTrue(r["disponible"])
            self.assertLess(r["norma_residual"],2e-7)
            self.assertGreater(r["empuje_absoluto"],0)
        self.assertNotAlmostEqual(vuelo["rpm"],base["rpm"])
        self.assertAlmostEqual(bajo["caudal_aire"],19,places=6)

    def test_temperatura_rpm_diferentes_y_balance(self):
        r=resolver_motor_acoplado(referencia=self.ref,T3=1550)
        self.assertTrue(r["disponible"])
        self.assertNotAlmostEqual(r["rpm"],self.ref["rpm_mecanicas"])
        self.assertAlmostEqual(r["compresor"]["h2"]-r["compresor"]["h1"],
                               r["compresor"]["trabajo_compresor"])
        b=r["combustor"]
        self.assertAlmostEqual(b["h2"]+b["f"]*b["eta_b"]*b["PCI"],
                               (1+b["f"])*b["h3"],places=8)
        self.assertAlmostEqual(r["caudal_gases"],r["caudal_aire"]+r["caudal_combustible"])
        self.assertAlmostEqual(r["turbina"]["h3"] if "h3" in r["turbina"] else b["h3"],h(b["T3"]))

    def test_geometria_fija_afecta_punto(self):
        corto=resolver_motor_acoplado(referencia=self.ref,
                    area_garganta=.95*self.ref["area_garganta_diseno"])
        self.assertTrue(corto["disponible"])
        self.assertNotAlmostEqual(corto["caudal_aire"],20)

    def test_rechazo_de_fuera_de_mapa_sin_inventar(self):
        fuera=resolver_motor_acoplado(referencia=self.ref,
                    area_garganta=1.10*self.ref["area_garganta_diseno"])
        self.assertFalse(fuera["disponible"])
        self.assertNotIn("empuje_absoluto",fuera)
        with self.assertRaises(ValueError):
            resolver_motor_acoplado(area_garganta=-1,referencia=self.ref)

    def test_reproducibilidad_y_limite_numerico(self):
        primero=resolver_motor_acoplado(referencia=self.ref,mach=.1)
        segundo=resolver_motor_acoplado(referencia=self.ref,mach=.1)
        self.assertTrue(primero["disponible"])
        self.assertEqual(primero["rpm"],segundo["rpm"])
        self.assertEqual(primero["historico_normas"],segundo["historico_normas"])
        agotado=resolver_motor_acoplado(referencia=self.ref,mach=.4,max_iteraciones=1)
        self.assertFalse(agotado["disponible"])

    def test_integracion_web_tres_modalidades(self):
        entrada=dict(DEFAULTS_TURBO)
        entrada["gasto_masico_aire"]="20"
        impuesto=simular_turborreactor(entrada)
        self.assertAlmostEqual(impuesto["prestaciones_absolutas"]["gasto_masico_aire"],20)
        entrada.update(modo_caudal="fijo",gasto_masico_aire="",
                       area_garganta_fija=str(self.ref["area_garganta_diseno"]))
        fijo=simular_turborreactor(entrada)
        self.assertAlmostEqual(fijo["prestaciones_absolutas"]["gasto_masico_aire"],20,places=5)
        entrada.update(modo_caudal="acoplado")
        acoplado=simular_turborreactor(entrada)
        self.assertAlmostEqual(acoplado["motor_acoplado"]["rpm"],20000)
        self.assertAlmostEqual(acoplado["prestaciones_absolutas"]["gasto_masico_aire"],20)
        self.assertAlmostEqual(acoplado["dimensionamiento_tobera"]["area_garganta"],
                               self.ref["area_garganta_diseno"],places=9)
        self.assertTrue(preparar_vista_turborreactor(acoplado)["svg_empuje"])

    def test_admision_modo_acoplado_consistencia(self):
        entrada=dict(DEFAULTS_TURBO,modo_caudal="acoplado",mach_entrada_compresor="0.2")
        estimado=simular_turborreactor(entrada)
        area=estimado["estudio_admision"]["area_entrada_compresor_requerida"]
        entrada["area_entrada_compresor"]=str(area)
        coherente=simular_turborreactor(entrada)
        self.assertEqual(coherente["estudio_admision"]["estado"],"continuidad_compatible")
        entrada["area_entrada_compresor"]=str(area*1.2)
        with self.assertRaisesRegex(ValueError,"no admiten el caudal"):
            simular_turborreactor(entrada)

    def test_web_no_permite_imponer_caudal_en_modo_acoplado(self):
        entrada=dict(DEFAULTS_TURBO,modo_caudal="acoplado",gasto_masico_aire="21")
        with self.assertRaisesRegex(ValueError,"caudal es resultado"):
            simular_turborreactor(entrada)

    def test_web_cd_geometria_compatible(self):
        ag=self.ref["area_garganta_diseno"]
        r=simular_turborreactor(dict(DEFAULTS_TURBO,modo_caudal="acoplado",
                  tipo_tobera="convergente_divergente",
                  area_garganta_fija=str(ag),area_salida_fija=str(1.2*ag)))
        self.assertTrue(r["motor_acoplado"]["disponible"])
        self.assertAlmostEqual(r["dimensionamiento_tobera"]["area_garganta"],ag,places=8)
        self.assertAlmostEqual(r["dimensionamiento_tobera"]["area_salida"],1.2*ag,places=8)
        self.assertGreater(r["prestaciones_absolutas"]["empuje_neto"],0)


if __name__=="__main__":
    unittest.main()
