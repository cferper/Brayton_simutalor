"""Atmósfera, remanso, difusor y empuje neto de turborreactor subsónico.

Modelo idealizado sin combustible. Temperaturas K, presiones kPa,
velocidades y empuje específico N/(kg/s)=m/s, altitud geopotencial m.
"""

from math import exp, isfinite, log, sqrt
from numbers import Real

from propiedades_aire import T_MIN, T_MAX, R_AIRE, T_desde_h, gamma, h, s, s0
from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo
from acoplamiento_turbomaquinaria_cp import resolver_acoplamiento
from tobera_cp_variable import resolver_tobera_convergente


T_ISA0 = 288.15  # K
P_ISA0 = 101.325  # kPa
G_ISA = 9.80665  # m/s2, gravedad convencional estándar
R_ISA = 287.05287  # J/(kg K), aire seco estándar para hidrostática
L_ISA = -0.0065  # K/m, gradiente troposférico
H_TROPOPAUSA = 11000.0  # m geopotenciales


def _finito(valor):
    return isinstance(valor, Real) and not isinstance(valor, bool) and isfinite(valor)


def atmosfera_estandar(altitud_geopotencial):
    """ISA simplificada 0–20 km geopotenciales -> T [K], p [kPa], rho [kg/m3]."""
    if not _finito(altitud_geopotencial) or not 0 <= altitud_geopotencial <= 20000:
        raise ValueError("La altitud geopotencial debe estar entre 0 y 20000 m.")
    z = float(altitud_geopotencial)
    T11 = T_ISA0 + L_ISA * H_TROPOPAUSA
    p11 = P_ISA0 * (T11 / T_ISA0) ** (-G_ISA / (L_ISA * R_ISA))
    if z <= H_TROPOPAUSA:
        T = T_ISA0 + L_ISA * z
        p = P_ISA0 * (T / T_ISA0) ** (-G_ISA / (L_ISA * R_ISA))
        capa = "troposfera"
    else:
        T = T11
        p = p11 * exp(-G_ISA * (z - H_TROPOPAUSA) / (R_ISA * T11))
        capa = "isotermica"
    return {"altitud_geopotencial": z, "temperatura": T,
            "presion": p, "densidad": p*1000/(R_ISA*T), "capa": capa}


def calcular_remanso(T_estatica, p_estatica, mach):
    """Freestream subsónico -> Tt,pt por h y s de aire cp(T)."""
    if not all(_finito(v) for v in (T_estatica, p_estatica, mach)):
        raise ValueError("Entradas de remanso no finitas o no reales.")
    if not T_MIN <= T_estatica <= T_MAX or p_estatica <= 0 or not 0 <= mach < 1:
        raise ValueError("T en 200–2000 K, presión positiva y 0 <= Mach < 1.")
    T, p, M = float(T_estatica), float(p_estatica), float(mach)
    a = sqrt(gamma(T) * R_AIRE * T)
    velocidad = M * a
    entalpia_t = h(T) + velocidad**2 / 2000
    if not isfinite(entalpia_t):
        raise ErrorNumericoCiclo("Entalpía de remanso no representable.")
    if not h(T_MIN) <= entalpia_t <= h(T_MAX):
        raise EstadoFueraDeRango("Temperatura de remanso fuera de 200–2000 K.")
    Tt = T if M == 0 else T_desde_h(entalpia_t)
    # Igualdad entrópica con presiones relativas a la misma referencia.
    exponente = (s0(Tt) - s0(T)) / (R_AIRE / 1000)
    try:
        pt = p * exp(exponente)
    except OverflowError as exc:
        raise ErrorNumericoCiclo("Presión total no representable.") from exc
    if not isfinite(pt) or pt <= 0:
        raise ErrorNumericoCiclo("Presión total no representable.")
    return {"temperatura_estatica": T, "presion_estatica": p,
            "mach": M, "velocidad_sonido": a, "velocidad_vuelo": velocidad,
            "temperatura_remanso": Tt, "presion_remanso": pt,
            "residuo_energia": h(Tt)-h(T)-velocidad**2/2000,
            "residuo_entropia": s(Tt, pt)-s(T, p)}


