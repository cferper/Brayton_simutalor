# Milestone 44.3 — Aprendizaje del balance energético de un turborreactor

## 1. Por qué no podemos sumar las cuatro barras

El compresor **recibe** energía mecánica; el combustible **aporta** energía química efectiva; la turbina **extrae** energía del gas para accionar el compresor; la tobera convierte una parte de entalpía en **velocidad del chorro**. Estas cantidades describen transformaciones sucesivas y, en parte, dos formas de contar una misma energía. Sumarlas como ingresos independientes duplicaría flujos de energía.

La interfaz muestra por ello **magnitudes positivas por separado** y una tabla con los **residuos de cinco balances físicos independientes**.

## 2. Referencia común: un kilogramo de aire

El combustible se añade después del compresor. Si entra 1 kg de aire, al resto del motor pasan `(1+f)` kg de gases, donde `f` tiene unidades kg de combustible/kg de aire. Por eso:

- Compresor: `wc=h2−h1`, en kJ/kg aire.
- Cámara: `h2+f ηb PCI=(1+f)h3`, por kg aire.
- Turbina: `wt=(1+f)(h3−h4)`, por kg aire.
- Tobera: `ec=(1+f)Ve²/2000`, por kg aire.

La función `propiedades_aire.h(T)` ya integra `cp(T)` variable y retorna entalpía específica referida a 298,15 K [kJ/kg gas equivalente]. No se calcula `cp × ΔT` usando un calor específico fijo. Tampoco se presupone que la composición química de los gases haya sido resuelta: el modelo utiliza aire equivalente.

## 3. Cómo funciona el eje

La turbina extrae más energía del gas de la que llega realmente al compresor: `ηm × wt = wc`. Si `ηm<1`, una parte no llega al compresor. Esta eficiencia mecánica **no es** la eficiencia isentrópica `ηt`: ésta determina el estado termodinámico de expansión, mientras la primera afecta a la transmisión.

Una caída de presión total por choque no implica por sí sola que haya desaparecido la entalpía total. Por eso el balance de tobera se basa en entalpía total, entalpía estática y energía cinética, incluso si hay un choque normal resuelto.

## 4. Qué calcula cada función nueva

### `datos_balance_energetico(resultado)`

Recibe el gran diccionario científico devuelto por `simular_turborreactor`, reutiliza sus subdiccionarios y obtiene magnitudes comunes en kJ/kg de aire. Devuelve un diccionario con las cuatro barras, `eje_util`, masa relativa `factor_masico` y otro diccionario `residuos`.

La sintaxis `r['combustor']['f']` significa tomar la clave `f` del subdiccionario `combustor`. La comprensión `any(...)` permite detectar si algún término carece de sentido; `None` representa ausencia de datos, **nunca cero**. Si los residuos no cierran dentro de la tolerancia de presentación, se lanza `ValueError`; no se maquilla el gráfico.

### `svg_balance_energetico(datos)`

Recibe ese diccionario y retorna una cadena SVG con barras de cuatro colores. Solo usa las magnitudes calculadas, y escala su longitud a la mayor para que quepan. El número al final de cada barra mantiene su valor en kJ/kg aire. Si la salida de tobera no está resuelta se escribe «No disponible» sin generar una barra nula.

### Integración

`preparar_vista_turborreactor(resultado)` llama las dos funciones y añade sus resultados al contexto de Jinja, que los muestra en «Visualizaciones y transformaciones». JavaScript no resuelve física ni recalcula energías. Las seis secciones y las gráficas 44.1 y 44.2 siguen presentes.

## 5. Ejemplo y ejercicio

Con los valores por defecto: compresor `316,236`, combustible efectivo `1193,161`, turbina `322,689` y cinética de salida `225,760`, todo en kJ/kg aire. El trabajo útil del eje es `316,236` gracias a ηm. No sumes esos números: comprueba cada ecuación por separado y observa los residuos prácticamente nulos.

**Ejercicio:** aumenta Mach de vuelo y luego cambia T3. Identifica qué barras cambian y por qué. Después prueba una condición de salida no resuelta: ¿qué valor de la tobera deja de ser conocido? La respuesta correcta es `None` (no disponible), aunque los balances del compresor, cámara y turbina pueden seguir definidos.

## 6. Verificación y límites

La primera ejecución de las pruebas acumuladas de 44.1–44.3 superó 26/26 métodos el 27/10/2026 (10 nuevos). Las pruebas contrastan las ecuaciones de conservación implementadas y la estructura del SVG; no son validación experimental de un motor real.

**Antecedente del desarrollo:** en esa ejecución estaban pendientes navegador y regresión web. La revisión Windows que sigue aporta esa comprobación; los perfiles pertenecen a la entrega independiente 44.4.


## 7. Aprendizaje de la integración Windows — cierre 28/10/2026

La integración parte de `mejoras/cp-variable`, HEAD
`d61ef3795ae58027927adc5077409bb3dfe6b018`, con 44.1/44.2 ya revisados
localmente y sin commit. Se incorpora el ZIP completo y se conserva ese trabajo.
La fecha de cierre no se atribuye a la implementación original de las funciones.

**PYTHON.** `datos_balance_energetico(resultado)` consume el dict del solver,
llama a `h(temperatura)` y devuelve energías [kJ/kg aire], dosado [-], factor
másico [-] y cinco residuos. `svg_balance_energetico(datos)` consume ese dict
comprobado y devuelve `str` SVG; usa `escape` y formato decimal, sin resolver
estados. Las llama `preparar_vista_turborreactor`, que a su vez llama Flask tras
POST. Las claves ausentes pueden producir `KeyError`; los datos incoherentes
producen `ValueError`. La tolerancia de residuos es `1e-8 × escala` y la del
factor másico, `1e-10 × factor`. Las firmas, estructura completa y validaciones
se detallan en [manual §4.83](../../CODE_WALKTHROUGH.md).

Ejemplo real: `balance = datos_balance_energetico(simular_turborreactor(DEFAULTS_TURBO))`;
`balance['compresor']` vale aproximadamente 316.235549 kJ/kg aire y
`svg_balance_energetico(balance)` crea la figura. En la página se leen además
los cinco residuos. Al pasar a Mach 0,7 se recalculan todas las barras; al
usar Mach=0,9, rp=3, πd=0,7 y T3=500 K, la cinética de tobera y su residuo
pasan a «No disponible», mientras los demás balances siguen definidos.

**INGENIERÍA.** La tabla verifica cada balance por separado. La energía
cinética utiliza el caudal de gases por kg de aire: `(1+f)Ve²/2000`. No se
suman las cuatro barras ni se interpreta la pérdida de presión total de un
choque como pérdida de entalpía total.

**Verificación realizada el 27/10/2026.** 42/42 específicas de 44.1–44.4,
74/74 web y 651 en regresión vigente: 641 correctas, 0 fallos/errores y diez
omisiones justificadas (SciPy 8, Cantera 1 y un subcaso de enlace simbólico).
Se corrige, con permiso expreso, el recuento de la prueba M40 de 7 a 8 SVG;
se conservan foco y accesibilidad. El navegador real muestra barras, unidades
y tabla en tamaños grande y estrecho. No se instalan dependencias ni se
cambian ecuaciones. Es verificación interna, no validación experimental;
la entrega sigue sin commit ni publicación.
