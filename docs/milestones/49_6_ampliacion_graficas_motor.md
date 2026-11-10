# Milestone 49.6 — Gráficas termodinámicas y propulsivas

## Base y alcance

Partida verificada: rama `mejoras/cp-variable`, commit `c731375046aff4a52fe6ac1e56659f22d1c4a297` (49.5). El desarrollo se efectuó en una copia independiente sin commit ni modificación de `main`. Solo se amplían las vistas; no se modifican los solucionadores ni se añaden dependencias.

## Gráficas del banco

| Familia | Representación | Origen y límites |
| --- | --- | --- |
| Ciclo | T–s | `svg_ts_turborreactor`; enlaces esquemáticos entre estados calculados. |
| Ciclo | Temperaturas y presiones totales | `estaciones_turborreactor` + `svg_evolucion`; **cuatro estaciones de remanso**: tras difusor, compresor, cámara y turbina. La salida estática no es un punto de estas curvas. |
| Ciclo | Trabajos específicos | `datos_balance_energetico` + `svg_trabajos_motor`. Compresor, turbina y transmisión por eje en kJ/kg de aire entrante. No se infiere un «trabajo neto» de propulsión de su diferencia. |
| Ciclo | Balance energético | `svg_balance_energetico` preexistente. Entradas de energía, trabajo y energía cinética en base común de aire, **magnitudes no aditivas**. No se presentan como una suma directa de barras. |
| Tobera | Geometría; Mach; presión estática | Visores 49.4 existentes, con perfil axial cuando es geométricamente resoluble y degradación al gráfico disponible. |
| Tobera | Temperatura estática y velocidad local | Nuevas opciones de `svg_perfil_axial`, usando exclusivamente `temperatura`, `velocidad` y `x` del perfil resuelto. Exclusivas de perfiles C-D con geometría axial disponible; para convergente no hay perfil axial ficticio. |
| Prestaciones | Contribuciones de empuje específico y absoluto | `svg_descomposicion_empuje`. El absoluto aparece únicamente si existe caudal y resultado absoluto; los términos conservan el signo del solucionador. |
| Prestaciones | Velocidades de vuelo y salida | `svg_velocidades_extremos`, desde `remanso.velocidad_vuelo` y `tobera.velocidad_salida`; dos valores discretos [m/s], sin trayectoria interna inventada. |
| Estudios | Barridos Mach, T3, mapa y comparación | Se conserva sin cambios el banco paramétrico 49.5, accesible desde el grupo y desde la navegación principal. |

## Coherencia física

- Los estados térmicos totales son discretos: unirlos sirve para orientarse, no equivale a resolver una distribución espacial en los componentes.
- En el perfil axial las dos ramas de choque se renderizan como polilíneas **separadas**: las condiciones inmediatamente anteriores y posteriores conservan la misma coordenada axial, sin interpolación a través del salto.
- La diferencia entre trabajo de turbina y compresor **no** se rotula como potencia útil de un turborreactor. El trabajo de eje contabiliza el rendimiento mecánico existente.
- El modelo de perfil proporciona temperatura estática y velocidad local, pero **no una serie explícita de presión total axial**. No se construye una curva de presión total a partir de presiones estáticas ni se asume una ley de pérdida inventada. Queda pendiente de una futura ampliación explícita del contrato de datos físicos, fuera de este milestone.
- El perfil axial requiere geometría física y perfil C-D resuelto; las gráficas ausentes se ocultan, no se sustituyen por ceros.
- Modos A/B/C comparten solucionadores, API y actualización automática; no hay recálculo al cambiar pestañas.

## Cambios de software

- `perfil_axial_tobera_conica.py`: admite temperatura estática y velocidad local, conservando la separación del choque y los puntos explorables.
- `turborreactor_web.py`: reutiliza las cuatro estaciones existentes e incorpora gráfico de trabajos y SVG axiales al objeto de presentación.
- `templates/turborreactor.html`: añade familias de gráficas exclusivamente al banco interactivo; el clásico retiene sus cuatro pestañas.
- `static/turborreactor_interactivo.js`: sincroniza disponibilidad y familia activa; un solo `fetch` y controlador M48. Se preservan zoom, lectura puntual y exportación 49.4.
- `static/turborreactor.css`: estilos de la selección de familias.

## Verificación y limitaciones

