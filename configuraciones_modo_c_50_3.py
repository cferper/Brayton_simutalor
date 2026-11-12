"""Ejemplos verificados y clasificación prudente del modo C (M50.3).

No contiene modelos físicos ni calcula equilibrios en tiempo de una petición web.
Cada entrada es un formulario completo; el cálculo sigue en el solver M47.
"""

from functools import lru_cache
from acoplamiento_motor_mapa_47 import punto_diseno_47
from turborreactor_web import DEFAULTS_TURBO


# Casos focalizados comprobados con el solucionador real M47/M50.2.
# No representan regiones continuas admisibles ni motores experimentales.
VARIANTES_50_3 = (
    ('diseno', 'Diseño de referencia', {}, 'Calibración M47, convergente.'),
    ('vuelo04', 'Vuelo Mach 0,4', {'mach': '0.4'}, 'Otros parámetros iguales al diseño.'),
    ('t3_1550', 'TIT 1550 K', {'T3': '1550'}, 'Cambio aislado de TIT.'),
    ('t3_1650', 'TIT 1650 K', {'T3': '1650'}, 'Cambio aislado de TIT.'),
    ('presion95', 'Presión exterior 95 kPa', {'p_amb': '95'}, 'Cambio de presión directa, no altitud ISA.'),
    ('cd12', 'Tobera C-D · Ae/Ag = 1,2', {'tipo_tobera': 'convergente_divergente'},
     'Convergente-divergente ideal salvo choque normal modelado; sin pérdidas viscosas.'),
)


@lru_cache(maxsize=1)
def _referencia_diseno_50_3():
    return punto_diseno_47()


def configuraciones_verificadas_50_3(*, referencia=None):
    """Devuelve entradas completas por caso con Ag del diseño actual [m²].

    No realiza una segunda simulación. ``referencia`` es el dict M47 opcional;
    si se omite, solo obtiene la calibración existente una vez al renderizar.
    """
    ref = _referencia_diseno_50_3() if referencia is None else referencia
    ag = ref['area_garganta_diseno']
    base = {**DEFAULTS_TURBO, 'modo_caudal': 'acoplado',
            'tipo_tobera': 'convergente', 'area_garganta_fija': str(ag),
            'area_salida_fija': str(ag), 'gasto_masico_aire': ''}
    ejemplos = []
    for clave, nombre, cambios, descripcion in VARIANTES_50_3:
        entradas = {**base, **cambios}
        if clave == 'cd12':
            entradas['area_salida_fija'] = str(1.2 * ag)
        ejemplos.append({'id': clave, 'nombre': nombre, 'descripcion': descripcion,
                         'entradas': entradas})
    return ejemplos


def diagnosticar_fallo_50_3(mensaje):
    """Clasifica *evidencia textual*; no diagnostica surge ni inviabilidad física.

    Devuelve código, resumen y consejo. Una causa ambigua queda indeterminada.
    Los mensajes de error no se transforman en resultados físicos.
    """
    texto = str(mensaje).lower()
    if any(x in texto for x in ('no converg', 'sin descenso del residuo',
                                'jacobiano', 'equilibrio numérico', 'agotamiento')):
        codigo = 'numerico'
        resumen = 'No se ha verificado la convergencia del algoritmo.'
    elif any(x in texto for x in ('fuera del dominio del mapa', 'fuera del dominio de los mapas',
                                  'fuera del dominio de mapa', 'extrapolación')):
        codigo = 'mapa'
        resumen = 'Se ha solicitado una condición fuera del mapa tabulado.'
    elif any(x in texto for x in ('no cierra la continuidad', 'no admiten el caudal',
                                  'cierres físicos insuficientes')):
        codigo = 'restricciones'
        resumen = 'No se satisfacen los cierres de masa o geometría comprobados.'
    elif any(x in texto for x in ('tobera no dispone de solución',
                                  'tobera c-d no dispone de solución',
                                  'régimen no resuelto', 'no dispone de una solución física de salida')):
        codigo = 'modelo'
        resumen = 'La salida de la tobera no está resuelta para este caso.'
    elif any(x in texto for x in ('inválid', 'debe ', 'requiere ', 'no combines',
                                  'fuera del modelo subsónico', 'no es admisible',
                                  'no permit', 'selecciona ', 'no puede ', 'deben ')):
        codigo = 'entradas'
        resumen = 'Una entrada incumple una condición explícita del modelo.'
    else:
        codigo = 'indeterminado'
        resumen = 'No se ha identificado una causa única con la información disponible.'
    return {
        'codigo': codigo, 'resumen': resumen,
        'recomendacion': ('Restablece el punto de diseño C comprobado y cambia una sola entrada cada vez. '
                          'La ausencia de solución numérica no demuestra imposibilidad física.'),
    }
