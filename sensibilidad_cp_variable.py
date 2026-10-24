"""Barridos OFAT y derivadas locales del ciclo cp(T), sin fórmulas duplicadas.

Todas las evaluaciones utilizan `resolver_ciclo` de la Fase 2B. Una fila
calculable no motora jamás se interpreta como prestación operativa.
"""

from collections import Counter
from math import isfinite

from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo, resolver_ciclo


# Rangos sugeridos para enseñar el método OFAT, no límites físicos universales.
PARAMETROS_CP = {
    'T1': {'etiqueta': 'Temperatura de entrada T1', 'unidad': 'K', 'rango': (260, 340)},
    'T3': {'etiqueta': 'Temperatura de entrada T3', 'unidad': 'K', 'rango': (1200, 1750)},
    'rp': {'etiqueta': 'Relación de compresión rp', 'unidad': '—', 'rango': (2, 65)},
    'p1': {'etiqueta': 'Presión absoluta p1', 'unidad': 'kPa', 'rango': (80, 130)},
    'eta_c': {'etiqueta': 'Eficiencia compresor ηc', 'unidad': 'fracción', 'rango': (0.75, 1)},
    'eta_t': {'etiqueta': 'Eficiencia turbina ηt', 'unidad': 'fracción', 'rango': (0.75, 1)},
    'delta': {'etiqueta': 'Pérdida del combustor δ', 'unidad': 'fracción', 'rango': (0, 0.15)},
}
MAGNITUDES = ('trabajo_compresor', 'trabajo_turbina', 'trabajo_neto',
              'calor_aportado', 'rendimiento', 'T2', 'T4')


def _evaluar(entradas):
    """Un punto y su estado observable, conservando la causa del descarte."""
    try:
        ciclo = resolver_ciclo(**entradas)
    except EstadoFueraDeRango as exc:
        return {'estado': 'fuera_rango', 'motivo': str(exc), 'ciclo': None}
    except ValueError as exc:
        return {'estado': 'entrada_invalida', 'motivo': str(exc), 'ciclo': None}
    except (ErrorNumericoCiclo, ArithmeticError, OverflowError) as exc:
        return {'estado': 'error_numerico', 'motivo': str(exc), 'ciclo': None}

    return {
        'estado': 'motor' if ciclo['viable'] else 'no_motor',
        'motivo': ', '.join(ciclo['motivos']) if not ciclo['viable'] else '',
        'ciclo': ciclo,
    }


def _magnitudes(ciclo):
    return {**{key: ciclo[key] for key in MAGNITUDES[:5]},
            'T2': ciclo['temperaturas'][1], 'T4': ciclo['temperaturas'][3]}


def sensibilidad_local(entradas, parametro, paso_relativo=1e-3):
    """S=(x/Y) dY/dx, central o unilateral en el dominio motor abierto.

    La estimación se repite con paso mitad; una discrepancia elevada produce
    diagnóstico de derivada inestable, nunca falsa precisión.
    """
    if parametro not in PARAMETROS_CP:
        raise ValueError('Parámetro de sensibilidad desconocido.')
    if not isinstance(paso_relativo, (float, int)) or not isfinite(paso_relativo) or not 0 < paso_relativo <= .05:
        raise ValueError('El paso relativo debe estar entre 0 y 0.05, excluido 0.')

    centro = _evaluar(entradas)
    respuestas = {}
    for objetivo in ('trabajo_neto', 'rendimiento'):
        if centro['estado'] != 'motor':
            respuestas[objetivo] = {'estado': 'no_disponible', 'motivo': 'El caso de referencia no es motor.'}
            continue
        x0, y0 = entradas[parametro], centro['ciclo'][objetivo]
        if x0 == 0 or y0 is None or abs(y0) < 1e-12:
            respuestas[objetivo] = {'estado': 'no_disponible', 'motivo': 'Normalización singular: x o Y es cero.'}
            continue
        h = paso_relativo * max(abs(x0), 1e-2)

        def aproximar(paso):
            resultados = []
            for signo in (-1, 1):
                variante = {**entradas, parametro: x0 + signo * paso}
                resultados.append(_evaluar(variante))
            anterior, posterior = resultados
            mas = posterior['ciclo'][objetivo] if posterior['estado'] == 'motor' else None
            menos = anterior['ciclo'][objetivo] if anterior['estado'] == 'motor' else None
            if mas is not None and menos is not None:
                return (mas - menos)/(2*paso), 'central'
            if mas is not None:
                return (mas - y0)/paso, 'adelante'
            if menos is not None:
                return (y0 - menos)/paso, 'atrás'
            return None, 'sin vecinos motores'

        derivada, esquema = aproximar(h)
        refinada, esquema_refinado = aproximar(h/2)
        if derivada is None or refinada is None:
            respuestas[objetivo] = {'estado': 'no_disponible', 'motivo': 'Sin puntos motores próximos.'}
            continue
        s, s_ref = x0*derivada/y0, x0*refinada/y0
        estable = esquema == esquema_refinado and abs(s-s_ref) <= max(1e-4, .05*max(abs(s), abs(s_ref)))
        respuestas[objetivo] = {
            'estado': 'disponible' if estable else 'inestable',
            'valor': s_ref if estable else None,
            'esquema': esquema_refinado,
            'diferencia_pasos': abs(s-s_ref),
            'motivo': '' if estable else 'La derivada cambia al reducir el paso o el esquema.',
        }
    return respuestas


def barrido_cp_variable(entradas, parametro, minimo, maximo, muestras=41):
    """Evalúa un factor manteniendo los otros seis constantes (OFAT).

    Conserva todas las posiciones de la malla incluso cuando hay un hueco,
    de modo que el trazador no una regiones motoras separadas.
    """
    if parametro not in PARAMETROS_CP:
        raise ValueError('Parámetro de sensibilidad desconocido.')
    if not isinstance(muestras, int) or isinstance(muestras, bool) or not 3 <= muestras <= 201:
        raise ValueError('El número de muestras debe ser un entero de 3 a 201.')
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and isfinite(v)
               for v in (minimo, maximo)) or not minimo < maximo:
        raise ValueError('Los límites deben ser finitos y el mínimo menor que el máximo.')
    if set(entradas) != set(PARAMETROS_CP):
        raise ValueError('El caso base debe contener exactamente las siete entradas físicas.')

    filas = []
    for indice in range(muestras):
        x = minimo + (maximo - minimo)*indice/(muestras-1)
        if indice == muestras-1:
            x = maximo
        resultado = _evaluar({**entradas, parametro: x})
        ciclo = resultado['ciclo']
        filas.append({
            'x': x,
            'estado': resultado['estado'],
            'motivo': resultado['motivo'],
            'magnitudes': _magnitudes(ciclo) if ciclo is not None else None,
            # Sólo una fila motora puede alimentar gráficas de prestaciones.
            'operativas': _magnitudes(ciclo) if resultado['estado'] == 'motor' else None,
            'residuo_primera_ley': ciclo['residuo_primera_ley'] if ciclo is not None else None,
        })
    referencia = _evaluar(entradas)
    return {
        'parametro': parametro,
        'unidad': PARAMETROS_CP[parametro]['unidad'],
        'minimo': minimo, 'maximo': maximo, 'muestras': muestras,
        'filas': filas,
        'conteos': dict(Counter(f['estado'] for f in filas)),
        'referencia_x': entradas[parametro],
        'referencia': referencia,
        'local': sensibilidad_local(entradas, parametro),
    }
