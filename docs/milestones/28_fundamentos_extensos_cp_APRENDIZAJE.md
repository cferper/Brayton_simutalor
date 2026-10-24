# Aprendizaje — Cómo convertir un simulador en una herramienta didáctica

**Milestone 28 (24/10/2026)** · Segunda iteración educativa del Brayton cp(T)  
**Rama:** `mejoras/cp-variable` · **Base:** `9dc0b8fe70c6667d2f3df9c30b2535379598c3c3`.

## 1. Por qué era necesaria esta iteración

Antes de este cambio el dashboard podía calcular correctamente y mostraba ayudas breves en todas las secciones. Sin embargo, un estudiante podía leer “se resuelve la compresión por entalpías” sin saber primero qué representa la entalpía, para qué sirve el estado isentrópico de referencia o por qué el trabajo absorbido se considera positivo.

La solución consiste en **separar dos ritmos de lectura**:

1. «Uso y configuración» responde qué hacer para obtener un resultado, en pocas líneas.
2. «Fundamentos y procedimiento» enseña desde el fenómeno físico hasta la ecuación y el algoritmo empleados, con ejemplos y límites expresos.

El simulador no cambia sus resultados: es una mejora de enseñanza y comprensión, no una nueva fase termodinámica.

## 2. Estructura de datos que permite esta ampliación

`educacion_cp_variable.py` centraliza todo el contenido de las ocho secciones en `CONTENIDOS`, un diccionario de Python. Una entrada ilustrativa simplificada es:

```python
CONTENIDOS = {
    'simulacion': {
        'uso': 'Configura el ciclo...',
        'fundamentos': (
            ('1 · Contexto', '<p>El ciclo Brayton...</p>'),
            ('2 · Procesos', '<ol><li>Compresión...</li></ol>'),
            # ... otros apartados escritos en el módulo real
        ),
    },
}
```

La estructura anterior es un **esquema pedagógico**, no una copia del contenido completo. En el código real hay seis secciones con ocho pares `(título, contenido)` y dos con cinco.

### ¿Qué hace Python con los textos de varias líneas?

Dos literales de cadena consecutivos entre paréntesis se concatenan automáticamente:

```python
texto = ('La entalpía describe ' 
         'energía de flujo por kilogramo.')
```

`texto` contiene una sola cadena. Se ha usado para que los bloques largos sean editables y revisables sin construir HTML dinámico a partir de datos del usuario.

## 3. Cómo llega una teoría de Python al navegador

La función existente `_tarjeta(titulo, cuerpo)` convierte cada par en un `<article>` con título y contenido. Escapa el **título** mediante `html.escape`, y el **cuerpo** es HTML confiable escrito en el propio módulo. No lee parámetros del usuario ni calcula propiedades.

`construir_educacion_cp()` recorre `CONTENIDOS`, construye una tarjeta para uso y una secuencia de tarjetas para fundamentos, y devuelve un diccionario con ambas claves. `dashboard.renderizar_dashboard()` lo entrega a Jinja; `templates/index.html` inserta, por ejemplo, `{{ educacion_cp.segunda_ley.fundamentos|safe }}`. El operador `safe` se reserva para **texto estático de autoría propia**: sería peligroso aplicarlo a entradas arbitrarias de un formulario.

Este diseño tiene una ventaja importante: el HTML general no necesita repetirse ni contener cientos de líneas de física; cada sección comparte la misma estructura y sus textos pueden revisarse de forma aislada.

## 4. Aprendizaje termodinámico que ahora se desarrolla

### Simulación y Resultados

Las explicaciones muestran por qué la ley p·v=R·T puede coexistir con cp(T), y por qué los estados 2s/4s se obtienen igualando entropías antes de aplicar las eficiencias isentrópicas. En Resultados se relaciona la primera ley con los saltos h2−h1 y h3−h4, aclarando qué entra en el balance y por qué el trabajo es específico por kilogramo.

### Optimización

El algoritmo no depende de escoger el mejor punto dibujado. Trabaja en x=ln(rp) y, según el criterio, busca la raíz de la derivada del trabajo o del numerador de la derivada del rendimiento. Una frontera abierta puede generar un supremo que no es un ciclo operable. Este matiz evita una confusión matemática y de diseño.

