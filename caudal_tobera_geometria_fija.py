"""Caudal de una tobera con áreas prescritas, reutilizando estados cp(T).

No acopla mapas de turbomáquinas: las condiciones de remanso se prescriben.
"""

from math import isfinite
from numbers import Real

from tobera_cp_variable import resolver_tobera_convergente
from tobera_convergente_divergente_cp import resolver_tobera_convergente_divergente


def validar_area(area, nombre):
    if isinstance(area, bool) or not isinstance(area, Real) or not isfinite(area) or area <= 0:
        raise ValueError(f"{nombre} debe ser un área positiva y finita [m²].")
    return float(area)


def resolver_caudal_tobera_fija(Tt, pt, p_amb, area_garganta, *,
                                area_salida=None, tipo_tobera="convergente",
                                eta_n=1.0):
    """Resuelve el flujo a remanso dado; caudales en kg/s y áreas en m².

    La convergente considera garganta y salida la misma sección. En C-D el
    cálculo de regímenes y choques pertenece al solucionador ya existente.
    """
    ag = validar_area(area_garganta, "Área de garganta")
    if tipo_tobera == "convergente":
        if area_salida is not None:
            ae = validar_area(area_salida, "Área de salida")
            if abs(ae-ag) > 2e-8*max(ae, ag):
                raise ValueError("En una tobera convergente la garganta coincide con la salida.")
        ae = ag
        n = resolver_tobera_convergente(Tt, pt, p_amb, eta_n)
    elif tipo_tobera == "convergente_divergente":
        if area_salida is None:
            raise ValueError("La tobera C-D necesita un área de salida.")
        ae = validar_area(area_salida, "Área de salida")
        if ae < ag:
            raise ValueError("En una tobera C-D se requiere Ae/Ag ≥ 1.")
        n = resolver_tobera_convergente_divergente(Tt, pt, p_amb, ae/ag)
    else:
        raise ValueError("Tipo de tobera desconocido.")
    return caudal_desde_estado_tobera(n, tipo_tobera, ag, ae)


def caudal_desde_estado_tobera(n, tipo_tobera, area_garganta, area_salida,
                              *, dosado=None):
    """Escala flujos superficiales ya resueltos y verifica continuidad.

    ``dosado`` es kg combustible/kg aire; solo si se conoce se deduce aire.
    """
    ag = validar_area(area_garganta, "Área de garganta")
    ae = validar_area(area_salida, "Área de salida")
    if tipo_tobera == "convergente" and abs(ae-ag) > 2e-8*max(ae, ag):
        raise ValueError("La convergente exige Ae = Ag.")
    if tipo_tobera == "convergente_divergente" and ae < ag:
        raise ValueError("Una tobera C-D exige Ae ≥ Ag.")
    base = {"disponible": False, "motivo": None, "tipo_tobera": tipo_tobera,
            "area_garganta": ag, "area_salida": ae, "relacion_areas": ae/ag,
            "gasto_masico_gases": None, "gasto_masico_aire": None,
            "gasto_masico_combustible": None, "residuo_continuidad": None,
            "regimen": n.get("regimen") if n else None,
            "garganta_bloqueada": None,
            "mach_salida": n.get("mach_salida") if n else None,
            "presion_salida": n.get("presion_salida") if n else None,
            "temperatura_salida": n.get("temperatura_salida") if n else None,
            "velocidad_salida": n.get("velocidad_salida") if n else None,
            "choque_normal": n.get("choque_normal") if n else None}
    if not n or n.get("temperatura_salida") is None or (
        tipo_tobera == "convergente_divergente" and not n.get("resuelto")
    ):
        base["motivo"] = (n.get("diagnostico") if n else None) or "La tobera no tiene solución de salida resuelta."
        return base
    if tipo_tobera == "convergente_divergente":
        epsilon = n["relacion_areas"]
        if abs(epsilon-ae/ag) > 2e-8*max(1, epsilon):
            raise ValueError("Las áreas fijas no corresponden a la solución C-D.")
        gg = n["flujo_masico_por_area_garganta"]
        mach_g = n["mach_garganta"]
    else:
        gg = n["densidad_salida"]*n["velocidad_salida"]
        mach_g = n["mach_salida"]
    ge = n["densidad_salida"]*n["velocidad_salida"]
    mg, me = gg*ag, ge*ae
    if not all(isfinite(v) and v > 0 for v in (gg, ge, mg, me)):
        base["motivo"] = "No existe flujo superficial positivo y finito."
        return base
    residuo = mg-me
    if abs(residuo) > 2e-6*max(mg, me):
        raise ValueError("La solución incumple conservación de masa en la geometría fija.")
    ma, mf = None, None
    if dosado is not None:
        if isinstance(dosado, bool) or not isinstance(dosado, Real) or not isfinite(dosado) or dosado < 0:
            raise ValueError("El dosado combustible/aire debe ser no negativo y finito.")
        ma = mg/(1+dosado)
        mf = mg-ma
    base.update(disponible=True, motivo=None, gasto_masico_gases=mg,
                gasto_masico_aire=ma, gasto_masico_combustible=mf,
                residuo_continuidad=residuo,
                garganta_bloqueada=mach_g is not None and abs(mach_g-1) <= 1e-6)
    return base
