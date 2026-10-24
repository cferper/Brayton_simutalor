"""Mapa rp–T3 del ciclo de aire cp(T) sin duplicar su termodinámica.

Malla logarítmica en rp y lineal en T3. Las magnitudes son específicas
[kJ/kg], las temperaturas están en K y las presiones en kPa.
"""

from collections import Counter
from math import exp, isfinite, log

from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo, resolver_ciclo


DEFAULT_MAPA = {'rp_min': 1.1, 'rp_max': 80.0,
                'T3_min': 1200.0, 'T3_max': 1800.0,
                'n_rp': 31, 'n_T3': 31}
MAX_PUNTOS_EJE = 51


def _configuracion_valida(entradas, rp_min, rp_max, T3_min, T3_max, n_rp, n_T3):
    """Valida presupuesto de malla y configuración; 2B valida la física."""
    if set(entradas) != {'T1', 'T3', 'rp', 'p1', 'eta_c', 'eta_t', 'delta'}:
        raise ValueError('El caso requiere las siete entradas físicas.')
    limites = (rp_min, rp_max, T3_min, T3_max)
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not isfinite(x)
           for x in limites):
        raise ValueError('Los límites deben ser números finitos.')
    if not (0 < rp_min < rp_max <= 1000):
        raise ValueError('Se requiere 0 < rp mínima < rp máxima ≤ 1000.')
    if not (0 < T3_min < T3_max <= 3000):
        raise ValueError('Se requiere 0 < T3 mínima < T3 máxima ≤ 3000 K.')
    for nombre, n in (('n_rp', n_rp), ('n_T3', n_T3)):
        if isinstance(n, bool) or not isinstance(n, int) or not 5 <= n <= MAX_PUNTOS_EJE:
            raise ValueError(f'{nombre}: utiliza un entero de 5 a {MAX_PUNTOS_EJE}.')
    # Valida las entradas físicas fijas utilizando el solucionador ya existente.
    # Un estado de referencia fuera de 200–2000 K no impide explorar otro rp/T3.
    try:
        resolver_ciclo(**entradas)
    except (EstadoFueraDeRango, ErrorNumericoCiclo):
        pass


def _evaluar_punto(entradas, rp, T3):
    """Adapta el retorno de 2B a una celda, sin usar el modelo histórico."""
    try:
        ciclo = resolver_ciclo(**{**entradas, 'rp': rp, 'T3': T3})
    except EstadoFueraDeRango as exc:
        return {'rp': rp, 'T3': T3, 'estado': 'fuera_rango',
                'motivo': str(exc), 'datos': None, 'operativas': None}
    except ValueError as exc:
        return {'rp': rp, 'T3': T3, 'estado': 'entrada_invalida',
                'motivo': str(exc), 'datos': None, 'operativas': None}
    except (ErrorNumericoCiclo, ArithmeticError, OverflowError) as exc:
        return {'rp': rp, 'T3': T3, 'estado': 'error_numerico',
                'motivo': str(exc), 'datos': None, 'operativas': None}

    datos = {clave: ciclo[clave] for clave in
             ('trabajo_compresor', 'trabajo_turbina', 'trabajo_neto',
              'calor_aportado', 'calor_rechazado', 'rendimiento',
              'residuo_primera_ley')}
    datos['temperaturas'] = ciclo['temperaturas']
    viable = ciclo['viable']
    return {'rp': rp, 'T3': T3, 'estado': 'motor' if viable else 'no_motor',
            'motivo': ', '.join(ciclo['motivos']) if not viable else '',
            'datos': datos, 'operativas': datos if viable else None}


def calcular_mapa_cp_variable(entradas, rp_min=1.1, rp_max=80.0,
                             T3_min=1200.0, T3_max=1800.0,
                             n_rp=31, n_T3=31):
    """Devuelve filas[T3][rp], recuentos y mejores *muestras* motoras.

    `entradas` son las siete entradas de 2B. Solo rp y T3 cambian. Los
    óptimos continuos A/B de 2C NO se obtienen de una malla discreta.
    """
    _configuracion_valida(entradas, rp_min, rp_max, T3_min, T3_max, n_rp, n_T3)
    log_min, log_max = log(rp_min), log(rp_max)
    rps = [exp(log_min+(log_max-log_min)*i/(n_rp-1)) for i in range(n_rp)]
    rps[0], rps[-1] = rp_min, rp_max
    temperaturas = [T3_min+(T3_max-T3_min)*j/(n_T3-1) for j in range(n_T3)]
    temperaturas[0], temperaturas[-1] = T3_min, T3_max
    filas = [[_evaluar_punto(entradas, rp, T3) for rp in rps] for T3 in temperaturas]
    contadores = Counter(celda['estado'] for fila in filas for celda in fila)
    motores = [celda for fila in filas for celda in fila if celda['operativas'] is not None]
    mejores = {}
    for clave in ('trabajo_neto', 'rendimiento'):
        mejores[clave] = max(motores, key=lambda p: p['operativas'][clave]) if motores else None
    return {
        'rps': rps, 'T3s': temperaturas, 'filas': filas,
        'n_rp': n_rp, 'n_T3': n_T3,
        'rp_min': rp_min, 'rp_max': rp_max, 'T3_min': T3_min, 'T3_max': T3_max,
        'conteos': dict(contadores), 'mejores_malla': mejores,
        'referencia_T3': entradas['T3'], 'fijos': {k: entradas[k] for k in
            ('T1', 'p1', 'eta_c', 'eta_t', 'delta')},
    }
