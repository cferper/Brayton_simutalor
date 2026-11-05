"""Interacciones M49.4: puntos calculados y compatibilidad del visor."""

from pathlib import Path
import re
import shutil
import subprocess
import unittest

from geometria_tobera_conica import svg_geometria_conica
from perfil_axial_tobera_conica import svg_perfil_axial
from turborreactor_web import svg_ts_turborreactor


ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')


class Graficas49_4(unittest.TestCase):
    def test_estados_ts_discretos_sin_inventar_series(self):
        estados = [
            {"tipo": "Remanso", "nombre": f"Estación {i}", "T": t, "p": p}
            for i, (t, p) in enumerate(((300, 100), (500, 900), (1400, 870), (840, 220)), 1)
        ]
        dibujo = svg_ts_turborreactor(estados)
        self.assertEqual(dibujo.count('data-plot-info='), 4)
        self.assertIn('kJ/(kg·K)', dibujo)
        self.assertIn('uniones esquemáticas', dibujo)

    def test_perfil_choque_separado_y_dos_valores_misma_x(self):
        anterior = {"x": 0.5, "mach": 2.0, "presion": 55.0}
        posterior = {"x": 0.5, "mach": 0.6, "presion": 180.0}
        perfil = {"disponible": True, "segmentos": ((
            {"x": 0.0, "mach": 1.0, "presion": 100.0}, anterior), (
            posterior, {"x": 1.0, "mach": 0.4, "presion": 210.0})),
            "choque": (anterior, posterior), "x_choque": 0.5,
            "longitud_divergente": 1.0, "p_ambiente": 100.0}
        for clave, saltos in (("mach", ("Mach=2", "Mach=0.6")),
                              ("presion", ("p=55", "p=180"))):
            svg = svg_perfil_axial(perfil, clave)
            self.assertEqual(svg.count('<polyline'), 2)
            self.assertIn('Choque: antes', svg)
            self.assertIn('Choque: después', svg)
            for salto in saltos:
                self.assertIn(salto, svg)

    def test_geometria_real_y_escala_uniforme(self):
        geometria = {"disponible": True, "radio_garganta": 0.1,
                     "radio_salida": 0.2, "longitud_divergente": 0.5,
                     "angulo_grados": 11.309932474}
        svg = svg_geometria_conica(geometria)
        self.assertIn('Garganta: x=0 m; radio=0.1 m', svg)
        self.assertIn('Salida: x=0.5 m; radio=0.2 m', svg)
        self.assertEqual(svg.count('data-plot-info='), 2)

    def test_controles_y_sin_api_adicional(self):
        html = (ROOT / 'templates/turborreactor.html').read_text(encoding='utf-8')
        js = (ROOT / 'static/turborreactor_interactivo.js').read_text(encoding='utf-8')
        for accion in ('in', 'out', 'reset', 'svg', 'png'):
            self.assertIn(f'data-plot-action="{accion}"', html)
        self.assertIn("explorador?.restaurar()", js)
        self.assertIn("if(!evento.ctrlKey", js)
        self.assertEqual(js.count("fetcher('/api/turborreactor/simular'"), 1)
        self.assertNotIn('cdn.', js)

    @unittest.skipUnless(NODE,
                         'Node.js no disponible')
    def test_limites_zoom_en_node(self):
        ruta = ROOT / 'static/turborreactor_interactivo.js'
        script = ("const v=require(process.argv[1]).escalaGrafica49; "
                  "if(v(1,.5)!==1||v(4,2)!==4||v(2,1.25)!==2.5)process.exit(1)")
        resultado = subprocess.run([NODE, '-e', script, str(ruta)], capture_output=True,
                                   text=True, check=False)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)


if __name__ == '__main__':
    unittest.main()
