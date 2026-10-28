# Milestone 44.3 — Balance energético por componentes del turborreactor

## Estado anterior

La base publicada continúa siendo `d61ef3795ae58027927adc5077409bb3dfe6b018`, rama de referencia `mejoras/cp-variable`. Las entregas 44.1 y 44.2 están presentes en esta copia reconstruida desde su ZIP acumulado; aún no se han publicado. No se ha efectuado commit, push ni modificación de `main`.

## Qué se ha añadido

Una gráfica de cuatro barras y una tabla independiente con residuos energéticos en la sección «Visualizaciones y transformaciones». Las barras representan **magnitudes** de transformaciones sucesivas; **no deben sumarse** porque no son cuatro aportaciones independientes al mismo balance.

Todas las magnitudes se normalizan por **kilogramo de aire de entrada**, en kJ/kg de aire. La entalpía utiliza el mismo origen de referencia `h_aire(298,15 K)=0` que el modelo y `cp(T)` variable, sin introducir `cp` constante.

## Modelo y ecuaciones reutilizadas

1. **Compresor**, trabajo entrante `wc=h2-h1` [kJ/kg aire]. El compresor es adiabático en el modelo.
2. **Cámara**, aporte químico efectivo `q=f ηb PCI`; por cada kg de aire, el balance utilizado es `h2 + f ηb PCI = (1+f)h3`. `PCI` se mide en kJ/kg combustible, `f` en kg combustible/kg aire y `ηb` es adimensional. No es un balance químico detallado ni implica composición variable; se desprecia la entalpía sensible de combustible entrante según la referencia del solucionador.
3. **Turbina**, trabajo extraído de gases `wt,aire=(1+f)(h3-h4)` [kJ/kg aire]. El trabajo útil por el eje es `ηm wt,aire=wc`. No se confunde ηm con la eficiencia isentrópica ηt; la diferencia de transmisión no se inventa como pérdida de calor calculada.
4. **Tobera**, si hay estado de salida resuelto, energía cinética del gas `ec,e=(1+f)Ve²/2000` [kJ/kg aire]. El modelo cumple `(1+f)(h4-he)=ec,e`, donde `he=h(Te)` [kJ/kg gas] y `Ve` está en m/s. El factor 2000 convierte V²/2 [J/kg] a kJ/kg. El plano 4 se usa como estado de remanso de entrada a tobera, no como entrada con velocidad calculada independiente.

Cada residuo se calcula como *entrada menos salida* de su balance particular:

| Componente | Residuo [kJ/kg aire] |
|---|---|
| Compresor | `h1 + wc − h2` |
| Cámara | `h2 + f ηb PCI − (1+f)h3` |
| Turbina | `(1+f)(h3−h4) − wt,aire` |
| Eje | `ηm wt,aire − wc` |
| Tobera | `(1+f)(h4−he) − (1+f)Ve²/2000` |

No se construye una ecuación global artificial sumando las cuatro barras. La caída de presión total por choque no se convierte en una supuesta pérdida de entalpía total: un choque adiabático sin trabajo puede conservar ésta aun generando entropía.

## Python, Jinja y manejo de ausencia de datos

- `datos_balance_energetico(resultado)` extrae `compresor`, `combustor`, `turbina` y `tobera`. Comprueba números finitos, normalización `(1+f)` y residuos. Devuelve un diccionario con `compresor`, `combustor`, `turbina`, `eje_util`, `tobera_cinetica`, `f`, `factor_masico` y `residuos`. Si no hay tobera o su velocidad de salida es `None`, `tobera_cinetica` y el residuo de tobera son `None`, sin afectar los otros cierres. Si hay velocidad pero falta temperatura o la velocidad es inválida, se lanza `ValueError`. Incoherencias materiales se rechazan mediante `ValueError`.
- `svg_balance_energetico(datos)` genera cuatro barras SVG y un rótulo «No disponible» sin dibujar una barra cero falsa cuando falta la salida.
- `preparar_vista_turborreactor` incorpora `balance_energetico` y `svg_balance_energetico` a la vista que ya proporciona las gráficas 43, 44.1 y 44.2.
- `templates/turborreactor.html` añade un bloque de gráfica, explicación y tabla de cinco cierres en la sección existente. No cambia la navegación, el modelo físico ni el JavaScript.
- `tests/test_balance_energetico_turborreactor_44_3.py` prueba las identidades, unidades, salidas ausentes, respuestas a parámetros, SVG y conservación de las gráficas anteriores.

## Resultados reproducibles

Caso base (T∞=288,15 K, p∞=100 kPa, Mach 0, rp=10, T3=1600 K, parámetros por defecto):

| Barra | Valor [kJ/kg aire] |
|---|---:|
| Trabajo al compresor | 316,235549 |
| Combustible efectivo | 1193,160806 |
| Trabajo extraído por turbina | 322,689336 |
| Energía cinética de salida | 225,760070 |

