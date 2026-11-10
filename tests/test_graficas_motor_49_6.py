"""M49.6: datos del solucionador y comportamiento del visor sin Flask."""

from pathlib import Path
import unittest

from perfil_axial_tobera_conica import svg_perfil_axial
from turborreactor_web import svg_trabajos_motor, svg_evolucion


BASE = Path(__file__).resolve().parents[1]


class GraficasMotor49_6(unittest.TestCase):
    def test_trabajos_usan_misma_base_y_no_restan_sin_sentido(self):
        datos = {'compresor': 245., 'turbina': 260., 'eje_util': 245.}
        svg = svg_trabajos_motor(datos)
        self.assertIn('245.00', svg)
        self.assertIn('260.00', svg)
        self.assertIn('kJ/kg de aire', svg)
        self.assertIn('rendimiento mecánico', svg)
        self.assertNotIn('trabajo neto', svg.lower())
        self.assertIsNone(svg_trabajos_motor({**datos, 'turbina': float('nan')}))

    def test_estaciones_totales_solo_cuatro(self):
        estados = [{'tipo': 'Remanso', 'nombre': str(i), 'T': 300+i*100,
                    'p': 100+i*20} for i in range(4)]
        estados.append({'tipo': 'Estático', 'nombre': 'Salida', 'T': 50, 'p': 10})
        for clave in ('T', 'p'):
            svg = svg_evolucion(estados, clave, 'Total', 'K' if clave == 'T' else 'kPa')
            self.assertEqual(svg.count('data-plot-info='), 4)
            self.assertNotIn('50.0', svg)

    def test_choque_separa_temperatura_y_velocidad(self):
        a = {'x': .5, 'temperatura': 300., 'velocidad': 700.}
        b = {'x': .5, 'temperatura': 400., 'velocidad': 350.}
        perfil = {'disponible': True, 'segmentos': ((
            {'x': 0., 'temperatura': 500., 'velocidad': 600.}, a),
            (b, {'x': 1., 'temperatura': 450., 'velocidad': 250.})),
            'choque': (a, b), 'x_choque': .5, 'longitud_divergente': 1.}
        for magnitud, unidad in [('temperatura', 'K'), ('velocidad', 'm/s')]:
            svg = svg_perfil_axial(perfil, magnitud)
            self.assertEqual(svg.count('<polyline'), 2)
            self.assertIn('Choque: antes', svg)
            self.assertIn('Choque: después', svg)
            self.assertIn(unidad, svg)
        self.assertIsNone(svg_perfil_axial({'disponible': False}, 'temperatura'))

    def test_interfaz_conserva_unica_api_y_estudios(self):
        plantilla = (BASE/'templates/turborreactor.html').read_text(encoding='utf-8')
        script = (BASE/'static/turborreactor_interactivo.js').read_text(encoding='utf-8')
        for grupo in ('ciclo', 'tobera', 'prestaciones', 'estudios'):
            self.assertIn('data-plot-group-button="'+grupo+'"', plantilla)
        for grafica in ('svg_temperaturas', 'svg_presiones', 'svg_trabajos_motor',
                        'svg_balance_energetico', 'svg_temperatura_axial',
                        'svg_velocidad_axial', 'svg_empuje'):
            self.assertIn(grafica, script)
        self.assertIn('[data-study49-view="estudios"]', script)
        self.assertEqual(script.count("fetcher('/api/turborreactor/simular'"), 1)


if __name__ == '__main__':
    unittest.main()
