# Milestone 49.3 — Selector de modalidades y visor de gráficas

## Estado anterior

El 49.2 había creado dos columnas y actualizado tarjetas y SVG, pero el
selector A/B/C estaba en un desplegable, la T–s quedaba relegada a la tercera
figura y algunas tarjetas mostraban «No aplicable» repetidamente.

Base verificada: `b1d8f0e6f2b6c14735f2d0dae5d71298b4d98853`, rama
`mejoras/cp-variable`, GitHub. La copia de partida estaba limpia.

## Implementación

- Tres botones visibles A/B/C, con `aria-pressed`, sincronizados mediante
  eventos `change` con el **único** campo real `modo_caudal` del formulario.
- Panel izquierdo contextual: gasto de aire en A; tobera y áreas relevantes
  en B y C; Mach y T3 siempre visibles. Otras entradas ya existentes se
  acceden mediante «Configuración avanzada». La lógica de habilitación
  original y las validaciones del backend siguen siendo autoritativas.
- Cambios de modalidad, ambiente o campos avanzados disparan la misma
  simulación HTTP con espera de 350 ms y protección contra respuestas tardías.
- Visor de SVG con pestañas T–s, Mach, presión y geometría, disponible cuando
  el servidor entregue el SVG correspondiente. Cambiar de pestaña no realiza
  peticiones HTTP. La pestaña elegida se conserva entre cálculos válidos.
- Las tarjetas con magnitudes ausentes se ocultan del resumen; se explican
  dos ausencias conocidas: fuerza absoluta sin gasto prescrito en A, y rpm
  fuera del modo C. Errores HTTP 422 mantienen sus mensajes.
- Conservación del clásico, Brayton y todas las rutas del 49.1.

## Fundamento de ingeniería

A dimensiona a partir del gasto de aire impuesto; B obtiene el gasto
compatible con la geometría fija; C acopla mapas educativos de compresor,
turbina y eje. T3 [K] es temperatura total de entrada a turbina, no salida.
El visor usa solo `svg_ts`, `svg_mach_axial`, `svg_presion_axial` y
`svg_geometria_conica` (con las alternativas ya existentes en la API), sin
crear gráficas nuevas ni modificar modelos físicos.

## Verificación y límites

Se añaden pruebas estructurales de selección, gráfico, tarjetas y rutas,
además de las ocho pruebas JavaScript previas. Los tests HTTP con Flask y la
inspección visual de escritorio/móvil deben ejecutarse en Windows si Flask
no está disponible. La interfaz no sustituye la validación física externa.

## Commit asociado

Pendiente: no se ha hecho staging, commit ni push.
