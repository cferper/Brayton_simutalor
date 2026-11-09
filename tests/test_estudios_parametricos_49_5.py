"""Regresiones focalizadas del agregador de estudios M49.5."""

from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from estudios_parametricos_49_5 import calcular_estudio_49_5, configurar_estudio_49_5
from turborreactor_web import simular_turborreactor, valores_turborreactor


ROOT = Path(__file__).resolve().parents[1]


class Estudios49_5(unittest.TestCase):
    def setUp(self):
        self.valores = valores_turborreactor()

    def test_mach_igual_a_solucion_individual_modo_a(self):
        v = dict(self.valores, gasto_masico_aire="20")
        d = calcular_estudio_49_5(v,{"tipo":"mach","mach_inicio":0,
                                  "mach_fin":.6,"mach_puntos":3})
        self.assertEqual(d["resumen"]["total"],3)
        self.assertEqual(d["constantes"]["T3"],v["T3"])
        for p in d["puntos"]:
            r = simular_turborreactor(dict(v, mach=str(p["mach"])))
            self.assertAlmostEqual(p["empuje_especifico"],r["prestaciones"]["empuje_especifico_neto"],places=8)
            self.assertAlmostEqual(p["empuje_N"],r["prestaciones_absolutas"]["empuje_neto"],places=6)
        self.assertEqual(d["unidades"]["TSFC"],"kg/(N·h)")

    def test_t3_empuje_tsfc_y_constante_mach(self):
        d = calcular_estudio_49_5(self.valores,{"tipo":"T3","T3_inicio":1400,
                        "T3_fin":1700,"T3_puntos":3})
        self.assertEqual([p["T3"] for p in d["puntos"]],[1400,1550,1700])
        self.assertTrue(all(p["mach"]==0 for p in d["puntos"]))
        self.assertTrue(all(p["TSFC"] is None or p["empuje_especifico"]>0 for p in d["puntos"]))
        self.assertTrue(all(p["empuje_N"] is None for p in d["puntos"]))

    def test_mapa_dimensiones_y_ejes(self):
        d = calcular_estudio_49_5(self.valores,{"tipo":"mapa","mach_inicio":0,
            "mach_fin":.6,"mach_puntos":3,"T3_inicio":1400,"T3_fin":1800,"T3_puntos":4})
        self.assertEqual((len(d["ejes"]["x"]),len(d["ejes"]["y"])),(3,4))
        self.assertEqual(len(d["puntos"]),12)
        self.assertEqual([p["mach"] for p in d["puntos"][:3]],[0,.3,.6])
        self.assertTrue(all(p["T3"]==1400 for p in d["puntos"][:3]))

    def test_modos_b_y_c_usando_su_modelo(self):
        casos = [("fijo",dict(area_garganta_fija="0.0473481164")),
                 ("acoplado",{})]
        for modo,extras in casos:
            with self.subTest(modo=modo):
                v=dict(self.valores,modo_caudal=modo,**extras)
                d=calcular_estudio_49_5(v,{"tipo":"mach","mach_inicio":0,
                    "mach_fin":.2,"mach_puntos":2})
                for p in d["puntos"]:
                    self.assertIn(p["estado"],("valido","sin_solucion","fallo_numerico","fuera_dominio"))
                    if p["estado"]=="valido":
                        r=simular_turborreactor(dict(v,mach=str(p["mach"])))
                        self.assertAlmostEqual(p["empuje_especifico"],
                            r["prestaciones"]["empuje_especifico_neto"],places=7)

    def test_ausencia_de_solucion_no_es_cero(self):
        v=dict(self.valores,T3="400")
        d=calcular_estudio_49_5(v,{"tipo":"mach","mach_inicio":0,
            "mach_fin":.2,"mach_puntos":2})
        self.assertEqual(len(d["puntos"]),2)
        for p in d["puntos"]:
            self.assertNotEqual(p["estado"],"valido")
            self.assertIsNone(p["empuje_N"])
            self.assertIsNone(p["TSFC"])

    def test_limites_validacion_costo(self):
        with self.assertRaises(ValueError):
            configurar_estudio_49_5({"tipo":"mapa","mach_inicio":0,
                "mach_fin":.96,"mach_puntos":11,"T3_inicio":1400,
                "T3_fin":1800,"T3_puntos":11},"impuesto")
        with self.assertRaises(ValueError):
            configurar_estudio_49_5({"tipo":"mapa","mach_inicio":0,
                "mach_fin":.6,"mach_puntos":9,"T3_inicio":1400,
                "T3_fin":1800,"T3_puntos":9},"acoplado")

    def test_tsfc_no_definido_si_empuje_no_positivo(self):
        falso={"tobera":{"resuelto":True},"prestaciones":{
            "empuje_especifico_neto":-2.,"TSFC_kg_N_h":1234.},
            "prestaciones_absolutas":{"empuje_neto":-20.}}
        with patch('estudios_parametricos_49_5.simular_turborreactor',return_value=falso):
            d=calcular_estudio_49_5(self.valores,{"tipo":"mach",
                "mach_inicio":0,"mach_fin":.2,"mach_puntos":2})
        self.assertTrue(all(p["TSFC"] is None for p in d["puntos"]))
        self.assertTrue(all(p["empuje_especifico"]==-2 for p in d["puntos"]))

    def test_js_sintaxis_csv_y_no_interpolacion(self):
        archivo=ROOT/'static/estudios_parametricos_49_5.js'
        script=("const c=require(process.argv[1]); const r=c.csv49({modo:'impuesto',"
                "tipo:'mach',constantes:{T3:'1600'},puntos:[{mach:0,T3:1600,estado:'valido',"
                "motivo:null,empuje_N:null,empuje_especifico:5,TSFC:.2}]});"
                "if(!r.includes('empuje_especifico')||!r.includes('valido')||!r.includes('1600'))process.exit(2)")
        check=subprocess.run(['node','--check',str(archivo)],capture_output=True,text=True)
        self.assertEqual(check.returncode,0,check.stderr)
        run=subprocess.run(['node','-e',script,str(archivo)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)

    def test_rutas_vistas_y_controlador_original_preservados(self):
        html=(ROOT/'templates/turborreactor.html').read_text(encoding='utf-8')
        api=(ROOT/'web_app.py').read_text(encoding='utf-8')
        js=(ROOT/'static/estudios_parametricos_49_5.js').read_text(encoding='utf-8')
        for ruta in ('/turborreactor/interactivo','/turborreactor','/brayton',
                     '/api/turborreactor/simular','/api/turborreactor/estudio'):
            self.assertIn(ruta,api)
        for campo in ('mach_inicio','mach_fin','T3_inicio','T3_fin'):
            self.assertIn('name="'+campo+'"',html)
        self.assertIn("{% if interfaz=='interactivo' %}",html)
        self.assertIn('data-study49-view="punto"',html)
        self.assertIn('data-study49-view="estudios"',html)
        self.assertIn("if(peticion)return;",js)
        self.assertIn("if(actual!==version)return;",js)
        self.assertIn("control=new AbortController()",js)


if __name__=='__main__':
    unittest.main()
