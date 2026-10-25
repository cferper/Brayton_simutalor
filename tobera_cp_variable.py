"""Tobera convergente de aire ideal con cp(T), sin vuelo ni combustible.

El estado (Tt, pt) es de remanso; p_e y T_e son estáticos.
Presiones en kPa; entalpías en kJ/kg; velocidad y empuje específico en m/s.
"""

from math import isfinite, sqrt, log, exp
from numbers import Real

from acoplamiento_turbomaquinaria_cp import resolver_acoplamiento
from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo, _temperatura_desde_s0
from propiedades_aire import T_MIN, T_MAX, R_AIRE, h, s, s0, gamma, T_desde_h


def _validar_real(x):
    return isinstance(x, Real) and not isinstance(x, bool) and isfinite(x)


def _estado_desde_isentropica(Tt, ht, Tes, eta_n):
    """T_s [K] -> (T_e [K], V_e [m/s], Mach), sin resolver presiones."""
    salto_ideal = ht - h(Tes)
    if salto_ideal < 0:
        raise ErrorNumericoCiclo("Expansión isentrópica con salto de entalpía negativo.")
    he_obj = ht - eta_n * salto_ideal
    if eta_n == 1:
        # Identidad exacta en el límite reversible: evita ruido de redondeo
        # en la frontera T_MIN sin alterar la entalpía representada.
        Te = Tes
    else:
        if not h(T_MIN) <= he_obj <= h(T_MAX):
            raise EstadoFueraDeRango("Temperatura estática fuera del dominio 200–2000 K.")
        Te = T_desde_h(he_obj)
    velocidad = sqrt(max(0., 2000 * (ht - h(Te))))
    sonido = sqrt(gamma(Te) * R_AIRE * Te)
    return Te, velocidad, velocidad / sonido


def _estado_critico(Tt, ht, eta_n):
    """Encuentra M=1 con cp(T); devuelve T_es crítica o None si no está en dominio."""
    _, _, mach_min = _estado_desde_isentropica(Tt, ht, T_MIN, eta_n)
    if mach_min < 1:
        return None
    inferior, superior = T_MIN, Tt
    for _ in range(85):
        medio = (inferior + superior) / 2
        _, _, mach = _estado_desde_isentropica(Tt, ht, medio, eta_n)
        if mach > 1:
            inferior = medio
        else:
            superior = medio
        if superior - inferior < 1e-10:
            return (inferior + superior) / 2
    raise ErrorNumericoCiclo("No converge la condición sónica.")


def resolver_tobera_convergente(Tt, pt, p_amb, eta_n=1.0):
    """Expansión hasta ambiente o salida sónica, con presión de empuje.

    Tt [K], pt y p_amb [kPa], 0<eta_n<=1. Retorna dict de estado
    estático de salida, presión crítica, Mach, área/caudal y empuje específico.
    No calcula empuje absoluto porque no conoce el caudal másico.
    """
    if not all(_validar_real(x) for x in (Tt, pt, p_amb, eta_n)):
        raise ValueError("Tt, pt, p_amb y eta_n deben ser reales finitos.")
    if not T_MIN <= Tt <= T_MAX or not (pt > p_amb > 0) or not 0 < eta_n <= 1:
        raise ValueError("Se exige Tt en 200–2000 K, pt>p_amb>0 y 0<eta_n<=1.")
    Tt, pt, p_amb, eta_n = map(float, (Tt, pt, p_amb, eta_n))
    ht = h(Tt)
    Tes_crit = _estado_critico(Tt, ht, eta_n)
    R_kJ = R_AIRE / 1000
    pcrit = (pt * exp((s0(Tes_crit) - s0(Tt)) / R_kJ)
             if Tes_crit is not None else None)
    if pcrit is not None and p_amb <= pcrit:
        presion_salida, Tes = pcrit, Tes_crit
        regimen = "bloqueado"
    else:
        # Inversión explícita: no extrapolar fuera de correlaciones de aire.
        Tes = _temperatura_desde_s0(s0(Tt) + R_kJ*(log(p_amb)-log(pt)))
        presion_salida = p_amb
        regimen = "no_bloqueado"
    Te, Ve, Mach = _estado_desde_isentropica(Tt, ht, Tes, eta_n)
    if Ve <= 1e-7:
        raise ValueError("Expansión insuficiente: velocidad prácticamente nula.")
    if regimen == "bloqueado" and abs(Mach - 1) > 1e-7:
        raise ErrorNumericoCiclo("No cierra la condición M=1.")
    if regimen == "no_bloqueado" and Mach > 1 + 1e-7:
        raise ErrorNumericoCiclo("Salida supersónica imposible en tobera convergente.")
    rho = presion_salida * 1000 / (R_AIRE * Te)  # kg/m³
    area_especifica = 1 / (rho * Ve)  # m² / (kg/s)
    f_presion = (presion_salida - p_amb) * 1000 * area_especifica
    return {
        "regimen": regimen,
        "temperatura_remanso": Tt, "presion_remanso": pt,
        "temperatura_isentropica_salida": Tes,
        "temperatura_salida": Te, "presion_salida": presion_salida,
        "presion_ambiente": p_amb, "presion_critica": pcrit,
        "temperatura_isentropica_critica": Tes_crit,
        "entalpia_remanso": ht, "entalpia_salida": h(Te),
        "velocidad_salida": Ve, "velocidad_sonido": sqrt(gamma(Te)*R_AIRE*Te),
        "mach_salida": Mach, "densidad_salida": rho,
        "area_por_caudal": area_especifica,
        "empuje_especifico_momento": Ve,
        "empuje_especifico_presion": f_presion,
        "empuje_especifico_total": Ve + f_presion,
        "rendimiento_tobera": eta_n,
        "residuo_energia": ht-h(Te)-Ve**2/2000,
        "residuo_isentropico": s(Tes, presion_salida)-s(Tt, pt),
    }


def resolver_nucleo_con_tobera(T_amb, p_amb, rp, eta_c, T3, delta,
                              eta_t, eta_m, eta_n=1.0):
    """Encadena el milestone 34 y la tobera; devuelve {'nucleo','tobera'}.

    El estado 4 del núcleo se toma como remanso de la tobera: hipótesis de
    velocidad axial despreciable en los planos de estados de la turbina.
    """
    nucleo = resolver_acoplamiento(T_amb, p_amb, rp, eta_c, T3,
                                  delta, eta_t, eta_m)
    salida = resolver_tobera_convergente(nucleo['temperaturas'][3],
                                        nucleo['presiones'][3], p_amb, eta_n)
    return {"nucleo": nucleo, "tobera": salida}
