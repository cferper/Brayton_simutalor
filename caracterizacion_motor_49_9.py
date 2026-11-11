"""Indicadores educativos del turborreactor, derivados del resultado ya resuelto.

No ejecuta el solucionador. Todas las presiones son totales salvo p∞;
los cocientes carecen de unidades y la potencia requiere caudal absoluto.
"""

from math import isfinite


def caracterizar_motor_49_9(resultado):
    """Recibe resultado dict del turborreactor y devuelve familias de indicadores.

    Cada fila contiene id, nombre, símbolo, valor (float o None), unidad,
    estado, definición, procedencia y limitación. Ninguna fila crea física nueva.
    """
    a, rem, d = (resultado[k] for k in ('ambiente', 'remanso', 'difusor'))
    c, b, t = (resultado[k] for k in ('compresor', 'combustor', 'turbina'))
    n = resultado.get('tobera') or {}
    p = resultado['prestaciones']
    abs_ = resultado.get('prestaciones_absolutas') or {}
    motor = resultado.get('motor_acoplado') or {}

    def ratio(num, den):
        return num / den if (isinstance(num, (float, int)) and
                             isinstance(den, (float, int)) and
                             isfinite(num) and isfinite(den) and den > 0) else None

    def item(clave, nombre, simbolo, valor, unidad, formula, fuente, *,
             derivado=False, nota='', pendiente=False):
        if isinstance(valor, (int, float)) and (not isfinite(valor)):
            valor = None
        disponible = valor is not None and not pendiente
        return {'id': clave, 'nombre': nombre, 'simbolo': simbolo,
                'valor': valor if disponible else None, 'unidad': unidad,
                'estado': ('no_disponible' if not disponible else
                           'derivado' if derivado else 'calculado'),
                'formula': formula, 'fuente': fuente, 'nota': nota}

    ma = abs_.get('gasto_masico_aire')
    f = b['f']
    weje = t['rendimiento_mecanico'] * t['trabajo_turbina_por_kg_aire']
    eta_c = ratio(c['h2s']-c['h1'], c['trabajo_compresor'])
    fs = p.get('empuje_especifico_neto')
    # TSFC solo tiene interpretación para empuje neto positivo.
    tsfc = p.get('TSFC_kg_N_h') if fs is not None and fs > 0 else None
    bruto_abs = (abs_['empuje_momento_salida'] + abs_['empuje_presion']
                 if abs_.get('empuje_momento_salida') is not None and
                 abs_.get('empuje_presion') is not None else None)
    return {
        'funcionamiento': [
            item('tit','Temperatura total de entrada a turbina','TIT',b['T3'],'K','TIT = T3 (interna) = Tt4 (convención orientativa)','combustor.T3'),
            item('rp','Relación de compresión','πc',ratio(c['p2'],c['p1']),'–','πc = pt,salida compresor / pt,entrada compresor','compresor.p2 / compresor.p1',derivado=True),
            item('pt2','Presión total entrada compresor','pt2',c['p1'],'kPa','Presión total después del difusor','compresor.p1'),
            item('pt3','Presión total salida compresor','pt3',c['p2'],'kPa','Presión total antes de cámara','compresor.p2'),
            item('pt4','Presión total entrada turbina','pt4',b['p3'],'kPa','Presión total después de cámara','combustor.p3'),
            item('pt5','Presión total salida turbina','pt5',t['p4'],'kPa','Presión total en entrada de tobera','turbina.p4'),
            item('tt2','Temperatura total entrada compresor','Tt2',c['T1'],'K','T1 interna, después de difusor','compresor.T1'),
            item('tt3','Temperatura total salida compresor','Tt3',c['T2'],'K','T2 interna, antes de cámara','compresor.T2'),
            item('tt5','Temperatura total salida turbina','Tt5',t['T4'],'K','T4 interna, antes de tobera','turbina.T4'),
            item('tpr','Relación de expansión de turbina','πt',ratio(b['p3'],t['p4']),'–','πt = pt,entrada turbina / pt,salida turbina','combustor.p3 / turbina.p4',derivado=True),
            item('npr','Relación de presiones de tobera','NPR',ratio(n.get('presion_remanso'),a['presion']),'–','NPR = pt,entrada tobera / p∞ (estática)','tobera.presion_remanso / ambiente.presion',derivado=True),
            item('epr','Relación de presiones del motor','EPR',ratio(t['p4'],c['p1']),'–','EPR = pt,salida turbina / pt,entrada compresor','turbina.p4 / compresor.p1',derivado=True,nota='Convención de descarga de turbina/entrada de compresor; indicador teórico, no lectura instrumental ni NPR.'),
            item('rpm','Régimen de giro monoeje','N',motor.get('rpm'),'rpm','Resultado de acoplamiento de mapas, exclusivamente C','motor_acoplado.rpm',nota='No disponible en A/B.'),
            item('ma','Caudal másico de aire','ṁa',ma,'kg/s','Caudal de aire antes de añadir combustible','prestaciones_absolutas.gasto_masico_aire',nota='Prescrito en A; resuelto en B/C, si existe solución.'),
            item('mg','Caudal másico de gases','ṁg',abs_.get('gasto_masico_gases'),'kg/s','ṁg = (1+f) ṁa','prestaciones_absolutas.gasto_masico_gases'),
        ],
        'consumo': [
            item('fn','Empuje neto absoluto','Fneto',abs_.get('empuje_neto'),'N','Fneto = ṁa · Fs','prestaciones_absolutas.empuje_neto',nota='Necesita caudal absoluto y salida de tobera resuelta.'),
            item('fb','Empuje bruto absoluto','Fbruto',bruto_abs,'N','Fbruto = Fmomento,salida + Fpresión','prestaciones_absolutas.empuje_momento_salida + empuje_presion',derivado=True),
            item('drag','Resistencia de captación','Dentrada',-abs_['resistencia_entrada'] if abs_.get('resistencia_entrada') is not None else None,'N','Dentrada = ṁa V∞ (magnitud positiva)','−prestaciones_absolutas.resistencia_entrada',derivado=True),
            item('fs','Empuje específico neto','Fs',fs,'N/(kg/s)','Fs = (1+f) Ve + Fpresión/ṁa − V∞','prestaciones.empuje_especifico_neto'),
            item('mf','Caudal de combustible','ṁf',abs_.get('gasto_masico_combustible'),'kg/s','ṁf = f · ṁa','prestaciones_absolutas.gasto_masico_combustible'),
            item('f','Dosado combustible/aire','f',f,'kg/kg aire','f = ṁf / ṁa, cuando ambos caudales existen; mismo f por balance de energía','combustor.f',nota='Combustible equivalente; no se calcula química ni composición.'),
            item('tsfc','Consumo específico de empuje','TSFC',tsfc,'kg/(N·h)','TSFC = 3600 f / Fs, solo Fs > 0','prestaciones.TSFC_kg_N_h',nota='No interpretable con empuje neto nulo/negativo.'),
            item('v0','Velocidad de vuelo','V∞',rem['velocidad_vuelo'],'m/s','V∞ = M∞ · a∞','remanso.velocidad_vuelo'),
            item('ve','Velocidad de salida','Ve',n.get('velocidad_salida'),'m/s','Velocidad estática de salida resuelta','tobera.velocidad_salida'),
        ],
        'rendimientos': [
            item('eta_m','Rendimiento mecánico','ηm',t['rendimiento_mecanico'],'–','ηm = trabajo transmitido / trabajo extraído','turbina.rendimiento_mecanico'),
            item('eta_c','Rendimiento isentrópico compresor','ηc',eta_c,'–','ηc = (h2s−h1)/(h2−h1)','compresor.h2s, h1, trabajo_compresor',derivado=True),
            item('eta_t','Rendimiento isentrópico turbina','ηt',t['rendimiento_turbina'],'–','ηt: relación de saltos entálpicos real/isentrópico','turbina.rendimiento_turbina'),
            item('loss_d','Pérdida de presión total del difusor','δd',100*(1-ratio(d['presion_remanso'],rem['presion_remanso'])) if ratio(d['presion_remanso'],rem['presion_remanso']) is not None else None,'%','δd = 100(1−pt,salida/pt,entrada)','difusor.presion_remanso / remanso.presion_remanso',derivado=True),
            item('loss_b','Pérdida de presión total de cámara','δb',100*b['delta'],'%','δb = 100(1−pt,salida/pt,entrada)','combustor.delta',derivado=True),
            item('wc','Trabajo específico compresor','wc',c['trabajo_compresor'],'kJ/kg aire','wc = h2−h1','compresor.trabajo_compresor'),
            item('wt','Trabajo específico turbina','wt',t['trabajo_turbina_por_kg_aire'],'kJ/kg aire','wt = (1+f)(h3−h4)','turbina.trabajo_turbina_por_kg_aire'),
            item('weje','Trabajo específico al compresor','weje',weje,'kJ/kg aire','weje = ηm wt','turbina.rendimiento_mecanico × trabajo_turbina_por_kg_aire',derivado=True),
            item('peje','Potencia transmitida','Peje',weje*ma if ma is not None else None,'kW','Peje = ṁa · weje','trabajo específico del eje × gasto_masico_aire',derivado=True),
            item('eta_th','Rendimiento térmico del turborreactor','ηth',None,'–','Requiere definir aumento de energía cinética y contribución de presión en volumen de control','No calculado',pendiente=True,nota='Pendiente de un balance propulsivo validado para este modelo.'),
            item('eta_p','Rendimiento propulsivo','ηp',None,'–','Requiere potencia propulsiva y potencia de chorro coherentes con empuje de presión','No calculado',pendiente=True,nota='En estático F·V∞ = 0; no se fuerza un rendimiento.'),
            item('eta_o','Rendimiento global','ηo',None,'–','Requiere una definición consistente de potencia útil / potencia química','No calculado',pendiente=True,nota='No se reutiliza la eficiencia de un Brayton productor de eje.'),
        ],
    }
