"""M50.1: los datos T–s llegan del servidor y el laboratorio no añade endpoints."""

import unittest
from pathlib import Path

from web_app import app


ROOT = Path(__file__).resolve().parents[1]


class LaboratorioComparativo50_1(unittest.TestCase):
    def test_banco_ofrece_laboratorio_sin_alterar_controles(self):
        with app.test_client() as cliente:
            pagina = cliente.get('/turborreactor/interactivo').get_data(as_text=True)
            clasico = cliente.get('/turborreactor').get_data(as_text=True)
        self.assertIn('data-lab-action="save"', pagina)
        self.assertIn('data-lab-chart="ts"', pagina)
        self.assertIn('laboratorio_comparativo_50_1.js', pagina)
        self.assertNotIn('data-lab-action="save"', clasico)
        for clave in ('id="mach"', 'id="T3"', 'data-bank-mode="acoplado"',
                      'data-study49-view="estudios"', 'turbo-reset-design-geometry'):
            self.assertIn(clave, pagina)

    def test_no_crea_solicitador_ni_solver_en_el_cliente(self):
        js = (ROOT/'static/laboratorio_comparativo_50_1.js').read_text(encoding='utf-8')
        principal = (ROOT/'static/turborreactor_interactivo.js').read_text(encoding='utf-8')
        self.assertNotIn('fetch(', js)
        self.assertNotIn('/api/turborreactor/simular', js)
        self.assertEqual(principal.count("fetcher('/api/turborreactor/simular'"),1)

    def test_estaciones_reales_incluyen_entropia(self):
        from turborreactor_web import estaciones_turborreactor, simular_turborreactor
        # La función pública admite el conjunto de parámetros predeterminado.
        from turborreactor_web import DEFAULTS_TURBO
        resultado=simular_turborreactor(dict(DEFAULTS_TURBO))
        estados=estaciones_turborreactor(resultado)
        for estado in estados:
            if estado['T'] is not None and estado['p'] is not None:
                self.assertIsInstance(estado['s'],float)
        self.assertEqual([e['id'] for e in estados if e['tipo']=='Remanso'],
                         ['pt2','pt3','pt4','pt5'])


if __name__=='__main__':
    unittest.main()
