# Milestone 25 — Mapa de diseño rp–T3 con aire cp(T) (Fase 2F)

## Estado anterior

Base comprobada: `cee7753eab68eafcb1616a3edd63e9a111248dcd`, rama `mejoras/cp-variable` del repositorio `cferper/Brayton_simutalor`. El dashboard único `templates/index.html` ya tenía Simulación, Resultados, Optimización A/B y Sensibilidad OFAT conectados al modelo cp(T). «Mapa de diseño» continuaba desactivado porque el módulo anterior pertenecía al gas de propiedades caloríficas constantes. Las 48 pruebas focalizadas de la Fase 2E constaban como superadas en GitHub Actions.

## Qué se ha añadido

- `mapa_diseno_cp_variable.py` genera mallas 2D de `rp` (horizontal, muestreo logarítmico) y `T3` [K] (vertical, muestreo lineal) llamando para **cada par** a `ciclo_cp_variable.resolver_ciclo`; los otros cinco parámetros físicos, `T1`, `p1`, `eta_c`, `eta_t` y `delta`, permanecen fijos. Los valores de entrada vienen de Simulación y no se modifican.
- Predeterminados: rp 1,1–80; T3 1200–1800 K; 31 × 31 = 961 celdas. Límite de aplicación de 5–51 puntos por eje (máximo 2601) y límites numéricos finitos ordenados, con rp>0 y ≤1000 y T3>0 y ≤3000 K como restricciones de la ventana solicitada. No son límites universales de Brayton: la **representabilidad termodinámica real** sigue siendo 200–2000 K para todos los estados, controlada por 2B.
- Cada celda devuelve coordenadas, clasificación, diagnóstico, datos calculables (wc, wt, wnet, qin, qout [kJ/kg], T1–T4 [K], rendimiento y residuo de primera ley), y prestaciones operativas **solo para motor**. La matriz `filas[j][i]` orienta las filas por T3 y columnas por rp. Los nodos inválidos se conservan sin sustituirlos por ceros.
- Estados separados: `motor`, `no_motor`, `fuera_rango`, `entrada_invalida`, `error_numerico`. Las razones originales se preservan. No se confunde falta de representación térmica, entradas fuera de dominio o fallo de solución con inviabilidad motora.
- `cp_variable_web.py` prepara dos SVG independientes dentro del dashboard: trabajo neto [kJ/kg] y rendimiento [%]. Cada **rectángulo representa una evaluación real**, sin interpolar a través de estados excluidos; los no motores, fuera de rango, entradas inadmisibles y fallos numéricos reciben colores no prestacionales. Barras de color, ejes físicos, leyendas, rótulos y `<title>` por celda consultable al pasar el cursor.
- Se muestran los mejores **puntos muestreados** entre motores para ambos criterios. Para T3 de referencia dentro de la ventana, cuando procede, se calcula **una sola** optimización A/B con la Fase 2C y se identifica su condición. Solo se marcan A/B en la gráfica cuando son máximos interiores y están dentro de la ventana; un supremo de frontera abierta no se identifica como punto alcanzado. No se calculan curvas de óptimos por fila.
- `web_app.py`, `dashboard.py` y `templates/index.html` integran `accion=mapa` en la ruta Flask principal `/` sin nuevas rutas, HTML o servidores. Se reutilizan las siete entradas físicas. Seis controles de ventana y resolución dan errores HTTP 400 con los valores conservados. Ninguna malla se calcula en GET, ni al cambiar de pestaña.
- Un ajuste acotado a `static/style.css` mejora la legibilidad de ambos mapas sin cambiar el estilo general. Sensibilidad y las demás secciones conservan su funcionamiento. Segunda ley sigue desactivada; los informes históricos permanecen de solo lectura y correctamente rotulados como gas perfecto.

## Nuevos conceptos de ingeniería

OFAT modifica un parámetro; una malla rp–T3 permite ver **interacción de dos factores** a las mismas condiciones fijas. En cada punto, `resolver_ciclo` impone las mismas relaciones isentrópicas, entalpías cp(T), balance de primera ley y restricciones motoras que en 2B. Si no hay ciclo motor, el rendimiento no es una prestación definida: un color gris no significa 0 %. T3 mayor suele proporcionar más salto de entalpía de turbina bajo condiciones comparables; aumentar rp consume más trabajo de compresor y no maximiza indefinidamente trabajo neto. Los objetivos trabajo y rendimiento pueden favorecer rp diferentes. Ni la malla ni las tendencias extrapolan a componentes de motor reales.

