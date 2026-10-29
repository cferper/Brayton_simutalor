"""Mapas NASA 47.3: procedencia, interpolación, escalado y giro monoeje."""

import unittest

from combustible_cp_variable import resolver_turborreactor_con_combustible
from mapas_turbomaquinaria_47 import (calibrar_mapas, cargar_mapas,
    consultar_compresor, consultar_turbina, flujo_corregido,
    giro_corregido, interpolar_bilineal)


class Mapas47(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.motor = resolver_turborreactor_con_combustible(
            T_amb=288.15,p_amb=100,mach=0,rp=10,eta_c=.85,T3=1600,
            delta=.04,eta_t=.9,eta_m=.98,eta_n=.95,pi_d=1)
        cls.mapas = cargar_mapas()
        cls.diseno = calibrar_mapas(cls.motor,20,20000,mapas=cls.mapas)

    def test_ejes_y_datos_fuente(self):
        m = self.mapas
        self.assertEqual(m["licencia"],"Apache-2.0")
        self.assertEqual(len(m["compresor"]["ncorr"]),13)
        self.assertEqual(len(m["compresor"]["rline"]),11)
        self.assertEqual(len(m["turbina"]["ncorr"]),6)
        self.assertEqual(len(m["turbina"]["pr"]),20)

    def test_interpolacion_nodos_y_centro_celda(self):
        m=self.mapas["compresor"]
        valor=interpolar_bilineal(m["ncorr"],m["rline"],m["wc"],1,2)
        self.assertAlmostEqual(valor,206,places=5)
        y0,y1=m["ncorr"][8:10]
        x0,x1=m["rline"][3:5]
        esperado=sum(m["wc"][i][j] for i in (8,9) for j in (3,4))/4
        self.assertAlmostEqual(interpolar_bilineal(m["ncorr"],m["rline"],m["wc"],
                              (y0+y1)/2,(x0+x1)/2),esperado)

    def test_reproduccion_punto_diseno(self):
        d=self.diseno
        c=consultar_compresor(d,20000,d["Tt2"],d["pt2"],2,mapas=self.mapas)
        t=consultar_turbina(d,20000,d["Tt3"],d["pt3"],d["rp_turbina"],mapas=self.mapas)
        for nombre,calculado,esperado in (("ma",c["gasto_masico_aire"],20),
                                           ("mg",t["gasto_masico_gases"],d["mdot_gases"]),
                                           ("prc",c["rp"],10),("eta_c",c["eta"],.85),
                                           ("eta_t",t["eta"],.9)):
            with self.subTest(nombre=nombre):
                self.assertAlmostEqual(calculado,esperado,places=9)
        self.assertAlmostEqual(t["rp"],d["rp_turbina"])
        self.assertAlmostEqual(t["gasto_masico_gases"],
                               c["gasto_masico_aire"]*(1+d["f"]))
        self.assertNotEqual(c["giro_corregido"],t["giro_corregido"])

    def test_corregidos_inversos_y_presion(self):
        d=self.diseno
        w=flujo_corregido(20,d["Tt2"],d["pt2"])
        self.assertAlmostEqual(w,20*(101.325/100))
        self.assertGreater(giro_corregido(20000,d["Tt2"]),
                           giro_corregido(20000,d["Tt3"]))

    def test_dominios_explicitos_no_extrapolar(self):
        d=self.diseno
        for rline in (.99,3.01):
            with self.subTest(rline=rline),self.assertRaises(ValueError):
                consultar_compresor(d,20000,d["Tt2"],d["pt2"],rline,mapas=self.mapas)
        with self.assertRaises(ValueError):
            consultar_turbina(d,20000,d["Tt3"],d["pt3"],100,mapas=self.mapas)


if __name__=="__main__":
    unittest.main()
