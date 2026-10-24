"""Pruebas focalizadas de los nuevos SVG; no revalidan los modelos 2A–2C."""

import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from ciclo_cp_variable import resolver_ciclo, EstadoFueraDeRango
from cp_variable_web import DEFAULTS, curvas_optimizacion, preparar_resultados
from graficas_cp_variable import (
    R_AIRE, _tramos, graficas_optimizacion, graficas_resultados,
    svg_balances, svg_comparacion, svg_propiedades, svg_pv, svg_ts,
)
from optimizacion_cp_variable import estudiar_cp_variable
from propiedades_aire import cp, gamma
from web_app import app

SVG = "{http://www.w3.org/2000/svg}"


def elementos(svg, etiqueta, **atributos):
    raiz = ET.fromstring(svg)
    encontrados = raiz.findall(f".//{SVG}{etiqueta}")
    return [x for x in encontrados if all(x.get(clave) == valor for clave, valor in atributos.items())]


class GraficasCPVariable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ciclo = resolver_ciclo(**DEFAULTS)
        cls.datos = preparar_resultados(DEFAULTS)

    def test_seis_resultados_tres_optimizaciones_y_svg_validos(self):
        self.assertEqual(len(self.datos["graficas_resultados"]), 6)
        self.assertEqual(len(self.datos["graficas_optimizacion"]), 3)
        for _, svg, explicacion in (self.datos["graficas_resultados"] +
                                    list(self.datos["graficas_optimizacion"])):
            self.assertTrue(svg)
            self.assertTrue(explicacion)
            self.assertEqual(ET.fromstring(svg).tag, SVG + "svg")
            self.assertNotRegex(svg.lower(), r"\bnan\b|\binf\b")

    def test_estado_ts_exactamente_el_del_solucionador(self):
        svg = svg_ts(self.ciclo)
        puntos = elementos(svg, "circle")
        self.assertEqual(len(puntos), 4)
        for i, punto in enumerate(puntos):
            self.assertEqual(punto.get("data-estado"), str(i + 1))
            self.assertAlmostEqual(float(punto.get("data-x")), self.ciclo["entropias"][i], places=8)
            self.assertAlmostEqual(float(punto.get("data-y")), self.ciclo["temperaturas"][i], places=6)
        self.assertIn('stroke-dasharray="7 5"', svg)

    def test_volumen_especifico_convierte_kpa_a_pa(self):
        svg = svg_pv(self.ciclo)
        puntos = elementos(svg, "circle")
        self.assertEqual(len(puntos), 4)
        for i, punto in enumerate(puntos):
            temp = self.ciclo["temperaturas"][i]
            presion_kpa = self.ciclo["presiones"][i]
            esperado = R_AIRE * temp / (1000 * presion_kpa)
            self.assertAlmostEqual(float(punto.get("data-x")), esperado, places=9)
            self.assertAlmostEqual(float(punto.get("data-y")), presion_kpa, places=6)
        self.assertIn("Volumen específico v [m³/kg]", svg)

    def test_cp_y_gamma_separados_con_estados_variables(self):
        tablas = self.datos["estados"]
        cp_svg, gamma_svg = svg_propiedades(tablas)
        self.assertIn("cp [J/(kg·K)]", cp_svg)
        self.assertIn("γ [–]", gamma_svg)
        for svg, funcion in ((cp_svg, cp), (gamma_svg, gamma)):
            puntos = elementos(svg, "circle")
            self.assertEqual(len(puntos), 4)
            for i, punto in enumerate(puntos):
                self.assertAlmostEqual(float(punto.get("data-x")), tablas[i]["T"], places=6)
                self.assertAlmostEqual(float(punto.get("data-y")), funcion(tablas[i]["T"]), places=5)
            self.assertIn(">200<", svg)
            self.assertIn(">2000<", svg)

    def test_barras_son_las_cinco_magnitudes_originales(self):
        svg = svg_balances(self.ciclo)
        self.assertIn("kJ/kg", svg)
        for clave in ("trabajo_compresor", "trabajo_turbina", "trabajo_neto",
                      "calor_aportado", "calor_rechazado"):
            barra = elementos(svg, "rect", **{"data-energia": clave})
            self.assertEqual(len(barra), 1)
            self.assertAlmostEqual(float(barra[0].get("data-valor")), self.ciclo[clave], places=7)
        self.assertAlmostEqual(self.ciclo["trabajo_neto"],
                               self.ciclo["trabajo_turbina"] -
                               self.ciclo["trabajo_compresor"], places=8)

    def test_ideal_y_configurado_utilizan_el_mismo_cp_variable(self):
        ideal = resolver_ciclo(DEFAULTS["T1"], DEFAULTS["T3"], DEFAULTS["rp"],
                               DEFAULTS["p1"], 1.0, 1.0, 0.0)
        svg = svg_comparacion(ideal, self.ciclo)
        for modelo, ciclo in (("ideal", ideal), ("configurado", self.ciclo)):
            for clave in ("trabajo_compresor", "trabajo_turbina", "trabajo_neto"):
                barras = elementos(svg, "rect", **{"data-modelo": modelo, "data-magnitud": clave})
                self.assertEqual(len(barras), 1)
                self.assertAlmostEqual(float(barras[0].get("data-valor")), ciclo[clave], places=7)
            barras = elementos(svg, "rect", **{"data-modelo": modelo, "data-magnitud": "rendimiento"})
            self.assertEqual(len(barras), 1)
            self.assertAlmostEqual(float(barras[0].get("data-valor")),
                                   100 * ciclo["rendimiento"], places=7)
        self.assertIn("Trabajos específicos [kJ/kg]", svg)
        self.assertIn("Rendimiento térmico [%]", svg)

    def test_no_motor_no_crea_barras_operativas_ni_falsa_comparacion(self):
        entradas = {**DEFAULTS, "rp": 1.0, "delta": 0.0}
        datos = preparar_resultados(entradas)
        self.assertFalse(datos["ciclo"]["viable"])
        self.assertEqual([g is not None for _, g, _ in datos["graficas_resultados"]],
                         [True, True, True, True, False, False])
        self.assertIn("no motor", datos["diagnostico_comparacion"])
        self.assertIsNone(svg_balances(datos["ciclo"]))
        self.assertIsNone(svg_comparacion(datos["ciclo"], self.ciclo))

    def test_excepcion_del_ideal_solo_anula_comparacion(self):
        with patch("graficas_cp_variable.resolver_ciclo", side_effect=EstadoFueraDeRango("fuera")):
            graficas, diagnostico = graficas_resultados(self.ciclo, self.datos["estados"], DEFAULTS)
        self.assertTrue(all(g for _, g, _ in graficas[:5]))
        self.assertIsNone(graficas[5][1])
        self.assertIn("no se puede resolver", diagnostico)

    def test_maximos_dibujados_proceden_de_2c(self):
        opt = self.datos["optimizacion"]
        trabajo, rendimiento, compromiso = [g[1] for g in self.datos["graficas_optimizacion"]]
        self.assertIn("escala logarítmica", trabajo)
        self.assertIn("escala logarítmica", rendimiento)
        for letra, svg in (("A", trabajo), ("B", rendimiento)):
            markers = elementos(svg, "circle", **{"data-estado": letra})
            self.assertEqual(len(markers), 1)
            self.assertAlmostEqual(float(markers[0].get("data-x")), opt[letra]["rp"], places=6)
        for letra in ("A", "B"):
            markers = elementos(compromiso, "circle", **{"data-estado": letra})
            self.assertEqual(len(markers), 1)
            self.assertAlmostEqual(float(markers[0].get("data-x")),
                                   opt[letra]["trabajo_neto"], places=6)
            self.assertAlmostEqual(float(markers[0].get("data-y")),
                                   100 * opt[letra]["rendimiento"], places=6)

    def test_supremo_abierto_no_se_marca_como_punto_B(self):
        entradas = {**DEFAULTS, "eta_c": 1.0, "eta_t": 1.0, "delta": 0.0}
        opt = estudiar_cp_variable(entradas["T1"], entradas["T3"], entradas["p1"],
                                   entradas["eta_c"], entradas["eta_t"], entradas["delta"])
        self.assertEqual(opt["B"]["tipo"], "supremo_frontera")
        graficas = graficas_optimizacion(curvas_optimizacion(entradas, opt), opt)
        self.assertEqual(len(graficas), 3)
        for _, svg, _ in graficas:
            self.assertFalse(elementos(svg, "circle", **{"data-estado": "B"}))

    def test_trazado_no_une_huecos_ni_rellena_muestras_invalidas(self):
        resultado = _tramos([(1, 1), None, (3, 2), (4, 4), None], lambda x, y: (x, y))
        self.assertEqual(resultado.count("<polyline"), 1)
        self.assertEqual(resultado.count("<circle"), 1)
        self.assertNotIn("1.000,1.000 3.000,2.000", resultado)

    def test_integracion_flask_usa_galeria_y_ampliacion_existentes(self):
        cliente = app.test_client()
        for accion in ("normal", "optimizar"):
            with self.subTest(accion=accion):
                respuesta = cliente.post(
                    "/", data={**{k: str(v) for k, v in DEFAULTS.items()}, "accion": accion}
                )
                self.assertEqual(respuesta.status_code, 200)
                html = respuesta.get_data(as_text=True)
                self.assertEqual(html.count('class="cp-figure"'), 9)
                self.assertIn('data-plot-viewer="cp-resultados"', html)
                self.assertIn('data-plot-viewer="cp-optimizacion"', html)
                self.assertIn("Diagrama P–v específico", html)
                self.assertIn("Compromiso trabajo–rendimiento", html)
        with (Path(__file__).resolve().parents[1] / "static/dashboard.js").open(encoding="utf-8") as archivo:
            js = archivo.read()
        self.assertIn("showModal()", js)
        self.assertIn("cloneNode(true)", js)


if __name__ == "__main__":
    unittest.main()
