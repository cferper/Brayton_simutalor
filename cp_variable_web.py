"""Presentadores y preparación de resultados cp(T) para el dashboard principal.

No implementa ecuaciones térmicas ni altera los módulos científicos.
"""
from math import exp, isfinite, log
from html import escape

from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo, resolver_ciclo
from optimizacion_cp_variable import estudiar_cp_variable
from propiedades_aire import cp, gamma
from sensibilidad_cp_variable import PARAMETROS_CP, barrido_cp_variable

DEFAULTS = {'T1': 288.15, 'T3': 1600.0, 'rp': 10.0, 'p1': 100.0,
            'eta_c': .85, 'eta_t': .90, 'delta': .05}
FIELDS = (
    ('T1', 'Entrada compresor', 'K'), ('T3', 'Entrada turbina', 'K'),
    ('rp', 'Relación de compresión', '—'), ('p1', 'Presión de entrada', 'kPa'),
    ('eta_c', 'Eficiencia compresor', 'fracción'),
    ('eta_t', 'Eficiencia turbina', 'fracción'),
    ('delta', 'Pérdida de presión', 'fracción'),
)


def leer_entradas(form):
    """Convierte los siete escalares, sin coerción de NaN o infinito.

    La validación de dominios físicos continúa en el solucionador de 2B.
    """
    values = {}
    for key, _, _ in FIELDS:
        raw = form.get(key, '').strip()
        try:
            number = float(raw)
        except (ValueError, TypeError):
            raise ValueError(f'{key}: introduce un número.') from None
        if not isfinite(number):
            raise ValueError(f'{key}: el valor debe ser finito.')
        values[key] = number
    return values


def propiedades_estados(p):
    """Tabla con propiedades reales en cuatro estados; depende sólo de 2A/2B."""
    return [dict(numero=i+1, T=T, presion=presion,
                 cp=cp(T), gamma=gamma(T), h=h, s=s)
            for i, (T, presion, h, s) in enumerate(zip(
                p['temperaturas'], p['presiones'], p['entalpias'], p['entropias']))]


def _escala(valor, low, high, inicio, ancho):
    return inicio + ancho*(valor-low)/max(high-low, 1e-12)


def svg_ts(p):
    """SVG esquemático: sólo los estados se consideran termodinámicamente exactos."""
    estados=list(zip(p['entropias'], p['temperaturas']))
    ss=[v[0] for v in estados]; ts=[v[1] for v in estados]
    smin,smax=min(ss),max(ss); tmin,tmax=min(ts),max(ts)
    puntos=[(_escala(s,smin,smax,60,560),
             _escala(t,tmin,tmax,320,-275)) for s,t in estados]
    coords=' '.join(f'{x:.2f},{y:.2f}' for x,y in puntos+[puntos[0]])
    circles=''.join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5" fill="#2563eb"/>'
                    f'<text x="{x+9:.2f}" y="{y-8:.2f}" font-size="15" fill="currentColor">{i}</text>'
                    for i,(x,y) in enumerate(puntos,1))
    return (f'<svg viewBox="0 0 680 390" role="img" aria-label="Estados del ciclo en diagrama temperatura-entropía">'
            f'<line x1="60" y1="340" x2="640" y2="340" stroke="currentColor"/>'
            f'<line x1="60" y1="340" x2="60" y2="20" stroke="currentColor"/>'
            f'<text x="310" y="374" fill="currentColor">s [kJ/(kg K)]</text>'
            f'<text x="12" y="25" fill="currentColor">T [K]</text>'
            f'<polyline points="{coords}" fill="none" stroke="#64748b" stroke-dasharray="7 5" stroke-width="2"/>'
            f'{circles}</svg>')


def curvas_optimizacion(entradas, estudio, muestras=90):
    """Muestreo interior en escala log(rp), sin fabricar datos inválidos."""
    intervalo=estudio.get('dominio_motor')
    if not intervalo:
        return []
    lo,hi=map(log,intervalo)
    valores=[]
    for i in range(1,muestras+1):
        x=lo+(hi-lo)*i/(muestras+1)
        rp=exp(x)
        try:
            p=resolver_ciclo(entradas['T1'],entradas['T3'],rp,entradas['p1'],
                             entradas['eta_c'],entradas['eta_t'],entradas['delta'])
        except (EstadoFueraDeRango, ErrorNumericoCiclo):
            valores.append(None)
            continue
        valores.append({'rp':rp,'trabajo':p['trabajo_neto'],
                        'rendimiento':p['rendimiento'] if p['viable'] else None} if p['viable'] else None)
    return valores


def svg_optimizacion(curva, estudio):
    """Gráfico de puntos evaluados; cortes entre tramos no calculables."""
    puntos=[p for p in curva if p is not None]
    if len(puntos)<2:
        return None
    xmin,xmax=min(log(p['rp']) for p in puntos),max(log(p['rp']) for p in puntos)
    segments=[]
    for key, color, offset in [('trabajo','#2563eb',0),('rendimiento','#c2410c',0)]:
        values=[p[key] for p in puntos if p[key] is not None]
        if not values:continue
        ymin,ymax=min(values),max(values)
        path=[]
        for p in curva:
            if p is None or p[key] is None:
                if path:segments.append((color,path));path=[]
                continue
            x=_escala(log(p['rp']),xmin,xmax,70,540)
            y=_escala(p[key],ymin,ymax,295,-245)
            path.append((x,y))
        if path:segments.append((color,path))
    paths=''.join(f'<polyline points="{" ".join(f"{x:.2f},{y:.2f}" for x,y in path)}" '
                  f'fill="none" stroke="{color}" stroke-width="2.5"/>' for color,path in segments)
    return (f'<svg viewBox="0 0 650 350" role="img" aria-label="Trabajo y rendimiento normalizados en dos escalas independientes frente a rp">'
            f'<line x1="70" y1="300" x2="620" y2="300" stroke="currentColor"/>'
            f'<text x="275" y="338" fill="currentColor">ln(rp)</text>'
            f'{paths}</svg>')


