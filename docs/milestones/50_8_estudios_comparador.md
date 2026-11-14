# Milestone 50.8 — Estudios, Comparador y navegación entre herramientas

**Fecha:** 14 de noviembre de 2026.
**Repositorio:** `cferper/Brayton_simutalor`.
**Rama:** `mejoras/cp-variable`.
**Base remota verificada:** `d819e506a68203b597c1e80c962381feb0668321` (M50.7).
**Commit de M50.8:** pendiente; no se modifica GitHub.

## Estado anterior

M49.5 y M50.4 proporcionaban un explorador Mach–T3 con barridos, mapas,
clasificación de convergencia, lectura de celdas, exportación y aplicación de
un punto C. M50.1 guardaba una referencia en memoria y comparaba con el punto
actual mediante tabla, diferencias y cuatro gráficas. M50.5 ubicaba Estudios
y Comparador en los espacios principales, pero sus herramientas aún ocupaban
largas secciones continuas. M50.6 y M50.7 ya reorganizaban los otros cinco
espacios. El controlador M50.5 era el único propietario de la navegación.

## Qué se ha añadido

- **Estudios:** pestañas *Barridos Mach/T3*, *Mapa Mach–T3* y *Sensibilidad y
  mapas clásicos*. Barrido y mapa comparten el **mismo nodo** `#estudio49`;
  su tipo conserva los nombres y validaciones originales. Los estudios
  clásicos `#sensibilidad` y `#mapa` quedan en `<details>` diferenciados con
  sus formularios HTTP anteriores. Una malla del explorador se dibuja en la
  región central y el panel `study49-point` se mueve a una tercera zona de
  diagnóstico. No se generan otras celdas, SVG ni respuestas numéricas.
- **Estudios desactualizados:** si se cambian límites, número de muestras
  o condiciones físicas de la fuente «banco» después de calcular, se avisa,
  se conserva el SVG antiguo como histórico y se deshabilita «Utilizar este
  punto» hasta solicitar un estudio nuevo. La invalidación existente de
  M49.5 sigue siendo la autoridad sobre sus datos privados. Un cambio
  explícito de tipo o de fuente muestra confirmación si existe gráfico,
  porque M49.5 reemplaza entonces sus resultados. Cambiar de espacio o a
  *Clásicos* no altera el estudio ni lo marca como desactualizado.
- **Comparador:** conserva una única `.turbo-lab50`. Los controles de
  referencia permanecen siempre visibles; las pestañas secundarias muestran
  *Prestaciones*, *Gráficas comparativas* o *Condiciones*. Entre las cuatro
  gráficas existentes se elige una; la selección actualiza también el
  marcador de gráfica activa del controlador M50.1 para su exportación SVG
  y zoom. No se guarda otra referencia ni se hacen cálculos de diferencias
  en el módulo nuevo.
- **Flujo:** enlaces entre Simulación, Estudios y Comparador llaman únicamente
  `controladorNavegacion50_5.navegar(...)`. La aplicación de una celda C
  mantiene el evento `brayton:aplicar-estudio-50-4` y el cargador completo
  M50.3/M48: una solicitud física, limpieza de resultados obsoletos y
  conservación de la referencia M50.1. No se añade otro listener de simulación.

## Archivos

- `static/estudios_comparador_50_8.js`: módulo nuevo de disposición y
  navegación secundaria sin `fetch` ni ecuaciones físicas.
- `templates/turborreactor.html`: carga `defer` del módulo, exclusivamente
  en `/turborreactor/interactivo` y después de los controladores anteriores.
- `static/turborreactor.css`: paneles, gráfico central, detalle lateral,
  foco visible y puntos de ruptura; conserva las correcciones de CSS
  publicadas en el commit 50.7.
- `tests/test_estudios_comparador_50_8.py` y
  `tests/js/test_estudios_comparador_50_8.cjs`: contratos e interacción.
- `CODE_WALKTHROUGH.md` (§4.112) y este documento más el aprendizaje 50.8.

No se modifican `web_app.py`, `estudios_parametricos_49_5.py`, los
solucionadores, los controladores M48/M50.1/M50.3/M50.4/M50.5, los mapas,
las API ni las rutas del turborreactor clásico y de Brayton.

## Arquitectura y datos compartidos

