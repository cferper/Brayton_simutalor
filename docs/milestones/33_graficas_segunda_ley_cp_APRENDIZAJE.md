# Milestone 33 — Aprendizaje: representar la segunda ley sin inventar física

**Base verificada:** 3edbe773947928534832ffa9457021db656d506c; rama mejoras/cp-variable. Fecha: 25/10/2026.

## INTERPRETACIÓN FÍSICA / INGENIERÍA
La primera ley conserva energía. La segunda ley señala qué parte de la posibilidad de obtener trabajo se pierde por irreversibilidades. En nuestro modelo de aire ideal cp(T), la entropía de un estado incluye temperatura y presión. El estudio de Fase 2G usa las entropías de los cuatro estados resueltos por 2B, sin recalcular las ecuaciones del ciclo.

La **exergía física** específica de un estado de flujo con respecto al ambiente T0/p0 es e=(h−h0)−T0(s−s0). El símbolo e mide el potencial físico de producir trabajo referido al estado ambiental, en kJ/kg. No es energía total ni exergía química. El primer nuevo gráfico muestra los cuatro valores e1..e4. Al variar T0/p0 cambiarán esos valores, aunque el ciclo haya mantenido sus siete parámetros. Cada barra preserva el signo de la magnitud calculada.

En un compresor adiabático, la entropía generada es s_gen,c=s2−s1. En una turbina adiabática, s_gen,t=s4−s3. Se expresan en kJ/(kg·K). **Entropía de estado** no es lo mismo que **incremento de entropía** y tampoco es lo mismo que **generación por irreversibilidad**, que para el volumen de control debe considerar las transferencias. El nuevo gráfico de generación solo atribuye valores a las dos máquinas adiabáticas.

Por Gouy–Stodola, la exergía destruida en cada máquina es eD=T0*s_gen [kJ/kg]. El programa ya contrastaba ese producto con los balances independientes:
- Compresor: wc=(e2−e1)+eD,c.
- Turbina: (e3−e4)=wt+eD,t.

En el gráfico, cada término aparece como barra individual con su valor real firmado y la magnitud del **residuo** numérico. La identidad se cumple si la suma de contribuciones corresponde al lado opuesto dentro de la tolerancia de 2G. No se sustituyen términos negativos por su valor absoluto para embellecer el gráfico.

**Advertencia:** las dos destrucciones no representan la destrucción total del ciclo Brayton. No conocemos la fuente de calor, la exergía química del combustible ni los volúmenes de control completos del aporte/rechazo térmico. Tampoco se calcula rendimiento exergético global.

Un ciclo no motor puede tener estados y balances calculables; se muestran como diagnóstico, pero no se le atribuyen prestaciones motoras. Si 2G detecta inconsistencia, las nuevas barras no se presentan como balances correctos y se conservan los diagnósticos existentes.

## PYTHON: firmas y recorrido de datos
- \`_svg_barras_signo(datos, titulo, unidad, nota)\`: recibe una lista de tuplas (etiqueta str, valor float, color str), devuelve SVG o None para entrada no finita/vacía. El cero de la escala vertical es un origen central: valores positivos dibujan anchura a derecha y negativos a izquierda. Conserva data-rol y data-valor para verificar la procedencia.
- \`svg_exergias_estados(estudio)\`: recibe el dict 2G, devuelve SVG/None, lee exergias [kJ/kg], T0 [K] y p0 [kPa], sin resolver propiedades ni alterar datos. Si el estado del estudio es inconsistente devuelve None.
- \`svg_generacion_entropia(estudio)\`: recibe el dict 2G, devuelve SVG/None, muestra dos valores [kJ/(kg·K)] e impide representar generación negativa significativa o un análisis inconsistente como correcto.
- \`svg_balances_exergia(ciclo, estudio)\`: recibe dict de ciclo 2B y dict 2G, devuelve SVG/None. Lee wc/wt y exergias y destrucciones; forma únicamente las diferencias exergéticas necesarias para etiquetar el balance, sin recalcular estados o generar nuevas ecuaciones. Añade data-residuo-c y data-residuo-t para que la comprobación de exactitud no dependa del dibujo.

La integración ocurre en web_app.index → cp_variable_web.preparar_segunda_ley: primero se consulta la caché de resolver_ciclo en función de los siete parámetros, después analizar_segunda_ley_cp_variable actualiza el ambiente y finalmente graficas_segunda_ley_cp construye los SVG. templates/index.html utiliza la macro grafica_cp y static/dashboard.js para ampliar sin recargar.

## Ejercicio guiado
Ejecuta la condición base T0=288,15 K, p0=100 kPa. Comprueba cómo eD,c y eD,t son coherentes con las generaciones al multiplicar por T0. Inspecciona el balance y registra sus residuos. Cambia solo T0 a 300 K: los cuatro estados del ciclo deben permanecer iguales, pero las destrucciones variarán con T0 y las exergías de estado con la nueva referencia.

## Pruebas y limitaciones
tests/test_graficas_segunda_ley_33.py verifica componentes numéricos de cada barra, residuos, signos, casos inconsistentes, condición no motora, referencia ambiental y Flask. Son pruebas internas del software, no validación experimental. La galería definitiva debe revisarse visualmente en Windows.
