# Milestone 38 — Mapas paramétricos de prestaciones y compromisos

## Estado anterior

La rama `mejoras/cp-variable` partía de `bdb869d609d34712b824d9a80006d9dd1b5c0bc0`
(milestone 37). Ya existían combustible equivalente, empuje específico neto
y TSFC en un punto, sin barridos ni búsqueda multicriterio.

## Qué se ha añadido

El módulo independiente `mapas_prestaciones_turborreactor_cp.py` evalúa
`resolver_turborreactor_con_combustible` sobre mallas `rp–T3` y
`Mach–altitud ISA`, devuelve las variables y estados por punto, conteos,
óptimos discretos, detección de frontera y, solo cuando el ambiente y Mach
son comunes, puntos no dominados de Pareto.

El mapa `rp–T3` permite restricciones configurables de `T3_max`, intervalos
de relación de compresión, Mach y altitud y requerimientos de empuje y margen
de expansión. Las clases de viabilidad se conservan aun cuando se relajen
estos últimos indicadores: una salida indefinida o un empuje no positivo
**nunca** entra en óptimos de empuje/TSFC. No se ha añadido ninguna gráfica.

## Nuevos conceptos de ingeniería

El compresor requiere `wc=h2-h1`, que suele aumentar con `rp` a condiciones
de entrada y rendimiento fijados. El eje exige
`eta_m(1+f)(h3-h4)=wc`, por lo que más carga puede disminuir la presión
`p4` disponible para la tobera. Elevar T3 cambia energía de cámara,
dosado `f`, expansión, empuje y TSFC. Las tendencias no son universalmente
monótonas y dependen del dominio y el modelo.

Un punto A domina otro B si `Fs_A>=Fs_B` y `TSFC_A<=TSFC_B` y al menos una
desigualdad es estricta. Pareto devuelve los puntos no dominados de los
**evaluados**: no demuestra óptimos continuos ni garantiza factibilidad de
un motor concreto. El mapa Mach–altitud no ofrece Pareto global porque
cambia el ambiente y, con Mach, la resistencia de aire de entrada; sus
extremos son descriptivos por unidad de caudal, no una elección de diseño
equivalente. Sin geometría ni gasto másico no se obtiene empuje absoluto.

## Casos reproducibles

Parámetros no indicados: `eta_c=.85`, `delta=.04`, `eta_t=.9`, `eta_m=.98`,
`eta_n=.95`, `eta_b=.99`, `PCI=43000 kJ/kg`.

| Estudio | Ejes (X / Y) | Válidos / total | Mayor Fs [N/(kg/s)] | Menor TSFC [kg/(N h)] | Pareto |
|---|---|---:|---|---|---|
| A | `rp=[5,7.5,10,12.5,15]`, `T3=[1400,1500,1600,1700,1800]` K, estático 288.15 K y 100 kPa | 25 / 25 | 1077.684377 en (15,1800) | 0.086202290 en (15,1400) | 7 puntos |
| B | `Mach=[0,.2,.4,.6,.8]`, `ISA=[0,5000,10000,15000,20000]` m, `rp=10`, `T3=1600 K`, `pi_d=.98` | 25 / 25 | 1030.247814 en (0,15000 m) | 0.105830471 en (0,0 m) | No aplicable entre ambientes distintos |
| C | `rp=[4,6,8,10,12,14,16,18,20]`, `T3=[1600]` K, estático 288.15 K y 100 kPa | 9 / 9 | 966.084294 en rp=14 | 0.092158889 en rp=20 | 4 puntos |

En A, el conjunto no dominado por `(rp, T3)` es:
`(12.5,1400), (15,1400), (12.5,1500), (15,1500), (15,1600),
(15,1700), (15,1800)`. En C: rp `14,16,18,20`. El máximo de A está
en el borde superior de ambos ejes: **no** se puede afirmar que sea el máximo
de un dominio continuo. En C, máximo Fs y mínimo TSFC no coinciden.

Para demostrar el tratamiento de descartes, aplicar en A
`restricciones={"T3_max":1500}`: los puntos con T3 superior quedan marcados
`inadmisible` y sus resultados indefinidos son `None`, no ceros. Otros
dominios pueden originar `sin_expansion`, `empuje_no_positivo` y
`fallo_numerico` explícitos.

## Nuevos conceptos de Python

`_eje` valida vectores crecientes, `_restricciones` normaliza límites,
`_incumplimiento` detecta recortes, `_punto` clasifica sin ocultar errores
de programación y `_barrer` compone filas (eje Y) y columnas (eje X).
`_resumen` usa `collections.Counter`, máximo y mínimo discretos, frontera;
`frente_pareto` usa comparación cuadrática O(n²) sin dependencias nuevas.
Funciones públicas: `barrer_rp_t3`, `barrer_mach_altitud`, `frente_pareto`.
Los puntos contienen inputs, índices, métricas y objeto científico original;
las métricas no definidas se representan con `None`.

## Qué hemos aprendido

- Un mapa paramétrico no es un mapa de operación fuera de diseño.
- El mayor empuje puede exigir un TSFC peor y viceversa.
- Un óptimo de malla puede estar en frontera y no ser un óptimo continuo.
- Las comparaciones Pareto requieren condiciones ambientales comparables.
- Una excepción numérica debe distinguirse de una configuración inadmisible.

## Limitaciones que siguen existiendo

Aire equivalente sin química de combustión, rendimientos y pérdidas
prescritos, ausencia de mapas de compresor/turbina, márgenes de bombeo,
revoluciones, geometría, compatibilidad de caudales y gasto másico absoluto.
Mallas pequeñas y resultados discretos; no se pretende optimización global
continua ni predicción meteorológica. ISA se limita a 0–20 km y Mach a [0,1).

## Verificación frente a validación

Las 15 pruebas específicas cubren el enlace exacto con milestone 37,
formas/índices, Pareto sintético independiente, máscaras, extremos,
fronteras, vacío, reproducción, restricciones y propagación explícita de
errores de programación. Un test analítico de dominancia verifica el
algoritmo, **no** valida prestaciones experimentales de motores.
La suite completa y GitHub Actions se registran en el informe de publicación.

## Referencias oficiales

- [NACA/NASA, *Performance Charts for a Turbojet System*](https://ntrs.nasa.gov/citations/19930093534): antecedente de gráficos de prestaciones, con hipótesis distintas.
- [NASA Glenn, *Specific Fuel Consumption*](https://www.grc.nasa.gov/www/k-12/airplane/sfc.html): significado de TSFC.
- [NASA Glenn, *Engine Temperature Variation*](https://www.grc.nasa.gov/WWW/K-12/airplane/etr.html): importancia de temperatura de ciclo.

## Commit asociado

Pendiente hasta publicación. No se escribe el hash del propio commit en
un documento incluido en ese mismo commit.
