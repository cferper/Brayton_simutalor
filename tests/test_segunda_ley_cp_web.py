"""Fase 2G: integración Flask y SVG dentro del dashboard existente."""

import unittest
from unittest.mock import patch

import cp_variable_web
from ciclo_cp_variable import resolver_ciclo
from cp_variable_web import DEFAULTS
from segunda_ley_cp_variable import analizar_segunda_ley_cp_variable
from web_app import app


BASE = {k:str(v) for k,v in DEFAULTS.items()}


class SegundaLeyCPWeb(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()

    def test_panel_activo_y_unica_plantilla(self):
        r=self.client.get('/')
        html=r.get_data(as_text=True)
        self.assertEqual(r.status_code,200)
        self.assertEqual(html.count('id="segunda_ley"'),1)
        self.assertIn('name="accion" value="segunda_ley"',html)
        self.assertIn('name="T0"',html)
        self.assertIn('name="p0"',html)
        self.assertEqual(html.count('type="number"'),18)
        self.assertNotIn('Pendiente cp(T)',html)
        self.assertNotIn('cp_variable.html',html)

    def test_valores_web_corresponden_a_calculo_cp(self):
        c=resolver_ciclo(**DEFAULTS)
        e=analizar_segunda_ley_cp_variable(c)
        r=self.client.post('/',data={**BASE,'accion':'segunda_ley','T0':'288.15','p0':'100'})
        texto=r.get_data(as_text=True)
        self.assertEqual(r.status_code,200)
        for valor in (*e['entropias'],*e['exergias'],*e['destruccion']):
            self.assertIn(f'{valor:.6f}',texto)
        self.assertIn(f'{100*e["eta_ex_compresor"]:.3f} %',texto)
        self.assertIn('Gouy',texto)
        self.assertIn('aria-label="Exergía destruida',texto)
        self.assertIn('data-initial-section="segunda_ley"',texto)

    def test_ambiente_independiente_sin_repetir_solucionador(self):
        cp_variable_web._ciclo_para_segunda_ley.cache_clear()
        with patch.object(cp_variable_web,'resolver_ciclo', wraps=resolver_ciclo) as solucionar:
            with patch.object(cp_variable_web,'estudiar_cp_variable') as optimizar:
                uno=self.client.post('/',data={**BASE,'accion':'segunda_ley','T0':'288.15','p0':'100'})
                dos=self.client.post('/',data={**BASE,'accion':'segunda_ley','T0':'300','p0':'120'})
        self.assertEqual(uno.status_code,200)
        self.assertEqual(dos.status_code,200)
        solucionar.assert_called_once()
        optimizar.assert_not_called()
        self.assertIn('300.00 K',dos.get_data(as_text=True))
        cp_variable_web._ciclo_para_segunda_ley.cache_clear()

    def test_errores_ambientales_y_de_ciclo_conservar_seccion(self):
        for cambios in ({'T0':'nan'},{'T0':'199'},{'T0':'2001'},
                        {'p0':'-2'},{'p0':'0'},{'p0':'inf'},
                        {'T1':'1900','rp':'5'}):
            with self.subTest(cambios=cambios):
                r=self.client.post('/',data={**BASE,'accion':'segunda_ley',**cambios})
                self.assertEqual(r.status_code,400)
                t=r.get_data(as_text=True)
                self.assertIn('data-initial-section="segunda_ley"',t)
                self.assertIn('No se ha completado la simulación',t)
                self.assertNotIn('Traceback',t)

    def test_no_motor_conserva_datos_sin_rendimiento(self):
        r=self.client.post('/',data={**BASE,'rp':'1','delta':'0','accion':'segunda_ley'})
        self.assertEqual(r.status_code,200)
        t=r.get_data(as_text=True)
        self.assertIn('Ciclo no motor',t)
        self.assertIn('No definido',t)
        self.assertIn('no se publican rendimientos exergéticos',t)

    def test_grafico_usa_datos_reales_y_tiene_unidades(self):
        datos=cp_variable_web.preparar_segunda_ley(DEFAULTS)
        svg=datos['svg_destruccion']
        self.assertTrue(svg.startswith('<svg '))
        self.assertIn(f'{datos["estudio"]["destruccion"][0]:.6f} kJ/kg',svg)
        self.assertIn(f'{datos["estudio"]["destruccion"][1]:.6f} kJ/kg',svg)
        self.assertEqual(svg.count('<rect '),2)

    def test_mismos_siete_parametros_y_rutas_anteriores(self):
        r=self.client.post('/',data={**BASE,'accion':'normal'})
        self.assertEqual(r.status_code,200)
        for ruta in ('/modelo-cp-variable','/segunda-ley'):
            self.assertEqual(self.client.get(ruta).status_code,404)
        self.assertIn('href="#mapa"',self.client.get('/').get_data(as_text=True))


if __name__=='__main__':
    unittest.main()
