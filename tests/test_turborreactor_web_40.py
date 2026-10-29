"""Milestone 40: contratos HTTP, formulario y fidelidad del presentador web."""

import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from web_app import app
from turborreactor_web import (DEFAULTS_TURBO, EJEMPLOS_TURBO,
                              leer_turborreactor, simular_turborreactor,
                              estaciones_turborreactor, preparar_vista_turborreactor)


RAIZ = Path(__file__).resolve().parents[1]


class InspectorPaneles(HTMLParser):
    """Lee estructura real HTML; no ejecuta ni simula el navegador."""
    def __init__(self):
        super().__init__()
        self.paneles = []
        self.navegacion = []
        self.region_svg = []
        self.inicial = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'body':
            self.inicial = a.get('data-initial-panel')
        if tag == 'section' and 'turbo-section' in a.get('class', '').split():
            self.paneles.append(a)
        if tag == 'a' and a.get('href', '').startswith('#') and a.get('href') != '#contenido':
            self.navegacion.append(a)
        if tag == 'div' and 'turbo-svg' in a.get('class', '').split():
            self.region_svg.append(a)


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
        r=self.cliente.get('/brayton')
        self.assertEqual(r.status_code,200)
        pagina=r.get_data(as_text=True)
        self.assertIn('href="/turborreactor"',pagina)
        self.assertEqual(pagina.count('class="dashboard-panel"'),8)
        turbo=self.cliente.get('/turborreactor').get_data(as_text=True)
        for texto in ('Fundamentos teóricos y procesos','Uso y configuraci','TSFC','Bloqueo','Combustible','propiedades de remanso'):
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
            self.cliente.get('/brayton')
        solver.assert_not_called()

    def test_pantallas_actuales_y_enlaces_univocos(self):
        html=self.cliente.get('/turborreactor').get_data(as_text=True)
        inspector=InspectorPaneles(); inspector.feed(html)
        ids=['configuracion','resultados','estaciones','graficas',
             'sensibilidad','mapa']
        self.assertEqual([p['id'] for p in inspector.paneles],ids)
        self.assertTrue(all(p.get('tabindex')=='-1' for p in inspector.paneles))
        self.assertEqual([a['href'] for a in inspector.navegacion],['#'+i for i in ids])
        self.assertEqual([a.get('aria-current') for a in inspector.navegacion].count('page'),1)

    def test_seleccion_inicial_resultados_y_errores(self):
        for respuesta,esperado in ((self.cliente.get('/turborreactor'),'configuracion'),
                                    (self._post(),'resultados'),
                                    (self._post(rp='0'),'configuracion')):
            with self.subTest(esperado=esperado):
                inspector=InspectorPaneles(); inspector.feed(respuesta.get_data(as_text=True))
                self.assertEqual(inspector.inicial,esperado)

    def test_navegacion_js_no_depende_de_scroll_y_es_historizable(self):
        js=(RAIZ/'static/turborreactor.js').read_text(encoding='utf-8')
        css=(RAIZ/'static/turborreactor.css').read_text(encoding='utf-8')
        for fragmento in ('paneles.forEach','p.hidden=p.id!==id','aria-current',
                          'history.pushState','popstate','hashchange',
                          'preventDefault','document.body.dataset.initialPanel'):
            self.assertIn(fragmento,js)
        self.assertIn('.turbo-section[hidden]{display:none!important}',css)
        self.assertIn('.turbo-page.turbo-nav-ready',css)
        self.assertNotIn('wheel',js)

    def test_conservar_estado_al_cambiar_de_panel(self):
        js=(RAIZ/'static/turborreactor.js').read_text(encoding='utf-8')
        # La selección actúa sobre las secciones del DOM existente: no hay
        # recarga, petición HTTP adicional ni reseteo del formulario.
        self.assertIn('paneles.forEach(p=>{p.hidden=p.id!==id;});',js)
        self.assertIn('elegir(ids.has(id)?id:document.body.dataset.initialPanel,true)',js)
        self.assertIn('if(location.hash',js)
        self.assertNotIn('sessionStorage',js)
        self.assertNotIn('fetch(',js)
        self.assertIn('value="1600"',self._post().get_data(as_text=True))

    def test_desglose_del_empuje_con_unidades(self):
        pagina=self._post().get_data(as_text=True)
        inspector=InspectorPaneles(); inspector.feed(pagina)
        for nombre in ('Momento de salida','Presión</dt>','Resistencia de entrada'):
            self.assertIn(nombre,pagina)
        self.assertGreaterEqual(pagina.count('N/(kg/s de aire)'),3)
        self.assertIn('Momento de salida + presión',pagina)

    def test_ejemplos_y_recuperacion_ideal_presion(self):
        pagina=self.cliente.get('/turborreactor').get_data(as_text=True)
        for texto in ('πd = 1','πd = 0,97','πd = 0,98','recuperación ideal'):
            self.assertIn(texto,pagina)

    def test_validacion_previa_especifica_rp(self):
        for rp in ('0','1','-1'):
            with self.subTest(rp=rp):
                r=self._post(rp=rp)
                self.assertEqual(r.status_code,400)
                html=r.get_data(as_text=True)
                self.assertIn('La relación de compresión rp debe ser mayor que 1.',html)
                self.assertIn(f'value="{rp}"',html)
        with patch('turborreactor_web.resolver_turborreactor_con_combustible') as solucionador:
            self._post(rp='0')
        solucionador.assert_not_called()

    def test_svg_legible_desplazable_y_foco(self):
        pagina=self._post().get_data(as_text=True)
        inspector=InspectorPaneles(); inspector.feed(pagina)
        # Tres SVG originales, cuatro de M44.1/M44.2 y el balance de M44.3.
        self.assertEqual(len(inspector.region_svg),8)
        self.assertTrue(all(r.get('tabindex')=='0' and r.get('role')=='region'
                            and 'aria-label' in r for r in inspector.region_svg))
        css=(RAIZ/'static/turborreactor.css').read_text(encoding='utf-8')
        self.assertIn('min-width:660px',css)
        self.assertIn('overflow-x:auto',css)
        self.assertIn('.turbo-svg:focus-visible',css)

    def test_educacion_distribuida_en_los_seis_apartados(self):
        pagina=self._post().get_data(as_text=True)
        for texto in ('Qué cambia con el ambiente','Cómo afecta la compresión',
                      'Pérdidas de potencia','combustible equivalente',
                      'Empuje bruto y neto','0 · Ambiente y 1 · Difusor',
                      '4→garganta→escape · Tobera','Temperaturas totales [K]',
                      'modelo educativo','Verificación','validación'):
            self.assertIn(texto,pagina)

    def test_respaldo_sin_js_con_formulario_post(self):
        pagina=self.cliente.get('/turborreactor').get_data(as_text=True)
        self.assertIn('method="post"',pagina)
        self.assertNotIn('hidden="hidden"',pagina)
        self.assertIn('data-initial-panel="configuracion"',pagina)
        self.assertEqual(self._post().status_code,200)


if __name__=='__main__':
    unittest.main()
