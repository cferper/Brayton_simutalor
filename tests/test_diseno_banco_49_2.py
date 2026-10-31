"""Comprobaciones estáticas del diseño 49.2 sin depender de Flask."""

from pathlib import Path
import unittest


RAIZ = Path(__file__).resolve().parents[1]


class DisenoBanco49(unittest.TestCase):
    def test_una_sola_fuente_para_controles_y_resultados(self):
        plantilla = (RAIZ / "templates/turborreactor.html").read_text(encoding="utf-8")
        self.assertEqual(plantilla.count('id="turbo-form"'), 1)
        self.assertEqual(plantilla.count('id="turbo-live"'), 1)
        # Los identificadores se generan en un único bucle Jinja para ambos campos.
        self.assertEqual(plantilla.count('id="{{ nombre }}_deslizador"'), 1)
        self.assertEqual(plantilla.count('id="{{ nombre }}_lectura"'), 1)
        self.assertIn("nombre in ('mach','T3')", plantilla)
        self.assertIn('turbo-bank-active-fields', plantilla)
        self.assertIn('turbo-bank-other-field', plantilla)

    def test_modo_clasico_no_recibe_maquetacion_del_banco(self):
        css = (RAIZ / "static/turborreactor.css").read_text(encoding="utf-8")
        self.assertIn('data-interfaz="interactivo"', css)
        self.assertIn('grid-template-columns:minmax(270px,.75fr) minmax(0,1.6fr)', css)
        self.assertIn('@media(max-width:900px)', css)
        self.assertIn('position:static;max-height:none', css)

    def test_api_y_graficas_compartidas_sin_duplicar(self):
        plantilla = (RAIZ / "templates/turborreactor.html").read_text(encoding="utf-8")
        script = (RAIZ / "static/turborreactor_interactivo.js").read_text(encoding="utf-8")
        for modo in ('impuesto', 'fijo', 'acoplado'):
            self.assertIn(f'value="{modo}"', plantilla)
        for grafica in ('mach', 'presion', 'geometria'):
            self.assertIn(f'data-live-plot="{grafica}"', plantilla)
        self.assertIn("'velocidad_salida_m_s'", plantilla)
        self.assertIn('"velocidad_salida_m_s":tobera.get("velocidad_salida")',
                      (RAIZ / "web_app.py").read_text(encoding="utf-8"))
        self.assertIn("'velocidad_salida_m_s'", script)
        self.assertIn("fetcher('/api/turborreactor/simular'", script)
        self.assertIn('controlador.cambiar()', script)


if __name__ == "__main__":
    unittest.main()
