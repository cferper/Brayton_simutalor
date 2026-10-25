"""Turborreactor subsónico con combustible y aire equivalente de cp(T).

Modelo energético, NO combustión química. T [K], p [kPa], h y trabajos
[kJ/kg], PCI [kJ/kg combustible], empuje específico [N/(kg/s aire)].
La entalpía sensible del combustible se toma nula en 298,15 K, referencia
de h(T) del aire. No representa productos de combustión reales.
"""

from math import exp, isfinite, log

from acoplamiento_turbomaquinaria_cp import _invertir_h
from ciclo_cp_variable import ErrorNumericoCiclo, _temperatura_desde_s0
from propiedades_aire import R_AIRE, T_MAX, T_MIN, h, s, s0
from tobera_cp_variable import resolver_tobera_convergente
from vuelo_cp_variable import _finito, aplicar_difusor, atmosfera_estandar, calcular_remanso


def _validar_entradas(rp, eta_c, T3, delta, eta_t, eta_m, eta_n,
                     eta_b, PCI):
    """Valida parámetros físicos y evita bool/NaN/inf (sin unidades)."""
    valores = (rp, eta_c, T3, delta, eta_t, eta_m, eta_n, eta_b, PCI)
    if not all(_finito(v) for v in valores):
        raise ValueError("Los parámetros del motor deben ser números reales finitos.")
    if not (rp > 1 and T_MIN <= T3 <= T_MAX and 0 <= delta < 1
            and all(0 < v <= 1 for v in (eta_c, eta_t, eta_m, eta_n, eta_b))
            and PCI > 0):
        raise ValueError("Parámetros del motor fuera de su dominio físico.")


def _compresor(T1, p1, rp, eta_c):
    """Compresor adiabático: devuelve dict de estados reales e isentrópicos."""
    p2 = p1 * rp
    if not isfinite(p2) or p2 <= 0:
        raise ErrorNumericoCiclo("Presión de compresor no representable.")
    R_kJ = R_AIRE / 1000
    T2s = _temperatura_desde_s0(s0(T1) + R_kJ * log(rp))
    h1, h2s = h(T1), h(T2s)
    T2 = _invertir_h(h1 + (h2s-h1)/eta_c, "Salida real del compresor")
    h2 = h(T2)
    wc = h2-h1
    if wc <= 0:
        raise ValueError("El compresor debe consumir trabajo positivo.")
    return {"T1": T1, "p1": p1, "h1": h1, "T2s": T2s, "h2s": h2s,
            "T2": T2, "p2": p2, "h2": h2,
            "trabajo_compresor": wc,
            "residuo_isentropico": s(T2s, p2)-s(T1, p1)}


def _combustor(h2, T3, p2, delta, eta_b, PCI):
    """Calcula f [kg combustible/kg aire] y balance con h(298,15 K)=0."""
    h3 = h(T3)
    salto = h3-h2
    denominador = eta_b*PCI-h3
    if salto <= 0:
        raise ValueError("T3 debe superar T2: aporte energético no positivo.")
    if not isfinite(denominador) or denominador <= 0:
        raise ValueError("PCI y eta_b no permiten alcanzar T3 en este modelo.")
    f = salto/denominador
    if not isfinite(f) or f <= 0 or not isfinite(1+f):
        raise ErrorNumericoCiclo("Relación combustible/aire no representable.")
    p3 = p2*(1-delta)
    if not isfinite(p3) or p3 <= 0:
        raise ErrorNumericoCiclo("Presión del combustor no representable.")
    return {"T3": float(T3), "p3": p3, "h3": h3,
            "h2": h2, "delta": float(delta), "eta_b": float(eta_b),
            "PCI": float(PCI), "f": f, "factor_masico": 1+f,
            "aporte_quimico_efectivo": f*eta_b*PCI,
            "residuo_energia": h2+f*eta_b*PCI-(1+f)*h3,
            "referencia_entalpia": "h_aire(298.15 K)=0; h_sensible_combustible=0"}


def _turbina(T3, p3, h3, wc, f, eta_m, eta_t):
    """Cierra eta_m*(1+f)*(h3-h4)=wc, devuelve presión por isentropía."""
    wt_objetivo = wc/(eta_m*(1+f))
    T4 = _invertir_h(h3-wt_objetivo, "Salida real de turbina con combustible")
    h4 = h(T4)
    wt = h3-h4
    if wt <= 0:
        raise ValueError("La turbina no desarrolla trabajo positivo.")
    T4s = _invertir_h(h3-wt/eta_t, "Salida isentrópica de turbina con combustible")
    R_kJ = R_AIRE/1000
    try:
        p4 = exp(log(p3)+(s0(T4s)-s0(T3))/R_kJ)
    except OverflowError as exc:
        raise ErrorNumericoCiclo("Presión de turbina no representable.") from exc
    if not isfinite(p4) or not 0 < p4 < p3:
        raise ErrorNumericoCiclo("Expansión de turbina inadmisible.")
    return {"T4": T4, "p4": p4, "h4": h4, "T4s": T4s,
            "h4s": h(T4s), "trabajo_turbina_por_kg_gas": wt,
            "trabajo_turbina_por_kg_aire": (1+f)*wt,
            "rendimiento_turbina": float(eta_t), "rendimiento_mecanico": float(eta_m),
            "residuo_eje": eta_m*(1+f)*wt-wc,
            "residuo_isentropico": s(T4s, p4)-s(T3, p3)}


