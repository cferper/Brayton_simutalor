# Milestone 41 — Sensibilidad y mapas de prestaciones del turborreactor cp(T)

## Estado anterior

En `mejoras/cp-variable`, commit verificado de partida
`bab698a026fc336efdda5ed24b6e7d9f22bd0a97`, la web del turborreactor
tenía cinco pantallas independientes y resolvía un único punto operativo.
Los barridos, clasificaciones y Pareto **ya existían** en
`mapas_prestaciones_turborreactor_cp.py` (milestones 38 y 39), sin interfaz.
El simulador Brayton convencional tiene su propia interfaz y no se modifica.

## Qué se ha añadido

- Dos pantallas a `/turborreactor`: **Sensibilidad** (OFAT, 2–31 puntos) y
  **Mapas de prestaciones** (malla entre 2×2 y 15×15). La navegación conserva
  siete paneles exclusivos, enlaces `#`, historial y teclado con JavaScript;
  sin JavaScript, permanecen visibles y funcionan los formularios HTTP POST.
- El adaptador de presentación `prestaciones_turborreactor_web.py`: interpreta
  controles, impone rangos y tamaños, delega la evaluación física en los
  barridos científicos M38, construye tablas y SVG autocontenidos.
- OFAT de rp, T3, Mach, ηc, ηt, πd y pérdida de cámara δ (%). Todos los demás
  parámetros permanecen en el valor configurado; δ pasa de porcentaje a
  fracción **una sola vez**. Dos curvas: Fs neto y TSFC, con huecos y cruces
  para estados no válidos y sin resultados falsos.
- Mapa A rp–T3 con ambiente y Mach fijos: empuje, TSFC, recuentos, extremos,
  fronteras y dispersión Pareto. Mapa B Mach–altitud ISA: las dos magnitudes,
  clasificación y extremos **descriptivos**, sin Pareto conjunto.
- Un envío de estudio conserva los campos del motor y vuelve a presentar el
  cálculo individual en Resultados. Los formularios son hermanos, no anidados;
  el JavaScript copia las entradas actualmente editadas al enviarlos. Sin JS
  se usan los últimos valores reflejados por el servidor.
- Pruebas específicas M41 y paso nuevo en GitHub Actions.

## Nuevos conceptos de ingeniería

OFAT estudia una dependencia parcial, sin evaluar interacciones de parámetros.
Los mapas muestran cómo cambian dos variables a la vez, pero **no** son mapas
reales de funcionamiento fuera de diseño. Cada celda es una resolución completa
de compresor, aporte energético con combustible equivalente, eje, turbina y
tobera, con rendimientos prescritos.

Fs neto [N/(kg/s de aire)] suma momentos de salida y presión, menos el momento
entrante del aire; TSFC [kg/(N·h)] = 3600 f/Fs está definido cuando Fs>0.
Para clasificar un punto se reutiliza M38/M39: `valido`,
`empuje_no_positivo`, `sin_expansion`, `inadmisible`, `fallo_numerico`.
Los valores no disponibles permanecen `None`/«—», no pasan a cero. Si un punto
sin empuje positivo tiene Fs calculado, el valor físico se conserva en la tabla,
pero no se usa en el frente ni se conecta en las curvas de configuraciones válidas.

El frente de Pareto identifica puntos evaluados no dominados en dos objetivos
contrapuestos: **maximizar Fs y minimizar TSFC**, sin extrapolar a soluciones
continuas. Sólo corresponde a rp–T3 con condiciones exteriores comunes; cambiar
Mach y altitud cambia el problema físico de referencia.

## Nuevos conceptos de Python

En `prestaciones_turborreactor_web.py` se separa el parsing de valores finitos,
la construcción de vectores equiespaciados, los despachos por tipo de estudio y
el dibujo SVG como `str`. `preparar_estudio(accion, formulario, valores_motor)`
usa `leer_turborreactor` y `barrer_rp_t3` / `barrer_mach_altitud`, sin ecuaciones
propias ni dependencias adicionales. La presentación guarda tanto el punto
científico con su `estado` como las métricas válidas/indefinidas.

