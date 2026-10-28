"""Proyección de los estados calculados M44.4 sobre una geometría M46.1.

No interpola ni resuelve de nuevo Mach, presión o choques normales.
"""

from math import isfinite, pi, radians, sqrt, tan

TOLERANCIA_RELATIVA_AREAS = 2e-6


def posicion_axial_por_area(area_relativa, geometria):
    """x [m] desde garganta para un A/Ag >= 1 en un divergente cónico.

    El dominio incluye los extremos 1 y Ae/Ag. Entrada fuera de rango:
    ValueError; la longitud se toma de la misma geometría M46.1.
    """
    if not geometria or not geometria.get("disponible"):
        raise ValueError("No existe geometría cónica válida para situar áreas.")
    if (isinstance(area_relativa, bool) or not isinstance(area_relativa, (int, float))
            or not isfinite(area_relativa)):
        raise ValueError("La relación de áreas debe ser real y finita.")
    eps = geometria["relacion_areas"]
    tolerancia = TOLERANCIA_RELATIVA_AREAS*max(1., eps)
    if not 1-tolerancia <= area_relativa <= eps+tolerancia:
        raise ValueError("La relación de áreas queda fuera del divergente.")
    if area_relativa <= 1:
        return 0.0
    if area_relativa >= eps:
        return geometria["longitud_divergente"]
    ag = geometria["area_garganta"]
    x = (sqrt(ag*area_relativa/pi)-geometria["radio_garganta"])/tan(
        radians(geometria["angulo_grados"]))
    if not isfinite(x) or not 0 <= x <= geometria["longitud_divergente"]:
        raise ValueError("La conversión axial ha producido una posición imposible.")
    return x


def proyectar_perfil_axial(perfil, geometria):
    """M44.4 -> dict con x [m], sin cambiar propiedades estáticas.

    Las dos ramas de choque conservan sendos estados en una única x.
    """
    base = {"disponible": False, "motivo": None, "segmentos": (),
            "choque": None, "x_choque": None, "longitud_divergente": None,
            "regimen": perfil.get("regimen") if perfil else None,
            "p_ambiente": perfil.get("p_ambiente") if perfil else None}
    if not geometria or not geometria.get("disponible"):
        base["motivo"] = "No existe divergente cónico físico para fijar una coordenada axial."
        return base
    if not perfil or not perfil.get("disponible"):
        base["motivo"] = "No existe un perfil cuasi-1D resuelto para transformar a posiciones."
        return base
    if abs(perfil["relacion_areas"]-geometria["relacion_areas"]) > (
            TOLERANCIA_RELATIVA_AREAS*max(1.,perfil["relacion_areas"],
                                          geometria["relacion_areas"])):
        raise ValueError("El perfil y la geometría no corresponden a las mismas áreas.")
    segmentos = tuple(tuple({**estado, "x": posicion_axial_por_area(
                         estado["area_relativa"], geometria)} for estado in serie)
                      for serie in perfil["segmentos"])
    choque = None
    x_choque = None
    if perfil.get("choque"):
        antes, despues = perfil["choque"]
        x_choque = posicion_axial_por_area(antes["area_relativa"], geometria)
        choque = ({**antes, "x":x_choque}, {**despues, "x":x_choque})
    base.update(disponible=True, motivo=None, segmentos=segmentos,
                choque=choque, x_choque=x_choque,
                longitud_divergente=geometria["longitud_divergente"])
    return base


def svg_perfil_axial(datos, magnitud):
    """SVG de Mach o presión frente a x [m]; choque sin unión ficticia."""
    if magnitud not in ("mach", "presion"):
        raise ValueError("Magnitud axial desconocida.")
    if not datos or not datos.get("disponible"):
        return None
    segmentos = datos["segmentos"]
    valores = [p[magnitud] for s in segmentos for p in s]
    if not valores:
        return None
    ref = 1. if magnitud == "mach" else datos["p_ambiente"]
    vmax = max(max(valores), ref)*1.18
    L = datos["longitud_divergente"]
    xplot = lambda x: 78+608*x/L
    yplot = lambda y: 247-207*y/vmax
    titulo = "Número de Mach [–]" if magnitud == "mach" else "Presión estática [kPa]"
    piezas = ["<rect width='760' height='335' fill='#f8fafc'/>",
              "<path d='M78 26 V247 H692' fill='none' stroke='#64748b'/>",
              f"<line x1='78' y1='{yplot(ref):.3f}' x2='692' y2='{yplot(ref):.3f}' stroke='#d97706' stroke-dasharray='6 5'/>",
              f"<text x='78' y='18' font-size='14' fill='#1e293b'>{titulo}</text>",
              "<text x='78' y='267' font-size='12' fill='#334155'>Garganta: 0 m</text>",
              f"<text x='690' y='267' text-anchor='end' font-size='12' fill='#334155'>Salida: {L:.5g} m</text>",
              "<text x='375' y='310' text-anchor='middle' font-size='13' fill='#334155'>Posición axial x [m]</text>"]
    for i in range(5):
        valor = vmax*i/4
        y = yplot(valor)
        piezas.append(f"<line x1='73' y1='{y:.3f}' x2='78' y2='{y:.3f}' stroke='#64748b'/>")
        piezas.append(f"<text x='68' y='{y+4:.3f}' text-anchor='end' font-size='12' fill='#334155'>{valor:.3g}</text>")
    for i in range(1,5):
        x = xplot(i*L/4)
        piezas.append(f"<line x1='{x:.3f}' y1='247' x2='{x:.3f}' y2='253' stroke='#64748b'/>")
        piezas.append(f"<text x='{x:.3f}' y='283' text-anchor='middle' font-size='11' fill='#334155'>{i*L/4:.3g}</text>")
    ref_nombre = "Referencia M = 1" if magnitud == "mach" else "p ambiente"
    piezas.append(f"<text x='684' y='{max(37,yplot(ref)-8):.3f}' text-anchor='end' font-size='12' fill='#92400e'>{ref_nombre}: {ref:.4g}</text>")
    for i, segmento in enumerate(segmentos):
        if not segmento:
            continue
        coords = " ".join(f"{xplot(p['x']):.3f},{yplot(p[magnitud]):.3f}" for p in segmento)
        color = "#2563eb" if i == 0 else "#059669"
        piezas.append(f"<polyline points='{coords}' fill='none' stroke='{color}' stroke-width='2.5'/>")
        for p in (segmento[0],segmento[-1]):
            piezas.append(f"<circle cx='{xplot(p['x']):.3f}' cy='{yplot(p[magnitud]):.3f}' r='4' fill='{color}'/>")
    if datos["choque"]:
        x = xplot(datos["x_choque"])
        piezas.append(f"<line x1='{x:.3f}' x2='{x:.3f}' y1='30' y2='247' stroke='#be123c' stroke-dasharray='4 4'/>")
        piezas.append(f"<text x='{x:.3f}' y='287' text-anchor='middle' font-size='12' fill='#9f1239'>Choque x={datos['x_choque']:.5g} m</text>")
    return ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 760 335' "
            "role='img' aria-label='Perfil axial calculado con salto discontinuo de choque, cuando existe'>"
            + "".join(piezas)+"</svg>")
