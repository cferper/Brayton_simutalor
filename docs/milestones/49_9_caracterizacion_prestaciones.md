# Milestone 49.9 — Panel de caracterización del turborreactor

## Estado anterior

Base: rama `mejoras/cp-variable`, HEAD `ca128874527b0b2a2712ef642b68a3c91bd64d13`, que publica el 49.8. La simulación devolvía prestaciones y fichas de piezas; faltaba un inventario de indicadores comparables de ingeniería.

## Qué se ha añadido

Panel de tres pestañas **Funcionamiento**, **Consumo y prestaciones**, **Rendimientos y pérdidas** en el banco interactivo; estado, símbolo, unidad, significado y origen de cada magnitud. Cada petición existente del motor actualiza el panel; cambiar pestaña o abrir la explicación no vuelve a simular. No se cambian solucionadores ni mapas.

`caracterizar_motor_49_9(resultado)` agrega datos del resultado físico ya disponible, ejecuta únicamente cocientes o productos dimensionalmente justificados y devuelve `dict[str,list[dict]]`. Cada fila contiene `id`, `nombre`, `simbolo`, `valor`, `unidad`, `estado`, `formula`, `fuente`, `nota`. `None` significa no disponible, nunca cero. Estados: calculado (campo del resultado), derivado (operación algebraica) o no_disponible.

## Auditoría obligatoria de indicadores

Abreviaturas de disponibilidad: **A** con caudal prescrito, **B** con geometría fija resuelta, **C** con convergencia del motor acoplado; en **A sin ṁa** no existen fuerzas absolutas ni potencias. Todas las cantidades requieren que el punto tenga salida numérica verificada.

| Indicador (símbolo) | Unidad / ecuación y fuente | A/B/C | Clasificación y límite |
| --- | --- | --- | --- |
| TIT (TIT) | K; `combustor.T3` = total a turbina | Sí/Sí/Sí | Calculado; T3 interna ≈ Tt4 |
| Compresión (πc) | –; `compresor.p2/p1` | Sí/Sí/Sí | Derivado; presiones totales |
| pt2, pt3, pt4, pt5 | kPa; `compresor.p1,p2`, `combustor.p3`, `turbina.p4` | Sí/Sí/Sí | Calculados; puntos de remanso |
| Tt2, Tt3, Tt5 | K; `compresor.T1,T2`, `turbina.T4` | Sí/Sí/Sí | Calculados; remanso |
| Expansión turbina (πt) | –; `combustor.p3/turbina.p4` | Sí/Sí/Sí | Derivado, siempre entrada/salida |
| NPR | –; `tobera.presion_remanso/ambiente.presion` | Sí/Sí/Sí | Derivado; pt entrada/p∞ estática, no pt∞ |
| EPR | –; `turbina.p4/compresor.p1` | Sí/Sí/Sí | Derivado; convención descarga turbina/cara compresor, no una lectura instrumental |
| Régimen (N) | rpm; `motor_acoplado.rpm` | No/No/Sí | Calculado; únicamente monoeje C |
| Aire (ṁa) | kg/s; `prestaciones_absolutas.gasto_masico_aire` | Opc./Sí/Sí | Calculado; entrada de usuario en A |
| Gases (ṁg) | kg/s; `prestaciones_absolutas.gasto_masico_gases` = (1+f)ṁa | Opc./Sí/Sí | Calculado; aire equivalente |
| Empuje neto (Fneto) | N; `prestaciones_absolutas.empuje_neto` | Opc./Sí/Sí | Calculado; requiere caudal |
| Empuje bruto (Fbruto) | N; momento salida + presión de empuje absolutos | Opc./Sí/Sí | Derivado; incluye presión |
| Resistencia captación (Dentrada) | N; negativo de `prestaciones_absolutas.resistencia_entrada` | Opc./Sí/Sí | Derivado; magnitud positiva, incluso cero en estático |
| Empuje específico (Fs) | N/(kg/s); `prestaciones.empuje_especifico_neto` | Sí/Sí/Sí | Calculado; puede ser ≤0 |
| Combustible (ṁf) | kg/s; `prestaciones_absolutas.gasto_masico_combustible` | Opc./Sí/Sí | Calculado; exige ṁa |
| Dosado (f) | kg/kg aire; `combustor.f`, equivale a ṁf/ṁa cuando existen | Sí/Sí/Sí | Calculado; combustión equivalente |
| TSFC | kg/(N·h); `prestaciones.TSFC_kg_N_h` = 3600f/Fs | Sí/Sí/Sí | Calculado solamente si Fs > 0 |
| V∞ | m/s; `remanso.velocidad_vuelo` | Sí/Sí/Sí | Calculado |
| Ve | m/s; `tobera.velocidad_salida` | Sí/Sí/Sí | Calculado si tobera resuelta |
| ηm, ηt | –; `turbina.rendimiento_mecanico`, `rendimiento_turbina` | Sí/Sí/Sí | Calculados, modelo de referencia |
| ηc | –; `(compresor.h2s-h1)/trabajo_compresor` | Sí/Sí/Sí | Derivado a partir de entalpías reales/isentrópicas |
| δd | %; 100(1−`difusor.pt/remanso.pt`) | Sí/Sí/Sí | Derivado, caída total en difusor |
| δb | %; 100·`combustor.delta` | Sí/Sí/Sí | Derivado, caída total en cámara |
| wc, wt | kJ/kg aire; trabajos del compresor y turbina | Sí/Sí/Sí | Calculados; wt incluye 1+f |
| weje | kJ/kg aire; `ηm wt` | Sí/Sí/Sí | Derivado; balance de eje |
| Peje | kW; `ṁa weje` | Opc./Sí/Sí | Derivado; no es empuje |
| ηth, ηp, ηo | –; pendientes de balances consistentes de potencia de chorro y empuje de presión | No/No/No | **No disponibles**; no confundir con eficiencia Brayton de eje |

