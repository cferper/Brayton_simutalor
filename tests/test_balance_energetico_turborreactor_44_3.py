"""Milestone 44.3: magnitudes y cierres por kg de aire entrante."""

from pathlib import Path
from xml.etree import ElementTree
import unittest

from propiedades_aire import h
from turborreactor_web import (
    DEFAULTS_TURBO, datos_balance_energetico, preparar_vista_turborreactor,
    simular_turborreactor, svg_balance_energetico,
)


class BalanceEnergetico443(unittest.TestCase):
    def _caso(self, **cambios):
        return simular_turborreactor({**DEFAULTS_TURBO, **cambios})

    def test_compresor_trabajo_por_aire_y_entalpia_total(self):
        r = self._caso()
        b = datos_balance_energetico(r)
        c = r['compresor']
        self.assertAlmostEqual(b['compresor'], c['h2']-c['h1'], places=9)
        self.assertAlmostEqual(b['residuos']['compresor'], 0, places=9)

    def test_camara_balance_de_masa_y_combustible_efectivo(self):
        r = self._caso()
        b = datos_balance_energetico(r)
        f = r['combustor']['f']
        self.assertAlmostEqual(b['factor_masico'], 1+f)
        self.assertAlmostEqual(b['combustor'],
                               f*r['combustor']['eta_b']*r['combustor']['PCI'])
        self.assertAlmostEqual(r['compresor']['h2']+b['combustor'],
                               (1+f)*r['combustor']['h3'], places=8)

    def test_turbina_trabajo_gases_y_cierre_mecanico(self):
        r = self._caso()
        b = datos_balance_energetico(r)
        t = r['turbina']
        self.assertAlmostEqual(b['turbina'],
                               (1+b['f'])*(r['combustor']['h3']-t['h4']))
        self.assertAlmostEqual(b['eje_util'],
                               t['rendimiento_mecanico']*b['turbina'])
        self.assertAlmostEqual(b['eje_util'], b['compresor'], places=8)
        self.assertGreater(b['turbina'], b['eje_util'])

    def test_entalpia_cinetica_tobera_convergente_y_cd(self):
        for cambios in ({}, {'tipo_tobera':'convergente_divergente','epsilon':'1.5'}):
            with self.subTest(cambios=cambios):
                r = self._caso(**cambios)
                b = datos_balance_energetico(r)
                self.assertIsNotNone(b['tobera_cinetica'])
                V = r['tobera']['velocidad_salida']
                self.assertAlmostEqual(b['tobera_cinetica'], (1+b['f'])*V**2/2000)
                self.assertAlmostEqual(b['tobera_cinetica'],
                                       (1+b['f'])*(r['turbina']['h4']-
                                                  h(r['tobera']['temperatura_salida'])),places=7)

    def test_cinco_residuos_consistentes_en_distintos_regimenes(self):
        for cambios in ({}, {'mach':'0.7'}, {'T3':'1700'}, {'eta_c':'0.9'},
                        {'eta_t':'0.85'},
                        {'tipo_tobera':'convergente_divergente','epsilon':'1.5'}):
            with self.subTest(cambios=cambios):
                d = datos_balance_energetico(self._caso(**cambios))
                for valor in d['residuos'].values():
                    if valor is not None:
                        self.assertLess(abs(valor),1e-7)

    def test_sin_salida_fisica_no_inventa_energia_cinetica(self):
        r = self._caso()
        r['tobera'] = None
        b = datos_balance_energetico(r)
        self.assertIsNone(b['tobera_cinetica'])
        self.assertIsNone(b['residuos']['tobera'])
        for clave in ('compresor','combustor','turbina','eje'):
            self.assertIsNotNone(b['residuos'][clave])
        self.assertIn('No disponible', svg_balance_energetico(b))

    def test_incoherencia_energetica_no_se_oculta(self):
        r = self._caso()
        r['combustor']['aporte_quimico_efectivo'] += 20
        with self.assertRaises(ValueError):
            datos_balance_energetico(r)

    def test_svg_y_unidades_y_leyenda(self):
        r = self._caso()
        svg = svg_balance_energetico(datos_balance_energetico(r))
        ElementTree.fromstring(svg)
        self.assertIn('kJ/kg de aire entrante', svg)
        for label in ('Compresor','Cámara','Turbina','Tobera'):
            self.assertIn(label, svg)

    def test_cambio_parametros_actualiza_y_conserva_graficas(self):
        vista1 = preparar_vista_turborreactor(self._caso())
        vista2 = preparar_vista_turborreactor(self._caso(T3='1700'))
        self.assertNotEqual(vista1['svg_balance_energetico'],
                            vista2['svg_balance_energetico'])
        for vista in (vista1, vista2):
            for clave in ('svg_empuje', 'svg_ts', 'svg_mach_tobera',
                          'svg_presion_tobera', 'svg_balance_energetico'):
                self.assertIn('<svg ', vista[clave])

    def test_integracion_plantilla_y_seis_apartados(self):
        html = (Path(__file__).resolve().parents[1] / 'templates' /
                'turborreactor.html').read_text(encoding='utf-8')
        self.assertIn('vista.svg_balance_energetico|safe', html)
        self.assertIn('vista.balance_energetico.residuos[clave]', html)
        self.assertIn('no sumables entre sí', html)
        for nombre in ('configuracion','resultados','estaciones','graficas',
                       'sensibilidad','mapa'):
            self.assertIn('data-edu-tabs="'+nombre+'"', html)


if __name__ == '__main__':
    unittest.main()
