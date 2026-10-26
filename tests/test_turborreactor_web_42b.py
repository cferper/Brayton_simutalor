"""Integración 42.B: C-D y continuidad de contratos del turborreactor."""

import unittest

from combustible_cp_variable import resolver_turborreactor_con_combustible
from turborreactor_web import (DEFAULTS_TURBO, _presion_adaptacion_cd, leer_turborreactor,
                             preparar_vista_turborreactor, simular_turborreactor)
from mapas_prestaciones_turborreactor_cp import barrer_rp_t3
from tobera_convergente_divergente_cp import (relacion_areas_adaptada,
                                              resolver_tobera_convergente_divergente)
from web_app import app


class TurborreactorWeb42B(unittest.TestCase):
    def setUp(self):
        self.valores = dict(DEFAULTS_TURBO)

    def test_legacy_y_valores_de_fabrica(self):
        previo = resolver_turborreactor_con_combustible(
            0, 10, .85, 1600, .04, .9, .98, .95, 1, .99, 43000,
            T_amb=288.15, p_amb=100)
        nuevo = simular_turborreactor(self.valores)
        self.assertEqual(nuevo["prestaciones"], previo["prestaciones"])

    def test_eta_n_validado_en_ambos_modos(self):
        self.valores.update(tipo_tobera="convergente_divergente", eta_n="no-numero")
        with self.assertRaises(ValueError):
            leer_turborreactor(self.valores)
        for valor in ("-100", "0", "1.01", "nan", "inf"):
            self.valores["eta_n"] = valor
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                leer_turborreactor(self.valores)
        self.valores["eta_n"] = "0.95"
        self.assertEqual(leer_turborreactor(self.valores)["eta_n"], .95)

    def test_api_cd_valida_eta_n_aunque_no_intervenga(self):
        kwargs = dict(T_amb=288.15, p_amb=100,
                      tipo_tobera="convergente_divergente", epsilon=1.5)
        def resolver(eta_n):
            return resolver_turborreactor_con_combustible(
                0, 10, .85, 1600, .04, .9, .98, eta_n, 1, .99, 43000, **kwargs)
        referencia = resolver(.95)
        self.assertEqual(referencia["prestaciones"], resolver(1)["prestaciones"])
        for invalido in (-100, 0, 1.01, float('nan')):
            with self.subTest(invalido=invalido), self.assertRaises(ValueError):
                resolver(invalido)

    def test_validacion_epsilon_y_tipo(self):
        self.valores["tipo_tobera"] = "convergente_divergente"
        for epsilon in ("0.99", "nan", "inf", "cero", ""):
            self.valores["epsilon"] = epsilon
            with self.subTest(epsilon=epsilon), self.assertRaises(ValueError):
                leer_turborreactor(self.valores)
        self.valores["tipo_tobera"] = "desconocido"
        with self.assertRaises(ValueError):
            leer_turborreactor(self.valores)

    def test_empuje_y_tsfc_cd(self):
        self.valores["tipo_tobera"] = "convergente_divergente"
        r = simular_turborreactor(self.valores)
        p, n = r["prestaciones"], r["tobera"]
        self.assertTrue(n["resuelto"])
        f = r["combustor"]["f"]
        bruto = (1+f)*(n["velocidad_salida"] + n["empuje_especifico_presion"])
        self.assertAlmostEqual(p["empuje_especifico_bruto"], bruto, places=9)
        self.assertAlmostEqual(p["empuje_especifico_neto"], bruto-r["remanso"]["velocidad_vuelo"], places=9)
        self.assertAlmostEqual(p["TSFC_kg_N_h"], 3600*f/p["empuje_especifico_neto"], places=9)
        vista = preparar_vista_turborreactor(r)
        self.assertEqual(vista["estaciones"][-2]["nombre"], "Garganta de tobera C-D")
        self.assertAlmostEqual(vista["adaptacion_cd"]["presion_adaptada"], n["presion_salida"], places=4)

    def test_choque_interno_resuelto_con_empuje_42c(self):
        self.valores.update(tipo_tobera="convergente_divergente", epsilon="6")
        # Geometría suficientemente abierta para exigir choque interno
        # con esta contrapresión: la garganta sí conserva estado sónico.
        r = simular_turborreactor(self.valores)
        self.assertIsNotNone(r["tobera"])
        self.assertTrue(r["tobera"]["resuelto"])
        self.assertIsNotNone(r["tobera"]["mach_garganta"])
        self.assertEqual(r["tobera"]["regimen"], "choque_normal_interno")
        self.assertIsNotNone(r["prestaciones"]["empuje_especifico_neto"])
        self.assertIsNotNone(r["prestaciones"]["TSFC_kg_N_h"])
        self.assertIsNotNone(preparar_vista_turborreactor(r)["estaciones"][-1]["T"])

    def test_html_muestra_estados_y_perdidas_choque_42c(self):
        self.valores.update(tipo_tobera='convergente_divergente',epsilon='6')
        esperado=simular_turborreactor(self.valores)['tobera']['choque_normal']
        self.assertIsNotNone(esperado)
        with app.test_client() as cliente:
            respuesta=cliente.post('/turborreactor',data=self.valores)
            self.assertEqual(respuesta.status_code,200)
            html=respuesta.get_data(as_text=True)
        bloque=html.split('<h4>Choque normal interno</h4>',1)[1].split('</dl>',1)[0]
        for rotulo in ('Achoque/Ag','Mach anterior / posterior',
                       'Presión anterior / posterior','Pérdida de presión total',
                       'Entropía generada'):
            self.assertIn(rotulo,bloque)
        for valor in ('%.5f'%esperado['relacion_areas_choque'],
                      '%.4f / %.4f'%(esperado['M1'],esperado['M2']),
                      '%.3f / %.3f kPa'%(esperado['p1'],esperado['p2']),
                      '%.3f kPa'%esperado['perdida_presion_total'],
                      '%.6f kJ/(kg·K)'%esperado['generacion_entropia']):
            self.assertIn(valor,bloque)
        self.assertNotIn('—',bloque)

    def test_mapa_conserva_geometria(self):
        m = barrer_rp_t3([10, 11], [1500, 1600], mach=0, T_amb=288.15,
                        p_amb=100, tipo_tobera="convergente_divergente", epsilon=1.5)
        self.assertEqual(m["total"], 4)
        for fila in m["puntos"]:
            for punto in fila:
                self.assertEqual(punto["entradas"]["tipo_tobera"], "convergente_divergente")
                self.assertEqual(punto["entradas"]["epsilon"], 1.5)

    def test_mapa_con_choque_no_resuelto_no_optimiza(self):
        m = barrer_rp_t3([10, 11], [1500, 1600], mach=0, T_amb=288.15,
                        p_amb=100, tipo_tobera="convergente_divergente", epsilon=6)
        for fila in m["puntos"]:
            for punto in fila:
                if punto["estado"] == "tobera_no_resuelta":
                    self.assertEqual(punto["motivo"], "choque_interno_o_salida_no_resuelto")
                    self.assertIsNone(punto["Fs"])
                    self.assertIsNone(punto["TSFC_kg_N_h"])
                    self.assertFalse(punto["cumple_restricciones"])
                    self.assertIsNotNone(punto["resultado"]["tobera"]["mach_garganta"])
        self.assertEqual(sum(m["por_estado"].values()), m["total"])
        self.assertTrue(any(p["regimen_tobera"] == "choque_normal_interno"
                            for fila in m["puntos"] for p in fila))

    def test_epsilon_uno_limite_sonico_y_adaptacion(self):
        self.valores.update(tipo_tobera="convergente_divergente", epsilon="1")
        r = simular_turborreactor(self.valores)
        self.assertAlmostEqual(r["tobera"]["mach_salida"], 1, places=5)
        self.assertAlmostEqual(preparar_vista_turborreactor(r)["adaptacion_cd"]["presion_adaptada"],
                               r["tobera"]["presion_critica"], places=5)

    def test_renderizado_y_accion_adaptacion(self):
        with app.test_client() as cliente:
            html = cliente.get("/turborreactor").get_data(as_text=True)
            self.assertIn('name="tipo_tobera"', html)
            self.assertIn('name="epsilon"', html)
            self.valores.update(tipo_tobera="convergente_divergente", accion="adaptacion")
            respuesta = cliente.post("/turborreactor", data=self.valores)
            self.assertEqual(respuesta.status_code, 200)
            html = respuesta.get_data(as_text=True)
            self.assertIn("Calculadora de adaptación geométrica", html)
            self.assertIn("Garganta de tobera C-D", html)

    def test_eta_n_visible_y_editable_en_cd(self):
        with app.test_client() as cliente:
            respuesta = cliente.get("/turborreactor")
            self.assertEqual(respuesta.status_code, 200)
            html = respuesta.get_data(as_text=True)
            campo = html.split('id="eta_n"', 1)[0].rsplit('<div class="field"', 1)[-1]
            self.assertNotIn('data-tobera=', campo)
            self.assertIn('name="eta_n"', html)
            self.assertIn('se valida', html)
            self.valores.update(tipo_tobera="convergente_divergente", eta_n="0.95", epsilon="1.7")
            html_cd = cliente.post("/turborreactor", data=self.valores).get_data(as_text=True)
            self.assertIn('id="eta_n" name="eta_n"', html_cd)
            self.assertIn('value="0.95"', html_cd)
            self.assertIn('value="1.7"', html_cd)
            self.assertIn('value="convergente_divergente" selected', html_cd)

    def test_eta_n_invalido_cd_se_puede_corregir(self):
        self.valores.update(tipo_tobera="convergente_divergente", eta_n="-100")
        with app.test_client() as cliente:
            respuesta = cliente.post("/turborreactor", data=self.valores)
            self.assertEqual(respuesta.status_code, 400)
            html = respuesta.get_data(as_text=True)
            self.assertIn('role="alert"', html)
            self.assertIn('eta_n debe estar en (0,1]', html)
            self.assertIn('id="eta_n" name="eta_n"', html)
            self.assertIn('value="-100"', html)


