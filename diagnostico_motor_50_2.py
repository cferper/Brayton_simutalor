"""M50.2: presentación de parámetros corregidos y mapa HPC educativo.

No resuelve otro punto motor. Usa el cálculo existente y los mapas públicos
NASA T-MATS escalados por M47; no interpreta Rline como margen de surge.
"""

from html import escape
from math import isfinite

from mapas_turbomaquinaria_47 import (T_REF_MAPA, P_REF_MAPA, cargar_mapas,
    flujo_corregido, giro_corregido)


def diagnosticar_motor_50_2(resultado):
    """Devuelve dict serializable: magnitudes, dominio, estado y curvas C.

    `resultado` es un dict de `simular_turborreactor` ya resuelto. No hace
    nuevas simulaciones del motor. Valores ausentes son None; unidades SI.
    """
    modo = resultado.get('modo_caudal', 'impuesto')
    c = resultado['compresor']
    a = resultado.get('prestaciones_absolutas') or {}
    motor = resultado.get('motor_acoplado') or {}
    mapa_actual = motor.get('compresor_mapa') or {}
    ma = a.get('gasto_masico_aire')
    tt, pt = c['T1'], c['p1']  # Estado total inmediatamente tras el difusor.
    def valido(valor):
        return isinstance(valor, (int, float)) and not isinstance(valor, bool) and isfinite(valor) and valor > 0

    wc = flujo_corregido(ma, tt, pt) if all(map(valido, (ma, tt, pt))) else None
    n = motor.get('rpm') if modo == 'acoplado' else None
    nc = giro_corregido(n, tt) if valido(n) and valido(tt) else None
    razones = []
    if wc is None:
        razones.append('Caudal corregido no disponible: falta un caudal de aire absoluto válido.')
    if nc is None:
        razones.append('Giro corregido no disponible: solo el modo C resuelve rpm del eje.')
    curvas = None
    punto = None
    dominio = 'No aplicable: A/B no resuelven el equilibrio sobre el mapa HPC.'
    if modo == 'acoplado' and motor.get('disponible') is True and wc is not None and nc is not None:
        # El propio solver proporciona las coordenadas de mapa C.
        m = cargar_mapas()['compresor']
        esc = resultado['referencia_mapa_compresor_47']
        punto = {'caudal_corregido': wc, 'giro_corregido': nc,
                 'relacion_compresion': c['p2']/c['p1'],
                 'rendimiento': mapa_actual.get('eta'),
                 'rline': mapa_actual.get('rline'),
                 'giro_mapa': mapa_actual.get('giro_mapa')}
        # Líneas nativas, escaladas exactamente como el interpolador M47;
        # una fila corresponde a una velocidad nativa tabulada, no a un ensayo.
        curvas = []
        for i, nmap in enumerate(m['ncorr']):
            puntos = []
            for j, rline in enumerate(m['rline']):
                w = esc['wc']*m['wc'][i][j]
                pr = 1+esc['pr']*(m['pr'][i][j]-1)
                eta = esc['eta']*m['eta'][i][j]
                if w > 0 and pr > 1 and 0 < eta <= 1:
                    puntos.append({'caudal_corregido': w, 'relacion_compresion': pr,
                                   'rendimiento': eta, 'rline': rline})
            if len(puntos) >= 2:
                curvas.append({'giro_mapa': nmap,
                               'giro_corregido': nmap/esc['nc'], 'puntos': puntos})
        dentro = (m['ncorr'][0] <= punto['giro_mapa'] <= m['ncorr'][-1]
                  and m['rline'][0] <= punto['rline'] <= m['rline'][-1])
        dominio = ('Dentro del dominio tabulado HPC, sin extrapolación.' if dentro
                   else 'Coordenadas fuera del dominio del mapa: resultado inconsistente.')
        if not dentro:
            # Nunca dibujar un punto supuestamente válido fuera del dominio.
            punto = None
    elif modo == 'acoplado':
        dominio = 'No hay un punto convergido de mapa válido para representar.'
    return {'modo': modo, 'referencia': {'temperatura_K': T_REF_MAPA,
                                        'presion_kPa': P_REF_MAPA},
            'entrada_compresor': {'Tt_K': tt, 'pt_kPa': pt},
            'caudal_corregido_kg_s': wc, 'giro_real_rpm': n,
            'giro_corregido_rpm': nc,
            'punto_compresor': punto, 'curvas_compresor': curvas,
            'dominio': dominio, 'avisos': razones,
            'modelo': 'HPC NASA T-MATS adaptado y escalado al diseño didáctico M47',
            'limite': 'Sin margen de surge verificado: Rline=1 es un borde de tabla, no un límite certificado.'}


