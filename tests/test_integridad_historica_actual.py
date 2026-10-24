"""Integridad de informes gas perfecto consultados, sin recálculo, desde cp(T).

Estos tests sustituyen las verificaciones Flask V.5 incompatibles con el
dashboard único cp(T), preservando las comprobaciones de integridad que sí
siguen siendo relevantes para los informes históricos de solo lectura.
"""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import dashboard
import main
import reporting
import segunda_ley
from viabilidad import evaluar_punto
import web_app


class IntegridadHistoricaActual(unittest.TestCase):
    def setUp(self):
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.destino = Path(carpeta.name) / "outputs"
        config = patch.dict(web_app.app.config, OUTPUTS_DIR=self.destino,
                            TESTING=False, PROPAGATE_EXCEPTIONS=False)
        config.start()
        self.addCleanup(config.stop)
        self.cliente = web_app.app.test_client()
        self.p = main.PARAMETROS_PREDETERMINADOS.copy()
        p = self.p
        puntos = {
            "ideal": evaluar_punto(p["T1"], p["T3"], p["gamma"], p["cp"],
                                    p["relacion_presiones"], p["p1"]),
            "noideal": evaluar_punto(p["T1"], p["T3"], p["gamma"], p["cp"],
                                      p["relacion_presiones"], p["p1"], p["eta_c"],
                                      p["eta_t"], p["perdida_presion_combustor"]),
        }
        self.estudio = json.loads(json.dumps(
            segunda_ley.analizar_segunda_ley(puntos, p["cp"], p["gamma"], 288.15)
        ))

    def _guardar(self, estudio=None):
        metadata = {
            "dashboard": 1,
            "tipo": "segunda_ley",
            "parametros": self.p.copy(),
            "segunda_ley": self.estudio if estudio is None else estudio,
            "fecha": "2026-10-23T10:00:00+02:00",
            "git": {"commit": "a" * 40, "modificado": False},
        }
        paneles = {k: "<p>Panel histórico conservado</p>" for k in
                   ("resultados", "optimizacion", "sensibilidad", "mapa", "segunda_ley")}
        valores = self.p.copy()
        valores["perdida_presion_combustor"] *= 100
        valores["T0"] = 288.15
        contenido = (reporting.MARCA_INICIO + dashboard.renderizar_dashboard(
            valores, contenidos=paneles, metadata=metadata, modo_local=False
        ) + reporting.MARCA_FINAL)
        return reporting.guardar_informe_html(contenido, self.destino,
                                             datetime.now(timezone.utc))

    def _adulterar(self, ruta, cambio):
        texto = ruta.read_text(encoding="utf-8")
        patron = r'(<script type="application/json" id="brayton-metadata">)(.*?)(</script>)'
        original = re.search(patron, texto, re.S)
        metadata = json.loads(original[2])
        cambio(metadata)
        texto = re.sub(patron, lambda match: match[1] +
                       json.dumps(metadata, allow_nan=True) + match[3], texto,
                       count=1, flags=re.S)
        ruta.write_text(texto, encoding="utf-8")
        return ruta.read_bytes()

    def test_json_legado_valido_se_presenta_y_descarga_sin_mutarlo(self):
        ruta = self._guardar()
        original = ruta.read_bytes()
        self.assertTrue(segunda_ley.validar_estudio_reutilizable(self.estudio, self.p))
        with patch.object(web_app, "preparar_resultados",
                          side_effect=AssertionError("No recalcular el ciclo")):
            respuesta = self.cliente.get("/informes/" + ruta.name)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Panel histórico conservado", respuesta.get_data(as_text=True))
        self.assertEqual(self.cliente.get("/informes/" + ruta.name +
                                         "?descargar=1").data, original)
        self.assertEqual(ruta.read_bytes(), original)

    def test_referencia_de_los_nueve_parametros_legados_no_se_puede_mezclar(self):
        self.assertTrue(segunda_ley.validar_estudio_reutilizable(self.estudio, self.p))
        for clave in self.p:
            with self.subTest(parametro=clave):
                distintos = {**self.p, clave: self.p[clave] * 1.01}
                self.assertFalse(segunda_ley.validar_estudio_reutilizable(
                    self.estudio, distintos))

    def test_estructuras_fisicas_ausentes_se_rechazan(self):
        cambios = (
            lambda e: e.pop("modelos"),
            lambda e: e["modelos"].pop("ideal"),
            lambda e: e["modelos"]["ideal"].pop("componentes"),
            lambda e: e["modelos"]["ideal"]["componentes"].pop("turbina"),
            lambda e: e["modelos"]["ideal"].update(temperaturas=[288., 400.]),
            lambda e: e["modelos"]["noideal"].update(entropias=[0., 1., 2.]),
            lambda e: e["modelos"]["noideal"].update(camara={}),
        )
        for numero, cambio in enumerate(cambios):
            with self.subTest(caso=numero):
                estudio = deepcopy(self.estudio)
                cambio(estudio)
                self.assertFalse(segunda_ley.validar_estudio_reutilizable(estudio, self.p))

    def test_tipos_no_finitos_y_booleanos_se_rechazan(self):
        cambios = (
            lambda e: e.update(cp=True),
            lambda e: e.update(T0="288.15"),
            lambda e: e["modelos"]["ideal"].update(temperaturas="texto"),
            lambda e: e["modelos"]["ideal"]["temperaturas"].__setitem__(1, True),
            lambda e: e["modelos"]["noideal"].update(viable=1),
            lambda e: e["modelos"]["noideal"]["componentes"]["turbina"].update(valor=False),
        )
        for numero, cambio in enumerate(cambios):
            with self.subTest(caso=numero):
                estudio = deepcopy(self.estudio)
                cambio(estudio)
                self.assertFalse(segunda_ley.validar_estudio_reutilizable(estudio, self.p))
        for valor in (None, float("nan"), float("inf"), float("-inf"), "nan"):
            with self.subTest(valor=str(valor)):
                estudio = deepcopy(self.estudio)
                estudio["modelos"]["ideal"]["entropias"][2] = valor
                self.assertFalse(segunda_ley.validar_estudio_reutilizable(estudio, self.p))

    def test_incoherencias_fisicas_y_exergia_se_rechazan(self):
        cambios = (
            lambda e: e["modelos"]["ideal"]["temperaturas"].__setitem__(1, 444.),
            lambda e: e["modelos"]["noideal"]["presiones"].__setitem__(2, 999.),
            lambda e: e["modelos"]["ideal"]["entropias"].__setitem__(1, 0.4),
            lambda e: e["modelos"]["noideal"]["componentes"]["turbina"].update(bruto=.4),
            lambda e: e["modelos"]["noideal"]["componentes"]["turbina"].update(exergia_destruida=100.),
            lambda e: e["modelos"]["noideal"].update(suma_componentes=0.),
            lambda e: e["modelos"]["noideal"]["camara"].update(total=12.),
            lambda e: e["modelos"]["noideal"].update(viable=False, estado="diagnostico_no_motor"),
        )
        for numero, cambio in enumerate(cambios):
            with self.subTest(caso=numero):
                estudio = deepcopy(self.estudio)
                cambio(estudio)
                self.assertFalse(segunda_ley.validar_estudio_reutilizable(estudio, self.p))

    def test_json_invalidado_no_se_reutiliza_y_original_se_puede_descargar(self):
        ruta = self._guardar()
        original = self._adulterar(ruta, lambda d: d["segunda_ley"]["modelos"]["ideal"].pop("componentes"))
        vista = self.cliente.get("/informes/" + ruta.name)
        self.assertEqual(vista.status_code, 200)
        self.assertIn("no se reutilizarán", vista.get_data(as_text=True))
        self.assertEqual(self.cliente.get("/informes/" + ruta.name + "?descargar=1").data,
                         original)
        self.assertEqual(ruta.read_bytes(), original)

    def test_metadata_invalida_devuelve_422_y_preserva_archivo(self):
        ruta = self._guardar()
        original = ruta.read_text(encoding="utf-8")
        ruta.write_text(original.replace('"dashboard": 1', '"dashboard": {', 1),
                        encoding="utf-8")
        dañado = ruta.read_bytes()
        respuesta = self.cliente.get("/informes/" + ruta.name)
        self.assertEqual(respuesta.status_code, 422)
        self.assertIn("Metadatos", respuesta.get_data(as_text=True))
        self.assertEqual(self.cliente.get("/informes/" + ruta.name + "?descargar=1").data,
                         dañado)
        self.assertEqual(ruta.read_bytes(), dañado)

    def test_post_cp_no_reutiliza_resultados_de_informe_antiguo(self):
        ruta = self._guardar()
        original = ruta.read_bytes()
        entradas = {clave: str(valor) for clave, valor in web_app.DEFAULTS.items()}
        with patch.object(web_app, "preparar_resultados", wraps=web_app.preparar_resultados) as preparar:
            respuesta = self.cliente.post("/", data={**entradas, "accion": "normal",
                                                  "informe_origen": ruta.name})
        self.assertEqual(respuesta.status_code, 200)
        preparar.assert_called_once()
        self.assertEqual(ruta.read_bytes(), original)
        self.assertEqual(len(list(self.destino.iterdir())), 1)


if __name__ == "__main__":
    unittest.main()