**Opc.** significa que A permite dejar el caudal en blanco y entonces solo proporciona magnitudes específicas. En B y C los caudales requieren que el cálculo correspondiente cierre y converja. Una salida no resuelta puede invalidar varias magnitudes aun con entradas correctas. En la API de simulación interactiva, los estados sin salida verificada devuelven error 422, sin indicadores.

## Nuevos conceptos de ingeniería

**NPR** compara la presión **total** aguas arriba de la tobera con la **estática ambiental**. **EPR** usa las presiones **totales** de salida de turbina y cara de compresor; son estaciones diferentes y en vuelo EPR y NPR divergen. La convención teórica elegida para EPR coincide con el indicador de relación de presiones a través del motor que describe el manual FAA; no garantiza correspondencia con la toma instrumental de un motor concreto. **πt** se define inequívocamente como entrada/salida (>1).

Un turborreactor no entrega potencia útil por eje al exterior, a diferencia del Brayton de eje. Definir eficiencias térmica, propulsiva y global exige un volumen de control y una separación coherente entre potencia cinética del chorro, captación y trabajo de presión. El caso V∞=0 necesita interpretación particular. Por ello se aplazan esas tres eficiencias.

Combustible: `f` resulta de un balance de entalpía con PCI y ηb; no se predicen especies ni química de combustión. TSFC es indefinido para Fs≤0. No existen N1/N2, bypass, EGT instrumental, peso, emisiones, ruido, márgenes frente a surge ni vida certificada.

## Nuevos conceptos de Python y JavaScript

El módulo de agregación `caracterizacion_motor_49_9.py` separa cálculo algebraico de representación web. `ratio` comprueba positividad del denominador y finitud; `item` normaliza metadatos y disponibilidad. `preparar_vista_turborreactor` incluye `caracterizacion`, reutilizada por la API y Jinja; el JSON anterior conserva sus claves. La interfaz mantiene `grupo` y `datos` en una clausura JS, crea textos mediante `textContent` e invalida datos al editar entradas o recibir error. No hay petición adicional al cambiar pestaña.

## Qué hemos aprendido

Una cifra puede estar disponible en un modelo educativo sin ser una magnitud instrumental real. Es fundamental identificar estaciones, bases másicas, signos y dominio. Más indicadores no significan más información si se obtienen a partir de supuestos injustificados.

## Limitaciones que siguen existiendo

No se introduce rendimiento de chorro/global, EGT, surge ni geometrías nuevas. El panel no valida un motor real y no atribuye imposibilidad física a una falta de convergencia numérica. Inspección visual final pendiente en Windows.

## Referencias primarias

- [NASA Glenn — Engine Pressure Ratio](https://www.grc.nasa.gov/www/k-12/airplane/epr.html): EPR por presiones totales de estaciones de motor; la numeración NASA varía según ubicación y configuración.
- [FAA — Pilot's Handbook of Aeronautical Knowledge, cap. 7](https://www.faa.gov/sites/faa.gov/files/09_phak_ch7.pdf): indicación EPR como relación entre descarga de turbina y entrada de compresor.

## Commit asociado

**Pendiente**: entrega en ZIP, sin `git add`, commit ni push.
