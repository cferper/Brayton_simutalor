"""Comparación puramente geométrica de semidivergencias (M46.3)."""

from geometria_tobera_conica import calcular_geometria_conica


ANGULOS_EDUCATIVOS = (5., 10., 15., 20., 25.)
ANGULOS_COMPARACION = (10., 15., 20.)


def estudiar_angulos_geometria(geometria, *, angulos=ANGULOS_EDUCATIVOS):
    """Dict de filas [°,m,m,m,–] manteniendo áreas Ag y Ae fijas.

    Conserva el ángulo del formulario aunque no esté en la lista inicial.
    Ninguna fila implica una pérdida aerodinámica ni rendimiento óptimo.
    """
    if not geometria or not geometria.get("disponible"):
        return {"disponible":False,"motivo":"No existe divergente cónico dimensionado.",
                "filas":(),"seleccionado":None,"comparacion":()}
    dimensionamiento = {"disponible":True,"tipo_tobera":"convergente_divergente",
                       "area_garganta":geometria["area_garganta"],
                       "area_salida":geometria["area_salida"]}
    seleccionado = geometria["angulo_grados"]
    lista = sorted(set((*angulos, seleccionado)))
    filas = []
    for alpha in lista:
        g = calcular_geometria_conica(dimensionamiento, alpha)
        filas.append({"angulo_grados":g["angulo_grados"],
                      "longitud_divergente":g["longitud_divergente"],
                      "diametro_garganta":g["diametro_garganta"],
                      "diametro_salida":g["diametro_salida"],
                      "radio_garganta":g["radio_garganta"],
                      "radio_salida":g["radio_salida"],
                      "relacion_areas":g["relacion_areas"],
                      "seleccionado":alpha==seleccionado})
    comparacion = tuple(calcular_geometria_conica(dimensionamiento, a)
                        for a in ANGULOS_COMPARACION)
    return {"disponible":True,"motivo":None,"filas":tuple(filas),
            "seleccionado":seleccionado,"comparacion":comparacion}


def svg_longitud_angulo(estudio):
    """SVG de Ld(α), con el α actual destacado y ambos ejes graduados."""
    if not estudio or not estudio["disponible"]:
        return None
    filas = estudio["filas"]
    max_l = max(f["longitud_divergente"] for f in filas)*1.12
    min_a, max_a = filas[0]["angulo_grados"], filas[-1]["angulo_grados"]
    # Si se solicita un solo ángulo válido, mantenemos un eje horizontal.
    ancho_a = max(1.,max_a-min_a)
    sx = lambda a: 95+570*(a-min_a)/ancho_a
    sy = lambda l: 255-203*l/max_l
    piezas = ["<rect width='760' height='330' fill='#f8fafc'/>",
              "<path d='M95 34 V255 H680' fill='none' stroke='#475569'/>",
              "<text x='95' y='20' fill='#334155' font-size='14'>Longitud del divergente [m]</text>",
              "<text x='380' y='317' text-anchor='middle' fill='#334155' font-size='13'>Semidivergencia α [°]</text>"]
    for i in range(5):
        valor = max_l*i/4
        y = sy(valor)
        piezas.append(f"<text x='85' y='{y+4:.2f}' text-anchor='end' font-size='12' fill='#334155'>{valor:.3g}</text>")
        piezas.append(f"<line x1='95' y1='{y:.2f}' x2='680' y2='{y:.2f}' stroke='#cbd5e1' stroke-dasharray='3 6'/>")
    cadena = " ".join(f"{sx(f['angulo_grados']):.2f},{sy(f['longitud_divergente']):.2f}" for f in filas)
    piezas.append(f"<polyline points='{cadena}' fill='none' stroke='#2563eb' stroke-width='2.5'/>")
    for f in filas:
        x, y = sx(f["angulo_grados"]), sy(f["longitud_divergente"])
        col = "#dc2626" if f["seleccionado"] else "#2563eb"
        piezas.append(f"<circle cx='{x:.2f}' cy='{y:.2f}' r='{7 if f['seleccionado'] else 4.5}' fill='{col}'/>")
        piezas.append(f"<text x='{x:.2f}' y='275' text-anchor='middle' font-size='12' fill='{col}'>{f['angulo_grados']:.4g}°</text>")
        if f["seleccionado"]:
            piezas.append(f"<text x='{x:.2f}' y='{max(46,y-12):.2f}' text-anchor='middle' font-size='12' fill='#991b1b'>Selección · {f['longitud_divergente']:.4g} m</text>")
    return ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 760 330' "
            "role='img' aria-label='Longitud frente a semidivergencia, ángulo elegido destacado'>"
            +"".join(piezas)+"</svg>")


def svg_comparacion_conos(estudio):
    """Tres divergentes (10°,15°,20°), todos con la misma escala en x e y."""
    if not estudio or not estudio["disponible"]:
        return None
    geometria = estudio["comparacion"]
    Lmax = max(g["longitud_divergente"] for g in geometria)
    re = geometria[0]["radio_salida"]
    escala = min(575/Lmax, 70/re)
    piezas = ["<rect width='760' height='620' fill='#f8fafc'/>",
              "<text x='35' y='23' font-size='15' fill='#334155'>Conos con Ag y Ae constantes · misma escala longitudinal y radial</text>"]
    for i,g in enumerate(geometria):
        eje = 117+180*i
        x0, xe = 130.,130+g["longitud_divergente"]*escala
        yg,ye = g["radio_garganta"]*escala, g["radio_salida"]*escala
        puntos = f"{x0:.3f},{eje-yg:.3f} {xe:.3f},{eje-ye:.3f} {xe:.3f},{eje+ye:.3f} {x0:.3f},{eje+yg:.3f}"
        piezas.extend((f"<polygon points='{puntos}' stroke='#2563eb' stroke-width='2' fill='#dbeafe'/>",
                       f"<line x1='110' y1='{eje}' x2='680' y2='{eje}' stroke='#94a3b8' stroke-dasharray='5 5'/>",
                       f"<text x='35' y='{eje+4}' font-size='14' fill='#1d4ed8'>{g['angulo_grados']:.0f}°</text>",
                       f"<text x='490' y='{eje-23}' font-size='13' fill='#334155'>Ld = {g['longitud_divergente']:.5g} m</text>"))
    piezas.append("<text x='35' y='604' font-size='12' fill='#475569'>La anchura y la altura usan la misma escala px/m en los tres dibujos.</text>")
    return ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 760 620' "
            "role='img' aria-label='Comparación a escala uniforme de tres toberas cónicas'>"
            +"".join(piezas)+"</svg>")
