"""Acoplamiento monoeje compresor–turbina de un turborreactor estático.

Aire ideal de composición fija y cp(T); sin combustible, tobera ni empuje.
Temperaturas K, presiones kPa, trabajos y entalpías kJ/kg.
"""

from math import exp, isfinite, log
from numbers import Real

from propiedades_aire import R_AIRE, T_MAX, T_MIN, T_desde_h, h, s, s0
from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo, _temperatura_desde_s0


def _real(valor):
    return not isinstance(valor, bool) and isinstance(valor, Real) and isfinite(valor)


def _invertir_h(valor, descripcion):
    if not isfinite(valor):
        raise ErrorNumericoCiclo(f"Entalpía no representable: {descripcion}.")
    if not h(T_MIN) <= valor <= h(T_MAX):
        raise EstadoFueraDeRango(f"{descripcion}: temperatura fuera de {T_MIN:g}–{T_MAX:g} K.")
    return T_desde_h(valor)


def resolver_acoplamiento(T_amb, p_amb, rp, eta_c, T3, delta, eta_t, eta_m):
    """Resuelve un monoeje sin carga externa; devuelve estados y diagnóstico.

    T_amb,T3 [K], p_amb [kPa], rp [-], eficiencias [-], delta [-].
    Rechaza configuraciones sin compresión, calor positivo o expansión real.
    Un p4 <= p_amb es calculable pero no deja margen de presión para tobera.
    """
    entradas = (T_amb, p_amb, rp, eta_c, T3, delta, eta_t, eta_m)
    if not all(_real(x) for x in entradas):
        raise ValueError("Todas las entradas deben ser reales finitas y no booleanas.")
    if not T_MIN <= T_amb <= T_MAX or not T_MIN <= T3 <= T_MAX:
        raise ValueError("Las temperaturas deben estar entre 200 y 2000 K.")
    if p_amb <= 0 or rp <= 1:
        raise ValueError("Se requiere p_amb > 0 y rp > 1 para un compresor.")
    if not (0 < eta_c <= 1 and 0 < eta_t <= 1 and 0 < eta_m <= 1
            and 0 <= delta < 1):
        raise ValueError("Se requiere 0 < eta_c, eta_t, eta_m <= 1 y 0 <= delta < 1.")

    T1, p1 = float(T_amb), float(p_amb)
    p2, p3 = p1 * rp, p1 * rp * (1 - delta)
    if not all(isfinite(p) and p > 0 for p in (p2, p3)):
        raise ErrorNumericoCiclo("Presiones intermedias no representables.")
    R = R_AIRE / 1000  # kJ/(kg K), coherente con s0
    T2s = _temperatura_desde_s0(s0(T1) + R * log(rp))
    h1, h2s, h3 = h(T1), h(T2s), h(T3)
    T2 = _invertir_h(h1 + (h2s - h1) / eta_c, "Salida real del compresor")
    h2 = h(T2)
    wc = h2 - h1
    qin = h3 - h2
    if not wc > 0 or not qin > 0:
        raise ValueError("Se requiere compresión con trabajo y aporte térmico positivos.")

    wt_objetivo = wc / eta_m
    T4 = _invertir_h(h3 - wt_objetivo, "Salida real de la turbina")
    h4 = h(T4)
    wt = h3 - h4
    if wt <= 0:
        raise ValueError("La turbina debe producir trabajo positivo.")
    h4s_objetivo = h3 - wt / eta_t
    T4s = _invertir_h(h4s_objetivo, "Salida isentrópica de la turbina")
    h4s = h(T4s)
    # s0(T4s) - R ln(p4/P_REF) = s0(T3) - R ln(p3/P_REF).
    log_p4 = log(p3) + (s0(T4s) - s0(T3)) / R
    try:
        p4 = exp(log_p4)
    except OverflowError as exc:
        raise ErrorNumericoCiclo("Presión de turbina no representable.") from exc
    if not isfinite(p4) or p4 <= 0 or p4 >= p3:
        raise ErrorNumericoCiclo("La expansión requiere 0 < p4 < p3 representables.")

    cierre = eta_m * wt - wc
    razon = p4 / p1
    if not isfinite(razon):
        raise ErrorNumericoCiclo("Relación de presiones no representable.")
    # No se interpreta una diferencia microscópica como margen útil de tobera.
    umbral = 1e-10
    if razon > 1 + umbral:
        margen = "con_margen"
    elif razon < 1 - umbral:
        margen = "sin_margen"
    else:
        margen = "limite"

    return {
        "temperaturas": (T1, T2, float(T3), T4),
        "presiones": (p1, p2, p3, p4),
        "entalpias": (h1, h2, h3, h4),
        "entropias": (s(T1, p1), s(T2, p2), s(T3, p3), s(T4, p4)),
        "T2s": T2s, "T4s": T4s,
        "h2s": h2s, "h4s": h4s,
        "trabajo_compresor": wc, "trabajo_turbina": wt,
        "calor_aportado": qin, "rendimiento_mecanico": float(eta_m),
        "rendimiento_turbina": float(eta_t),
        "residuo_eje": cierre,
        "residuo_isentropico_turbina": s(T4s, p4) - s(T3, p3),
        "relacion_salida_ambiente": razon,
        "diagnostico_tobera": margen,
        "margen_presion_kpa": p4 - p1,
    }
