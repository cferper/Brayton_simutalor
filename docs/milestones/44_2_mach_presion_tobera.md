# Milestone 44.2 — Mach y presión estática en la tobera

## Estado anterior

Base remota verificada: `d61ef3795ae58027927adc5077409bb3dfe6b018`, rama `mejoras/cp-variable` (M43). La entrega 44.1 aún no publicada se recuperó desde su ZIP íntegro conservado: descomposición del empuje, T–s, tests y documentación. La implementación 44.2 se añade a esos cambios acumulados. No se ha hecho commit ni push.

## Qué se ha añadido

Dos SVG coordinados en «Visualizaciones y transformaciones»: **Mach** y **presión estática [kPa]** con los mismos nombres y orden de estados. Se ofrecen referencias horizontales M=1 y p∞. No se introduce JavaScript, biblioteca ni nueva ecuación de flujo.

La abscisa es **la secuencia discreta de estados** de cada solución, sin unidad y **sin escala espacial**. No es longitud de tobera, distancia del choque ni A/A*: esa relación solo se proporciona para choque C-D, no como trayectoria continua universal. Los estados se dibujan como puntos sin líneas que simulen un perfil intermedio.

## Datos físicos utilizados

- **Convergente:** el solucionador da Mach y presión estática **solo en salida**. Si el régimen es `bloqueado`, el plano de salida coincide con la garganta; si no, no se inventa una garganta adicional.
- **C-D:** utiliza `mach_garganta`, `presion_garganta`, `mach_salida`, `presion_salida` y `regimen`. En presencia de `choque_normal`, añade dos puntos separados tomados directamente de `choque_normal['M1','p1','M2','p2']`.
- **Presión ambiente:** `resultado['ambiente']['presion']`, referencia externa en kPa.
- **Estado de remanso:** `temperatura_remanso` y `presion_remanso` de la entrada de la tobera son condiciones **totales**, no valores de la serie de presión **estática**. No se mezclan en esa gráfica.
- **Salidas no resueltas:** si falta Mach o presión de salida, se devuelve `None` y la interfaz explica que no hay gráfica posible; no se dibujan ceros.

## Regímenes y su interpretación

| Régimen | Lectura |
|---|---|
| Convergente bloqueada | M≈1 en salida/garganta; puede mantener pe distinta de p∞ |
| C-D subsónica no bloqueada | M inferior a 1 en garganta y salida |
| C-D supersónica ideal | M≈1 garganta y M superior a 1 en salida; sin perfil longitudinal calculado |
| Choque normal interno | M1 mayor que 1 y M2 menor que 1; presión estática aumenta bruscamente p2>p1; presión total disminuye |
| Choque normal en salida | Se muestran ambos lados del choque y salida; puntos coincidentes físicamente pueden tener nombres distintos |
| Salida no resuelta / sin expansión | Información de diagnóstico, sin barras o puntos ficticios |

Una presión de salida superior a p∞ implica subexpansión; inferior, sobreexpansión, según la rama resuelta. La solución supersónica «ideal sobreexpandida» **no** predice choques oblicuos exteriores, separación viscosa ni rendimiento fuera de diseño.

## Implementación Python y web

- `datos_tobera_graficas(resultado)` toma el dict científico y retorna `{'estados': tuple[dict], 'ambiente': float, 'regimen': str, 'tipo': str}` o `None`. Cada estado tiene `nombre`, `mach` [-], `presion` [kPa] y `papel`. Rechaza datos no finitos, presiones no positivas y Mach negativo con `ValueError`. No interpola ni resuelve nada.
- `svg_estados_tobera(datos, magnitud)` produce un SVG (o `None`) si `magnitud` vale `'mach'` o `'presion'`; una magnitud desconocida provoca `ValueError`. Las abscisas son categorías compartidas y las ordenadas están normalizadas solo para presentación.
- `preparar_vista_turborreactor` añade `datos_tobera_graficas`, `svg_mach_tobera` y `svg_presion_tobera` a la vista existente, conservando `svg_empuje` y `svg_ts` de 44.1.
- `templates/turborreactor.html` inserta un bloque educativo y ambos SVG en la sección de gráficas, sin tocar sus seis apartados, pestañas ni formularios.
- `tests/test_graficas_tobera_44_2.py` cubre casos físicos, saltos de choque, integridad SVG, actualización y preservación de 44.1.

## Verificación previa en el entorno de desarrollo — 27/10/2026

Esta sección conserva los antecedentes de desarrollo; las comprobaciones locales actuales se distinguen en la revisión Windows posterior.

