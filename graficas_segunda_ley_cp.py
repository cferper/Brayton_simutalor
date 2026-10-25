"""Representaciones auxiliares de segunda ley a partir de estados cp(T) resueltos.

Solo dibuja datos entregados por Fases 2B/2G: sin termodinámica adicional.
Los signos se conservan, incluidos los de posibles incrementos de exergía.
"""
from html import escape
from math import isfinite


def _svg_barras_signo(datos, titulo, unidad, nota):
    """Barras horizontales firmadas a partir de (etiqueta, valor, color).

    Devuelve SVG o None si faltan datos numéricos válidos. Cero no es una
    barra positiva inventada; barras negativas crecen a la izquierda del 0.
    """
    if not datos or not all(isfinite(valor) for _,valor,_ in datos):
        return None
    escala = max(1.0, *(abs(valor) for _,valor,_ in datos))
    alto = 110 + 53*len(datos)
    origen, max_ancho = 355, 238
    barras=[]
    for i, (nombre, valor, color) in enumerate(datos):
        y=70+i*53
        ancho=abs(valor)/escala*max_ancho
        x=origen if valor>=0 else origen-ancho
        barras.append(
            f'<text x="15" y="{y+16}" font-size="13" '
            f'fill="currentColor">{escape(nombre)}</text>'
            f'<rect data-rol="{escape(nombre)}" data-valor="{valor:.12g}" '
            f'x="{x:.2f}" y="{y}" width="{ancho:.2f}" height="25" '
            f'fill="{color}" rx="2"><title>{escape(nombre)}: '
            f'{valor:.9g} {escape(unidad)}</title></rect>'
            f'<text x="617" y="{y+18}" font-size="13" '
            f'fill="currentColor">{valor:.6g}</text>')
    return (f'<svg viewBox="0 0 750 {alto}" role="img" '
            f'aria-label="{escape(titulo)} [{escape(unidad)}]">'
            f'<text x="16" y="22" font-size="16" font-weight="600" '
            f'fill="currentColor">{escape(titulo)} [{escape(unidad)}]</text>'
            f'<text x="16" y="44" font-size="12" '
            f'fill="currentColor">{escape(nota)}</text>'
            f'<line x1="{origen}" x2="{origen}" y1="57" y2="{alto-25}" '
            f'stroke="currentColor" stroke-width="1.5"/>'
            f'{"".join(barras)}</svg>')


def svg_exergias_estados(estudio):
    """Exergías físicas e1..e4 [kJ/kg]; referencia ambiental T0, p0.

    Los valores se representan con signo. No se atribuye exergía química.
    """
    if estudio['estado']=='inconsistente':
        return None
    datos=[(f'Estado {i+1}', e, '#2563eb') for i,e in enumerate(estudio['exergias'])]
    return _svg_barras_signo(
        datos,'Exergía física de los cuatro estados','kJ/kg',
        f"T0={estudio['T0']:.3f} K; p0={estudio['p0']:.3f} kPa · solo exergía física")


def svg_generacion_entropia(estudio):
    """Generación [kJ/(kg·K)] solo si no hay inconsistencia científica."""
    if estudio['estado']=='inconsistente' or any(s<0 for s in estudio['generacion']):
        return None
    return _svg_barras_signo(
        [('Compresor',estudio['generacion'][0],'#2563eb'),
         ('Turbina',estudio['generacion'][1],'#c2410c')],
        'Generación de entropía de las turbomáquinas','kJ/(kg·K)',
        'Entropía generada en compresor y turbina adiabáticos; no es Δs del ciclo entero')


def svg_balances_exergia(ciclo, estudio):
    """Dos balances adiabáticos con contribuciones firmadas y residuos.

    Compresor: wc=(e2-e1)+ed,c; turbina: (e3-e4)=wt+ed,t.
    Usa trabajos existentes de 2B y exergías/destrucciones existentes de 2G.
    """
    if estudio['estado']=='inconsistente':
        return None
    e1,e2,e3,e4=estudio['exergias']
    wc,wt=ciclo['trabajo_compresor'],ciclo['trabajo_turbina']
    edc,edt=estudio['destruccion']
    datos=[
        ('Compresor · wc',wc,'#1d4ed8'),
        ('Compresor · e2−e1',e2-e1,'#0d9488'),
        ('Compresor · eD,c',edc,'#c2410c'),
        ('Turbina · e3−e4',e3-e4,'#0d9488'),
        ('Turbina · wt',wt,'#1d4ed8'),
        ('Turbina · eD,t',edt,'#c2410c'),
    ]
    base=_svg_barras_signo(
        datos,'Balances exergéticos de compresor y turbina','kJ/kg',
        'Cada barra conserva su signo; la destrucción es solo de ambas turbomáquinas')
    if base is None:
        return None
    rc,rt=estudio['residuos_balances']
    # Los residuos cuantifican acuerdo de balances, no se ocultan en redondeos.
    aviso=(f'<text x="15" y="58" font-size="11" fill="currentColor">'
           f'R compresor={rc:.3e} kJ/kg; R turbina={rt:.3e} kJ/kg</text>')
    return base.replace('<svg ',f'<svg data-residuo-c="{rc:.12g}" data-residuo-t="{rt:.12g}" ',1
                        ).replace('</svg>',aviso+'</svg>')
