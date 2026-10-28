"""Perfiles C-D cuasi-1D con cp(T), sin presuponer longitud axial.

El eje A/Ag usa siempre la garganta física. Conserva el caudal G*Ag,
pero después de un choque utiliza la presión total posterior y su A*.
Las ramas son estados calculados, no interpolaciones entre extremos.
"""

from math import isfinite
from numbers import Integral

from ciclo_cp_variable import ErrorNumericoCiclo
from propiedades_aire import h, s
from tobera_convergente_divergente_cp import (
    _biseccion, _estado, _salida_area, _sonico,
)


def _malla(inicio, fin, puntos):
    """Relaciones A/Ag calculadas; ambos extremos incluidos."""
    return tuple(inicio + (fin-inicio)*i/(puntos-1) for i in range(puntos))


def _punto(area, estado, Tt, pt, g_star, rama, papel="intermedio"):
    """Estado termodinámico estático, residuos y área crítica de su región."""
    T, p, V, G = (estado[k] for k in ("T", "p", "V", "G"))
    return {
        "area_relativa": area, "temperatura": T, "presion": p,
        "densidad": estado["rho"], "velocidad": V, "mach": estado["M"],
        "entalpia": h(T), "entropia": s(T, p),
        "flujo_masico_por_area": G, "flujo_masico_por_garganta": area*G,
        "residuo_energia": h(T)+V*V/2000-h(Tt),
        "residuo_entropia": s(T, p)-s(Tt, pt),
        "area_sobre_critica": g_star/G if g_star is not None else None,
        "presion_remanso_region": pt, "rama": rama, "papel": papel,
    }


def _desde_choque(area, choque, lado, Tt, g_star):
    """Reutiliza exactamente el estado calculado de Rankine–Hugoniot."""
    i = 1 if lado == "antes" else 2
    T, p, V, rho, M = (choque[f"{campo}{i}"]
                         for campo in ("T", "p", "V", "rho", "M"))
    pt = choque["pt1"] if i == 1 else choque["pt2"]
    estado = {"T": T, "p": p, "V": V, "rho": rho, "M": M, "G": rho*V}
    return _punto(area, estado, Tt, pt, g_star,
                  "supersonica" if i == 1 else "subsonica",
                  "choque_antes" if i == 1 else "choque_despues")


def _subsonico(Tt, pt, temperatura_sonica, flujo_objetivo):
    """Raíz G(T)=objetivo en la rama sub, con remanso de esta región."""
    return _estado(_biseccion(
        lambda T: _estado(T, Tt, pt)["G"]-flujo_objetivo,
        temperatura_sonica, Tt), Tt, pt)


def _validar_perfil(segmentos, flujo_garganta, *, salto=None):
    """Descarta resultados inconsistentes, sin ajustarlos visualmente."""
    for segmento in segmentos:
        for estado in segmento:
            escala = max(1.0, abs(flujo_garganta))
            if (not all(isfinite(estado[k]) for k in
                        ("area_relativa", "temperatura", "presion", "mach",
                         "densidad", "velocidad", "entalpia", "entropia"))
                    or abs(estado["flujo_masico_por_garganta"]-flujo_garganta)
                    > 2e-6*escala
                    or abs(estado["residuo_energia"]) > 1e-7
                    or abs(estado["residuo_entropia"]) > 1e-8):
                raise ErrorNumericoCiclo("El perfil incumple masa, energía o entropía regional.")
    if salto:
        antes, despues = salto
        if (abs(antes["area_relativa"]-despues["area_relativa"]) > 1e-12
                or not antes["mach"] > 1 > despues["mach"]
                or not despues["presion"] > antes["presion"]
                or not despues["entropia"] > antes["entropia"]
                or not despues["presion_remanso_region"]
                           < antes["presion_remanso_region"]):
            raise ErrorNumericoCiclo("El perfil incumple el salto de choque normal.")


