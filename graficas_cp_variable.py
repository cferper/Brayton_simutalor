"""Gráficas SVG del ciclo cp(T); presenta resultados sin alterar el modelo.

Solo los puntos y muestras procedentes de los módulos científicos representan
estados/ciclos calculados. Las uniones T–s y P–v son guías esquemáticas.
"""

from html import escape
from math import exp, isfinite, log

from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo, resolver_ciclo
from propiedades_aire import R_AIRE, T_MAX, T_MIN, cp, gamma


AZUL = "#2563eb"
NARANJA = "#c2410c"
VERDE = "#0f766e"
GRIS = "#64748b"


def _numero(valor):
    """Texto breve de una marca numérica, sin alterar el dato de origen."""
    if abs(valor) < 1e-12:
        return "0"
    return f"{valor:.4g}"


def _margen(valores):
    """Amplía solo la ventana vertical para no cortar puntos extremos."""
    minimo, maximo = min(valores), max(valores)
    amplitud = maximo - minimo
    if amplitud <= 0:
        amplitud = max(abs(minimo) * .2, 1e-3)
    return minimo - .09 * amplitud, maximo + .09 * amplitud


def _marco(nombre, x_etiqueta, y_etiqueta, x_lim, y_lim, *, log_x=False):
    """Devuelve el prefijo SVG y una función que proyecta magnitudes físicas.

    Las abscisas logarítmicas se proyectan mediante ln(x), pero las marcas
    muestran la relación de compresión real, nunca su logaritmo.
    """
    xa, xb = x_lim
    ya, yb = y_lim
    if not all(isfinite(v) for v in (xa, xb, ya, yb)):
        raise ValueError("Los ejes deben contener valores finitos.")
    if log_x:
        if xa <= 0 or xb <= 0:
            raise ValueError("La escala logarítmica necesita abscisas positivas.")
        xa, xb = log(xa), log(xb)
    if xb <= xa:
        ancho = max(abs(xa) * .1, 1e-5)
        xa -= ancho
        xb += ancho
    if yb <= ya:
        alto = max(abs(ya) * .1, 1e-5)
        ya -= alto
        yb += alto

    def posicion(x, y):
        xx = log(x) if log_x else x
        return 88 + 582 * (xx - xa) / (xb - xa), 325 - 277 * (y - ya) / (yb - ya)

    piezas = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 408" role="img" '
        f'aria-label="{escape(nombre, quote=True)}" '
        f'data-grafica="{escape(nombre, quote=True)}">',
        f'<title>{escape(nombre)}</title>',
        '<rect x="88" y="48" width="582" height="277" fill="#fff"/>',
    ]
    for i in range(6):
        valor_x = xa + (xb - xa) * i / 5
        valor_y = ya + (yb - ya) * i / 5
        px = 88 + 582 * i / 5
        py = 325 - 277 * i / 5
        etiqueta_x = _numero(exp(valor_x) if log_x else valor_x)
        piezas += [
            f'<line x1="{px:.3f}" y1="48" x2="{px:.3f}" y2="325" stroke="#e2e8f0"/>',
            f'<text x="{px:.3f}" y="346" text-anchor="middle" font-size="12" fill="currentColor">{etiqueta_x}</text>',
            f'<line x1="88" y1="{py:.3f}" x2="670" y2="{py:.3f}" stroke="#e2e8f0"/>',
            f'<text x="79" y="{py + 4:.3f}" text-anchor="end" font-size="12" fill="currentColor">{_numero(valor_y)}</text>',
        ]
    piezas += [
        '<rect x="88" y="48" width="582" height="277" fill="none" stroke="#64748b"/>',
        f'<text x="379" y="383" text-anchor="middle" font-size="15" fill="currentColor">{escape(x_etiqueta)}</text>',
        f'<text x="21" y="185" text-anchor="middle" transform="rotate(-90 21 185)" '
        f'font-size="15" fill="currentColor">{escape(y_etiqueta)}</text>',
    ]
    return "".join(piezas), posicion


def _tramos(muestras, posicion, *, color=AZUL):
    """Conserva cada None como discontinuidad; no une dominios separados."""
    partes, actual = [], []

    def vaciar():
        if len(actual) > 1:
            coords = " ".join(f"{x:.3f},{y:.3f}" for x, y in actual)
            partes.append(f'<polyline points="{coords}" fill="none" stroke="{color}" '
                          'stroke-width="2.7" stroke-linejoin="round" stroke-linecap="round"/>')
        elif actual:
            partes.append(f'<circle cx="{actual[0][0]:.3f}" cy="{actual[0][1]:.3f}" '
                          f'r="3" fill="{color}"/>')
        actual.clear()

    for muestra in muestras:
        if muestra is None:
            vaciar()
        else:
            actual.append(posicion(*muestra))
    vaciar()
    return "".join(partes)


