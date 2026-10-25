# Milestone 32 — Aprendizaje: mapas de viabilidad y cortes rp–T3

**Base verificada:** a6fab62f5759e199af883c29ef1ddea74aad7037; rama mejoras/cp-variable. Fecha: 25/10/2026.

## INTERPRETACIÓN FÍSICA / INGENIERÍA
El problema de diseño usa dos variables: la relación de compresión rp y la temperatura T3. Todas las demás entradas permanecen constantes. La Fase 2F resuelve una malla logarítmica en rp y lineal en T3, cada celda con datos físicos propios y una clasificación.

La categoría **motor** significa que el punto satisface las condiciones de ciclo motor del solucionador. «Calculable no motor» significa que las ecuaciones devuelven estados, pero no se debe interpretar el rendimiento como prestación operativa. «Fuera de rango» significa que se excede el intervalo de correlaciones 200–2000 K; «entrada inválida» rechaza una condición inadmisible; «error numérico» representa un cálculo sin resultado fiable. El mapa de clases muestra esos cinco estados con colores separados de la escala de prestaciones.

Una frontera dibujada en el mapa es una frontera **muestreada**, no la raíz exacta del límite físico. Un par de celdas adyacentes con distinta clasificación no determina la ubicación continua del cambio de viabilidad. No se interpola ni se crea una falsa curva exacta.

Para comparar diseños a temperatura constante se toman tres **filas reales**: primera, central y última. Cada fila contiene las relaciones de presión y las prestaciones calculadas para su T3 exacta. La curva de trabajo W_net [kJ/kg] y la curva de rendimiento η [%] son dos gráficos distintos, aunque usan los mismos nodos de la malla. Un hueco no se rellena con cero ni se conecta visualmente a través de una zona excluida.

El mejor punto encontrado sobre las muestras de una malla no equivale al máximo matemático del modelo; la Fase 2C calcula óptimos continuos A/B a una T3 fija que debe declararse al compararlos.

## PYTHON: funciones introducidas
- \`svg_mapa_viabilidad(estudio)\`: recibe el diccionario de calcular_mapa_cp_variable, con rps, T3s, filas y dimensiones. Devuelve un SVG de todos los nodos, incluso cuando no hay motor. Cada rectángulo tiene data-estado/data-rp/data-T3 y su tooltip; las unidades de los ejes son rp adimensional y T3 [K]. Un estado desconocido produce ValueError en lugar de asignar color silencioso.
- \`svg_cortes_mapa(estudio, magnitud)\`: recibe el mismo dict y la clave trabajo_neto o rendimiento. Devuelve un SVG o None si no hay muestras motoras en las tres filas. Convierte fracción de rendimiento en % para la visualización, conservando el dato original; el trabajo se representa en kJ/kg. Rechaza magnitudes ajenas con ValueError. La coordenada horizontal utiliza log(rp), pero las marcas muestran rp real.

El código usa índices [0,(n_T3−1)//2,n_T3−1], zip y una función anidada cerrar() que corta el segmento cuando operativas es None. Un título SVG permite consultar el punto; no constituye una interpolación entre celdas. Los atributos data-valor son verificables directamente sin comparar imágenes.

## Flujo de ejecución
Formulario del Mapa → web_app.index → cp_variable_web.preparar_mapa → calcular_mapa_cp_variable (Fase 2F) → graficas_mapa_cp → listas SVG → macro grafica_cp en templates/index.html → modal existente de static/dashboard.js. No se hacen nuevas llamadas a resolver_ciclo: los gráficos solo leen filas ya calculadas.

## Ejercicio
Ejecuta un mapa 7×7 entre rp=2–40 y T3=1200–1800 K. En el mapa de categorías localiza una celda no motora. Identifica su posición en los cortes: la prestación debe faltar, no aparecer como cero. Aumenta n_rp y comprueba que el aspecto de la frontera cambia con la resolución; no concluyas que la física haya cambiado.

## Verificación y limitaciones
tests/test_graficas_mapa_32.py contrasta cada rectángulo y cada muestra contra el diccionario original y comprueba el caso sin motor. Es verificación interna, no validación física experimental. La inspección visual definitiva corresponde al navegador Windows.
