"""Milestone 38: barridos, clasificación, Pareto sintético y regresión."""

import unittest
from unittest.mock import patch

from ciclo_cp_variable import ErrorNumericoCiclo
from combustible_cp_variable import resolver_turborreactor_con_combustible
from mapas_prestaciones_turborreactor_cp import (
    barrer_mach_altitud, barrer_rp_t3, frente_pareto)


class MapasTurborreactor38(unittest.TestCase):
    def test_reproduce_m37(self):
        m = barrer_rp_t3([10], [1600])
        p = m["puntos"][0][0]
        r = resolver_turborreactor_con_combustible(
            0, 10, .85, 1600, .04, .9, .98, .95, 1, .99, 43000,
            T_amb=288.15, p_amb=100)
        self.assertEqual(p["Fs"], r["prestaciones"]["empuje_especifico_neto"])
        self.assertEqual(p["f"], r["combustor"]["f"])

    def test_ejes_y_forma_orden(self):
        m = barrer_rp_t3([5,10,15], [1400,1600])
        self.assertEqual((len(m["puntos"]),len(m["puntos"][0])),(2,3))
        self.assertEqual((m["puntos"][1][2]["entradas"]["rp"],
                          m["puntos"][1][2]["entradas"]["T3"]), (15,1600))
        self.assertEqual(m["total"],6)

    def test_unidades(self):
        m = barrer_rp_t3([10],[1600])
        self.assertEqual(m["unidades"]["Fs"], "N/(kg/s aire)")
        self.assertEqual(m["unidades"]["p4"], "kPa")
        self.assertEqual(m["unidades"]["TSFC_kg_N_h"], "kg/(N h)")

    def test_inadmisible_y_sin_falsos_ceros(self):
        m = barrer_rp_t3([5,10], [200,1600])
        p = m["puntos"][0][0]
        self.assertEqual(p["estado"], "inadmisible")
        self.assertIsNone(p["Fs"])
        self.assertIsNone(p["TSFC_kg_N_h"])
        self.assertEqual(m["validos"]+m["descartados"], m["total"])

    def test_maximo_fs_independiente(self):
        m = barrer_rp_t3([5,10,15],[1400,1600])
        validos = [p for fila in m["puntos"] for p in fila if p["estado"]=="valido"]
        self.assertEqual(m["maximo_Fs"]["valor"], max(p["Fs"] for p in validos))

    def test_minimo_tsfc_independiente(self):
        m = barrer_rp_t3([5,10,15],[1400,1600])
        validos = [p for fila in m["puntos"] for p in fila if p["estado"]=="valido"]
        self.assertEqual(m["minimo_TSFC"]["valor"],
                         min(p["TSFC_kg_N_h"] for p in validos))

    def test_pareto_sintetico_y_igualdad(self):
        def p(nombre, fs, tsfc):
            return {"nombre":nombre, "estado":"valido", "Fs":fs,
                    "TSFC_kg_N_h":tsfc}
        datos = [p("A",100,2),p("B",110,3),p("C",90,3),
                 p("D",110,2),p("E",120,4),p("F",110,2)]
        # D y F idénticos son ambos no dominados; A, B, C dominados.
        self.assertEqual([i["nombre"] for i in frente_pareto(datos)], ["D","E","F"])

    def test_sin_puntos_validos(self):
        m = barrer_rp_t3([5,10],[1300,1400], restricciones={"T3_max":900})
        self.assertEqual(m["validos"],0)
        self.assertIsNone(m["maximo_Fs"])
        self.assertIsNone(m["minimo_TSFC"])
        self.assertEqual(m["pareto"],[])
        self.assertTrue(all(p["Fs"] is None for fila in m["puntos"] for p in fila))

    def test_fronteras_discretas(self):
        m = barrer_rp_t3([5,10,15], [1400,1600,1800])
        self.assertIn(m["maximo_Fs"]["en_frontera_malla"], (True,False))
        for e in ("maximo_Fs","minimo_TSFC"):
            iy, ix = m[e]["punto"]["indices"]
            self.assertEqual(m[e]["en_frontera_malla"],
                             ix in (0,2) or iy in (0,2))

    def test_repetibilidad(self):
        a = barrer_rp_t3([5,10],[1400,1600])
        b = barrer_rp_t3([5,10],[1400,1600])
        self.assertEqual(a,b)

    def test_sin_pareto_mach_altitud(self):
        m = barrer_mach_altitud([0,.5,.8],[0,10000])
        self.assertEqual(m["total"], 6)
        self.assertIsNone(m["pareto"])
        self.assertFalse(m["pareto_aplicable"])
        self.assertEqual(m["eje_y"], "altitud_geopotencial")

    def test_entradas_invalidas(self):
        for x,y in (([],[1600]),([10],[1600,1600]),([10,5],[1600]),
                    ([1],[1600]),([10],[2001]),([True],[1600])):
            with self.subTest(x=x,y=y), self.assertRaises(ValueError):
                barrer_rp_t3(x,y)
        with self.assertRaises(ValueError):
            barrer_mach_altitud([1],[0])
        with self.assertRaises(ValueError):
            barrer_mach_altitud([0],[20001])

    def test_restricciones_diseno(self):
        m = barrer_rp_t3([5,10,15],[1400,1600],
                         restricciones={"rp_min":10,"T3_max":1500})
        self.assertEqual(m["por_motivo"]["restriccion_rp_min"],2)
        self.assertEqual(m["por_motivo"]["restriccion_T3_max"],2)
        self.assertTrue(all(p["estado"]=="inadmisible" for p in m["puntos"][1]))

    def test_no_cambia_solucionador_anterior(self):
        args=(0,10,.85,1600,.04,.9,.98,.95,1,.99,43000)
        antes = resolver_turborreactor_con_combustible(*args,T_amb=288.15,p_amb=100)
        barrer_rp_t3([5,10],[1400,1600])
        despues = resolver_turborreactor_con_combustible(*args,T_amb=288.15,p_amb=100)
        self.assertEqual(antes,despues)

    def test_distingue_fallo_numerico_de_error_programacion(self):
        with patch('mapas_prestaciones_turborreactor_cp.resolver_turborreactor_con_combustible',
                   side_effect=ErrorNumericoCiclo('inversion sin convergencia')):
            m = barrer_rp_t3([10],[1600])
            self.assertEqual(m['puntos'][0][0]['estado'],'fallo_numerico')
            self.assertIsNone(m['puntos'][0][0]['Fs'])
        with patch('mapas_prestaciones_turborreactor_cp.resolver_turborreactor_con_combustible',
                   side_effect=TypeError('error de programación')):
            with self.assertRaises(TypeError):
                barrer_rp_t3([10],[1600])


if __name__ == '__main__':
    unittest.main()
