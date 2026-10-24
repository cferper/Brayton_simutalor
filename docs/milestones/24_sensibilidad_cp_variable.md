# Milestone 24 — Sensibilidad paramétrica con cp(T) (Fase 2E)

## Objetivo y base

Base remota comprobada: `5c83ff52ab0b84be8e35e9b41482649b5aa6b7e9`, rama `mejoras/cp-variable` del repositorio `cferper/Brayton_simutalor`. La aplicación ya utiliza `templates/index.html` como único dashboard de cálculo cp(T), con Simulación, Resultados y Optimización activos. Sensibilidad estaba desactivada por depender del anterior gas perfecto.

Este hito adapta **solo** la sección Sensibilidad; Mapa de diseño y Segunda ley continúan pendientes. No se modifican `propiedades_aire.py`, `ciclo_cp_variable.py`, `optimizacion_cp_variable.py`, la documentación histórica ni el repositorio de conservación.

## Arquitectura implementada

1. `sensibilidad_cp_variable.py`: módulo científico OFAT separado de Flask y SVG. Recibe exactamente siete entradas y un factor de entre T1, T3, rp, p1, eta_c, eta_t y delta; cada muestra es un `resolver_ciclo` nuevo de 2B con las otras seis entradas fijas. Los límites del barrido son finitos, editables, estrictamente crecientes; la cantidad es un entero entre 3 y 201. La malla lineal incluye ambos extremos.
2. Cada registro declara explícitamente uno de cinco estados: `motor`, `no_motor` (calculable pero no operativo), `fuera_rango` (algún estado requiere salir de 200–2000 K), `entrada_invalida` (entrada fuera del dominio o mal formada) y `error_numerico` (no representable/convergencia). Los `motivos` se conservan. Trabajo de compresor, turbina y neto; calor aportado; rendimiento; T2/T4; y residuo de primera ley quedan disponibles para inspección en `magnitudes` **solo si existe ciclo calculado**. `operativas` se rellena únicamente para puntos motores; ninguna gráfica emplea las otras filas.
3. `sensibilidad_local(entradas,parametro,paso_relativo=1e-3)`: estima elasticidad local adimensional \(S_x^Y=(x/Y)\,dY/dx\) para \(Y=w_\mathrm{neto}\) y \(Y=\eta\). Utiliza central cuando ambos vecinos son motores o lateral cuando sólo lo es uno. Compara `h` con `h/2` y rechaza estimaciones inestables, normalización singular y base no motor; no añade una fórmula física paralela.
4. `cp_variable_web.py`: presentador con tres SVG separados (trabajo neto, rendimiento, trabajos de equipos). Respeta los huecos por filas inválidas o no motoras y marca con línea vertical el valor de referencia cuando cae en el intervalo. Las escalas verticales son independientes y cada eje indica sus unidades.
5. `web_app.py`, `dashboard.py` y la única plantilla `templates/index.html`: nuevo POST `/`, `accion=sensibilidad`, y configuración OFAT dentro de la sección original; se reutiliza la caja de los siete parámetros en Simulación. El JavaScript actualiza únicamente valores sugeridos de límites al elegir factor; no resuelve ciclos ni introduce selector de modelo. Errores retornan HTTP 400, se conservan los valores introducidos y queda seleccionada Sensibilidad.

## Resultados físicos del caso base

`T1=288.15 K, T3=1600 K, rp=10, p1=100 kPa, ηc=0.85, ηt=0.90, δ=0.05`:

- Fase 2B: \(w_\mathrm{neto}\approx402.070798\) kJ/kg y \(\eta\approx34.893428\%\).
- OFAT T3 en 1200–1750 K, 41 muestras: **41 motoras**. Cerca del base, \(S_{T3}^{w}\approx1.848248\) y \(S_{T3}^{\eta}\approx0.154523\), usando derivada central y comparación con paso mitad.
- OFAT p1 en 80–120 kPa: nueve muestras motoras con trabajo neto y rendimiento invariantes en precisión numérica; las entropías absolutas y presiones sí cambian. Elasticidades locales ≈0 en este modelo.
- Al variar rp desde 10, el trabajo crece inicialmente y después disminuye más allá de su máximo interior; el rendimiento maximiza en otra rp. Como comparación externa **del mismo solucionador** (Fase 2C), A está en rp≈15.878 y B en rp≈46.819. El estudio OFAT no redefine esos óptimos ni los infiere a partir de vértices de una malla.

Las cifras son comprobaciones del software contra su solucionador y reglas termodinámicas, **no validación experimental**. Las elasticidades describen perturbaciones pequeñas alrededor de una referencia, no leyes universales ni predicciones de un motor real.

## Verificación acotada

- Nuevo `tests/test_sensibilidad_cp_variable.py`: 10 pruebas: referencia de 2B, conservación de entradas, malla, comparación punto a punto con 2B, balance de energía, cinco estados y exclusiones, dominio 200–2000 K, errores de configuración, invariancia en p1, derivadas/convergencia, paso unilateral y tendencias de rp.
- Nuevo `tests/test_sensibilidad_cp_web.py`: 6 pruebas: integración en la única página, GET sin cálculo, POST y SVG, ausencia de llamadas a optimización en OFAT, estados no motores y fuera de rango, errores 400 sin trazas.
- Actualizado `tests/test_cp_variable_web.py`: sus diez tests reconocen tres inputs numéricos OFAT adicionales y que solo quedan dos paneles temporalmente inactivos.
- Workflow `.github/workflows/verificacion_web_cp_variable.yml`: ejecuta las pruebas nuevas junto con los 32 tests focalizados de dashboard/Flask ya existentes (total previsto **48**). Se prepara rama temporal `validacion/fase-2e-cp` antes de publicar en desarrollo.

**Estado de las ejecuciones:** los resultados locales y definitivos del workflow deben consultarse en el informe de publicación; esta documentación describe la batería, no inventa resultados de GitHub Actions.

## Límites y pendientes

No se han incorporado interacciones multifactoriales, intervalos de confianza, muestreo adaptativo, recálculo de A/B por cada punto, mapa de diseño, exergía, generación de nuevos informes HTML ni validación con datos de banco. Una derivada estable no prueba que el modelo físico sea realista. Los regímenes no motores se muestran como diagnóstico y dejan huecos en las curvas. Las pruebas HTML no equivalen a verificar visualmente todos los navegadores.

## Publicación

Autorizada una sola incorporación en `mejoras/cp-variable` con mensaje `feat: add variable-cp parametric sensitivity analysis`, después de GitHub Actions en la rama temporal; sin merges ni rebases. No se toca `main` ni `Brayton_simutalor-gas_perfecto`.
