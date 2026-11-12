# Milestone 50.3 — Configuraciones reproducibles y ayuda para el modo C

## Base y límites del desarrollo

- Rama: `mejoras/cp-variable`.
- Commit **publicado** de partida: `39a303545be4d5578c0780d303d583378b9376ea` (M50.2). El paquete M50.2 suministrado anteriormente coincide en los ficheros de control comprobados con los blobs del commit publicado.
- Este trabajo se desarrolla sin commit ni push. La inspección visual y las pruebas HTTP con Flask se trasladan al ordenador Windows.
- Se mantiene intacto `acoplamiento_motor_mapa_47.py`, los mapas NASA T-MATS escalados, las tolerancias, el método de Newton, las condiciones de cierre, las físicas y los modos A/B. Tampoco se modifica la API de simulación exitosa salvo su HTML de presentación.

## Configuraciones reproducidas por el solucionador de producción

Todos los casos comienzan de **una configuración completa** de diseño, no de los valores avanzados que pudiera haber dejado el usuario. Comparten, salvo donde se indique: `modo_caudal=acoplado`, ambiente **directo**, `T∞=288,15 K`, `p∞=100 kPa`, `Mach=0`, `T3=1600 K`, `πd=1`, `δ=4 %`, `ηm=0,98`, `ηn=0,95`, `ηb=0,99`, `PCI=43000 kJ/kg`, `Ag=0,04734811643457149 m²`, tobera convergente con `Ae=Ag`. Se conservan en el formulario `rp=10`, `ηc=0,85`, `ηt=0,90` como campos heredados **deshabilitados** en C: los valores físicos reales los resuelven los mapas. Sin caudal de aire impuesto, ni secciones de captación o de entrada adicionales.

| Caso | Diferencia respecto al diseño | N [rpm] | ṁa [kg/s] | πc [–] | F neto [N] | Iter. | Residuo normalizado |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Diseño | Referencia, C convergente | 20000,000 | 20,0000 | 10,0000 | 19165,154 | 0 | 0 |
| Vuelo moderado | Mach = 0,4 | 20139,259 | 21,2896 | 9,53393 | 17801,188 | 3 | 1,05·10⁻⁸ |
| TIT menor | T3 = 1550 K | 19820,938 | 19,3582 | 9,51744 | 17985,975 | 3 | 8,48·10⁻⁹ |
| TIT mayor | T3 = 1650 K | 20284,379 | 20,3381 | 10,33888 | 19996,349 | 3 | 1,19·10⁻⁸ |
| Presión menor | p∞ = 95 kPa (directa) | 20000,000 | 19,0000 | 10,0000 | 18206,896 | 0 | ~9·10⁻¹⁶ |
| Tobera C-D | Ae = 1,2 Ag = 0,05681773972148579 m² | 20524,341 | 20,6410 | 10,32667 | 20243,342 | 3 | 3,07·10⁻⁸ |

Estas cifras se obtuvieron en esta tarea con `turborreactor_web.simular_turborreactor` y `acoplamiento_motor_mapa_47.resolver_motor_acoplado`; no son resultados experimentales, tampoco constituyen intervalos continuos válidos. La condición de C-D incorpora únicamente el modelo físico existente (sin pérdidas de capa límite ni separación). La geometría y el mapa escalado son educativos. Las pruebas focalizadas recalculan cada caso y comprueban el residuo final ≤ 2·10⁻⁷.

### Compatibilidad muestreada, no frontera de funcionamiento

Con los parámetros de diseño fijos y una sola variación cada vez se comprobaron valores aislados: Mach 0 y 0,4; T3 1550, 1600, 1650 K; p∞ 95 y 100 kPa; área de garganta 0,9, 1,0 y 1,1 veces Ag,d; relación Ae/Ag de 1 y 1,2 en los casos indicados. Para Ag = 0,9 Ag,d el acoplamiento resolvió un punto; para 1,1 Ag,d el algoritmo devolvió **«Sin descenso del residuo en línea de búsqueda»** tras 11 iteraciones, sin empuje. No hay evidencia para interpolar una frontera entre estos casos ni declarar inviabilidad física fuera de ellos.

Los ensayos alterando un solo parámetro describen tendencias de un **modelo particular bajo restricciones fijadas**, no reglas universales. Para diagnóstico de estabilidad real serían necesarios mapas y límites experimentales compatibles.

## Arquitectura y flujo web

