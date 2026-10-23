"""Fase 2B: verificación de un solucionador Brayton aislado con cp(T).

La cuadratura de cp de algunas pruebas es independiente de las primitivas
Shomate h y s0 usadas por el solucionador; no es validación experimental.
"""

from math import isclose, log
import unittest

import propiedades_aire as aire
from ciclo_cp_variable import (ErrorNumericoCiclo, EstadoFueraDeRango,
                               resolver_ciclo)


def _integral_cp(a, b, *, sobre_T=False, divisiones=5000):
    """Referencia independiente: regla del punto medio sobre cp tabulado.

    Integra cp/1000 o cp/(1000*T) sin usar h, s0 ni T_desde_h.
    La malla excluye los extremos, donde puede cambiar el tramo NIST.
    """
    ancho = (b - a) / divisiones
    total = 0.0
    for indice in range(divisiones):
        T = a + (indice + 0.5) * ancho
        valor = aire.cp(T) / 1000.0
        total += valor / T if sobre_T else valor
    return total * ancho


def _raiz_referencia_sin_s0(T_entrada, cambio_presion):
    """Bisección independiente, integral numérica de cp(T)/T."""
    objetivo = aire.R_AIRE / 1000.0 * log(cambio_presion)
    izquierda, derecha = aire.T_MIN, aire.T_MAX
    for _ in range(46):
        medio = (izquierda + derecha) / 2.0
        entropia_integrada = _integral_cp(T_entrada, medio, sobre_T=True,
                                         divisiones=2500)
        if entropia_integrada < objetivo:
            izquierda = medio
        else:
            derecha = medio
    return (izquierda + derecha) / 2.0


