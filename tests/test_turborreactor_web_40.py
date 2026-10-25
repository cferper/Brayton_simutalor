"""Milestone 40: contratos HTTP, formulario y fidelidad del presentador web."""

import unittest
from unittest.mock import patch

from web_app import app
from turborreactor_web import (DEFAULTS_TURBO, EJEMPLOS_TURBO,
                              leer_turborreactor, simular_turborreactor,
                              estaciones_turborreactor, preparar_vista_turborreactor)


class TurborreactorWeb40(unittest.TestCase):
    def setUp(self):
        self.cliente = app.test_client()

    def _post(self, **variaciones):
        return self.cliente.post("/turborreactor", data={**DEFAULTS_TURBO, **variaciones})

    def test_get_200_formulario_sin_calculo(self):
        with patch("web_app.simular_turborreactor") as sim:
            respuesta = self.cliente.get("/turborreactor")
        self.assertEqual(respuesta.status_code, 200)
        sim.assert_not_called()
        self.assertIn(b'"/turborreactor"', respuesta.data)
        self.assertIn(b'Pendiente de c', respuesta.data)

    def test_campos_unidades_y_ayudas(self):
        pagina = self.cliente.get("/turborreactor").get_data(as_text=True)
        for nombre in DEFAULTS_TURBO:
            self.assertIn('name="'+nombre+'"', pagina)
        for unidad in ('kPa', 'kJ/kg', '%', 'Mach', 'ISA'):
            self.assertIn(unidad, pagina)
        self.assertIn('data-ejemplo="isa"', pagina)

    def test_post_estatico_reproduce_cientifico(self):
        esperado = simular_turborreactor(DEFAULTS_TURBO)
        respuesta = self._post()
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(f'{esperado["prestaciones"]["empuje_especifico_neto"]:.5g}', respuesta.get_data(as_text=True))
        self.assertIn('bloqueado', respuesta.get_data(as_text=True))

    def test_post_mach_07(self):
        respuesta = self._post(mach="0.7")
        self.assertEqual(respuesta.status_code, 200)
        texto = respuesta.get_data(as_text=True)
        esperado = simular_turborreactor({**DEFAULTS_TURBO, "mach": "0.7"})
        self.assertIn(f'{esperado["prestaciones"]["TSFC_kg_N_h"]:.5g}', texto)

    def test_post_isa_diez_km(self):
        respuesta = self.cliente.post('/turborreactor', data=EJEMPLOS_TURBO['isa'])
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('bloqueado', respuesta.get_data(as_text=True))
        self.assertIn('value="10000"', respuesta.get_data(as_text=True))

    def test_delta_porcentaje_se_convierte_antes_del_solver(self):
        with patch('turborreactor_web.resolver_turborreactor_con_combustible') as solucionador:
            simular_turborreactor(DEFAULTS_TURBO)
        self.assertAlmostEqual(solucionador.call_args.kwargs['delta'], .04)
        self.assertNotIn('delta_pct', solucionador.call_args.kwargs)

    def test_rechaza_modos_combinados(self):
        r = self._post(altitud_geopotencial='5000')
        self.assertEqual(r.status_code, 400)
        self.assertIn('No combines altitud', r.get_data(as_text=True))
        r = self._post(modo_ambiente='ISA', altitud_geopotencial='5000')
        self.assertEqual(r.status_code, 400)
        self.assertIn('deja vac', r.get_data(as_text=True))

    def test_errores_no_numericos_y_dominios(self):
        for cambio in ({'mach':'xyz'}, {'mach':'nan'}, {'mach':'1.4'},
                       {'eta_n':'0'}, {'delta_pct':'100'}, {'T3':'2001'}):
            with self.subTest(cambio=cambio):
                r=self._post(**cambio)
                self.assertEqual(r.status_code, 400)
                self.assertNotIn('Traceback', r.get_data(as_text=True))

    def test_entradas_se_escapan_y_se_conservan(self):
        texto='<script>alert(1)</script>'
        pagina=self._post(rp=texto).get_data(as_text=True)
        self.assertEqual(self._post(rp=texto).status_code, 400)
        self.assertNotIn('value="'+texto+'"', pagina)
        self.assertIn('&lt;script&gt;', pagina)

    def test_sin_expansion_no_inventa_tsfc(self):
        datos={**DEFAULTS_TURBO,'mach':'0.9','rp':'3','pi_d':'0.7','T3':'500'}
        resultado=simular_turborreactor(datos)
        self.assertIsNone(resultado['tobera'])
        r=self.cliente.post('/turborreactor',data=datos)
        self.assertEqual(r.status_code,200)
        self.assertIn('Sin expansi',r.get_data(as_text=True))
        self.assertIn('Indefinido f',r.get_data(as_text=True))

    def test_empuje_no_positivo_tsfc_indefinido(self):
        datos={**DEFAULTS_TURBO,'mach':'0.9','rp':'3','pi_d':'0.7','T3':'600'}
        resultado=simular_turborreactor(datos)
        self.assertLessEqual(resultado['prestaciones']['empuje_especifico_neto'],0)
        self.assertIsNone(resultado['prestaciones']['TSFC_kg_N_h'])
        pagina=self.cliente.post('/turborreactor',data=datos).get_data(as_text=True)
        self.assertIn('no es positivo',pagina)

    def test_no_empuje_absoluto(self):
        pagina=self._post().get_data(as_text=True)
        self.assertNotIn('Empuje absoluto',pagina)
        self.assertIn('N/(kg/s)',pagina)

    def test_estaciones_estaticas_y_totales(self):
        estados=estaciones_turborreactor(simular_turborreactor(DEFAULTS_TURBO))
        self.assertEqual(len(estados),6)
        self.assertEqual([e['tipo'] for e in estados],['Estático']+['Remanso']*4+['Estático'])
        self.assertNotEqual(estados[-2]['p'],estados[-1]['p'])

    def test_svg_independientes_sin_datos_inventados(self):
        vista=preparar_vista_turborreactor(simular_turborreactor(DEFAULTS_TURBO))
        for campo in ('svg_componentes','svg_temperaturas','svg_presiones'):
            self.assertEqual(vista[campo].count('<svg'),1)
            self.assertIn('</svg>',vista[campo])
        self.assertEqual(vista['svg_temperaturas'].count('<circle'),4)

    def test_ruta_original_ocho_secciones_y_educacion(self):
        r=self.cliente.get('/')
        self.assertEqual(r.status_code,200)
        pagina=r.get_data(as_text=True)
        self.assertIn('href="/turborreactor"',pagina)
        self.assertEqual(pagina.count('class="dashboard-panel"'),8)
        turbo=self.cliente.get('/turborreactor').get_data(as_text=True)
        for texto in ('Fundamentos y procedimiento','Uso y configuraci','TSFC','Bloqueo','Combustible','propiedades de remanso'):
            if texto=='Bloqueo':
                self.assertIn('bloqueo',turbo.lower())
            else:
                self.assertIn(texto,turbo)

    def test_informes_historicos_no_reciben_enlace_nuevo(self):
        from dashboard import renderizar_dashboard
        texto=renderizar_dashboard(DEFAULTS_TURBO,modo_local=False)
        self.assertNotIn('href="/turborreactor"',texto)

    def test_no_hay_llamadas_cientificas_get(self):
        with patch('turborreactor_web.resolver_turborreactor_con_combustible') as solver:
            self.cliente.get('/turborreactor')
            self.cliente.get('/')
        solver.assert_not_called()


if __name__=='__main__':
    unittest.main()
