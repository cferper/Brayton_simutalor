"""Escalado extensivo y áreas de tobera desde un punto termodinámico resuelto.

No reevalúa compresor, combustor, turbina ni tobera. Sus valores son
condicionales al gasto másico de aire supuesto [kg/s], no una predicción
del mapa de funcionamiento de una turbomáquina real.
"""

from math import isfinite, pi, sqrt
from numbers import Real


def validar_gasto_masico_aire(gasto_masico_aire):
    """float positivo finito [kg/s] o ValueError (bool excluido)."""
    if (isinstance(gasto_masico_aire, bool)
            or not isinstance(gasto_masico_aire, Real)):
        raise ValueError("El gasto másico de aire debe ser real, positivo y finito [kg/s].")
    try:
        valor = float(gasto_masico_aire)
    except (OverflowError, ValueError, TypeError) as exc:
        raise ValueError("El gasto másico de aire debe ser finito [kg/s].") from exc
    if not isfinite(valor) or valor <= 0:
        raise ValueError("El gasto másico de aire debe ser mayor que cero y finito [kg/s].")
    return valor


def _finito(valor):
    return (isinstance(valor, Real) and not isinstance(valor, bool)
            and isfinite(valor))


def calcular_prestaciones_absolutas(resultado, gasto_masico_aire):
    """Escala caudales [kg/s], fuerzas [N] y consumo [kg/h] sin resolver motor.

    Cuando la salida no está resuelta, conserva caudales pero devuelve None
    para empujes y TSFC, evitando fabricar prestaciones a partir de cero.
    """
    ma = validar_gasto_masico_aire(gasto_masico_aire)
    f = resultado["combustor"]["f"]
    if not _finito(f) or f < 0:
        raise ValueError("El dosado combustible/aire del solucionador es inválido.")
    mf = f*ma
    me = (1+f)*ma
    mf_h = 3600*mf
    if not all(isfinite(v) for v in (mf, me, mf_h)):
        raise ValueError("El gasto másico produce valores absolutos no representables.")
    p = resultado["prestaciones"]
    claves = ("empuje_especifico_salida", "resistencia_entrada",
              "empuje_especifico_presion", "empuje_especifico_neto")
    datos = [p.get(k) for k in claves]
    base = {
        "gasto_masico_aire": ma, "gasto_masico_combustible": mf,
        "consumo_combustible_hora": mf_h, "gasto_masico_gases": me,
        "empuje_momento_salida": None, "resistencia_entrada": None,
        "empuje_presion": None, "empuje_neto": None, "empuje_neto_kN": None,
        "TSFC_kg_N_h": None, "residuo_empuje": None,
        "residuo_TSFC": None,
    }
    if any(x is None for x in datos):
        return base
    if not all(_finito(x) for x in datos):
        raise ValueError("Las prestaciones específicas del solucionador son inválidas.")
    salida, resistencia, presion, neto = datos
    termino_salida = salida*ma
    termino_entrada = -resistencia*ma
    termino_presion = presion*ma
    fuerza = neto*ma
    residuo = termino_salida+termino_entrada+termino_presion-fuerza
    if not all(isfinite(v) for v in (termino_salida, termino_entrada,
                                     termino_presion, fuerza, residuo)):
        raise ValueError("El empuje absoluto no es representable.")
    if abs(residuo) > 1e-8*max(1., abs(fuerza), abs(termino_salida),
                               abs(termino_entrada), abs(termino_presion)):
        raise ValueError("Las contribuciones absolutas no cierran el empuje neto.")
    tsfc = mf_h/fuerza if fuerza > 0 else None
    tsfc_referencia = p["TSFC_kg_N_h"]
    residuo_tsfc = (tsfc-tsfc_referencia if tsfc is not None
                    and tsfc_referencia is not None else None)
    if residuo_tsfc is not None and abs(residuo_tsfc) > 1e-8*max(1, abs(tsfc)):
        raise ValueError("El TSFC absoluto no coincide con el específico.")
    base.update(empuje_momento_salida=termino_salida,
                resistencia_entrada=termino_entrada,
                empuje_presion=termino_presion, empuje_neto=fuerza,
                empuje_neto_kN=fuerza/1000, TSFC_kg_N_h=tsfc,
                residuo_empuje=residuo, residuo_TSFC=residuo_tsfc)
    return base


