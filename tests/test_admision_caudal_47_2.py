"""Admisión M47.2: flujo exterior y condición local de compresor."""

import unittest

from admision_caudal_cp import evaluar_admision, estado_seccion_compresor
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor


class Admision47(unittest.TestCase):
    def motor(self, **cambios):
        datos = dict(DEFAULTS_TURBO)
        datos.update(cambios)
        return simular_turborreactor(datos)

    def test_estatico_no_caudal_de_aire_cero(self):
        r = evaluar_admision(self.motor(), area_captacion=.15)
        self.assertEqual(r["estado"], "aspiracion_no_determinada")
        self.assertIsNone(r["caudal_captacion_geometrica"])
        self.assertIsNone(r["caudal_entrada_compresor"])

    def test_estatico_aspiracion_con_condicion_local(self):
        motor = self.motor()
        r = evaluar_admision(motor,area_entrada_compresor=.1,
                              mach_entrada_compresor=.3)
        self.assertGreater(r["caudal_entrada_compresor"],0)
        self.assertFalse(r["captacion_en_vuelo"])
        self.assertAlmostEqual(r["estado_entrada_compresor"]["residuo_energia"],0,places=9)

    def test_vuelo_area_captacion_para_caudal_conocido(self):
        motor = self.motor(mach="0.6")
        r = evaluar_admision(motor,gasto_masico_aire=20)
        a = r["area_captacion_requerida"]
        self.assertGreater(a,0)
        b = evaluar_admision(motor,area_captacion=a)
        self.assertAlmostEqual(b["caudal_captacion_geometrica"],20)
        self.assertEqual(b["estado"],"caudal_no_determinado")

    def test_ambiente_y_area_escalan_flujo_exterior(self):
        base = self.motor(mach="0.5")
        r = evaluar_admision(base,area_captacion=.1)
        r2 = evaluar_admision(base,area_captacion=.2)
        self.assertAlmostEqual(2*r["caudal_captacion_geometrica"],
                               r2["caudal_captacion_geometrica"])
        p = evaluar_admision(self.motor(mach="0.5",p_amb="80"),area_captacion=.1)
        t = evaluar_admision(self.motor(mach="0.5",T_amb="300"),area_captacion=.1)
        self.assertLess(p["caudal_captacion_geometrica"],r["caudal_captacion_geometrica"])
        self.assertNotEqual(t["caudal_captacion_geometrica"],r["caudal_captacion_geometrica"])

    def test_difusor_recuperacion_presion(self):
        r1 = self.motor(mach="0.5",pi_d="1")
        r2 = self.motor(mach="0.5",pi_d="0.9")
        s1 = evaluar_admision(r1,area_entrada_compresor=.1,mach_entrada_compresor=.2)
        s2 = evaluar_admision(r2,area_entrada_compresor=.1,mach_entrada_compresor=.2)
        self.assertAlmostEqual(s2["caudal_entrada_compresor"]/.9,
                               s1["caudal_entrada_compresor"],places=7)

    def test_continuidad_local_y_diagnostico_incompatible(self):
        motor = self.motor(mach="0.4")
        a = evaluar_admision(motor,mach_entrada_compresor=.25,gasto_masico_aire=20)
        seccion = a["area_entrada_compresor_requerida"]
        bien = evaluar_admision(motor,area_entrada_compresor=seccion,
                 mach_entrada_compresor=.25,gasto_masico_aire=20)
        mal = evaluar_admision(motor,area_entrada_compresor=seccion*1.2,
                 mach_entrada_compresor=.25,gasto_masico_aire=20)
        self.assertEqual(bien["estado"],"continuidad_compatible")
        self.assertLess(abs(bien["residuo_continuidad"]),1e-9)
        self.assertEqual(mal["estado"],"incompatible_con_caudal_impuesto")

    def test_limites_no_inventan_gasto(self):
        for mach in (-.1,1,True,float('nan')):
            with self.subTest(mach=mach),self.assertRaises(ValueError):
                estado_seccion_compresor(300,100,mach)
        with self.assertRaises(ValueError):
            evaluar_admision(self.motor(),area_captacion=0)

    def test_integracion_web_ambas_modalidades(self):
        r = self.motor(mach="0.5",gasto_masico_aire="20",
                       area_captacion="0.1",area_entrada_compresor="0.1",
                       mach_entrada_compresor="0.3")
        self.assertIn("estudio_admision", r)
        self.assertGreater(r["estudio_admision"]["caudal_entrada_compresor"],0)
        fijo = self.motor(modo_caudal="fijo",tipo_tobera="convergente_divergente",
                          area_garganta_fija=".01",area_salida_fija=".015",
                          mach_entrada_compresor=".3",area_entrada_compresor=".1")
        self.assertIn("estudio_admision",fijo)
        self.assertIsNotNone(fijo["estudio_admision"]["residuo_continuidad"])


if __name__ == "__main__":
    unittest.main()
