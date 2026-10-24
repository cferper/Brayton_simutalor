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


# Los bloques teóricos extensos se leen de forma secuencial y a una sola columna.
# HTML de autoría controlada: subíndices, fórmulas y listas permanecen legibles.
CONTENIDOS = {
    'simulacion': {
        'uso': ('Definimos las condiciones de entrada de un Brayton abierto idealizado con aire de composición fija. '
                'El ciclo recorre cuatro estados: 1 antes de compresor, 2 después de compresor, '
                '3 antes de turbina y 4 después de turbina. Introduce siete magnitudes: '
                'temperaturas T1/T3 [K], presión p1 [kPa], rp=p2/p1 [−], ηc/ηt [fracción] y δ [fracción]. '
                'El botón Simulación calcula los estados; después puedes estudiar diseños y pérdidas en las otras secciones.'),
        'fundamentos': (
            ('1 · Contexto: qué es un ciclo Brayton',
             '<p>Una turbina de gas comprime aire, lo calienta y lo expande para obtener trabajo. '
             'El <strong>ciclo Brayton</strong> es el modelo termodinámico de esta secuencia; permite estudiar '
             'la energía necesaria para comprimir y la recuperada en la turbina. En propulsión aeronáutica '
             'constituye una base para entender turborreactores y turbofanes, pero este programa '
             '<strong>no calcula empuje</strong>, caudales, velocidades de salida ni prestaciones de una aeronave.</p>'
             '<p>Se usan cuatro estados: <strong>1</strong> entrada al compresor; <strong>2</strong> salida del '
             'compresor; <strong>3</strong> entrada a la turbina después del aporte térmico; '
             '<strong>4</strong> salida de la turbina. La numeración permite asociar cada componente con '
             'dos estados y escribir balances en sus extremos.</p>'),
            ('2 · Los cuatro procesos y su idealización',
             '<ol><li><strong>1→2, compresión:</strong> se eleva la presión empleando trabajo de eje. '
             'El compresor se trata como adiabático, pero admite irreversibilidades.</li>'
             '<li><strong>2→3, aporte térmico:</strong> aumenta la entalpía hasta T3. '
             'Se representa una pérdida de presión mediante δ; no se modelan reacciones químicas.</li>'
             '<li><strong>3→4, expansión:</strong> la turbina extrae trabajo al reducir la presión, '
             'con rendimiento isentrópico propio.</li>'
             '<li><strong>4→1, cierre del balance:</strong> se contabiliza un rechazo de calor equivalente '
             'para comparar estados. En una turbina de gas abierta real, el fluido sale al ambiente: '
             'la unión 4→1 <em>no</em> es una conducción física de retorno del mismo aire.</li></ol>'),
            ('3 · Gas ideal no significa cp constante',
             '<p>La ley de estado <strong>p·v=R·T</strong> sigue siendo válida para un gas ideal, '
             'aunque su capacidad calorífica cambie con T. Es otra hipótesis distinta afirmar '
             'que cp y γ tienen un valor fijo para cualquier temperatura. En el nuevo modelo '
             'se usa aire seco de composición molar fija (78 % N₂, 21 % O₂ y 1 % Ar), '
             'con correlaciones térmicas integradas en el intervalo 200–2000 K.</p>'
             '<p>Se calcula <strong>cp(T)</strong> [J/(kg·K)], '
             '<strong>h(T)</strong> [kJ/kg] y <strong>s(T,p)</strong> [kJ/(kg·K)]. '
             'Las funciones de h y s son diferencias respecto a referencias convencionales; '
             'las diferencias entre estados no dependen de escoger otro cero. '
             'El cociente γ(T)=cp(T)/(cp(T)−R) se informa para entender el comportamiento del aire, '
             'pero no se reemplaza toda la evolución por un único γ.</p>'),
            ('4 · La compresión real frente a la isentrópica',
             '<p>Un proceso <em>isentrópico</em> conserva la entropía específica. '
             'Se imagina primero la salida 2s que alcanzaría un compresor reversible y adiabático '
             'con las mismas presiones de entrada y salida. El compresor real necesita más trabajo '
             'porque la irreversibilidad provoca una elevación adicional de entalpía.</p>'
             '<p class="edu-equation">s(T₂s,p₂)=s(T₁,p₁); '
             'ηc=(h₂s−h₁)/(h₂−h₁).</p>'
             '<p>La eficiencia ηc es un cociente <strong>de saltos de entalpía</strong>, no el rendimiento '
             'térmico del ciclo. Con ηc=1, T2 coincide con T2s. Cuando ηc disminuye, para el mismo '
             'salto de presión el compresor tiende a consumir más trabajo específico.</p>'),
            ('5 · La expansión real y la pérdida de presión',
             '<p>Para la turbina se construye el estado 4s de expansión reversible y adiabática '
             'hasta p4. La máquina real entrega menos trabajo de eje que la ideal para esas '
             'presiones: el rendimiento ηt mide cuánto de la caída entálpica isentrópica se aprovecha.</p>'
             '<p class="edu-equation">s(T₄s,p₄)=s(T₃,p₃); '
             'ηt=(h₃−h₄)/(h₃−h₄s).</p>'
             '<p>La pérdida de presión entre 2 y 3 se representa con '
             '<strong>p3=p2(1−δ)</strong>. Un δ mayor reduce la presión disponible para expandir '
             'si se mantienen las demás entradas. Este modelo incorpora dicha pérdida '
             'en las presiones y estados; no modela por separado una cámara de combustión química.</p>'),
            ('6 · Qué calcula realmente el solucionador',
             '<ol><li>Valida las siete entradas y establece p2=p1·rp, p3=p2(1−δ), p4=p1.</li>'
             '<li>Para 2s invierte la función de entropía térmica con <strong>bisección</strong>, '
             'resolviendo s°(T2s)−s°(T1)=R·ln(rp).</li>'
             '<li>Halla h2=h1+(h2s−h1)/ηc e invierte h(T) por bisección para obtener T2.</li>'
             '<li>Determina T4s mediante s°(T4s)−s°(T3)=R·ln(p4/p3), '
             'y luego h4=h3−ηt(h3−h4s) para recuperar T4.</li>'
             '<li>Reevalúa h y s en los cuatro estados, calcula balances y clasifica la viabilidad.</li></ol>'
             '<p>Las raíces se buscan <strong>dentro de 200–2000 K</strong>; no se extrapolan '
             'las funciones de propiedades ni se usan expresiones de potencia con γ constante.</p>'),
            ('7 · Ejemplo de presiones, sin simular un caso',
             '<p>Supón, solo para seguir el razonamiento, p1=100 kPa, rp=10 y δ=0,05. '
             'Entonces p2=1000 kPa y p3=950 kPa, mientras p4=100 kPa. '
             'El compresor realiza un salto de presión 100→1000 y la turbina '
             'expande entre 950→100. Es un <strong>ejemplo algebraico</strong> de presiones, '
             'no un resultado numérico de temperaturas, trabajos o rendimiento.</p>'
             '<aside class="edu-insight"><strong>Idea clave:</strong> primero se fijan las '
             'presiones y los estados de referencia; después las eficiencias determinan '
             'las entalpías de salida reales.</aside>'),
            ('8 · Qué condiciones limitan las conclusiones',
             '<p>Un conjunto de entradas numéricamente válido puede describir un ciclo '
             'que no produce trabajo neto. El programa exige para clasificarlo como motor '
             'una compresión y una expansión efectivas, calor aportado y trabajo neto positivos, '
             'y ausencia de generación de entropía negativa significativa en ambas '
             'turbomáquinas, respetando tolerancias numéricas. También impone el intervalo '
             'térmico 200–2000 K a los estados reales e isentrópicos.</p>'
             '<p>El resultado sigue siendo <strong>específico por kilogramo de aire</strong>, '
             'sin caudal, emisiones, geometría, combustión real, regeneración ni empuje. '
             'La clasificación motora del programa no equivale a certificar una máquina física.</p>')),
    },
    'resultados': {
        'uso': ('Consultamos qué estados, trabajos y calores resultan de las siete entradas. Las propiedades se evalúan '
                'en cada temperatura; ηt y ηc son los parámetros de los equipos, no el rendimiento térmico del ciclo. '
                'La tabla reúne T, p, cp(T), γ(T), h y s para los cuatro estados; el diagrama T–s se explica por separado.'),
        'fundamentos': (
            ('1 · Por qué aplicamos la primera ley',
             '<p>La primera ley expresa la <strong>conservación de la energía</strong>. '
             'Para una máquina de flujo estacionario, la energía puede entrar o salir '
             'en forma de trabajo de eje, calor y energía transportada por la corriente. '
             'En los componentes aquí estudiados se desprecian los cambios de energía '
             'cinética y potencial, de modo que los saltos de entalpía describen '
             'la parte térmica y de flujo de la energía específica del aire.</p>'
             '<p>El objetivo no es obtener simplemente una temperatura final: '
             'queremos conocer cuánto consume el compresor, cuánto produce la turbina '
             'y qué balance energético conjunto aparece por kilogramo de aire.</p>'),
            ('2 · Energía, calor, trabajo y entalpía no son sinónimos',
             '<p>La energía es una propiedad general; el <strong>calor</strong> es transferencia '
             'de energía por diferencia de temperatura y el <strong>trabajo</strong> es '
             'transferencia mediante fuerzas y desplazamientos, incluido un eje giratorio. '
             'La <strong>entalpía</strong> h=u+p·v incluye la energía interna específica '
             'y el trabajo de flujo asociado al paso de masa por un sistema abierto.</p>'
             '<p>Para aire ideal de composición fija, h depende de T. Si cp(T) varía, '
             'la diferencia entre dos temperaturas se obtiene integrando '
             'cp(T)·dT, no multiplicando una diferencia de temperatura por un cp fijo. '
             'El programa evalúa directamente la función h(T) ya integrada.</p>'),
            ('3 · Signos y balances de las turbomáquinas',
             '<p>Se adopta la convención de <strong>trabajos positivos como magnitudes '
             'consumidas por el compresor y entregadas por la turbina</strong> cuando '
             'funcionan en su sentido nominal. Para un compresor adiabático, '
             'la corriente sale con más entalpía; para la turbina, con menos.</p>'
             '<p class="edu-equation">w<sub>c</sub>=h₂−h₁ [kJ/kg]; '
             'w<sub>t</sub>=h₃−h₄ [kJ/kg].</p>'
             '<p>Estos signos se refieren a los equipos en modo motor. Si un caso algebraicamente '
             'resoluble da un signo incompatible, no se convierte en prestación '
             'operativa simplemente tomando un valor absoluto; se informa el diagnóstico.</p>'),
            ('4 · Trabajo neto, aporte de calor y rendimiento',
             '<p>El trabajo disponible del conjunto se obtiene restando al trabajo '
             'de turbina el consumido por el compresor. El modelo representa '
             'el aporte térmico entre 2 y 3 y el rechazo equivalente entre 4 y 1.</p>'
             '<p class="edu-equation">w<sub>neto</sub>=w<sub>t</sub>−w<sub>c</sub>; '
             'q<sub>in</sub>=h₃−h₂; q<sub>out</sub>=h₄−h₁.</p>'
             '<p>Solo para un <strong>ciclo motor viable</strong>, con aporte de calor positivo, '
             'el rendimiento térmico se define como '
             '<strong>η<sub>térmica</sub>=w<sub>neto</sub>/q<sub>in</sub></strong>. '
             'No es ηc ni ηt (eficiencias isentrópicas de máquina), '
             'ni un rendimiento exergético.</p>'),
            ('5 · Comprobación de energía y error numérico',
             '<p>La igualdad <strong>w<sub>neto</sub>=q<sub>in</sub>−q<sub>out</sub></strong> '
             'se deduce algebraicamente de las mismas cuatro entalpías. El programa '
             'evalúa el residuo de esa identidad: debería ser próximo a cero '
             'dentro de la precisión de punto flotante. Un residuo pequeño indica '
             'consistencia del cálculo, pero <em>no</em> valida el modelo contra ensayos.</p>'
             '<ol><li>Resolver estados reales e isentrópicos.</li>'
             '<li>Calcular h y s en cada estado.</li>'
             '<li>Evaluar wc, wt, qin y qout por sus saltos entálpicos.</li>'
             '<li>Comprobar el balance y, si es motor, obtener el rendimiento.</li></ol>'),
            ('6 · Cómo interpretar la tabla y el diagrama T–s',
             '<p>La tabla muestra para cada estado T [K], p [kPa], cp(T) '
             '[J/(kg·K)], γ(T), h [kJ/kg] y s [kJ/(kg·K)]. '
             'Comparar cp o γ entre estados permite apreciar la diferencia '
             'frente al gas caloríficamente perfecto. Las entalpías son relativas '
             'a 298,15 K; las entropías también usan 100 kPa como referencia.</p>'
             '<p>En el plano T–s, T aumenta hacia arriba y la entropía '
             'hacia la derecha. Una compresión o expansión isentrópica '
             'se caracteriza por entropía constante, mientras que la '
             'irreversibilidad adiabática tiende a aumentarla. '
             '<strong>Solo los cuatro puntos corresponden a estados calculados:</strong> '
             'las líneas discontinuas que los unen son esquemáticas, '
             'no trayectorias integradas del fluido.</p>'),
            ('7 · Ejemplo ilustrativo de un balance',
             '<p>Para practicar la aritmética, toma cuatro entalpías ficticias '
             'h1=0, h2=300, h3=1300 y h4=700 kJ/kg. Se obtiene '
             'wc=300, wt=600, wnet=300, qin=1000 y qout=700 kJ/kg. '
             'Así se comprueba que <strong>600−300=1000−700=300</strong>, '
             'y que el rendimiento del balance sería 300/1000=30 % '
             '<em>si</em> los estados formasen un ciclo motor físicamente admisible.</p>'
             '<aside class="edu-insight">Ejemplo de <strong>contabilidad energética</strong>, '
             'no salida de resolver_ciclo ni verificación de las restricciones de estados.</aside>'),
            ('8 · Resultados no motores y alcance físico',
             '<p>El solucionador puede producir T2 y T4 reales y, aun así, '
             'detectar ausencia de compresión/expansión nominal, calor aportado '
             'insuficiente, trabajo no positivo o comportamiento incompatible '
             'con la generación de entropía. En tal caso mantiene los valores '
             'como <strong>diagnóstico</strong>, sin publicar rendimiento '
             'de motor. No confundas “calculable” con “operable”.</p>'
             '<p>Todas las energías se expresan en <strong>kJ/kg</strong> '
             'porque el modelo no conoce el caudal másico. '
             'Para convertir un trabajo específico en potencia de eje '
             'sería necesario un caudal [kg/s] y otras hipótesis: '
             'kJ/kg × kg/s = kW. El programa no estima esa potencia.</p>')),
    },
    'optimizacion': {
        'uso': ('Buscamos la mejor relación de compresión rp para dos objetivos distintos. '
                'Se mantienen fijos T1, T3, p1, ηc, ηt y δ; el algoritmo solo modifica rp. '
                'A maximiza trabajo neto [kJ/kg], B rendimiento térmico [%], siempre dentro del dominio motor abierto. '
                'Pulsa «Calcular máximos» y compara la rp y el tipo de resultado de las fichas A y B. '
                'Puede aparecer un supremo que no sea un punto operativo.'),
        'fundamentos': (
            ('1 · Qué significa optimizar un ciclo',
             '<p>Optimizar consiste en elegir una variable de diseño para que una '
             'prestación sea la mayor posible <strong>dentro de condiciones admisibles</strong>. '
             'En este estudio la variable es la relación de compresión '
             '<strong>rp=p2/p1</strong>, sin unidades. Las otras seis entradas físicas '
             '(T1, T3, p1, ηc, ηt y δ) permanecen constantes.</p>'
             '<p>La relación de compresión no es una medida de eficiencia. '
             'Al aumentarla suele elevarse el trabajo exigido al compresor '
             'y también cambia el salto de expansión de la turbina. '
             'Por eso no existe una regla válida que diga “cuanto mayor rp, mejor ciclo”.</p>'),
            ('2 · Dos criterios de diseño diferentes',
             '<p>El criterio <strong>A</strong> maximiza '
             'w<sub>neto</sub>=w<sub>t</sub>−w<sub>c</sub> [kJ/kg]: '
             'interesa cuando importa el trabajo específico obtenido del fluido. '
             'El criterio <strong>B</strong> maximiza '
             'η<sub>térmica</sub>=w<sub>neto</sub>/q<sub>in</sub> [fracción]: '
             'interesa cuando importa qué proporción del calor aportado '
             'se transforma en trabajo neto.</p>'
             '<p>El numerador y el denominador del rendimiento cambian con rp. '
             'Por ello el máximo de una diferencia energética y el máximo de '
             'un cociente <strong>no tienen por qué coincidir</strong>. '
             'Elegir entre A y B exige plantear primero la necesidad física, '
             'no escoger automáticamente el punto de mayor valor en una gráfica.</p>'),
            ('3 · El dominio motor y sus fronteras',
             '<p>Antes de buscar máximos se determinan relaciones de compresión '
             'para las que el sentido de funcionamiento es correcto, existe '
             'aporte y rechazo de calor compatibles, los estados permanecen '
             'entre 200 y 2000 K y el trabajo neto es positivo. '
             'El optimizador acota el intervalo con restricciones de entropía, '
             'entalpía y temperaturas, y localiza si es necesario los ceros '
             'de w<sub>neto</sub>.</p>'
             '<p>Se trabaja con un <strong>dominio abierto</strong>: sus límites '
             'no son estados motores operativos. En una frontera podría '
             'anularse el trabajo, desaparecer la expansión o alcanzarse '
             'un límite del modelo. No debe dibujarse allí un óptimo '
             'como si fuera un ciclo viable.</p>'),
            ('4 · Qué resuelve exactamente el algoritmo A',
             '<p>El código trabaja con <strong>x=ln(rp)</strong> para que las '
             'presiones muy diferentes se exploren de forma estable. '
             'Con R en kJ/(kg·K), obtiene la derivada del trabajo:</p>'
             '<p class="edu-equation">dw<sub>neto</sub>/dx = '
             'R·(ηt·T₄s − T₂s/ηc).</p>'
             '<p>Evalúa su signo cerca de ambos límites. Si cambia de positivo '
             'a negativo, encuentra la raíz mediante <strong>bisección</strong> '
             'y comprueba que el trabajo es positivo. Si no aparece una raíz '
             'interior, no fabrica un máximo: la prestación mayor puede '
             'quedar únicamente como un límite no alcanzado. '
             'El solucionador cp(T) vuelve a evaluar los estados de cada '
             'rp candidata; la derivada no usa un γ constante.</p>'),
            ('5 · Cómo obtiene el criterio B',
             '<p>El máximo de η=w<sub>neto</sub>/q<sub>in</sub> '
             'requiere estudiar la derivada de un <strong>cociente</strong>, '
             'no reutilizar la condición de A. El código calcula '
             'un numerador proporcional al signo de dη/dx:</p>'
             '<p class="edu-equation">F(x)=R·ηt·T₄s·q<sub>in</sub> '
             '− (R·T₂s/ηc)·q<sub>out</sub>.</p>'
             '<p>Con q<sub>in</sub> y q<sub>out</sub> positivos en su dominio, '
             'el algoritmo aprovecha la monotonía de F. '
             'Si F cambia de positivo a negativo, usa bisección '
             'para encontrar el máximo interior B; en caso contrario '
             'informa un <em>supremo de frontera</em>. '
             'A y B se buscan independientemente; B no sale de leer A.</p>'),
            ('6 · Máximo alcanzado, supremo y gráfica',
             '<p>Un <strong>máximo interior</strong> corresponde a un punto '
             'admisible cuya prestación supera a las cercanas. '
             'Un <strong>supremo</strong> es un valor límite al que '
             'pueden aproximarse puntos admisibles sin llegar a alcanzarlo. '
             'Matemáticamente son conceptos distintos, con consecuencias '
             'de diseño distintas. Si no hay dominio motor, ningún '
             'criterio produce un punto de funcionamiento.</p>'
             '<p>La gráfica presenta trabajo neto y rendimiento frente '
             'a rp con <strong>escalas verticales diferentes</strong>: '
             'un pico más alto en píxeles no demuestra que una prestación '
             'sea “mayor” que la otra. Comprueba las unidades y la etiqueta '
             'de cada eje al comparar las curvas.</p>'),
            ('7 · Ejemplo conceptual de decisiones',
             '<p>Imagina, solo como ilustración, una curva de trabajo '
             'que alcanza su máximo en una rp moderada. Al aumentar rp '
             'un poco más, el compresor exige más energía y el trabajo '
             'neto desciende. Mientras tanto, el rendimiento puede '
             'seguir mejorando si el calor aportado disminuye '
             'proporcionalmente más. Así puede aparecer B a la derecha de A.</p>'
             '<aside class="edu-insight"><strong>No son cifras calculadas:</strong> '
             'para conocer A y B del caso actual pulsa el botón de '
             'optimización y lee las relaciones de compresión y el tipo '
             'de extremo que devuelve el programa.</aside>'),
            ('8 · Supuestos, incertidumbre y límites',
             '<p>Las búsquedas numéricas emplean tolerancias y comprobaciones '
             'de signo; sus resultados son aproximaciones a máximos '
             'del <strong>modelo</strong>, no medidas de un motor. '
             'La búsqueda no se basa en tomar el mejor punto de una '
             'malla de la gráfica: esta sirve para visualizar las tendencias.</p>'
             '<p>El análisis fija T1, T3, p1, ηc, ηt y δ, y no modela '
             'límites de materiales, mapas reales de turbomáquinas, '
             'costes, combustible ni empuje. Un máximo termodinámico '
             'interior no garantiza que sea el diseño óptimo de '
             'una instalación aeroespacial completa.</p>'),
        ),
    },
    'sensibilidad': {
        'uso': ('Hacemos un barrido <em>one factor at a time</em> (OFAT): escogemos una de las siete entradas '
                'y probamos valores entre un mínimo y un máximo. Los otros seis parámetros permanecen fijos. '
                'Las curvas muestran trabajo, rendimiento y trabajos de turbomáquinas solo donde el ciclo es motor. '
                'Elige el parámetro y su intervalo, establece entre 3 y 201 muestras y ejecuta el análisis. '
                'Consulta los huecos, los recuentos de estados y la tabla de sensibilidad local.'),
        'fundamentos': (
            ('1 · Qué pregunta responde la sensibilidad',
             '<p>En ingeniería conviene saber si un resultado es muy sensible '
             'a una entrada: ¿cambia mucho el trabajo si cambia T3?, '
             '¿cuánto penaliza una turbina menos eficiente?, ¿qué pasa '
             'al introducir una pérdida de presión mayor? El análisis '
             'de sensibilidad explora la respuesta a pequeñas o grandes '
             'variaciones controladas de parámetros.</p>'
             '<p>Este apartado usa <strong>OFAT</strong> (<em>one factor at a time</em>): '
             'varía una sola de las siete entradas y mantiene las otras '
             'seis con sus valores de Simulación. Así se aísla el efecto '
             'condicional de ese factor, sin atribuir a él cambios '
             'simultáneos de otras condiciones.</p>'),
            ('2 · Qué significa variar cada entrada',
             '<ul><li><strong>T1 [K]:</strong> afecta a la compresión y al estado inicial.</li>'
             '<li><strong>T3 [K]:</strong> fija el nivel térmico disponible para la turbina.</li>'
             '<li><strong>rp [−]:</strong> modifica simultáneamente salto de compresión '
             'y expansión; puede cruzar el dominio motor.</li>'
             '<li><strong>p1 [kPa]:</strong> desplaza la escala absoluta de presiones; '
             'en este modelo ideal, fijadas T y relaciones de presión, no modifica '
             'los saltos de entalpía ni el rendimiento.</li>'
             '<li><strong>ηc, ηt [fracción]:</strong> representan pérdidas internas '
             'de compresor y turbina.</li>'
             '<li><strong>δ [fracción]:</strong> reduce p3 respecto a p2.</li></ul>'
             '<p>Ninguno de esos efectos garantiza una respuesta monótona '
             'para todos los valores: importa el punto base y la viabilidad física.</p>'),
            ('3 · Cómo se construye el barrido OFAT',
             '<p>El usuario elige parámetro, mínimo, máximo y número N '
             'de muestras (3–201). El programa distribuye valores '
             '<strong>linealmente</strong> entre ambos extremos, incluidos '
             'los límites, y sustituye solo la variable seleccionada '
             'en una copia de las siete entradas.</p>'
             '<p>En cada muestra se ejecuta <code>resolver_ciclo</code> con cp(T) '
             'y se conservan estados, trabajos, calor y posibles errores. '
             'Se clasifican puntos <strong>motor, no motor, fuera de rango, '
             'entrada inválida o error numérico</strong>. '
             'Las curvas de prestaciones representan solo motores, '
             'interrumpiéndose en puntos descartados; un hueco no '
             'es un valor cero ni una interpolación física.</p>'),
            ('4 · De la curva a una derivada local',
             '<p>Una curva amplia muestra tendencias; una <strong>derivada</strong> '
             'describe la pendiente en un valor x0. Para trabajo neto '
             'o rendimiento Y, el programa aproxima dY/dx mediante '
             'diferencias finitas alrededor del <strong>caso base</strong>, '
             'que puede estar en otra posición respecto al intervalo dibujado.</p>'
             '<p class="edu-equation">dY/dx ≈ [Y(x₀+h)−Y(x₀−h)]/(2h).</p>'
             '<p>Si un vecino sale del dominio motor, puede utilizar '
             'diferencia unilateral hacia adelante o atrás. Si no '
             'existen vecinos motores, la derivada no se publica. '
             'No se recalcula el óptimo A o B en cada muestra: '
             'OFAT y reoptimización son problemas distintos.</p>'),
            ('5 · Elasticidad o sensibilidad normalizada',
             '<p>Las derivadas de trabajo y rendimiento tienen unidades '
             'distintas según x. Para compararlas se introduce la '
             '<strong>sensibilidad normalizada</strong> o elasticidad:</p>'
             '<p class="edu-equation">S<sub>Y,x</sub>=(x₀/Y₀)·(dY/dx).</p>'
             '<p>Es adimensional si x0 y Y0 son no nulos. '
             'Con S&gt;0, pequeñas variaciones relativas de x y de Y '
             'tienen el mismo signo; con S&lt;0, signo contrario; '
             'S≈0 indica escasa respuesta <em>local</em>. '
             'No se puede normalizar cuando x0=0 o Y0≈0, '
             'ni publicar una sensibilidad operativa en un caso no motor.</p>'),
            ('6 · Paso numérico y confianza en la derivada',
             '<p>El valor de h afecta a la estimación: un paso enorme '
             'promedia un intervalo demasiado amplio; uno diminuto '
             'puede amplificar errores de redondeo. El programa '
             'establece por defecto h=0,001·max(|x0|,0,01) '
             'en las unidades de la variable estudiada.</p>'
             '<p>Calcula la elasticidad con ese paso y de nuevo con h/2. '
             'Si cambia el esquema central/unilateral o la diferencia '
             'entre ambas estimaciones supera el umbral implementado, '
             'la clasifica como <strong>inestable</strong> y no imprime '
             'una cifra aparentemente exacta. Esta es una comprobación '
             'de convergencia local, no una incertidumbre experimental.</p>'),
            ('7 · Ejemplo de interpretación porcentual',
             '<p>Supón que, para un punto motor ficticio, '
             'S<sub>w,T3</sub>=−0,5. Una subida pequeña del 2 % '
             'de T3 se asociaría, por aproximación lineal local, '
             'con una variación del trabajo de aproximadamente '
             '<strong>−1 % respecto a su valor inicial</strong>. '
             'No serían “−1 kJ/kg” ni “−1 punto porcentual”. '
             'El signo es ilustrativo: no describe una tendencia '
             'real calculada para el T3 de tu ciclo.</p>'
             '<aside class="edu-insight">Si Y es un rendimiento del 30 % '
             'y varía un +1 % <em>relativo</em>, pasa aproximadamente '
             'al 30,3 %, no al 31 %. Así se distinguen porcentaje '
             'relativo y puntos porcentuales.</aside>'),
            ('8 · Limitaciones que hay que recordar',
             '<p>OFAT no detecta cómo se combinan dos cambios, por '
             'ejemplo si mejorar ηc modifica la influencia de rp. '
             'Tampoco demuestra causalidad experimental ni da '
             'incertidumbres del modelo. Las regiones no motoras '
             'no se rellenan con curvas ficticias.</p>'
             '<p>Los rangos iniciales son <strong>sugerencias didácticas</strong>, '
             'no cotas universales de máquinas reales. '
             'Para comparar dos análisis hay que mantener consistentes '
             'unidades, punto de referencia y condiciones fijas; '
             'para estudiar interacciones de rp y T3 utiliza el '
             'Mapa de diseño, no infieras interacciones de OFAT.</p>'),
        ),
    },
    'mapa': {
        'uso': ('Exploramos dos entradas simultáneas: rp (eje horizontal, espaciado logarítmico) '
                'y T3 [K] (eje vertical, espaciado lineal). Se fijan T1, p1, ηc, ηt y δ. '
                'Cada celda tiene un ciclo calculado; su color solo representa prestación si el punto es motor. '
                'Introduce extremos de rp y T3, elige entre 5 y 51 puntos por eje y pulsa «Calcular mapa». '
                'Compara trabajo, rendimiento y los mejores nodos discretos de la malla.'),
        'fundamentos': (
            ('1 · Para qué sirve un mapa de diseño',
             '<p>En vez de cambiar una sola entrada, un mapa permite explorar '
             'dos factores a la vez. Aquí se estudian '
             '<strong>rp</strong> (relación de compresión) y '
             '<strong>T3 [K]</strong> (temperatura de entrada a turbina). '
             'Ambos influyen en el trabajo consumido por compresión, '
             'el trabajo obtenido de expansión y el calor necesario.</p>'
             '<p>El objetivo es identificar regiones donde el modelo '
             'predice puntos motores con más trabajo específico o mayor '
             'rendimiento. Se mantienen constantes T1, p1, ηc, ηt y δ. '
             'Las zonas encontradas pueden orientar una exploración '
             'de diseño, pero todavía no son restricciones de un '
             'componente aeronáutico real.</p>'),
            ('2 · De los intervalos a una malla bidimensional',
             '<p>Se fijan extremos mínimos/máximos y números de nodos '
             'independientes para rp y T3, entre 5 y 51 por eje. '
             'Cada pareja forma una <strong>celda o punto de evaluación</strong>. '
             'Por ejemplo, una malla 5×5 contiene 25 ciclos '
             'potenciales; no son 25 estados del mismo ciclo.</p>'
             '<p>La temperatura avanza a incrementos <strong>lineales</strong> '
             '(diferencia constante en kelvin); rp utiliza '
             '<strong>espaciado logarítmico</strong> (cociente constante). '
             'Este último distribuye mejor las muestras cuando se '
             'exploran valores de rp de órdenes de magnitud distintos. '
             'El programa limita la malla a 2601 evaluaciones '
             'para controlar el tiempo de respuesta.</p>'),
            ('3 · Qué calcula y clasifica cada celda',
             '<ol><li>Copiar las siete entradas físicas, sustituyendo '
             'solo rp y T3 por los valores de la celda.</li>'
             '<li>Resolver los cuatro estados con h(T) y s(T,p) mediante '
             'el mismo solucionador utilizado en Simulación.</li>'
             '<li>Clasificar como motor, calculable no motor, fuera '
             'de 200–2000 K, entrada inválida o error numérico.</li>'
             '<li>Guardar trabajo neto y rendimiento como '
             '<strong>prestaciones</strong> únicamente si el ciclo es motor.</li>'
             '<li>Calcular recuentos de estados y seleccionar los '
             'mejores puntos motores de la malla.</li></ol>'
             '<p>Una celda no motora no se dibuja como prestación '
             'nula: su estado se conserva para interpretar el mapa.</p>'),
            ('4 · Cómo leer los dos mapas de colores',
             '<p>El mapa A representa trabajo neto [kJ/kg]. '
             'El mapa B representa rendimiento térmico [%]. '
             'Para una celda motora, el color se obtiene de su '
             'valor y la barra de escala propia de esa magnitud. '
             'Las categorías de exclusión utilizan tonos neutros '
             'diferenciados, no los colores de una prestación válida.</p>'
             '<p>Un color “muy alto” en A no puede compararse '
             'directamente con el mismo color en B: son '
             '<strong>variables y escalas diferentes</strong>. '
             'Lee ejes, unidades, leyendas y marcas antes de interpretar '
             'cualquier zona como favorable. El tooltip de una celda '
             'permite relacionar su clasificación con su posición.</p>'),
            ('5 · Buscar regiones, no un punto mágico',
             '<p>Observa primero dónde aparece el dominio motor. '
             'Dentro de él, compara regiones extensas de prestaciones '
             'altas en lugar de basar toda la conclusión en una sola '
             'celda. El mapa ayuda a ver cómo puede cambiar el '
             'efecto de rp cuando cambia también T3: información '
             'que un barrido OFAT no ofrece directamente.</p>'
             '<p>El código selecciona el mejor nodo motor para '
             'cada magnitud mediante una comparación entre los '
             '<strong>valores que se han calculado</strong>. '
             'Al mover los extremos o el número de muestras, '
             'puede cambiar qué nodo resulta elegido aunque '
             'la termodinámica subyacente sea la misma.</p>'),
            ('6 · Malla discreta frente a óptimo continuo',
             '<p>Un máximo discreto solo afirma “el mejor entre '
             'estos puntos”. Una malla puede pasar a ambos lados '
             'de un máximo interior sin evaluarlo exactamente. '
             'Aumentar resolución suele revelar detalle, '
             'pero <strong>no convierte automáticamente</strong> '
             'el mejor nodo en la solución exacta ni elimina '
             'errores de modelo.</p>'
             '<p>Si se cumplen las condiciones, la interfaz añade '
             'una referencia independiente a los óptimos A/B '
             'del módulo 2C, calculados <strong>una sola vez</strong> '
             'para la T3 de referencia de Simulación. '
             'No se reoptimiza cada fila del mapa. Una marca '
             'solo aparece si el óptimo es interior y cae '
             'dentro de los ejes mostrados.</p>'),
            ('7 · Ejemplo de una malla pequeña',
             '<p>Como ejercicio de construcción, elige rp de 2 a 32 '
             'con cinco valores logarítmicamente equiespaciados: '
             '<strong>2, 4, 8, 16 y 32</strong>. '
             'Elige T3 de 1200 a 1600 K con cinco valores '
             'lineales: <strong>1200, 1300, 1400, 1500 y 1600 K</strong>. '
             'La combinación de ambas listas crea 25 celdas.</p>'
             '<aside class="edu-insight">Se describen los <strong>puntos de '
             'la malla</strong>, no sus prestaciones: algunos podrían '
             'ser no motores o no calculables según los otros '
             'cinco parámetros físicos. El programa los evalúa '
             'antes de asignar colores de prestaciones.</aside>'),
            ('8 · Diferencia respecto a un mapa de máquina real',
             '<p>Un mapa de compresor real suele relacionar caudal, '
             'relación de presiones, régimen de giro y eficiencia, '
             'con límites de bombeo o bloqueo. Un mapa real de '
             'turbina necesita variables de funcionamiento '
             'y geometría adicionales. El gráfico rp–T3 de esta '
             'aplicación <strong>no representa</strong> esas curvas.</p>'
             '<p>El aire conserva una composición ideal fija, '
             'las eficiencias son constantes durante la malla '
             'y no se modelan materiales, emisiones, masa del motor '
             'ni restricciones de caudal. Por tanto, el mapa '
             'apoya una reflexión termodinámica, no la elección '
             'final de un motor aeronáutico.</p>'),
        ),
    },
    'segunda_ley': {
        'uso': ('Utilizamos los cuatro estados del mismo ciclo para estudiar sus irreversibilidades. '
                'El ambiente de referencia tiene T0 [K] y p0 [kPa] independientes de T1/p1. '
                'Calculamos entropía, exergía física, destrucción en turbomáquinas y rendimientos exergéticos '
                'cuando son aplicables; no se simula combustión química. '
                'Introduce T0 y p0, ejecuta el análisis y consulta la tabla de estados, los balances '
                'independientes y el gráfico. La destrucción publicada solo cubre compresor y turbina.'),
        'fundamentos': (
            ('1 · Primera ley y segunda ley: dos preguntas',
             '<p>La <strong>primera ley</strong> comprueba que la energía '
             'de entrada, salida y acumulación se equilibra: '
             'el trabajo neto depende de las diferencias de entalpía. '
             'Sin embargo, esa conservación no dice cuánta de la '
             'energía <em>podría</em> convertirse en trabajo útil. '
             'Dos procesos pueden conservar exactamente la misma '
             'energía y destruir cantidades diferentes de potencial de trabajo.</p>'
             '<p>La <strong>segunda ley</strong> añade la dirección '
             'de los procesos: una transformación real genera '
             'entropía debido a irreversibilidades. En este modelo '
             'se estudian las que tienen lugar en las dos '
             'turbomáquinas adiabáticas, sin atribuir a los procesos '
             'de aporte o rechazo de calor un balance no modelado.</p>'),
            ('2 · Entropía y generación de entropía',
             '<p>La entropía s [kJ/(kg·K)] es una propiedad de '
             'estado útil para formular la segunda ley. '
             'En un proceso reversible adiabático permanece '
             'constante; en un equipo adiabático real pasivo '
             'en régimen estacionario, su generación es '
             '<strong>no negativa</strong>. '
             'La generación no es lo mismo que una simple '
             'diferencia de entropía en cualquier proceso: '
             'si existe transferencia de calor también puede '
             'transportarse entropía a través de los límites.</p>'
             '<p class="edu-equation">s(T,p)=s°(T)−R·ln(p/p<sub>ref</sub>); '
             's<sub>gen,c</sub>=s₂−s₁; '
             's<sub>gen,t</sub>=s₄−s₃.</p>'
             '<p>Las dos últimas igualdades se aplican aquí '
             'a <strong>compresor y turbina adiabáticos</strong>, '
             'por unidad de masa. No son una regla para '
             'la cámara donde se aporta calor.</p>'),
            ('3 · Qué es la exergía y por qué necesita ambiente',
             '<p>La exergía representa el <strong>trabajo útil '
             'potencial</strong> que una corriente podría proporcionar '
             'al alcanzar equilibrio con un ambiente especificado, '
             'con las hipótesis del modelo. Ese ambiente se fija '
             'con T0 [K] y p0 [kPa], independientes de la '
             'temperatura T1 y presión p1 del ciclo.</p>'
             '<p>El llamado <strong>estado muerto</strong> es '
             'la referencia de equilibrio térmico y mecánico '
             'con dicho ambiente. En él, la exergía física '
             'relativa es cero. Por eso el mismo estado de aire '
             'puede tener valores distintos de exergía '
             'al cambiar T0 o p0, aun cuando el ciclo '
             'termodinámico no se recalcule.</p>'),
            ('4 · Fórmula de exergía física específica',
             '<p>Para una corriente estacionaria sin cambios '
             'de energía cinética o potencial, se usa '
             'la exergía física de flujo:</p>'
             '<p class="edu-equation">e=(h−h₀)−T₀(s−s₀) [kJ/kg].</p>'
             '<p>h0=h(T0) y s0=s(T0,p0). La resta de entalpías '
             'mide el contenido energético relativo; '
             'el término T0·(s−s0) descuenta la parte '
             'condicionada por la segunda ley respecto '
             'del ambiente. Tanto h como s usan '
             'las mismas funciones cp(T) del ciclo.</p>'
             '<p>El programa calcula e1…e4 de esos estados '
             'sin resolver de nuevo el ciclo al cambiar '
             'solo T0 o p0; no incorpora exergía química.</p>'),
            ('5 · Gouy–Stodola: irreversibilidad en trabajo perdido',
             '<p>La generación de entropía permite cuantificar '
             'el potencial de trabajo destruido por '
             'irreversibilidades. El teorema de '
             '<strong>Gouy–Stodola</strong> establece '
             'la relación entre ambas magnitudes:</p>'
             '<p class="edu-equation">e<sub>D</sub>=T₀·s<sub>gen</sub> '
             '[kJ/kg].</p>'
             '<p>Para el compresor, eD,c=T0(s2−s1); '
             'para la turbina, eD,t=T0(s4−s3). '
             'Una irreversibilidad mayor se asocia '
             'con mayor destrucción cuando T0 es fijo. '
             'La referencia p0 puede alterar los '
             'valores absolutos de e, pero en este modelo '
             'no altera sus diferencias entre estados '
             'ni estas destrucciones; T0 sí las escala.</p>'),
            ('6 · Balances independientes de cada máquina',
             '<p>Además de calcular T0·sgen, el código '
             'verifica las destrucciones mediante balances '
             'de exergía de equipos adiabáticos. '
             'Se utiliza trabajo de compresor absorbido '
             'wc positivo y trabajo de turbina entregado wt positivo:</p>'
             '<p class="edu-equation">Compresor: '
             'e<sub>D,c</sub>=w<sub>c</sub>−(e₂−e₁).<br>'
             'Turbina: e<sub>D,t</sub>=(e₃−e₄)−w<sub>t</sub>.</p>'
             '<p>El <strong>residuo</strong> resta cada '
             'balance alternativo menos T0·sgen. '
             'Un residuo próximo a cero demuestra '
             'coherencia algebraica y numérica entre '
             'dos expresiones del mismo modelo; '
             'no significa que se haya medido '
             'experimentalmente la exergía de un motor.</p>'),
            ('7 · Rendimientos exergéticos e interpretación',
             '<p>El rendimiento exergético de una '
             'turbomáquina compara su <strong>efecto útil</strong> '
             'con el recurso exergético consumido. '
             'El compresor emplea trabajo para aumentar '
             'la exergía de la corriente; la turbina '
             'convierte parte de la caída de exergía '
             'en trabajo de eje.</p>'
             '<p class="edu-equation">η<sub>ex,c</sub>=(e₂−e₁)/w<sub>c</sub>; '
             'η<sub>ex,t</sub>=w<sub>t</sub>/(e₃−e₄).</p>'
             '<p>Solo se publican si el ciclo es motor '
             'y los balances, signos y denominadores '
             'son físicamente consistentes. '
             'No confundas estas eficiencias de '
             '<strong>componente</strong> con '
             'η<sub>térmica</sub>=wnet/qin, '
             'ni con un rendimiento exergético global, '
             'que aquí no está definido.</p>'),
            ('8 · Ejemplo y límites de la suma parcial',
             '<p>Ejemplo aritmético independiente: con '
             'T0=300 K y sgen=0,020 kJ/(kg·K) '
             'en una máquina, Gouy–Stodola da '
             '<strong>eD=6 kJ/kg</strong>. '
             'Ese valor ilustra unidades y significado; '
             'no corresponde a una ejecución particular '
             'de este simulador.</p>'
             '<aside class="edu-insight"><strong>Límite esencial:</strong> '
             'la suma publicada eD,c+eD,t cubre '
             '<em>solo compresor y turbina adiabáticos</em>. '
             'No es la destrucción de exergía total '
             'del ciclo. No se calculan exergía química, '
             'generación de entropía en los intercambios '
             'de calor ni rendimiento exergético global.</aside>'
             '<p>Una generación negativa significativa '
             'o un residuo que supere la tolerancia '
             'numérica se comunica como inconsistencia. '
             'Pequeños negativos debidos al redondeo '
             'se toleran bajo un umbral declarado.</p>'),
        ),
    },
    'informes': {
        'uso': ('Este apartado consulta los HTML conservados del simulador histórico, '
                'sin recalcularlos. Comprueba el modelo, la fecha, los parámetros y el commit '
                'antes de comparar cualquier magnitud con un estudio cp(T). '
                'No es necesario introducir parámetros: selecciona un informe y utiliza «Ver archivo» '
                'o «Descargar HTML» si necesitas conservarlo. '
                'Actualmente el nuevo simulador no genera informes cp(T).'),
        'fundamentos': (
            ('1 · Qué debe permitir un informe reproducible',
             '<p>Un informe técnico útil no es solo una tabla final: debe '
             'permitir saber <strong>qué caso</strong> se resolvió y '
             '<strong>cómo</strong> se obtuvo. Para repetir una simulación '
             'hacen falta las entradas, sus unidades, la versión del '
             'modelo, las hipótesis y el estado de los cálculos. '
             'También conviene conservar identificadores de '
             'versión —por ejemplo, un commit Git— que permitan '
             'relacionar los resultados con el código que los produjo.</p>'),
            ('2 · Interpretar los documentos históricos',
             '<p>Los HTML del historial pertenecen al simulador '
             'anterior de <strong>propiedades caloríficas constantes</strong>. '
             'Contienen resultados producidos bajo esas hipótesis; '
             'abrirlos desde el dashboard cp(T) no los vuelve '
             'a calcular ni los transforma. Antes de compararlos, '
             'verifica etiquetas de modelo, fecha, parámetros '
             'y unidades, así como la clasificación de motor '
             'o no motor de los puntos representados.</p>'),
            ('3 · Verificación y validación no son equivalentes',
             '<p><strong>Verificación</strong> significa contrastar '
             'que el programa implementa coherentemente sus '
             'ecuaciones y reglas: balances, residuos, referencias '
             'y pruebas de software. <strong>Validación</strong> '
             'exige comparar las predicciones con datos físicos '
             'externos adecuados al problema y sus incertidumbres. '
             'Un informe reproducible y 100 % de pruebas internas '
             'correctas no convierten un ciclo idealizado '
             'en un motor experimentalmente validado.</p>'),
            ('4 · Procedimiento seguro de consulta',
             '<ol><li>Identificar el tipo de informe y el modelo '
             'que figura en su cabecera.</li><li>Comprobar entradas, '
             'unidades y criterios de viabilidad.</li>'
             '<li>Leer los resultados con sus hipótesis originales '
             'y conservar el HTML si se necesita la referencia.</li>'
             '<li>Si se desea comparar con cp(T), ejecutar '
             '<strong>un nuevo caso</strong> en este simulador '
             'con entradas equivalentes y reconocer '
             'que se trata de modelos diferentes.</li></ol>'),
            ('5 · Límite actual de Informes',
             '<p>La aplicación cp(T) presenta resultados '
             'de Simulación, Optimización, Sensibilidad, Mapa '
             'y Segunda ley en pantalla. <strong>Todavía no '
             'genera informes HTML nuevos para cp(T)</strong>. '
             'El historial existente sigue disponible '
             'en modo de consulta, sin reescritura de archivos. '
             'No debe atribuirse una diferencia entre modelos '
             'a un error numérico sin analizar sus hipótesis.</p>'),
        ),
    },
    'ayuda': {
        'uso': ('Empieza por Simulación para fijar condiciones físicas; usa Resultados para entender '
                'balances, Optimización para comparar A/B, Sensibilidad y Mapa para explorar '
                'entradas y Segunda ley para irreversibilidades. Todas las secciones comparten la misma física. '
                'En cada sección puedes pasar de «Uso y configuración» a «Fundamentos y procedimiento». '
                'Consulta aquí el glosario, las unidades, los diagnósticos frecuentes y los límites '
                'de aplicación del modelo antes de interpretar prestaciones.'),
        'fundamentos': (
            ('1 · Glosario mínimo de magnitudes',
             '<p><strong>T1–T4, T2s, T4s:</strong> temperaturas absolutas '
             '[K]. <strong>p1–p4:</strong> presiones absolutas [kPa]. '
             '<strong>rp=p2/p1:</strong> relación de compresión [−]. '
             '<strong>ηc y ηt:</strong> eficiencias isentrópicas [−]; '
             '<strong>δ:</strong> fracción de pérdida de presión [−]. '
             'δ=0,05 equivale a perder el 5 % de p2 entre 2 y 3.</p>'
             '<p><strong>cp(T):</strong> J/(kg·K); '
             '<strong>γ(T):</strong> adimensional; '
             '<strong>h, trabajo, calor y exergía:</strong> kJ/kg; '
             '<strong>s y sgen:</strong> kJ/(kg·K). '
             'Un trabajo en kJ/kg no es una potencia en kW '
             'sin un caudal másico.</p>'),
            ('2 · Hipótesis y alcance físico',
             '<p>Un <strong>gas ideal</strong> satisface p·v=R·T; '
             'esto no obliga a fijar cp ni γ como constantes. '
             'El simulador modela aire seco de composición '
             'fija N₂/O₂/Ar con cp(T) entre 200 y 2000 K. '
             'El compresor y la turbina son adiabáticos, '
             'con eficiencias isentrópicas de entrada. '
             'No se incluyen química de combustión, '
             'mapas de máquinas reales, pérdidas adicionales, '
             'caudal, masa ni empuje. Estas hipótesis '
             'deben acompañar cualquier conclusión.</p>'),
            ('3 · Orden recomendado para aprender',
             '<ol><li><strong>Simulación:</strong> reconoce los '
             'cuatro estados, sus presiones y la diferencia '
             'entre las salidas reales e isentrópicas.</li>'
             '<li><strong>Resultados:</strong> sigue las '
             'entalpías, trabajos y primera ley.</li>'
             '<li><strong>Optimización:</strong> distingue '
             'el máximo trabajo A del máximo rendimiento B.</li>'
             '<li><strong>Sensibilidad y Mapa:</strong> '
             'estudia uno o dos cambios de entrada y las '
             'regiones motoras.</li><li><strong>Segunda ley:</strong> '
             'analiza generación de entropía y exergía '
             'destruida en componentes.</li><li><strong>Informes:</strong> '
             'comprueba trazabilidad e hipótesis.</li></ol>'),
            ('4 · Estados de resultado y errores frecuentes',
             '<p><strong>Motor:</strong> satisface las condiciones '
             'nominales definidas por el código. '
             '<strong>No motor:</strong> estados calculables, '
             'pero prestaciones operativas inadmisibles. '
             '<strong>Fuera de rango:</strong> se necesitaría '
             'una temperatura no cubierta por cp(T). '
             '<strong>Entrada inválida:</strong> parámetros '
             'mal definidos. <strong>Error numérico:</strong> '
             'no se pudo representar o resolver un estado '
             'bajo las condiciones de cómputo.</p>'
             '<p>Un <strong>supremo</strong> es un valor límite '
             'no alcanzado en el dominio motor abierto, '
             'no un punto operativo. “No disponible” no '
             'equivale a cero. El diagrama T–s incluye '
             'segmentos esquemáticos, no trayectorias '
             'exactas de un proceso.</p>'),
            ('5 · Cómo utilizar el dashboard críticamente',
             '<p>Lee primero <strong>Uso y configuración</strong> '
             'para ejecutar la tarea; después abre '
             '<strong>Fundamentos y procedimiento</strong> '
             'para comprender sus ecuaciones, criterios '
             'y limitaciones. Los gráficos se pueden '
             'ampliar con el botón de la figura y cerrar '
             'mediante Escape. Al comparar resultados, '
             'mantén unidades, entradas y modelo coherentes.</p>'
             '<p>Las pruebas de código y los residuos '
             'de balance verifican la implementación; '
             'no sustituyen una <strong>validación '
             'experimental</strong>. El programa sirve '
             'para aprender termodinámica de ciclos, '
             'no para certificar prestaciones de un '
             'propulsor aeroespacial.</p>'),
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