def resolver_turborreactor_con_combustible(mach, rp, eta_c, T3, delta,
                                          eta_t, eta_m, eta_n=1.0, pi_d=1.0,
                                          eta_b=0.99, PCI=43000.0, *,
                                          T_amb=None, p_amb=None,
                                          altitud_geopotencial=None):
    """Resuelve turborreactor subsónico; ambiente directo o ISA 0–20 km.

    f [kg/kg aire], Fs [N/(kg/s aire)], TSFC [kg/(N s), kg/(N h)].
    Ausencia de expansión deja tobera, Fs y TSFC en None; Fs<=0 deja
    TSFC en None. Los componentes antiguos permanecen independientes.
    """
    _validar_entradas(rp, eta_c, T3, delta, eta_t, eta_m, eta_n, eta_b, PCI)
    if altitud_geopotencial is not None:
        if T_amb is not None or p_amb is not None:
            raise ValueError("Elige altitud ISA o temperatura/presión directas.")
        ambiente = atmosfera_estandar(altitud_geopotencial)
        origen = "ISA"
    else:
        if not all(_finito(v) for v in (T_amb, p_amb)):
            raise ValueError("T_amb y p_amb deben ser reales finitos.")
        if not T_MIN <= T_amb <= T_MAX or p_amb <= 0:
            raise ValueError("Ambiente fuera de dominio.")
        ambiente = {"temperatura": float(T_amb), "presion": float(p_amb),
                    "densidad": float(p_amb)*1000/(R_AIRE*float(T_amb)),
                    "altitud_geopotencial": None, "capa": None}
        origen = "directo"
    remanso = calcular_remanso(ambiente["temperatura"], ambiente["presion"], mach)
    difusor = aplicar_difusor(remanso, pi_d)
    compresor = _compresor(difusor["temperatura_remanso"],
                           difusor["presion_remanso"], rp, eta_c)
    combustor = _combustor(compresor["h2"], T3, compresor["p2"],
                           delta, eta_b, PCI)
    f = combustor["f"]
    turbina = _turbina(T3, combustor["p3"], combustor["h3"],
                       compresor["trabajo_compresor"], f, eta_m, eta_t)
    p_infinito = ambiente["presion"]
    margen = turbina["p4"]/p_infinito
    estado = "con_margen" if margen > 1+1e-10 else (
        "sin_margen" if margen < 1-1e-10 else "limite")
    diagnosticos = {"margen_tobera": estado, "relacion_p4_p_amb": margen,
                    "aproximacion": "aire equivalente, sin química de combustión"}
    if turbina["p4"] <= p_infinito:
        diagnosticos["funcionamiento"] = "sin_expansion_disponible"
        return {"origen_ambiente": origen, "ambiente": ambiente,
                "remanso": remanso, "difusor": difusor, "compresor": compresor,
                "combustor": combustor, "turbina": turbina, "tobera": None,
                "prestaciones": {"empuje_especifico_bruto": None,
                                 "empuje_especifico_salida": None,
                                 "resistencia_entrada": remanso["velocidad_vuelo"],
                                 "empuje_especifico_presion": None,
                                 "empuje_especifico_neto": None,
                                 "TSFC_kg_N_s": None, "TSFC_kg_N_h": None},
                "diagnosticos": diagnosticos}
    tobera = resolver_tobera_convergente(turbina["T4"], turbina["p4"],
                                        p_infinito, eta_n)
    salida = (1+f)*tobera["empuje_especifico_momento"]
    presion = (1+f)*tobera["empuje_especifico_presion"]
    resistencia = remanso["velocidad_vuelo"]
    bruto = salida+presion
    neto = bruto-resistencia
    if not isfinite(neto):
        raise ErrorNumericoCiclo("Empuje no representable.")
    diagnosticos["funcionamiento"] = (
        "empuje_positivo" if neto > 0 else "empuje_no_positivo")
    diagnosticos["regimen_tobera"] = tobera["regimen"]
    return {"origen_ambiente": origen, "ambiente": ambiente,
            "remanso": remanso, "difusor": difusor, "compresor": compresor,
            "combustor": combustor, "turbina": turbina, "tobera": tobera,
            "prestaciones": {"empuje_especifico_bruto": bruto,
                             "empuje_especifico_salida": salida,
                             "resistencia_entrada": resistencia,
                             "empuje_especifico_presion": presion,
                             "empuje_especifico_neto": neto,
                             "TSFC_kg_N_s": f/neto if neto > 0 else None,
                             "TSFC_kg_N_h": 3600*f/neto if neto > 0 else None},
            "diagnosticos": diagnosticos}
