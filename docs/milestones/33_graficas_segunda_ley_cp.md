# Milestone 33 — Gráficas de segunda ley y exergía física con cp(T)

## Estado anterior
Un gráfico de barras de destrucción parcial de exergía en compresor y turbina; los estados termodinámicos y balances 2G estaban disponibles en tablas y diagnósticos.

## Qué se ha añadido
Tres gráficos SVG a partir de estados 2B y estudio 2G: exergía física e1–e4 con referencia ambiental, generación de entropía de dos turbomáquinas, y balances exergéticos independientes compresor/turbina con contribuciones firmadas y residuos. Se conserva el gráfico inicial y el visor ampliable.

## Nuevos conceptos de ingeniería
La exergía física es (h−h0)−T0(s−s0), en kJ/kg y referida a T0/p0. La generación adiabática de entropía es s2−s1 en compresor y s4−s3 en turbina, en kJ/(kg·K). Gouy–Stodola da destrucción T0·s_gen. Los balances son wc=(e2−e1)+eD,c y (e3−e4)=wt+eD,t. El signo de cada contribución y el residuo se conservan sin truncar: una inconsistencia científica impide dibujar balances como válidos.

## Nuevos conceptos de Python
graficas_segunda_ley_cp.py es un módulo de presentación pura que no llama a h, s ni resolver_ciclo. Su auxiliar de barras firmadas conserva el signo; ejes, título y unidades se adaptan a los datos. Atributos data-rol, data-valor y data-residuo permiten pruebas numéricas de la representación. La caché de estados del ciclo existente no cambia.

## Qué hemos aprendido
La segunda ley permite comparar capacidad de generar trabajo y sus pérdidas. Las barras del compresor y turbina contienen flujos de exergía y trabajo con convenciones explícitas, no dos rendimientos globales. La suma eD,c+eD,t no es la exergía destruida total del ciclo: faltan procesos externos y combustión química real.

## Verificación
tests/test_graficas_segunda_ley_33.py contrasta estados, entropías, barras y signos, residuos, ciclo no motor, referencia ambiental y Flask. La suite científica y web vigente completa se ejecuta en GitHub Actions. Los gráficos requieren revisión visual definitiva en Windows. No se afirma validación experimental.

## Limitaciones que siguen existiendo
No hay exergía química, transferencia térmica exergética modelada ni rendimiento global. Las temperaturas de ambiente deben permanecer en 200–2000 K. La representación no corrige incoherencias físicas del análisis y no oculta residuos.

## Commit asociado
Pendiente hasta publicación.
