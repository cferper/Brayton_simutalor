# Milestone 29 — Gráficas científicas de Resultados y Optimización con cp(T)

**Fecha de trabajo:** 24/10/2026. **Rama objetivo:** mejoras/cp-variable.
**Commit base verificado por conector GitHub:** 9fe989bc58bda3fbe031265d694b7dc95b21a2f5.
**Commit de esta iteración:** pendiente hasta su publicación.

## Estado anterior

El dashboard cp(T) tenía ocho SVG: uno T–s en Resultados, uno dual de trabajo y rendimiento en Optimización, tres de Sensibilidad, dos de Mapa y uno de Segunda ley. Los fundamentos teóricos extensos de milestone 28 y el visor modal ampliable ya existían.

## Qué se ha añadido

| Sección | Antes | Después | Qué representa |
|---|---:|---:|---|
| Resultados | 1 | 6 | T–s mejorado, P–v específico, cp(T), γ(T), balance de cinco energías y comparación de componentes ideales/configurados. |
| Optimización | 1 | 3 | Trabajo–rp, rendimiento–rp y compromiso trabajo–rendimiento, con A/B interiores cuando proceda. |
| Otras seis secciones | 6 | 6 | Sin cambios de funcionalidad ni gráficos. |
| **Total potencial** | **8** | **15** | Los nueve SVG de las dos secciones activas se calculan con una simulación; las otras seis requieren sus acciones. |

El nuevo módulo de presentación es `graficas_cp_variable.py`; `cp_variable_web.preparar_resultados` reúne sus SVG en dos listas sin duplicar el barrido optimizador. `templates/index.html` reutiliza macro `grafica_cp`, cuadrícula responsive y visor JavaScript. No se han modificado los algoritmos 2A–2G, formularios, informes ni las otras secciones.

## Nuevos conceptos de ingeniería

1. **Estado y trayectoria:** T–s y P–v sitúan los estados científicos 1–4, pero las uniones discontinuas son esquemáticas, no politrópicas ni procesos reales integrados.
2. **Gas ideal con calor variable:** P–v usa `v=R_AIRE·T/(1000·p_kPa)` en m³/kg; cp(T) y γ(T) se evalúan con el mismo aire seco ideal en 200–2000 K, sin extrapolar.
3. **Balances energéticos:** cinco magnitudes específicas en kJ/kg mantienen la convención del solucionador y la primera ley; no equivalen a potencia sin caudal.
4. **Comparación homogénea:** los componentes ideales se simulan con `ηc=ηt=1`, `δ=0`, pero conservando T1, T3, rp, p1 y el mismo cp(T). La representación usa paneles separados para kJ/kg y porcentaje.
5. **Óptimos y muestras:** los gráficos de rp se basan en un único conjunto de 90 ciclos motores evaluados; A/B provienen directamente del optimizador continuo 2C, no de escoger el mejor píxel. Un supremo abierto nunca se marca como diseño operativo.

## Nuevos conceptos de Python

- Funciones pequeñas y un módulo dedicado a representación, sin lógica científica duplicada.
- Una función anidada de coordenadas para proyectar pares físicos a posiciones SVG.
- Transformación logarítmica de posición, conservando etiquetas numéricas de rp.
- Listas con `None` para impedir unir tramos no calculables.
- Atributos SVG `data-estado`, `data-x`, `data-y` y `data-valor` para probar datos numéricos, no solo presencia de texto.
- Dos listas de tuplas `(título, SVG | None, explicación)` recorridas por Jinja y ampliadas por el visor existente.
- Tratamiento local de error de la comparación ideal, sin convertir un fallo opcional en fallo de la simulación principal.

## Qué hemos aprendido

Un gráfico científicamente útil debe preservar datos, unidades, condiciones de admisibilidad y tipo de extremo. La misma tabla de muestras puede visualizarse con ejes diferentes sin repetir el análisis termodinámico. La comparación ideal debe mantener **las propiedades variables** para aislar el efecto de las pérdidas internas.

## Pruebas y alcance

`tests/test_graficas_cp_variable.py` contrasta estados, unidades, fórmula P–v, propiedades, balances, comparación ideal y configurada, marcadores A/B, supremos, discontinuidades e integración Flask/visor. El workflow `.github/workflows/verificacion_web_cp_variable.yml` ejecuta esas pruebas junto con las regresiones web ya existentes. No se afirma validación experimental ni inspección visual de la aplicación en Windows.

**Verificación local realizada:** 110/110 pruebas focalizadas y de regresión web correctas (12 nuevas). Cinco tipos de SVG fueron renderizados a PNG y examinados visualmente fuera de Windows: T–s, P–v, cp(T), trabajo–rp, compromiso; también se revisó la comparación ideal/configurado. El JavaScript de ampliación no se modificó.

**Suite histórica completa:** se ejecutó una vez sobre el commit anterior (427 métodos: 18 fallos y 62 errores) y sobre los nuevos archivos (439 métodos: exactamente 18 fallos y 62 errores). Estas pruebas heredadas esperan métodos Flask e informes históricos ya eliminados en fases anteriores; **no son regresiones introducidas por el milestone 29**. Por eso la aceptación funcional se basa en las 110 pruebas web vigentes y GitHub Actions de esta rama. No se han alterado las pruebas históricas para hacerlas pasar artificialmente.

## Limitaciones que siguen existiendo

- No hay trayectorias exactas T–s/P–v, mapa real de turbomáquina, geometría, caudal, potencia o empuje.
- La curva de compromiso no es necesariamente una frontera de Pareto.
- Si el ciclo base o el ideal no es motor/no calculable, la tarjeta comparativa muestra diagnóstico, sin barras engañosas.
- Los marcadores A/B aparecen solo para máximos **interiores**; los supremos se informan en las fichas existentes.
- El tamaño y legibilidad final del SVG y la ampliación del modal requieren revisión manual en el navegador Windows.

## Commit asociado

Pendiente hasta la creación y publicación del commit autorizado. El hash base indicado arriba es anterior a este milestone.
