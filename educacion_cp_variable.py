"""Textos educativos estáticos del dashboard cp(T), sin cálculos físicos.

Los fragmentos HTML son contenido propio del proyecto; nunca interpolan datos
del usuario. Las conclusiones que dependen de resultados se generan en Jinja.
"""

from html import escape


AYUDAS_CP = {
    'T1': 'Temperatura del aire antes de comprimir (200–2000 K). Afecta al trabajo que necesita el compresor.',
    'T3': 'Temperatura del aire antes de expandirse en turbina (200–2000 K). Condiciona la energía disponible para producir trabajo.',
    'rp': 'Relación p2/p1, adimensional y positiva. Al aumentarla crece la exigencia de compresión; no garantiza más trabajo neto.',
    'p1': 'Presión absoluta a la entrada del compresor, en kPa (>0). Fija la escala de presiones de los cuatro estados.',
    'eta_c': 'Rendimiento isentrópico del compresor (0 < ηc ≤ 1). Un valor menor exige más trabajo para el mismo salto de presión.',
    'eta_t': 'Rendimiento isentrópico de la turbina (0 < ηt ≤ 1). Un valor menor permite extraer menos trabajo en la expansión.',
    'delta': 'Fracción de presión perdida entre 2 y 3 (0 ≤ δ < 1). Por ejemplo, 0.05 es una pérdida del 5 % y reduce la expansión disponible.',
}

AYUDAS_MAPA = {
    'rp_min': 'Extremo inferior positivo del intervalo de relaciones de compresión; no implica que sea motor.',
    'rp_max': 'Extremo superior del intervalo (mayor que el mínimo, hasta 1000). No equivale a una frontera física del ciclo.',
    'T3_min': 'Temperatura más baja explorada, en K, que puede producir estados fuera del rango 200–2000 K.',
    'T3_max': 'Temperatura más alta explorada, en K (cota de configuración 3000 K; los estados de más de 2000 K se excluyen).',
    'n_rp': 'Número de columnas entre los extremos de rp (5–51); más puntos dan más detalle, pero implican más cálculos.',
    'n_T3': 'Número de filas entre los extremos de T3 (5–51); no modifica las ecuaciones ni la ubicación de los óptimos continuos.',
}


