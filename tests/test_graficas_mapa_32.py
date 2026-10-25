"""Milestone 32: mapa categórico, cortes exactos, máscaras y Flask."""
import unittest
from xml.etree import ElementTree
from cp_variable_web import DEFAULTS, preparar_mapa
from graficas_mapa_cp import COLORES_ESTADO, svg_cortes_mapa, svg_mapa_viabilidad
from mapa_diseno_cp_variable import calcular_mapa_cp_variable
from web_app import app


class GraficasMapa32(unittest.TestCase):
    def test_cada_celda_conserva_categoria_y_coordenadas(self):
        estudio=calcular_mapa_cp_variable(DEFAULTS,.5,20,1200,2005,7,7)
        svg=svg_mapa_viabilidad(estudio)
        rects=[n.attrib for n in ElementTree.fromstring(svg).iter()
               if n.tag.endswith('rect')]
        self.assertEqual(len(rects),49+5)  # 49 celdas + cinco símbolos de leyenda
        celdas=[r for r in rects if 'data-estado' in r]
        self.assertEqual(len(celdas),49)
        for j,row in enumerate(estudio['filas']):
            for i,c in enumerate(row):
                r=celdas[j*7+i]
                self.assertEqual(r['data-estado'],c['estado'])
                self.assertAlmostEqual(float(r['data-rp']),c['rp'],places=8)
                self.assertAlmostEqual(float(r['data-T3']),c['T3'],places=8)
                self.assertEqual(r['fill'],COLORES_ESTADO[c['estado']])

    def test_cinco_categorias_y_leyenda_incluidas(self):
        estudio=calcular_mapa_cp_variable(DEFAULTS,2,10,1200,1600,5,5)
        svg=svg_mapa_viabilidad(estudio)
        for nombre in ('Motor','No motor','Fuera de rango','Entrada inválida','Error numérico'):
            self.assertIn(nombre,svg)
        self.assertIn('sin interpolar fronteras',svg)

    def test_cortes_proceden_de_tres_filas_originales(self):
        e=calcular_mapa_cp_variable(DEFAULTS,2,40,1200,1800,9,7)
        for clave,factor in [('trabajo_neto',1),('rendimiento',100)]:
            with self.subTest(magnitud=clave):
                svg=svg_cortes_mapa(e,clave)
                puntos=[n.attrib for n in ElementTree.fromstring(svg).iter()
                        if n.tag.endswith('circle')]
                indices=(0,3,6)
                esperado=[c for j in indices for c in e['filas'][j]
                          if c['operativas'] is not None]
                self.assertEqual(len(puntos),len(esperado))
                for p,c in zip(puntos,esperado):
                    self.assertAlmostEqual(float(p['data-rp']),c['rp'],places=8)
                    self.assertAlmostEqual(float(p['data-T3']),c['T3'],places=8)
                    self.assertAlmostEqual(float(p['data-valor']),
                                           factor*c['operativas'][clave],places=8)
                for j in indices:
                    self.assertIn(f'T3={e["T3s"][j]:.6g} K',svg)

    def test_no_motor_no_usa_valor_cero_y_sin_curva(self):
        e=calcular_mapa_cp_variable(DEFAULTS,1.1,20,210,215,5,5)
        self.assertIsNone(svg_cortes_mapa(e,'trabajo_neto'))
        self.assertIsNone(svg_cortes_mapa(e,'rendimiento'))
        svg=svg_mapa_viabilidad(e)
        self.assertEqual(svg.count('data-estado='),25)
        self.assertNotIn('data-magnitud=',svg)

    def test_rechaza_magnitud_ajena_y_no_altera_malla(self):
        e=calcular_mapa_cp_variable(DEFAULTS,8,20,1450,1650,5,5)
        original=repr(e['filas'])
        with self.assertRaises(ValueError):
            svg_cortes_mapa(e,'gamma')
        svg_cortes_mapa(e,'trabajo_neto')
        svg_mapa_viabilidad(e)
        self.assertEqual(original,repr(e['filas']))

    def test_ruta_flask_cinco_graficas_y_visor_original(self):
        form={**{k:str(v) for k,v in DEFAULTS.items()},'accion':'mapa',
              'mapa_cp_rp_min':'2','mapa_cp_rp_max':'20',
              'mapa_cp_T3_min':'1200','mapa_cp_T3_max':'1800',
              'mapa_cp_n_rp':'7','mapa_cp_n_T3':'7'}
        r=app.test_client().post('/',data=form)
        self.assertEqual(r.status_code,200)
        t=r.get_data(as_text=True)
        for k in ('Mapa de viabilidad','Cortes · Trabajo neto','Cortes · Rendimiento',
                  'data-plot-viewer="cp-mapa"','data-estado=','data-magnitud='):
            self.assertIn(k,t)

    def test_representacion_sin_motor_sigue_mostrando_estado(self):
        form={**{k:str(v) for k,v in DEFAULTS.items()},'accion':'mapa',
              'mapa_cp_rp_min':'1.1','mapa_cp_rp_max':'20',
              'mapa_cp_T3_min':'210','mapa_cp_T3_max':'215',
              'mapa_cp_n_rp':'5','mapa_cp_n_T3':'5'}
        r=app.test_client().post('/',data=form)
        t=r.get_data(as_text=True)
        self.assertEqual(r.status_code,200)
        self.assertIn('Mapa de viabilidad',t)
        self.assertIn('No hay puntos motores',t)
        self.assertNotIn('Cortes · Trabajo neto',t)
