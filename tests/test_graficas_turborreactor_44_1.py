"""Milestone 44.1: coherencia entre los gráficos y los estados científicos."""

from math import isclose
from pathlib import Path
import unittest
from xml.etree import ElementTree

from propiedades_aire import s
from turborreactor_web import (
    DEFAULTS_TURBO, datos_empuje_grafica, datos_ts_turborreactor,
    estaciones_turborreactor, preparar_vista_turborreactor,
    simular_turborreactor, svg_descomposicion_empuje, svg_ts_turborreactor,
)


class GraficasTurbojet441(unittest.TestCase):
    def _caso(self, **cambios):
        valores = dict(DEFAULTS_TURBO)
        valores.update(cambios)
        return simular_turborreactor(valores)

    def test_componentes_y_neto_coinciden_con_solucionador(self):
        for ajustes in ({}, {'mach': '0.7'},
                        {'tipo_tobera': 'convergente_divergente', 'epsilon': '1.5'}):
            with self.subTest(ajustes=ajustes):
                r = self._caso(**ajustes)
                componentes = datos_empuje_grafica(r)
                self.assertIsNotNone(componentes)
                self.assertTrue(isclose(sum(componentes[:3]), componentes[3],
                                        rel_tol=1e-12, abs_tol=1e-10))
                self.assertAlmostEqual(componentes[0], r['prestaciones']['empuje_especifico_salida'])
                self.assertAlmostEqual(componentes[1], -r['remanso']['velocidad_vuelo'])
                self.assertAlmostEqual(componentes[2], r['prestaciones']['empuje_especifico_presion'])
                ElementTree.fromstring(svg_descomposicion_empuje(r))

    def test_salida_no_resuelta_no_produce_barras_ficticias(self):
        r = self._caso(tipo_tobera='convergente_divergente', epsilon='6')
        if r['prestaciones']['empuje_especifico_neto'] is None:
            self.assertIsNone(datos_empuje_grafica(r))
            self.assertIsNone(svg_descomposicion_empuje(r))
        else:
            # El régimen real determina si hay salida: no se fuerza None.
            self.assertIsNotNone(datos_empuje_grafica(r))
        r['prestaciones']['empuje_especifico_presion'] = None
        self.assertIsNone(svg_descomposicion_empuje(r))

    def test_incoherencia_de_prestaciones_no_se_oculta(self):
        r = self._caso()
        r['prestaciones']['empuje_especifico_neto'] += 10
        with self.assertRaises(ValueError):
            datos_empuje_grafica(r)

    def test_entropia_cp_variable_estados_totales_y_salida_estatica(self):
        for ajustes in ({}, {'mach': '0.7'},
                        {'tipo_tobera': 'convergente_divergente', 'epsilon': '1.5'}):
            with self.subTest(ajustes=ajustes):
                r = self._caso(**ajustes)
                estaciones = estaciones_turborreactor(r)
                puntos = datos_ts_turborreactor(estaciones)
                remanso = [e for e in estaciones if e['tipo'] == 'Remanso']
                self.assertEqual(len(remanso), 4)
                for punto, estado in zip(puntos, remanso):
                    self.assertEqual(punto[3], 'Remanso')
                    self.assertAlmostEqual(punto[1], s(estado['T'], estado['p']))
                    self.assertEqual(punto[2], estado['T'])
                if r['tobera'] and r['tobera']['temperatura_salida'] is not None:
                    self.assertEqual(puntos[-1][0], 'E')
                    self.assertEqual(puntos[-1][3], 'Estático')
                ElementTree.fromstring(svg_ts_turborreactor(estaciones))

    def test_salida_ausente_se_excluye_del_ts(self):
        r = self._caso()
        r['tobera'] = None
        estaciones = estaciones_turborreactor(r)
        self.assertEqual(len(datos_ts_turborreactor(estaciones)), 4)
        self.assertNotIn('Tobera (estático)', svg_ts_turborreactor(estaciones))

    def test_vista_contiene_ambos_svg_actualizados(self):
        estatico = preparar_vista_turborreactor(self._caso())
        vuelo = preparar_vista_turborreactor(self._caso(mach='0.7'))
        for vista in (estatico, vuelo):
            self.assertIn('<svg ', vista['svg_ts'])
            self.assertIn('N/(kg/s de aire)', vista['svg_empuje'])
        self.assertNotEqual(estatico['svg_empuje'], vuelo['svg_empuje'])
        self.assertNotEqual(estatico['svg_ts'], vuelo['svg_ts'])

    def test_plantilla_integra_las_dos_graficas_en_paneles_previos(self):
        plantilla = (Path(__file__).resolve().parents[1] /
                     'templates' / 'turborreactor.html').read_text(encoding='utf-8')
        self.assertIn('vista.svg_empuje|safe', plantilla)
        self.assertIn('vista.svg_ts|safe', plantilla)
        self.assertLess(plantilla.index('id="resultados"'),
                        plantilla.index('vista.svg_empuje|safe'))
        self.assertLess(plantilla.index('id="graficas"'),
                        plantilla.index('vista.svg_ts|safe'))
        self.assertIn('no son trayectorias continuas calculadas', plantilla)
        self.assertIn('No es empuje absoluto', plantilla)


if __name__ == '__main__':
    unittest.main()