if __name__ == "__main__":
    unittest.main()


class AdaptacionCD42BCorreccion(unittest.TestCase):
    def test_ida_vuelta_areas_y_presiones(self):
        Tt, pt = 1200.0, 500.0
        for epsilon in (1.0001, 1.001, 1.01, 1.5, 2, 10):
            with self.subTest(epsilon=epsilon):
                presion = _presion_adaptacion_cd(Tt, pt, epsilon)
                inversa = relacion_areas_adaptada(Tt, pt, presion)
                self.assertAlmostEqual(inversa/epsilon, 1, delta=3e-9)
                modelo = resolver_tobera_convergente_divergente(Tt, pt, presion, epsilon)
                self.assertTrue(modelo["resuelto"])
                self.assertAlmostEqual(modelo["presion_salida"], presion,
                                       delta=3e-6*pt)

    def test_caso_revision_independiente(self):
        presion = _presion_adaptacion_cd(1200, 500, 1.001)
        self.assertAlmostEqual(presion, 259.1196, delta=3e-4)
        self.assertAlmostEqual(relacion_areas_adaptada(1200, 500, presion),
                               1.001, delta=2e-9)

    def test_limite_epsilon_uno(self):
        from tobera_convergente_divergente_cp import _sonico
        presion = _presion_adaptacion_cd(1200, 500, 1)
        self.assertAlmostEqual(presion, _sonico(1200, 500)["p"], places=8)

    def test_fuera_de_dominio_y_entradas_invalidas(self):
        for epsilon in (1e4, 1e8):
            with self.subTest(epsilon=epsilon), self.assertRaises(ValueError):
                _presion_adaptacion_cd(1200, 500, epsilon)
        for epsilon in (0.5, float("nan"), float("inf"), True):
            with self.subTest(entrada=epsilon), self.assertRaises(ValueError):
                _presion_adaptacion_cd(1200, 500, epsilon)
