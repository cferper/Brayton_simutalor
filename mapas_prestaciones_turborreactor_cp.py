"""Barridos paramétricos de un turborreactor cp(T), NO mapas fuera de diseño.

Los parámetros del núcleo se prescriben independientemente en cada punto;
no existen mapas de compresor/turbina, caudales ni geometría del motor.
"""

from collections import Counter
from combustible_cp_variable import resolver_turborreactor_con_combustible
from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo
from vuelo_cp_variable import _finito


ESTADOS = ("valido", "empuje_no_positivo", "sin_expansion", "tobera_no_resuelta",
           "inadmisible", "fallo_numerico")
RESTRICCIONES = ("T3_max", "rp_min", "rp_max", "mach_min", "mach_max",
                 "altitud_min", "altitud_max", "exigir_empuje_positivo",
                 "exigir_margen_tobera")


def _eje(valores, nombre, minimo, maximo, incluir_maximo=True):
    """Devuelve tupla ordenada de reales finitos; rechaza malla vacía."""
    try:
        v = tuple(valores)
    except TypeError as exc:
        raise ValueError(f"{nombre}: se requiere secuencia de valores.") from exc
    if not v or not all(_finito(x) for x in v):
        raise ValueError(f"{nombre}: vector no vacío de números finitos.")
    if any(not (minimo <= x <= maximo if incluir_maximo else minimo <= x < maximo)
           for x in v):
        raise ValueError(f"{nombre}: valores fuera de límites.")
    if any(v[i] >= v[i+1] for i in range(len(v)-1)):
        raise ValueError(f"{nombre}: valores estrictamente crecientes y únicos.")
    return v


def _restricciones(configuracion):
    """Normaliza restricciones de diseño; no inventa límites de materiales."""
    config = dict(configuracion or {})
    if set(config) - set(RESTRICCIONES):
        raise ValueError("Restricción desconocida: " + str(sorted(set(config)-set(RESTRICCIONES))))
    for k, val in config.items():
        if k.startswith("exigir_"):
            if not isinstance(val, bool):
                raise ValueError(f"{k} debe ser booleano.")
        elif not _finito(val):
            raise ValueError(f"{k} debe ser un real finito.")
    for minimo, maximo in (("rp_min", "rp_max"), ("mach_min", "mach_max"),
                           ("altitud_min", "altitud_max")):
        if minimo in config and maximo in config and config[minimo] > config[maximo]:
            raise ValueError(f"Intervalo incoherente: {minimo}/{maximo}.")
    if "T3_max" in config and not 200 <= config["T3_max"] <= 2000:
        raise ValueError("T3_max debe quedar dentro de 200–2000 K.")
    if ("rp_min" in config and config["rp_min"] <= 1 or
            "mach_min" in config and config["mach_min"] < 0 or
            "mach_max" in config and not config["mach_max"] < 1 or
            "altitud_min" in config and config["altitud_min"] < 0 or
            "altitud_max" in config and config["altitud_max"] > 20000):
        raise ValueError("Restricción fuera del dominio del modelo.")
    config.setdefault("exigir_empuje_positivo", True)
    config.setdefault("exigir_margen_tobera", True)
    return config


def _incumplimiento(entradas, config):
    """Motivo de descarte por restricciones antes de llamar al solucionador."""
    for variable, inferior, superior in (
        ("rp", "rp_min", "rp_max"),
        ("mach", "mach_min", "mach_max"),
        ("altitud_geopotencial", "altitud_min", "altitud_max")):
        valor = entradas.get(variable)
        if valor is None:
            continue
        if inferior in config and valor < config[inferior]:
            return "restriccion_" + inferior
        if superior in config and valor > config[superior]:
            return "restriccion_" + superior
    if "T3_max" in config and entradas["T3"] > config["T3_max"]:
        return "restriccion_T3_max"
    return None


