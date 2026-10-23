"""Ciclo Brayton independiente con aire ideal de cp(T) (Fase 2B).

Temperaturas en K, presiones en kPa, h y energías en kJ/kg,
entropías en kJ/(kg K). Se reutilizan las propiedades de Fase 2A.
No se importa este solucionador desde el modelo anterior ni desde la web.
"""

from math import isfinite, log
from numbers import Real

from propiedades_aire import R_AIRE, T_MAX, T_MIN, T_desde_h, h, s, s0


class EstadoFueraDeRango(ValueError):
    """Un estado solicitado exigiría T fuera de los 200–2000 K del modelo."""


class ErrorNumericoCiclo(ArithmeticError):
    """El estado no es representable o la búsqueda de raíces no converge."""


def _numero_finito(valor):
    """Acepta reales finitos, pero no bool, cadenas ni enteros enormes."""
    if isinstance(valor, bool) or not isinstance(valor, Real):
        return False
    try:
        return isfinite(valor)
    except (OverflowError, TypeError, ValueError):
        return False


def _validar_entradas(T1, T3, rp, p1, eta_c, eta_t, delta, tolerancia):
    valores = (T1, T3, rp, p1, eta_c, eta_t, delta, tolerancia)
    if not all(_numero_finito(valor) for valor in valores):
        raise ValueError("Todas las entradas deben ser números reales finitos, sin booleanos.")
    if not (T_MIN <= T1 <= T_MAX and T_MIN <= T3 <= T_MAX):
        raise ValueError("T1 y T3 deben estar entre 200 y 2000 K.")
    if rp <= 0 or p1 <= 0:
        raise ValueError("rp y p1 deben ser estrictamente positivos.")
    if not (0 < eta_c <= 1 and 0 < eta_t <= 1 and 0 <= delta < 1):
        raise ValueError("Se requiere 0 < eta_c, eta_t <= 1 y 0 <= delta < 1.")
    if not 0 <= tolerancia < 1:
        raise ValueError("La tolerancia relativa debe estar en [0, 1).")


def _temperatura_desde_s0(objetivo):
    """Invierte la entropía térmica por bisección monótona, sin extrapolar."""
    minimo, maximo = s0(T_MIN), s0(T_MAX)
    if not minimo <= objetivo <= maximo:
        raise EstadoFueraDeRango(
            "La temperatura isentrópica requerida está fuera de 200–2000 K.")
    if objetivo == minimo:
        return T_MIN
    if objetivo == maximo:
        return T_MAX
    inferior, superior = T_MIN, T_MAX
    for _ in range(80):
        medio = (inferior + superior) / 2.0
        valor = s0(medio)
        if valor == objetivo:
            return medio
        if valor < objetivo:
            inferior = medio
        else:
            superior = medio
        if superior - inferior <= 1e-10:
            return (inferior + superior) / 2.0
    raise ErrorNumericoCiclo("La inversión de entropía no ha convergido.")


def _temperatura_desde_h_acotada(entalpia):
    """Distingue una entalpía físicamente fuera de rango del fallo numérico."""
    if not h(T_MIN) <= entalpia <= h(T_MAX):
        raise EstadoFueraDeRango(
            "La temperatura real requerida está fuera de 200–2000 K.")
    return T_desde_h(entalpia)