def _estado(numero, x, y, posicion, *, color=AZUL, etiqueta=None):
    px, py = posicion(x, y)
    info = etiqueta or f"Estado {numero}"
    return (f'<circle cx="{px:.3f}" cy="{py:.3f}" r="5" '
            f'fill="{color}" stroke="#fff" stroke-width="1.5" '
            f'data-estado="{numero}" data-x="{x:.10g}" data-y="{y:.10g}">'
            f'<title>{escape(info)}</title></circle>'
            f'<text x="{px + 9:.3f}" y="{py - 9:.3f}" font-size="15" '
            f'font-weight="600" fill="currentColor">{numero}</text>')


def svg_ts(ciclo):
    """T–s: cuatro estados exactos y conexiones exclusivamente esquemáticas."""
    puntos = list(zip(ciclo["entropias"], ciclo["temperaturas"]))
    cuerpo, posicion = _marco(
        "T–s, estados cp(T) y tramos esquemáticos",
        "Entropía específica s [kJ/(kg·K)]", "Temperatura T [K]",
        (min(x for x, _ in puntos), max(x for x, _ in puntos)),
        _margen([y for _, y in puntos]),
    )
    coords = " ".join(f"{posicion(*p)[0]:.3f},{posicion(*p)[1]:.3f}"
                      for p in puntos + puntos[:1])
    cuerpo += (f'<polyline points="{coords}" fill="none" stroke="{GRIS}" '
               'stroke-width="2" stroke-dasharray="7 5"/>')
    for i, (entropia, temperatura) in enumerate(puntos, 1):
        cuerpo += _estado(i, entropia, temperatura, posicion,
                          etiqueta=f"Estado {i}: T={temperatura:.4f} K, s={entropia:.5f} kJ/(kg·K)")
    return cuerpo + "</svg>"


def svg_pv(ciclo):
    """P–v: p en kPa, volumen específico v = (R_AIRE/1000)·T/p en m³/kg."""
    puntos = [(R_AIRE * t / (1000.0 * p), p)
              for t, p in zip(ciclo["temperaturas"], ciclo["presiones"])]
    cuerpo, posicion = _marco(
        "P–v, estados cp(T) y tramos esquemáticos",
        "Volumen específico v [m³/kg]", "Presión p [kPa]",
        (min(x for x, _ in puntos), max(x for x, _ in puntos)),
        _margen([p for _, p in puntos]),
    )
    coords = " ".join(f"{posicion(*p)[0]:.3f},{posicion(*p)[1]:.3f}"
                      for p in puntos + puntos[:1])
    cuerpo += (f'<polyline points="{coords}" fill="none" stroke="{GRIS}" '
               'stroke-width="2" stroke-dasharray="7 5"/>')
    for i, (volumen, presion) in enumerate(puntos, 1):
        cuerpo += _estado(i, volumen, presion, posicion,
                          etiqueta=f"Estado {i}: v={volumen:.6g} m³/kg, p={presion:.5g} kPa")
    return cuerpo + "</svg>"


def svg_propiedades(estados):
    """Dos SVG independientes: cp(T) y gamma(T), de 200 a 2000 K."""
    temperaturas = [T_MIN + (T_MAX - T_MIN) * i / 72 for i in range(73)]
    curvas = (("Calor específico cp(T)", "cp [J/(kg·K)]", cp, VERDE),
              ("Relación de calores gamma(T)", "γ [–]", gamma, NARANJA))
    salida = []
    for titulo, eje_y, funcion, color in curvas:
        muestras = [(t, funcion(t)) for t in temperaturas]
        puntos = [(e["T"], funcion(e["T"])) for e in estados]
        cuerpo, posicion = _marco(
            titulo, "Temperatura T [K]", eje_y,
            (T_MIN, T_MAX), _margen([y for _, y in muestras] +
                                    [y for _, y in puntos]),
        )
        cuerpo += _tramos(muestras, posicion, color=color)
        for e, (t, valor) in zip(estados, puntos):
            px, py = posicion(t, valor)
            cuerpo += (f'<line x1="{px:.3f}" y1="{py:.3f}" x2="{px:.3f}" '
                       f'y2="325" stroke="{GRIS}" stroke-dasharray="3 4"/>')
            cuerpo += _estado(e["numero"], t, valor, posicion, color=color,
                              etiqueta=f"Estado {e['numero']}: T={t:.4f} K, valor={valor:.6g}")
        salida.append(cuerpo + "</svg>")
    return tuple(salida)


