# Milestone 45 — Gasto másico, empuje absoluto y dimensionamiento de tobera

## Estado anterior y base verificada

La rama `mejoras/cp-variable` se comprobó en GitHub y se clonó de manera independiente en el commit **`52331435f1b55f01b64153517048c60809de5865`**, que incluye las entregas 44.1–44.4. El repositorio de trabajo comenzó limpio. Hasta el 44, el turborreactor proporcionaba empuje por unidad de gasto de aire, dosado, TSFC y estados estáticos de la tobera, pero ninguna escala másica o geométrica absoluta.

## Objetivo y fases implementadas

1. **45.1:** entrada opcional `gasto_masico_aire` [kg/s], caudales de aire, combustible y gases y consumo horario.
2. **45.2:** empuje absoluto en N y kN, contribuciones firmadas, contraste de TSFC y cierres.
3. **45.3:** áreas de garganta/salida por continuidad, relación de áreas y diámetros circulares equivalentes.

La integración en la interfaz, ayuda educativa, gráficas, pruebas y documentación son actividades **transversales** de las tres entregas. Esta organización no cambia las funciones, ecuaciones ni resultados existentes.

No se han modificado los solucionadores de combustión, turbina, flujo C-D, convergente, choque normal ni la hipótesis de propiedades `cp(T)`.

## Modelo físico, unidades y ecuaciones

`ṁa` [kg/s] es el gasto másico de **aire entrante** antes de combustible, no el gasto de gases. Del dosado `f` [kg combustible/kg aire] que ya calcula el milestone 37:

\[
\dot m_f=f\dot m_a,\qquad \dot m_{f,h}=3600 f\dot m_a,
\qquad \dot m_e=(1+f)\dot m_a.
\]

Del empuje específico neto `Fs` [N/(kg/s aire)]:

\[
F=\dot m_a F_s=\dot m_e V_e-\dot m_a V_0+(p_e-p_\infty)A_e.
\]

La presión del modelo está en **kPa**. En la ecuación dimensional se multiplica `(pe−p∞)` por **1000** para obtener pascales; `A_e` se expresa en m². La descomposición de momento, entrada y presión se escala exactamente por `ṁa`. Los términos pueden tener signo; el empuje negativo se conserva y el TSFC convencional es `None` cuando `F≤0` o falta salida.

Para salida física válida de cualquier tobera:

\[
A_e=\frac{\dot m_e}{\rho_e V_e},\quad
A_g=\frac{\dot m_e}{G_g},\quad
D_{e,g}=\sqrt{\frac{4A_{e,g}}{\pi}}.
\]

En tobera convergente la garganta geométrica es la salida, **incluso sin bloqueo**; su `Gg` es `ρeVe`. En tobera C-D el solucionador proporciona `flujo_masico_por_area_garganta` para garganta bloqueada o no bloqueada; no se impone M=1 cuando es subsónica. La salida tras choque normal interno o en salida utiliza el **estado estático de salida resuelto**, no el estado supersónico previo al choque. Se verifica `Ae/Ag≈ε` y el empuje dimensional frente al específico. Los diámetros son los de **círculos de igual área**, no una geometría de tobera real certificada.

## Contratos y flujo Python

Nuevo `dimensionamiento_turborreactor.py`:

- `validar_gasto_masico_aire(gasto_masico_aire)`: real `int/float` finito, `>0`, sin `bool`; devuelve `float` [kg/s] o `ValueError` comprensible.
- `calcular_prestaciones_absolutas(resultado, gasto_masico_aire)`: recibe `dict` del solucionador M37 y caudal [kg/s]; devuelve `dict` con `gasto_masico_aire`, `gasto_masico_combustible`, `consumo_combustible_hora`, `gasto_masico_gases`, `empuje_momento_salida`, `resistencia_entrada` (firmada), `empuje_presion`, `empuje_neto`, `empuje_neto_kN`, `TSFC_kg_N_h`, `residuo_empuje` y `residuo_TSFC`. Si falta salida deja `None` para fuerzas y TSFC, pero conserva caudales. No resuelve de nuevo el modelo.
- `dimensionar_tobera(resultado, gasto_masico_aire, *, absolutos=None)`: recibe dict científico, caudal [kg/s] y opcionalmente las magnitudes anteriores para evitar duplicar cálculos. Devuelve dict con `disponible`, `motivo`, `tipo_tobera`, `regimen`, `garganta_bloqueada`, `area_garganta`, `area_salida`, `diametro_garganta`, `diametro_salida`, `relacion_areas` y residuos de continuidad, área y empuje dimensional. Las dimensiones son `None` si no hay salida física. Rechaza incoherencias internas materiales con `ValueError`.
- `_finito(valor)` es una comprobación auxiliar de reales finitos que rechaza `bool`; devuelve `bool`.