`iniciarAnalisis50_8(documento,ventana=raiz)` se ejecuta en `DOMContentLoaded`
si la ruta es interactiva y el M50.5 ya se ha iniciado. Solo utiliza
`appendChild`: conserva identidad, identificadores, listeners y estado de
`#estudio49`, `#turbo-study49-form`, `.turbo-lab50` y sus gráficos. Las
pestañas activan/ocultan paneles mediante `hidden`, `role="tab"`,
`aria-selected`, `aria-controls` y foco con flechas/Home/End. En los cambios
Barridos ↔ Mapa se cambia el selector original `#study49-tipo`, no se
reescribe el algoritmo M49.5. En cambios de ventanas principales no se toca
ningún selector ni se ejecutan operaciones HTTP.

El comparador guarda en la clausura de M50.1 la referencia profunda y el
punto actual. No se almacena una segunda copia en M50.8. La diferencia
relativa continúa definida solo cuando la referencia es distinta de cero,
y las magnitudes no aplicables no se convierten en cero.

Los formularios OFAT/mapas clásicos conservan su **POST histórico**, que sí
puede recargar la página cuando se ejecuta. Esto es distinto de navegar
entre subpestañas, operación que no recarga. No se transforman artificialmente
en estudios de la API M49.5.

## Ingeniería, alcance y limitaciones

Este cambio es exclusivamente de presentación. No cambia cp(T), balance de
energía, Newton, tolerancias, datos NASA T-MATS, restricciones de mapa ni
criterios de convergencia. Una celda sin convergencia no acredita una
frontera física. Rline no es margen de surge. En A/B no se inventan rpm,
caudales o comparaciones que el modelo no resuelve. El comparador distingue
cambios simultáneos de condiciones y evita atribuir una variación a una sola
entrada cuando no corresponde. El motor sigue siendo educativo, sin
validación experimental del motor real.

## Pruebas y verificaciones efectuadas

En este entorno, con los paquetes incrementales de 50.3–50.7:

- 8 pruebas Python específicas M50.8, y 23 pruebas Python estáticas M50.5–50.7:
  **31 correctas**. Jinja se analizó con `Environment().parse`.
- Prueba nueva M50.8: **70 verificaciones JavaScript** con DOM simulado.
  Incluye navegación, cancelación de cambios destructivos, retención de nodos,
  persistencia de la referencia, gráfica única, accesibilidad básica,
  invalidación de controles y ausencia de solicitudes HTTP.
- Regresiones JavaScript locales M50.3–50.7 ejecutadas sin fallos. El código
  JavaScript 50.7 del ZIP de partida difiere de la versión con correcciones
  publicada; estas pruebas locales no sustituyen su nueva regresión en Windows.
- Sintaxis Node del módulo y de la plantilla Jinja correcta. La base de
  `CODE_WALKTHROUGH.md` se reconstruyó y contrastó contra el SHA del commit
  publicado antes de actualizarla.

**No ejecutado aquí:** regresión termodinámica total, recorrido real con Flask,
HTTP 422 y navegador; faltan archivos físicos del repositorio y Flask en la
copia incremental. Las comprobaciones con DOM simulado no equivalen a una
prueba visual. M50.7 ya tenía una regresión Windows comunicada, pero no se
presenta como una prueba repetida de M50.8.

### Integración en Windows · 14-11-2026

- Se recuperó la visibilidad de ambos formularios clásicos al abrir
  sus paneles de Estudios. Los dos devolvieron HTTP 200 con gráficas.
- Se excluyó el evento `input` de los selectores de tipo y fuente de la
  invalidación de rangos. Cancelar conserva la gráfica, la selección, el
  aviso y el botón de aplicar. Los cambios físicos del banco se observan
  con `input` y `change`; navegar no invalida el estudio.
- En Chrome y Flask, la malla C de 2 × 2 convergió en los cuatro puntos.
  Seleccionar la celda Mach 0,82 / T3 1690 K hizo cero peticiones motor.
  Aplicarla trasladó sus entradas con una sola petición y conservó la
  referencia Mach 0 / T3 1600 K. HTTP 422 retiró el punto actual y sus
  diferencias hasta recuperar una solución, conservando la referencia.
- Se comprobaron barridos, zoom, exportaciones, cuatro gráficas
  comparativas, navegación por fragmento y teclado. Las seis vistas de
  Estudios y Comparador se midieron a 1920, 1366, 768 y 390 px sin
  desplazamiento horizontal de página.
- Pasaron 31 pruebas focalizadas Python y 32 pruebas de Node, que
  incluyeron 71 comprobaciones internas del M50.8. En la regresión general
  final, 843 correctas, 10 omitidas y 0 fallidas de 853 pruebas.

## Continuidad

Queda la revisión visual personal.
La revisión global responsive y de accesibilidad pertenece al 50.9;
no se ha comenzado en este desarrollo.

## Commit asociado

**Pendiente.** No se han realizado commits, push, merges ni rebases.
