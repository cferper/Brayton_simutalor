# Milestone 50.2 — Aprendizaje: parámetros corregidos y mapa del compresor

## De dónde partimos

El milestone 50.1 permite comparar dos soluciones estacionarias. M47 ya resuelve el acoplamiento compresor–turbina de un **turborreactor monoeje hipotético** con mapas NASA T-MATS escalados. Faltaba mostrar una lectura ingenieril del caudal y giro normalizados por condiciones de remanso, y visualizar en qué lugar del mapa se encuentra un punto convergido.

Base GitHub verificada `7036c43abf6861b7d8aad0ff4ebb0675985dd5fe` (`mejoras/cp-variable`), sin commit de esta entrega. Se reutiliza la auditoría preliminar del 11-11-2026.

## INTERPRETACIÓN FÍSICA / INGENIERÍA

### ¿Por qué corregimos caudal y rpm?

Un compresor a distintas condiciones de temperatura/presión de admisión no tiene el mismo comportamiento aerodinámico para igual caudal real. Para comparar puntos sobre una misma tabla se normalizan magnitudes con la **temperatura y presión totales a la entrada del compresor**, llamadas aquí `Tt2` y `pt2`. En código son `compresor.T1` y `compresor.p1` (no temperatura ni presión ambiente).

\[
\dot m_{corr}=\dot m_a\frac{\sqrt{T_{t2}/288.15}}{p_{t2}/101.325},\qquad
N_{corr}=\frac{N}{\sqrt{T_{t2}/288.15}}.
\]

Temperaturas K; presiones kPa; ṁ real kg/s, ṁcorr kg/s de referencia; N real rpm, Ncorr rpm corregidas. Las referencias se han elegido **expresamente** en M47, no se deducen de ISA ni del vuelo actual.

**Ejemplo:** para Tt2=288,15 K, pt2=100 kPa, ṁaire=20 kg/s y N=20 000 rpm, se obtiene ṁcorr=20×101,325/100=20,265 kg/s (referencia) y Ncorr=20 000 rpm. Si Tt2 varía, no podemos interpretar una variación de Ncorr como variación idéntica de giro mecánico real.

### ¿Qué muestra el gráfico?

Eje horizontal: **caudal corregido**. Eje vertical: **relación de presión total del compresor**. Cada curva corresponde a una velocidad corregida tabulada. Las muestras se obtienen de las matrices NASA HPC disponibles en el proyecto, con los mismos factores de escala usados por el solucionador de M47. El marcador destacado representa el **único punto C resuelto**; al modificar Mach o T3 puede moverse porque cambian las condiciones de remanso y la solución del acoplamiento.

- **Modo A:** con caudal prescrito podemos calcular ṁcorr, pero no Ncorr ni posicionar un punto acoplado.
- **Modo B:** el caudal procede de la tobera y su geometría; todavía no se resuelve el régimen del eje.
- **Modo C:** rpm, caudal y relación de compresión proceden de una solución simultánea de mapas y balance de eje; se pueden expresar en variables corregidas y situar en el mapa.

Las curvas nativas se escalaron para que un punto **educativo** de 20 kg/s de aire y 20 000 rpm reprodujera un ciclo de diseño prescrito. Esa coincidencia no valida el comportamiento fuera de diseño frente a un banco experimental.

### ¿Podemos calcular un margen de bombeo (*surge*)?

**No.** El campo `RlineStall=1` de la tabla original proporciona un borde de coordenada del mapa, pero no una línea límite experimental validada del motor simulado. Un punto que abandona la malla puede fallar la interpolación; un Jacobiano singular puede impedir el cálculo; ninguno de esos casos demuestra una inestabilidad física real. Por eso el panel comunica el dominio y limita lo representado, sin mostrar porcentajes artificiales de seguridad.

## PYTHON — Estructura de datos y funciones nuevas

### `diagnosticar_motor_50_2(resultado)`

- **Entrada:** `resultado: dict`, respuesta física ya resuelta de `simular_turborreactor`; utiliza `compresor`, `prestaciones_absolutas`, `motor_acoplado` y `modo_caudal`.
- **Salida:** `dict` serializable con `caudal_corregido_kg_s`, `giro_real_rpm`, `giro_corregido_rpm`, `entrada_compresor` (Tt en K y pt en kPa), `punto_compresor` y `curvas_compresor` (solo C), `dominio`, `avisos`, `referencia`, `modelo`, `limite`.
- **Reglas:** ausencia `None`, nada de rpm en A/B; solo genera curvas en C convergido y con coordenadas de mapa dentro del dominio. Puede propagar errores de datos corruptos, no transforma fallos del solver en resultados.
- **Reutiliza:** `flujo_corregido`, `giro_corregido`, `cargar_mapas`, y las escalas `referencia_mapa_compresor_47` conservadas por el adaptador web C del cálculo existente.
- **Llamador:** `turborreactor_web.preparar_vista_turborreactor`, que a su vez es utilizado por la ruta Flask existente. No llama a un solucionador de funcionamiento nuevo.

