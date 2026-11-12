"""Barridos M49.5 ampliados en M50.4: un cálculo físico por celda.

La clasificación y las magnitudes de presentación no resuelven otro motor.
"""
from math import isfinite
from time import perf_counter

from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo
from turborreactor_web import simular_turborreactor
from diagnostico_motor_50_2 import diagnosticar_motor_50_2
from configuraciones_modo_c_50_3 import diagnosticar_fallo_50_3


UNIDADES = {
    'empuje_N': 'N', 'empuje_especifico': 'N/(kg/s)', 'TSFC': 'kg/(N·h)',
    'caudal_aire': 'kg/s', 'caudal_corregido': 'kg/s de referencia',
    'rpm': 'rpm', 'rpm_corregidas': 'rpm corregidas',
    'relacion_compresion': '–', 'rendimiento_compresor': '–',
    'rline': '–', 'iteraciones': '–', 'norma_residual': '–',
    'estado_convergencia': 'clasificación',
}

MAGNITUDES_C = ('caudal_aire', 'caudal_corregido', 'rpm', 'rpm_corregidas',
               'relacion_compresion', 'rendimiento_compresor', 'rline',
               'iteraciones', 'norma_residual')

CLASES_C = {
    'entradas': ('entrada_fuera_dominio', 'fuera_dominio'),
    'mapa': ('fuera_mapa', 'sin_solucion'),
    'numerico': ('sin_convergencia_numerica', 'fallo_numerico'),
    'modelo': ('modelo_no_resuelto', 'sin_solucion'),
    'restricciones': ('causa_indeterminada', 'sin_solucion'),
    'indeterminado': ('causa_indeterminada', 'sin_solucion'),
}


def configurar_estudio_49_5(configuracion, modo):
    """Valida ejes crecientes; C: máximo 6×6 y 9 puntos por curva.

    configuracion: dict JSON; modo: str 'impuesto'/'fijo'/'acoplado'.
    Devuelve dict con tipo, listas x/y y nombres de ejes; ValueError al fallar.
    """
    if not isinstance(configuracion, dict):
        raise ValueError('Configuración del estudio no válida.')
    tipo = configuracion.get('tipo')
    if tipo not in ('mach', 'T3', 'mapa'):
        raise ValueError('Selecciona un estudio Mach, T3 o mapa Mach–T3.')
    limites = {'mach': (0., .95), 'T3': (200., 2000.)}

    def eje(nombre):
        try:
            inicio = float(configuracion[f'{nombre}_inicio'])
            fin = float(configuracion[f'{nombre}_fin'])
            numero_bruto = configuracion[f'{nombre}_puntos']
            numero = int(numero_bruto)
            # Evitar convertir valores fraccionarios silenciosamente.
            if float(numero_bruto) != numero:
                raise ValueError('Número de puntos fraccionario.')
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f'Intervalo o resolución de {nombre} inválidos.') from exc
        minimo, maximo = limites[nombre]
        limite_puntos = (6 if modo == 'acoplado' else 11) if tipo == 'mapa' else (
            9 if modo == 'acoplado' else 21)
        if (not all(isfinite(v) for v in (inicio, fin)) or
                not minimo <= inicio < fin <= maximo or
                not 2 <= numero <= limite_puntos):
            raise ValueError(f'{nombre}: usa {minimo} ≤ inicio < fin ≤ {maximo} '
                             f'y de 2 a {limite_puntos} puntos.')
        return [inicio + (fin-inicio)*i/(numero-1) for i in range(numero)]

    xs = eje('mach' if tipo != 'T3' else 'T3')
    ys = eje('T3') if tipo == 'mapa' else None
    if tipo == 'mapa' and len(xs)*len(ys) > (36 if modo == 'acoplado' else 121):
        raise ValueError('Malla demasiado grande.')
    return {'tipo': tipo, 'x': xs, 'y': ys,
            'eje_x': 'mach' if tipo != 'T3' else 'T3',
            'eje_y': 'T3' if tipo == 'mapa' else None}


def _diagnostico_fallo_c_50_4(mensaje, *, excepcion=None):
    """Normaliza evidencia M50.3: causa, estado heredado y explicación.

    mensaje: str; excepcion: clase de excepción opcional. No predice surge
    ni transforma la ausencia de convergencia en inviabilidad física.
    """
    info = diagnosticar_fallo_50_3(mensaje)
    codigo = info['codigo']
    if excepcion is EstadoFueraDeRango:
        codigo = 'entradas'
    elif excepcion is ErrorNumericoCiclo:
        codigo = 'numerico'
    clase, estado = CLASES_C[codigo]
    return estado, {'codigo': clase, 'evidencia': codigo,
                    'resumen': info['resumen'],
                    'recomendacion': info['recomendacion']}


def _magnitudes_c_50_4(resultado):
    """Extrae solo resultados M47 y M50.2; sin física de presentación.

    resultado: dict devuelto por ``simular_turborreactor`` en modo C.
    Devuelve magnitudes numéricas opcionales; ValueError si M47 no verificó.
    """
    motor = resultado.get('motor_acoplado') or {}
    if motor.get('disponible') is not True:
        raise ValueError('No convergió el motor acoplado: sin estado verificado.')
    norma = motor.get('norma_residual')
    if not isinstance(norma, (int, float)) or not isfinite(norma):
        raise ValueError('El resultado C carece de norma residual verificada.')
    comp = motor.get('compresor_mapa') or {}
    correccion = diagnosticar_motor_50_2(resultado)
    absoluto = resultado.get('prestaciones_absolutas') or {}
    return {
        'caudal_aire': absoluto.get('gasto_masico_aire'),
        'caudal_corregido': correccion['caudal_corregido_kg_s'],
        'rpm': motor.get('rpm'),
        'rpm_corregidas': correccion['giro_corregido_rpm'],
        'relacion_compresion': comp.get('rp'),
        'rendimiento_compresor': comp.get('eta'),
        'rline': comp.get('rline'),
        'iteraciones': motor.get('iteraciones'),
        'norma_residual': norma,
    }