def aplicar_difusor(remanso, pi_d):
    """Recuperación total de presión con Tt constante; pi_d adimensional."""
    if not _finito(pi_d) or not 0 < pi_d <= 1:
        raise ValueError("El factor de recuperación de presión debe estar en (0,1].")
    pt2 = remanso['presion_remanso'] * float(pi_d)
    if not isfinite(pt2) or pt2 <= 0:
        raise ErrorNumericoCiclo("Presión de difusor no representable.")
    return {"temperatura_remanso": remanso['temperatura_remanso'],
            "presion_remanso": pt2, "recuperacion_presion": float(pi_d),
            "presion_remanso_ideal": remanso['presion_remanso']}


def resolver_turborreactor_vuelo(mach, rp, eta_c, T3, delta, eta_t, eta_m,
                                eta_n=1.0, pi_d=1.0, *, T_amb=None,
                                p_amb=None, altitud_geopotencial=None):
    """Encadena atmósfera o T/p directas, difusor, núcleo y tobera.

    Devuelve dict con condiciones, núcleo, tobera (o None) y empuje neto.
    Si no hay expansión de tobera, el empuje específico queda indefinido.
    """
    if altitud_geopotencial is not None:
        if T_amb is not None or p_amb is not None:
            raise ValueError("Elige altitud ISA o T/p directas, no ambas.")
        ambiente = atmosfera_estandar(altitud_geopotencial)
        origen = "ISA"
    else:
        if not all(_finito(v) for v in (T_amb, p_amb)):
            raise ValueError("Se requieren T_amb y p_amb reales finitas.")
        if not T_MIN <= T_amb <= T_MAX or p_amb <= 0:
            raise ValueError("Ambiente fuera de rango.")
        ambiente = {"temperatura": float(T_amb), "presion": float(p_amb),
                    "densidad": float(p_amb)*1000/(R_AIRE*float(T_amb)),
                    "altitud_geopotencial": None, "capa": None}
        origen = "directo"

    remanso = calcular_remanso(ambiente['temperatura'], ambiente['presion'], mach)
    difusor = aplicar_difusor(remanso, pi_d)
    # El argumento p_amb del milestone 34 significa p1 del compresor.
    # En vuelo debe ser presión TOTAL tras difusor, no presión exterior.
    Tt2, pt2 = difusor['temperatura_remanso'], difusor['presion_remanso']
    nucleo_original = resolver_acoplamiento(Tt2, pt2, rp, eta_c, T3,
                                           delta, eta_t, eta_m)
    p4 = nucleo_original['presiones'][3]
    p_ext = ambiente['presion']
    razon = p4 / p_ext
    tol = 1e-10
    diagnostico = ("con_margen" if razon > 1+tol else
                   "sin_margen" if razon < 1-tol else "limite")
    # No exponer el diagnóstico del M34 relativo a pt2: sería una referencia
    # incorrecta para la tobera, que descarga frente a p_ext estática.
    nucleo = dict(nucleo_original)
    nucleo.update({"relacion_salida_ambiente": razon,
                   "margen_presion_kpa": p4-p_ext,
                   "diagnostico_tobera": diagnostico,
                   "presion_referencia_diagnostico": p_ext})
    if p4 <= p_ext:
        return {"origen_ambiente": origen, "ambiente": ambiente,
                "remanso": remanso, "difusor": difusor, "nucleo": nucleo,
                "tobera": None, "diagnostico": "sin_expansion_disponible",
                "empuje_especifico_momento": None,
                "resistencia_entrada": remanso['velocidad_vuelo'],
                "empuje_especifico_presion": None,
                "empuje_especifico_neto": None,
                "empuje_neto_positivo": None}
    salida = resolver_tobera_convergente(nucleo['temperaturas'][3], p4,
                                        p_ext, eta_n)
    f_momento = salida['empuje_especifico_momento']
    ram = remanso['velocidad_vuelo']
    f_presion = salida['empuje_especifico_presion']
    neto = f_momento - ram + f_presion
    return {"origen_ambiente": origen, "ambiente": ambiente,
            "remanso": remanso, "difusor": difusor, "nucleo": nucleo,
            "tobera": salida,
            "diagnostico": "empuje_positivo" if neto > 0 else "empuje_no_positivo",
            "empuje_especifico_momento": f_momento,
            "resistencia_entrada": ram,
            "empuje_especifico_presion": f_presion,
            "empuje_especifico_neto": neto,
            "empuje_neto_positivo": neto > 0}