def _punto(entradas, indices, config):
    """Ejecuta una configuración; conserva None para resultados inexistentes."""
    base = {"indices": indices, "entradas": dict(entradas), "estado": None,
            "motivo": None, "Fs": None, "TSFC_kg_N_h": None, "f": None,
            "trabajo_compresor": None, "T4": None, "p4": None,
            "regimen_tobera": None, "resultado": None,
            "cumple_restricciones": False}
    motivo = _incumplimiento(entradas, config)
    if motivo is not None:
        base.update(estado="inadmisible", motivo=motivo)
        return base
    try:
        r = resolver_turborreactor_con_combustible(**entradas)
    except EstadoFueraDeRango as exc:
        base.update(estado="inadmisible", motivo=f"dominio_termico: {exc}")
        return base
    except ValueError as exc:
        base.update(estado="inadmisible", motivo=f"dominio_fisico: {exc}")
        return base
    except ErrorNumericoCiclo as exc:
        base.update(estado="fallo_numerico", motivo=f"error_numerico: {exc}")
        return base
    # No se captura Exception: TypeError, AttributeError y otros errores de
    # programación deben hacerse visibles durante el desarrollo.
    base["resultado"] = r
    base["f"] = r["combustor"]["f"]
    base["trabajo_compresor"] = r["compresor"]["trabajo_compresor"]
    base["T4"] = r["turbina"]["T4"]
    base["p4"] = r["turbina"]["p4"]
    if r["tobera"] is None:
        base.update(estado="sin_expansion", motivo="p4 <= presion_exterior")
        # Sin tobera no se puede acreditar empuje positivo: ambas
        # condiciones deben estar relajadas para cumplir el filtro.
        base["cumple_restricciones"] = (not config["exigir_margen_tobera"]
                                         and not config["exigir_empuje_positivo"])
        return base
    base["regimen_tobera"] = r["tobera"]["regimen"]
    base["Fs"] = r["prestaciones"]["empuje_especifico_neto"]
    base["TSFC_kg_N_h"] = r["prestaciones"]["TSFC_kg_N_h"]
    if base["Fs"] is None:
        base.update(estado="tobera_no_resuelta", motivo="choque_interno_o_salida_no_resuelto")
        # Ni una relajación de filtros convierte un choque sin resolver en
        # empuje calculado o en un punto de optimización.
        return base
    if base["Fs"] <= 0:
        base.update(estado="empuje_no_positivo", motivo="Fs <= 0")
        base["cumple_restricciones"] = not config["exigir_empuje_positivo"]
    else:
        motivo = ("choque_normal_resuelto" if r["tobera"]["regimen"] in
                  ("choque_normal_interno", "choque_normal_salida")
                  else "empuje_neto_positivo")
        base.update(estado="valido", motivo=motivo)
        base["cumple_restricciones"] = True
    return base


def frente_pareto(puntos):
    """Puntos válidos no dominados: maximizar Fs, minimizar TSFC.

    Cada punto es un dict con estado='valido', Fs, TSFC_kg_N_h; se devuelve
    una lista de los propios puntos, en el orden original. O(n²), sin scipy.
    Úsese SOLO entre condiciones ambientales/hipótesis comparables.
    """
    candidatos = [p for p in puntos if p["estado"] == "valido"]
    if any(not (_finito(p["Fs"]) and _finito(p["TSFC_kg_N_h"]) and
                p["Fs"] > 0 and p["TSFC_kg_N_h"] > 0) for p in candidatos):
        raise ValueError("Punto válido con prestaciones indefinidas.")
    return [p for p in candidatos if not any(
        q is not p and q["Fs"] >= p["Fs"] and
        q["TSFC_kg_N_h"] <= p["TSFC_kg_N_h"] and
        (q["Fs"] > p["Fs"] or q["TSFC_kg_N_h"] < p["TSFC_kg_N_h"])
        for q in candidatos)]


def _resumen(puntos, nx, ny, comparar):
    """Contadores, extremos discretos y, si procede, Pareto."""
    cont = Counter(p["estado"] for p in puntos)
    motivos = dict(Counter(p["motivo"] for p in puntos if p["estado"] != "valido"))
    validos = [p for p in puntos if p["estado"] == "valido"]
    def extremo(clave, fn):
        if not validos:
            return None
        ganador = fn(validos, key=lambda p:p[clave])
        iy, ix = ganador["indices"]
        return {"punto": ganador, "valor": ganador[clave],
                "en_frontera_malla": ((nx > 1 and ix in (0, nx-1)) or
                                      (ny > 1 and iy in (0, ny-1)))}
    return {"total": len(puntos), "validos": len(validos),
            "descartados": len(puntos)-len(validos),
            "cumplen_restricciones": sum(p["cumple_restricciones"] for p in puntos),
            "por_estado": {e:cont[e] for e in ESTADOS}, "por_motivo": motivos,
            "maximo_Fs": extremo("Fs", max),
            "minimo_TSFC": extremo("TSFC_kg_N_h", min),
            "pareto": frente_pareto(validos) if comparar else None,
            "pareto_aplicable": comparar}


