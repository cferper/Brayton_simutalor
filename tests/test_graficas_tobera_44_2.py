"""Milestone 44.2: representaciones discretas de Mach y presión estática."""

from pathlib import Path
from xml.etree import ElementTree
import unittest

from tobera_convergente_divergente_cp import resolver_tobera_convergente_divergente
from turborreactor_web import (
    DEFAULTS_TURBO, datos_tobera_graficas, preparar_vista_turborreactor,
    simular_turborreactor, svg_estados_tobera,
)


class VisualizacionTobera442(unittest.TestCase):
    def _motor(self, **cambios):
        return simular_turborreactor({**DEFAULTS_TURBO, **cambios})

    def _caso_directo_cd(self, pamb):
        n = resolver_tobera_convergente_divergente(1200, 500, pamb, 1.5)
        return {'tobera': n, 'diagnosticos': {'tipo_tobera': 'convergente_divergente'},
                'ambiente': {'presion': pamb}}

    def test_convergente_bloqueada_solo_salida_calculada(self):
        motor = self._motor()
        d = datos_tobera_graficas(motor)
        self.assertEqual(d['tipo'], 'convergente')
        self.assertEqual(d['regimen'], 'bloqueado')
        self.assertEqual(len(d['estados']), 1)
        self.assertEqual(d['estados'][0]['nombre'], 'Salida = garganta')
        self.assertAlmostEqual(d['estados'][0]['mach'], 1, places=7)
        self.assertEqual(d['estados'][0]['presion'], motor['tobera']['presion_salida'])

    def test_cd_supersonica_bloqueada_con_garganta_y_salida(self):
        r = self._caso_directo_cd(40)
        d = datos_tobera_graficas(r)
        self.assertEqual(d['regimen'], 'supersonico_ideal')
        self.assertEqual([e['papel'] for e in d['estados']], ['garganta', 'salida'])
        self.assertAlmostEqual(d['estados'][0]['mach'], 1, places=7)
        self.assertGreater(d['estados'][-1]['mach'], 1)
        self.assertLess(d['estados'][-1]['presion'], d['estados'][0]['presion'])

    def test_cd_subsonica_no_inventa_mach_uno(self):
        r = self._caso_directo_cd(480)
        d = datos_tobera_graficas(r)
        self.assertEqual(d['regimen'], 'subsonico_no_bloqueado')
        self.assertLess(d['estados'][0]['mach'], 1)
        self.assertLess(d['estados'][1]['mach'], 1)
        self.assertAlmostEqual(d['estados'][-1]['presion'], 480, places=6)

    def test_choque_interno_muestra_dos_lados_distintos(self):
        r = self._caso_directo_cd(350)
        d = datos_tobera_graficas(r)
        self.assertEqual(d['regimen'], 'choque_normal_interno')
        self.assertEqual([e['papel'] for e in d['estados']],
                         ['garganta', 'choque_antes', 'choque_despues', 'salida'])
        antes, despues = d['estados'][1:3]
        self.assertGreater(antes['mach'], 1)
        self.assertLess(despues['mach'], 1)
        self.assertGreater(despues['presion'], antes['presion'])
        self.assertEqual(antes['presion'], r['tobera']['choque_normal']['p1'])
        self.assertEqual(despues['presion'], r['tobera']['choque_normal']['p2'])

    def test_choque_en_salida_identifica_lados_y_salida(self):
        base = self._caso_directo_cd(100)
        ps = base['tobera']['umbral_choque_salida_aproximado']
        r = self._caso_directo_cd(ps)
        self.assertEqual(r['tobera']['regimen'], 'choque_normal_salida')
        d = datos_tobera_graficas(r)
        self.assertEqual(d['estados'][-2]['papel'], 'choque_despues')
        self.assertAlmostEqual(d['estados'][-2]['presion'],
                               d['estados'][-1]['presion'], places=5)

    def test_sin_expansion_o_salida_no_resuelta_no_grafica_ceros(self):
        r = self._motor()
        r['tobera'] = None
        self.assertIsNone(datos_tobera_graficas(r))
        r = self._caso_directo_cd(350)
        r['tobera']['presion_salida'] = None
        self.assertIsNone(datos_tobera_graficas(r))
        self.assertIsNone(svg_estados_tobera(None, 'mach'))

    def test_ambos_svg_comparten_estaciones_y_referencias(self):
        d = datos_tobera_graficas(self._caso_directo_cd(350))
        for magnitud, texto in [('mach', 'M = 1'), ('presion', 'p∞ ambiente')]:
            svg = svg_estados_tobera(d, magnitud)
            ElementTree.fromstring(svg)
            self.assertIn(texto, svg)
            for e in d['estados']:
                self.assertIn(e[magnitud].__format__('.3f'), svg)
            self.assertIn('Estados discretos', svg)
        with self.assertRaises(ValueError):
            svg_estados_tobera(d, 'presion_total')

    def test_cambio_de_parametros_y_preservacion_44_1(self):
        vista1 = preparar_vista_turborreactor(self._motor())
        vista2 = preparar_vista_turborreactor(self._motor(mach='0.7'))
        self.assertNotEqual(vista1['svg_presion_tobera'], vista2['svg_presion_tobera'])
        for vista in (vista1, vista2):
            self.assertIn('<svg ', vista['svg_ts'])
            self.assertIn('<svg ', vista['svg_empuje'])
            self.assertIn('<svg ', vista['svg_mach_tobera'])
            self.assertIn('<svg ', vista['svg_presion_tobera'])

    def test_plantilla_conserva_seis_secciones_y_paneles(self):
        texto = (Path(__file__).resolve().parents[1] / 'templates' /
                 'turborreactor.html').read_text(encoding='utf-8')
        for n in ('configuracion', 'resultados', 'estaciones', 'graficas',
                  'sensibilidad', 'mapa'):
            self.assertIn(f'data-edu-tabs="{n}"', texto)
        for variable in ('svg_empuje', 'svg_ts', 'svg_mach_tobera',
                         'svg_presion_tobera'):
            self.assertIn('vista.'+variable+'|safe', texto)


if __name__ == '__main__':
    unittest.main()