def svg_balances(ciclo):
    """Cinco magnitudes con sus signos originales, en kJ/kg; solo ciclo motor."""
    if not ciclo["viable"]:
        return None
    conceptos = [
        ("Compresor · consumido", "trabajo_compresor", NARANJA),
        ("Turbina · producido", "trabajo_turbina", VERDE),
        ("Trabajo neto", "trabajo_neto", AZUL),
        ("Calor aportado", "calor_aportado", "#a16207"),
        ("Calor rechazado", "calor_rechazado", GRIS),
    ]
    valores = [ciclo[clave] for _, clave, _ in conceptos]
    minimo, maximo = min(0, *valores), max(0, *valores)
    amplitud = max(maximo - minimo, 1)
    minimo -= .07 * amplitud
    maximo += .17 * amplitud

    def px(valor):
        return 215 + 420 * (valor - minimo) / (maximo - minimo)

    cuerpo = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 390" role="img" '
              'aria-label="Balance de energías específicas cp(T)" data-grafica="balances">',
              '<title>Trabajo y calor por kilogramo de aire</title>']
    for i in range(6):
        valor = minimo + (maximo - minimo) * i / 5
        x = px(valor)
        cuerpo.append(f'<line x1="{x:.3f}" y1="54" x2="{x:.3f}" y2="318" stroke="#e2e8f0"/>')
        cuerpo.append(f'<text x="{x:.3f}" y="340" text-anchor="middle" '
                      f'font-size="12" fill="currentColor">{_numero(valor)}</text>')
    cero = px(0)
    cuerpo.append(f'<line x1="{cero:.3f}" y1="48" x2="{cero:.3f}" y2="318" '
                  'stroke="currentColor" stroke-width="1.7"/>')
    for i, (titulo, clave, color) in enumerate(conceptos):
        valor = ciclo[clave]
        y = 78 + 51 * i
        extremo = px(valor)
        cuerpo.append(f'<text x="12" y="{y + 6}" font-size="13" '
                      f'fill="currentColor">{escape(titulo)}</text>')
        cuerpo.append(f'<rect x="{min(cero, extremo):.3f}" y="{y - 10}" '
                      f'width="{abs(extremo - cero):.3f}" height="19" fill="{color}" '
                      f'data-energia="{clave}" data-valor="{valor:.12g}"/>')
        texto_x = extremo + 5 if valor >= 0 else extremo - 5
        anchor = "start" if valor >= 0 else "end"
        cuerpo.append(f'<text x="{texto_x:.3f}" y="{y + 5}" text-anchor="{anchor}" '
                      f'font-size="12" fill="currentColor">{_numero(valor)}</text>')
    cuerpo.append('<text x="422" y="372" text-anchor="middle" font-size="15" '
                  'fill="currentColor">Energía específica [kJ/kg]</text></svg>')
    return "".join(cuerpo)


