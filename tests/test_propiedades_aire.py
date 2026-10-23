"""Fase 2A: verificación numérica del módulo aislado de aire ideal cp(T).

Las referencias cp de la tabla provienen de las correlaciones NIST Shomate
de N2/O2, evaluadas separadamente con mezcla 78/21/1 % molar y Ar monoatómico.
No constituyen validación experimental del ciclo Brayton.
"""

from math import isclose, log
import unittest

import propiedades_aire as aire


class PropiedadesAireTests(unittest.TestCase):
    def test_coeficientes_shomate_transcritos_del_nist(self):
        # Tablas NIST Chemistry WebBook (A, B, C, D, E, F, G, H).
        referencias = {
            "N2": (500.,
                   (28.98641, 1.853978, -9.647459, 16.63537, 0.000117,
                    -8.671914, 226.4168, 0.),
                   (19.50583, 19.88705, -8.598535, 1.369784, 0.527601,
                    -4.935202, 212.3900, 0.)),
            "O2": (700.,
                   (31.32234, -20.23531, 57.86644, -36.50624, -0.007374,
                    -8.903471, 246.7945, 0.),
                   (30.03235, 8.772972, -3.988133, 0.788313, -0.741599,
                    -11.32468, 236.1663, 0.)),
        }
        self.assertEqual(aire._SHOMATE, referencias)

    def test_constantes_y_fracciones_molares(self):
        self.assertAlmostEqual(aire.MASA_MOLAR, 0.02896968, places=11)
        self.assertAlmostEqual(aire.R_AIRE, 287.0056769061, places=8)
        self.assertEqual(aire.T_REF, 298.15)
        self.assertEqual(aire.P_REF, 100.)

    def test_cp_con_referencias_nist_independientes(self):
        # J/(kg K): valores fijados a partir de los coeficientes de NIST
        # y el cp,molar de Ar = (5/2)*Ru, NO del módulo probado.
        referencias = {
            200.: 1001.92373248,
            300.: 1004.41363843,
            500.: 1028.93303914,
            700.: 1074.41841284,
            1000.: 1140.11720514,
            1500.: 1210.37147701,
            2000.: 1249.44265981,
        }
        for T, esperado in referencias.items():
            with self.subTest(T=T):
                self.assertAlmostEqual(aire.cp(T), esperado, delta=1e-5)

    def test_referencias_termicas_cero(self):
        self.assertEqual(aire.h(aire.T_REF), 0.)
        self.assertEqual(aire.s0(aire.T_REF), 0.)
        self.assertAlmostEqual(aire.s(aire.T_REF, aire.P_REF), 0., places=14)

    def test_derivada_de_entalpia_igual_cp(self):
        paso = 0.001  # K; lejos de los cambios de tramo
        for T in (201., 288.15, 400., 499., 501., 699., 701., 1000., 1800., 1999.):
            with self.subTest(T=T):
                derivada = (aire.h(T + paso) - aire.h(T - paso)) / (2 * paso)
                self.assertAlmostEqual(derivada, aire.cp(T)/1000, delta=2e-7)

    def test_derivada_de_entropia_igual_cp_dividido_por_T(self):
        paso = 0.001
        for T in (201., 288.15, 400., 499., 501., 699., 701., 1000., 1800., 1999.):
            with self.subTest(T=T):
                derivada = (aire.s0(T + paso) - aire.s0(T - paso)) / (2 * paso)
                self.assertAlmostEqual(derivada, aire.cp(T)/(1000*T), delta=5e-10)

    def test_h_y_s0_continuas_en_ambos_tramos(self):
        delta = 1e-7  # K; no se exige continuidad de cp entre ajustes NIST
        for frontera in (500., 700.):
            with self.subTest(frontera=frontera):
                for magnitud in (aire.h, aire.s0):
                    # Ausencia de salto: la diferencia lateral tiende a cero.
                    izquierda = magnitud(frontera - delta)
                    derecha = magnitud(frontera + delta)
                    central = magnitud(frontera)
                    self.assertLess(abs(derecha - central), 2e-7)
                    self.assertLess(abs(izquierda - central), 2e-7)

    def test_cp_positivo_y_entalpia_monotona(self):
        anteriores = None
        for indice in range(1801):
            T = 200. + indice
            self.assertGreater(aire.cp(T), aire.R_AIRE)
            if anteriores is not None:
                self.assertGreater(aire.h(T), anteriores)
            anteriores = aire.h(T)

    def test_integrales_con_cuadratura_numerica_independiente(self):
        a, b, n = 300., 1800., 15000  # extremos evitan discrepancias de referencia
        ancho = (b-a)/n
        suma_cp = suma_cp_sobre_T = 0.
        for i in range(n):
            izquierda, derecha = a+i*ancho, a+(i+1)*ancho
            suma_cp += (aire.cp(izquierda)+aire.cp(derecha))*ancho/(2*1000)
            suma_cp_sobre_T += (aire.cp(izquierda)/izquierda + aire.cp(derecha)/derecha)*ancho/(2*1000)
        self.assertAlmostEqual(aire.h(b)-aire.h(a), suma_cp, delta=2e-5)
        self.assertAlmostEqual(aire.s0(b)-aire.s0(a), suma_cp_sobre_T, delta=2e-8)

    def test_entropia_con_presion(self):
        T = 900.
        self.assertAlmostEqual(aire.s(T, 100.), aire.s0(T), places=13)
        self.assertAlmostEqual(aire.s(T, 200.)-aire.s(T, 100.),
                               -(aire.R_AIRE/1000)*log(2.), places=12)
        self.assertAlmostEqual(aire.s(T, 50.)-aire.s(T, 100.),
                               (aire.R_AIRE/1000)*log(2.), places=12)

    def test_presion_positiva_extrema_no_provoca_desbordamiento(self):
        for p in (5e-324, 1e-300, 1e300):
            with self.subTest(p=p):
                self.assertAlmostEqual(aire.s(500., p),
                                       aire.s0(500.)-(aire.R_AIRE/1000)*(log(p)-log(100.)),
                                       places=10)

    def test_gamma_decreciente_en_muestras(self):
        self.assertGreater(aire.gamma(300.), aire.gamma(1000.))
        self.assertGreater(aire.gamma(1000.), aire.gamma(2000.))
        for T in (200., 300., 500., 700., 1000., 2000.):
            with self.subTest(T=T):
                c = aire.cp(T)
                self.assertTrue(isclose(aire.gamma(T), c/(c-aire.R_AIRE), rel_tol=1e-14))

    def test_inversion_recupera_temperatura_y_tramos(self):
        for T in (200., 225., 298.15, 499.999, 500., 500.001,
                  699.999, 700., 700.001, 800., 1000., 1600., 1999.9, 2000.):
            with self.subTest(T=T):
                recuperada = aire.T_desde_h(aire.h(T))
                self.assertAlmostEqual(recuperada, T, delta=1e-8)

    def test_inversion_rechaza_entalpias_fuera_del_intervalo(self):
        for valor in (aire.h(200.)-1e-5, aire.h(2000.)+1e-5):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                aire.T_desde_h(valor)

    def test_todas_las_funciones_rechazan_temperaturas_invalidas(self):
        for invalida in (None, True, False, "298.15", complex(300,1),
                         float("nan"), float("inf"), -float("inf"),
                         0, 199.999, 2000.001, 10**1000):
            for funcion in (aire.cp, aire.h, aire.s0, aire.gamma):
                with self.subTest(valor=str(invalida)[:20], funcion=funcion.__name__):
                    with self.assertRaises(ValueError):
                        funcion(invalida)
            with self.subTest(valor=str(invalida)[:20], funcion="s"):
                with self.assertRaises(ValueError):
                    aire.s(invalida, 100.)

    def test_presiones_invalidas(self):
        for invalida in (None, True, False, "100", complex(1,1),
                         float("nan"), float("inf"), -float("inf"),
                         0, -1, 10**1000):
            with self.subTest(valor=str(invalida)[:20]), self.assertRaises(ValueError):
                aire.s(300., invalida)

    def test_entalpias_invalidas_en_inversion(self):
        for invalida in (None, True, False, "500", complex(1,1),
                         float("nan"), float("inf"), -float("inf"), 10**1000):
            with self.subTest(valor=str(invalida)[:20]), self.assertRaises(ValueError):
                aire.T_desde_h(invalida)


if __name__ == "__main__":
    unittest.main()
