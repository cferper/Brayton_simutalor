"""Botón de referencia geométrica M49.6 sin alterar el modelo acoplado."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import unittest

from acoplamiento_motor_mapa_47 import punto_diseno_47
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor


ROOT = Path(__file__).resolve().parents[1]


class GeometriaDiseno49_6(unittest.TestCase):
    def test_referencia_procede_del_modelo_y_no_de_mach_t3(self):
        r = punto_diseno_47()
        ag, ae = r['area_garganta_diseno'], r['area_salida_diseno']
        self.assertGreater(ag, 0)
        self.assertEqual(ag, ae)  # Diseño convergente, no C-D optimizado.
        self.assertAlmostEqual(ag, 0.0473481164, places=9)

    def test_mismo_caso_con_areas_de_referencia_converge(self):
        r = punto_diseno_47()
        parametros = dict(DEFAULTS_TURBO, modo_caudal='acoplado',
                         mach='0.838', T3='1704',
                         tipo_tobera='convergente_divergente',
                         area_garganta_fija=str(r['area_garganta_diseno']),
                         area_salida_fija=str(r['area_salida_diseno']))
        solucion = simular_turborreactor(parametros)
        self.assertTrue(solucion['motor_acoplado']['disponible'])
        self.assertEqual(parametros['mach'], '0.838')
        self.assertEqual(parametros['T3'], '1704')

    def test_control_solo_interactivo_y_modo_c(self):
        plantilla = (ROOT/'templates/turborreactor.html').read_text(encoding='utf8')
        css = (ROOT/'static/turborreactor.css').read_text(encoding='utf8')
        js = (ROOT/'static/turborreactor_interactivo.js').read_text(encoding='utf8')
        self.assertIn('id="turbo-reset-design-geometry"', plantilla)
        self.assertIn("{% if interfaz=='interactivo' %}<div class=\"turbo-design-geometry\"", plantilla)
        self.assertIn('[data-bank-mode="acoplado"]', css)
        self.assertIn('selectorModo.value!==\'acoplado\'', js)
        self.assertIn('garganta.value!==anteriores[0]', js)
        self.assertIn('controlador.cambiar()', js)
        self.assertIn('/api/turborreactor/geometria-diseno', js)
        self.assertIn('#estudio49', css)

    @unittest.skipUnless(shutil.which('node'), 'Node.js no disponible')
    def test_actualizacion_de_solo_dos_campos_y_validacion(self):
        codigo = '''const assert=require('node:assert/strict');
const f=require(process.argv[1]).aplicarGeometriaDiseno49;
const g={value:'0.5'},e={value:'3.5'},mach={value:'0.838'};
assert.throws(()=>f(g,e,{area_garganta_m2:-1,area_salida_m2:5}));
assert.equal(g.value,'0.5');assert.equal(e.value,'3.5');
f(g,e,{area_garganta_m2:0.0473481164,area_salida_m2:0.0473481164});
assert.equal(g.value,'0.0473481164');assert.equal(e.value,'0.0473481164');
assert.equal(mach.value,'0.838');
g.value='0.08';assert.equal(g.value,'0.08');'''
        r = subprocess.run(['node', '-e', codigo,
                            str(ROOT/'static/turborreactor_interactivo.js')],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    @unittest.skipUnless(importlib.util.find_spec('flask'), 'Flask no instalado')
    def test_http_referencia_y_rutas(self):
        from web_app import app
        cliente = app.test_client()
        respuesta = cliente.get('/api/turborreactor/geometria-diseno')
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.get_json()
        modelo = punto_diseno_47()
        self.assertEqual(datos['area_garganta_m2'], modelo['area_garganta_diseno'])
        self.assertEqual(datos['area_salida_m2'], modelo['area_salida_diseno'])
        for ruta in ('/turborreactor/interactivo', '/turborreactor', '/brayton'):
            self.assertEqual(cliente.get(ruta).status_code, 200)


if __name__ == '__main__':
    unittest.main()