Flask diferencia `accion='simular'`, `'sensibilidad'` y `'mapa'`, con errores
HTTP 400 en formularios inválidos; los errores no generan archivos. Jinja
presenta las nuevas secciones y tablas; el JS sincroniza hidden inputs de los
formularios hermanos sin alterar el ciclo Brayton. SVG conserva tamaños
propios, `viewBox`, textos con unidades y desplazamiento horizontal de su
región enfocable mediante teclado. La interfaz dibuja explícitamente `×` y
estado en la tabla, no distingue viabilidad sólo por colores.

## Casos reproducibles

Se usan **exactamente** las convenciones de referencia del milestone 38.

| Estudio | Condiciones y malla | Válidos | Máximo Fs [N/(kg/s)] | Mínimo TSFC [kg/(N·h)] | Pareto |
| --- | --- | ---: | ---: | ---: | --- |
| A | rp=5,7.5,10,12.5,15; T3=1400,1500,1600,1700,1800 K; 288,15 K; 100 kPa; Mach=0; πd=1 | 25/25 | 1077,684377 (15, 1800 K) | 0,086202290 (15, 1400 K) | 7 puntos |
| B | Mach=0,.2,.4,.6,.8; ISA=0,5000,10000,15000,20000 m; rp=10; T3=1600 K; **πd=.98** | 25/25 | 1030,247814 (Mach=0; 15 km) | 0,105830471 (Mach=0; 0 m) | No aplicable |
| C | OFAT rp=4,6,8,10,12,14,16,18,20; T3=1600 K; 288,15 K; 100 kPa; Mach=0; πd=1 | 9/9 | 966,084294 (rp=14) | 0,092158889 (rp=20) | 4 puntos (evaluación científica) |

Los casos A/B comprueban los retornos de los barridos integrados en la web;
C comprueba la curva OFAT y contrasta Pareto de M38 sobre sus puntos válidos.
La interfaz no declara un Pareto para B ni asegura óptimos continuos.

## Verificación del software y validación física

- **Verificación:** `tests/test_prestaciones_turborreactor_web_41.py` (25
  pruebas) contrasta referencias del milestone 38, contratos del adaptador,
  mallas 15×15 y OFAT 31, errores, estados, tablas, rutas, ausencia de
  formularios anidados, preservación del ciclo individual y del historial.
  También se ha ejecutado la batería M40 (27 pruebas) tras actualizar su
  expectativa de cinco a siete paneles. La suite completa, ejecutada en
  Linux/Python 3.12 con las dependencias del entorno de pruebas y sin modificar
  los módulos científicos, obtuvo **557 pruebas descubiertas, 548 superadas,
  nueve omitidas opcionalmente y cero fallos** (`unittest discover -s tests -q`).
- **Validación física:** no realizada. No hay ensayos de un motor real, mapas
  de componentes experimentales ni condiciones fuera de diseño contrastadas.
  Reproducir salidas de M38 verifica integración y estabilidad, **no** valida
  experimentalmente el modelo.

## Limitaciones que siguen existiendo

El flujo se representa con aire equivalente de composición fija; el combustible
es un aporte energético y los rendimientos, recuperaciones y pérdidas son
prescritos. No hay mapas reales de compresor/turbina, caudal másico absoluto,
geometría, regulación, capacidad fuera de diseño ni validación experimental.
El modelo permanece subsónico y con tobera convergente. Las restricciones de
tamaño y rango de la UI son límites educativos de interacción, no límites
estructurales o certificados.

## Commit asociado

Pendiente hasta publicación autorizada de un único commit conjunto de código,
pruebas y documentación en `mejoras/cp-variable`. No se modifican `main`, el
repositorio histórico ni Windows.
