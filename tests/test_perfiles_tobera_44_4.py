"""Verificación física del perfil cuasi-1D del milestone 44.4."""

from pathlib import Path
import unittest
from xml.etree import ElementTree

from perfil_tobera_cp_variable import perfil_tobera_cp_variable
from propiedades_aire import h, s
from tobera_convergente_divergente_cp import resolver_tobera_convergente_divergente
from turborreactor_web import (
    DEFAULTS_TURBO, preparar_vista_turborreactor, simular_turborreactor,
    svg_perfil_tobera,
)


class PerfilesTobera44_4(unittest.TestCase):
    @staticmethod
    def _caso(p=50.0, *, epsilon=1.5, puntos=41, Tt=1200.0, pt=500.0):
        n = resolver_tobera_convergente_divergente(Tt, pt, p, epsilon)
        resultado = {"tobera": n,
                     "diagnosticos": {"tipo_tobera": "convergente_divergente"}}
        return n, perfil_tobera_cp_variable(resultado, puntos_por_region=puntos)

    @staticmethod
    def _todos(datos):
        return [p for region in datos["segmentos"] for p in region]

    def test_rama_supersonica_mach_presion_y_garganta(self):
        n, d = self._caso()
        self.assertEqual(n["regimen"], "supersonico_ideal")
        valores = self._todos(d)
        self.assertEqual(len(valores), 41)
        self.assertAlmostEqual(valores[0]["mach"], 1, places=7)
        self.assertTrue(all(a["mach"] <= b["mach"] for a,b in zip(valores, valores[1:])))
        self.assertTrue(all(a["presion"] >= b["presion"] for a,b in zip(valores, valores[1:])))
        self.assertAlmostEqual(valores[-1]["mach"], n["mach_salida"], places=7)

    def test_sobreexpansion_no_inventa_choque_exterior(self):
        n, d = self._caso(250)
        self.assertEqual(n["regimen"], "supersonico_sobreexpandido_ideal")
        self.assertIsNone(d["choque"])
        self.assertEqual(len(d["segmentos"]), 1)

    def test_no_bloqueada_garganta_no_sonica_y_rama_subsonica(self):
        n, d = self._caso(490)
        self.assertEqual(n["regimen"], "subsonico_no_bloqueado")
        puntos = self._todos(d)
        self.assertLess(puntos[0]["mach"], 1)
        self.assertTrue(all(a["mach"] > b["mach"] for a,b in zip(puntos,puntos[1:])))
        self.assertTrue(all(a["presion"] < b["presion"] for a,b in zip(puntos,puntos[1:])))
        self.assertGreater(d["area_critica"]["antes"], 1)

    def test_frontera_bloqueada_salida_subsonica(self):
        # La frontera de bloqueo es sónica en garganta pero sub en salida.
        from tobera_convergente_divergente_cp import _salida_area, _sonico
        critico = _sonico(1200,500)
        p_limite = _salida_area(1200,500,critico,1.5,supersonica=False)["p"]
        n,d = self._caso(p_limite)
        self.assertEqual(n["regimen"], "bloqueado_salida_subsonica_limite")
        self.assertAlmostEqual(d["segmentos"][0][0]["mach"], 1, places=6)
        self.assertLess(d["segmentos"][0][-1]["mach"], 1)

    def test_masa_energia_y_entropia_en_todos_los_regimenes(self):
        for p in (50, 250, 350, 425, 490):
            with self.subTest(p=p):
                n,d = self._caso(p, puntos=31)
                self.assertTrue(d["disponible"])
                for e in self._todos(d):
                    self.assertAlmostEqual(e["flujo_masico_por_garganta"],
                                           d["flujo_masico_por_garganta"], delta=1e-4)
                    self.assertAlmostEqual(e["residuo_energia"], 0, delta=1e-7)
                    self.assertAlmostEqual(e["residuo_entropia"], 0, delta=1e-8)
                    self.assertAlmostEqual(e["entalpia"], h(e["temperatura"]))
                    self.assertAlmostEqual(e["entropia"], s(e["temperatura"], e["presion"]))

    def test_choque_interno_dos_estados_misma_area_y_salto_fisico(self):
        n,d = self._caso(350)
        self.assertEqual(n["regimen"], "choque_normal_interno")
        anterior, posterior = d["choque"]
        self.assertEqual(anterior["area_relativa"], posterior["area_relativa"])
        self.assertEqual(anterior["area_relativa"], n["relacion_areas_choque"])
        self.assertGreater(anterior["mach"], 1)
        self.assertLess(posterior["mach"], 1)
        self.assertGreater(posterior["presion"], anterior["presion"])
        self.assertGreater(posterior["entropia"], anterior["entropia"])
        self.assertLess(posterior["presion_remanso_region"],
                        anterior["presion_remanso_region"])
        self.assertAlmostEqual(anterior["flujo_masico_por_garganta"],
                               posterior["flujo_masico_por_garganta"], delta=1e-4)
        self.assertEqual(len(d["segmentos"]), 2)
        self.assertIs(d["segmentos"][0][-1], anterior)
        self.assertIs(d["segmentos"][1][0], posterior)

    def test_choque_en_salida_no_inventa_rama_exterior(self):
        limite = resolver_tobera_convergente_divergente(1200,500,350,1.5)[
            "umbral_choque_salida_aproximado"]
        n,d = self._caso(limite)
        self.assertEqual(n["regimen"], "choque_normal_salida")
        self.assertEqual(len(d["segmentos"][1]), 1)
        self.assertEqual(d["segmentos"][1][0]["papel"], "choque_despues_salida")
        self.assertAlmostEqual(d["choque"][0]["area_relativa"], 1.5)

    def test_criticas_distintas_despues_del_choque(self):
        _,d = self._caso(350)
        antes, despues = d["choque"]
        self.assertAlmostEqual(d["area_critica"]["antes"], 1.0)
        self.assertLess(d["area_critica"]["despues"], 1.0)
        self.assertAlmostEqual(antes["area_sobre_critica"],
                               antes["area_relativa"], places=5)
        self.assertNotAlmostEqual(despues["area_sobre_critica"],
                                  despues["area_relativa"], places=3)

    def test_extremos_coinciden_con_solucionador_cientifico(self):
        for p in (50, 350, 490):
            with self.subTest(p=p):
                n,d = self._caso(p)
                garganta = d["segmentos"][0][0]
                salida = d["segmentos"][-1][-1]
                self.assertAlmostEqual(garganta["mach"], n["mach_garganta"], places=6)
                self.assertAlmostEqual(garganta["presion"], n["presion_garganta"], places=5)
                self.assertAlmostEqual(salida["mach"], n["mach_salida"], places=6)
                self.assertAlmostEqual(salida["presion"], n["presion_salida"], places=4)

    def test_convergente_sin_geometria_es_ausente(self):
        n = resolver_tobera_convergente_divergente(1200,500,50,1.5)
        d = perfil_tobera_cp_variable({"tobera":n,
                                      "diagnosticos":{"tipo_tobera":"convergente"}})
        self.assertFalse(d["disponible"])
        self.assertIn("distribución de áreas", d["motivo"])
        self.assertIsNone(svg_perfil_tobera(d, "mach"))

    def test_no_resuelto_y_area_unidad_no_generan_puntos_ficticios(self):
        n = resolver_tobera_convergente_divergente(1200,500,50,1.5)
        n["resuelto"] = False
        r = {"tobera":n, "diagnosticos":{"tipo_tobera":"convergente_divergente"}}
        self.assertFalse(perfil_tobera_cp_variable(r)["disponible"])
        n["resuelto"] = True
        n["relacion_areas"] = 1.0
        self.assertFalse(perfil_tobera_cp_variable(r)["disponible"])

    def test_parametro_discretizacion_exige_entero_fisico(self):
        n,_ = self._caso()
        r = {"tobera":n, "diagnosticos":{"tipo_tobera":"convergente_divergente"}}
        for valor in (2, 122, 4.2, True, None):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                perfil_tobera_cp_variable(r, puntos_por_region=valor)

    def test_malla_fina_no_altera_estados_fisicos(self):
        for p in (50, 350, 490):
            with self.subTest(p=p):
                _,d11 = self._caso(p, puntos=11)
                _,d61 = self._caso(p, puntos=61)
                self.assertEqual(d11["segmentos"][0][0]["mach"],
                                 d61["segmentos"][0][0]["mach"])
                self.assertAlmostEqual(d11["segmentos"][-1][-1]["presion"],
                                       d61["segmentos"][-1][-1]["presion"], places=6)
                self.assertEqual(d11["choque"], d61["choque"])

    def test_puntos_cercanos_a_garganta_validos(self):
        _,d = self._caso(50, puntos=121)
        for e in d["segmentos"][0][:4]:
            self.assertGreaterEqual(e["mach"], 1-1e-6)
            self.assertAlmostEqual(e["residuo_energia"], 0, places=7)

    def test_svg_mismo_eje_y_segmentos_separados(self):
        _,d = self._caso(350)
        for clave in ("mach", "presion"):
            with self.subTest(clave=clave):
                svg = svg_perfil_tobera(d, clave)
                ElementTree.fromstring(svg)
                self.assertIn("A/Ag", svg)
                self.assertIn("Choque", svg)
                self.assertEqual(svg.count("<polyline"), 2)
        with self.assertRaises(ValueError):
            svg_perfil_tobera(d, "temperatura")

    def test_vista_actualizacion_y_conservacion_44_1_44_2_44_3(self):
        valores = {**DEFAULTS_TURBO, "tipo_tobera":"convergente_divergente"}
        a = preparar_vista_turborreactor(simular_turborreactor(valores))
        b = preparar_vista_turborreactor(simular_turborreactor({**valores,"T3":"1500"}))
        self.assertTrue(a["perfil_tobera"]["disponible"])
        self.assertNotEqual(a["svg_mach_perfil_tobera"], b["svg_mach_perfil_tobera"])
        for clave in ("svg_empuje", "svg_ts", "svg_mach_tobera",
                      "svg_presion_tobera", "svg_balance_energetico"):
            self.assertIn(clave, a)
            self.assertTrue(a[clave])
        html = (Path(__file__).resolve().parents[1]/"templates"/"turborreactor.html").read_text(encoding="utf-8")
        self.assertIn("vista.svg_mach_perfil_tobera|safe", html)
        self.assertIn("vista.svg_presion_perfil_tobera|safe", html)
        self.assertIn("vista.svg_mach_tobera|safe", html)
        self.assertIn("vista.svg_balance_energetico|safe", html)


if __name__ == "__main__":
    unittest.main()
