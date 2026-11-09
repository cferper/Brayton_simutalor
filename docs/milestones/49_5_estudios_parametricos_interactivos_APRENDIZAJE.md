# Milestone 49.5 — Aprendizaje: barridos y mapas de un turborreactor

## Estado anterior y objetivo

En el 49.4 explorábamos con zoom un **único punto motor**: Mach, T3,
prestaciones, estados y perfiles. Ahora repetimos el cálculo del mismo motor
para una lista explícita de condiciones. No cambiamos las ecuaciones;
estudiamos la dependencia de sus resultados respecto a las entradas.

## Interpretación física / INGENIERÍA

### Empuje frente a Mach

El Mach de vuelo `M∞ = V∞/a∞` es adimensional. A igualdad de las demás
entradas, el difusor recibe distintas condiciones de remanso y la velocidad
de entrada modifica el balance de empuje neto. Por eso la curva puede cambiar
de dirección: el código **no impone** tendencia creciente o decreciente.
Cuando existe caudal, `F [N] = Fs [N/(kg/s)] × ṁaire [kg/s]` según el propio
solucionador. Sin caudal no hay fuerza absoluta: el usuario puede consultar
`Fs`, claramente etiquetado, pero no fabricar `F`.

### Empuje y consumo frente a T3

T3 es la **temperatura total de entrada a turbina**, a la salida de la cámara.
Al modificarla cambia el combustible equivalente necesario y la energía
disponible tras alimentar el compresor mediante la turbina. El empuje no tiene
por qué responder linealmente. El `TSFC [kg/(N·h)]` relaciona caudal de
combustible y empuje; solo tiene sentido con empuje neto positivo. Si el
denominador deja de ser físicamente válido, la casilla se omite, no se
transforma en cero ni en infinito representable.

### Mapa Mach–T3

Cada celda es un punto calculado y **no** un valor interpolado. Mach aparece
horizontal y T3 [K] vertical. El color representa una magnitud elegida,
con unidades independientes para empuje absoluto, específico o TSFC. La
escala cambia cuando se elige otra magnitud. Gris significa que el punto no
se pudo calcular o esa magnitud no existe; **gris no representa empuje cero**.
Las celdas se consultan para leer valores exactos y diagnósticos.

### A/B/C

- **A:** mantiene el caudal de aire impuesto, cuando se proporciona.
- **B:** conserva el área física de garganta y salida y recalcula el caudal
  compatible con las condiciones de cada muestra.
- **C:** resuelve de nuevo el acoplamiento de eje y mapas educativos en cada
  punto. Hay más regiones sin solución y el coste depende de convergencia.

No se consideran los tres modelos intercambiables. Una región no admisible
es información sobre las restricciones del **modelo educativo**, no prueba de
que un motor industrial real no pueda funcionar allí.

## PYTHON: funciones nuevas

`configurar_estudio_49_5(configuracion, modo)` recibe un diccionario JSON y
un modo `str`; devuelve los ejes `list[float]`, nombres de variable y tipo.
Valida límites, orden y resolución y lanza `ValueError` ante configuración
no válida. Ejemplo: con Mach `[0, 0.4, 0.8]`, `T3=1600` fijo, la lista
contendrá tres números reales, no tres modelos físicos distintos.

`calcular_estudio_49_5(valores, configuracion)` recibe el mismo `dict[str,str]`
del formulario que `simular_turborreactor` y el diccionario de intervalos.
Construye una **copia** de parámetros con `dict(valores)` en cada iteración
para no modificar el original, cambia solo el eje y llama al solucionador
de un punto. Devuelve ejes, constantes, unidades, lista ordenada de puntos,
estado de cada uno y tiempo medido en segundos. Las excepciones de dominio,
convergencia y valor se convierten en diagnósticos **de cada celda**, para
que el resto de la malla pueda continuar.

`api_estudio_parametrico_49_5()` es una vista Flask sin argumentos explícitos:
lee un objeto JSON, valida el formato y devuelve `Response` JSON (200/400).
No modifica ni sustituye `/api/turborreactor/simular`.

## JavaScript: interacción y exportación

`iniciar49(doc, fetcher)` monta la vista al cargarse el documento, recoge
`FormData` del formulario principal y del estudio y realiza una única petición
al pulsar «Calcular estudio». `async/await` espera la respuesta; una versión
creciente y `AbortController` ayudan a descartar respuestas antiguas. El
gráfico se construye con nodos SVG y sus coordenadas se obtienen por escalado
**visual** de datos numéricos (no del modelo termodinámico).

`colorMapa49(valor,min,max)` asigna un color según el intervalo de la métrica;
no calcula puntos nuevos. `csv49(datos)` convierte cada punto calculado y
diagnóstico a filas con valores delimitados y unidades declaradas. Las
comillas dobles de los textos se escapan para un CSV válido. Su uso en Node:

```js
const {colorMapa49} = require('./static/estudios_parametricos_49_5.js');
console.log(colorMapa49(50, 0, 100)); // Color de un punto, no valor físico
```

El navegador permite guardar dos configuraciones de curva comparables y
superponerlas con la actual. Las constantes distintas se muestran bajo el
gráfico. Cambiar el estudio o su magnitud limpia las comparaciones para no
mezclar definiciones o unidades.

## Verificación frente a validación

Comprobar un punto del barrido contra una llamada individual al mismo motor
verifica la **integración de software**, pero no valida el modelo contra un
ensayo experimental. También hay que revisar dimensionalmente ejes y unidades,
ausencia de valores ficticios, límites de resolución y diagnósticos.

## Limitaciones

No se optimiza el funcionamiento; no se interpolan regiones inválidas. La
cancelación del navegador puede ignorar una respuesta pendiente, pero no
garantiza detener la ejecución en el servidor. Los mapas C siguen siendo
educativos y costosos, por lo que la malla máxima es más pequeña.

**Base:** `fa81eef98f5b1c18c6c13941d5b0f33b6e30fdfe` en
`mejoras/cp-variable`. El 49.5 permanece local, pendiente de revisión y commit.

## Integración y verificación en Windows (2026-11-05)

Se integraron los nueve archivos entregados. Pasaron las 9 pruebas nuevas,
la regresión completa (766 pruebas correctas, 10 omitidas), los 8 tests
JavaScript y la comprobación sintáctica de ambos controladores. Con Flask test
client, las vistas respondieron 200 y `/` redirigió al banco; el endpoint nuevo
devolvió JSON válido para A, B y C, rechazó mapas por encima de sus límites y
marcó como `sin_solucion` los puntos de un caso de combustión inviable, sin
inventar empuje absoluto ni TSFC. El empuje y las muestras válidas coinciden
con llamadas individuales al mismo solucionador. La inspección visual y las
exportaciones gráficas quedan para la revisión manual solicitada.
