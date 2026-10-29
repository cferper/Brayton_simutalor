"""M46.1: verifica el divergente cónico sin tocar el solver físico."""

from math import isclose, pi, radians, sqrt, tan
import unittest
from xml.etree import ElementTree

from geometria_tobera_conica import (calcular_geometria_conica,
                                    svg_geometria_conica,
                                    validar_semidivergencia)
from turborreactor_web import (DEFAULTS_TURBO, preparar_vista_turborreactor,
                              simular_turborreactor, valores_turborreactor)


class GeometriaConica461(unittest.TestCase):
    def _motor(self, caudal="20", angulo="15", **cambios):
        valores = {**DEFAULTS_TURBO, "tipo_tobera": "convergente_divergente",
                   "gasto_masico_aire": caudal, "angulo_semidivergencia": angulo,
                   **cambios}
        return simular_turborreactor(valores)

    def test_longitud_analitica_radios_y_areas(self):
        g = self._motor()["geometria_conica"]
        self.assertTrue(g["disponible"])
        self.assertAlmostEqual(g["longitud_divergente"],
                               (g["radio_salida"]-g["radio_garganta"])/tan(radians(15)))
        self.assertAlmostEqual(pi*g["radio_garganta"]**2,g["area_garganta"])
        self.assertAlmostEqual(pi*g["radio_salida"]**2,g["area_salida"])
        self.assertAlmostEqual((g["radio_salida"]/g["radio_garganta"])**2,
                               g["relacion_areas"])

    def test_el_angulo_cambia_longitud_no_areas_ni_fisica(self):
        a, b = self._motor(angulo="10"), self._motor(angulo="20")
        ga, gb = a["geometria_conica"], b["geometria_conica"]
        self.assertGreater(ga["longitud_divergente"],gb["longitud_divergente"])
        self.assertAlmostEqual(ga["longitud_divergente"]*tan(radians(10)),
                               gb["longitud_divergente"]*tan(radians(20)))
        self.assertEqual(ga["area_salida"],gb["area_salida"])
        self.assertEqual(a["tobera"],b["tobera"])
        self.assertEqual(a["prestaciones"],b["prestaciones"])

    def test_escala_masica_raices_y_longitudes(self):
        a = self._motor(caudal="20")["geometria_conica"]
        b = self._motor(caudal="80")["geometria_conica"]
        for clave in ("radio_garganta", "radio_salida", "longitud_divergente"):
            self.assertAlmostEqual(b[clave]/a[clave],2)
        for clave in ("area_garganta", "area_salida"):
            self.assertAlmostEqual(b[clave]/a[clave],4)

    def test_sin_caudal_se_conserva_modo_especifico(self):
        r = self._motor(caudal="")
        self.assertNotIn("geometria_conica",r)
        self.assertNotIn("dimensionamiento_tobera",r)
        self.assertIsNone(preparar_vista_turborreactor(r)["svg_geometria_conica"])

    def test_convergente_no_inventa_divergente(self):
        r = self._motor(tipo_tobera="convergente")
        self.assertNotIn("geometria_conica",r)
        self.assertIsNone(preparar_vista_turborreactor(r)["svg_geometria_conica"])

    def test_salida_no_resuelta_no_inventa_longitud(self):
        r = self._motor(caudal="20", mach="0.9",rp="3",T3="500",pi_d="0.7")
        self.assertFalse(r["geometria_conica"]["disponible"])
        self.assertIsNone(svg_geometria_conica(r["geometria_conica"]))

    def test_invalidos_angulo(self):
        for valor in (0,90,-1,100,float("inf"),float("nan"),True,"15",None):
            with self.subTest(valor=valor),self.assertRaises(ValueError):
                validar_semidivergencia(valor)

    def test_invalidos_area_y_relacion(self):
        base = {"disponible":True,"tipo_tobera":"convergente_divergente",
                "area_garganta":0.1,"area_salida":0.2}
        for datos in ({"area_garganta":0},{"area_salida":0.09},
                      {"area_salida":float("nan")}, {"area_garganta":-1}):
            with self.subTest(datos=datos),self.assertRaises(ValueError):
                calcular_geometria_conica({**base,**datos},15)

    def test_svg_xml_y_proporcion(self):
        g = self._motor()["geometria_conica"]
        svg = svg_geometria_conica(g)
        self.assertIn("Longitud divergente",svg)
        self.assertIn("Garganta",svg)
        self.assertIn("Eje de simetría",svg)
        self.assertEqual(ElementTree.fromstring(svg).tag,"{http://www.w3.org/2000/svg}svg")
        vista = preparar_vista_turborreactor(self._motor())
        self.assertEqual(vista["svg_geometria_conica"][:4],"<svg")
        # Comprueba la escala única: delta y / delta x = tan(alpha).
        escala = min(580/g["longitud_divergente"],155/g["radio_salida"])
        dx = g["longitud_divergente"]*escala
        dy = (g["radio_salida"]-g["radio_garganta"])*escala
        self.assertTrue(isclose(dy/dx,tan(radians(g["angulo_grados"]))))

    def test_post_antiguo_sin_angulo_usa_default(self):
        campos = valores_turborreactor({**DEFAULTS_TURBO,"gasto_masico_aire":"20",
                                       "tipo_tobera":"convergente_divergente"})
        campos.pop("angulo_semidivergencia")
        r = simular_turborreactor(campos)
        self.assertEqual(r["geometria_conica"]["angulo_grados"],15.)

    def test_angulo_irrelevante_no_bloquea_convergente_ni_sin_caudal(self):
        for cambios in ({"tipo_tobera":"convergente", "gasto_masico_aire":"20"},
                        {"tipo_tobera":"convergente_divergente", "gasto_masico_aire":""}):
            r = self._motor(angulo="no es un ángulo",**cambios)
            self.assertNotIn("geometria_conica",r)
            self.assertIn("prestaciones",r)

    def test_limite_area_unidad_no_bloquea_motor(self):
        r = self._motor(epsilon="1")
        self.assertTrue(r["dimensionamiento_tobera"]["disponible"])
        self.assertEqual(r["dimensionamiento_tobera"]["relacion_areas"],1)
        self.assertFalse(r["geometria_conica"]["disponible"])
        self.assertIn("Ae/Ag = 1",r["geometria_conica"]["motivo"])
        self.assertIsNone(preparar_vista_turborreactor(r)["svg_geometria_conica"])


if __name__ == "__main__":
    unittest.main()
