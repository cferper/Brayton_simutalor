# Milestone 50.2 — Diagnóstico avanzado condicionado por física

## Alcance y base

Rama de desarrollo `mejoras/cp-variable`. Árbol entregado por el usuario correspondiente a **`7036c43abf6861b7d8aad0ff4ebb0675985dd5fe`**, publicación de M50.1. Los archivos comparados con GitHub tienen los mismos blobs al normalizar finales CRLF a LF. La auditoría preliminar del 11-11-2026 se reutiliza; no se interpreta una falta de convergencia como surge. **Sin commit ni push.**

## Auditoría aplicada: magnitudes existentes y estado

| Indicador | A (caudal impuesto) | B (geometría fija) | C (monoeje con mapas) | Fuente |
| --- | --- | --- | --- | --- |
| Caudal de aire ṁa | Prescrito si se introduce | Derivado del flujo de tobera y áreas | Resuelto del acoplamiento | `prestaciones_absolutas.gasto_masico_aire` |
| Tt2, pt2, entrada compresor | Solucionador | Solucionador | Solucionador | `compresor.T1`, `compresor.p1` |
| ṁcorr | Derivable con caudal | Derivable con caudal | Derivable y cotejable con compresor mapa | `flujo_corregido` del M47.3 |
| N, rpm mecánicas | No disponible | No disponible | Calculado | `motor_acoplado.rpm` |
| Ncorr | No disponible | No disponible | Derivable | `giro_corregido` del M47.3 |
| πc, ηc | Estado de ciclo prescrito | Estado de ciclo prescrito | Punto de mapa resuelto | `compresor`, `motor_acoplado.compresor_mapa` |
| Línea de estabilidad real, margen surge | No disponible | No disponible | No disponible | Sin datos independientes validados |

Se usan **propiedades totales** en la entrada del compresor. Referencias constantes M47.3: Tref = 288,15 K, pref = 101,325 kPa. Las convenciones de corrected flow/speed corresponden al módulo original `mapas_turbomaquinaria_47.py` y al escalado educativo de [M47.3](47_3_mapas_turbomaquinaria.md):

\[
\dot m_{\mathrm{corr}}=\dot m_a\sqrt{T_{t2}/T_{\mathrm{ref}}}\,\frac{p_{\mathrm{ref}}}{p_{t2}},\qquad
N_{\mathrm{corr}}=N\sqrt{T_{\mathrm{ref}}/T_{t2}}.
\]

El primero se expresa en **kg/s de referencia** y el segundo en **rpm corregidas**; no son el caudal real ni rpm reales. En A sin gasto de aire, ambos no disponibles; en B solo es posible ṁcorr; en C se muestran los dos. El caudal corregido del modo C debe reproducir el valor de `compresor_mapa.caudal_corregido`, con tolerancia numérica.

## Arquitectura implementada

- `diagnostico_motor_50_2.py`: funciones puras de presentación `diagnosticar_motor_50_2(resultado)` y `svg_mapa_compresor_50_2(diagnostico)`; **no llaman a** `resolver_motor_acoplado` ni a un segundo solucionador físico. Reutilizan las escalas de calibración M47 que el adaptador C ya ha calculado y la tabla HPC para trazar el mapa de presentación; no recalculan el punto de diseño.
- `turborreactor_web.preparar_vista_turborreactor`: incorpora `diagnostico_50_2` y `svg_mapa_compresor_50_2` a la vista.
- `web_app.api_turborreactor_simular`: expone `diagnostico_50_2` en el **POST existente**, además del SVG dentro del objeto `svg` ya existente. No añade otro endpoint ni otro `fetch`.
- `templates/turborreactor.html` y `static/turborreactor.css`: panel del banco interactivo, no del clásico. La ficha incorpora unidades, origen de mapa y limitaciones.
- `static/diagnostico_motor_50_2.js`: consumidor exclusivo de presentación. Recibe una respuesta válida, construye textos y SVG; ante `pendiente` o fallo limpia cifras, diagnóstico y dibujo previos. Marcadores consultables por cursor, foco, Enter o espacio.
- `static/turborreactor_interactivo.js`: integra `actualizado(datos)` / `pendiente()` con el mismo controlador de M48, antes de cualquier nueva simulación.

## Mapa de compresor

