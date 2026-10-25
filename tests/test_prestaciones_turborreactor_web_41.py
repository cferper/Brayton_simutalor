"""Milestone 41: UI, validaciones, contratos M38 y referencias independientes."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from web_app import app
from turborreactor_web import DEFAULTS_TURBO
from prestaciones_turborreactor_web import (
    DEFAULT_ESTUDIOS, ESTADOS_WEB, PARAMETROS_OFAT,
    _svg_curva, _svg_mapa, preparar_estudio, valores_estudios)


RAIZ = Path(__file__).resolve().parents[1]


def controles(**cambios):
    return {**DEFAULT_ESTUDIOS, **{k: str(v) for k, v in cambios.items()}}


def base(**cambios):
    return {**DEFAULTS_TURBO, **{k: str(v) for k, v in cambios.items()}}


class PrestacionesWeb41(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.cliente = app.test_client()

    def _post(self, accion, controles_extra=None, **motor):
        return self.cliente.post('/turborreactor', data={**base(**motor),
            **controles(**(controles_extra or {})), 'accion': accion})

    def test_siete_secciones_y_navegacion_sin_scroll(self):
        respuesta = self.cliente.get('/turborreactor')
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.get_data(as_text=True)
        ids = ['configuracion', 'resultados', 'estaciones', 'graficas',
               'sensibilidad', 'mapa', 'fundamentos']
        for ident in ids:
            self.assertIn(f'id="{ident}" class="turbo-section"', html)
            self.assertIn(f'href="#{ident}"', html)
        self.assertEqual(html.count('class="turbo-section"'), 7)
        js = (RAIZ/'static/turborreactor.js').read_text(encoding='utf-8')
        self.assertIn('history.pushState', js)
        self.assertIn('popstate', js)
        self.assertIn('hashchange', js)
        self.assertIn('p.hidden=p.id!==id', js)
        self.assertNotIn('wheel', js)

    def test_educacion_propulsion_ejes_unidades_legend_y_keyboard(self):
        html = self.cliente.get('/turborreactor').get_data(as_text=True)
        for frase in ('One Factor At a Time', 'interacciones',
                      'frontera de la malla', 'No se define un frente global',
                      'kg/(N·h)', 'data-study-form="sensibilidad"',
                      'data-study-form="mapa"', 'tabindex="0"'):
            # El mensaje Pareto se materializa al calcular el mapa B.
            if frase == 'No se define un frente global':
                continue
            self.assertIn(frase, html)
        css = (RAIZ/'static/turborreactor.css').read_text(encoding='utf-8')
        self.assertIn('overflow-x:auto', css)
        self.assertIn('.turbo-study-svg:focus-visible', css)
        self.assertIn('mapa_tipo', html)

    def test_no_formularios_anidados(self):
        from html.parser import HTMLParser
        class FormParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.abiertos = 0
                self.maximo = 0
                self.cuenta = 0
            def handle_starttag(self, tag, attrs):
                if tag == 'form':
                    self.abiertos += 1
                    self.maximo = max(self.maximo, self.abiertos)
                    self.cuenta += 1
            def handle_endtag(self, tag):
                if tag == 'form':
                    self.abiertos -= 1
        p = FormParser()
        p.feed(self.cliente.get('/turborreactor').get_data(as_text=True))
        self.assertEqual(p.maximo, 1)
        self.assertEqual(p.cuenta, 3)
        self.assertEqual(p.abiertos, 0)

    def test_ofat_7_parametros_e_integracion_con_m38(self):
        self.assertEqual(set(PARAMETROS_OFAT),
                         {'rp','T3','mach','eta_c','eta_t','pi_d','delta_pct'})
        from prestaciones_turborreactor_web import barrer_rp_t3
        with patch('prestaciones_turborreactor_web.barrer_rp_t3',
                   wraps=barrer_rp_t3) as llamada:
            r = preparar_estudio('sensibilidad', controles(sens_parametro='eta_c',
                sens_min='.75', sens_max='.9', sens_n='4'), base())
        self.assertEqual(llamada.call_count, 4)
        self.assertEqual([round(p['valor_parametro'], 4) for p in r['puntos']],
                         [.75, .8, .85, .9])
        self.assertEqual(r['total'], 4)
        self.assertIn('svg', r['grafico_Fs'])
        self.assertEqual(r['puntos'][2]['punto']['entradas']['eta_c'], .85)

    def test_porcentaje_delta_convertido_una_vez(self):
        r = preparar_estudio('sensibilidad', controles(sens_parametro='delta_pct',
                 sens_min='4', sens_max='6', sens_n='3'), base())
        self.assertEqual([p['punto']['entradas']['delta'] for p in r['puntos']],
                         [.04, .05, .06])

    def test_ofat_reproduce_m37_para_punto_base(self):
        from turborreactor_web import simular_turborreactor
        r = preparar_estudio('sensibilidad', controles(sens_parametro='rp',
                 sens_min='9', sens_max='11', sens_n='3'), base())
        self.assertAlmostEqual(r['puntos'][1]['punto']['Fs'],
             simular_turborreactor(base())['prestaciones']['empuje_especifico_neto'], places=8)

    def test_validacion_ofat_antes_de_calcular(self):
        casos = [dict(sens_n='1'), dict(sens_n='32'), dict(sens_n='3.5'),
                 dict(sens_n='inf'), dict(sens_parametro='inventado'),
                 dict(sens_min='15',sens_max='5'),
                 dict(sens_min='nan'), dict(sens_max='inf'),
                 dict(sens_parametro='mach',sens_min='0',sens_max='1'),
                 dict(sens_parametro='eta_c',sens_min='0',sens_max='1')]
        for kwargs in casos:
            with self.subTest(kwargs=kwargs):
                with patch('prestaciones_turborreactor_web.barrer_rp_t3') as solver:
                    with self.assertRaises(ValueError):
                        preparar_estudio('sensibilidad', controles(**kwargs), base())
                    solver.assert_not_called()

    def test_validacion_mapas_antes_de_calcular(self):
        casos = [dict(mapa_nx='1'),dict(mapa_nx='16'),dict(mapa_ny='0'),
                 dict(mapa_ny='10000'),dict(mapa_nx='2.5'),
                 dict(mapa_tipo='arbitrario'),
                 dict(mapa_rp_min='15', mapa_rp_max='5'),
                 dict(mapa_T3_max='2001'),dict(mapa_rp_min='1'),
                 dict(mapa_tipo='Mach_altitud', mapa_mach_max='1'),
                 dict(mapa_tipo='Mach_altitud', mapa_altitud_max='20001')]
        for kwargs in casos:
            with self.subTest(kwargs=kwargs):
                with patch('prestaciones_turborreactor_web.barrer_rp_t3') as a, \
                     patch('prestaciones_turborreactor_web.barrer_mach_altitud') as b:
                    with self.assertRaises(ValueError):
                        preparar_estudio('mapa', controles(**kwargs), base())
                    a.assert_not_called()
                    b.assert_not_called()

    def test_reproduccion_referencia_A_exacta_y_pareto(self):
        mapa = preparar_estudio('mapa', controles(mapa_tipo='rp_T3',
              mapa_rp_min='5', mapa_rp_max='15', mapa_T3_min='1400',
              mapa_T3_max='1800',mapa_nx='5',mapa_ny='5'), base())['datos']
        self.assertEqual((mapa['validos'],mapa['total'],len(mapa['pareto'])),(25,25,7))
        self.assertAlmostEqual(mapa['maximo_Fs']['valor'],1077.68437665,places=6)
        self.assertAlmostEqual(mapa['minimo_TSFC']['valor'],.08620228954,places=9)
        self.assertEqual(mapa['maximo_Fs']['punto']['entradas']['rp'],15)
        self.assertEqual(mapa['maximo_Fs']['punto']['entradas']['T3'],1800)
        self.assertTrue(mapa['maximo_Fs']['en_frontera_malla'])

    def test_reproduccion_referencia_B_isa_y_sin_pareto(self):
        r = preparar_estudio('mapa', controles(mapa_tipo='Mach_altitud',
              mapa_mach_min='0',mapa_mach_max='0.8',mapa_altitud_min='0',
              mapa_altitud_max='20000',mapa_nx='5',mapa_ny='5'),
              base(pi_d='.98',mach='0.3',T_amb='288.15',p_amb='100'))
        m = r['datos']
        self.assertEqual((m['validos'],m['total']), (25,25))
        self.assertAlmostEqual(m['maximo_Fs']['valor'],1030.247813835,places=6)
        self.assertAlmostEqual(m['minimo_TSFC']['valor'],.105830470736,places=9)
        self.assertFalse(m['pareto_aplicable'])
        self.assertIsNone(m['pareto'])
        self.assertIsNone(r['grafico_pareto'])
        self.assertEqual(m['puntos'][0][0]['entradas']['pi_d'],.98)
        self.assertEqual(m['puntos'][0][0]['entradas']['mach'],0)

    def test_reproduccion_referencia_C_ofat_compromiso(self):
        r = preparar_estudio('sensibilidad', controles(sens_parametro='rp',
                 sens_min='4',sens_max='20',sens_n='9'),base())
        puntos = [fila['punto'] for fila in r['puntos']]
        self.assertEqual(len(puntos),9)
        self.assertEqual(max(puntos,key=lambda p:p['Fs'])['entradas']['rp'],14)
        self.assertEqual(min(puntos,key=lambda p:p['TSFC_kg_N_h'])['entradas']['rp'],20)
        from mapas_prestaciones_turborreactor_cp import frente_pareto
        self.assertEqual(len(frente_pareto(puntos)),4)

    def test_representacion_inadmisible_guion_y_corte_de_lineas(self):
        r = preparar_estudio('sensibilidad', controles(sens_parametro='T3',
                 sens_min='200',sens_max='1600',sens_n='3'),base())
        self.assertNotEqual(r['puntos'][0]['punto']['estado'],'valido')
        self.assertIsNone(r['puntos'][0]['punto']['Fs'])
        self.assertIn('Sin dato',r['grafico_Fs'])
        self.assertIn('×',r['grafico_Fs'])
        self.assertNotIn('>0.0000<',r['grafico_Fs'])
        pagina = self._post('sensibilidad', dict(sens_parametro='T3',sens_min='200',
                                              sens_max='1600',sens_n='3'))
        self.assertEqual(pagina.status_code,200)
        self.assertIn('Inadmisible', pagina.get_data(as_text=True))

    def test_curva_no_interpola_entre_dos_validos_separados_por_error(self):
        puntos = [{'valor_parametro': x, 'punto': {'estado': estado, 'Fs': fs}}
                  for x, estado, fs in ((5,'valido',200),
                                       (10,'inadmisible',None),
                                       (15,'valido',320))]
        svg = _svg_curva(puntos, 'rp', '–', 'Fs', 'Empuje', 'N/(kg/s)')
        self.assertEqual(svg.count('<circle'),2)
        self.assertEqual(svg.count('<polyline'),0)  # no línea sobre el hueco
        self.assertIn('× Sin dato',svg)

    def test_sin_expansion_y_fuerza_negativa_reales(self):
        r = preparar_estudio('sensibilidad',controles(sens_parametro='T3',
                       sens_min='500',sens_max='600',sens_n='2'),
                       base(mach='.9',rp='3',pi_d='.7'))
        primero, segundo = [fila['punto'] for fila in r['puntos']]
        self.assertEqual(primero['estado'],'sin_expansion')
        self.assertEqual(segundo['estado'],'empuje_no_positivo')
        self.assertIsNone(primero['Fs'])
        self.assertLess(segundo['Fs'],0)
        self.assertIsNone(segundo['TSFC_kg_N_h'])
        pagina = self._post('sensibilidad',dict(sens_parametro='T3',
                     sens_min='500',sens_max='600',sens_n='2'),
                     mach='.9',rp='3',pi_d='.7')
        self.assertEqual(pagina.status_code,200)
        self.assertIn('Sin expansión',pagina.get_data(as_text=True))
        self.assertIn('Empuje no positivo',pagina.get_data(as_text=True))

    def test_mapas_celdas_invalidas_y_recuento_sin_falsear(self):
        r = preparar_estudio('mapa',controles(mapa_rp_min='5',mapa_rp_max='15',
                      mapa_T3_min='200',mapa_T3_max='1800',mapa_nx='3',mapa_ny='3'),base())
        m = r['datos']
        self.assertGreater(m['descartados'],0)
        self.assertEqual(m['validos']+m['descartados'],m['total'])
        self.assertIn('× Sin dato',r['grafico_Fs'])
        self.assertTrue(any(p['Fs'] is None for p in r['filas']))

    def test_fallos_numericos_y_estados_expuestos_sin_cero_ficticio(self):
        from ciclo_cp_variable import ErrorNumericoCiclo
        with patch('mapas_prestaciones_turborreactor_cp.resolver_turborreactor_con_combustible',
                   side_effect=ErrorNumericoCiclo('inversión fallida')):
            r = preparar_estudio('sensibilidad', controles(sens_n='2'), base())
            self.assertEqual([p['punto']['estado'] for p in r['puntos']],
                             ['fallo_numerico']*2)
            self.assertEqual(r['cuenta_validos'], 0)
            self.assertTrue(all(p['punto']['Fs'] is None for p in r['puntos']))
        self.assertIn('fallo_numerico',ESTADOS_WEB)
        self.assertIn('sin_expansion',ESTADOS_WEB)
        self.assertIn('empuje_no_positivo',ESTADOS_WEB)

    def test_no_ocultar_errores_de_programacion(self):
        with patch('mapas_prestaciones_turborreactor_cp.resolver_turborreactor_con_combustible',
                   side_effect=TypeError('bug')):
            with self.assertRaises(TypeError):
                preparar_estudio('mapa', controles(mapa_nx='2',mapa_ny='2'),base())

    def test_post_ofat_conserva_resultado_individual_y_entrada(self):
        r = self._post('sensibilidad',dict(sens_n='3'),rp='12',mach='0.4')
        self.assertEqual(r.status_code,200)
        html = r.get_data(as_text=True)
        self.assertIn('data-initial-panel="sensibilidad"',html)
        self.assertIn('Caso calculado',html)
        self.assertIn('value="12"',html)
        self.assertIn('value="0.4"',html)
        self.assertIn('Puntos evaluados y diagnóstico',html)

    def test_post_mapa_muestra_ambos_y_pareto_solo_en_a(self):
        a = self._post('mapa',dict(mapa_nx='2',mapa_ny='2'))
        self.assertEqual(a.status_code,200)
        self.assertIn('frente de Pareto',a.get_data(as_text=True))
        b = self._post('mapa',dict(mapa_tipo='Mach_altitud',mapa_nx='2',mapa_ny='2'))
        self.assertEqual(b.status_code,200)
        html = b.get_data(as_text=True)
        self.assertIn('Pareto no aplicable',html)
        self.assertIn('data-initial-panel="mapa"',html)
        self.assertIn('Caso calculado',html)

    def test_post_error_estado_http_400_sin_perder_campos(self):
        respuesta = self._post('sensibilidad',dict(sens_min='15',sens_max='5'))
        self.assertEqual(respuesta.status_code,400)
        html=respuesta.get_data(as_text=True)
        self.assertIn('No se ha calculado el estudio OFAT',html)
        self.assertIn('value="15"',html)
        self.assertIn('value="5"',html)
        self.assertIn('data-initial-panel="sensibilidad"',html)

    def test_sin_js_formularios_completos_y_parametros_servidor(self):
        html = self.cliente.get('/turborreactor').get_data(as_text=True)
        self.assertEqual(html.count('data-motor-field'),2*len(DEFAULTS_TURBO))
        self.assertEqual(html.count('method="post" action="/turborreactor"'),3)
        self.assertIn('Sin JavaScript',html)
        js=(RAIZ/'static/turborreactor.js').read_text(encoding='utf-8')
        self.assertIn('input[data-motor-field]',js)

    def test_cotas_tamanos_no_exceden_225_y_31(self):
        ofat = preparar_estudio('sensibilidad', controles(sens_n='31'),base())
        self.assertEqual(ofat['total'],31)
        mapa = preparar_estudio('mapa',controles(mapa_nx='15',mapa_ny='15'),base())
        self.assertEqual(mapa['datos']['total'],225)

    def test_isa_en_a_y_parametros_configuracion(self):
        isa = base(modo_ambiente='ISA',T_amb='',p_amb='',
                   altitud_geopotencial='10000',mach='0.5',pi_d='.97')
        a = preparar_estudio('mapa', controles(mapa_nx='2',mapa_ny='2'),isa)['datos']
        p = a['puntos'][0][0]
        self.assertEqual(p['entradas']['altitud_geopotencial'],10000)
        self.assertEqual(p['entradas']['mach'],.5)
        self.assertEqual(p['entradas']['pi_d'],.97)
        b = preparar_estudio('mapa', controles(mapa_tipo='Mach_altitud',
                                  mapa_nx='2',mapa_ny='2'),isa)['datos']
        self.assertNotIn('T_amb',b['puntos'][0][0]['entradas'])

    def test_no_modificar_dashboard_original_ni_informes(self):
        anterior = app.config['OUTPUTS_DIR']
        self.addCleanup(app.config.__setitem__, 'OUTPUTS_DIR', anterior)
        with TemporaryDirectory() as carpeta:
            app.config['OUTPUTS_DIR'] = Path(carpeta)
            get_br = self.cliente.get('/')
            get_inf = self.cliente.get('/informes/informe_inexistente.html')
            r = self._post('mapa',dict(mapa_nx='2',mapa_ny='2'))
            self.assertEqual(r.status_code,200)
            self.assertEqual(get_br.status_code,200)
            self.assertEqual(get_inf.status_code,404)
            self.assertEqual(list(Path(carpeta).iterdir()),[])
            self.assertEqual(self.cliente.get('/informes/informe_inexistente.html').status_code,404)

    def test_no_cambio_modulos_cientificos_por_estudios(self):
        from turborreactor_web import simular_turborreactor
        previo = simular_turborreactor(base())
        preparar_estudio('sensibilidad', controles(sens_n='3'),base())
        preparar_estudio('mapa',controles(mapa_nx='3',mapa_ny='3'),base())
        self.assertEqual(previo,simular_turborreactor(base()))


if __name__ == '__main__':
    unittest.main()
