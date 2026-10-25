# Milestone 32 — Mapa de viabilidad y cortes de diseño cp(T)

## Estado anterior
Mapa rp–T3 con dos representaciones continuas por color de trabajo neto y rendimiento sobre celdas motoras. La malla guarda también el diagnóstico de las celdas no motoras e inválidas.

## Qué se ha añadido
Una representación categórica de las cinco clases de celda, sin confundir «no motor» con rendimiento cero. Dos cortes de trabajo y rendimiento frente a rp usando exclusivamente las filas T3 inferior, central y superior ya calculadas; se muestra el valor real de cada T3. Los dos mapas previos, las tablas de mejores puntos muestreados y la comparación con óptimos continuos A/B se conservan.

## Nuevos conceptos de ingeniería
Un mapa de viabilidad es discreto: colorear estados por celda no crea una frontera analítica interpolada. Los cortes ilustran dependencia de rp a tres T3 distintas, sin reoptimizar ni igualar sus valores con un óptimo continuo. Trabajo neto y rendimiento no se mezclan en el mismo eje; se usan kJ/kg y porcentaje respectivamente, aunque el solucionador conserva η como fracción interna.

## Nuevos conceptos de Python
graficas_mapa_cp.py es una capa SVG pura. El bucle enumerate sobre filas y columnas crea rectángulos con identificadores de estado; los cortes leen filas existentes y cierran la polilínea cuando una muestra no es operativa. Los atributos data-rp/data-T3/data-valor permiten verificar numericamente los gráficos con ElementTree.

## Qué hemos aprendido
La misma matriz física admite varias preguntas distintas: ¿cuánto produce el ciclo?, ¿qué fracción aprovecha?, y ¿en qué región existe operación motora? Un corte de malla es un muestreo, nunca una función interpolada continua ni una curva de óptimos.

## Verificación
tests/test_graficas_mapa_32.py contrasta atributos de todas las celdas con su diccionario científico, valores de tres filas, enmascaramiento, el caso sin motor y la integración Flask. Se mantiene la suite completa vigente y se ejecuta el workflow de Actions. La revisión final del aspecto visual sigue en Windows.

## Limitaciones que siguen existiendo
Máximo 51×51 puntos, fronteras visibles dependientes de resolución, sin mapa real de turbomáquinas ni interpolación. Las filas seleccionadas son las tres posiciones de la malla, no temperaturas de consigna independientes.

## Commit asociado
Pendiente de publicación.
