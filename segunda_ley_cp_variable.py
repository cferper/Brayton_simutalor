"""Segunda ley y exergía física del Brayton con cp(T), sin resolver otro ciclo.

Las entropías y entalpías provienen de 2A/2B. Las únicas destrucciones
atribuidas son las de compresor y turbina adiabáticos (kJ/kg de aire).
"""

from math import isfinite
from numbers import Real

from propiedades_aire import T_MAX, T_MIN, h, s


def _ambiente_valido(T0, p0):
    """Valida la referencia ambiental: K, kPa; rechaza bool y no finitos."""
    if any(isinstance(v, bool) or not isinstance(v, Real) for v in (T0, p0)):
        raise ValueError("T0 y p0 deben ser números reales finitos.")
    try:
        if not all(isfinite(v) for v in (T0, p0)):
            raise ValueError("T0 y p0 deben ser números reales finitos.")
    except (OverflowError, TypeError):
        raise ValueError("T0 y p0 deben ser números reales finitos.") from None
    if not T_MIN <= T0 <= T_MAX:
        raise ValueError("T0 debe estar entre 200 y 2000 K.")
    if p0 <= 0:
        raise ValueError("p0 debe ser positiva en kPa.")


def analizar_segunda_ley_cp_variable(ciclo, T0=288.15, p0=100.0):
    """Exergía y entropía de cuatro estados existentes y dos turbomáquinas.

    ``ciclo`` es el dict devuelto por resolver_ciclo (2B), sin mutarlo;
    T0 [K] y p0 [kPa] definen un ambiente independiente del ciclo.
    Retorna un dict de entropías [kJ/(kg K)], exergías y balances [kJ/kg],
    eficiencias exergéticas en fracción o None, estado y diagnósticos.
    ValueError identifica ambiente/datos inválidos, nunca un no-motor.
    """
    _ambiente_valido(T0, p0)
    T0, p0 = float(T0), float(p0)
    try:
        entropias = tuple(ciclo['entropias'])
        entalpias = tuple(ciclo['entalpias'])
        presiones = tuple(ciclo['presiones'])
        temperaturas = tuple(ciclo['temperaturas'])
        wc, wt = ciclo['trabajo_compresor'], ciclo['trabajo_turbina']
        viable = ciclo['viable']
    except (KeyError, TypeError) as exc:
        raise ValueError("Faltan estados del solucionador cp(T).") from exc
    numeros = (*entropias, *entalpias, *presiones, *temperaturas, wc, wt)
    if (any(len(v) != 4 for v in (entropias, entalpias, presiones, temperaturas))
            or any(isinstance(v, bool) or not isinstance(v, Real) for v in numeros)
            or not all(isfinite(v) for v in numeros)
            or type(viable) is not bool):
        raise ValueError("Los cuatro estados del ciclo deben ser finitos y válidos.")

    h0, s_amb = h(T0), s(T0, p0)
    exergias = tuple((hi-h0)-T0*(si-s_amb)
                     for hi, si in zip(entalpias, entropias))
    sg_bruta = (entropias[1]-entropias[0], entropias[3]-entropias[2])
    # Una banda absoluta estricta en entropía; no depende del cero de s.
    tol_s = 1e-10  # kJ/(kg K), superior al redondeo de las inversiones de 2B
    generacion = tuple(0.0 if -tol_s <= x < 0 else x for x in sg_bruta)
    destruccion = tuple(T0*x for x in generacion)
    balance = (wc-(exergias[1]-exergias[0]),
               (exergias[2]-exergias[3])-wt)
    residuos = tuple(b-g for b,g in zip(balance, destruccion))
    tol_e = 1e-8*max(1.0, abs(wc), abs(wt), *(abs(e) for e in exergias))
    diagnosticos = []
    if any(x < -tol_s for x in sg_bruta):
        diagnosticos.append("Generación de entropía negativa significativa: "
                            "configuración o interpretación no compatible con turbomáquina adiabática pasiva.")
    if any(abs(r) > tol_e for r in residuos):
        diagnosticos.append("El balance de exergía no coincide con Gouy–Stodola dentro de la tolerancia.")
    if not viable:
        diagnosticos.append("Ciclo calculable pero no motor: no se publican rendimientos exergéticos operativos.")

    eta_c = eta_t = None
    if viable and not diagnosticos:
        incremento_e = exergias[1]-exergias[0]
        descenso_e = exergias[2]-exergias[3]
        if wc > tol_e and incremento_e > tol_e:
            eta_c = incremento_e/wc
        else:
            diagnosticos.append("Rendimiento del compresor no definido: trabajo o aumento de exergía no positivo.")
        if wt > tol_e and descenso_e > tol_e:
            eta_t = wt/descenso_e
        else:
            diagnosticos.append("Rendimiento de la turbina no definido: trabajo o caída de exergía no positivo.")
        if any(eta is not None and not (0 <= eta <= 1+1e-8)
               for eta in (eta_c, eta_t)):
            diagnosticos.append("Rendimiento exergético incompatible con las hipótesis adiabáticas.")
            eta_c = eta_t = None

    total = sum(destruccion)
    porcentajes = (tuple(100*d/total for d in destruccion)
                   if total > tol_e and all(d >= 0 for d in destruccion)
                   else (None, None))
    return {
        'T0': T0, 'p0': p0, 'h0': h0, 's0': s_amb,
        'entropias': entropias, 'exergias': exergias,
        'generacion_bruta': sg_bruta, 'generacion': generacion,
        'destruccion': destruccion, 'suma_turbomaquinas': total,
        'aportaciones_porcentaje': porcentajes,
        'balances_exergia': balance, 'residuos_balances': residuos,
        'tolerancia_entropia': tol_s, 'tolerancia_energia': tol_e,
        'eta_ex_compresor': eta_c, 'eta_ex_turbina': eta_t,
        'estado': ('inconsistente' if any(x < -tol_s for x in sg_bruta)
                   or any(abs(r) > tol_e for r in residuos)
                   else 'motor' if viable else 'no_motor'),
        'diagnosticos': tuple(diagnosticos),
    }