- `configuraciones_modo_c_50_3.py`: presenta seis conjuntos completos de parámetros. `configuraciones_verificadas_50_3(*, referencia=None)` entrega una lista de `{'id','nombre','descripcion','entradas'}` donde `entradas` tiene todas las claves del formulario. Con la referencia por defecto utiliza una calibración M47 memorizada durante el proceso. El usuario sigue resolviendo un caso con la misma API: este generador no calcula una segunda solución al pulsar.
- `diagnosticar_fallo_50_3(mensaje)` clasifica en `entradas`, `mapa`, `restricciones`, `numerico`, `modelo` o `indeterminado`, en función de **evidencias textuales** verificables. Incluye recomendación prudente, nunca afirma que la ausencia de equilibrio pruebe un surge o imposibilidad física. Un fallo de Jacobiano se interpreta como numérico aun si menciona el mapa.
- `web_app._render_turborreactor` pasa los ejemplos completos solamente a la plantilla interactiva. En `/api/turborreactor/simular` se añade la clasificación **solo a las respuestas 422 del modo C** dentro de `error.diagnostico_50_3`, sin modificar el `tipo` ni el `mensaje` históricos.
- `templates/turborreactor.html`: selector y botón «Restablecer punto de diseño C», con `<script type="application/json">` escapado por Jinja `tojson`. La ayuda se muestra solo con C seleccionado.
- `static/configuraciones_modo_c_50_3.js`: `aplicarEjemplo50_3` copia los campos de un caso **ya completo**, actualiza los sliders y sincroniza ambiente/tobera mediante eventos `change` que no se propagan hasta el controlador. `iniciarConfiguraciones50_3` inicializa selector, botón y mensajes; invoca un único callback de recálculo. No hace `fetch` ni calcula ecuaciones.
- `static/turborreactor_interactivo.js`: añade el callback al controlador M48 existente. Se conservan la invalidación de datos, el laboratorio M50.1 (referencia guardada), la sincronización M50.0 y el visor M50.2 (se retira punto/curva obsoleta al fallar). Los modos A/B no disparan la lógica de asistencia C.

La carga del diseño C restablece **todas** las entradas y la geometría; es diferente del botón 49.6 que solo consulta y restablece las dos áreas. Este segundo botón se conserva por compatibilidad.

## Significado de los diagnósticos

| Clase | Qué permite afirmar | Qué no permite afirmar |
| --- | --- | --- |
| Entradas | Alguna entrada incumple una validación explícita | Que toda región vecina sea inviable |
| Mapa | La consulta excede el dominio tabulado conocido | Que el compresor real presente surge |
| Restricciones | Cierre de continuidad/potencia/área explícitamente no satisfecho | Inexistencia de toda solución para cualquier condición |
| Numérico | El algoritmo no ha verificado el equilibrio dentro de sus criterios | Inviabilidad física, fallo real de motor |
| Modelo no resuelto | No se dispone de salida de tobera para ese régimen | Que el flujo real no pueda existir |
| Indeterminado | Falta evidencia suficiente para clasificar | Una causa física concreta |

## Verificación y restricciones restantes

**Ejecución en este entorno (12-11-2026):** pruebas Python focalizadas con el solucionador real: **7 correctas y 1 omitida** (la prueba HTTP exige Flask). Pruebas JavaScript completas: **23 correctas**, sin fallos. La sintaxis Python y Node y el análisis sintáctico Jinja de la plantilla pasan. La regresión Python general se ejecutó **una vez**, con **498 pruebas, 24 errores de importación y 4 omisiones**, sin otras fallas detectadas; las importaciones fallidas corresponden a tests que requieren `web_app` y no tienen Flask disponible. No se afirma regresión completa satisfactoria. La prueba HTTP nueva comprueba la estructura de 200 y el diagnóstico numérico de 422 cuando Flask esté instalado en Windows. Esta prueba omitida se ejecutará allí junto con la regresión general.

Pendiente de revisión visual en Windows: posición y legibilidad del selector, foco y teclado, selección consecutiva, cambio C→A/B→C, estado tras error 422, persistencia del punto guardado M50.1, controles Mach/T3, mapa HPC M50.2 y funcionalidad 49.5–50.0. Verificar con Flask instalado que el error JSON trae una clase correcta y que el POST completo mantiene todas las entradas.

**Integración Windows (12-11-2026).** Las 8 pruebas focalizadas pasaron,
incluida la prueba HTTP que se omitía en el entorno anterior. La suite
JavaScript completa pasó (23/23), con sintaxis Python y JavaScript correcta.
La regresión ejecutó 815 pruebas: 805 correctas, 10 omitidas y ningún fallo.
Las omisiones corresponden a SciPy (8), Cantera (1) y permiso de symlinks en
Windows (1). Los seis casos convergieron con el solucionador existente y sus
rpm, caudales, relaciones de presión, empujes y residuos coincidieron con la
tabla anterior. La inspección visual queda pendiente del usuario.
