"""Presentación web de sensibilidad y mapas de turborreactor; sin ecuaciones nuevas.

Los barridos se delegan a ``mapas_prestaciones_turborreactor_cp`` (M38/M39).
Los gráficos SVG, los límites de tamaño y los formularios son responsabilidad
exclusiva de este adaptador. Ninguna salida indefinida se convierte en cero.
"""

from html import escape
from math import isfinite

from mapas_prestaciones_turborreactor_cp import barrer_mach_altitud, barrer_rp_t3
from turborreactor_web import leer_turborreactor


ESTADOS_WEB = {
    "valido": "Válida",
    "empuje_no_positivo": "Empuje no positivo",
    "sin_expansion": "Sin expansión",
    "inadmisible": "Inadmisible",
    "fallo_numerico": "Fallo numérico",
}

# Límites de la *interfaz*, no límites de certificación de un motor real.
PARAMETROS_OFAT = {
    "rp": ("Relación de compresión", "–", 1.01, 40, "5", "15"),
    "T3": ("Temperatura de entrada a turbina", "K", 200, 2000, "1400", "1800"),
    "mach": ("Mach de vuelo", "–", 0, .95, "0", "0.8"),
    "eta_c": ("Rendimiento del compresor", "–", .2, 1, "0.7", "1"),
    "eta_t": ("Rendimiento de turbina", "–", .2, 1, "0.7", "1"),
    "pi_d": ("Recuperación del difusor", "–", .5, 1, "0.8", "1"),
    "delta_pct": ("Pérdida de presión de cámara", "%", 0, 30, "0", "10"),
}

DEFAULT_ESTUDIOS = {
    "sens_parametro": "rp", "sens_min": "5", "sens_max": "15", "sens_n": "11",
    "mapa_tipo": "rp_T3", "mapa_rp_min": "5", "mapa_rp_max": "15",
    "mapa_T3_min": "1400", "mapa_T3_max": "1800",
    "mapa_mach_min": "0", "mapa_mach_max": "0.8",
    "mapa_altitud_min": "0", "mapa_altitud_max": "20000",
    "mapa_nx": "5", "mapa_ny": "5",
}


def valores_estudios(formulario=None):
    """Devuelve dict[str,str] de controles; retiene valores erróneos en POST."""
    valores = dict(DEFAULT_ESTUDIOS)
    if formulario is not None:
        valores.update({clave: formulario.get(clave, predeterminado)
                        for clave, predeterminado in DEFAULT_ESTUDIOS.items()})
    return valores


def _real(valores, clave, minimo, maximo):
    """Convierte una cadena finita dentro del intervalo inclusivo indicado."""
    try:
        valor = float(valores[clave].strip())
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"{clave}: introduce un número.") from exc
    if not isfinite(valor) or not minimo <= valor <= maximo:
        raise ValueError(f"{clave}: introduce un número entre {minimo:g} y {maximo:g}.")
    return valor


def _entero(valores, clave, minimo, maximo):
    """Exige entero decimal real: no acepta flotantes ni fracciones."""
    try:
        valor = int(valores[clave].strip())
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"{clave}: introduce un entero de {minimo} a {maximo}.") from exc
    if not minimo <= valor <= maximo:
        raise ValueError(f"{clave}: admite de {minimo} a {maximo} puntos.")
    return valor


def _eje(valores, clave_min, clave_max, limite_min, limite_max, n):
    """Malla de n puntos equiespaciados, sin numpy, con extremos incluidos."""
    inferior = _real(valores, clave_min, limite_min, limite_max)
    superior = _real(valores, clave_max, limite_min, limite_max)
    if inferior >= superior:
        raise ValueError(f"{clave_min} debe ser estrictamente menor que {clave_max}.")
    return [inferior + (superior-inferior)*i/(n-1) for i in range(n)]


def _argumentos_comunes(datos):
    """Filtra los parámetros físicos que aceptan los barridos públicos M38."""
    claves = ("eta_c", "eta_t", "eta_m", "eta_n", "eta_b", "PCI", "pi_d", "delta")
    return {clave: datos[clave] for clave in claves}


def _ambiente_mapa(datos):
    """Selecciona una única convención ambiental, directa o ISA."""
    if "altitud_geopotencial" in datos:
        return {"altitud_geopotencial": datos["altitud_geopotencial"]}
    return {"T_amb": datos["T_amb"], "p_amb": datos["p_amb"]}


def _base_svg(ancho, alto, cuerpo, descripcion):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" '
            f'viewBox="0 0 {ancho} {alto}" '
            f'role="img" aria-label="{escape(descripcion, quote=True)}">'
            '<g font-family="sans-serif" fill="#17334e">' + ''.join(cuerpo) + '</g></svg>')