def svg_comparacion(ideal, configurado):
    """Comparación en dos paneles con ejes independientes kJ/kg y porcentaje."""
    if not ideal["viable"] or not configurado["viable"]:
        return None
    pares = (("Compresor", "trabajo_compresor"), ("Turbina", "trabajo_turbina"),
             ("Neto", "trabajo_neto"))
    techo = max(ideal[k] for _, k in pares)
    techo = max(techo, *(configurado[k] for _, k in pares), 1.0) * 1.24
    ancho = 390
    origen = 240

    def barra(valor, y, color, clave, modelo, *, escala):
        x_fin = origen + ancho * valor / escala
        return (f'<rect x="{origen}" y="{y}" width="{max(0, x_fin - origen):.3f}" '
                f'height="14" fill="{color}" data-modelo="{modelo}" '
                f'data-magnitud="{clave}" data-valor="{valor:.12g}"/>'
                f'<text x="{x_fin + 5:.3f}" y="{y + 11}" font-size="11" '
                f'fill="currentColor">{_numero(valor)}</text>')

    cuerpo = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 490" role="img" '
        'aria-label="Comparación cp(T) ideal de componentes y caso configurado" '
        'data-grafica="comparacion-ideal">',
        '<title>Ambos casos usan aire de propiedades variables cp(T)</title>',
        f'<rect x="240" y="25" width="14" height="12" fill="{AZUL}"/>',
        '<text x="260" y="36" font-size="13" fill="currentColor">Componentes ideales</text>',
        f'<rect x="445" y="25" width="14" height="12" fill="{NARANJA}"/>',
        '<text x="465" y="36" font-size="13" fill="currentColor">Caso configurado</text>',
    ]
    for i, (titulo, clave) in enumerate(pares):
        y = 70 + i * 72
        cuerpo.append(f'<text x="16" y="{y + 21}" font-size="14" fill="currentColor">'
                      f'{escape(titulo)}</text>')
        cuerpo.append(barra(ideal[clave], y, AZUL, clave, "ideal", escala=techo))
        cuerpo.append(barra(configurado[clave], y + 17, NARANJA, clave,
                           "configurado", escala=techo))
    for i in range(5):
        val = techo * i / 4
        x = origen + ancho * i / 4
        cuerpo.append(f'<line x1="{x:.3f}" y1="62" x2="{x:.3f}" y2="280" '
                      'stroke="#e2e8f0" stroke-dasharray="2 4"/>')
        cuerpo.append(f'<text x="{x:.3f}" y="304" text-anchor="middle" '
                      f'font-size="12" fill="currentColor">{_numero(val)}</text>')
    cuerpo.append('<text x="439" y="327" text-anchor="middle" font-size="14" '
                  'fill="currentColor">Trabajos específicos [kJ/kg]</text>')
    cuerpo.append('<text x="16" y="388" font-size="14" fill="currentColor">'
                  'Rendimiento</text>')
    limite_eta = 100.0
    for i in range(5):
        val = i * 25
        x = origen + ancho * val / limite_eta
        cuerpo.append(f'<line x1="{x:.3f}" y1="349" x2="{x:.3f}" y2="415" '
                      'stroke="#e2e8f0" stroke-dasharray="2 4"/>')
        cuerpo.append(f'<text x="{x:.3f}" y="440" text-anchor="middle" '
                      f'font-size="12" fill="currentColor">{val}</text>')
    cuerpo.append(barra(100 * ideal["rendimiento"], 366, AZUL, "rendimiento",
                       "ideal", escala=limite_eta))
    cuerpo.append(barra(100 * configurado["rendimiento"], 388, NARANJA, "rendimiento",
                       "configurado", escala=limite_eta))
    cuerpo.append('<text x="439" y="470" text-anchor="middle" font-size="14" '
                  'fill="currentColor">Rendimiento térmico [%]</text></svg>')
    return "".join(cuerpo)


def graficas_resultados(ciclo, estados, entradas):
    """Seis tarjetas y diagnóstico; una resolución adicional para el ideal cp(T).

    Parámetros: dict científico 2B, cuatro dict de propiedades y siete entradas.
    Retorno: (lista de tuplas título/SVG o None/explicación, diagnóstico comparativo).
    """
    cp_svg, gamma_svg = svg_propiedades(estados)
    diagnostico = ""
    try:
        ideal = resolver_ciclo(entradas["T1"], entradas["T3"], entradas["rp"],
                              entradas["p1"], 1.0, 1.0, 0.0)
    except (ValueError, EstadoFueraDeRango, ErrorNumericoCiclo) as exc:
        ideal = None
        diagnostico = f"El caso ideal cp(T) no se puede resolver: {exc}"
    if ideal is not None:
        motivos = []
        if not ideal["viable"]:
            motivos.append("El caso ideal de componentes es calculable, no motor.")
        if not ciclo["viable"]:
            motivos.append("El caso configurado es calculable, no motor.")
        if motivos:
            diagnostico = (" ".join(motivos) +
                           " No se comparan trabajos ni rendimientos como prestaciones operativas.")
    comparacion = (svg_comparacion(ideal, ciclo)
                   if ideal is not None and ideal["viable"] and ciclo["viable"] else None)
    resultado = [
        ("Diagrama T–s del ciclo", svg_ts(ciclo),
         "Esquemático: estados cp(T) exactos; líneas discontinuas de guía, no trayectorias integradas."),
        ("Diagrama P–v específico", svg_pv(ciclo),
         "v=R·T/p con presión absoluta; volumen específico, no volumen geométrico de un motor. Las uniones son esquemáticas."),
        ("Calor específico cp(T)", cp_svg,
         "Curva del aire seco ideal entre 200 y 2000 K; los círculos numerados sitúan los cuatro estados."),
        ("Relación de calores γ(T)", gamma_svg,
         "γ es adimensional y varía con T; no se sustituye por una constante en las ecuaciones del ciclo."),
        ("Balance energético específico", svg_balances(ciclo),
         "Magnitudes tal como las devuelve 2B [kJ/kg]: wnet=wt−wc=qin−qout. Sin caudal no hay potencia; solo se grafican prestaciones motoras."),
        ("Componentes ideales frente a caso configurado", comparacion,
         "Ambos cálculos usan cp(T). Panel superior: trabajos [kJ/kg]; inferior: rendimiento [%]. Ideal: ηc=ηt=1, δ=0."),
    ]
    return resultado, diagnostico


