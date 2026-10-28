# Milestone 44.1 — Descomposición del empuje y diagrama T–s

## Punto de partida y alcance

- Rama prevista: `mejoras/cp-variable`.
- Base publicada verificada en GitHub: `d61ef3795ae58027927adc5077409bb3dfe6b018` (milestone 43).
- El árbol de desarrollo se reconstruyó en una **copia separada**, comparando las huellas Git de los 15 archivos de M43 con los contenidos del commit publicado. El directorio antiguo con cambios pendientes quedó intacto.
- Alcance original de 44.1: dos SVG para la pantalla existente. La entrega acumulada revisada en Windows añade las gráficas de tobera/Mach de [44.2](44_2_mach_presion_tobera.md); no incorpora balances energéticos de 44.3.
- No se han modificado solvers, ecuaciones, tolerancias físicas, CSS ni JavaScript; no se ha hecho commit ni push.

## Gráfica de empuje específico

Se reutilizan **sin recalcular la tobera** los campos de `resultado['prestaciones']`:

\[
F_s = \underbrace{(1+f)V_e}_{\text{momento de salida}} -
\underbrace{V_0}_{\text{momento de entrada}} +
\underbrace{(1+f)\,(p_e-p_\infty) A_e/\dot m_e}_{\text{presión normalizada}}.
\]

La última fórmula describe la normalización ya aplicada en el solucionador mediante el empuje específico de presión de la tobera: **no se ha calculado ninguna área nueva**. Las unidades de los cuatro términos son **N/(kg/s de aire)**, equivalentes dimensionalmente a m/s. El factor de masa `(1+f)` es parte de las contribuciones de salida y presión del solver; no se multiplica otra vez.

`datos_empuje_grafica(resultado)` retorna cuatro magnitudes firmadas en el orden salida, entrada negativa, presión, neto. Devuelve `None` si una contribución no existe. Comprueba que la suma reproduce el neto dentro de `1e-8 × escala`; una incoherencia provoca `ValueError` en vez de un gráfico engañoso. `svg_descomposicion_empuje(resultado)` dibuja cuatro barras con un cero de referencia, signos y valores. Cuando faltan prestaciones, la plantilla muestra una explicación sin barras inventadas.

## Diagrama T–s

`datos_ts_turborreactor(estaciones)` utiliza exactamente los cuatro estados **totales/de remanso** 1–4 ya producidos por `estaciones_turborreactor`: tras difusor, compresor, cámara y turbina. Obtiene su entropía con `propiedades_aire.s(T,p)`, que integra `cp(T)` y corrige presión por `−R ln(p/P_ref)`. Las unidades son K, kPa y kJ/(kg·K). Si la salida de tobera está resuelta, incorpora un punto adicional `E` **estático** a partir de la temperatura y presión estáticas; si no, lo omite.

`svg_ts_turborreactor(estaciones)` representa puntos numéricos y **segmentos discontinuos esquemáticos**, separados por colores para compresión, combustión equivalente, turbina y (si existe) tobera. Las rectas no son curvas de proceso ni perfiles geométricos. La conexión 4→E relaciona remanso con estático y tampoco implica evolución espacial continua. No añade puntos isentrópicos ficticios ni interpreta la entropía del aire equivalente como producción rigurosa de entropía química en la cámara. No se cuantifica aquí la entropía generada por choque u otros procesos; esa física queda en los diagnósticos originales.

## Integración

- `turborreactor_web.py`: cuatro funciones nuevas y dos entradas (`svg_empuje`, `svg_ts`) en `preparar_vista_turborreactor()`.
- `templates/turborreactor.html`: barras en «Resultados y uso» y T–s en «Visualizaciones y transformaciones», manteniendo las seis secciones y las dos pestañas educativas.
- `tests/test_graficas_turborreactor_44_1.py`: suma de fuerzas, cambios de parámetros, datos ausentes, comparación con `s(T,p)`, tipos de estación, SVG válido y propagación de incoherencias.
- `CODE_WALKTHROUGH.md` y documento de aprendizaje: explicación de funciones, contratos y errores comunes.

## Pruebas previas en el entorno de desarrollo — 26 y 27/10/2026

Los resultados y limitaciones de esta sección corresponden al entorno previo, no al Windows configurado que se revisa después.

