"""Milestone 49.7: presencia, aislamiento y accesibilidad del esquema."""

from pathlib import Path
import unittest

from web_app import app


ROOT = Path(__file__).resolve().parents[1]


class EsquemaEducativo49_7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_banco_tiene_seis_partes_accesibles(self):
        html = self.client.get('/turborreactor/interactivo').get_data(as_text=True)
        self.assertIn('turbo-engine-educational', html)
        for nombre in ('difusor', 'compresor', 'camara', 'turbina', 'eje', 'tobera'):
            self.assertIn(f'data-engine-part="{nombre}"', html)
        self.assertEqual(html.count('data-engine-part='), 6)
        self.assertIn('aria-pressed="true" class="is-selected"', html)
        self.assertEqual(html.count('focusable="true"'), 6)

    def test_clasico_sin_esquema_y_controles_existentes(self):
        banco = self.client.get('/turborreactor/interactivo').get_data(as_text=True)
        clasico = self.client.get('/turborreactor').get_data(as_text=True)
        self.assertNotIn('turbo-engine-educational', clasico)
        for token in ('id="mach"', 'id="T3"', 'id="mach_deslizador"',
                      'id="T3_deslizador"', 'data-bank-mode="impuesto"',
                      'data-bank-mode="fijo"', 'data-bank-mode="acoplado"',
                      'id="turbo-reset-design-geometry"', 'data-plot-tab="ts"',
                      'data-study49-view="estudios"'):
            self.assertIn(token, banco)

    def test_seleccion_no_tiene_api_propia(self):
        js = (ROOT/'static/turborreactor_interactivo.js').read_text(encoding='utf-8')
        inicio = js.index('function iniciarEsquemaEducativo49_7(')
        fin = js.index('function inicializar48(', inicio)
        seleccion = js[inicio:fin]
        self.assertNotIn('fetch(', seleccion)
        self.assertNotIn('controlador.cambiar(', seleccion)
        self.assertEqual(js.count("fetcher('/api/turborreactor/simular'"), 1)


if __name__ == '__main__':
    unittest.main()
