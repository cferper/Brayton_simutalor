# Milestone 47.5 — Verificación focalizada y cierre de la fase de caudal

## Resumen acumulado (47.1–47.5)

| Entrega | Componente | Alcance y conservación de compatibilidad |
| --- | --- | --- |
| 47.1 | `caudal_tobera_geometria_fija.py` | Se prescribe el área y el remanso de la tobera; se calcula el gasto de gas bloqueado y no bloqueado, se separan aire y combustible. Se conserva el dimensionamiento a caudal impuesto. La prueba web C-D requiere ahora solución real disponible; el texto de empuje distingue gasto conocido y desconocido. |
| 47.2 | `admision_caudal_cp.py` | Captación exterior en vuelo y sección interna local de compresor. En estático no se inventa velocidad de aspiración. La recuperación de presión total se toma del difusor existente. |
| 47.3 | `mapas_turbomaquinaria_47.py`, `data/tmats_47/` | Mapas públicos HPC/HPT T-MATS con atribución, interpolación sin extrapolación, transformación de velocidad y gasto corregidos y escalado alrededor de diseño monoeje explícito. |
| 47.4 | `acoplamiento_motor_mapa_47.py` | Tres incógnitas y tres cierres independientes para eje, mapa de turbina y garganta; Newton amortiguado, diagnóstico de no solución, modalidad C web. A y B no cambian de significado. |
| 47.5 | Pruebas y documentación | Revisión de residuos, reproducibilidad, límites de mapas, modos previos y compatibilidad con tobera. |

## Ecuaciones físicas verificadas

En admisión `ṁ=ρVA` solo cuando se conoce una velocidad **local o exterior apropiada**. En cámara `f=(h3−h2)/(ηb·PCI−h3)` en la convención energética existente, y `ṁg=ṁa(1+f)`. En el eje, la turbina suministra el trabajo compresor corregido por `ηm`. Para garganta: `ṁg=Gg Ag` (estado sónico si se bloquea; subsónico compatible con contrapresión si no). Los mapas utilizan `ṁcorr=ṁ√(Tt/Tref)/(pt/pref)` y `Ncorr=N/√(Tt/Tref)` con distintas temperaturas de entrada para compresor y turbina. El punto de diseño está especificado y su reproducción comprobada en [47.3](47_3_mapas_turbomaquinaria.md) y [47.4](47_4_acoplamiento_motor.md).

## Pruebas ejecutadas en la copia de desarrollo

- `python -m unittest tests.test_caudal_geometria_fija_47_1 tests.test_admision_caudal_47_2 tests.test_mapas_turbomaquinaria_47_3 tests.test_acoplamiento_motor_47_4 tests.test_gasto_masico_dimensionamiento_45 tests.test_perfiles_tobera_44_4 tests.test_tobera_convergente_divergente_42a`: **86 métodos correctos**, ninguno fallido ni omitido; incluye regresiones de geometría, bloqueo, choques y modelos anteriores.
- `python -m compileall -q` en los módulos modificados o nuevos y pruebas: **sin errores de sintaxis**. `node --check static/turborreactor.js`: **correcto**.
- Reextracción de las tablas NASA (`13×11` compresor, `6×20` turbina) y comparación binaria del JSON generado: **idéntico**, fuentes atribuidas con SHA-256.
- Se intentó ejecutar una prueba web histórica dependiente de `web_app.py`, pero el intérprete disponible carece de Flask (`ModuleNotFoundError`). Esta **limitación de entorno** no demuestra fallo de aplicación; la prueba deberá repetirse en el `.venv` de Windows. No se instalaron dependencias. La interfaz se verificó en la capa de simulación y de generación de SVG; no se ha realizado inspección visual del navegador en este entorno.

Tolerancia de acoplamiento: norma euclídea de los tres residuos adimensionales ≤ `2·10⁻⁷`; se verifican nuevamente diferencias de masa con ese mismo factor sobre el gasto de diseño y balance de potencia relativo ≤ `10⁻⁴`. No se acepta salida del algoritmo por agotamiento como éxito. Las tolerancias de la continuidad de admisión (`2·10⁻⁶` relativo) dejan margen a bisecciones numéricas `cp(T)` sin encubrir diferencias de diseño; una entrada geométrica incompatible en modo C produce error.

## Ejemplos reproducibles y límites

El punto estático educativo T∞=288,15 K, p∞=100 kPa, Tt3=1600 K, garganta de 0,047348116435 m² y mapas calibrados produce 20 kg/s aire, ≈20,560564 kg/s gas, 20 000 rpm, PRc=10 y ≈19,165 kN de empuje absoluto. En Mach 0,4 el punto se desplaza a ≈21,29 kg/s y ≈20 139 rpm, con cierre numérico. Un área un 10 % mayor que el diseño queda fuera de los límites de este mapa escalado y retorna **sin solución disponible**. Son ejemplos del modelo hipotético, no de un motor físico ensayado.

Las características cuasiunidimensionales `cp(T)` disponibles incluyen choques normales modelados por el solucionador de tobera existente. No se han añadido mapas genéricos de surge real, pérdidas tridimensionales, separación, resistencia externa, curvas de emisiones o transitorios de arranque. No se extrapolan los mapas fuera de su dominio ni se garantiza que cualquier combinación de áreas y Tt3 disponga de solución. Los mapas no contienen datos experimentales validados del turborreactor construido por este proyecto.

## Pendiente al integrar el ZIP acumulado en Windows

1. Confirmar base Git publicada y que la copia local no contiene modificaciones conflictivas, preservando `docs/PLAN_MEJORAS_BRAYTON_SIMULATOR.md`.
2. Ejecutar las pruebas históricas completas con `.venv\\Scripts\\python.exe` y Flask/Jinja2 disponibles, sin instalar nuevas dependencias salvo instrucción del usuario.
3. Inspeccionar en navegador los tres selectores A/B/C, los campos específicos, resultados y gráficas anteriores; probar bloqueada, subsónica y C-D, incluyendo diagnósticos sin solución.
4. Revisar científicamente los mapas escalados y cualquier decisión futura antes de atribuir prestaciones a un motor real.

**Estado:** entrega preparada sin commit ni push, sobre `mejoras/cp-variable` en HEAD `208a6ce92b982f0db35078053e60d5be9bb7b2ba`; no se modifican `main` ni los solucionadores termodinámicos históricos. No comienza milestone 48.