def graficas_optimizacion(curva, estudio):
    """Tres SVG de un mismo muestreo de rp, con A/B solo si son interiores."""
    validos = [p for p in curva if p is not None and p["rendimiento"] is not None]
    if not estudio.get("dominio_motor") or len(validos) < 2:
        return ()
    rango = estudio["dominio_motor"]
    graficas = []
    for clave, letra, titulo, eje, color, factor in (
        ("trabajo", "A", "Trabajo neto frente a rp", "Trabajo neto [kJ/kg]", AZUL, 1),
        ("rendimiento", "B", "Rendimiento térmico frente a rp", "Rendimiento [%]", NARANJA, 100),
    ):
        extremo = estudio.get(letra)
        marcas = ([extremo] if extremo and extremo["tipo"] == "maximo_interior" else [])
        xs_ys = [p[clave] * factor for p in validos] + [
            e["trabajo_neto" if clave == "trabajo" else "rendimiento"] * factor for e in marcas
        ]
        cuerpo, posicion = _marco(
            titulo, "Relación de compresión rp [–] · escala logarítmica",
            eje, rango, _margen(xs_ys), log_x=True,
        )
        secuencia = [(p["rp"], p[clave] * factor) if p is not None and p[clave] is not None
                     else None for p in curva]
        cuerpo += _tramos(secuencia, posicion, color=color)
        for e in marcas:
            dato = e["trabajo_neto" if clave == "trabajo" else "rendimiento"] * factor
            cuerpo += _estado(letra, e["rp"], dato, posicion, color=VERDE,
                              etiqueta=f"Máximo interior {letra}: rp={e['rp']:.8g}, Y={dato:.8g}")
        graficas.append((titulo, cuerpo + "</svg>",
                         "Cada muestra representa un ciclo motor cp(T). La escala de rp es logarítmica; "
                         f"solo el máximo interior {letra}, si existe, se señala como punto alcanzado."))

    tradeoff = [(p["trabajo"], 100 * p["rendimiento"]) if p is not None and
                p["rendimiento"] is not None else None for p in curva]
    ambos = [p for p in tradeoff if p is not None]
    puntos_optimos = [estudio[k] for k in ("A", "B")
                     if estudio.get(k) and estudio[k]["tipo"] == "maximo_interior"]
    xs = [x for x, _ in ambos] + [e["trabajo_neto"] for e in puntos_optimos]
    ys = [y for _, y in ambos] + [100 * e["rendimiento"] for e in puntos_optimos]
    cuerpo, posicion = _marco(
        "Compromiso entre trabajo específico y rendimiento",
        "Trabajo neto [kJ/kg]", "Rendimiento térmico [%]",
        _margen(xs), _margen(ys),
    )
    cuerpo += _tramos(tradeoff, posicion, color=GRIS)
    for letra in ("A", "B"):
        e = estudio.get(letra)
        if e and e["tipo"] == "maximo_interior":
            cuerpo += _estado(letra, e["trabajo_neto"], 100 * e["rendimiento"],
                              posicion, color=AZUL if letra == "A" else NARANJA,
                              etiqueta=f"Máximo interior {letra}: rp={e['rp']:.8g}")
    graficas.append(("Compromiso trabajo–rendimiento", cuerpo + "</svg>",
                     "Cada punto es una rp motora admisible; A prioriza trabajo y B rendimiento. "
                     "La curva completa no tiene por qué ser frontera de Pareto."))
    return tuple(graficas)
