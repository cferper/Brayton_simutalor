"""Extrae una sección bidimensional documentada de HPC.map y HPT.map.

Uso: python scripts/extraer_mapas_tmats_47.py HPC.map HPT.map salida.json
Datos de origen: nasa/T-MATS Resources/JT9D_Public_NPSSv241/Maps_and_Elements
Se conserva alpha=0 de HPC; no se extrapolan otras posiciones de geometría.
"""

import hashlib
import json
from pathlib import Path
import re
import sys


BASE = "https://github.com/nasa/T-MATS/blob/master/Resources/JT9D_Public_NPSSv241/Maps_and_Elements/"


def numeros(cadena):
    return [float(v) for v in re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", cadena)]


def tabla(texto, nombre, eje_filas, eje_columnas, campo, *, restringir_alpha=False):
    bloque = texto.split(f"Table {nombre}(",1)[1].split(".interp",1)[0]
    if restringir_alpha:
        bloque = bloque.split("alphaMap= 90.000",1)[0]
    columnas = re.search(rf"{eje_columnas}\s*=\s*\{{([^}}]+)\}}",bloque)
    if columnas is None:
        raise ValueError(f"Falta eje de columnas en {nombre}")
    eje_x = numeros(columnas.group(1))
    filas = re.findall(rf"{eje_filas}\s*=\s*([0-9.]+)\s*\{{(.*?){campo}\s*=\s*\{{([^}}]+)\}}",bloque,re.S)
    if not filas:
        raise ValueError(f"No se encontraron filas en {nombre}")
    eje_y, matriz = [], []
    for fila, _, valores in filas:
        valores = numeros(valores)
        if len(valores) != len(eje_x):
            raise ValueError(f"Longitud inválida en {nombre}, fila {fila}")
        eje_y.append(float(fila))
        matriz.append(valores)
    return eje_y,eje_x,matriz


def extraer(hpc_path, hpt_path):
    hpc = Path(hpc_path).read_text(encoding="utf-8")
    hpt = Path(hpt_path).read_text(encoding="utf-8")
    eje_nc = eje_r = None
    comp = {}
    for tabla_nom,campo,clave in (("TB_Wc","WcorrMap","wc"),
                                   ("TB_PR","PratioMap","pr"),
                                   ("TB_eff","effAdiabMap","eta")):
        ny,rx,matriz=tabla(hpc,tabla_nom,"NcorrMap","RlineMap",campo,
                           restringir_alpha=True)
        if eje_nc is not None and (ny!=eje_nc or rx!=eje_r):
            raise ValueError("Los ejes de las tablas del compresor difieren")
        eje_nc,eje_r=ny,rx
        comp[clave]=matriz
    eje_nt = eje_prt = None
    turb = {}
    for tabla_nom,campo,clave in (("TB_Wp","WcMap","wc"),
                                   ("TB_eff","effMap","eta")):
        ny,rx,matriz=tabla(hpt,tabla_nom,"NcDes","PRdes",campo)
        if eje_nt is not None and (ny!=eje_nt or rx!=eje_prt):
            raise ValueError("Los ejes de las tablas de turbina difieren")
        eje_nt,eje_prt=ny,rx
        turb[clave]=matriz
    for matriz in (comp["eta"],turb["eta"]):
        if any(not 0 < v <= 1 for fila in matriz for v in fila):
            raise ValueError("Eficiencias originales fuera de (0,1]")
    comp.update(ncorr=eje_nc,rline=eje_r)
    turb.update(ncorr=eje_nt,pr=eje_prt)
    return {"licencia":"Apache-2.0", "origen":"NASA T-MATS — JT9D Public NPSS v2.4.1",
            "nota":"HPC alpha=0 exclusivamente; magnitudes Wc nativas del mapa, escaladas en el punto de diseño",
            "fuentes":{nombre:{"url":BASE+nombre,"sha256":hashlib.sha256(Path(ruta).read_bytes()).hexdigest()}
                       for nombre,ruta in (("HPC.map",hpc_path),("HPT.map",hpt_path))},
            "compresor":comp,"turbina":turb}


def main():
    if len(sys.argv)!=4:
        raise SystemExit("Uso: extraer_mapas_tmats_47.py HPC.map HPT.map salida.json")
    contenido = extraer(sys.argv[1],sys.argv[2])
    Path(sys.argv[3]).write_text(json.dumps(contenido,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(len(contenido["compresor"]["ncorr"]),len(contenido["compresor"]["rline"]),
          len(contenido["turbina"]["ncorr"]),len(contenido["turbina"]["pr"]))


if __name__=="__main__":
    main()
