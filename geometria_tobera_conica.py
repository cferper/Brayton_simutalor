"""Geometría *hipotética* de un divergente cónico axisimétrico (M46.1).

Sólo convierte áreas equivalentes de M45 en radios y longitud. No cambia
velocidades, presiones, choques, rendimiento ni empuje termodinámico.
"""

from math import isfinite, pi, radians, sqrt, tan
from numbers import Real


def validar_semidivergencia(angulo_grados):
    """Devuelve ángulo finito [°] en (0,90), o lanza ValueError."""
    if isinstance(angulo_grados, bool) or not isinstance(angulo_grados, Real):
        raise ValueError("La semidivergencia debe ser un número real en grados.")
    angulo = float(angulo_grados)
    if not isfinite(angulo) or not 0 < angulo < 90:
        raise ValueError("La semidivergencia debe ser finita y estar entre 0° y 90°, sin incluirlos.")
    return angulo


def calcular_geometria_conica(dimensionamiento, angulo_grados):
    """Devuelve dict de radios [m], áreas [m²], ángulo [°] y Ld [m].

    Cuando faltan dimensiones o la tobera no es C-D, devuelve disponible=False.
    Con áreas incompatibles o ángulo inválido, lanza ValueError.
    """
    angulo = validar_semidivergencia(angulo_grados)
    base = {"disponible": False, "motivo": None, "angulo_grados": angulo,
            "radio_garganta": None, "radio_salida": None,
            "area_garganta": None, "area_salida": None,
            "diametro_garganta": None, "diametro_salida": None,
            "longitud_divergente": None, "relacion_areas": None,
            "residuo_area_garganta": None, "residuo_area_salida": None}
    if not dimensionamiento or not dimensionamiento.get("disponible"):
        base["motivo"] = "No existen áreas físicas disponibles del milestone 45."
        return base
    if dimensionamiento.get("tipo_tobera") != "convergente_divergente":
        base["motivo"] = "El divergente cónico sólo se define para una tobera C-D."
        return base
    ag = dimensionamiento["area_garganta"]
    ae = dimensionamiento["area_salida"]
    if any(isinstance(a, bool) or not isinstance(a, Real) or not isfinite(a)
           or a <= 0 for a in (ag, ae)):
        raise ValueError("Las áreas de garganta y salida deben ser positivas y finitas.")
    # Ae/Ag=1 es un caso límite aceptado por el solucionador: no existe
    # tramo divergente que dimensionar, pero tampoco es un fallo del motor.
    if ae == ag:
        base["motivo"] = "Ae/Ag = 1: la garganta y la salida coinciden; no existe tramo divergente."
        return base
    if ae < ag:
        raise ValueError("Una sección divergente requiere Ae >= Ag.")
    rg, re = sqrt(ag/pi), sqrt(ae/pi)
    longitud = (re-rg)/tan(radians(angulo))
    if not isfinite(longitud) or longitud <= 0:
        raise ValueError("La longitud geométrica no es representable.")
    base.update(disponible=True, radio_garganta=rg, radio_salida=re,
                area_garganta=ag, area_salida=ae,
                diametro_garganta=2*rg, diametro_salida=2*re,
                longitud_divergente=longitud, relacion_areas=ae/ag,
                residuo_area_garganta=pi*rg*rg-ag,
                residuo_area_salida=pi*re*re-ae)
    return base


def svg_geometria_conica(geometria):
    """SVG autocontenido de la sección longitudinal, a escala en x e y.

    Retorna None si no hay geometría; usa escala uniforme para no deformar
    el ángulo. Las anotaciones se sitúan fuera del perfil físico.
    """
    if not geometria or not geometria.get("disponible"):
        return None
    rg, re = geometria["radio_garganta"], geometria["radio_salida"]
    L = geometria["longitud_divergente"]
    a = geometria["angulo_grados"]
    # Una única escala px/m evita falsear las pendientes del cono.
    escala = min(580/L, 155/re)
    xg, xe, eje = 92., 92.+L*escala, 225.
    yg, ye = rg*escala, re*escala
    # En casos de cono muy esbelto, se conserva el perfil real y se
    # confía a las cotas textuales la legibilidad de dimensiones pequeñas.
    puntos = f"{xg:.3f},{eje-yg:.3f} {xe:.3f},{eje-ye:.3f} {xe:.3f},{eje+ye:.3f} {xg:.3f},{eje+yg:.3f}"
    marcas = f"<line x1='{xg:.3f}' y1='{eje-yg:.3f}' x2='{xg:.3f}' y2='{eje+yg:.3f}' stroke='#f97316' stroke-width='2'/>"
    marcas += f"<line x1='{xe:.3f}' y1='{eje-ye:.3f}' x2='{xe:.3f}' y2='{eje+ye:.3f}' stroke='#f97316' stroke-width='2'/>"
    # Arco angular en el vértice de garganta, construido con la pendiente
    # real. Se representa un segmento inicial como indicador del ángulo.
    arco = min(55., .38*L*escala)
    arco_y = arco*tan(radians(a))
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 790 490' "
        "role='img' aria-label='Divergente cónico axisimétrico a escala uniforme'>"
        "<rect width='790' height='490' rx='14' fill='#f8fafc'/>"
        f"<polygon points='{puntos}' fill='#dbeafe' stroke='#1d4ed8' stroke-width='2.3'/>"
        f"{marcas}"
        f"<line x1='55' y1='{eje}' x2='735' y2='{eje}' stroke='#64748b' stroke-dasharray='7 5'/>"
        f"<line x1='{xg:.3f}' y1='60' x2='{xg:.3f}' y2='385' stroke='#ea580c' stroke-dasharray='3 5'/>"
        f"<line x1='{xe:.3f}' y1='60' x2='{xe:.3f}' y2='385' stroke='#ea580c' stroke-dasharray='3 5'/>"
        f"<line x1='{xg:.3f}' y1='405' x2='{xe:.3f}' y2='405' stroke='#334155' stroke-width='1.6'/>"
        f"<line x1='{xg:.3f}' y1='398' x2='{xg:.3f}' y2='412' stroke='#334155'/>"
        f"<line x1='{xe:.3f}' y1='398' x2='{xe:.3f}' y2='412' stroke='#334155'/>"
        f"<line x1='{xg:.3f}' y1='{eje-yg:.3f}' x2='{xg+arco:.3f}' y2='{eje-yg-arco_y:.3f}' stroke='#16a34a' stroke-width='1.6'/>"
        f"<text x='{xg:.3f}' y='45' fill='#9a3412' font-size='16'>Garganta · Dg = {2*rg:.4f} m</text>"
        f"<text x='440' y='45' fill='#9a3412' font-size='16'>Salida · De = {2*re:.4f} m</text>"
        f"<text x='270' y='435' fill='#0f172a' font-size='17'>Longitud divergente Ld = {L:.5g} m</text>"
        f"<text x='270' y='461' fill='#166534' font-size='15'>Semidivergencia α = {a:.5g}°</text>"
        "<text x='595' y='245' fill='#475569' font-size='13'>Eje de simetría</text>"
        "<text x='20' y='482' fill='#475569' font-size='12'>Sólo divergente; sin convergente ni modelo de pérdidas.</text>"
        "</svg>"
    )