def perfil_tobera_cp_variable(resultado, *, puntos_por_region=41):
    """Dict de curvas C-D calculadas, o dict con disponible=False y motivo.

    Entrada: el resultado completo de `resolver_turborreactor_con_combustible`.
    La discretización es por A/Ag, sin coordenada longitudinal; ninguna
    interpolación de Mach/presión ni gas de gamma constante.
    """
    if (isinstance(puntos_por_region, bool)
            or not isinstance(puntos_por_region, Integral)
            or not 3 <= puntos_por_region <= 121):
        raise ValueError("puntos_por_region debe ser entero entre 3 y 121.")
    n = resultado.get("tobera")
    tipo = resultado.get("diagnosticos", {}).get("tipo_tobera")
    def ausente(motivo):
        return {"disponible": False, "motivo": motivo, "segmentos": (),
                "choque": None, "regimen": n.get("regimen") if n else None}
    if tipo != "convergente_divergente":
        return ausente("Tobera convergente: no se conoce una distribución de áreas; se conservan las estaciones discretas.")
    if not n or not n.get("resuelto") or n.get("mach_salida") is None:
        return ausente("La tobera C-D no tiene una solución física completa; consulta su diagnóstico.")
    epsilon = n["relacion_areas"]
    if epsilon <= 1:
        return ausente("Ae/Ag = 1: no existe tramo divergente para calcular un perfil por área.")
    Tt, pt = n["temperatura_remanso"], n["presion_remanso"]
    critico = _sonico(Tt, pt)
    if critico is None:
        return ausente("No se alcanza el estado sónico dentro del dominio de propiedades: A* no disponible.")
    Gg = n["flujo_masico_por_area_garganta"]
    if Gg is None or Gg <= 0:
        return ausente("No se dispone de caudal válido en la garganta.")
    regimen = n["regimen"]
    choque = n.get("choque_normal")
    segmentos = []
    salto = None
    g_star2 = None
    if choque:
        area_choque = n["relacion_areas_choque"]
        if area_choque is None or not 1 < area_choque <= epsilon*(1+1e-9):
            return ausente("La posición de choque excede la geometría física calculada.")
        area_choque = min(area_choque, epsilon)
        anterior = [_punto(a, _salida_area(Tt, pt, critico, a, supersonica=True),
                           Tt, pt, critico["G"], "supersonica",
                           "garganta" if i == 0 else "intermedio")
                    for i, a in enumerate(_malla(1.0, area_choque, puntos_por_region))]
        antes = _desde_choque(area_choque, choque, "antes", Tt, critico["G"])
        anterior[-1] = antes
        g_star2 = _sonico(Tt, choque["pt2"])
        if g_star2 is None:
            return ausente("No existe estado crítico posterior al choque en el dominio.")
        despues = _desde_choque(area_choque, choque, "despues", Tt, g_star2["G"])
        posterior = [despues]
        if area_choque < epsilon-1e-10:
            for a in _malla(area_choque, epsilon, puntos_por_region)[1:]:
                posterior.append(_punto(
                    a, _subsonico(Tt, choque["pt2"], critico["T"], Gg/a),
                    Tt, choque["pt2"], g_star2["G"], "subsonica",
                    "salida" if abs(a-epsilon) < 1e-12 else "intermedio"))
        else:
            posterior[-1] = {**posterior[-1], "papel": "choque_despues_salida"}
        segmentos = [tuple(anterior), tuple(posterior)]
        salto = (antes, despues)
    else:
        # La frontera bloqueada puede tener salida *subsónica* sin choque.
        # Es una solución límite diferente de la rama supersónica normal.
        bloqueado = regimen not in ("subsonico_no_bloqueado",
                                   "bloqueado_salida_subsonica_limite")
        temperaturas_garganta = n["temperatura_garganta"]
        rama = "supersonica" if bloqueado else "subsonica"
        serie = []
        for i, a in enumerate(_malla(1.0, epsilon, puntos_por_region)):
            if i == 0:
                estado = _estado(temperaturas_garganta, Tt, pt)
            elif bloqueado:
                estado = _salida_area(Tt, pt, critico, a, supersonica=True)
            else:
                estado = _subsonico(Tt, pt, critico["T"], Gg/a)
            serie.append(_punto(a, estado, Tt, pt, critico["G"], rama,
                                 "garganta" if i == 0 else
                                 "salida" if i == puntos_por_region-1 else "intermedio"))
        segmentos = [tuple(serie)]
    _validar_perfil(segmentos, Gg, salto=salto)
    salida = segmentos[-1][-1]
    if (abs(salida["mach"]-n["mach_salida"]) > 1e-5
            or abs(salida["presion"]-n["presion_salida"]) >
            1e-5*max(1.0, abs(n["presion_salida"]))):
        raise ErrorNumericoCiclo("La salida del perfil no coincide con el solucionador C-D.")
    return {
        "disponible": True, "motivo": None, "regimen": regimen,
        "tipo": tipo, "segmentos": tuple(segmentos), "choque": salto,
        "p_ambiente": n["presion_ambiente"], "relacion_areas": epsilon,
        "flujo_masico_por_garganta": Gg,
        "area_critica": {"antes": critico["G"]/Gg,
                         "despues": g_star2["G"]/Gg if g_star2 else None},
    }
