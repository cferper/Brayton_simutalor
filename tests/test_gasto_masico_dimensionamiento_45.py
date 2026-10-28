"""Contratos de caudales, fuerzas y áreas del milestone 45."""

from math import sqrt
from pathlib import Path
import unittest
from xml.etree import ElementTree

from combustible_cp_variable import resolver_turborreactor_con_combustible
from dimensionamiento_turborreactor import (
    calcular_prestaciones_absolutas, dimensionar_tobera,
    validar_gasto_masico_aire,
)
from tobera_convergente_divergente_cp import resolver_tobera_convergente_divergente
from turborreactor_web import (DEFAULTS_TURBO, preparar_vista_turborreactor,
                              simular_turborreactor)


class MagnitudesAbsolutas45(unittest.TestCase):
    @staticmethod
    def _motor(**cambios):
        parametros = dict(T_amb=288.15, p_amb=100, mach=0., rp=10,
                          eta_c=.85, T3=1600, delta=.04, eta_t=.9,
                          eta_m=.98, eta_n=.95, **cambios)
        return resolver_turborreactor_con_combustible(**parametros)

    @staticmethod
    def _tobera_cd(p):
        """Sustituye solo la tobera por otra solución científica independiente.

        Así se comprueba el dimensionamiento de los regímenes de choque
        sin inventar estados ni alterar ecuaciones del solucionador.
        """
        n = resolver_tobera_convergente_divergente(1200,500,p,1.5)
        resultado = MagnitudesAbsolutas45._motor()
        f = resultado["combustor"]["f"]
        salida = (1+f)*n["empuje_especifico_momento"]
        presion = (1+f)*n["empuje_especifico_presion"]
        neto = salida+presion
        resultado["diagnosticos"] = {"tipo_tobera":"convergente_divergente"}
        resultado["tobera"] = n
        resultado["ambiente"]["presion"] = p
        resultado["prestaciones"] = dict(
            empuje_especifico_salida=salida, empuje_especifico_presion=presion,
            resistencia_entrada=0.0, empuje_especifico_neto=neto,
            TSFC_kg_N_h=3600*f/neto if neto>0 else None)
        return resultado

    def test_caso_base_empuje_y_combustible(self):
        r = self._motor()
        a = calcular_prestaciones_absolutas(r,20)
        self.assertAlmostEqual(a["gasto_masico_combustible"],
                               20*r["combustor"]["f"])
        self.assertAlmostEqual(a["gasto_masico_gases"],
                               20*(1+r["combustor"]["f"]))
        self.assertAlmostEqual(a["consumo_combustible_hora"],
                               3600*a["gasto_masico_combustible"])
        self.assertAlmostEqual(a["empuje_neto"],
                               20*r["prestaciones"]["empuje_especifico_neto"])
        self.assertAlmostEqual(a["empuje_neto_kN"],a["empuje_neto"]/1000)

    def test_empuje_firmado_y_cierre_descomposicion(self):
        a = calcular_prestaciones_absolutas(self._motor(),20)
        self.assertAlmostEqual(a["empuje_momento_salida"]+a["resistencia_entrada"]+
                               a["empuje_presion"],a["empuje_neto"])
        self.assertAlmostEqual(a["residuo_empuje"],0,places=6)

    def test_tsfc_identico_al_especifico(self):
        r = self._motor()
        a = calcular_prestaciones_absolutas(r,20)
        self.assertAlmostEqual(a["TSFC_kg_N_h"],r["prestaciones"]["TSFC_kg_N_h"])
        self.assertAlmostEqual(a["TSFC_kg_N_h"],
                               a["consumo_combustible_hora"]/a["empuje_neto"])

    def test_caudal_cambia_extensivos_no_especificos(self):
        r = self._motor()
        inicial = (r["compresor"].copy(),r["combustor"].copy(),
                   r["prestaciones"].copy())
        a = calcular_prestaciones_absolutas(r,20)
        b = calcular_prestaciones_absolutas(r,40)
        for clave in ("gasto_masico_combustible", "gasto_masico_gases",
                      "consumo_combustible_hora", "empuje_momento_salida",
                      "resistencia_entrada", "empuje_presion", "empuje_neto"):
            self.assertAlmostEqual(b[clave],2*a[clave])
        self.assertEqual(a["TSFC_kg_N_h"],b["TSFC_kg_N_h"])
        self.assertEqual((r["compresor"],r["combustor"],r["prestaciones"]),inicial)

    def test_gasto_invalido(self):
        for valor in (0,-2,float("inf"),float("nan"),True,"20",None):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                validar_gasto_masico_aire(valor)

    def test_sin_tobera_hay_combustible_pero_no_empuje(self):
        r = resolver_turborreactor_con_combustible(
            T_amb=288.15,p_amb=100,mach=.9,rp=3,eta_c=.85,
            T3=500,delta=.04,eta_t=.9,eta_m=.98,eta_n=.95,pi_d=.7)
        a = calcular_prestaciones_absolutas(r,20)
        self.assertIsNone(a["empuje_neto"])
        self.assertIsNone(a["TSFC_kg_N_h"])
        self.assertGreater(a["gasto_masico_combustible"],0)
        self.assertFalse(dimensionar_tobera(r,20)["disponible"])

    def test_empuje_negativo_no_se_trunca(self):
        r = resolver_turborreactor_con_combustible(
            T_amb=288.15,p_amb=100,mach=.9,rp=3,eta_c=.85,
            T3=600,delta=.04,eta_t=.9,eta_m=.98,eta_n=.95,pi_d=.7)
        a = calcular_prestaciones_absolutas(r,20)
        self.assertLess(a["empuje_neto"],0)
        self.assertIsNone(a["TSFC_kg_N_h"])
        self.assertTrue(dimensionar_tobera(r,20)["disponible"])

    def test_dimensionamiento_convergente_bloqueada(self):
        r = self._motor()
        a = calcular_prestaciones_absolutas(r,20)
        d = dimensionar_tobera(r,20,absolutos=a)
        self.assertTrue(d["disponible"])
        self.assertTrue(d["garganta_bloqueada"])
        self.assertEqual(d["area_garganta"],d["area_salida"])
        self.assertAlmostEqual(d["relacion_areas"],1)
        self.assertAlmostEqual(d["residuo_empuje_dimensional"],0,places=7)

    def test_dimensionamiento_cd_supersonico(self):
        r = self._motor(tipo_tobera="convergente_divergente",epsilon=1.5)
        d = dimensionar_tobera(r,20)
        self.assertAlmostEqual(d["area_salida"]/d["area_garganta"],1.5,places=6)
        self.assertTrue(d["garganta_bloqueada"])
        self.assertAlmostEqual(d["residuo_empuje_dimensional"],0,places=6)

    def test_regimenes_cd_subsonico_choque_interno_y_salida(self):
        n_ref=resolver_tobera_convergente_divergente(1200,500,350,1.5)
        umbral=n_ref["umbral_choque_salida_aproximado"]
        for p, nombre in ((490,"subsonico_no_bloqueado"),
                          (350,"choque_normal_interno"),
                          (umbral,"choque_normal_salida")):
            with self.subTest(p=p):
                r = self._tobera_cd(p)
                self.assertEqual(r["tobera"]["regimen"],nombre)
                d = dimensionar_tobera(r,20)
                self.assertTrue(d["disponible"])
                self.assertAlmostEqual(d["relacion_areas"],1.5,places=6)
                self.assertAlmostEqual(d["residuo_empuje_dimensional"],0,places=5)
                self.assertEqual(d["garganta_bloqueada"],p!=490)

    def test_dimensionamiento_convergente_no_bloqueada(self):
        r = resolver_turborreactor_con_combustible(
            T_amb=288.15,p_amb=100,mach=.9,rp=3,eta_c=.85,
            T3=600,delta=.04,eta_t=.9,eta_m=.98,eta_n=.95,pi_d=.7)
        d=dimensionar_tobera(r,20)
        self.assertTrue(d["disponible"])
        self.assertFalse(d["garganta_bloqueada"])
        self.assertAlmostEqual(d["area_garganta"],d["area_salida"])

    def test_escalado_area_y_diametro(self):
        r = self._motor(tipo_tobera="convergente_divergente",epsilon=1.5)
        a,b=dimensionar_tobera(r,20),dimensionar_tobera(r,40)
        for k in ("garganta","salida"):
            self.assertAlmostEqual(b["area_"+k],2*a["area_"+k])
            self.assertAlmostEqual(b["diametro_"+k],sqrt(2)*a["diametro_"+k])

    def test_conservacion_masa_y_relacion_en_distintos_gastos(self):
        r = self._motor(tipo_tobera="convergente_divergente",epsilon=1.8)
        for gasto in (1,20,100):
            with self.subTest(gasto=gasto):
                d=dimensionar_tobera(r,gasto)
                self.assertAlmostEqual(d["residuo_masa_salida"],0,places=7)
                self.assertAlmostEqual(d["residuo_masa_garganta"],0,places=7)
                self.assertAlmostEqual(d["residuo_relacion_areas"],0,places=6)

    def test_web_caudal_vacio_conserva_resultados_anteriores(self):
        nuevo = simular_turborreactor(DEFAULTS_TURBO)
        antiguo = resolver_turborreactor_con_combustible(
            T_amb=288.15,p_amb=100,mach=0,rp=10,eta_c=.85,T3=1600,
            delta=.04,eta_t=.9,eta_m=.98,eta_n=.95,pi_d=1,
            eta_b=.99,PCI=43000,tipo_tobera="convergente")
        self.assertEqual(nuevo,antiguo)
        self.assertNotIn("prestaciones_absolutas",nuevo)

    def test_web_opcional_agrega_sin_alterar_salida_especifica(self):
        base = simular_turborreactor(DEFAULTS_TURBO)
        con_caudal = simular_turborreactor({**DEFAULTS_TURBO,"gasto_masico_aire":"20"})
        for clave in base:
            self.assertEqual(con_caudal[clave],base[clave])
        self.assertAlmostEqual(con_caudal["prestaciones_absolutas"]["empuje_neto"],
                               20*base["prestaciones"]["empuje_especifico_neto"])
        self.assertTrue(con_caudal["dimensionamiento_tobera"]["disponible"])

    def test_web_valida_masa_y_conserva_mensaje(self):
        for valor in ("0","-3","nan","inf","20a"):
            with self.subTest(valor=valor),self.assertRaisesRegex(ValueError,"Gasto másico"):
                simular_turborreactor({**DEFAULTS_TURBO,"gasto_masico_aire":valor})

        self.assertNotIn("prestaciones_absolutas",simular_turborreactor(
            {**DEFAULTS_TURBO,"gasto_masico_aire":"   "}))

    def test_web_salida_no_resuelta_no_crea_empuje_absoluto(self):
        r=simular_turborreactor({**DEFAULTS_TURBO,"gasto_masico_aire":"20",
                                "mach":"0.9","rp":"3","pi_d":"0.7","T3":"500"})
        self.assertIsNone(r["prestaciones_absolutas"]["empuje_neto"])
        self.assertFalse(r["dimensionamiento_tobera"]["disponible"])
        self.assertIsNone(preparar_vista_turborreactor(r)["svg_empuje_absoluto"])

    def test_svg_empuje_absoluto_y_especifico_no_se_confunden(self):
        r=simular_turborreactor({**DEFAULTS_TURBO,"gasto_masico_aire":"20"})
        vista=preparar_vista_turborreactor(r)
        a,b=vista["svg_empuje_absoluto"],vista["svg_empuje"]
        ElementTree.fromstring(a)
        ElementTree.fromstring(b)
        self.assertIn("neto [N]",a)
        self.assertIn("N/(kg/s de aire)",b)
        self.assertNotEqual(a,b)

    def test_template_y_formulario_etapas_45(self):
        html=(Path(__file__).resolve().parents[1]/"templates"/"turborreactor.html").read_text(encoding="utf8")
        self.assertIn("Prestaciones absolutas del motor",html)
        self.assertIn("Dimensionamiento de la tobera",html)
        self.assertIn("vista.svg_empuje_absoluto|safe",html)
        self.assertIn("gasto_masico_aire",DEFAULTS_TURBO)


if __name__ == "__main__":
    unittest.main()