def preparar_resultados(entradas):
    """Reúne estados, propiedades, curvas y óptimos ya resueltos por 2B/2C.

    `entradas` es el diccionario validado de siete escalares; el resultado
    se usa para presentar el caso sin mezclarlo con el modelo histórico.
    Propaga los errores físicos y numéricos al controlador Flask.
    """
    ciclo = resolver_ciclo(**entradas)
    estudio = estudiar_cp_variable(entradas['T1'], entradas['T3'], entradas['p1'],
                                  entradas['eta_c'], entradas['eta_t'], entradas['delta'])
    return {
        'ciclo': ciclo,
        'estados': propiedades_estados(ciclo),
        'ts': svg_ts(ciclo),
        'optimizacion': estudio,
        'grafica': svg_optimizacion(curvas_optimizacion(entradas, estudio), estudio),
    }


def svg_sensibilidad(barrido, claves, etiqueta, unidad_y):
    """Representa exclusivamente filas motoras; cada hueco corta el trazado.

    No interpola máximos, no cruza regiones no motoras y señala dónde está
    el caso base aun si no coincide con un punto de la malla OFAT.
    """
    colores = ('#2563eb', '#c2410c')
    puntos = [p for p in barrido['filas'] if p['operativas'] is not None]
    valores = [p['operativas'][clave]*(100 if clave == 'rendimiento' else 1)
               for p in puntos for clave in claves]
    if not valores:
        return None
    ymin, ymax = min(valores), max(valores)
    holgura = max((ymax-ymin)*.09, max(abs(ymin),abs(ymax),1)*.015)
    ymin -= holgura
    ymax += holgura
    xmin, xmax = barrido['minimo'], barrido['maximo']
    x_coord = lambda x: _escala(x,xmin,xmax,76,555)
    y_coord = lambda y: _escala(y,ymin,ymax,295,-245)

    trazos=[]
    for clave,color in zip(claves,colores):
        tramo=[]
        for punto in barrido['filas']+[{'operativas':None}]:
            if punto['operativas'] is None:
                if len(tramo)>1:
                    coords=' '.join(f'{x:.2f},{y:.2f}' for x,y in tramo)
                    trazos.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2.5"/>')
                elif tramo:
                    x,y=tramo[0]
                    trazos.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.5" fill="{color}"/>')
                tramo=[]
                continue
            y=punto['operativas'][clave]*(100 if clave == 'rendimiento' else 1)
            tramo.append((x_coord(punto['x']),y_coord(y)))

    referencia=barrido['referencia_x']
    vertical = ''
    if xmin <= referencia <= xmax:
        x = x_coord(referencia)
        vertical=(f'<line x1="{x:.2f}" x2="{x:.2f}" y1="48" y2="300" '
                  f'stroke="#64748b" stroke-width="1.5" stroke-dasharray="4 5"/>'
                  f'<text x="{x:.2f}" y="39" font-size="12" text-anchor="middle" fill="currentColor">Referencia</text>')
    eje=escape(f"{barrido['parametro']} [{barrido['unidad']}]")
    etiquetas=''.join(
        f'<text x="{x_coord(x):.2f}" y="324" font-size="12" text-anchor="middle" fill="currentColor">{x:.4g}</text>'
        for x in (xmin,(xmin+xmax)/2,xmax))
    ylabels=''.join(
        f'<text x="67" y="{y_coord(y)+4:.2f}" font-size="12" text-anchor="end" fill="currentColor">{y:.4g}</text>'
        for y in (ymin,(ymin+ymax)/2,ymax))
    leyenda=' · '.join(clave.replace('_',' ') for clave in claves)
    return (f'<svg viewBox="0 0 670 385" role="img" aria-label="{escape(etiqueta)} en función de {eje}; '
            'los tramos ausentes no representan ciclos motores">'
            '<line x1="76" x2="632" y1="300" y2="300" stroke="currentColor"/>'
            '<line x1="76" x2="76" y1="47" y2="300" stroke="currentColor"/>'
            f'{vertical}{"".join(trazos)}{etiquetas}{ylabels}'
            f'<text x="345" y="349" text-anchor="middle" fill="currentColor">{eje}</text>'
            f'<text x="80" y="18" fill="currentColor">{escape(etiqueta)} [{escape(unidad_y)}]</text>'
            f'<text x="345" y="376" font-size="12" text-anchor="middle" fill="currentColor">{escape(leyenda)} · huecos = no motor / sin datos</text>'
            '</svg>')


def preparar_sensibilidad(entradas, parametro, minimo, maximo, muestras):
    """Presenter de la Fase 2E: OFAT y dos (o tres) gráficas independientes."""
    estudio = barrido_cp_variable(entradas,parametro,minimo,maximo,muestras)
    estudio['graficas'] = (
        ('Trabajo neto',svg_sensibilidad(estudio,('trabajo_neto',),'Trabajo neto','kJ/kg')),
        ('Rendimiento térmico',svg_sensibilidad(estudio,('rendimiento',),'Rendimiento térmico','%')),
        ('Compresor y turbina',svg_sensibilidad(estudio,('trabajo_compresor','trabajo_turbina'),
                                              'Trabajo de compresor y turbina','kJ/kg')),
    )
    estudio['etiqueta']=PARAMETROS_CP[parametro]['etiqueta']
    return estudio
