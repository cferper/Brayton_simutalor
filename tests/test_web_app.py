"""Pruebas HTTP del único dashboard cp(T) y del archivo histórico de solo lectura."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ciclo_cp_variable import resolver_ciclo
import reporting
import web_app

BASE = {k: str(v) for k,v in web_app.DEFAULTS.items()}


class WebTests(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.carpeta = Path(temporal.name) / 'outputs'
        config = patch.dict(web_app.app.config, {'OUTPUTS_DIR': self.carpeta,
                            'TESTING': False, 'PROPAGATE_EXCEPTIONS': False})
        config.start()
        self.addCleanup(config.stop)
        self.client = web_app.app.test_client()

    def test_formulario_seven_campos_y_staticos(self):
        respuesta = self.client.get('/')
        texto = respuesta.get_data(as_text=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(texto.count('type="number"'), 10)  # 7 del ciclo + 3 OFAT
        for key in BASE:
            self.assertIn(f'name="{key}"', texto)
        self.assertIn('Restablecer valores', texto)
        with self.client.get('/static/style.css') as recurso:
            self.assertEqual(recurso.status_code, 200)
        self.assertFalse(self.carpeta.exists())

    def test_post_sin_informes_constantes(self):
        datos = {**BASE, 'accion':'normal'}
        p = resolver_ciclo(288.15,1600,10,100,.85,.9,.05)
        respuesta = self.client.post('/', data=datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(f'{p["trabajo_neto"]:.3f}', respuesta.get_data(as_text=True))
        self.assertFalse(self.carpeta.exists())

    def test_parametros_invalidos_y_acciones_vetadas(self):
        for field,value in [('T1',''),('T3','nan'),('p1','inf'),('eta_t','0')]:
            with self.subTest(field=field):
                respuesta = self.client.post('/', data={**BASE,'accion':'normal',field:value})
                self.assertEqual(respuesta.status_code, 400)
                self.assertNotIn('data-kpi=',respuesta.get_data(as_text=True))
        for accion in ('mapa','segunda_ley'):
            with self.subTest(accion=accion):
                self.assertEqual(self.client.post('/',data={**BASE,'accion':accion}).status_code,400)
        self.assertFalse(self.carpeta.exists())

    def test_error_inesperado_es_500_sin_traza_visible(self):
        with patch.object(web_app, 'preparar_resultados', side_effect=RuntimeError('SECRETO_INTERNO')):
            with self.assertLogs(web_app.app.logger, level='ERROR'):
                r = self.client.post('/',data={**BASE,'accion':'normal'})
        self.assertEqual(r.status_code,500)
        self.assertIn('error interno',r.get_data(as_text=True))
        self.assertNotIn('SECRETO_INTERNO',r.get_data(as_text=True))

    def test_historial_legado_solo_lectura_y_descarga_exacta(self):
        contenido = reporting.MARCA_INICIO + '<html>histórico gas perfecto</html>' + reporting.MARCA_FINAL
        ruta = reporting.guardar_informe_html(contenido,self.carpeta,datetime.now(timezone.utc))
        antes = ruta.read_bytes()
        portada = self.client.get('/').get_data(as_text=True)
        self.assertIn(ruta.name,portada)
        self.assertIn('histórico',portada)
        r = self.client.get('/informes/'+ruta.name)
        self.assertEqual(r.status_code,200)
        descarga = self.client.get('/informes/'+ruta.name+'?descargar=1')
        self.assertEqual(descarga.data,antes)
        self.assertIn('attachment;',descarga.headers['Content-Disposition'])
        self.assertEqual(antes,ruta.read_bytes())

    def test_documentacion_y_rutas_ajenas_rechazadas(self):
        for path in ('/main.py','/informes/main.py','/informes/..%2Fmain.py',
                     '/modelo-cp-variable','/documentacion/web_app.py'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code,404)
        for doc in ('README.md','CODE_WALKTHROUGH.md'):
            self.assertEqual(self.client.get('/documentacion/'+doc).status_code,200)

    def test_servidor_arranca_en_un_solo_puerto_local(self):
        with patch.object(web_app.app,'run') as run:
            web_app.iniciar_servidor()
        run.assert_called_once_with(host='127.0.0.1',port=5000,debug=False,
                                    use_reloader=False,threaded=False)

if __name__=='__main__':
    unittest.main()
