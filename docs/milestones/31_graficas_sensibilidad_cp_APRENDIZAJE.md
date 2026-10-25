# Milestone 31 — Aprendizaje: del barrido OFAT a cinco gráficas

**Base comprobada:** 9c54000e34b92f5464c0a17002d88caa31b02062; rama mejoras/cp-variable. Fecha: 25/10/2026.

## Física: cambios relativos frente a derivadas
Si un ciclo motor de referencia tiene trabajo W0 y rendimiento η0, la variación de una muestra es ΔW/W0 = (W−W0)/W0. Multiplicamos por 100 para usar porcentajes. La misma operación para η permite comparar tendencias sin sumar unidades heterogéneas. El eje horizontal es 100·(x−x0)/x0 y el vertical reúne ambas respuestas porcentuales. Una subida de cinco por ciento relativo de eficiencia no es lo mismo que una subida de cinco puntos porcentuales.

Esto describe un cambio **finito** respecto del caso base. En cambio la sensibilidad local S=(x/Y)·dY/dx requiere aproximar una derivada; la Fase 2E usa diferencias finitas, comprueba la estabilidad al reducir el paso y puede dejar el resultado sin definir. No intercambiamos ambos indicadores.

Si x0=0 (por ejemplo δ=0) dividir por x0 carece de significado: la gráfica de cambios relativos no aparece y se presenta el motivo. Del mismo modo, si el caso base no es motor o W0, η0 no permiten dividir, no se inventan prestaciones.

## Física: temperaturas T2 y T4
T2 es la temperatura de salida del compresor y T4 de la turbina, ambas en K. El barrido ya las incluye a partir de los cuatro estados de 2B. Al aumentar rp suelen cambiar ambas, pero la tendencia concreta depende de las eficiencias, la presión disponible y las restricciones de temperatura. Solo dibujamos los valores correspondientes a ciclos motores. Los puntos no motores siguen en la tabla con diagnósticos.

## PYTHON: firmas y datos
- \`_svg_dos_series(filas, etiqueta_x, unidad_x, claves, etiqueta_y, unidad_y, x_ref=None)\`: recibe filas de diccionarios con x y operativas (dict o None), dos claves con valores numéricos ya convertidos, y etiqueta/unidades. Devuelve una cadena SVG o None si no hay datos admisibles. La función no calcula termodinámica; convierte a coordenadas y crea segmentos con discontinuidades. Las etiquetas se escapan para producir HTML seguro.
- \`svg_variaciones_relativas(estudio)\`: recibe el dict producido por barrido_cp_variable, consulta referencia_x y referencia.ciclo, devuelve (svg, mensaje) y rechaza normalización singular o caso no motor; no tiene unidades dimensionales en los ejes porcentuales.
- \`svg_temperaturas_caracteristicas(estudio)\`: reutiliza filas operativas y las claves T2/T4, devolviendo SVG o None, con eje vertical [K] y x en la unidad del parámetro seleccionado.

Flujo: formulario del dashboard → web_app.index → cp_variable_web.preparar_sensibilidad → barrido_cp_variable → graficas_sensibilidad_cp → lista graficas → macro grafica_cp en templates/index.html → visor de static/dashboard.js.

El nuevo código introduce una función interna emitir() que guarda los segmentos contiguos. Cuando encuentra operativas=None, cierra el segmento y comienza otro: evita conectar dos regiones que no están unidas por muestras motoras. Los círculos almacenan data-x/data-valor para que las pruebas puedan comparar los números reales frente al resultado OFAT.

## Experimento guiado
Ejecuta un barrido de T3 entre 1450 y 1750 K, compara trabajo y rendimiento relativos y relaciona T4 con el trabajo de la turbina. Repite el estudio con delta=0: la normalización horizontal pasa a ser imposible aunque todavía puedan calcularse temperaturas. Comprueba cómo cambia la disponibilidad de las gráficas sin alterar el modelo.

## Pruebas y límites
Las pruebas están en tests/test_graficas_sensibilidad_31.py. La suite vigente se ejecutará en GitHub Actions; la revisión visual final de los SVG ampliados queda para Windows. Este trabajo es verificación de software, no validación experimental de las correlaciones de aire.