def dimensionar_tobera(resultado, gasto_masico_aire, *, absolutos=None):
    """Áreas [m²] y diámetros circulares equivalentes [m] por continuidad.

    Para convergente, garganta=salida geométrica aunque no esté bloqueada.
    Para C-D se usa Gg real del solucionador, con o sin choque interno.
    """
    ma = validar_gasto_masico_aire(gasto_masico_aire)
    if absolutos is None:
        absolutos = calcular_prestaciones_absolutas(resultado, ma)
    n = resultado.get("tobera")
    tipo = resultado["diagnosticos"]["tipo_tobera"]
    base = {
        "disponible": False, "motivo": None, "tipo_tobera": tipo,
        "regimen": n.get("regimen") if n else None, "garganta_bloqueada": None,
        "area_garganta": None, "area_salida": None,
        "diametro_garganta": None, "diametro_salida": None,
        "relacion_areas": None, "residuo_masa_garganta": None,
        "residuo_masa_salida": None, "residuo_relacion_areas": None,
        "residuo_empuje_dimensional": None,
    }
    if not n or n.get("temperatura_salida") is None or n.get("velocidad_salida") is None:
        base["motivo"] = "No existe una salida física de tobera resuelta."
        return base
    if tipo == "convergente_divergente" and not n.get("resuelto"):
        base["motivo"] = "El solucionador C-D no ha resuelto la tobera."
        return base
    rho_e, ve = n["densidad_salida"], n["velocidad_salida"]
    if not all(_finito(v) and v > 0 for v in (rho_e, ve)):
        base["motivo"] = "La densidad o velocidad de salida no permite determinar un área."
        return base
    me = absolutos["gasto_masico_gases"]
    area_e = me/(rho_e*ve)
    if tipo == "convergente_divergente":
        gg = n["flujo_masico_por_area_garganta"]
        eps = n["relacion_areas"]
        mach_g = n.get("mach_garganta")
    else:
        gg = rho_e*ve
        eps = 1.0
        mach_g = n.get("mach_salida")
    if not _finito(gg) or gg <= 0 or not _finito(eps) or eps < 1:
        base["motivo"] = "El caudal superficial de garganta no es físico."
        return base
    area_g = me/gg
    relacion = area_e/area_g
    d_e, d_g = sqrt(4*area_e/pi), sqrt(4*area_g/pi)
    if not all(isfinite(v) and v > 0 for v in (area_e, area_g, d_e, d_g)):
        raise ValueError("Las dimensiones de tobera no son representables.")
    residuo_area = relacion-eps
    residuo_g = gg*area_g-me
    residuo_e = rho_e*ve*area_e-me
    if abs(residuo_area) > 2e-6*max(1, eps):
        raise ValueError("La relación de áreas no coincide con la geometría C-D resuelta.")
    if any(abs(v) > 2e-6*max(1, me) for v in (residuo_g, residuo_e)):
        raise ValueError("El dimensionamiento incumple la continuidad másica.")
    residuo_fuerza = None
    if absolutos["empuje_neto"] is not None:
        pe, p0 = n["presion_salida"], resultado["ambiente"]["presion"]
        v0 = resultado["remanso"]["velocidad_vuelo"]
        fuerza_dimensional = me*ve-ma*v0+1000*(pe-p0)*area_e
        residuo_fuerza = fuerza_dimensional-absolutos["empuje_neto"]
        if abs(residuo_fuerza) > 2e-6*max(1, abs(fuerza_dimensional)):
            raise ValueError("El empuje dimensional no coincide con el específico.")
    base.update(disponible=True, motivo=None, garganta_bloqueada=(
                    mach_g is not None and abs(mach_g-1) <= 1e-6),
                area_garganta=area_g, area_salida=area_e,
                diametro_garganta=d_g, diametro_salida=d_e,
                relacion_areas=relacion, residuo_masa_garganta=residuo_g,
                residuo_masa_salida=residuo_e,
                residuo_relacion_areas=residuo_area,
                residuo_empuje_dimensional=residuo_fuerza)
    return base
