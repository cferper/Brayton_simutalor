"""Estudio de sensibilidad geométrica sin alterar el motor."""

from math import isclose, radians, tan
import unittest
from xml.etree import ElementTree

from estudio_geometrico_tobera import (estudiar_angulos_geometria,
                                      svg_comparacion_conos, svg_longitud_angulo)
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor, preparar_vista_turborreactor


class EstudioGeometrico463(unittest.TestCase):
    def _motor(self,angulo="15",caudal="20"):
        return simular_turborreactor({**DEFAULTS_TURBO,
            "tipo_tobera":"convergente_divergente",
            "gasto_masico_aire":caudal,"angulo_semidivergencia":angulo})

    def test_longitudes_analiticas_y_monotonia(self):
        g=self._motor()["geometria_conica"]
        filas=estudiar_angulos_geometria(g)["filas"]
        self.assertEqual([f["angulo_grados"] for f in filas],[5,10,15,20,25])
        self.assertTrue(all(a["longitud_divergente"]>b["longitud_divergente"]
                            for a,b in zip(filas,filas[1:])))
        for f in filas:
            self.assertAlmostEqual(f["longitud_divergente"],
               (g["radio_salida"]-g["radio_garganta"])/tan(radians(f["angulo_grados"])))

    def test_areas_y_diametros_fijos(self):
        filas=estudiar_angulos_geometria(self._motor()["geometria_conica"])["filas"]
        for clave in ("diametro_garganta","diametro_salida","relacion_areas"):
            self.assertTrue(all(isclose(f[clave],filas[0][clave]) for f in filas))

    def test_seleccion_formulario_no_optima(self):
        a=self._motor("12")
        estudio=estudiar_angulos_geometria(a["geometria_conica"])
        marcados=[f for f in estudio["filas"] if f["seleccionado"]]
        self.assertEqual(len(marcados),1)
        self.assertEqual(marcados[0]["angulo_grados"],12)
        self.assertAlmostEqual(marcados[0]["longitud_divergente"],
                               a["geometria_conica"]["longitud_divergente"])

    def test_comparacion_misma_escala_y_tres_angulos(self):
        estudio=estudiar_angulos_geometria(self._motor()["geometria_conica"])
        comparacion=estudio["comparacion"]
        self.assertEqual([g["angulo_grados"] for g in comparacion],[10,15,20])
        self.assertGreater(comparacion[0]["longitud_divergente"],
                           comparacion[-1]["longitud_divergente"])
        self.assertTrue(all(g["area_garganta"]==comparacion[0]["area_garganta"]
                            for g in comparacion))
        svg=svg_comparacion_conos(estudio)
        raiz=ElementTree.fromstring(svg)
        self.assertEqual(len(raiz.findall("{http://www.w3.org/2000/svg}polygon")),3)
        self.assertIn("misma escala",svg)

    def test_curva_svg_y_etiqueta_seleccion(self):
        estudio=estudiar_angulos_geometria(self._motor("15")["geometria_conica"])
        svg=svg_longitud_angulo(estudio)
        self.assertIn("Selección",svg)
        self.assertIn("Semidivergencia",svg)
        self.assertEqual(ElementTree.fromstring(svg).tag,"{http://www.w3.org/2000/svg}svg")

    def test_angulo_no_modifica_solver(self):
        a,b=self._motor("10"),self._motor("20")
        for clave in ("tobera","prestaciones","compresor","combustor","turbina"):
            self.assertEqual(a[clave],b[clave])
        self.assertNotEqual(a["geometria_conica"]["longitud_divergente"],
                            b["geometria_conica"]["longitud_divergente"])

    def test_sin_geometria_no_hay_grafica(self):
        estudio=estudiar_angulos_geometria(None)
        self.assertFalse(estudio["disponible"])
        self.assertIsNone(svg_longitud_angulo(estudio))
        self.assertIsNone(svg_comparacion_conos(estudio))
        r=self._motor(caudal="")
        v=preparar_vista_turborreactor(r)
        self.assertFalse(v["estudio_geometrico"]["disponible"])
        self.assertIsNone(v["svg_longitud_angulo"])

    def test_compatibilidad_con_461_y_462(self):
        r=self._motor()
        vista=preparar_vista_turborreactor(r)
        self.assertTrue(vista["perfil_axial_tobera"]["disponible"])
        self.assertEqual(vista["estudio_geometrico"]["seleccionado"],
                         r["geometria_conica"]["angulo_grados"])
        self.assertIn("<svg",vista["svg_longitud_angulo"])
        self.assertIn("<svg",vista["svg_comparacion_conos"])


if __name__=="__main__":
    unittest.main()
