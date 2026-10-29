# Milestone 48.2 — Primera simulación interactiva

## Estado anterior

La entrega 48.1 preparó `POST /api/turborreactor/simular`, que devuelve magnitudes estructuradas, SVG y `html_documento` de una sola simulación. Todavía había que pulsar el botón tradicional para recalcular. El código sigue en la copia de trabajo basada en `a6cb03f843a2d3d6718155324ec198e55349d212`; 48.1 y 48.2 permanecen **sin commit**.

## Controles y límites físicos

Se conservan todos los campos originales, incluidos Mach y T3, que ahora son entradas numéricas sincronizadas con controles `range`:

| Magnitud | Límite científico | Intervalo del deslizador | Campo exacto |
| --- | --- | --- | --- |
| Mach de vuelo | `0 ≤ M < 1` (vuelo subsónico del difusor y del motor C) | `0–0,999`, paso `0,001` | `0–0,999999` en HTML, paso libre; Python exige estrictamente `M < 1` |
| T3, remanso de entrada a turbina | `200 ≤ T3 ≤ 2000 K` por `propiedades_aire.py`; debe además superar la temperatura de compresor y satisfacer los demás balances | `200–2000 K`, paso `1 K` | `200–2000 K`, paso libre |

Los pasos del deslizador representan resolución de interfaz, **no** fronteras adicionales del modelo. Se conserva el valor exacto introducido, incluso si no es representable en la rejilla del deslizador, y el servidor decide su admisibilidad. Mach/T3 son entradas tanto en A, B como en C; en C son datos de vuelo y consigna térmica, nunca giro o relación de compresión impuestos.

## Ciclo de solicitud y consistencia

`static/turborreactor_interactivo.js` inicia solo con JavaScript disponible, dejando intacto el formulario HTML sin JavaScript. `acoplarControl48` asocia los eventos `input` del control numérico y del rango; actualiza al instante la lectura visible. `crearControlador48` concentra los cambios en **350 ms** (debounce). Al comenzar otro cambio aumenta un identificador secuencial y aborta la petición anterior mediante `AbortController`. También comprueba el identificador **después** de recibir la respuesta: ni siquiera un servidor que ignore la cancelación puede hacer que un resultado antiguo sustituya al reciente.

La función `inicializar48` envía `new FormData(formulario)` mediante `fetch` a la API existente. Al éxito, usa la misma `html_documento` renderizada por Jinja: extrae los paneles de uso `#turbo-resultados-vista-uso`, `#turbo-estaciones-vista-uso` y `#turbo-graficas-vista-uso`, preserva las pestañas, la navegación y el contenido educativo actual, y reemplaza sus hijos. El resumen inmediato dentro de Configuración utiliza las magnitudes del mismo JSON y previsualiza SVG del mismo cálculo. No hay ecuaciones ni interpolaciones termodinámicas en JavaScript.

Un cambio marca primero todos los indicadores como pendientes y retira los gráficos y resultados antiguos de las regiones actualizadas. En éxito muestra **Actualizado**; en error, el motivo del solucionador y **Error de cálculo** o **Fuera del mapa** cuando el diagnóstico del modo C menciona expresamente el dominio de mapas. No se muestran ceros ficticios; `null` pasa a «No aplicable». Cambios de otros campos invalidan lo anterior, pero no lanzan cálculos automáticos de estudios independientes. Cambiar la modalidad o tipo de tobera solicita una simulación nueva. El botón manual, sus seis secciones, las descargas, sensibilidad y mapas siguen existentes.

## Pruebas

- `node tests/js/test_interaccion_48_2.cjs`: seis pruebas sin dependencias para sincronización de Mach/T3, preservación de valor exacto, debounce, orden de respuestas y recuperación tras error.
- `node --check static/turborreactor_interactivo.js`, `python -m compileall -q web_app.py` y `git diff --check` para sintaxis e higiene.
- Pruebas HTTP de las tres modalidades ya preparadas en `tests/test_navegacion_api_48_1.py`; si faltan Flask/Jinja2 en la copia Linux, requieren ejecución posterior en Windows. Tampoco equivale una prueba de lógica Node a una inspección visual real de DOM y CSS en navegador.

## Limitaciones y fases siguientes

- La actualización del cuerpo HTML via `DOMParser` es deliberadamente limitada a los tres paneles de resultados de uso; no reemplaza sus pestañas educativas ni vuelve a calcular sensibilidad/mapa.
- La UI refleja inmediatamente el valor del control, **pero la física no cambia** hasta que el servidor termina una simulación válida. Los indicadores de estado distinguen ambas fases.
- La futura entrega 48.3 podrá mejorar otros controles y aspectos del banco. No se implementa en esta entrega.

## Commit asociado

Pendiente, sin staging, commit ni push. `main` y los solucionadores científicos permanecen intactos.
