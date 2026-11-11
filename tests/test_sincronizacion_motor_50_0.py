"""M50.0: identidades de estaciones y anotaciones de gráficas existentes."""

import unittest

from turborreactor_web import (svg_balance_energetico, svg_evolucion,
                              svg_estados_tobera, svg_trabajos_motor, svg_ts_turborreactor)


class Sincronizacion50_0(unittest.TestCase):
    def setUp(self):
        self.estados = [
            {'id': id_, 'nombre': nombre, 'tipo': 'Remanso', 'T': T, 'p': p}
            for id_, nombre, T, p in (
                ('pt2', 'Difusor', 300, 100), ('pt3', 'Compresor', 570, 900),
                ('pt4', 'Cámara', 1500, 850), ('pt5', 'Turbina', 820, 240))
        ] + [{'id':'salida','nombre':'Salida de tobera','tipo':'Estático','T':620,'p':110}]

    def test_puntos_totales_y_diagrama_ts(self):
        for clave in ('T', 'p'):
            svg = svg_evolucion(self.estados, clave, clave, 'K')
            for id_ in ('pt2', 'pt3', 'pt4', 'pt5'):
                self.assertIn(f'data-engine-station="{id_}"', svg)
            self.assertNotIn('data-engine-station="salida"', svg)
        ts = svg_ts_turborreactor(self.estados)
        self.assertIn('data-engine-station="salida"', ts)
        self.assertEqual(ts.count('data-engine-station='), 5)

    def test_balance_y_eje_no_se_confunden_con_estaciones(self):
        trabajos = svg_trabajos_motor({'compresor':250,'turbina':270,'eje_util':250})
        self.assertIn('data-engine-work="eje"', trabajos)
        self.assertNotIn('data-engine-station', trabajos)
        balance = svg_balance_energetico({'compresor':250,'combustor':940,
                                         'turbina':270,'tobera_cinetica':300})
        for pieza in ('compresor','camara','turbina','tobera'):
            self.assertIn(f'data-engine-energy="{pieza}"', balance)

    def test_garganta_y_salida_solo_si_existen(self):
        datos={'estados':[
            {'papel':'garganta','nombre':'Garganta','mach':1.,'presion':300.},
            {'papel':'salida','nombre':'Salida','mach':2.,'presion':100.}],
            'ambiente':101.3}
        svg=svg_estados_tobera(datos,'mach')
        self.assertIn('data-engine-station="garganta"',svg)
        self.assertIn('data-engine-station="salida"',svg)
        solo={'estados':[datos['estados'][1]],'ambiente':101.3}
        self.assertNotIn('data-engine-station="garganta"',svg_estados_tobera(solo,'presion'))


if __name__ == '__main__':
    unittest.main()
