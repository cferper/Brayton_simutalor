"""Proyección axial de estados de M44.4 y compatibilidad geométrica 46.1."""

from math import isclose, pi, radians, sqrt, tan
import unittest
from xml.etree import ElementTree

from geometria_tobera_conica import calcular_geometria_conica
from perfil_axial_tobera_conica import (posicion_axial_por_area,
                                      proyectar_perfil_axial,
                                      svg_perfil_axial)
from perfil_tobera_cp_variable import perfil_tobera_cp_variable
from tobera_convergente_divergente_cp import resolver_tobera_convergente_divergente
from turborreactor_web import DEFAULTS_TURBO, preparar_vista_turborreactor, simular_turborreactor


class PerfilesAxiales462(unittest.TestCase):
    @staticmethod
    def _caso(p=50., *, angulo=15., epsilon=1.5):
        # El solver M44.4 calcula los estados; la superficie física se fija
        # por un caudal de referencia independiente de la transformación x.
        n = resolver_tobera_convergente_divergente(1200,500,p,epsilon)
        perfil = perfil_tobera_cp_variable({"tobera":n,
                   "diagnosticos":{"tipo_tobera":"convergente_divergente"}})
        g = calcular_geometria_conica({"disponible":True,
             "tipo_tobera":"convergente_divergente", "area_garganta":.04,
             "area_salida":.04*epsilon},angulo)
        return perfil,g,proyectar_perfil_axial(perfil,g)

    def test_conversion_analitica_e_inversion_areas(self):
        _,g,_=self._caso()
        for a in (1,1.12,1.25,1.45,1.5):
            with self.subTest(a=a):
                x=posicion_axial_por_area(a,g)
                r=g["radio_garganta"]+x*tan(radians(g["angulo_grados"]))
                self.assertAlmostEqual(pi*r*r/g["area_garganta"],a,places=9)

    def test_garganta_y_salida(self):
        _,g,d=self._caso()
        self.assertEqual(posicion_axial_por_area(1,g),0)
        self.assertEqual(posicion_axial_por_area(g["relacion_areas"],g),g["longitud_divergente"])
        self.assertEqual(d["segmentos"][0][0]["x"],0)
        self.assertEqual(d["segmentos"][-1][-1]["x"],g["longitud_divergente"])

    def test_monotonia_y_preservacion_estados_mach_presion(self):
        for p in (50,250,350,490):
            with self.subTest(p=p):
                perfil,g,d=self._caso(p)
                self.assertTrue(d["disponible"])
                for original,axial in zip(perfil["segmentos"],d["segmentos"]):
                    for o,a in zip(original,axial):
                        self.assertEqual(o["mach"],a["mach"])
                        self.assertEqual(o["presion"],a["presion"])
                        self.assertEqual(o["area_relativa"],a["area_relativa"])
                    self.assertTrue(all(a["x"]<=b["x"] for a,b in zip(axial,axial[1:])))

    def test_choque_interno_discontinuidad_en_misma_posicion(self):
        perfil,g,d=self._caso(350)
        antes,despues=d["choque"]
        self.assertEqual(antes["x"],despues["x"])
        self.assertEqual(antes["x"],d["x_choque"])
        self.assertAlmostEqual(d["x_choque"],posicion_axial_por_area(
            perfil["choque"][0]["area_relativa"],g))
        self.assertGreater(antes["mach"],1)
        self.assertLess(despues["mach"],1)
        self.assertGreater(despues["presion"],antes["presion"])
        for magnitud in ("mach","presion"):
            raiz=ElementTree.fromstring(svg_perfil_axial(d,magnitud))
            polilineas=raiz.findall("{http://www.w3.org/2000/svg}polyline")
            self.assertEqual(len(polilineas),2)
            self.assertTrue(all(p.attrib["points"] for p in polilineas))

    def test_choque_en_salida(self):
        umbral=resolver_tobera_convergente_divergente(1200,500,350,1.5)[
            "umbral_choque_salida_aproximado"]
        _,g,d=self._caso(umbral)
        self.assertEqual(d["x_choque"],g["longitud_divergente"])
        self.assertEqual(len(d["segmentos"][1]),1)

    def test_angulo_y_caudal_cambian_solo_abscisas(self):
        perfil,g,a=self._caso(350,angulo=10)
        _,g2,b=self._caso(350,angulo=20)
        self.assertGreater(a["longitud_divergente"],b["longitud_divergente"])
        self.assertEqual(a["segmentos"][0][10]["mach"],b["segmentos"][0][10]["mach"])
        g3=calcular_geometria_conica({"disponible":True,"tipo_tobera":"convergente_divergente",
            "area_garganta":.16,"area_salida":.24},10)
        c=proyectar_perfil_axial(perfil,g3)
        self.assertAlmostEqual(c["longitud_divergente"],2*a["longitud_divergente"])
        self.assertEqual(c["segmentos"][0][10]["presion"],a["segmentos"][0][10]["presion"])

    def test_sin_geometria_ni_perfil(self):
        perfil,g,_=self._caso()
        self.assertFalse(proyectar_perfil_axial(perfil,None)["disponible"])
        self.assertFalse(proyectar_perfil_axial({"disponible":False},g)["disponible"])
        self.assertIsNone(svg_perfil_axial({"disponible":False},"mach"))
        with self.assertRaises(ValueError):
            posicion_axial_por_area(2,g)

    def test_compatibilidad_formulario_461(self):
        for angulo in ("10","15","25"):
            r=simular_turborreactor({**DEFAULTS_TURBO,
               "tipo_tobera":"convergente_divergente","gasto_masico_aire":"20",
               "angulo_semidivergencia":angulo})
            vista=preparar_vista_turborreactor(r)
            self.assertEqual(vista["perfil_axial_tobera"]["longitud_divergente"],
                             r["geometria_conica"]["longitud_divergente"])
            self.assertIn("<svg",vista["svg_mach_axial"])
            self.assertIn("<svg",vista["svg_presion_axial"])

    def test_tolerancia_compatible_sin_perder_estados(self):
        perfil, _, _ = self._caso(350)
        # Geometría con discrepancia relativa minúscula aceptada por la
        # comparación global, aunque el último punto la sobrepase.
        g = calcular_geometria_conica({"disponible":True,
            "tipo_tobera":"convergente_divergente", "area_garganta":.04,
            "area_salida":.04*(1.5-1e-6)},15)
        d = proyectar_perfil_axial(perfil,g)
        self.assertTrue(d["disponible"])
        self.assertEqual(d["segmentos"][-1][-1]["x"],g["longitud_divergente"])
        self.assertEqual(d["segmentos"][-1][-1]["presion"],
                         perfil["segmentos"][-1][-1]["presion"])
        with self.assertRaises(ValueError):
            posicion_axial_por_area(1.51,g)

    def test_svg_ejes_graduados_y_referencias(self):
        _,_,d=self._caso(350)
        mach=svg_perfil_axial(d,"mach")
        presion=svg_perfil_axial(d,"presion")
        self.assertIn("Referencia M = 1",mach)
        self.assertIn("p ambiente",presion)
        self.assertIn("Posición axial x [m]",mach)
        self.assertGreaterEqual(mach.count("text"),16)
        self.assertGreaterEqual(presion.count("text"),16)


if __name__ == "__main__":
    unittest.main()