`f≈0,028028208`, factor de caudal tras combustión `1+f≈1,028028208` y trabajo útil al eje `≈316,235549 kJ/kg aire`. Residuos compresor, cámara y turbina 0 dentro de precisión; eje aproximadamente `−1,22×10⁻¹¹` y tobera `−5,68×10⁻¹⁴ kJ/kg aire`.

## Verificación previa del desarrollo — 27/10/2026

Los resultados y limitaciones siguientes corresponden al entorno previo; la revisión Windows se distingue más abajo.

- Primera batería acumulada: `python3 -m unittest -v tests.test_balance_energetico_turborreactor_44_3 tests.test_graficas_tobera_44_2 tests.test_graficas_turborreactor_44_1`: **26 métodos correctos, 0 fallos, 0 errores, 0 omisiones** (10 M44.3, 9 M44.2, 7 M44.1).
- La gráfica SVG del caso base se exportó y examinó para comprobar legibilidad del formato de barras. Una exportación aislada no sustituye la revisión interactiva Flask/Jinja en un navegador.
- Regresión científica relacionada:
  `python3 -m unittest -q tests.test_balance_energetico_turborreactor_44_3 tests.test_graficas_tobera_44_2 tests.test_graficas_turborreactor_44_1 tests.test_combustible_cp_variable_37 tests.test_mapas_prestaciones_turborreactor_38 tests.test_verificacion_independiente_turborreactor_39 tests.test_tobera_convergente_divergente_42a tests.test_choque_normal_42c tests.test_propiedades_aire tests.test_tobera_cp_variable_35`:
  **125 métodos: 124 correctos, 0 fallos, 0 errores y 1 omisión**. La única omisión es `test_propiedades_cantera_opcional` del milestone 39, cuyo paquete científico externo Cantera es expresamente opcional y no está instalado.
- `python3 -m compileall -q turborreactor_web.py tests/test_balance_energetico_turborreactor_44_3.py`: correcto.
- `node --check static/turborreactor.js`: correcto, sin cambios en JavaScript.
- **Limitación del entorno de revisión:** Flask y Jinja2 no están instalados; por instrucción no se han instalado dependencias. Quedan pendientes la compilación dinámica de la plantilla con Jinja2, las pruebas web y la inspección final de la página en Windows. No se declara una regresión completa de todo el repositorio.

La verificación numérica es comprobación interna del software, **no validación científica experimental**. La predicción no contempla combustión química completa, pérdidas viscosas de tobera, transferencia de calor al exterior, distribución espacial de flujo ni rendimiento fuera de diseño.

## Alcance original de esta entrega

En el desarrollo original de 44.3 no se incluyeron perfiles intermedios. La entrega acumulada actual los incorpora como [44.4](44_4_perfiles_cuasidimensionales_tobera.md), sin convertirlos en una capacidad atribuida a esta fase.

## Integración y revisión Windows — 27/10/2026

Se incorpora desde `milestone_44_completo_para_revision.zip`, junto a 44.4,
sobre la rama `mejoras/cp-variable`, HEAD
`d61ef3795ae58027927adc5077409bb3dfe6b018`. Windows ya contenía la revisión
44.1/44.2 sin commit, que se conserva. No se cambian ecuaciones, solucionadores
ni tolerancias físicas; no se instalan paquetes.

Python 3.13.0, Windows 11 (10.0.26300), `.venv`: **42/42** específicas acumuladas,
**74/74** de integración web y **651** en regresión vigente: 641 correctas,
0 fallos, 0 errores, 10 omisiones justificadas. No se suman baterías solapadas.
Los comandos completos e incidencias están en la revisión Windows del
[técnico 44.4](44_4_perfiles_cuasidimensionales_tobera.md).

Se verifican en la página las cuatro barras, sus unidades y cinco balances.
Los valores del caso inicial reproducen la tabla anterior; en vuelo cambian
a 346.721070, 1132.213118, 353.797010 y 221.207294 kJ/kg aire, respectivamente
(las etiquetas se redondean). Ante ausencia de expansión, la cinética y su
residuo son «No disponible»; los otros cuatro balances siguen calculados.
La condición se representa como ausencia, sin un cero ficticio ni datos anteriores.

La prueba de accesibilidad M40 se actualiza de 7 a 8 SVG para el caso inicial,
con autorización expresa del usuario porque queda fuera del ZIP. Conserva
foco, nombre y desplazamiento; no se relajan comprobaciones. Se preserva
el ajuste visual anterior del T–s y su documentación. Esta inspección incluye
pantalla grande y estrecha y no equivale a validación experimental.

Cierre documental de esta revisión: **28/10/2026**. Los resultados anteriores
corresponden a las ejecuciones realizadas el 27/10/2026; no se presentan como
una nueva ejecución durante el cierre.

## Commit asociado

Pendiente de autorización: 44.1–44.3 se preparan conjuntamente en un ZIP de revisión. No se ha hecho commit ni push.