Ejemplo:

```python
from diagnostico_motor_50_2 import diagnosticar_motor_50_2
from turborreactor_web import simular_turborreactor, DEFAULTS_TURBO
resultado = simular_turborreactor(dict(DEFAULTS_TURBO))
diagnostico = diagnosticar_motor_50_2(resultado)
assert diagnostico['giro_corregido_rpm'] is None  # modo A
```

**Sintaxis:** `resultado.get('motor_acoplado') or {}` proporciona un diccionario vacío para resultados opcionales ausentes. La función local `valido` comprueba tipo numérico finito y signo físico; no acepta `True` como número aunque en Python `bool` herede de `int`. La lista `curvas` reúne diccionarios, cada uno con `giro_mapa`, `giro_corregido` y una lista de `puntos`.

### `svg_mapa_compresor_50_2(diagnostico)`

- **Entrada:** diccionario anterior.
- **Salida:** cadena SVG vectorial con ejes, curvas y marcador real del modo C; cadena vacía si no existe punto compatible.
- **Unidades:** horizontal kg/s corregidos, vertical relación de presión adimensional.
- **Propósito:** solo visualización de estados tabulados; no interpola una nueva solución física ni modifica las coordenadas del motor.
- **Reutiliza:** `html.escape` para atributos y títulos; no emplea librerías gráficas pesadas.
- **Llamador:** `preparar_vista_turborreactor`.

Ejemplo:

```python
svg = svg_mapa_compresor_50_2(diagnostico)
assert svg == ''  # A/B: no hay punto de mapa
```

**Sintaxis:** las listas de cadenas se construyen y se unen con `''.join(...)`; las expresiones `f'...'` insertan números formateados; `<circle tabindex="0">` permite recorrer los puntos por teclado. Las series del mapa utilizan exactamente las muestras de los nudos HPC y sus factores de escala.

## JAVASCRIPT — Estado visual sin simulación adicional

`iniciarDiagnostico50_2(documento)` devuelve `{pendiente, actualizado}` o `null` cuando el panel no existe (vista clásica). El parámetro `documento` es el DOM del navegador; las funciones internas escriben únicamente texto, crean filas y presentan un SVG devuelto por la API. Son llamadas por `inicializar48` en `static/turborreactor_interactivo.js`:

```javascript
// Tras recibir una respuesta válida del único POST:
diagnostico50?.actualizado(datos);
// En un cambio de entrada, antes de la respuesta:
diagnostico50?.pendiente('Entradas modificadas');
```

El operador `?.` evita invocar una función si el panel es `null`. `replaceChildren()` borra elementos anteriores sin conservar valores obsoletos. `textContent` introduce números/mensajes como texto y no como HTML. El visor SVG incluye consultas por cursor, foco o Enter/Espacio, sin iniciar otra simulación. La respuesta 422 no contiene cifras diagnosticadas y dispara limpieza por el controlador principal.

## Recorrido y actividades de comprobación

1. Abre `/turborreactor/interactivo`. En A sin caudal, observa «No disponible» en ṁcorr y Ncorr.
2. Introduce 20 kg/s en A y modifica Mach: aparece ṁcorr, pero no Ncorr ni un marcador de mapa.
3. Selecciona B y resuelve una geometría física: aparece ṁcorr, sin giro.
4. Selecciona C, restablece garganta de diseño y simula: verás Ncorr y un punto sobre las curvas HPC.
5. Cambia Mach o T3: observa el nuevo resultado o su ausencia explícita si el cálculo no converge; nunca interpretes el fallo como surge.

## Verificación, límites y entrega

La prueba de software contrasta las fórmulas con las funciones originales M47 y las coordenadas del mapa con el resultado de acoplamiento. No constituye validación experimental. En la integración Windows pasaron las 8 pruebas focalizadas del 50.2 y las 19 pruebas JavaScript. La regresión Python terminó con 797 correctas y 10 omitidas de 807. El [documento técnico 50.2](50_2_diagnostico_avanzado.md) distingue esta ejecución de la del entorno de desarrollo. La inspección visual queda pendiente. No se han alterado ecuaciones ni mapas. No se ha creado commit ni push.