En `turborreactor_web.py`, `DEFAULTS_TURBO` incorpora `gasto_masico_aire=''` (opcional), y `GRUPOS_TURBO` lo presenta en la configuración. `simular_turborreactor(valores)` valida el texto, llama **una sola vez** a `resolver_turborreactor_con_combustible`, y solo si hay caudal añade `prestaciones_absolutas` y `dimensionamiento_tobera` al resultado, sin modificar sus componentes específicos. `svg_descomposicion_empuje(resultado, *, absoluto=False)` conserva la vista 44.1 al omitir el nuevo argumento y admite N si se solicita modo absoluto. `preparar_vista_turborreactor` proporciona `svg_empuje_absoluto`, opcional. La plantilla conserva los seis apartados, la sensibilidad, mapas y todos los SVG del milestone 44.

## Ejemplo reproducible

Ambiente directo `288,15 K`, `100 kPa`, `M0=0`, compresor `rp=10`, `ηc=0,85`, combustión `T3=1600 K`, `δ=4 %`, `ηt=0,90`, `ηm=0,98`, `ηn=0,95`, `ηb=0,99`, `PCI=43 000 kJ/kg`, C-D `ε=1,5`, y caudal educativo `ṁa=20 kg/s`:

| Magnitud | Resultado |
|---|---:|
| Caudal combustible [kg/s] | 0,560564156 |
| Consumo horario [kg/h] | 2018,030962 |
| Caudal de gases [kg/s] | 20,560564156 |
| Empuje momento salida [N] | 21620,295714 |
| Resistencia de entrada [N] | 0 |
| Empuje de presión [N] | −2021,856521 |
| **Empuje neto [N]** | **19598,439194** |
| **Empuje neto [kN]** | **19,598439** |
| TSFC [kg/(N·h)] | 0,102968963 |
| Área de garganta [m²] | 0,045717175 |
| Área de salida [m²] | 0,068575763 |
| Diámetro circular equivalente garganta [m] | 0,241265239 |
| Diámetro circular equivalente salida [m] | 0,295488364 |
| Relación de áreas calculada | 1,500000 |

El estado es `supersonico_sobreexpandido_ideal`, por lo que el empuje de presión **es negativo**. El modelo no predice separación exterior. Los residuos de continuidad, relación de áreas y empuje dimensional son nulos dentro de precisión numérica.

Duplicar `ṁa` con el mismo punto termodinámico duplica fuerzas, caudales y **áreas**, pero multiplica los diámetros por `√2`; **no** cambia T, p, dosado, rendimiento, Fs ni TSFC.

## Verificación previa del entorno de desarrollo — 28/10/2026

Los resultados y restricciones siguientes son antecedentes de desarrollo; la revisión Windows de esta tarea se distingue al final.

- Pruebas específicas `python3 -m unittest -q tests.test_gasto_masico_dimensionamiento_45`: **19 correctas, 0 fallos, 0 errores y 0 omisiones**.
- Regresión científica relacionada de 45, 44 y módulos 35–42: **160 métodos, 159 correctos, cero fallos, cero errores, una omisión** (`test_propiedades_cantera_opcional`, Cantera no instalada). Comando ejecutado desde la raíz del repositorio:

```bash
python3 -m unittest -q \
  tests.test_gasto_masico_dimensionamiento_45 \
  tests.test_perfiles_tobera_44_4 \
  tests.test_balance_energetico_turborreactor_44_3 \
  tests.test_graficas_tobera_44_2 \
  tests.test_graficas_turborreactor_44_1 \
  tests.test_combustible_cp_variable_37 \
  tests.test_mapas_prestaciones_turborreactor_38 \
  tests.test_verificacion_independiente_turborreactor_39 \
  tests.test_tobera_convergente_divergente_42a \
  tests.test_choque_normal_42c \
  tests.test_propiedades_aire \
  tests.test_tobera_cp_variable_35
```

