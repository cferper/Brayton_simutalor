"""Presentadores y preparación de resultados cp(T) para el dashboard principal.

No implementa ecuaciones térmicas ni altera los módulos científicos.
"""
from functools import lru_cache
from math import exp, isfinite, log
from html import escape

from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo, resolver_ciclo
from optimizacion_cp_variable import estudiar_cp_variable
from propiedades_aire import cp, gamma
from graficas_cp_variable import graficas_resultados, graficas_optimizacion
from sensibilidad_cp_variable import PARAMETROS_CP, barrido_cp_variable
from graficas_sensibilidad_cp import svg_variaciones_relativas, svg_temperaturas_caracteristicas
from mapa_diseno_cp_variable import calcular_mapa_cp_variable
from segunda_ley_cp_variable import analizar_segunda_ley_cp_variable

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


def preparar_resultados(entradas):
    """Reúne estados, propiedades, curvas y óptimos ya resueltos por 2B/2C.

    `entradas` es el diccionario validado de siete escalares; el resultado
    se usa para presentar el caso sin mezclarlo con el modelo histórico.
    Propaga los errores físicos y numéricos al controlador Flask.
    """
    ciclo = resolver_ciclo(**entradas)
    estudio = estudiar_cp_variable(entradas['T1'], entradas['T3'], entradas['p1'],
                                  entradas['eta_c'], entradas['eta_t'], entradas['delta'])
    estados = propiedades_estados(ciclo)
    graficas_r, diagnostico_comparacion = graficas_resultados(ciclo, estados, entradas)
    # El mismo barrido numérico alimenta las tres vistas de optimización.
    curva = curvas_optimizacion(entradas, estudio)
    return {
        'ciclo': ciclo,
        'estados': estados,
        'graficas_resultados': graficas_r,
        'diagnostico_comparacion': diagnostico_comparacion,
        'optimizacion': estudio,
        'graficas_optimizacion': graficas_optimizacion(curva, estudio),
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
    relativo, diagnostico = svg_variaciones_relativas(estudio)
    estudio['diagnostico_variaciones'] = diagnostico
    estudio['graficas'] += (
        ('Variaciones relativas', relativo),
        ('Temperaturas características', svg_temperaturas_caracteristicas(estudio)),
    )
    estudio['etiqueta']=PARAMETROS_CP[parametro]['etiqueta']
    return estudio


def _color_mapa(fraccion, rendimiento=False):
    """Interpolación de color para la presentación, sin interpretación física."""
    inferior, superior = ((254, 243, 199), (154, 52, 18)) if rendimiento else ((219, 234, 254), (29, 78, 216))
    return '#'+''.join(f'{round(a+(b-a)*max(0,min(1,fraccion))):02x}'
                     for a,b in zip(inferior, superior))


def svg_mapa_cp_variable(estudio, magnitud, opt=None):
    """SVG con celdas reales, máscaras discretas, barra de color y tooltips.

    Cada rectángulo corresponde a un ciclo evaluado. Los no motores nunca
    reciben color de prestación y ningún píxel es interpolado a través de ellos.
    """
    if magnitud not in ('trabajo_neto', 'rendimiento'):
        raise ValueError('Magnitud de mapa desconocida.')
    operativos = [c['operativas'][magnitud] for fila in estudio['filas']
                  for c in fila if c['operativas'] is not None]
    if not operativos:
        return None
    porcentaje = magnitud == 'rendimiento'
    lo, hi = min(operativos), max(operativos)
    escala = max(hi-lo, 1e-12)
    left, top, width, height = 86, 52, 540, 350
    cw, ch = width/estudio['n_rp'], height/estudio['n_T3']
    colores_estado = {'no_motor':'#e2e8f0', 'fuera_rango':'#94a3b8',
                      'entrada_invalida':'#f8fafc', 'error_numerico':'#fecaca'}
    nombres_estado = {'no_motor':'No motor', 'fuera_rango':'Fuera de 200–2000 K',
                      'entrada_invalida':'Entrada inadmisible', 'error_numerico':'Fallo numérico'}
    celdas=[]
    for j,fila in enumerate(estudio['filas']):
        for i,p in enumerate(fila):
            operativo=p['operativas']
            if operativo is None:
                color=colores_estado[p['estado']]
                tooltip=f"rp={p['rp']:.5g}; T3={p['T3']:.3f} K; {nombres_estado[p['estado']]}: {p['motivo']}"
            else:
                valor=operativo[magnitud]
                color=_color_mapa((valor-lo)/escala, porcentaje)
                tooltip=(f"rp={p['rp']:.5g}; T3={p['T3']:.3f} K; "
                         f"{'eta='+format(100*valor,'.3f')+' %' if porcentaje else 'wneto='+format(valor,'.3f')+' kJ/kg'}; "
                         f"wc={operativo['trabajo_compresor']:.3f}; wt={operativo['trabajo_turbina']:.3f} kJ/kg")
            x=left+i*cw
            y=top+(estudio['n_T3']-1-j)*ch
            celdas.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{cw+.03:.3f}" height="{ch+.03:.3f}" '
                          f'fill="{color}"><title>{escape(tooltip)}</title></rect>')

    # Ejes etiquetados con los valores físicos de los nodos, no con índices.
    marcas_x=[]
    for i in sorted({0,(estudio['n_rp']-1)//4,(estudio['n_rp']-1)//2,
                     3*(estudio['n_rp']-1)//4,estudio['n_rp']-1}):
        x=left+(i+.5)*cw
        marcas_x.append(f'<text x="{x:.2f}" y="423" fill="currentColor" font-size="12" text-anchor="middle">{estudio["rps"][i]:.3g}</text>')
    marcas_y=[]
    for j in sorted({0,(estudio['n_T3']-1)//2,estudio['n_T3']-1}):
        y=top+(estudio['n_T3']-.5-j)*ch
        marcas_y.append(f'<text x="77" y="{y+4:.2f}" fill="currentColor" font-size="12" text-anchor="end">{estudio["T3s"][j]:.0f}</text>')
    marcas_opt=[]
    if opt and estudio['T3_min'] <= estudio['referencia_T3'] <= estudio['T3_max']:
        for clave,color in (('A','#1e3a8a'),('B','#9a3412')):
            punto=opt.get(clave)
            if not punto or punto.get('tipo')!='maximo_interior' or punto['rp'] is None:
                continue
            rp=punto['rp']
            if not estudio['rp_min'] <= rp <= estudio['rp_max']:
                continue
            xx=left+cw/2+cw*(estudio['n_rp']-1)*(
                log(rp)-log(estudio['rp_min']))/(log(estudio['rp_max'])-log(estudio['rp_min']))
            yy=top+height-ch/2-ch*(estudio['n_T3']-1)*(
                estudio['referencia_T3']-estudio['T3_min'])/(estudio['T3_max']-estudio['T3_min'])
            marcas_opt.append(f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="6" fill="{color}" stroke="white" stroke-width="2">'
                              f'<title>{clave}: óptimo continuo 2C para T3={estudio["referencia_T3"]:.2f} K, rp={rp:.6f}</title></circle>'
                              f'<text x="{xx+9:.2f}" y="{yy-9:.2f}" font-size="13" font-weight="bold" fill="{color}" stroke="white" stroke-width="2" paint-order="stroke">{clave}</text>')
    unidades='%' if porcentaje else 'kJ/kg'
    etiqueta='Rendimiento térmico' if porcentaje else 'Trabajo neto'
    gradiente=''.join(f'<rect x="{190+i*31}" y="470" width="32" height="14" fill="{_color_mapa(i/7,porcentaje)}"/>' for i in range(8))
    leyenda=''.join(f'<rect x="{x}" y="510" width="12" height="12" fill="{color}"/>'
                    f'<text x="{x+17}" y="521" fill="currentColor" font-size="11">{texto}</text>'
                    for x,color,texto in ((18,'#e2e8f0','No motor'),(160,'#94a3b8','Fuera de rango'),
                                          (344,'#f8fafc','Entrada inválida'),(518,'#fecaca','Numérico')))
    return (f'<svg viewBox="0 0 720 542" role="img" aria-label="Mapa rp-T3 de {etiqueta} en {unidades}; '
            'gris indica zonas no motoras o no calculables">'
            f'<text x="86" y="24" fill="currentColor" font-weight="600" font-size="16">{etiqueta} [{unidades}]</text>'
            f'<text x="86" y="40" fill="currentColor" font-size="12">Cada celda: una evaluación cp(T). Pasa el cursor para consultar sus datos.</text>'
            f'{"".join(celdas)}{"".join(marcas_opt)}{"".join(marcas_x)}{"".join(marcas_y)}'
            '<text x="355" y="448" fill="currentColor" text-anchor="middle">rp [−] (escala logarítmica)</text>'
            '<text x="12" y="48" fill="currentColor">T3 [K]</text>'
            f'<text x="86" y="481" font-size="12" fill="currentColor">{lo*(100 if porcentaje else 1):.3g}</text>'
            f'{gradiente}<text x="449" y="481" font-size="12" fill="currentColor">{hi*(100 if porcentaje else 1):.3g} {unidades}</text>'
            f'{leyenda}<text x="360" y="538" text-anchor="middle" font-size="11" fill="currentColor">A/B: óptimos 2C solo a T3 de referencia · colores: mejores muestras de esta malla</text>'
            '</svg>')


def preparar_mapa(entradas, rp_min, rp_max, T3_min, T3_max, n_rp, n_T3):
    """Prepara dos mapas SVG y una sola optimización 2C de referencia, si procede."""
    estudio=calcular_mapa_cp_variable(entradas,rp_min,rp_max,T3_min,T3_max,n_rp,n_T3)
    opt=None
    if (estudio['conteos'].get('motor',0)>0 and T3_min<=entradas['T3']<=T3_max
            and 200<=entradas['T3']<=2000):
        try:
            opt=estudiar_cp_variable(entradas['T1'],entradas['T3'],entradas['p1'],
                                    entradas['eta_c'],entradas['eta_t'],entradas['delta'])
        except (ValueError,ArithmeticError):
            opt=None
    estudio['optimos_referencia']=opt
    estudio['svg_trabajo']=svg_mapa_cp_variable(estudio,'trabajo_neto',opt)
    estudio['svg_rendimiento']=svg_mapa_cp_variable(estudio,'rendimiento',opt)
    return estudio


@lru_cache(maxsize=16)
def _ciclo_para_segunda_ley(T1, T3, rp, p1, eta_c, eta_t, delta):
    """Conserva los estados 2B para cambios aislados de T0/p0, sin optimizar."""
    return resolver_ciclo(T1, T3, rp, p1, eta_c, eta_t, delta)


def svg_exergia_destruida(estudio):
    """Barras SVG en kJ/kg; no dibuja destrucciones negativas inconsistentes."""
    a, b = estudio['destruccion']
    if min(a, b) < 0:
        return None
    escala = max(1.0, a, b)
    barras = []
    for i, (nombre, valor, color) in enumerate((('Compresor', a, '#2563a6'),
                                                 ('Turbina', b, '#c2410c'))):
        y = 64 + 82*i
        ancho = 375*valor/escala
        barras.append(f'<text x="20" y="{y+18}" fill="currentColor" font-size="15">{nombre}</text>'
                      f'<rect x="140" y="{y}" width="{ancho:.2f}" height="30" fill="{color}" rx="3">'
                      f'<title>{nombre}: {valor:.6f} kJ/kg</title></rect>'
                      f'<text x="{153+ancho:.2f}" y="{y+20}" font-size="14" fill="currentColor">{valor:.3f}</text>')
    return ('<svg viewBox="0 0 665 260" role="img" '
            'aria-label="Exergía destruida en compresor y turbina, en kilojulios por kilogramo">'
            '<text x="20" y="26" fill="currentColor" font-weight="600">Exergía destruida [kJ/kg]</text>'
            '<text x="20" y="44" fill="currentColor" font-size="12">Solo turbomáquinas adiabáticas; no representa la destrucción total del ciclo</text>'
            + ''.join(barras) + '</svg>')


def preparar_segunda_ley(entradas, T0=288.15, p0=100.0):
    """Una solución 2B cacheada por ciclo y un estudio ambiental recalculable.

    Entradas: dict de 7 números (K, kPa, fracciones), T0 [K], p0 [kPa].
    Devuelve ciclo, estudio físico y SVG opcional sin optimizar ni guardar.
    Las entradas inválidas propagan ValueError/excepciones de 2B.
    """
    ciclo = _ciclo_para_segunda_ley(*(entradas[k] for k in
        ('T1', 'T3', 'rp', 'p1', 'eta_c', 'eta_t', 'delta')))
    estudio = analizar_segunda_ley_cp_variable(ciclo, T0, p0)
    return {'ciclo': ciclo, 'estudio': estudio,
            'svg_destruccion': svg_exergia_destruida(estudio)}