def svg_mapa_compresor_50_2(diagnostico):
    """Devuelve SVG de curvas y punto C; para A/B devuelve cadena vacía.

    Ejes: caudal corregido [kg/s de referencia] y razón de presión total [-].
    Solo visualiza los puntos tabulados y el punto convergido existente.
    """
    curvas = diagnostico.get('curvas_compresor') or []
    punto = diagnostico.get('punto_compresor')
    if not punto or not curvas:
        return ''
    todos = [p for curva in curvas for p in curva['puntos']] + [punto]
    xs = [p['caudal_corregido'] for p in todos]
    ys = [p['relacion_compresion'] for p in todos]
    if not all(isfinite(v) for v in xs+ys):
        return ''
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    dx, dy = max(xmax-xmin, 1e-9), max(ymax-ymin, 1e-9)
    xmin -= dx*.06; xmax += dx*.06; ymin = max(0, ymin-dy*.09); ymax += dy*.10
    width, height = 760, 440
    x0, y0, w, h = 84, 45, 625, 315
    x = lambda v: x0+(v-xmin)/(xmax-xmin)*w
    y = lambda v: y0+h-(v-ymin)/(ymax-ymin)*h
    el = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
          'role="img" aria-label="Mapa educativo HPC: curvas de velocidad corregida y punto de operación calculado">',
          '<title>Mapa educativo escalado del compresor HPC</title>',
          '<desc>Relación de presión total frente a caudal corregido. Curvas discretas tabuladas y marcador del punto acoplado C. Sin margen de surge.</desc>',
          f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#f6fafc" stroke="#b7cbd9"/>']
    for i in range(5):
        xv=xmin+(xmax-xmin)*i/4; yv=ymin+(ymax-ymin)*i/4
        el += [f'<path d="M{x(xv):.2f} {y0}V{y0+h}" stroke="#dae5ed"/>',
               f'<path d="M{x0} {y(yv):.2f}H{x0+w}" stroke="#dae5ed"/>',
               f'<text x="{x(xv):.2f}" y="{y0+h+23}" text-anchor="middle" font-size="12" fill="#32516b">{xv:.2f}</text>',
               f'<text x="{x0-12}" y="{y(yv)+4:.2f}" text-anchor="end" font-size="12" fill="#32516b">{yv:.2f}</text>']
    for idx, curva in enumerate(curvas):
        ps=curva['puntos']
        ruta=' '.join(('M' if k==0 else 'L')+f'{x(p["caudal_corregido"]):.2f},{y(p["relacion_compresion"]):.2f}' for k,p in enumerate(ps))
        stroke='#527c98' if idx%2==0 else '#7799ad'
        el.append(f'<path d="{ruta}" stroke="{stroke}" stroke-width="1.7" fill="none"/>')
        ultimo=ps[-1]
        el.append(f'<text x="{x(ultimo["caudal_corregido"])+5:.1f}" y="{y(ultimo["relacion_compresion"])-3:.1f}" font-size="10" fill="#315c75">Ncorr={curva["giro_corregido"]:.0f}</text>')
        for p in ps:
            msg=(f'Ncorr={curva["giro_corregido"]:.1f} rpm; ṁcorr={p["caudal_corregido"]:.4g} kg/s; '
                 f'πc={p["relacion_compresion"]:.4g}; ηc={p["rendimiento"]:.4g}; Rline={p["rline"]:.3g}')
            el.append(f'<circle cx="{x(p["caudal_corregido"]):.2f}" cy="{y(p["relacion_compresion"]):.2f}" r="2.4" fill="{stroke}" tabindex="0" data-plot-info="{escape(msg, quote=True)}"><title>{escape(msg)}</title></circle>')
    px,py=x(punto['caudal_corregido']),y(punto['relacion_compresion'])
    msg=(f'Punto C actual: ṁcorr={punto["caudal_corregido"]:.5g} kg/s; Ncorr={punto["giro_corregido"]:.5g} rpm; '
         f'πc={punto["relacion_compresion"]:.5g}; ηc={punto["rendimiento"]:.4g}; Rline={punto["rline"]:.4g}')
    el += [f'<circle cx="{px:.2f}" cy="{py:.2f}" r="8" fill="#b75023" stroke="white" stroke-width="2" tabindex="0" role="img" data-plot-info="{escape(msg, quote=True)}" aria-label="{escape(msg, quote=True)}"><title>{escape(msg)}</title></circle>',
           f'<text x="{px+12:.2f}" y="{py-10:.2f}" font-size="12" font-weight="bold" fill="#8e3a20">Punto C actual</text>',
           f'<text x="{x0+w/2:.1f}" y="{height-27}" text-anchor="middle" font-size="13" fill="#244961">Caudal corregido [kg/s de referencia]</text>',
           f'<text x="19" y="{y0+h/2:.1f}" transform="rotate(-90 19 {y0+h/2:.1f})" text-anchor="middle" font-size="13" fill="#244961">Relación de presión total πc [–]</text>',
           '</svg>']
    return ''.join(el)
