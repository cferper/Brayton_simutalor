"""Tobera cp(T): verificación algebraica, numérica y de integración; no validación."""
import math
import unittest

from tobera_cp_variable import resolver_tobera_convergente, resolver_nucleo_con_tobera
from ciclo_cp_variable import EstadoFueraDeRango
from propiedades_aire import R_AIRE, gamma, h, s


class Tobera35(unittest.TestCase):
    def test_caso_bloqueado_y_balance(self):
        r = resolver_tobera_convergente(1332.54579137895, 404.82264067596, 100, .95)
        self.assertEqual(r['regimen'], 'bloqueado')
        self.assertAlmostEqual(r['mach_salida'], 1, places=8)
        self.assertGreater(r['presion_salida'], 100)
        self.assertAlmostEqual(r['residuo_energia'], 0, places=9)
        self.assertAlmostEqual(r['residuo_isentropico'], 0, places=9)

    def test_subsonico_y_empuje_presion_cero(self):
        r = resolver_tobera_convergente(1200, 300, 280, .9)
        self.assertEqual(r['regimen'], 'no_bloqueado')
        self.assertLess(r['mach_salida'], 1)
        self.assertAlmostEqual(r['presion_salida'], 280)
        self.assertEqual(r['empuje_especifico_presion'], 0)
        self.assertAlmostEqual(r['empuje_especifico_total'], r['velocidad_salida'])

    def test_critico_y_continuidad(self):
        inicial = resolver_tobera_convergente(1200, 300, 100, .87)
        pc = inicial['presion_critica']
        debajo = resolver_tobera_convergente(1200, 300, pc*(1-1e-6), .87)
        encima = resolver_tobera_convergente(1200, 300, pc*(1+1e-6), .87)
        self.assertEqual(debajo['regimen'], 'bloqueado')
        self.assertEqual(encima['regimen'], 'no_bloqueado')
        self.assertAlmostEqual(debajo['mach_salida'], 1, places=7)
        self.assertLess(abs(debajo['velocidad_salida']-encima['velocidad_salida']), .01)
        self.assertLess(abs(debajo['empuje_especifico_total']-encima['empuje_especifico_total']), .01)

    def test_rendimiento_nota_y_energia(self):
        ideal = resolver_tobera_convergente(1200, 300, 270, 1)
        real = resolver_tobera_convergente(1200, 300, 270, .8)
        self.assertLess(real['velocidad_salida'], ideal['velocidad_salida'])
        self.assertGreater(real['temperatura_salida'], ideal['temperatura_salida'])
        self.assertAlmostEqual(h(1200)-real['entalpia_salida'],
                               .8*(h(1200)-h(real['temperatura_isentropica_salida'])), places=8)

    def test_termino_presion_y_continuidad_masa(self):
        r = resolver_tobera_convergente(1200, 300, 100, 1)
        self.assertAlmostEqual(r['densidad_salida']*r['velocidad_salida']*
                               r['area_por_caudal'], 1, places=10)
        presion = (r['presion_salida']-100)*1000*r['area_por_caudal']
        self.assertAlmostEqual(r['empuje_especifico_presion'], presion, places=10)
        self.assertAlmostEqual(r['empuje_especifico_total'],
                               r['empuje_especifico_momento']+presion, places=10)

    def test_referencia_gamma_constante(self):
        # Analítico aproximado ideal cp constante, sin usar las inversiones del módulo.
        Tt, pt = 600., 300.
        g = gamma(Tt)
        relacion = (2/(g+1))**(g/(g-1))
        r = resolver_tobera_convergente(Tt, pt, 50, 1)
        self.assertLess(abs(r['presion_critica']/pt - relacion), .025)
        self.assertAlmostEqual(r['mach_salida'], 1, places=8)

    def test_consistencia_unidades(self):
        r = resolver_tobera_convergente(1200, 300, 100, .95)
        self.assertAlmostEqual(r['velocidad_salida']**2,
                               2000*(r['entalpia_remanso']-r['entalpia_salida']), places=7)
        self.assertAlmostEqual(r['velocidad_sonido']**2,
                               gamma(r['temperatura_salida'])*R_AIRE*r['temperatura_salida'], places=7)
        self.assertAlmostEqual(s(r['temperatura_isentropica_salida'], r['presion_salida']),
                               s(1200, 300), places=8)

    def test_entradas_invalidas(self):
        for entradas in ((1200, 100, 100, 1), (1200, 80, 100, .9),
                         (1200, 300, 100, 0), (1200, 300, 100, 1.2),
                         (1200, 300, 100, True), (199, 300, 100, 1),
                         (1200, 300, math.nan, 1)):
            with self.subTest(entradas=entradas), self.assertRaises(ValueError):
                resolver_tobera_convergente(*entradas)
        with self.assertRaises(EstadoFueraDeRango):
            resolver_tobera_convergente(200.1, 1000, 1, 1)

    def test_sin_sonico_en_dominio_y_caso_subsonico(self):
        # Temperatura de remanso baja, dominio termina antes del Mach crítico.
        r = resolver_tobera_convergente(230, 105, 104, 1)
        self.assertEqual(r['regimen'], 'no_bloqueado')
        self.assertLess(r['mach_salida'], 1)

    def test_integracion_nucleo_y_brayton_independiente(self):
        r = resolver_nucleo_con_tobera(288.15, 100, 10, .85, 1600, .04, .9, .98, .95)
        n, t = r['nucleo'], r['tobera']
        self.assertAlmostEqual(n['temperaturas'][3], t['temperatura_remanso'])
        self.assertAlmostEqual(n['presiones'][3], t['presion_remanso'])
        self.assertEqual(t['regimen'], 'bloqueado')
        self.assertGreater(t['empuje_especifico_total'], t['velocidad_salida'])
        self.assertAlmostEqual(n['residuo_eje'], 0, places=8)


if __name__ == '__main__':
    unittest.main()
