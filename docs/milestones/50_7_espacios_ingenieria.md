# Milestone 50.7 — Organización de los espacios de ingeniería

## Estado anterior

- Rama `mejoras/cp-variable`; HEAD publicado de partida **`4cbd77769e4e8d0f2888685c3ba4ab31aef8e141`** (milestone 50.6), comprobado el 13 de noviembre de 2026.
- M50.5 ya ofrecía siete espacios y movía el único `#turbo-live` entre Simulación, Termodinámica y Tobera. M50.6 organizaba los controles y resultados de Simulación.
- Los componentes M49.7–M50.2, las estaciones del informe y los diagramas existían, pero gran parte de su acceso dependía del scroll o de contenedores provisionales.

## Qué se ha añadido

- **Motor**: navegación interna «Esquema y ficha» / «Estaciones y propiedades»; se reutilizan el SVG interactivo, su selección de seis componentes y las pestañas Funcionamiento/Resultados/Ecuaciones, más las tablas originales.
- **Termodinámica**: selección compacta de T–s, temperaturas/presiones totales, trabajos, balance e informe antiguo. Solo se ve la gráfica activa; conserva zoom, lectura de marcadores y exportación del M48.
- **Tobera**: selección de Mach, presión estática, temperatura, velocidad, geometría y explicación de funcionamiento. Se consultan las dos tarjetas originales de régimen/velocidad de salida en este espacio; las demás permanecen en Simulación. Acceso directo a la ficha real de tobera en Motor.
- **Turbomáquinas**: pestañas para mapa HPC y corregidos (M50.2), indicadores existentes de funcionamiento/rendimientos (M49.9) y límites de interpretación. El módulo de caracterización se **traslada**, no se clona, desde Motor.
- Se agrega `static/espacios_ingenieria_50_7.js` y estilos focalizados para navegación secundaria, paneles compactos y responsive. Se sincroniza el manual actual.

## Integración y propiedad de los nodos

`static/navegacion_superior_50_5.js` sigue siendo el **único controlador** que traslada `#turbo-live`. M50.7 comunica los dos contenedores de destino mediante `destinoVisor50_7(espacio)`; M50.5 ejecuta `appendChild(live)` y notifica la vista activa a `activarEspacioIngenieria50_7`. M50.7 usa los botones **reales** `data-plot-group-button` y `data-plot-tab` de M48 para elegir la gráfica; no construye ni solicita gráficos alternativos.

Los componentes de Motor, el diagnóstico HPC, la caracterización y las tablas se mueven una sola vez al inicializar. La selección secundaria altera únicamente `hidden` y `aria-pressed`. La navegación principal conserva fragmentos `#espacio-*`, historial y franja del motor. Se evita que el restablecimiento de visibilidad de M50.5 interfiera con las nuevas subpestañas Estaciones/Informe. No se altera el formulario, el controlador M48, la API ni el estado de referencia M50.1.

## Nuevos conceptos de ingeniería

El esquema no es un plano a escala. T3 interna es temperatura **total** a la entrada de turbina; no debe confundirse con la salida. Los diagramas T–s representan estaciones calculadas y uniones esquemáticas. Los perfiles de tobera no permiten deducir choques/separación que el modelo no resuelve. Las magnitudes corregidas de HPC proceden de la referencia M50.2; en A/B no se dispone de rpm calculadas por equilibrio de eje. El mapa HPC NASA T-MATS escalado no es validación experimental y **Rline no es margen certificado de surge**. No se incorpora mapa gráfico HPT.

## Conceptos de programación

Se usa `appendChild` para mover nodos conservando su identidad y eventos. `Map` almacena botones/contenedores por clave; `dataset` guarda la vista secundaria elegida; `hidden` y `aria-pressed` distinguen presentación y selección accesible. Las funciones de inicialización dependen de `DOMContentLoaded` y de la inicialización previa M48/M50.5/M50.6; guardan contra doble montaje. Los callbacks de M50.5 son un contrato mínimo entre controladores, no un estado físico adicional.

## Comprobaciones del paquete incremental

- Tests focalizados M50.7: **9 Python** de estructura/sintaxis y **48 comprobaciones JavaScript** con DOM simulado, correctos.
- Regresión focal de compatibilidad: **7 Python M50.5 + 7 Python M50.6** correctas; JavaScript M50.5 (**29 comprobaciones**), M50.6 (**25 comprobaciones**), M50.4 (**5 casos**) y M50.3 (**4 casos**) correctos. En total, **23 tests Python** de los archivos disponibles, sin fallos.
- Comprobación sintáctica Jinja y Node, sin arranque de Flask ni evaluación de ecuaciones termodinámicas. Un intento de Chromium headless sobre una plantilla de prueba no llegó a arrancar y **no se contabiliza como prueba superada**.

## Integración en Windows · 13-11-2026

- Pasaron 23 pruebas Python focalizadas (9 del 50.7 y 14 del 50.5/50.6) y 31 pruebas de Node. La regresión general del repositorio ejecutó 845 pruebas, con 835 correctas, 10 omitidas y 0 fallos. Tras los ajustes se repitieron las 9 pruebas Python del 50.7 y su prueba de Node, que pasó 49 comprobaciones internas.
- Chrome con Flask verificó las seis piezas, las fichas, estaciones, los cinco gráficos de Termodinámica y su informe. Tobera convergente mostró Mach y presión; el caso convergente-divergente del modo A con caudal de 20 kg/s y semiángulo de 15° también produjo temperatura, velocidad y geometría. El punto HPC apareció en C y quedó ausente en A/B, que tampoco calcularon rpm.
- Se corrigió el enlace a la ficha SVG de la tobera, la regla CSS que ocultaba las estaciones y el informe, y la restauración de la subvista gráfica al cambiar el estado del motor. Se comprobaron carga por fragmento, selección con teclado, zoom conservado, exportación SVG/PNG, ausencia de identificadores duplicados y conservación de la referencia del comparador. Las transiciones entre los siete espacios no enviaron peticiones de simulación. El HTTP 422 retiró los SVG previos y el restablecimiento del diseño C recuperó el punto.
- Se midieron las cuatro vistas y sus subvistas a 1920, 1366, 768 y 390 px, sin desbordamiento horizontal de la página.

## Limitaciones que siguen existiendo

- No se crean magnitudes físicas, validaciones experimentales ni mapas adicionales. El usuario debe seguir comprobando la disponibilidad de cada gráfica y su interpretación.
- La navegación secundaria cambia únicamente la presentación, no el modelo ni el estado del motor.
- Estudios y Comparador mantienen la distribución anterior: su reorganización se reserva para **50.8**; la revisión final responsive y accesibilidad corresponde al **50.9**.
- Queda pendiente la revisión visual personal de la legibilidad y la distribución.

## Commit asociado

**Pendiente.** Este ZIP no se ha publicado; no se han realizado commits ni push. Base del trabajo: `4cbd77769e4e8d0f2888685c3ba4ab31aef8e141`.