### Sensibilidad y Mapa

La sensibilidad local es una pendiente del **caso base**, estimada mediante diferencias finitas; el mapa evalúa combinaciones concretas de rp y T3. Ninguno sustituye la reoptimización del ciclo. Se explican los huecos no motores y la diferencia entre máximos discretos y continuos.

### Segunda ley

La primera ley conserva energía y la segunda cuantifica irreversibilidades. El programa usa las entropías de los estados existentes, un ambiente T0/p0 y la relación eD=T0·sgen para compresor y turbina. La destrucción total del motor **no se conoce** en este modelo porque faltan intercambios térmicos, combustión y sus volúmenes de control. Los rendimientos exergéticos de los componentes tampoco equivalen al rendimiento térmico global.

## 5. Ejemplos que no engañan al usuario

Se han elegido ejemplos que enseñan una operación concreta sin fingir que son resultados del caso vigente:

- Presiones 100→1000→950→100 kPa para ilustrar rp y δ.
- Un conjunto **ficticio** de entalpías para comprobar el balance wc, wt, qin y qout.
- Una elasticidad hipotética para distinguir porcentaje relativo de puntos porcentuales.
- Una malla de cinco valores de rp por cinco temperaturas T3 para entender las 25 evaluaciones.
- La multiplicación 300 K × 0,020 kJ/(kg·K) = 6 kJ/kg para entender Gouy–Stodola.

Al separar claramente el ejemplo de la simulación real, el usuario aprende a operar las fórmulas sin confundir datos docentes y datos calculados.

## 6. CSS de lectura frente a CSS de dashboard

Antes, `.edu-deep-grid` distribuía los bloques en dos columnas. Ese formato favorece tarjetas informativas breves, pero hace incómodo seguir demostraciones, pasos numerados y ecuaciones largas. Ahora las tarjetas se ordenan **en una sola columna**, con un ancho máximo para evitar líneas excesivas.

Se diferencian visualmente:

- `.edu-equation`: ecuación o balance destacado, con unidades.
- `.edu-insight`: interpretación o advertencia metodológica.
- Párrafos y listas: separación y tamaño de letra adecuados para leer varios minutos.

El resto del CSS, los ocho paneles, los formularios, las galerías de SVG y su visor son los de la iteración anterior. No se han añadido dependencias ni código JavaScript.

## 7. Cómo comprobarlo y qué no certifican los tests

Las pruebas verifican que el contenido de las ocho secciones se genera, que seis tienen teoría desarrollada, que la configuración sigue siendo concisa, que las fórmulas y ejemplos aparecen en HTML y que las entradas, rutas, gráficos y prestaciones se mantienen. El workflow conserva las pruebas científicas y web focalizadas anteriores.

Eso **no demuestra automáticamente** que un párrafo explique bien una idea o que todos los símbolos se lean cómodamente en una pantalla concreta. Esa parte requiere revisar los textos contra el código —en especial 2B/2C, OFAT, mapa y exergía— e inspeccionar la interfaz en Windows.

## 8. Mini ejercicios

1. Localiza en `ciclo_cp_variable.py` las cuatro temperaturas calculadas. ¿Qué dos se obtienen primero mediante entropía y por qué?
2. ¿Por qué `wnet=wt−wc` puede ser positivo mientras que un conjunto de parámetros sigue siendo no motor?
3. Encuentra en `optimizacion_cp_variable.py` la variable `x` y la función `numerador_derivada`. ¿Qué criterio optimiza esta última?
4. ¿Qué diferencia hay entre un valor de S=−0,5 y una disminución de 0,5 puntos porcentuales de rendimiento?
5. ¿Por qué la suma de destrucciones de compresor y turbina no permite afirmar cuánto potencial de trabajo pierde toda la instalación?

**Conclusión:** el contenido científico original se mantiene; el desarrollo pedagógico ahora permite comprender las ecuaciones, su implementación numérica y lo que legítimamente se puede inferir de cada resultado.