def _barrer(nombre, eje_x, eje_y, fijo, nombre_x, nombre_y, restricciones,
            comparar):
    config = _restricciones(restricciones)
    puntos = []
    for iy, y in enumerate(eje_y):
        for ix, x in enumerate(eje_x):
            parametros = dict(fijo)
            parametros[nombre_x] = x
            parametros[nombre_y] = y
            puntos.append(_punto(parametros, (iy, ix), config))
    resumen = _resumen(puntos, len(eje_x), len(eje_y), comparar)
    return {"nombre": nombre, "eje_x": nombre_x, "eje_y": nombre_y,
            "valores_x": eje_x, "valores_y": eje_y,
            "fijos": dict(fijo), "restricciones": config,
            "puntos": [puntos[i*len(eje_x):(i+1)*len(eje_x)]
                       for i in range(len(eje_y))],
            "estados": [[p["estado"] for p in puntos[i*len(eje_x):(i+1)*len(eje_x)]]
                        for i in range(len(eje_y))],
            "unidades": {"Fs":"N/(kg/s aire)","TSFC_kg_N_h":"kg/(N h)",
                        "f":"kg combustible/kg aire", "trabajo_compresor":"kJ/kg aire",
                        "T4":"K", "p4":"kPa"},
            "comparabilidad": ("mismo ambiente y Mach" if comparar else
                              "ambiente/Mach variables: no calcular Pareto conjunto"),
            **resumen}


def barrer_rp_t3(valores_rp, valores_T3, *, mach=0, pi_d=1,
                 T_amb=None, p_amb=None, altitud_geopotencial=None,
                 eta_c=.85, delta=.04, eta_t=.9, eta_m=.98, eta_n=.95,
                 eta_b=.99, PCI=43000, restricciones=None,
                 tipo_tobera="convergente", epsilon=1.5):
    """Malla fija de ambiente y Mach: x=rp, y=T3; permite Pareto global."""
    rp = _eje(valores_rp, "rp", 1.0, float("inf"))
    if rp[0] <= 1:
        raise ValueError("rp debe ser estrictamente mayor que 1.")
    t3 = _eje(valores_T3, "T3", 200, 2000)
    fijo = dict(mach=mach, pi_d=pi_d, eta_c=eta_c, delta=delta,
                eta_t=eta_t, eta_m=eta_m, eta_n=eta_n, eta_b=eta_b, PCI=PCI,
                tipo_tobera=tipo_tobera, epsilon=epsilon)
    if altitud_geopotencial is not None:
        if T_amb is not None or p_amb is not None:
            raise ValueError("Con altitud ISA, no suministres ambiente directo.")
        fijo["altitud_geopotencial"] = altitud_geopotencial
    else:
        fijo.update(T_amb=288.15 if T_amb is None else T_amb,
                    p_amb=100 if p_amb is None else p_amb)
    return _barrer("rp_T3", rp, t3, fijo, "rp", "T3", restricciones, True)


def barrer_mach_altitud(valores_mach, valores_altitud, *, rp=10, T3=1600,
                        pi_d=.98, eta_c=.85, delta=.04, eta_t=.9,
                        eta_m=.98, eta_n=.95, eta_b=.99, PCI=43000,
                        restricciones=None, tipo_tobera="convergente", epsilon=1.5):
    """Malla x=Mach, y=altitud ISA; extremos descriptivos, SIN Pareto global."""
    mach = _eje(valores_mach, "Mach", 0, 1, incluir_maximo=False)
    altura = _eje(valores_altitud, "altitud", 0, 20000)
    fijo = dict(rp=rp, T3=T3, pi_d=pi_d, eta_c=eta_c, delta=delta,
                eta_t=eta_t, eta_m=eta_m, eta_n=eta_n, eta_b=eta_b, PCI=PCI,
                tipo_tobera=tipo_tobera, epsilon=epsilon)
    return _barrer("Mach_altitud", mach, altura, fijo,
                   "mach", "altitud_geopotencial", restricciones, False)
