# Milestone 31 — Dos gráficas adicionales de Sensibilidad cp(T)

## Estado anterior
La sección Sensibilidad tenía tres curvas: trabajo neto, rendimiento y trabajos de compresor/turbina. El OFAT y la derivación local estaban verificados y no se modifican.

## Qué se ha añadido
Dos SVG autónomos y ampliables: variación porcentual finita del parámetro, trabajo neto y rendimiento respecto de un ciclo de referencia; y temperaturas T2/T4 de muestras motoras. La sección conserva la tabla, los diagnósticos y las tres representaciones anteriores. Se avisa expresamente si x0=0, W0 o η0 son nulos o el caso base no es motor. Las regiones no operativas cortan las curvas.

## Nuevos conceptos de ingeniería
Las variaciones relativas 100·(Y−Y0)/Y0 comparan dos prestaciones adimensionalizadas en una sola escala porcentual. No equivalen a la derivada S=(x/Y)·∂Y/∂x; esta última describe un cambio local infinitesimal aproximado. Los valores térmicos T2/T4 proceden del estado de salida de las máquinas y se muestran en kelvin. Este gráfico publica solo estados motores para evitar interpretaciones de operación erróneas.

## Nuevos conceptos de Python
El módulo de presentación graficas_sensibilidad_cp.py consume la colección de muestras de la Fase 2E sin volver a llamar al solucionador 2B. Los dicts con operativas=None generan tramos discontinuos. El retorno (SVG, diagnóstico) separa visualización de mensajes físicos. Los atributos data-serie, data-x y data-valor permiten contrastar los datos sin inspeccionar píxeles.

## Qué hemos aprendido
Comparar cambios relativos de dos indicadores de unidades distintas es lícito si ambos se normalizan contra su valor de referencia no nulo. Las condiciones de dominio tienen prioridad frente a la continuidad visual. Los SVG son representaciones discretas de estados resueltos, no predicciones fuera de la malla.

## Verificación
tests/test_graficas_sensibilidad_31.py contrasta puntos contra barrido_cp_variable, referencias singulares y no motoras, huecos, temperaturas e integración Flask. Además se mantiene la suite íntegra vigente de milestone 30. La inspección final de pantalla se hará en Windows. No se realiza validación experimental.

## Limitaciones que siguen existiendo
El análisis continúa siendo OFAT, no sensibilidad global ni propagación estadística de incertidumbre. No se extrapolan valores ni se recalculan estados de ciclos excluidos.

## Commit asociado
Pendiente hasta publicación.