Se representa **πc frente a ṁcorr**. Las 13 curvas de giro nativo que contiene el HPC del archivo `data/tmats_47/mapas_normalizados.json` se transforman con los **mismos coeficientes de calibración del diseño M47** que usa `consultar_compresor`. Cada curva enlaza únicamente sus muestras tabuladas por Rline; el trazo entre puntos es interpolación visual de muestras del mapa, no datos de ensayos del motor. Se representa el `Ncorr` correspondiente a cada fila y el punto C calculado por el acoplamiento. El punto real se muestra únicamente con solución C convergida y coordenadas dentro de los ejes `[ncorr_min,ncorr_max]` y `[Rline_min,Rline_max]`.

Una `Rline` de 1 representa un **borde tabulado de mapa** procedente de T-MATS y no una línea experimental de surge del turborreactor educativo. No se muestra distancia a bombeo ni margen porcentual. Los puntos de A/B carecen de equilibrio rpm–Rline y no se proyectan artificialmente al mapa aunque dispongan de caudal corregido. Los datos de T-MATS originales no corresponden a un motor monoeje calibrado experimentalmente: las escalas de gasto, presión, eficiencia y giro fueron elegidas para reproducir el **diseño hipotético** de 20 kg/s y 20 000 rpm.

### Estados y límites

- Valores ausentes: `None` en Python/JSON, «No disponible» en interfaz; nunca cero supuesto.
- Error de entrada, salida 422 o no convergencia: la respuesta carece de nuevas cifras; el controlador ya existente invalida y limpia los elementos del panel sin conservar un punto previo.
- La validez dentro de la **malla tabulada** no establece estabilidad dinámica, margen frente al surge ni seguridad operativa.
- Para una predicción de inestabilidad harían falta límites de funcionamiento verificables, modelo dinámico y compatibilidad con un motor real. No se han añadido.
- No se han alterado solvers, interpolación bilineal, tolerancias, mapas originales, geometría ni la física de la tobera.
- Estudios paramétricos de Mach y T3 ya existentes siguen disponibles; la actualización del diagnóstico usa el mismo recálculo al variar entradas, sin ejecutar barridos adicionales.

## Pruebas y verificación

**Ejecución en el entorno de desarrollo (11-11-2026).** Las 23 pruebas Python focalizadas de
M47.3, M47.4 y M50.2 concluyeron sin fallos: **21 correctas, 2 omitidas**.
Las dos omitidas son pruebas HTTP que requieren Flask. Los 19 tests JavaScript
existentes y nuevos terminaron correctos (19/19); la sintaxis de los archivos
Python/JS modificados pasó. La regresión general Python se lanzó una vez:
**491 pruebas ejecutadas, 24 errores de importación, 4 omitidas**; los errores
corresponden a módulos que importan `web_app` porque **Flask no está instalado**.
No ha sido posible instalar Flask porque el índice de paquetes no es accesible
por red. Por tanto, no se afirma que la regresión general esté superada.
La ejecución en navegador y la comprobación visual responsive quedan pendientes
en Windows. No se han ejecutado pruebas HTTP en esta sesión.

**Integración local en Windows.** El entorno virtual del proyecto tiene Flask.
Pasaron las 8 pruebas focalizadas del 50.2, incluidas las 2 HTTP con el cliente
de pruebas de Flask, y las 19 pruebas JavaScript (3 propias del 50.2). La
regresión ejecutó 807 pruebas: 797 correctas, 10 omitidas y ningún fallo.
Las omisiones corresponden a SciPy (8), Cantera (1) y permisos de enlaces
simbólicos en Windows (1). La revisión visual en navegador queda pendiente.


`tests/test_diagnostico_motor_50_2.py` cubre A con/sin caudal, B, C, ecuaciones y referencias, curvas, dominio y ausencia de valores ficticios; los dos ensayos HTTP se omiten automáticamente si falta Flask. `tests/js/test_diagnostico_motor_50_2.cjs` verifica integración con el controlador y la ausencia de llamadas físicas adicionales en el módulo. Los resultados concretos de esta sesión se registran al entregar el paquete. La inspección visual en Windows y las pruebas HTTP con Flask siguen siendo necesarias cuando este entorno no tenga dependencias instaladas.

## Fuentes

- [NASA T-MATS (código)](https://github.com/nasa/T-MATS)
- [NASA/TM-2014-218410](https://ntrs.nasa.gov/citations/20150002325)
- [NASA Glenn — corrected airflow](https://www.grc.nasa.gov/WWW/K-12/airplane/wcora.html)
- [Origen, licencia y escalado de los datos incorporados](../../data/tmats_47/README.md)
