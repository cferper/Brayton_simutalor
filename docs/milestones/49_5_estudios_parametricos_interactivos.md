# Milestone 49.5 — Estudios paramétricos interactivos

## Base verificada

Rama `mejoras/cp-variable`; commit inicial publicado
`fa81eef98f5b1c18c6c13941d5b0f33b6e30fdfe` (milestone 49.4).
El árbol de trabajo de partida estaba limpio. Se conservan íntegramente las
simulaciones, sus SVG, el API original y las rutas de la aplicación.

## Arquitectura

- **Python:** `estudios_parametricos_49_5.py` valida los ejes, crea una
  configuración completa por punto y llama directamente a
  `simular_turborreactor(valores)`, el mismo solucionador que utiliza el punto
  motor. No hay aproximaciones termodinámicas ni sustituciones entre modos.
- **Flask:** `POST /api/turborreactor/estudio` recibe JSON
  `{parametros:{...},estudio:{...}}` y retorna `{ok:true, estudio:{...}}`, o
  HTTP 400 con un error de configuración. El endpoint `/simular` se conserva.
- **JavaScript:** `static/estudios_parametricos_49_5.js` gestiona la solicitud
  explícita, el selector de magnitudes, zoom, consulta de puntos, exportación
  y comparación temporal. Dibuja SVG a partir de los puntos numéricos que
  responde Python; nunca resuelve ecuaciones físicas.
- **HTML/CSS:** una vista conmutable «Punto motor» / «Estudios paramétricos»
  reutiliza el formulario principal como origen de parámetros constantes.
  El simulador clásico y Brayton no tienen nuevos controles ni cambios.

## Ejes, resultados y estados

| Estudio | Eje X | Eje Y | Muestras |
|---|---|---|---|
| Mach | M∞ [–] | Empuje [N] o específico [N/(kg/s)] | 2–21 (A/B); 2–9 (C) |
| T3 | T3 [K] | Empuje y TSFC en vistas separadas | 2–21 (A/B); 2–9 (C) |
| Mapa | M∞ [–] | T3 [K] | hasta 11×11 (A/B); 6×6 (C) |

Los límites de entrada son Mach 0–0,95 y T3 200–2000 K, con extremos
estrictamente crecientes. La admisibilidad real la determina el solucionador
individual. El mapa es de **celdas discretas sin interpolación**. Cada celda
contiene Mach, T3, tres métricas opcionales, estado y diagnóstico textual.

Clases de punto: `valido`, `fuera_dominio` (temperatura fuera de tablas),
`fallo_numerico` (no convergencia), `sin_solucion` (restricciones físicas) y
`no_calculado` (estado inicial antes de evaluar). El servidor ejecuta toda la
malla de manera síncrona; al completarse, la respuesta contiene todos los
puntos, incluso los que fallan. El mapa marca en gris las regiones sin valor.
Las curvas rompen sus trazos al encontrar un punto no válido. Nunca se
rellenan huecos con ceros. Si el empuje específico no es positivo o el TSFC
es indefinido, éste se devuelve `null`. El empuje absoluto también será
`null` cuando la modalidad A carezca de caudal impuesto; se selecciona por
defecto su magnitud específica si está disponible.

## Comparación y exportación

Se pueden guardar temporalmente dos curvas de Mach o T3 y superponerlas con
la curva actual, siempre con **igual definición y unidades** de magnitud.
Las leyendas identifican modalidad y condición fija de Mach o T3, y un aviso
detalla los parámetros fijos diferentes. No se superponen mapas de métricas
heterogéneas. Los SVG con marcadores facilitan consulta al cursor/teclado.
CSV usa las filas originales de la respuesta, parámetros fijos, estados,
unidades y valores nulos como campos vacíos; el dibujo no se digitaliza.
SVG y PNG se exportan localmente; si falla la rasterización PNG, se ofrece SVG.

## Coste y cancelación

Mediciones puntuales en el entorno de implementación (Linux, Python 3.12):

- Un punto A: ~0,0084 s; uno B: ~0,0077 s.
- Un punto C de referencia: ~0,0239 s, pero un mapa 5×5 C necesita ~6,068 s
  por iteraciones de convergencia variables; 5×5 A ~0,192 s.

Por este motivo C se limita a 6×6 y A/B a 11×11. El estudio solo se calcula
al pulsar el botón; el botón se deshabilita mientras espera, con indicador
de progreso lógico y posibilidad de abortar/ignorar la respuesta. `AbortController`
impide usar respuestas obsoletas, **pero no interrumpe necesariamente un
cálculo ya iniciado en el servidor Flask**. No se ha añadido un ejecutor
paralelo ni progreso real punto por punto.

## Pruebas y limitaciones

En Windows (2026-11-05) pasaron las 9 pruebas específicas, la suite completa
(766 correctas y 10 omitidas), los 8 tests JavaScript y la sintaxis de ambos
controladores interactivos. El cliente de pruebas Flask confirmó las rutas,
la redirección, A/B/C, rechazo de resoluciones excesivas y clasificación de
casos sin solución con magnitudes nulas. La interfaz queda pendiente de la
revisión visual manual del usuario. La clasificación `sin_solucion` puede
cubrir diferentes motivos (combustión, tobera, mapas); se conserva su texto
detallado.

No se optimiza automáticamente, no se crean nuevos mapas de componentes y
no se pretende validación experimental de motores reales.

## Commit asociado

Pendiente; implementación local sin staging, commit, push ni merge.
