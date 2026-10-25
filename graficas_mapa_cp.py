"""Mapa categórico y cortes de una malla rp-T3 ya resuelta con cp(T).

El módulo recibe los diccionarios de la Fase 2F y jamás evalúa ciclos.
Los cortes son filas reales: no existe interpolación termodinámica.
"""
from html import escape
from math import log


COLORES_ESTADO = {
    'motor': '#15803d',
    'no_motor': '#94a3b8',
    'fuera_rango': '#7c3aed',
    'entrada_invalida': '#f59e0b',
    'error_numerico': '#dc2626',
}
ETIQUETAS_ESTADO = {
    'motor': 'Motor',
    'no_motor': 'No motor',
    'fuera_rango': 'Fuera de rango',
    'entrada_invalida': 'Entrada inválida',
    'error_numerico': 'Error numérico',
}


def svg_mapa_viabilidad(estudio):
    """SVG categórico de todas las celdas, incluso si no hay ciclo motor.

    Cada rectángulo lleva data-estado, data-rp y data-T3 para trazar su
    origen exacto; los colores representan categorías, no valores.
    """
    n_rp, n_t = estudio['n_rp'], estudio['n_T3']
    left, top, ancho, alto = 85, 53, 558, 340
    dx, dy = ancho/n_rp, alto/n_t
    celdas = []
    for j, fila in enumerate(estudio['filas']):
        for i, celda in enumerate(fila):
            estado = celda['estado']
            if estado not in COLORES_ESTADO:
                raise ValueError(f'Estado desconocido en la malla: {estado}')
            x, y = left+i*dx, top+(n_t-1-j)*dy
            aviso = (f"rp={celda['rp']:.6g}; T3={celda['T3']:.6g} K; "
                     f"{ETIQUETAS_ESTADO[estado]}; {celda['motivo']}")
            celdas.append(
                f'<rect data-estado="{estado}" data-rp="{celda["rp"]:.12g}" '
                f'data-T3="{celda["T3"]:.12g}" x="{x:.2f}" y="{y:.2f}" '
                f'width="{dx+.03:.2f}" height="{dy+.03:.2f}" '
                f'fill="{COLORES_ESTADO[estado]}"><title>'
                f'{escape(aviso)}</title></rect>')
    xticks = ''.join(
        f'<text x="{left+(i+.5)*dx:.2f}" y="415" fill="currentColor" '
        f'font-size="12" text-anchor="middle">{estudio["rps"][i]:.4g}</text>'
        for i in sorted({0,(n_rp-1)//2,n_rp-1}))
    yticks = ''.join(
        f'<text x="75" y="{top+(n_t-.5-j)*dy+4:.2f}" '
        f'fill="currentColor" text-anchor="end" font-size="12">'
        f'{estudio["T3s"][j]:.4g}</text>'
        for j in sorted({0,(n_t-1)//2,n_t-1}))
    leyenda = ''.join(
        f'<rect x="{15+i*143}" y="463" width="13" height="13" '
        f'fill="{COLORES_ESTADO[key]}"/>'
        f'<text x="{32+i*143}" y="474" font-size="11" fill="currentColor">'
        f'{ETIQUETAS_ESTADO[key]}</text>'
        for i,key in enumerate(COLORES_ESTADO))
    return ('<svg viewBox="0 0 750 498" role="img" '
            'aria-label="Mapa categórico de viabilidad del ciclo cp(T)">'
            '<text x="85" y="25" fill="currentColor" font-weight="600">'
            'Viabilidad calculada de cada celda rp–T3</text>'
            '<text x="85" y="42" font-size="12" fill="currentColor">'
            'Categorías discretas, sin interpolar fronteras</text>'
            + ''.join(celdas) + xticks + yticks +
            '<text x="370" y="443" text-anchor="middle" fill="currentColor">'
            'rp [−] (escala logarítmica)</text>'
            '<text x="11" y="51" fill="currentColor">T3 [K]</text>'
            + leyenda + '</svg>')


def svg_cortes_mapa(estudio, magnitud):
    """Traza tres filas T3 reales; retorna SVG o None si no hay muestras motoras.

    magnitud: trabajo_neto [kJ/kg] o rendimiento [fracción interna],
    convertido a porcentaje únicamente al dibujar. Mantiene discontinuidades
    mediante operativas=None; no interpola puntos ni busca óptimos continuos.
    """
    if magnitud not in ('trabajo_neto','rendimiento'):
        raise ValueError('Magnitud de corte no reconocida.')
    indices = sorted({0,(estudio['n_T3']-1)//2,estudio['n_T3']-1})
    colores = ('#2563eb','#c2410c','#15803d')
    factor = 100 if magnitud == 'rendimiento' else 1
    unidades = '%' if factor == 100 else 'kJ/kg'
    etiqueta = 'Rendimiento térmico' if factor == 100 else 'Trabajo neto'
    valores = [c['operativas'][magnitud]*factor for j in indices
               for c in estudio['filas'][j] if c['operativas'] is not None]
    if not valores:
        return None
    y_min, y_max = min(valores), max(valores)
    margen = max((y_max-y_min)*.08, max(abs(y_min),abs(y_max),1)*.02)
    y_min -= margen
    y_max += margen
    x_min, x_max = log(estudio['rps'][0]), log(estudio['rps'][-1])

    def cx(rp):
        return 77 + 550*(log(rp)-x_min)/(x_max-x_min)

    def cy(y):
        return 302 - 244*(y-y_min)/(y_max-y_min)

    trazos=[]
    for j, color in zip(indices,colores):
        fila = estudio['filas'][j]
        segmento = []

        def cerrar():
            if len(segmento)>1:
                trazos.append(
                    f'<polyline stroke="{color}" stroke-width="2.4" '
                    f'fill="none" points="' +
                    ' '.join(f'{cx(x):.2f},{cy(y):.2f}' for x,y in segmento) + '"/>')
            segmento.clear()

        for celda in fila + [{'operativas':None}]:
            if celda['operativas'] is None:
                cerrar()
                continue
            y = celda['operativas'][magnitud]*factor
            x = celda['rp']
            segmento.append((x,y))
            trazos.append(
                f'<circle data-rp="{x:.12g}" data-T3="{celda["T3"]:.12g}" '
                f'data-valor="{y:.12g}" data-magnitud="{magnitud}" '
                f'cx="{cx(x):.2f}" cy="{cy(y):.2f}" r="2.3" fill="{color}">'
                f'<title>rp={x:.5g}; T3={celda["T3"]:.6g} K; '
                f'{etiqueta}={y:.6g} {unidades}</title></circle>')
    marcas_x=''.join(
        f'<text x="{cx(rp):.2f}" y="327" text-anchor="middle" '
        f'fill="currentColor" font-size="12">{rp:.4g}</text>'
        for rp in (estudio['rps'][0], estudio['rps'][(estudio['n_rp']-1)//2],
                   estudio['rps'][-1]))
    marcas_y=''.join(
        f'<text x="69" y="{cy(y)+4:.2f}" text-anchor="end" '
        f'font-size="12" fill="currentColor">{y:.4g}</text>'
        for y in (y_min,(y_min+y_max)/2,y_max))
    leyenda=''.join(
        f'<line x1="{75+i*185}" x2="{100+i*185}" y1="372" y2="372" '
        f'stroke="{color}" stroke-width="3"/>'
        f'<text x="{106+i*185}" y="376" font-size="12" fill="currentColor">'
        f'T3={estudio["T3s"][j]:.6g} K</text>'
        for i,(j,color) in enumerate(zip(indices,colores)))
    return (
        f'<svg viewBox="0 0 700 416" role="img" '
        f'aria-label="Cortes del mapa: {etiqueta} frente a rp, tres T3 de la malla">'
        '<line x1="77" x2="628" y1="306" y2="306" stroke="currentColor"/>'
        '<line x1="77" x2="77" y1="55" y2="306" stroke="currentColor"/>'
        f'<text x="80" y="26" fill="currentColor">{etiqueta} [{unidades}]</text>'
        f'{"".join(trazos)}{marcas_x}{marcas_y}{leyenda}'
        '<text x="355" y="351" text-anchor="middle" fill="currentColor">'
        'rp [−] (escala logarítmica)</text>'
        '<text x="355" y="406" text-anchor="middle" font-size="12" '
        'fill="currentColor">Cortes de filas calculadas · huecos = no motor/sin datos</text>'
        '</svg>')