- Compilación Python: `python3 -m compileall -q dimensionamiento_turborreactor.py turborreactor_web.py tests/test_gasto_masico_dimensionamiento_45.py`; sintaxis JavaScript conservado: `node --check static/turborreactor.js`. Ambos comandos terminaron sin errores.
- En este entorno no están instalados Flask ni Jinja2. No se han instalado dependencias; la compilación Jinja en ejecución, las pruebas de integración Flask, la inspección responsive y la regresión histórica completa deben ejecutarse en Windows. **Esta batería no es la regresión total del repositorio.**

La equivalencia dimensional y conservación de las ecuaciones constituye **verificación interna**, no validación experimental de un motor real.

## Limitaciones y próximos pasos

El caudal introducido determina un **dimensionamiento condicional**, no la capacidad de admisión de un compresor real: no hay mapas de funcionamiento completos, área de entrada determinada ni predicción de caudal a partir de altitud o velocidad. No se calculan longitud de tobera, ángulos, contorno de campana, rozamiento adicional, masa de material ni longitud óptima; corresponden al eventual milestone 46. La geometría circular es una equivalencia de área elegida a efectos educativos.

## Revisión Windows — 28/10/2026

Base local verificada: `mejoras/cp-variable`, HEAD
`52331435f1b55f01b64153517048c60809de5865`; archivos versionados limpios,
dos personales no versionados. ZIP íntegro de siete rutas seguras, extraído
y comparado fuera del repositorio: tres archivos actualizados y cuatro nuevos.
Se conserva la función T–s de M44 íntegra; los solucionadores no cambian.
La corrección documental afecta solo a la numeración 45.1–45.3 y su explicación
actual; conserva las ecuaciones y la tabla de resultados anterior.

Python 3.13.0, Windows 11, entorno `.venv`, sin instalaciones:

```powershell
.\.venv\Scripts\python.exe -B -m unittest -q tests.test_gasto_masico_dimensionamiento_45
.\.venv\Scripts\python.exe -B -m unittest -q tests.test_turborreactor_web_40 tests.test_prestaciones_turborreactor_web_41 tests.test_turborreactor_web_42b tests.test_turborreactor_web_43
```

19/19 específicas y 74/74 web, sin fallos, errores u omisiones. Tras el ajuste
de formato se repiten los mismos módulos juntos: 93/93 correctas. No se suman
baterías solapadas ni se repite la regresión científica histórica. Los procesos
de pruebas usan temporales externos autorizados mediante `TMPDIR/TEMP/TMP`,
sin cambiar variables persistentes de Windows.

La revisión real confirma campo opcional [kg/s], funcionamiento con campo
vacío, aceptación de 20/40 y rechazo de 0, -3, texto y NaN con mensaje claro.
Se comprueba escalado sin cambios del punto termodinámico: fuerzas, caudales y
áreas ×2; diámetros ×√2. Se revisan tarjetas, tabla, gráfico desplegable,
unidades y dimensiones en escritorio y pantalla estrecha. El cero firmado
«−0» de la resistencia estática se normaliza solo al representarlo en tabla
y SVG; se mantienen los valores del resultado científico y todos los signos
negativos no nulos. No se rediseña CSS ni se modifica JavaScript.

Una segunda instancia antigua compartía el puerto 5000 y ocultaba el campo
nuevo. Se identifica por PID/comando y se cierra para dejar solo el servidor
actualizado; no se corrige código para resolver esa incidencia operativa.
Servidor de revisión: `http://127.0.0.1:5000/turborreactor`.

Los documentos personales mantienen su SHA-256 y siguen no versionados.
Sin staging, commit ni push; rama, HEAD y `main` intactos. Estas comprobaciones
verifican implementación y presentación, no un motor mediante ensayos externos.

## Commit asociado

Sin commit ni push en esta entrega; pendiente de autorización tras revisión Windows. No se modificó `main` ni `docs/PLAN_MEJORAS_BRAYTON_SIMULATOR.md`.