## Nuevos conceptos de Python

Matriz de listas `filas[j][i]`, comprensiones anidadas, copias de diccionario `{**entradas, 'rp':rp, 'T3':T3}`, `Counter` para diagnósticos, filtro de prestaciones válidas, función `max(...,key=...)` solo sobre puntos motores y retorno `None` para dominio sin motores. Gráficos SVG con rectángulos y `<title>` sin dependencias nuevas. Argumentos opcionales en el renderizador Flask para compartir la plantilla con archivos históricos sin alterarlos. Cotas de muestreo que evitan excesos de CPU y HTML.

## Resultados reproducibles

Caso base completo: T1=288,15 K, T3=1600 K, rp=10, p1=100 kPa, ηc=0,85, ηt=0,90 y δ=0,05.

- Referencia 2B en rp=10/T3=1600: trabajo neto ≈ **402,071 kJ/kg** y η≈**34,893 %**.
- Mapa predeterminado 31×31 (rp 1,1–80; T3 1200–1800 K): **959 celdas motoras, 2 calculables no motoras**. Mejor trabajo muestreado ≈ **524,635 kJ/kg**; mejor rendimiento muestreado ≈ **47,004 %**. Estos máximos dependen de la ventana de T3 y **no** son los máximos continuos de 2C a 1600 K.
- Solo como referencia independiente a T3=1600 K: máximo trabajo de 2C en rp≈**15,877934** y máximo rendimiento de 2C en rp≈**46,819105**. Las posiciones se muestran sobre el mapa cuando quedan dentro de la ventana; no son resultados de otras filas T3.

## Verificaciones realizadas

- `tests/test_mapa_diseno_cp_variable.py`: **10 pruebas** de malla/orientación, concordancia directa con 2B, caso base, restricciones físicas, motores y no motores, mascarado de inválidos, error numérico, dominio sin motores, mejor muestra frente a optimización y límites de cálculo.
- `tests/test_mapa_cp_web.py`: **6 pruebas** de GET sin cálculo, POST de ambos SVG, navegación, unidades, tooltips, errores HTTP 400, no contaminación de otras secciones, ausencia de motores y referencia A/B.
- Se actualizan expectativas de presentación en las **48 pruebas existentes** de dashboard, Flask y OFAT. Total de verificación focalizada: **64 pruebas** (48 regresiones y 16 nuevas).
- El workflow existente `.github/workflows/verificacion_web_cp_variable.yml` se amplía para ejecutar las pruebas de esta fase y habilitar una rama temporal `validacion/fase-2f-cp`, antes del fast-forward de desarrollo.

**Resultado de GitHub Actions y enlace:** se consignan en el informe final después de comprobar la ejecución de exactamente el mismo árbol que se publique; no se inventan datos de CI.

## Qué hemos aprendido

La *exploración* de una malla identifica regiones y ejemplos, no demuestra óptimos globales ni sustituye la búsqueda matemática continua. La viabilidad es una **máscara lógica**, no un cero físico. Separar solucionador, muestreo, presentador y Flask permite conservar el contrato científico sin mezclar el modelo histórico con cp(T).

## Limitaciones que siguen existiendo

No hay mapas de equipos reales, modelo de combustión, caudal másico ni empuje. No se calculan contornos continuos de fronteras ni curvas A/B por cada T3; los bordes visuales de las celdas son discretos. Los tooltips SVG dependen del soporte del navegador (especialmente en pantallas táctiles). No se incluyen dependencias nuevas, validación experimental, Fase 2G ni exportación de nuevos informes cp(T). Inspección visual completa pendiente si no se dispone de navegador accesible.

## Commit asociado

Pendiente hasta verificar GitHub Actions y publicar un único commit autorizado en `mejoras/cp-variable`, mensaje previsto `feat: add variable-cp Brayton design maps`. `main`, el repositorio de conservación y el equipo Windows no se modifican.
