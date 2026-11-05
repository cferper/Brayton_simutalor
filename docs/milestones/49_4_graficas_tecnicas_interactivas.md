# Milestone 49.4 — Gráficas técnicas interactivas

## Base y alcance

- Rama: `mejoras/cp-variable`; commit remoto de partida: `ca8d0554935607bf7cc68e051aec9b617c9ef40e`.
- Se confirmó en GitHub la publicación de los componentes y las pruebas de 49.3.
- No se modifican solucionadores, cálculos físicos, formularios, API ni rutas.

## Arquitectura

Los SVG siguen generándose en Python con los estados que ya calculaba el motor.
Se han añadido **anotaciones de presentación** `data-plot-info` a puntos reales:

- `turborreactor_web.svg_ts_turborreactor`: estados discretos de remanso,
  eventualmente salida estática; entropía calculada con las propiedades existentes.
- `perfil_axial_tobera_conica.svg_perfil_axial`: todos los puntos obtenidos
  mediante la proyección axial existente, identificando garganta, salida y
  las ramas **antes/después** del choque en la misma coordenada.
- `geometria_tobera_conica.svg_geometria_conica`: garganta y salida con
  posición, radio y diámetro; la escala original es uniforme en x/y.

La interfaz 49.3 continúa solicitando **una** simulación con
`POST /api/turborreactor/simular`. Al recibirla, inserta sus SVG en las cuatro
pestañas y el explorador 49.4 reinicia el zoom. El visor actúa **únicamente sobre
el DOM**: ninguna interacción de consulta, zoom o descarga envía HTTP.

## Interacción y exportación

- Zoom por botones (100–400 %), Ctrl + rueda del ratón, desplazamiento de la
  región ampliada con scroll nativo, incluida interacción táctil. Escala
  **uniformemente** la imagen; no transforma coordenadas físicas ni modifica
  los datos, e impide reducir por debajo de la vista original.
- Zoom independiente en cada pestaña. «Vista original» restablece la activa;
  un cálculo nuevo restablece todas para evitar conservar un encuadre obsoleto.
- Los puntos SVG identificados se consultan con cursor, toque/clic, foco del
  teclado y Enter/Espacio. No se interpolan otros puntos por cercanía visual.
- Descarga SVG autocontenido mediante serialización del SVG original sin
  ampliar, con los rótulos de unidades y leyendas intactos.
- PNG opcional en navegadores con canvas/blob/imagen SVG compatibles. Si falla,
  se comunica el error y se mantiene disponible la opción SVG. Se rasteriza a
  doble resolución y nunca se extraen datos de píxeles.
- No se añade CSV: los datos de los SVG alternativos de tobera no comparten un
  esquema de salida uniforme; exportarlos exigiría una ampliación de API.

## Discontinuidades y límites

Los segmentos pre/postchoque siguen siendo dos `polyline` diferentes. Los
marcadores muestran los estados previos y posteriores sin inventar una curva
continua entre ambos. El T–s conserva uniones **esquemáticas** entre estados,
no representa trayectorias reversibles exactas. Los perfiles axiales solo están
disponibles si el modelo ofrece geometría cónica compatible; el sistema de
pestañas del 49.3 conserva sus alternativas y oculta las no disponibles.

## Comprobaciones

Pruebas nuevas: integridad de estados T–s, separación del choque y presión/Mach
de sus ramas, geometría y unidades, presencia de controles, unicidad de llamada
API y límites de zoom con Node.js. Se conservan las pruebas históricas.

Limitaciones: zoom a través de scroll del SVG completo (los títulos interiores
pueden desplazarse, pero se recuperan con scroll o vista original); no hay
interpolación ni búsqueda del punto más cercano a lo largo del trazo, ni barridos
paramétricos. En Windows conviene verificar manualmente PNG y el comportamiento
táctil en el navegador real. No se han generado nuevas series científicas.