def resolver_ciclo(T1, T3, rp, p1, eta_c=1.0, eta_t=1.0, delta=0.0,
                  tolerancia=1e-10):
    """Resuelve cuatro estados con cp(T); no exige funcionamiento motor.

    T1,T3 [K], rp=p2/p1 [-], p1 [kPa], eficiencias [-], delta [-].
    Devuelve un dict con estados, energías, entropías, residuos y viabilidad.
    ValueError para entradas inválidas; EstadoFueraDeRango para estados que
    requerirían extrapolación; ErrorNumericoCiclo para valores no representables.
    """
    _validar_entradas(T1, T3, rp, p1, eta_c, eta_t, delta, tolerancia)
    T1, T3, rp, p1 = float(T1), float(T3), float(rp), float(p1)
    eta_c, eta_t, delta = float(eta_c), float(eta_t), float(delta)

    # Calcular las presiones sin imponer que exista compresión ni expansión.
    p2 = p1 * rp
    p3 = p2 * (1.0 - delta)
    if not all(isfinite(p) and p > 0 for p in (p2, p3)):
        raise ErrorNumericoCiclo("Las presiones intermedias no son representables.")
    p4 = p1
    R_kJ = R_AIRE / 1000.0

    # Compresor: s0(T2s)-s0(T1) = R ln(rp), y después salto real de h.
    T2s = _temperatura_desde_s0(s0(T1) + R_kJ * log(rp))
    h1, h2s = h(T1), h(T2s)
    h2_objetivo = h1 + (h2s - h1) / eta_c
    if not isfinite(h2_objetivo):
        raise ErrorNumericoCiclo("Entalpía del compresor no representable.")
    T2 = _temperatura_desde_h_acotada(h2_objetivo)

    # Turbina: se usa diferencia de logaritmos para presiones positivas.
    T4s = _temperatura_desde_s0(s0(T3) + R_kJ * (log(p4) - log(p3)))
    h3, h4s = h(T3), h(T4s)
    h4_objetivo = h3 - eta_t * (h3 - h4s)
    if not isfinite(h4_objetivo):
        raise ErrorNumericoCiclo("Entalpía de la turbina no representable.")
    T4 = _temperatura_desde_h_acotada(h4_objetivo)

    # h(T) vuelve a evaluarse en los estados recuperados, en lugar de
    # sustituirla por h_objetivo y ocultar cualquier residuo de inversión.
    h2, h4 = h(T2), h(T4)
    wc, wt = h2 - h1, h3 - h4
    qin, qout = h3 - h2, h4 - h1
    wnet = wt - wc
    primera_ley = wnet - (qin - qout)

    entropias = (s(T1, p1), s(T2, p2), s(T3, p3), s(T4, p4))
    sg_c = entropias[1] - entropias[0]
    sg_t = entropias[3] - entropias[2]
    residuo_2s = s0(T2s) - s0(T1) - R_kJ * log(rp)
    residuo_4s = s0(T4s) - s0(T3) - R_kJ * (log(p4) - log(p3))

    # Las fronteras no son motoras. Una máquina sometida a la relación de
    # presiones contraria puede ser calculable algebraicamente, pero estas
    # definiciones de eficiencia ya no garantizan producción de entropía >=0.
    escala_h = max(abs(wc), abs(wt), h(T_MAX) - h(T_MIN))
    tol_energia = tolerancia * escala_h
    tol_presion = tolerancia * max(p1, p2, p3)
    # El umbral de generación no debe escalar con el cero arbitrario de s:
    # éste cambia con la presión absoluta aunque sg_c y sg_t no cambien.
    tol_entropia = max(1e-11, tolerancia * max(1.0, abs(sg_c), abs(sg_t)))
    margenes = {
        "compresion": rp - 1.0,
        "expansion": p3 - p4,
        "calor_aportado": qin,
        "trabajo_neto": wnet,
        "segunda_ley_compresor": sg_c,
        "segunda_ley_turbina": sg_t,
    }
    tolerancias = {
        "compresion": tolerancia * max(rp, 1.0),
        "expansion": tol_presion,
        "calor_aportado": tol_energia,
        "trabajo_neto": tol_energia,
        "segunda_ley_compresor": -tol_entropia,
        "segunda_ley_turbina": -tol_entropia,
    }
    motivos = tuple(clave for clave, margen in margenes.items()
                    if (margen <= tolerancias[clave]
                        if not clave.startswith("segunda_ley")
                        else margen < tolerancias[clave]))
    viable = not motivos
    return {
        "temperaturas": (T1, T2, T3, T4),
        "presiones": (p1, p2, p3, p4),
        "T2s": T2s, "T4s": T4s,
        "entalpias": (h1, h2, h3, h4),
        "entalpias_isentropicas": (h2s, h4s),
        "entropias": entropias,
        "generacion_entropia_compresor": sg_c,
        "generacion_entropia_turbina": sg_t,
        "residuo_isentropico_compresor": residuo_2s,
        "residuo_isentropico_turbina": residuo_4s,
        "trabajo_compresor": wc,
        "trabajo_turbina": wt,
        "trabajo_neto": wnet,
        "calor_aportado": qin,
        "calor_rechazado": qout,
        "residuo_primera_ley": primera_ley,
        "viable": viable,
        "motivos": motivos,
        "margenes": margenes,
        "tolerancias": tolerancias,
        "rendimiento": wnet / qin if viable else None,
        "back_work_ratio": wc / wt if viable else None,
    }