# Cinco bloques en cada sección: objetivo, hipótesis, cálculo, interpretación y límites.
# HTML de autoría controlada: subíndices y fórmulas se conservan legibles.
CONTENIDOS = {
    'simulacion': {
        'uso': ('Definimos las condiciones de entrada de un Brayton abierto idealizado con aire de composición fija. '
                'El ciclo recorre cuatro estados: 1 antes de compresor, 2 después de compresor, '
                '3 antes de turbina y 4 después de turbina. Introduce siete magnitudes: '
                'temperaturas T1/T3 [K], presión p1 [kPa], rp=p2/p1 [−], ηc/ηt [fracción] y δ [fracción]. '
                'El botón Simulación calcula los estados; después puedes estudiar diseños y pérdidas en las otras secciones.'),
        'fundamentos': (
            ('Objetivo termodinámico', 'Obtener un ciclo Brayton coherente a partir de condiciones de operación y pérdidas. '
             'La compresión consume trabajo, el aporte de calor eleva la entalpía, la turbina produce trabajo '
             'y el rechazo de calor cierra el balance energético del ciclo idealizado.'),
            ('Hipótesis del modelo', 'El aire sigue la ley de gas ideal y mantiene proporciones fijas de N₂, O₂ y Ar. '
             'La novedad es que su calor específico <em>cp(T)</em> cambia con la temperatura: ideal <strong>no</strong> '
             'significa calor específico constante. El rango de propiedades es 200–2000 K; '
             'se omiten combustión química real, caudal y empuje.'),
            ('Procedimiento de cálculo paso a paso', '<ol><li>Definir p2=p1·rp y p3=p2·(1−δ), con p4=p1.</li>'
             '<li>Hallar T2s haciendo s(T2s,p2)=s(T1,p1); obtener T2 real mediante '
             'ηc=(h2s−h1)/(h2−h1).</li>'
             '<li>Hallar T4s con s(T4s,p4)=s(T3,p3); obtener T4 con '
             'ηt=(h3−h4)/(h3−h4s).</li>'
             '<li>Comprobar temperaturas y restricciones motoras; usar h(T) y s(T,p) para balances. '
             'No aparece una potencia constante T<sup>(γ−1)/γ</sup>, porque γ varía.</li></ol>'),
            ('Interpretación física', 'Bajar ηc normalmente incrementa el trabajo consumido; bajar ηt reduce el trabajo obtenido. '
             'Aumentar δ reduce la presión disponible antes de la turbina. Subir T3 puede favorecer la expansión, '
             'pero la respuesta real depende de todas las entradas. El simulador puede calcular un estado <em>no motor</em>.'),
            ('Limitaciones y conclusiones', 'El formulario describe un ciclo termodinámico educativo, no una turbina certificada. '
             'Las entradas no garantizan estado motor ni rendimiento definido. Aprendemos a separar '
             'las <strong>hipótesis del gas</strong> de las <strong>pérdidas de los componentes</strong>.')),
    },
    'resultados': {
        'uso': ('Consultamos qué estados, trabajos y calores resultan de las siete entradas. Las propiedades se evalúan '
                'en cada temperatura; ηt y ηc son los parámetros de los equipos, no el rendimiento térmico del ciclo. '
                'La tabla reúne T, p, cp(T), γ(T), h y s para los cuatro estados; el diagrama T–s se explica por separado.'),
        'fundamentos': (
            ('Objetivo termodinámico', 'Responder cuánto trabajo extraemos por kilogramo de aire, cuánto consumimos '
             'para comprimirlo y qué fracción de la energía aportada aparece como trabajo neto. '
             'La primera ley comprueba conservación, no rendimiento de un motor real.'),
            ('Hipótesis del modelo', 'Las entalpías se definen respecto a 298,15 K y las entropías respecto a 298,15 K '
             'y 100 kPa. Sus ceros son convencionales; las <strong>diferencias</strong> importan. '
             'Se desprecia variación de energía cinética/potencial.'),
            ('Procedimiento de cálculo paso a paso', '<ol><li>Resolver T2s y T4s isentrópicas como referencias y, después, '
             'T2 y T4 reales con eficiencias de componente.</li>'
             '<li>Evaluar h1…h4 y s1…s4 con las funciones de propiedades variables.</li>'
             '<li>Trabajos específicos: wc=h2−h1 (absorbe), wt=h3−h4 (produce), wnet=wt−wc.</li>'
             '<li>Calores: qin=h3−h2 y qout=h4−h1. Verificar wnet=qin−qout con un residuo numérico pequeño.</li>'
             '<li>Solo si el caso es motor, ηtérmica=wnet/qin. Comparar también cp(T) y γ(T) entre estados.</li></ol>'),
            ('Interpretación física', 'Un trabajo de compresor más alto puede anular el beneficio de una turbina potente. '
             'El eje horizontal del diagrama T–s es entropía específica y el vertical temperatura: '
             'los <strong>cuatro puntos</strong> son calculados; los segmentos discontinuos son guías '
             'esquemáticas, <strong>no</strong> trayectorias termodinámicas exactas.'),
            ('Limitaciones y conclusiones', 'El rendimiento térmico no es rendimiento exergético ni mide potencia: '
             'sin caudal másico no hay kW. Un ciclo no motor conserva valores de diagnóstico, '
             'pero no una prestación térmica operativa.')),
    },
    'optimizacion': {
        'uso': ('Buscamos la mejor relación de compresión rp para dos objetivos distintos. '
                'Se mantienen fijos T1, T3, p1, ηc, ηt y δ; el algoritmo solo modifica rp. '
                'A maximiza trabajo neto [kJ/kg], B rendimiento térmico [%], siempre dentro del dominio motor abierto.'),
        'fundamentos': (
            ('Objetivo termodinámico', 'Elegir una relación de compresión que optimice una magnitud claramente definida. '
             'El máximo de trabajo y el de rendimiento generalmente responden a necesidades de diseño diferentes.'),
            ('Hipótesis del modelo', 'Cada rp candidata se evalúa con el mismo ciclo cp(T), sin sustituirlo por una '
             'expresión analítica de γ constante. T1, T3, p1, ηc, ηt y δ siguen fijos.'),
            ('Procedimiento de cálculo paso a paso', '<ol><li>Delimitar la región motor: compresión, expansión, '
             'calor aportado y trabajo neto positivos, con estados dentro de 200–2000 K.</li>'
             '<li>Evaluar cómo wc y wt varían con rp: su diferencia define wnet(rp).</li>'
             '<li>Buscar A donde se anula la derivada del trabajo y comprobar máximo interior.</li>'
             '<li>Buscar B usando la derivada del cociente wnet/qin y verificar máximo interior.</li>'
             '<li>Si el valor límite solo se aproxima en una frontera excluida, informar <em>supremo</em> '
             'sin inventar una rp operativa.</li></ol>'),
            ('Interpretación física', 'A busca kJ/kg máximos; B busca porcentaje de calor convertido en trabajo. '
             'Subir rp aumenta la compresión y cambia la expansión, por lo que puede perjudicar trabajo neto '
             'aunque cambie favorablemente η. Una gráfica con escalas distintas no permite comparar '
             'alturas de trabajo [kJ/kg] y rendimiento [%].'),
            ('Limitaciones y conclusiones', 'El dominio motor es abierto: alcanzar matemáticamente un límite '
             'no equivale a poder operar allí. El óptimo depende del modelo educativo y las seis condiciones '
             'fijas, no determina por sí solo el diseño completo de un motor.'),
        ),
    },
    'sensibilidad': {
        'uso': ('Hacemos un barrido <em>one factor at a time</em> (OFAT): escogemos una de las siete entradas '
                'y probamos valores entre un mínimo y un máximo. Los otros seis parámetros permanecen fijos. '
                'Las curvas muestran trabajo, rendimiento y trabajos de turbomáquinas solo donde el ciclo es motor.'),
        'fundamentos': (
            ('Objetivo termodinámico', 'Conocer cuánto cambia el comportamiento ante una variación controlada '
             'de una entrada y detectar qué intervalos dejan de ser físicamente operativos.'),
            ('Hipótesis del modelo', 'En un estudio OFAT se mantiene fijo el resto del caso. '
             'Si no se escoge rp, tampoco se reoptimiza en cada muestra: las curvas no son trayectorias A/B.'),
            ('Procedimiento de cálculo paso a paso', '<ol><li>Elegir parámetro y unidad, límites y número de muestras '
             '(3–201).</li><li>Construir valores equiespaciados y resolver los cuatro estados con cp(T) '
             'para cada muestra.</li><li>Etiquetar motor, no motor, fuera de rango o error; '
             'dejar huecos donde no hay prestación válida.</li><li>Para el caso base, aproximar '
             'dY/dx por diferencias finitas y comprobar estabilidad al reducir el paso.</li>'
             '<li>Normalizar, cuando sea posible, S=(x/Y)·dY/dx, adimensional.</li></ol>'),
            ('Interpretación física', 'Si S≈1, un +1 % pequeño en x sugiere +1 % relativo en Y cerca del '
             'punto estudiado, <strong>no</strong> +1 punto porcentual. Los huecos de las curvas no '
             'representan ceros: pueden indicar ciclos no motores o estados no calculables.'),
            ('Limitaciones y conclusiones', 'La sensibilidad local depende de la referencia y no equivale '
             'a una ley universal; OFAT no informa sobre interacciones entre parámetros. '
             'Un paso inestable o denominador nulo deja S sin definir.'),
        ),
    },
    'mapa': {
        'uso': ('Exploramos dos entradas simultáneas: rp (eje horizontal, espaciado logarítmico) '
                'y T3 [K] (eje vertical, espaciado lineal). Se fijan T1, p1, ηc, ηt y δ. '
                'Cada celda tiene un ciclo calculado; su color solo representa prestación si el punto es motor.'),
        'fundamentos': (
            ('Objetivo termodinámico', 'Visualizar interacciones entre relación de compresión y temperatura '
             'de entrada a turbina; comparar zonas de mayor trabajo específico y mayor rendimiento.'),
            ('Hipótesis del modelo', 'Cinco parámetros físicos fijos. Cada pareja (rp,T3) se evalúa por separado '
             'con el mismo solucionador cp(T) y la misma clasificación motora.'),
            ('Procedimiento de cálculo paso a paso', '<ol><li>Definir rp mínima/máxima y T3 mínima/máxima, '
             'más resolución de 5–51 nodos por eje.</li><li>Construir columnas en ln(rp), '
             'filas en T3; evaluar cada combinación.</li><li>Clasificar celdas motoras, no motoras, '
             'fuera del rango térmico, inválidas o con error numérico.</li><li>Aplicar dos escalas '
             'de color independientes para wnet [kJ/kg] y ηtérmica [%] solo sobre celdas motoras.</li>'
             '<li>Señalar los mejores nodos discretos. Comparar con A/B de 2C, '
             'calculados para una única T3 de referencia cuando proceda.</li></ol>'),
            ('Interpretación física', 'Una celda gris no significa rendimiento cero. '
             'Los tonos de dos mapas distintos no se pueden comparar directamente sin mirar sus barras. '
             'Los máximos observados dependen del dominio y el tamaño de la malla; '
             'un óptimo continuo es un problema matemático diferente.'),
            ('Limitaciones y conclusiones', 'Un mapa termodinámico rp–T3 <strong>no</strong> '
             'es un mapa operativo real de compresor o turbina, que incluiría caudal, velocidad, '
             'líneas de bombeo, etc. Las fronteras y celdas no inventan puntos operativos.'),
        ),
    },
    'segunda_ley': {
        'uso': ('Utilizamos los cuatro estados del mismo ciclo para estudiar sus irreversibilidades. '
                'El ambiente de referencia tiene T0 [K] y p0 [kPa] independientes de T1/p1. '
                'Calculamos entropía, exergía física, destrucción en turbomáquinas y rendimientos exergéticos '
                'cuando son aplicables; no se simula combustión química.'),
        'fundamentos': (
            ('Objetivo termodinámico', 'La primera ley asegura que la energía se conserva. La segunda '
             'revela que las irreversibilidades destruyen parte de su potencial de convertirse en trabajo.'),
            ('Hipótesis del modelo', 'Compresor y turbina adiabáticos, estacionarios, '
             'aire ideal de composición fija, energía cinética y potencial despreciables. '
             'No se modelan fuentes de calor externas ni exergía química.'),
            ('Procedimiento de cálculo paso a paso', '<ol><li>Leer s1…s4 y h1…h4 directamente del ciclo cp(T).</li>'
             '<li>Evaluar h0=h(T0), s0=s(T0,p0), y exergía física e=(h−h0)−T0(s−s0).</li>'
             '<li>Generaciones de compresor s2−s1 y turbina s4−s3, ambas no negativas '
             'para equipos pasivos adiabáticos válidos.</li><li>Gouy–Stodola: eD,c=T0(s2−s1), '
             'eD,t=T0(s4−s3); contrastar también wc−(e2−e1) y (e3−e4)−wt.</li>'
             '<li>Solo con denominadores positivos y ciclo motor: ηex,c=(e2−e1)/wc, '
             'ηex,t=wt/(e3−e4).</li></ol>'),
            ('Interpretación física', 'Exergía es trabajo útil <em>potencial</em> respecto al ambiente. '
             'Una mayor generación de entropía supone mayor destrucción T0·sgen. '
             'Cambiar solo p0 desplaza exergías absolutas de los estados pero no sus diferencias; '
             'cambiar T0 sí modifica la destrucción atribuida al mismo proceso.'),
            ('Limitaciones y conclusiones', 'Solo se suman las destrucciones de compresor y turbina. '
             'No se puede obtener la destrucción total del ciclo con s3−s2 o s1−s4 sin '
             'considerar transferencia de entropía con las fuentes térmicas. '
             'Tampoco se define un rendimiento exergético global sin recurso exergético externo.'),
        ),
    },
    'informes': {
        'uso': ('Este apartado consulta los HTML conservados del simulador histórico, '
                'sin recalcularlos. Comprueba el modelo, la fecha, los parámetros y el commit '
                'antes de comparar cualquier magnitud con un estudio cp(T).'),
        'fundamentos': (
            ('Objetivo', 'Guardar trazabilidad permite reconstruir qué parámetros y qué modelo '
             'se usaron para generar un resultado, sin atribuirle el significado de una medición.'),
            ('Cómo leerlos', 'Identifica el modelo de gas perfecto en los informes antiguos. '
             'Lee unidades, supuestos, puntos motores y marcas de disponibilidad antes de comparar.'),
            ('Procedimiento', 'Abre el informe desde el historial y conserva una copia HTML si deseas '
             'estudiarlo; no se transforman automáticamente sus números a propiedades variables.'),
            ('Interpretación', 'Un valor calculado bajo cp constante puede diferir del modelo cp(T) '
             'sin que ninguno represente por sí mismo un ensayo experimental.'),
            ('Limitaciones y conclusiones', 'El dashboard cp(T) muestra sus estudios en pantalla '
             'pero todavía no crea informes cp(T). Los documentos históricos siguen siendo '
             'archivos de solo lectura y no se reetiquetan.'),
        ),
    },
    'ayuda': {
        'uso': ('Empieza por Simulación para fijar condiciones físicas; usa Resultados para entender '
                'balances, Optimización para comparar A/B, Sensibilidad y Mapa para explorar '
                'entradas y Segunda ley para irreversibilidades. Todas las secciones comparten la misma física.'),
        'fundamentos': (
            ('Variables y unidades', 'Temperaturas absolutas en K; presiones absolutas en kPa; '
             'h, trabajo y exergía en kJ/kg; cp en J/(kg·K); entropía en kJ/(kg·K); '
             'ηc, ηt, δ y rp adimensionales. δ=0,05 significa 5 %.'),
            ('Hipótesis', 'Aire ideal con cp(T), gamma(T) y mezcla fija. Los resultados son '
             'específicos por kg de aire, sin caudal, combustión química o empuje.'),
            ('Cómo navegar', 'Selecciona una sección en la barra lateral y alterna sus pestañas '
             'de configuración/fundamentos. Puedes abrir las gráficas mediante «Ampliar» '
             'y cerrarlas con Escape o el botón.'),
            ('Interpretación', 'Compara magnitudes solo con las mismas unidades y supuestos. '
             'No motor, fuera de rango y supremo abierto son situaciones distintas; '
             '«No disponible» no significa valor cero.'),
            ('Límites y conclusiones', 'El software se ha verificado mediante casos y balances internos; '
             'no constituye una validación experimental de un motor real. '
             'Profundiza en cada sección antes de interpretar resultados.'),
        ),
    },
}


def _tarjeta(titulo, cuerpo):
    """Una tarjeta HTML de texto educativo estático, sin datos de usuario."""
    return (f'<article class="card edu-deep-block"><h3>{escape(titulo)}</h3>'
            f'<div class="edu-deep-text">{cuerpo}</div></article>')


def construir_educacion_cp():
    """Devuelve dict seccion→{uso, fundamentos}, HTML propio seguro para Jinja."""
    return {seccion: {
        'uso': _tarjeta('Qué vamos a hacer', item['uso']),
        'fundamentos': ('<div class="edu-deep-grid">'
                        + ''.join(_tarjeta(titulo, contenido)
                                  for titulo, contenido in item['fundamentos'])
                        + '</div>'),
    } for seccion, item in CONTENIDOS.items()}