- `python3 -m unittest -v tests.test_graficas_tobera_44_2 tests.test_graficas_turborreactor_44_1`: **16 pruebas correctas, ninguna fallida/omitida** (9 de 44.2 y 7 de 44.1).
- Regresión científica relacionada: `python3 -m unittest -q tests.test_graficas_tobera_44_2 tests.test_graficas_turborreactor_44_1 tests.test_combustible_cp_variable_37 tests.test_mapas_prestaciones_turborreactor_38 tests.test_verificacion_independiente_turborreactor_39 tests.test_tobera_convergente_divergente_42a tests.test_choque_normal_42c tests.test_propiedades_aire tests.test_tobera_cp_variable_35`: **115 métodos, 114 correctos, 0 fallos, 0 errores, 1 omitido**. Omisión preexistente `test_propiedades_cantera_opcional`: no se incluye Cantera opcional en dependencias.
- `python3 -m compileall -q turborreactor_web.py tests/test_graficas_tobera_44_2.py tests/test_graficas_turborreactor_44_1.py` y `node --check static/turborreactor.js`: correctos.
- Se exportaron los SVG del caso con choque normal interno para revisar su legibilidad; se ajustó la posición del rótulo de referencia de presión ambiente para evitar solaparlo con el estado de salida. No se ha inspeccionado una página Flask en navegador.
- Caso directo de tobera C-D con Tt=1200 K, pt=500 kPa, p∞=350 kPa, Ae/Ag=1,5: `choque_normal_interno`, M1≈1,702, M2≈0,634, p1≈102,0 kPa, p2≈327,1 kPa. Los gráficos usan literalmente las cuatro variables del solucionador.
- En este entorno siguen **sin estar instalados Flask ni Jinja2**; el usuario pidió no instalar dependencias. Por tanto, las pruebas web, compilación Jinja y regresión íntegra del repositorio siguen **pendientes**. No se presenta la ejecución científica parcial como regresión total.

La coherencia de las gráficas con las salidas del solucionador es **verificación de software**, no validación experimental del motor. Tampoco justifica una geometría longitudinal ni una trayectoria continua entre los puntos.

## Integración y revisión en Windows — 27/10/2026

**Estado inicial y entrega.** Rama `mejoras/cp-variable`, HEAD
`d61ef3795ae58027927adc5077409bb3dfe6b018`, mensaje
`feat: add milestone 43 educational turbojet interface`; sin modificaciones
versionadas y dos archivos personales no versionados. El ZIP acumulado contiene
exactamente los nueve archivos indicados por el usuario; CRC correcto, sin
rutas absolutas, `..`, enlaces simbólicos ni destinos nuevos ya existentes.
Se extrae en una carpeta temporal autorizada fuera del repositorio, se comparan
los tres archivos existentes y se verifica byte a byte la copia de los nueve.

**Entorno real.** Python **3.13.0**, Windows **11 / 10.0.26300**, intérprete
`.venv\Scripts\python.exe`. Flask/Jinja2 ya están instalados; no se añade
ninguna dependencia. Las rutas temporales predeterminadas de la sandbox
rechazaban escritura/limpieza. Solo para los procesos de prueba se fijan
`TMPDIR`, `TEMP` y `TMP` a una carpeta autorizada externa al repositorio.
Se verifica creación, escritura y limpieza antes de repetir. No se cambian
variables persistentes de Windows ni código para eludir errores.

| Comprobación | Ejecutadas | Correctas | Fallos | Errores | Omisiones |
|---|---:|---:|---:|---:|---:|
| Específicas 44.1 + 44.2 | 16 | 16 | 0 | 0 | 0 |
| Regresión vigente final | 625 | 615 | 0 | 0 | 10 |
| Web M40 + M41 + M42.B + M43 | 74 | 74 | 0 | 0 | 0 |
| Repetición específica + web tras ajuste visual T–s | 90 | 90 | 0 | 0 | 0 |

Comandos ejecutados desde la raíz (se muestran los definitivos):

```powershell
.\.venv\Scripts\python.exe -B -m unittest -q tests.test_graficas_turborreactor_44_1 tests.test_graficas_tobera_44_2
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m unittest -q tests.test_turborreactor_web_40 tests.test_prestaciones_turborreactor_web_41 tests.test_turborreactor_web_42b tests.test_turborreactor_web_43
.\.venv\Scripts\python.exe -B -m unittest -q tests.test_graficas_turborreactor_44_1 tests.test_graficas_tobera_44_2 tests.test_turborreactor_web_40 tests.test_prestaciones_turborreactor_web_41 tests.test_turborreactor_web_42b tests.test_turborreactor_web_43
```

La regresión se repite con `-v` y salida a un log temporal para identificar
omisiones sin imprimir cientos de resultados: **ocho métodos** requieren
SciPy opcional, **uno** Cantera opcional y **un subcaso** requiere crear un
enlace simbólico (Windows no concede ese privilegio). Las otras verificaciones
del método parcialmente omitido sí se conservan. El perfil vigente importa
una selección explícita de pruebas históricas mediante su cargador existente;
no se ejecuta indiscriminadamente `legacy_tests`.

