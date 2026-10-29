"""Diagnóstico de admisión condicionado: continuidad sin inventar aspiración.

La geometría exterior sola no determina el caudal en reposo; la sección de
entrada de compresor exige también Mach local o un caudal conocido.
"""

from math import exp, isfinite, sqrt
from numbers import Real

from propiedades_aire import R_AIRE, T_MIN, gamma, h, s0


def _positivo(x, nombre):
    if isinstance(x, bool) or not isinstance(x, Real) or not isfinite(x) or x <= 0:
        raise ValueError(f"{nombre} debe ser real, positivo y finito.")
    return float(x)


def estado_seccion_compresor(Tt2, pt2, mach_local):
    """Estado estático isentrópico de una sección a Mach prescrito, cp(T).

    Presión total recibida *después* de aplicar la recuperación del difusor.
    Flujo superficial rho V en kg/(m² s); sin área no hay caudal total.
    """
    Tt2 = _positivo(Tt2, "Temperatura total de entrada")
    pt2 = _positivo(pt2, "Presión total de entrada")
    if (isinstance(mach_local, bool) or not isinstance(mach_local, Real)
            or not isfinite(mach_local) or not 0 <= mach_local < 1):
        raise ValueError("El Mach local de entrada debe estar en [0,1).")
    if Tt2 < T_MIN:
        raise ValueError("Temperatura total fuera del dominio de propiedades.")
    M = float(mach_local)
    if M == 0:
        T = Tt2
    else:
        # h(Tt) = h(T) + M² gamma(T) R T/2000; bisección acotada.
        objetivo = h(Tt2)
        inferior, superior = T_MIN, Tt2
        def residuo(temperatura):
            return h(temperatura) + M*M*gamma(temperatura)*R_AIRE*temperatura/2000 - objetivo
        if residuo(inferior) > 0:
            raise ValueError("El estado de entrada queda fuera del dominio cp(T).")
        for _ in range(80):
            medio = (inferior+superior)/2
            if residuo(medio) > 0:
                superior = medio
            else:
                inferior = medio
        T = (inferior+superior)/2
    p = pt2*exp((s0(T)-s0(Tt2))/(R_AIRE/1000))
    a = sqrt(gamma(T)*R_AIRE*T)
    V = M*a
    rho = p*1000/(R_AIRE*T)
    return {"temperatura":T,"presion":p,"densidad":rho,
            "mach":M,"velocidad":V,"flujo_masico_superficial":rho*V,
            "residuo_energia":h(Tt2)-h(T)-V*V/2000}


def evaluar_admision(resultado, *, area_captacion=None,
                     area_entrada_compresor=None, mach_entrada_compresor=None,
                     gasto_masico_aire=None):
    """Separa área de captación en vuelo de sección local del compresor.

    ``area_captacion`` representa solo la corriente exterior interceptada.
    ``area_entrada_compresor`` es sección interna, tras el difusor.
    Con caudal conocido se dimensiona una sección; con área+Mach local se
    calcula un gasto local condicionado, sin resolver mapas de compresor.
    """
    if area_captacion is not None:
        area_captacion = _positivo(area_captacion, "Área de captación")
    if area_entrada_compresor is not None:
        area_entrada_compresor = _positivo(area_entrada_compresor, "Área de entrada del compresor")
    if gasto_masico_aire is not None:
        gasto_masico_aire = _positivo(gasto_masico_aire, "Gasto de aire")
    ambiente, remanso, difusor = (resultado[clave] for clave in ("ambiente","remanso","difusor"))
    rho_inf = ambiente["presion"]*1000/(R_AIRE*ambiente["temperatura"])
    velocidad_inf = remanso["velocidad_vuelo"]
    gc = rho_inf*velocidad_inf
    salida = {"estado": "condicionado", "captacion_en_vuelo": velocidad_inf > 0,
              "flujo_superficial_exterior": gc,
              "caudal_captacion_geometrica": None,
              "area_captacion_requerida": None,
              "caudal_entrada_compresor": None,
              "area_entrada_compresor_requerida": None,
              "estado_entrada_compresor": None,
              "residuo_continuidad": None,
              "diagnostico": None}
    if velocidad_inf > 0:
        if area_captacion is not None:
            salida["caudal_captacion_geometrica"] = gc*area_captacion
        if gasto_masico_aire is not None:
            salida["area_captacion_requerida"] = gasto_masico_aire/gc
    if mach_entrada_compresor is not None:
        estado = estado_seccion_compresor(difusor["temperatura_remanso"],
                                         difusor["presion_remanso"],
                                         mach_entrada_compresor)
        salida["estado_entrada_compresor"] = estado
        g2 = estado["flujo_masico_superficial"]
        if area_entrada_compresor is not None:
            salida["caudal_entrada_compresor"] = g2*area_entrada_compresor
        if gasto_masico_aire is not None and g2 > 0:
            salida["area_entrada_compresor_requerida"] = gasto_masico_aire/g2
        if gasto_masico_aire is not None and salida["caudal_entrada_compresor"] is not None:
            salida["residuo_continuidad"] = salida["caudal_entrada_compresor"]-gasto_masico_aire
    if velocidad_inf == 0 and mach_entrada_compresor is None:
        salida["estado"] = "aspiracion_no_determinada"
        salida["diagnostico"] = ("En estático, V∞=0 no determina aspiración. "
                                 "Se requiere caudal del motor o condición local de entrada al compresor.")
    elif salida["caudal_entrada_compresor"] is None and gasto_masico_aire is None:
        salida["estado"] = "caudal_no_determinado"
        salida["diagnostico"] = ("El área de captación por sí sola no cierra el caudal "
                                 "del motor: falta el comportamiento del compresor.")
    elif salida["residuo_continuidad"] is not None:
        if abs(salida["residuo_continuidad"]) > 2e-6*max(gasto_masico_aire,
                                      salida["caudal_entrada_compresor"]):
            salida["estado"] = "incompatible_con_caudal_impuesto"
            salida["diagnostico"] = "El Mach y área de entrada no transportan el caudal prescrito."
        else:
            salida["estado"] = "continuidad_compatible"
    return salida
