# Aprendizaje 48.3 — Integridad de una simulación interactiva

## Qué existía y qué problema cerramos

48.1 creó la API Flask y 48.2 enlazó deslizadores de Mach y T3 con una simulación Python. En este cierre no añadimos ecuaciones; comprobamos que una interfaz asíncrona no atribuya al estado actual resultados de una solicitud anterior.

## PYTHON: una ejecución, una interpretación física

En `api_turborreactor_simular()` el servidor recibe parámetros del formulario, llama a `simular_turborreactor(valores)` una sola vez y pasa ese resultado a `preparar_vista_turborreactor(resultado)`. La respuesta incluye magnitudes numéricas y representaciones de esos mismos estados. Mach no tiene unidades y T3 se expresa en kelvin. El código existente decide si el punto es físicamente admisible: un deslizador no garantiza que, por ejemplo, T3 baste para la compresión seleccionada.

Las modalidades plantean incógnitas distintas: A conoce el caudal de aire, B conoce la geometría y busca caudal compatible, y C busca equilibrio del motor monoeje. La interfaz no debe inventar valores si una de ellas no converge. Eso verifica coherencia del programa, **no** que prediga un motor real medido.

## JAVASCRIPT: por qué abortar no basta

Una solicitud `fetch()` puede finalizar después de que el usuario haya cambiado de idea. `AbortController` intenta cancelar, pero un servidor ya puede haber calculado la respuesta. Por ello `crearControlador48` mantiene un número `version` y solo procesa respuestas que coinciden con la versión actual.

El cierre modifica la implementación de `cancelar()` (sin argumentos ni valor devuelto), llamada desde el evento `submit` del formulario manual:

```javascript
function detener() {
  version += 1;
  cancelar();
}
```

`cancelar()` interno detiene el temporizador y aborta la solicitud; `detener()` además vuelve obsoleto cualquier resultado antiguo. El objeto público devuelve `cancelar: detener`. Es una forma sencilla de resolver una **condición de carrera**: el orden de llegada de respuestas no debe decidir qué física ve el usuario.

`invalidar()` realiza un paso equivalente al editar otros campos y muestra el estado pendiente. `cambiar()` programa un nuevo cálculo 350 ms después del último evento. Ninguno de estos métodos calcula Mach, empuje o temperaturas; solo controla la comunicación y la presentación.

## HTML: sustituir solo lo necesario

`DOMParser` recibe el HTML de Jinja y extrae tres regiones concretas. `replaceChildren` cambia los resultados mostrados, pero deja en su sitio los botones de pestaña y los controles que ya tienen eventos. Los SVG y los indicadores se generan desde la misma respuesta. Si hay error, se retiran los resultados anteriores y se presenta el diagnóstico. Los estudios de sensibilidad y mapas permanecen independientes.

## Ejemplo de prueba reproducible

1. Inicia una petición automática moviendo Mach.
2. Antes de que termine, pulsa el botón tradicional «Simular».
3. Aunque la solicitud antigua devuelva datos después, su número de versión ya es obsoleto y no puede modificar el resultado.

La prueba automatizada correspondiente está en `tests/js/test_interaccion_48_2.cjs`, junto a las de debounce e invalidación. Se ejecuta con `node tests/js/test_interaccion_48_2.cjs` sin nuevas dependencias.

En esta copia se verificaron ocho pruebas JavaScript y 19 regresiones científicas relacionadas. Quedan pendientes en Windows las ocho pruebas HTTP de 48.1 y la comprobación en navegador de modalidades A/B/C, presentación y descargas, porque este entorno no incluye Flask/Jinja2.

**Git:** rama `mejoras/cp-variable`, base `a6cb03f843a2d3d6718155324ec198e55349d212`, sin commit ni push de 48.1–48.3.

## Corrección final: estado inicial y estudios independientes (29-10-2026)

**Python/Flask.** En el ciclo Brayton histórico la ruta es `/brayton`.
Los enlaces con fragmentos (`/brayton#resultados`) siguen siendo GET normales;
el fragmento se interpreta en el navegador y no es una solicitud de cálculo.
Las pruebas que suponían que Brayton residía en `/` debían actualizar su URL,
sin cambiar las comprobaciones del contenido.

**JavaScript.** `inicializar48(documento,fetcher)` consulta el valor
`documento.body.dataset.simulacionInicial`. Si es `pendiente`, usa
`controlador.cambiar()` para que el GET inicial se calcule automáticamente;
si es `resuelta` conserva el POST manual ya representado en la página y no
desencadena otra petición física. El atributo lo genera Jinja y no contiene
datos termodinámicos: es solo una señal de estado del servidor.

La función local `estudioDesactualizado()` recorre las advertencias
`.turbo-study-stale` y pone `hidden=false`. Es una función de interfaz sin
argumentos, sin retorno y sin ecuaciones físicas; se invoca cuando se editan
entradas principales. Un mapa antiguo no se vuelve falso matemáticamente:
simplemente podría describir **otra configuración**, por eso se advierte al
usuario sin reescribir sus valores. El error previo del formulario principal
se borra solamente al recibir una solución automática válida; los errores de
estudios independientes no se tocan.

La corrección mantiene la espera de 350 ms, la cancelación y las tres
modalidades A/B/C. Se verificaron ocho pruebas JavaScript; el entorno carece
de Flask/Jinja2 y las dos pruebas HTTP afectadas deben repetirse en Windows.