- `python3 -m unittest tests.test_graficas_turborreactor_44_1 -v`: **7 métodos definidos** en el archivo final (incluida la comprobación de integración estática de plantilla), 0 fallos, 0 errores, 0 omisiones al reejecutarlos el **27/10/2026**. La cifra de 6 métodos corresponde a una ejecución anterior, antes de añadir el séptimo; no representa el contenido definitivo de la entrega.
- Última batería de regresión científica: `python3 -m unittest -q tests.test_graficas_turborreactor_44_1 tests.test_combustible_cp_variable_37 tests.test_mapas_prestaciones_turborreactor_38 tests.test_verificacion_independiente_turborreactor_39 tests.test_tobera_convergente_divergente_42a tests.test_choque_normal_42c tests.test_propiedades_aire`: **96 pruebas descubiertas, 95 correctas, 0 fallos, 0 errores, 1 omitida**. La omisión justificada es `test_propiedades_cantera_opcional` (milestone 39): Cantera no está instalada y es una comparación externa opcional no incluida en `requirements.txt`.
- `python3 -m compileall -q turborreactor_web.py tests/test_graficas_turborreactor_44_1.py`: correcto.
- `node --check static/turborreactor.js`: correcto (archivo no modificado).
- Los dos SVG del caso base se exportaron para inspección de los dibujos (no equivale a una revisión de la interfaz web). Se ajustó la presentación de entrada nula para evitar el rótulo `−0.00`.
- Casos numéricos de las pruebas: estacionario, Mach 0.7 y tobera C-D. En el ejemplo estacionario: salida ≈681.304221, entrada 0, presión ≈276.953463, neto ≈958.257683 N/(kg/s de aire).
- El entorno de esta copia **no dispone de Flask ni Jinja2**. No se han instalado dependencias por restricción expresa; por ello aún no se han ejecutado la integración Flask/Jinja ni la regresión completa. **Esta entrega no puede declararse aprobada integralmente en web hasta repetirlas en el entorno Windows configurado.**
- La inspección visual de ambas nuevas gráficas en navegador real queda pendiente de la revisión solicitada por el usuario.

Las pruebas constatan coherencia interna del software; no son una validación del modelo con datos experimentales.


## Integración y revisión en Windows — 27/10/2026

Base local comprobada: rama `mejoras/cp-variable`, HEAD
`d61ef3795ae58027927adc5077409bb3dfe6b018`
(`feat: add milestone 43 educational turbojet interface`). Los archivos
versionados estaban limpios. Se conservaron los dos no versionados ajenos:
`docs/PLAN_MEJORAS_BRAYTON_SIMULATOR.md` y el archivo de nombre iniciado por
`tone 43 educational turbojet interface`, comprobando sus SHA-256.

ZIP acumulado verificado por CRC y lista exacta de nueve rutas seguras,
extraído fuera del repositorio y comparado antes de copiar. Los seis destinos
nuevos no existían. Se incorporan los nueve archivos; adicionalmente se
corrige la expectativa de accesibilidad de `tests/test_turborreactor_web_40.py`
de tres a siete regiones SVG, manteniendo foco, nombres y desplazamiento.

**PYTHON / PRESENTACIÓN.** La revisión real detectó solapamiento de rótulos
4/E y una conexión sobre texto en T–s con choque. `svg_ts_turborreactor(estaciones)`
conserva su firma y datos; sitúa E debajo (`y + 20`), añade contorno blanco
al texto SVG y eleva a 420 px su altura máxima. Son coordenadas de dibujo,
no cambios de T, s ni del solucionador. Los contratos, ejemplos y llamadas
se explican en [manual §4.81](../../CODE_WALKTHROUGH.md#481--milestone-441-dos-gráficos-educativos-del-turborreactor).

**RESULTADOS.** Python 3.13.0 de `.venv`, Windows 11 (10.0.26300):
16/16 pruebas específicas, 74/74 web; regresión vigente de 625 pruebas,
615 correctas, 0 fallos, 0 errores, 10 omisiones justificadas. Tras el ajuste
visual se repiten las 90 específicas/web: 90 correctas, sin omisiones.
Los comandos completos, intentos iniciales y motivos de omisión se registran
en [la revisión Windows de 44.2](44_2_mach_presion_tobera.md#integración-y-revisión-en-windows--27102026).
No se suman ejecuciones repetidas como pruebas distintas.

Se revisan en navegador los cinco casos de la tabla de 44.2 y tamaños grande
y estrecho. Las barras reproducen el neto; T–s distingue cuatro estados de
remanso y E estático opcional. Se comprueba actualización al volver a simular,
retirada de datos ausentes y desplazamiento horizontal por teclado. No se
modifican CSS/JS, ecuaciones, tolerancias ni algoritmos físicos. Sin instalaciones,
commit, staging, push ni cambio de rama. M44.1/M44.2 permanecen pendientes de
commit y aprobación del usuario. Es verificación interna, no validación experimental.