class CicloCPVariableTests(unittest.TestCase):
    def setUp(self):
        self.base = (288.15, 1600.0, 10.0, 100.0, .85, .9, .05)

    def punto(self, **cambios):
        entradas = dict(zip(("T1", "T3", "rp", "p1", "eta_c", "eta_t", "delta"),
                            self.base))
        entradas.update(cambios)
        return resolver_ciclo(**entradas)

    def test_caso_base_valido_con_estados_y_signos(self):
        punto = self.punto()
        self.assertTrue(punto["viable"])
        self.assertEqual(punto["motivos"], ())
        self.assertEqual(punto["presiones"], (100., 1000., 950., 100.))
        T1, T2, T3, T4 = punto["temperaturas"]
        self.assertTrue(T1 < punto["T2s"] < T2 < T3)
        self.assertTrue(T1 < punto["T4s"] < T4 < T3)
        for clave in ("trabajo_compresor", "trabajo_turbina", "trabajo_neto",
                      "calor_aportado", "calor_rechazado", "rendimiento"):
            self.assertGreater(punto[clave], 0)
        self.assertLess(punto["rendimiento"], 1)

    def test_isentropicas_compresor_y_turbina_independientes_de_s0(self):
        punto = self.punto()
        ref2 = _raiz_referencia_sin_s0(288.15, 10.)
        ref4 = _raiz_referencia_sin_s0(1600., 100./950.)
        self.assertAlmostEqual(punto["T2s"], ref2, delta=0.003)
        self.assertAlmostEqual(punto["T4s"], ref4, delta=0.003)
        self.assertLess(abs(punto["residuo_isentropico_compresor"]), 1e-10)
        self.assertLess(abs(punto["residuo_isentropico_turbina"]), 1e-10)

    def test_eficiencias_entalpicas_y_no_de_temperatura(self):
        punto = self.punto()
        h1, h2, h3, h4 = punto["entalpias"]
        h2s, h4s = punto["entalpias_isentropicas"]
        self.assertAlmostEqual((h2s-h1)/(h2-h1), .85, delta=2e-12)
        self.assertAlmostEqual((h3-h4)/(h3-h4s), .9, delta=2e-12)
        T1, T2, T3, T4 = punto["temperaturas"]
        self.assertGreater(abs((punto["T2s"]-T1)/(T2-T1) - .85), 0.003)
        self.assertGreater(abs((T3-T4)/(T3-punto["T4s"]) - .9), 0.003)

    def test_primera_ley_con_calor_rechazado(self):
        for cambios in ({}, {"eta_c": 1, "eta_t": 1, "delta": 0},
                        {"rp": 1.}, {"T3": 500.}):
            with self.subTest(cambios=cambios):
                punto = self.punto(**cambios)
                self.assertAlmostEqual(punto["trabajo_neto"],
                                       punto["calor_aportado"]-punto["calor_rechazado"],
                                       delta=1e-9)
                self.assertLess(abs(punto["residuo_primera_ley"]), 1e-9)

    def test_saltos_de_entalpia_con_cuadratura_independiente(self):
        punto = self.punto()
        T1, T2, T3, T4 = punto["temperaturas"]
        self.assertAlmostEqual(punto["trabajo_compresor"],
                               _integral_cp(T1, T2), delta=1e-3)
        self.assertAlmostEqual(punto["trabajo_turbina"],
                               _integral_cp(T4, T3), delta=1e-3)

    def test_segunda_ley_en_compresor_y_turbina_adiabaticos(self):
        for eficiencias in ((.85, .9), (.5, .5), (1, 1)):
            with self.subTest(eficiencias=eficiencias):
                punto = self.punto(eta_c=eficiencias[0], eta_t=eficiencias[1])
                self.assertGreaterEqual(punto["generacion_entropia_compresor"], -1e-10)
                self.assertGreaterEqual(punto["generacion_entropia_turbina"], -1e-10)
                s1, s2, s3, s4 = punto["entropias"]
                self.assertAlmostEqual(s2-s1, punto["generacion_entropia_compresor"])
                self.assertAlmostEqual(s4-s3, punto["generacion_entropia_turbina"])

    def test_limite_reversible_con_y_sin_perdida_de_presion(self):
        for delta in (0.0, .05):
            with self.subTest(delta=delta):
                punto = self.punto(eta_c=1, eta_t=1, delta=delta)
                self.assertAlmostEqual(punto["temperaturas"][1], punto["T2s"], delta=1e-8)
                self.assertAlmostEqual(punto["temperaturas"][3], punto["T4s"], delta=1e-8)
                self.assertAlmostEqual(punto["generacion_entropia_compresor"], 0, delta=1e-10)
                self.assertAlmostEqual(punto["generacion_entropia_turbina"], 0, delta=1e-10)

    def test_estado_ideal_vs_noideal_y_perdida_de_presion(self):
        ideal = self.punto(eta_c=1, eta_t=1, delta=0)
        noideal = self.punto()
        self.assertGreater(noideal["trabajo_compresor"], ideal["trabajo_compresor"])
        self.assertLess(noideal["trabajo_turbina"], ideal["trabajo_turbina"])
        self.assertLess(noideal["trabajo_neto"], ideal["trabajo_neto"])
        self.assertLess(noideal["rendimiento"], ideal["rendimiento"])

    def test_caso_degenerado_sin_compresion_ni_expansion(self):
        punto = self.punto(rp=1, eta_c=1, eta_t=1, delta=0)
        self.assertFalse(punto["viable"])
        self.assertIn("compresion", punto["motivos"])
        self.assertIn("expansion", punto["motivos"])
        self.assertIn("trabajo_neto", punto["motivos"])
        self.assertAlmostEqual(punto["trabajo_compresor"], 0, delta=1e-9)
        self.assertAlmostEqual(punto["trabajo_turbina"], 0, delta=1e-9)
        self.assertIsNone(punto["rendimiento"])

    def test_caso_no_motor_con_calor_no_positivo(self):
        punto = self.punto(T1=500., T3=400., rp=1., delta=0,
                           eta_c=1, eta_t=1)
        self.assertFalse(punto["viable"])
        self.assertLess(punto["calor_aportado"], 0)
        self.assertIn("calor_aportado", punto["motivos"])
        self.assertIsNone(punto["rendimiento"])
        self.assertTrue(isclose(punto["residuo_primera_ley"], 0, abs_tol=1e-9))

    def test_frontera_expansion_con_perdida_no_es_motor(self):
        perdida = .05
        punto = self.punto(rp=1/(1-perdida), delta=perdida)
        self.assertFalse(punto["viable"])
        self.assertIn("expansion", punto["motivos"])
        self.assertAlmostEqual(punto["presiones"][2], punto["presiones"][3],
                               delta=1e-11)

    def test_frontera_trabajo_neto_y_vecindades(self):
        # Para este conjunto existe una raíz interior entre rp=1,1 y rp=2.
        # La búsqueda del TEST sólo lee resultados y no emplea los algoritmos
        # del solucionador para hallar la frontera.
        inferior, superior = 1.1, 2.0
        self.assertLess(self.punto(T3=550., rp=inferior)["trabajo_neto"], 0)
        self.assertGreater(self.punto(T3=550., rp=superior)["trabajo_neto"], 0)
        for _ in range(45):
            medio = (inferior+superior)/2
            if self.punto(T3=550., rp=medio)["trabajo_neto"] < 0:
                inferior = medio
            else:
                superior = medio
        frontera = (inferior+superior)/2
        punto = self.punto(T3=550., rp=frontera)
        self.assertAlmostEqual(punto["trabajo_neto"], 0, delta=1e-8)
        self.assertFalse(punto["viable"])
        self.assertIn("trabajo_neto", punto["motivos"])
        self.assertFalse(self.punto(T3=550., rp=frontera-1e-4)["viable"])
        self.assertTrue(self.punto(T3=550., rp=frontera+1e-4)["viable"])

    def test_presion_absoluta_no_altera_estados_ideales(self):
        base = self.punto(p1=100.)
        otro = self.punto(p1=500.)
        for clave in ("temperaturas", "entalpias", "entalpias_isentropicas"):
            for a, b in zip(base[clave], otro[clave]):
                self.assertAlmostEqual(a, b, delta=1e-8)
        self.assertAlmostEqual(base["rendimiento"], otro["rendimiento"], delta=1e-12)

    def test_temperaturas_extremas_iguales_son_calculables_pero_no_motoras(self):
        punto = resolver_ciclo(500., 500., 1., 100., 1., 1., 0.)
        self.assertFalse(punto["viable"])
        self.assertAlmostEqual(punto["calor_aportado"], 0, delta=1e-9)
        self.assertIsNone(punto["rendimiento"])

    def test_inversion_reevaluada_no_oculta_residuos(self):
        punto = self.punto()
        h1, h2, h3, h4 = punto["entalpias"]
        h2s, h4s = punto["entalpias_isentropicas"]
        self.assertAlmostEqual(h2, h1+(h2s-h1)/.85, delta=1e-9)
        self.assertAlmostEqual(h4, h3-.9*(h3-h4s), delta=1e-9)

    def test_no_recorta_temperatura_isentropica_fuera_de_rango(self):
        for cambios in ({"T1": 1900., "rp": 5.},
                        {"T1": 200., "rp": .5, "delta": 0},
                        {"T3": 200., "rp": 10.}):
            with self.subTest(cambios=cambios), self.assertRaises(EstadoFueraDeRango):
                self.punto(**cambios)

    def test_no_recorta_temperatura_real_fuera_de_rango(self):
        with self.assertRaisesRegex(EstadoFueraDeRango, "real"):
            self.punto(T1=700., rp=8., eta_c=.10)

    def test_parametros_invalidos_diferenciados_de_inviabilidad(self):
        invalidos = ({"T1": 199.99}, {"T3": 2000.01}, {"rp": 0},
                     {"p1": -1}, {"eta_c": 0}, {"eta_t": 1.1},
                     {"delta": 1}, {"delta": -.1}, {"tolerancia": -1},
                     {"eta_t": float('nan')}, {"p1": float('inf')},
                     {"rp": True}, {"T3": False}, {"eta_c": None},
                     {"delta": "0.05"}, {"p1": complex(100, 1)},
                     {"rp": 10**1000})
        for cambios in invalidos:
            with self.subTest(cambios=str(cambios)[:45]), self.assertRaises(ValueError):
                self.punto(**cambios)

    def test_extremos_admitidos_sin_extrapolacion(self):
        extremo = resolver_ciclo(200., 2000., 1., 100., 1., 1., 0.)
        self.assertEqual(extremo["temperaturas"][0], 200.)
        self.assertEqual(extremo["temperaturas"][2], 2000.)
        self.assertFalse(extremo["viable"])

    def test_presiones_irrepresentables_producen_error_numerico(self):
        with self.assertRaises(ErrorNumericoCiclo):
            self.punto(p1=1e300, rp=1e300)
        with self.assertRaises(ErrorNumericoCiclo):
            self.punto(p1=1e-300, rp=1e-300)

    def test_maquinas_en_sentido_contrario_no_se_validan_como_motor(self):
        punto = self.punto(rp=1.0, delta=.05)
        self.assertFalse(punto["viable"])
        self.assertIn("expansion", punto["motivos"])
        self.assertIn("segunda_ley_turbina", punto["motivos"])
        self.assertLess(punto["generacion_entropia_turbina"], 0)


if __name__ == "__main__":
    unittest.main()