def calcular_estudio_49_5(valores, configuracion):
    """Simula la malla M49.5 conservando A/B y extendiendo resultados de C.

    valores: dict[str,str] completo; configuracion: dict JSON.
    Devuelve dict JSON con ejes, constantes, puntos, diagnósticos y resumen.
    La física se calcula una sola vez por muestra con ``simular_turborreactor``.
    """
    modo = valores.get('modo_caudal', 'impuesto')
    if modo not in ('impuesto', 'fijo', 'acoplado'):
        raise ValueError('Modalidad A/B/C desconocida.')
    ejes = configurar_estudio_49_5(configuracion, modo)
    inicio_tiempo = perf_counter()
    puntos = []
    barridos = ({'mach', 'T3'} if ejes['tipo'] == 'mapa' else {ejes['eje_x']})
    constantes = {k: v for k, v in valores.items() if k not in barridos}
    for y in (ejes['y'] if ejes['y'] is not None else [None]):
        for x in ejes['x']:
            parametros = dict(valores)
            parametros[ejes['eje_x']] = format(x, '.12g')
            if y is not None:
                parametros['T3'] = format(y, '.12g')
            coordenadas = {'mach': float(parametros['mach']),
                           'T3': float(parametros['T3'])}
            punto = {**coordenadas, 'estado': 'no_calculado', 'motivo': None,
                     'empuje_N': None, 'empuje_especifico': None, 'TSFC': None,
                     'regimen_tobera': None}
            if modo == 'acoplado':
                punto.update({k: None for k in MAGNITUDES_C})
                punto.update(clasificacion=None, diagnostico=None,
                             entradas=parametros)
            try:
                resultado = simular_turborreactor(parametros)
                if not resultado.get('tobera') or resultado['tobera'].get('resuelto') is False:
                    raise ValueError('Tobera no dispone de una solución física de salida.')
                nuevos = _magnitudes_c_50_4(resultado) if modo == 'acoplado' else {}
                fs = resultado['prestaciones']['empuje_especifico_neto']
                absoluto = (resultado.get('prestaciones_absolutas') or {}).get('empuje_neto')
                tsfc = resultado['prestaciones'].get('TSFC_kg_N_h')
                punto.update(estado='valido', empuje_N=absoluto,
                             empuje_especifico=fs,
                             regimen_tobera=resultado.get('diagnosticos', {}).get('regimen_tobera'),
                             TSFC=tsfc if fs is not None and fs > 0 and
                             tsfc is not None and isfinite(tsfc) and tsfc >= 0 else None)
                if modo == 'acoplado':
                    punto.update(nuevos)
                    punto.update(clasificacion='convergencia_verificada',
                                 diagnostico={'codigo': 'convergencia_verificada',
                                              'resumen': 'Equilibrio aceptado por M47.',
                                              'evidencia': 'solucionador',
                                              'recomendacion': 'Punto calculado con mapas educativos escalados.'})
            except (EstadoFueraDeRango, ErrorNumericoCiclo) as exc:
                if modo == 'acoplado':
                    estado, diagnostico = _diagnostico_fallo_c_50_4(str(exc), excepcion=type(exc))
                    punto.update(estado=estado, clasificacion=diagnostico['codigo'],
                                 diagnostico=diagnostico, motivo=str(exc)[:180])
                elif isinstance(exc, EstadoFueraDeRango):
                    punto.update(estado='fuera_dominio', motivo='Propiedades fuera de 200–2000 K')
                else:
                    punto.update(estado='fallo_numerico', motivo='No convergió el cálculo')
            except (ValueError, ArithmeticError, OverflowError) as exc:
                if modo == 'acoplado':
                    estado, diagnostico = _diagnostico_fallo_c_50_4(str(exc))
                    punto.update(estado=estado, clasificacion=diagnostico['codigo'],
                                 diagnostico=diagnostico, motivo=str(exc)[:180])
                else:
                    punto.update(estado='sin_solucion', motivo=str(exc)[:180])
            puntos.append(punto)
    validos = sum(p['estado'] == 'valido' for p in puntos)
    resumen = {'total': len(puntos), 'validos': validos,
               'sin_solucion': len(puntos)-validos,
               'segundos': round(perf_counter()-inicio_tiempo, 4)}
    if modo == 'acoplado':
        resumen['por_clasificacion'] = {codigo: sum(p['clasificacion'] == codigo for p in puntos)
                                        for codigo in ('convergencia_verificada',
                                            'entrada_fuera_dominio', 'fuera_mapa',
                                            'sin_convergencia_numerica', 'modelo_no_resuelto',
                                            'causa_indeterminada')}
    return {'tipo': ejes['tipo'], 'modo': modo, 'ejes': ejes,
            'constantes': constantes, 'unidades': UNIDADES.copy(),
            'puntos': puntos, 'resumen': resumen}
