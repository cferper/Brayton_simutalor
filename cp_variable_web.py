"""Capa web aislada para el aire con cp(T); no implementa ecuaciones térmicas.

Se registra en web_app.py mediante app.register_blueprint(cp_variable_bp).
No persiste informes ni altera el historial del modelo constante.
"""
from math import exp, isfinite, log
from numbers import Real

from flask import Blueprint, render_template, request

from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo, resolver_ciclo
from optimizacion_cp_variable import estudiar_cp_variable
from propiedades_aire import cp, gamma

cp_variable_bp = Blueprint('cp_variable', __name__)

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


@cp_variable_bp.route('/modelo-cp-variable', methods=['GET','POST'])
def modelo_cp_variable():
    """Página separada; GET no ejecuta cálculos. POST simula y optimiza."""
    valores={k:str(v) for k,v in DEFAULTS.items()}
    ciclo=None; optimizacion=None; estados=[]; ts=None; grafica=None; error=None
    if request.method=='POST':
        valores={key:request.form.get(key,'') for key in DEFAULTS}
        try:
            p=leer_entradas(request.form)
            ciclo=resolver_ciclo(**p)
            estados=propiedades_estados(ciclo)
            ts=svg_ts(ciclo)
            optimizacion=estudiar_cp_variable(p['T1'],p['T3'],p['p1'],
                                                p['eta_c'],p['eta_t'],p['delta'])
            grafica=svg_optimizacion(curvas_optimizacion(p,optimizacion),optimizacion)
        except EstadoFueraDeRango as exc:
            error='Estado fuera de 200–2000 K: '+str(exc)
        except ErrorNumericoCiclo:
            error='No se ha podido completar la operación numérica. Revisa los parámetros.'
        except ValueError as exc:
            error='Entrada no válida: '+str(exc)
        except ArithmeticError:
            error='No ha convergido el cálculo numérico.'
    return render_template('cp_variable.html',campos=FIELDS,valores=valores,
                           ciclo=ciclo,optimizacion=optimizacion,estados=estados,
                           ts=ts,grafica=grafica,error=error), (400 if error else 200)