def _svg_curva(puntos, parametro, unidad_x, clave, titulo, unidad_y):
    """Polilíneas *separadas* en cada ausencia; cruces en puntos sin dato."""
    ancho, alto = 790, 340
    x0, x1, y0, y1 = 88, 750, 44, 262
    xs = [p["valor_parametro"] for p in puntos]
    disponibles = [p["punto"].get(clave) for p in puntos]
    validos = [v for p, v in zip(puntos, disponibles)
               if p["punto"]["estado"] == "valido" and v is not None]
    lo, hi = (min(validos), max(validos)) if validos else (0, 1)
    if hi == lo:
        margen = max(abs(hi)*.05, 1e-6)
        lo, hi = lo-margen, hi+margen
    xa, xb = xs[0], xs[-1]
    coord_x = lambda x: x0+(x-xa)/(xb-xa)*(x1-x0)
    coord_y = lambda v: y1-(v-lo)/(hi-lo)*(y1-y0)
    svg = [f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="#71879b"/>',
           f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#71879b"/>',
           f'<text x="{x0}" y="{y0-11}" font-size="13">{escape(titulo)} [{escape(unidad_y)}]</text>',
           f'<text x="{(x0+x1)/2}" y="{alto-19}" text-anchor="middle" font-size="13">'
           f'{escape(PARAMETROS_OFAT[parametro][0])} [{escape(unidad_x)}]</text>']
    for i in range(5):
        y = y1-(y1-y0)*i/4
        val = lo+(hi-lo)*i/4
        svg.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" '
                   f'stroke="#e2e9f0"/><text x="{x0-8}" y="{y+4:.1f}" text-anchor="end" font-size="11">{val:.4g}</text>')
    for i in sorted(set((0, len(xs)//4, len(xs)//2, 3*len(xs)//4, len(xs)-1))):
        svg.append(f'<text x="{coord_x(xs[i]):.1f}" y="{y1+19}" '
                   f'text-anchor="middle" font-size="11">{xs[i]:.4g}</text>')
    segmento = []
    def cerrar():
        if len(segmento) > 1:
            svg.append(f'<polyline points="{" ".join(segmento)}" fill="none" '
                       'stroke="#1967a6" stroke-width="2.8"/>')
        segmento.clear()
    for p, valor in zip(puntos, disponibles):
        x = coord_x(p["valor_parametro"])
        if p["punto"]["estado"] == "valido" and valor is not None:
            y = coord_y(valor)
            segmento.append(f'{x:.2f},{y:.2f}')
            svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#1967a6">'
                       f'<title>{p["valor_parametro"]:.4g}: {valor:.5g}</title></circle>')
        else:
            cerrar()
            svg.append(f'<path d="M{x-5:.2f} {y1-5} l10 10 m-10 0 l10 -10" '
                       f'stroke="#ad4b24" stroke-width="2"><title>'
                       f'{escape(ESTADOS_WEB[p["punto"]["estado"]])}: sin dato</title></path>')
    cerrar()
    if not validos:
        svg.append('<text x="430" y="153" text-anchor="middle" font-size="16">'
                   'Sin prestaciones definidas en este intervalo</text>')
    svg.append('<text x="120" y="310" font-size="12" fill="#1967a6">● Válido</text>'
               '<text x="245" y="310" font-size="12" fill="#ad4b24">× Sin dato / inadmisible</text>')
    return _base_svg(ancho, alto, svg, f'{titulo} frente a {parametro}; interrupciones si faltan resultados')


def _color(valor, minimo, maximo, clave):
    proporcion = .5 if maximo == minimo else (valor-minimo)/(maximo-minimo)
    tono = 205 if clave == 'Fs' else 32
    return f'hsl({tono} 72% {92-42*proporcion:.1f}%)'


def _svg_mapa(mapa, clave, titulo):
    """Mapa discreto con escalas, unidades, cruces y leyenda independiente del color."""
    xs, ys = mapa["valores_x"], mapa["valores_y"]
    celda_x, celda_y = 62, 40
    x0, y0 = 124, 64
    ancho, alto = x0+len(xs)*celda_x+25, y0+len(ys)*celda_y+105
    datos = [p[clave] for fila in mapa["puntos"] for p in fila
             if p["estado"] == "valido" and p[clave] is not None]
    lo, hi = (min(datos), max(datos)) if datos else (0, 1)
    unidad = "N/(kg/s de aire)" if clave == "Fs" else "kg/(N·h)"
    svg = [f'<text x="{x0}" y="25" font-size="15" font-weight="600">'
           f'{escape(titulo)} [{escape(unidad)}]</text>',
           f'<text x="{x0}" y="43" font-size="11">Escala de valores válidos: '
           f'{lo:.5g} → {hi:.5g} (más intenso = mayor valor)</text>']
    for iy, fila in enumerate(mapa["puntos"]):
        for ix, p in enumerate(fila):
            x, y = x0+ix*celda_x, y0+iy*celda_y
            valor = p[clave] if p["estado"] == "valido" else None
            color = _color(valor, lo, hi, clave) if valor is not None else "#ebeff3"
            descripcion = (f'{xs[ix]:.5g}, {ys[iy]:.5g}: '
                           + (f'{valor:.6g} {unidad}' if valor is not None else
                              ESTADOS_WEB[p["estado"]]))
            svg.append(f'<rect x="{x}" y="{y}" width="{celda_x-2}" height="{celda_y-2}" '
                       f'rx="3" fill="{color}" stroke="#9aacbb">'
                       f'<title>{escape(descripcion)}</title></rect>')
            if valor is None:
                svg.append(f'<text x="{x+celda_x/2}" y="{y+25}" font-size="21" '
                           'fill="#904228" text-anchor="middle">×</text>')
            else:
                svg.append(f'<text x="{x+celda_x/2}" y="{y+24}" font-size="11" '
                           f'text-anchor="middle">{valor:.4g}</text>')
    for i, x in enumerate(xs):
        svg.append(f'<text x="{x0+i*celda_x+celda_x/2}" y="{y0+len(ys)*celda_y+17}" '
                   f'font-size="11" text-anchor="middle">{x:.4g}</text>')
    for i, y in enumerate(ys):
        svg.append(f'<text x="{x0-10}" y="{y0+i*celda_y+25}" text-anchor="end" '
                   f'font-size="11">{y:.5g}</text>')
    eje_x = "rp [–]" if mapa["eje_x"] == "rp" else "Mach [–]"
    eje_y = "T3 [K]" if mapa["eje_y"] == "T3" else "Altitud ISA [m]"
    svg.append(f'<text x="{x0+len(xs)*celda_x/2}" y="{alto-50}" font-size="12" '
               f'text-anchor="middle">{eje_x}</text>')
    svg.append(f'<text x="10" y="{y0-12}" font-size="12">{eje_y}</text>')
    svg.append(f'<text x="{x0}" y="{alto-21}" font-size="12">'
               '× Sin dato / estado inválido; el número dentro de cada celda expresa el valor</text>')
    if not datos:
        svg.append(f'<text x="{x0}" y="{alto-8}" font-size="11">'
                   'No hay magnitudes definidas en esta malla.</text>')
    return _base_svg(ancho, alto, svg, f'Mapa {titulo}; {eje_x} y {eje_y}; puntos inválidos con cruz')


def _svg_pareto(mapa):
    """Dispersión Fs–TSFC: círculo sin dominar destacado por anillo y leyenda."""
    candidatos = [p for fila in mapa["puntos"] for p in fila if p["estado"] == "valido"]
    frontera = {id(p) for p in mapa["pareto"]}
    x0, x1, y0, y1 = 104, 730, 43, 270
    xs = [p["TSFC_kg_N_h"] for p in candidatos]
    ys = [p["Fs"] for p in candidatos]
    if not candidatos:
        return _base_svg(780, 360, ['<text x="70" y="160">Sin puntos válidos para Pareto.</text>'],
                         'Sin frente de Pareto definido')
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    dx = max(xmax-xmin, 1e-9)
    dy = max(ymax-ymin, 1e-9)
    cx = lambda v: x0+(v-xmin)/dx*(x1-x0)
    cy = lambda v: y1-(v-ymin)/dy*(y1-y0)
    svg = [f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="#71879b"/>',
           f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#71879b"/>',
           '<text x="120" y="20" font-size="14">Empuje específico neto [N/(kg/s de aire)]</text>',
           '<text x="415" y="342" font-size="13" text-anchor="middle">TSFC [kg/(N·h)]</text>']
    for i in range(5):
        fx=xmin+dx*i/4
        fy=ymin+dy*i/4
        xx=x0+(x1-x0)*i/4
        yy=y1-(y1-y0)*i/4
        svg.extend([f'<text x="{xx}" y="{y1+19}" font-size="11" text-anchor="middle">{fx:.4g}</text>',
                    f'<text x="{x0-8}" y="{yy+4}" font-size="11" text-anchor="end">{fy:.4g}</text>',
                    f'<line x1="{x0}" y1="{yy}" x2="{x1}" y2="{yy}" stroke="#e4eaf0"/>'])
    for p in candidatos:
        x,y=cx(p["TSFC_kg_N_h"]),cy(p["Fs"])
        no_dominado=id(p) in frontera
        svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{6 if no_dominado else 3.2}" '
                   f'fill="{"#d28b1b" if no_dominado else "#648bb0"}" '
                   f'stroke="{"#553800" if no_dominado else "none"}" '
                   f'stroke-width="1.5"><title>rp={p["entradas"]["rp"]:.5g}, '
                   f'T3={p["entradas"]["T3"]:.5g} K; '
                   f'Fs={p["Fs"]:.6g}, TSFC={p["TSFC_kg_N_h"]:.6g}'
                   f'{"; no dominado" if no_dominado else "; dominado"}</title></circle>')
    svg.append('<text x="110" y="315" font-size="12">● Azul: evaluado válido  '
               '◉ Ocre con borde: no dominado</text>')
    return _base_svg(780, 360, svg, 'Pareto del mapa rp y T3: minimizar TSFC y maximizar empuje neto')


def preparar_estudio(accion, formulario, valores_motor):
    """Valida el formulario y devuelve dict de vista para OFAT o mapa M38.

    :param accion: 'sensibilidad' o 'mapa', str.
    :param formulario: dict/multidict[str,str] con controles de estudio.
    :param valores_motor: dict[str,str] de configuración existente M40.
    :returns: dict con puntos, SVG, resumen, tablas y unidades; ningún cálculo
        termodinámico propio. Lanza ValueError ante dominios/tamaños inválidos.
    """
    v = valores_estudios(formulario)
    datos = leer_turborreactor(valores_motor)
    comunes = _argumentos_comunes(datos)
    if accion == "sensibilidad":
        nombre = v["sens_parametro"]
        if nombre not in PARAMETROS_OFAT:
            raise ValueError("Parámetro OFAT desconocido.")
        etiqueta, unidad, inferior, superior, _, _ = PARAMETROS_OFAT[nombre]
        n = _entero(v, "sens_n", 2, 31)
        eje = _eje(v, "sens_min", "sens_max", inferior, superior, n)
        puntos = []
        for x in eje:
            fijos = {**comunes, **_ambiente_mapa(datos), "mach": datos["mach"]}
            rp, t3 = datos["rp"], datos["T3"]
            if nombre == "rp":
                rp = x
            elif nombre == "T3":
                t3 = x
            elif nombre == "delta_pct":
                fijos["delta"] = x/100
            else:
                fijos[nombre] = x
            barrido = barrer_rp_t3([rp], [t3], **fijos)
            puntos.append({"valor_parametro": x, "punto": barrido["puntos"][0][0]})
        return {"tipo": "sensibilidad", "parametro": nombre,
                "etiqueta": etiqueta, "unidad": unidad, "puntos": puntos,
                "grafico_Fs": _svg_curva(puntos, nombre, unidad, "Fs",
                                         "Empuje específico neto", "N/(kg/s de aire)"),
                "grafico_TSFC": _svg_curva(puntos, nombre, unidad, "TSFC_kg_N_h",
                                           "TSFC", "kg/(N·h)"),
                "cuenta_validos": sum(p["punto"]["estado"] == "valido" for p in puntos),
                "total": len(puntos)}
    if accion == "mapa":
        tipo = v["mapa_tipo"]
        if tipo not in ("rp_T3", "Mach_altitud"):
            raise ValueError("Tipo de mapa desconocido.")
        nx = _entero(v, "mapa_nx", 2, 15)
        ny = _entero(v, "mapa_ny", 2, 15)
        if tipo == "rp_T3":
            xs = _eje(v, "mapa_rp_min", "mapa_rp_max", 1.01, 40, nx)
            ys = _eje(v, "mapa_T3_min", "mapa_T3_max", 200, 2000, ny)
            mapa = barrer_rp_t3(xs, ys, mach=datos["mach"],
                                **_ambiente_mapa(datos), **comunes)
        else:
            xs = _eje(v, "mapa_mach_min", "mapa_mach_max", 0, .95, nx)
            ys = _eje(v, "mapa_altitud_min", "mapa_altitud_max", 0, 20000, ny)
            mapa = barrer_mach_altitud(xs, ys, rp=datos["rp"], T3=datos["T3"],
                                        **comunes)
        return {"tipo": "mapa", "nombre": tipo, "datos": mapa,
                "grafico_Fs": _svg_mapa(mapa, "Fs", "Empuje específico neto"),
                "grafico_TSFC": _svg_mapa(mapa, "TSFC_kg_N_h", "TSFC"),
                "grafico_pareto": _svg_pareto(mapa) if mapa["pareto_aplicable"] else None,
                "filas": [p for fila in mapa["puntos"] for p in fila]}
    raise ValueError("Acción de estudio desconocida.")
