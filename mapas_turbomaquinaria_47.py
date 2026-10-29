"""Mapas T-MATS adaptados, interpolación acotada y escalado a monoeje.

Los mapas de origen proceden de componentes HPC/HPT del ejemplo JT9D
de NASA. **No** son medidas del motor educativo ni un JT9D monoeje.
"""

import json
from math import isfinite, sqrt
from numbers import Real
from pathlib import Path


T_REF_MAPA = 288.15  # K; referencia explícita de corrección usada aquí
P_REF_MAPA = 101.325  # kPa; ambas magnitudes en unidades del proyecto
RUTA_MAPAS = Path(__file__).resolve().parent / "data" / "tmats_47" / "mapas_normalizados.json"


def _finito_positivo(x, nombre):
    if isinstance(x, bool) or not isinstance(x, Real) or not isfinite(x) or x <= 0:
        raise ValueError(f"{nombre} debe ser positivo y finito.")
    return float(x)


def cargar_mapas(ruta=RUTA_MAPAS):
    with Path(ruta).open(encoding="utf-8") as archivo:
        return json.load(archivo)


def _tramo(eje, valor):
    if not isfinite(valor) or not eje[0] <= valor <= eje[-1]:
        raise ValueError(f"Fuera del dominio del mapa [{eje[0]}, {eje[-1]}]: {valor}.")
    for j in range(len(eje)-1):
        if eje[j] <= valor <= eje[j+1]:
            return j, (valor-eje[j])/(eje[j+1]-eje[j])
    raise ValueError("Eje de mapa inválido.")


def interpolar_bilineal(eje_filas, eje_columnas, tabla, fila, columna):
    """Interpolación afín en cada eje; prohíbe cualquier extrapolación."""
    i, ti = _tramo(eje_filas, fila)
    j, tj = _tramo(eje_columnas, columna)
    abajo = tabla[i][j]*(1-tj)+tabla[i][j+1]*tj
    arriba = tabla[i+1][j]*(1-tj)+tabla[i+1][j+1]*tj
    return abajo*(1-ti)+arriba*ti


def flujo_corregido(mdot, Tt, pt):
    """ṁcorr=ṁ sqrt(Tt/Tref)/(pt/Pref) [kg/s de referencia]."""
    return (_finito_positivo(mdot,"Gasto")
            *sqrt(_finito_positivo(Tt,"Temperatura total")/T_REF_MAPA)
            /(_finito_positivo(pt,"Presión total")/P_REF_MAPA))


def giro_corregido(rpm, Tt):
    """Ncorr=N/sqrt(Tt/Tref); rpm corregidas (no adimensional)."""
    return _finito_positivo(rpm,"Giro")/sqrt(
        _finito_positivo(Tt,"Temperatura total")/T_REF_MAPA)


