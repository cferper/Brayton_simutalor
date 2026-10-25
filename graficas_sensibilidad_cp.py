"""Dos diagramas OFAT para el dashboard; usan únicamente muestras de Fase 2E.

Las curvas excluyen los puntos no motores; None corta el trazado. Ninguna
función de este módulo resuelve estados ni aproxima derivadas.
"""
from html import escape
from math import isfinite


def _svg_dos_series(filas, etiqueta_x, unidad_x, claves, etiqueta_y, unidad_y,
                    x_ref=None):
    """Dibuja dos series de puntos motores, con huecos explícitos.

    filas: secuencia de dicts {x, operativas}; operativas es dict o None.
    claves: dos nombres de magnitud del diccionario; los valores son
    cantidades ya calculadas en unidad_y. Retorna SVG o None.
    """
    puntos = [f for f in filas if f['operativas'] is not None]
    if not puntos:
        return None
    ys = [f['operativas'][key] for f in puntos for key in claves]
    if not all(isfinite(v) for v in ys):
        return None
    xmin, xmax = min(f['x'] for f in filas), max(f['x'] for f in filas)
    if xmax <= xmin:
        return None
    ymin, ymax = min(ys), max(ys)
    margen = max((ymax-ymin)*.07, max(abs(ymin), abs(ymax), 1)*.02)
    ymin -= margen
    ymax += margen

    def cx(x):
        return 76 + 555*(x-xmin)/(xmax-xmin)

    def cy(y):
        return 294 - 240*(y-ymin)/(ymax-ymin)

    colores = ('#2563eb', '#c2410c')
    trazos = []
    for key, color in zip(claves, colores):
        segmento = []

        def emitir():
            if len(segmento) >= 2:
                trazos.append('<polyline fill="none" stroke="' + color +
                              '" stroke-width="2.5" points="' +
                              ' '.join(f'{cx(x):.2f},{cy(y):.2f}' for x,y in segmento) + '"/>')
            segmento.clear()

        for fila in list(filas) + [{'operativas': None}]:
            if fila['operativas'] is None:
                emitir()
                continue
            x, y = fila['x'], fila['operativas'][key]
            segmento.append((x,y))
            trazos.append(
                f'<circle data-serie="{escape(key)}" data-x="{x:.12g}" '
                f'data-valor="{y:.12g}" cx="{cx(x):.2f}" cy="{cy(y):.2f}" '
                f'r="2.4" fill="{color}"><title>'
                f'{escape(key)}: x={x:.6g} {escape(unidad_x)}; '
                f'y={y:.6g} {escape(unidad_y)}</title></circle>')

    etiquetas_x = ''.join(
        f'<text x="{cx(x):.2f}" y="317" font-size="12" text-anchor="middle" '
        f'fill="currentColor">{x:.4g}</text>'
        for x in (xmin,(xmin+xmax)/2,xmax))
    etiquetas_y = ''.join(
        f'<text x="69" y="{cy(y)+4:.2f}" font-size="12" text-anchor="end" '
        f'fill="currentColor">{y:.4g}</text>'
        for y in (ymin,(ymin+ymax)/2,ymax))
    referencia = ''
    if x_ref is not None and xmin <= x_ref <= xmax:
        referencia = (
            f'<line data-referencia="{x_ref:.12g}" x1="{cx(x_ref):.2f}" '
            f'x2="{cx(x_ref):.2f}" y1="50" y2="300" stroke="#64748b" '
            f'stroke-width="1.5" stroke-dasharray="4 5"/>')
    leyenda = ' · '.join(claves)
    return (
        f'<svg viewBox="0 0 670 386" role="img" '
        f'aria-label="{escape(etiqueta_y)} en función de {escape(etiqueta_x)}">'
        '<line x1="76" x2="632" y1="300" y2="300" stroke="currentColor"/>'
        '<line x1="76" x2="76" y1="50" y2="300" stroke="currentColor"/>'
        f'{referencia}{etiquetas_x}{etiquetas_y}{"".join(trazos)}'
        f'<text x="345" y="346" text-anchor="middle" fill="currentColor">'
        f'{escape(etiqueta_x)} [{escape(unidad_x)}]</text>'
        f'<text x="80" y="23" fill="currentColor">{escape(etiqueta_y)} '
        f'[{escape(unidad_y)}]</text>'
        f'<text x="345" y="377" font-size="12" text-anchor="middle" '
        f'fill="currentColor">{escape(leyenda)} · huecos: puntos excluidos</text>'
        '</svg>')


def svg_variaciones_relativas(estudio):
    """Retorna (svg, diagnóstico) para Δx, ΔW y Δη porcentuales finitos.

    La referencia debe ser motora y x0, W0, η0 no nulos. Las variaciones
    finitas no se interpretan como derivadas o sensibilidades locales.
    """
    x0 = estudio['referencia_x']
    base = estudio['referencia']
    if x0 == 0:
        return None, 'Variación relativa no definida: el parámetro de referencia es cero.'
    if base['estado'] != 'motor':
        return None, 'Variación relativa no disponible: el ciclo de referencia no es motor.'
    w0 = base['ciclo']['trabajo_neto']
    eta0 = base['ciclo']['rendimiento']
    if (not all(isfinite(v) for v in (x0,w0,eta0))
            or abs(w0) < 1e-12 or abs(eta0) < 1e-12):
        return None, 'Variación relativa no definida: una prestación de referencia es nula.'
    filas = []
    for fila in estudio['filas']:
        valores = fila['operativas']
        filas.append({
            'x': 100*(fila['x']-x0)/x0,
            'operativas': ({
                'ΔW/W0': 100*(valores['trabajo_neto']-w0)/w0,
                'Δη/η0': 100*(valores['rendimiento']-eta0)/eta0,
            } if valores is not None else None),
        })
    svg = _svg_dos_series(filas, 'Variación relativa del parámetro', '%',
                         ('ΔW/W0', 'Δη/η0'), 'Variación finita de prestaciones',
                         '%', 0)
    return svg, ('' if svg is not None else
                 'No hay suficientes puntos motores para comparar variaciones relativas.')


def svg_temperaturas_caracteristicas(estudio):
    """T2 y T4 [K] en muestras motoras, con estados ya calculados por 2B."""
    return _svg_dos_series(estudio['filas'], estudio['parametro'],
                           estudio['unidad'], ('T2','T4'),
                           'Temperaturas de salida de las máquinas', 'K',
                           estudio['referencia_x'])