**Intentos iniciales, no aprobados.** El comando solicitado con
`discover -s tests -q` informó 581 pruebas, 1 fallo, 46 errores y 9 omisiones:
los errores de temporales impidieron completar clases y por eso el recuento
es inferior al definitivo. La primera batería web informó 74 pruebas,
1 fallo y 1 error. El fallo común era la expectativa antigua de **tres**
regiones SVG en M40; se corrige a **siete**, manteniendo sus controles de
accesibilidad. El error web era de limpieza de temporales. No se atribuyen
estos intentos a un fallo termodinámico ni se ocultan como pruebas aprobadas.

**Casos físicos e integración HTTP.** Se comprueban cinco POST con HTTP 200,
comparación exacta de los cuatro SVG contra el presentador, XML válido y
coherencia con el solucionador. Son comprobaciones adicionales de escenarios,
no cinco métodos añadidos a `unittest`. Se revisan también en navegador real:

| Caso y cambios sobre formulario inicial | Resultado calculado |
|---|---|
| Estático convergente | Salida 681.304221 + entrada 0 + presión 276.953463 ≈ neto 958.257683 N/(kg/s de aire); Me≈1; pe≈216.986053 kPa |
| Vuelo Mach 0,7 | 673.929721 − 238.218634 + 322.670483 ≈ 758.381570 N/(kg/s de aire); Me≈1; pe≈274.467801 kPa |
| C-D, Ae/Ag=1,5 | `supersonico_sobreexpandido_ideal`; Mg≈1; Me≈1.821278; pe≈70.516456 kPa; Fs≈979.921960 N/(kg/s de aire) |
| C-D, Ae/Ag=6 | `choque_normal_interno`; M1≈3.141495→M2≈0.456981; p1≈8.407155→p2≈96.905779 kPa; Me≈0.399778; pe≈100 kPa; Fs≈288.993259 N/(kg/s de aire) |
| Mach 0,9; rp=3; πd=0,7; T3=500 K, convergente | pt4≈84.839 kPa < p∞=100 kPa; sin expansión disponible; empuje/TSFC sin valor; cuatro estados de remanso en T–s y sin E ni gráficas de salida ficticias |

**Inspección visual y educativa.** Se conserva el diseño de seis secciones y
sus pestañas M43. Empuje está en Resultados; T–s, Mach y presión en
Visualizaciones. Las referencias Mach 1 y p∞ son legibles; ambos lados del
choque son puntos separados, sin suavizado ni distancias inventadas. En
T–s se corrige únicamente posición/contorno de rótulos y altura del SVG
(véase revisión 44.1). Se revisan el tamaño normal del navegador, la
configuración grande 1920×1080 y estrecha 390×844. En estrecho, los SVG
mantienen desplazamiento horizontal local y foco por teclado, sin ensanchar
la página. Las regiones de Mach/presión se apilan en una columna.
Las gráficas se actualizan tras POST; Mach puede permanecer en 1 al cambiar
Mach de vuelo si la salida sigue bloqueada: esa igualdad es física, no caché.
El caso sin expansión retira los SVG que requieren salida y conserva el T–s
parcial. Se guardan capturas fuera del repositorio; no se generan informes
persistentes ajenos a esta revisión. La revisión cubre estos casos y tamaños,
no todos los navegadores ni todo el dominio de entradas.

**Ejecución personal.** Abrir `Abrir_Brayton_Simulator.cmd` o ejecutar
`.\.venv\Scripts\python.exe -B web_app.py` y visitar
`http://127.0.0.1:5000/turborreactor`. Elegir ejemplo o parámetros, pulsar
«Simular turborreactor» y abrir Resultados/Visualizaciones. Para el choque,
seleccionar C-D y Ae/Ag=6 con los demás valores iniciales. Mantener el
servidor activo; Ctrl+C lo detiene. El servidor de revisión solo escucha en
127.0.0.1:5000. La sandbox inicial bloqueó ese acceso; se reinició fuera de
ella para la inspección local, sin cambiar el enlace de red de la aplicación.

**Estado final.** Los nueve archivos incorporados más una corrección mínima
en `tests/test_turborreactor_web_40.py`: cuatro archivos versionados modificados
y seis nuevos de la entrega. Los dos archivos personales conservan sus hashes
y su condición no versionada. Rama y HEAD permanecen iguales; sin staging,
commit, merge, rebase ni push. Las comprobaciones son verificación científica
interna y de integración/presentación; no validación experimental del motor.

## Commit asociado

**Pendiente.** M44.1 y M44.2 se entregan como ZIP acumulado para revisión; no se ha autorizado publicación.