def calibrar_mapas(resultado_diseno, mdot_aire_diseno=20.0, rpm_diseno=20000.0,
                   *, mapas=None):
    """Determina cuatro escalas por componente en un punto de diseño coherente.

    Punto nativo: HPC (Ncorr=1,Rline=2,alpha=0), HPT (Nc=100,PR=5).
    Las escalas de velocidades difieren porque cada componente recibe Tt
    distinto aunque N mecánica sea común.
    """
    ma = _finito_positivo(mdot_aire_diseno,"Caudal de aire de diseño")
    rpm = _finito_positivo(rpm_diseno,"Giro de diseño")
    d = resultado_diseno
    if d["diagnosticos"]["tipo_tobera"] != "convergente":
        raise ValueError("La calibración de referencia exige la tobera convergente de diseño.")
    c, b, t, d2 = (d[k] for k in ("compresor","combustor","turbina","difusor"))
    pt2,Tt2 = d2["presion_remanso"],d2["temperatura_remanso"]
    pt3,Tt3 = b["p3"], b["T3"]
    rp_c = c["p2"]/pt2
    rp_t = pt3/t["p4"]
    if min(rp_c,rp_t) <= 1 or d["tobera"] is None:
        raise ValueError("Punto de diseño sin margen termodinámico.")
    mapas = cargar_mapas() if mapas is None else mapas
    cm, tm = mapas["compresor"], mapas["turbina"]
    def ic(campo):
        return interpolar_bilineal(cm["ncorr"],cm["rline"],cm[campo],1.,2.)
    def it(campo):
        return interpolar_bilineal(tm["ncorr"],tm["pr"],tm[campo],100.,5.)
    # Eta isentrópica real en condiciones del núcleo anterior, no una
    # eficiencia efectiva deducida del flujo de aire.
    # Las entradas se fijan explícitamente por el usuario/diseño.
    eta_c = (c["h2s"]-c["h1"])/(c["h2"]-c["h1"])
    eta_t = t["rendimiento_turbina"]
    mg = ma*(1+b["f"])
    referencia = {
        "mdot_aire":ma,"mdot_gases":mg,"rpm_mecanicas":rpm,
        "Tt2":Tt2,"pt2":pt2,"Tt3":Tt3,"pt3":pt3,
        "rp_compresor":rp_c,"eta_compresor":eta_c,
        "rp_turbina":rp_t,"eta_turbina":eta_t,
        "f":b["f"],
        "compresor":{"wc":flujo_corregido(ma,Tt2,pt2)/ic("wc"),
                      "pr":(rp_c-1)/(ic("pr")-1),
                      "eta":eta_c/ic("eta"),
                      "nc":1./giro_corregido(rpm,Tt2)},
        "turbina":{"wc":flujo_corregido(mg,Tt3,pt3)/it("wc"),
                   "pr":(rp_t-1)/(5.-1.),
                   "eta":eta_t/it("eta"),
                   "nc":100./giro_corregido(rpm,Tt3)},
    }
    if any(v<=0 or not isfinite(v) for partes in (referencia["compresor"],referencia["turbina"])
           for v in partes.values()):
        raise ValueError("Escalas de diseño no admisibles.")
    return referencia


def consultar_compresor(referencia, rpm, Tt2, pt2, rline, *, mapas=None):
    mapas = cargar_mapas() if mapas is None else mapas
    m = mapas["compresor"]
    esc = referencia["compresor"]
    nmap = giro_corregido(rpm,Tt2)*esc["nc"]
    def i(campo):
        return interpolar_bilineal(m["ncorr"],m["rline"],m[campo],nmap,rline)
    wc, pr, eta = i("wc")*esc["wc"],1+(i("pr")-1)*esc["pr"],i("eta")*esc["eta"]
    if not 0 < eta <= 1 or pr <= 1:
        raise ValueError("Compresor fuera del dominio físico de eficiencia o presión.")
    ma = wc*(pt2/P_REF_MAPA)/sqrt(Tt2/T_REF_MAPA)
    return {"gasto_masico_aire":ma,"caudal_corregido":wc,"giro_corregido":giro_corregido(rpm,Tt2),
            "giro_mapa":nmap,"rline":rline,"rp":pr,"eta":eta,
            "distancia_rline_bombeo":rline-1.0}


def consultar_turbina(referencia, rpm, Tt3, pt3, rp_turbina, *, mapas=None):
    _finito_positivo(rp_turbina,"Relación de expansión de turbina")
    mapas = cargar_mapas() if mapas is None else mapas
    m = mapas["turbina"]
    esc = referencia["turbina"]
    nmap = giro_corregido(rpm,Tt3)*esc["nc"]
    prmap = 1+(rp_turbina-1)/esc["pr"]
    def i(campo):
        return interpolar_bilineal(m["ncorr"],m["pr"],m[campo],nmap,prmap)
    wc, eta = i("wc")*esc["wc"],i("eta")*esc["eta"]
    if not 0 < eta <= 1:
        raise ValueError("Turbina fuera de dominio físico de eficiencia.")
    mg = wc*(pt3/P_REF_MAPA)/sqrt(Tt3/T_REF_MAPA)
    return {"gasto_masico_gases":mg,"caudal_corregido":wc,
            "giro_corregido":giro_corregido(rpm,Tt3),"giro_mapa":nmap,
            "pr_mapa":prmap,"rp":rp_turbina,"eta":eta}