- Windows (2026-11-09): el archivo focalizado ejecutó 4 métodos `unittest`, los 4 correctos; el ZIP refiere 17 pruebas focalizadas, pero el archivo recibido contiene cuatro métodos. La regresión completa pasó 770 pruebas, con 10 omitidas y 0 fallidas. `node --check` pasó y los 8 tests JavaScript existentes fueron correctos.
- Flask test client confirmó `/` (302 al banco), las tres vistas (200), el endpoint individual en A/B/C y el endpoint paramétrico 49.5. JSON se serializó sin NaN/infinito. A/B/C generaron temperatura y velocidad axial, trabajos y velocidades extremas para un caso C-D con geometría; en tobera convergente, las dos series axiales quedan no disponibles.
- Se preservaron API, simulador clásico, Brayton y solucionadores. La inspección visual y las exportaciones desde navegador quedan pendientes de la revisión manual del usuario.

No se ha modificado la física; tampoco se ha implementado el milestone 49.7.

## Mejora localizada posterior: restaurar geometría de referencia en C (10-11-2026)

Se parte del paquete **corregido y verificado en Windows** del 49.6, que incluía el arreglo de visibilidad de `#estudio49`, diagnósticos, pruebas y documentos posteriores al ZIP inicial. Se conservan esas correcciones.

- `acoplamiento_motor_mapa_47.punto_diseno_47()` ejecuta el diseño matemático de calibración con `PARAMETROS_DISENO_47` (Mach 0, T3 1600 K, gasto de aire 20 kg/s, entre otras entradas) y llama a `dimensionar_tobera`. Sus claves `area_garganta_diseno` y `area_salida_diseno` proporcionan ambas **0,04734811643457149 m²** con el modelo vigente. La coincidencia Ae = Ag es consecuencia de que el diseño de calibración usa una tobera **convergente**; no constituye una relación C-D óptima.
- No hay una relación de áreas C-D calibrada por `punto_diseno_47`. Por ello el botón aplica exactamente el par de referencia que devuelve el modelo, sin imponer el 1,5 de algunos casos de prueba ni el valor 0,0710221746 m² como constante universal. El usuario puede modificar inmediatamente Ae para explorar un divergente real.
- Nuevo GET `/api/turborreactor/geometria-diseno`: devuelve `area_garganta_m2`, `area_salida_m2`, origen y tipo de referencia; exclusivamente al pulsar el botón. No se incorpora un segundo sistema de solución y no se alteran los parámetros de calibración.
- El botón solo está disponible en `/turborreactor/interactivo` y únicamente visible con C. Después de recibir y validar la respuesta, actualiza los dos `<input>` existentes. Si el usuario cambia modo o áreas durante la petición, **no** los sustituye. Emite eventos `input` para marcar estudios y resultados desactualizados y pide **una sola** simulación mediante `controlador.cambiar()`.
- La geometría influye en los residuos de masa y en la condición de equilibrio del monoeje. Un fallo de convergencia no es una demostración de imposibilidad física. No se modifican mapas, algoritmos, tolerancias ni parámetros del motor.

La verificación de esta integración en Windows ejecutó las 5 pruebas focalizadas (API, vistas, valores M47, caso Mach 0,838/T3=1704 K y escritura limitada a Ag/Ae), las 21 pruebas de navegación HTTP, estudios 49.5 y gráficas, además de la regresión completa: **779 pruebas, 769 correctas, 10 omitidas, 0 fallidas**. Los 9 tests JavaScript pasaron. Las áreas de referencia convergen en modo C y mantienen Ag = Ae = 0,04734811643457149 m² aun con el selector C-D; esa condición degenerada no se anuncia como óptimo C-D. La inspección visual manual fue aprobada por el usuario el 10-11-2026. El milestone se publica en un único commit de `mejoras/cp-variable`; `main` no se modifica.

## Correcciones de revisión Windows (2026-11-09)

Se excluye `#estudio49` de la regla CSS que oculta las secciones clásicas del
banco, recuperando la vista paramétrica 49.5. El modo C conserva resultados y
fallos numéricos de la base publicada; el adaptador distingue explícitamente
no convergencia de inviabilidad física en su mensaje. El caso Mach 0,838 /
T3=1704 K converge con garganta de diseño, pero falla la búsqueda al aumentarla
un 10 % (también en 49.5). El caso exacto confirmado por el usuario usa Ag=0,5 m²
y Ae=3,5 m²: ambas versiones fallan tras 13 iteraciones con residuo normalizado
8,201032. Ag es 10,5601 veces la garganta de diseño. No se ha demostrado un
defecto que justifique cambiar el solver ni la inexistencia física de solución.
La regresión posterior ejecutó 774 métodos: 764 correctos y 10 omitidos, sin
fallos ni errores. También pasaron las 4 pruebas Python nuevas, las 10
históricas del acoplamiento y los 9 tests JavaScript.
