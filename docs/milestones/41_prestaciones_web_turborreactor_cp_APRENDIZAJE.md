# Milestone 41 — Guía de aprendizaje: sensibilidad y mapas web de un turborreactor

**Fecha de esta iteración:** 25 de octubre de 2026. **Rama:**
`mejoras/cp-variable`. **Base remota verificada:**
`bab698a026fc336efdda5ed24b6e7d9f22bd0a97`.

## 1. De resolver un motor a estudiar muchas configuraciones

En el milestone 40 disponíamos de una aplicación `/turborreactor` con cinco
pantallas: podíamos fijar una configuración, simularla y ver las estaciones.
En el milestone 38 ya habíamos programado los barridos de prestaciones; el
milestone 39 había separado el estado físico real del cumplimiento de filtros.
La novedad de esta fase es **la interfaz de exploración**, no una ecuación
termodinámica nueva.

Ahora hay siete pantallas independientes:

1. Configuración: las entradas actuales del motor.
2. Resultados: empuje bruto, neto y TSFC de un solo punto.
3. Estaciones: temperaturas, presiones y entalpías.
4. Visualizaciones: componentes y estados del núcleo.
5. Sensibilidad: OFAT de una variable (2–31 evaluaciones).
6. Mapas de prestaciones: barridos de dos variables (hasta 15×15).
7. Fundamentos: modelo físico y limitaciones.

Con JavaScript sólo se muestra el panel activo; la rueda desplaza su contenido,
no avanza al siguiente. Los enlaces `#sensibilidad` y `#mapa`, las teclas y el
historial atrás/adelante funcionan igual que los cinco paneles anteriores.
Sin JavaScript las secciones quedan apiladas, pero sus formularios POST son
operativos: una degradación progresiva que permite seguir utilizando la web.

## 2. Física: OFAT frente a un mapa bidimensional

**OFAT** (*One Factor At a Time*) significa cambiar una variable dejando
**idénticas las demás**. Por ejemplo, para `rp = 5, 7.5, 10, 12.5, 15`,
mantener `T3=1600 K`, `Mach=0` y todos los rendimientos constantes permite
aislar el efecto de variar la compresión.

Para cada configuración, el núcleo M37 resuelve de nuevo:

- Compresor: aumento de entalpía y trabajo específico `wc=h2−h1` [kJ/kg aire].
- Cámara energética: `f=(h3−h2)/(ηb PCI−h3)` [kg combustible/kg aire].
- Eje acoplado: `ηm(1+f)(h3−h4)=wc` [kJ/kg aire].
- Turbina y tobera convergente: salto de entalpía disponible, posible bloqueo
  sónico y presión estática de salida, con aire equivalente de propiedades
  variables. `p4` es una **presión de remanso**, no la presión exterior.
- Empuje neto: `Fs = (1+f)Ve + (1+f)1000(pe−p∞)/(ρe Ve) − V∞`
  [N/(kg/s de aire)], donde el factor 1000 convierte kPa a Pa.
- Consumo específico cuando `Fs>0`: `TSFC=3600 f/Fs` [kg/(N·h)].

Por ello una curva creciente de Fs con la compresión no es una ley universal:
al aumentar `rp` también aumenta el trabajo exigido a la turbina, que puede
consumir margen de expansión de la tobera. Asimismo, una T3 mayor aporta
energía, pero también modifica el combustible requerido. **OFAT no revela
interacciones** si Mach y T3 cambian simultáneamente.

Un **mapa paramétrico** sí varía dos entradas:

- **A: rp–T3.** El ambiente y Mach son comunes a todos los puntos. Para una
  misma situación de vuelo, podemos comparar empuje y TSFC y construir Pareto.
- **B: Mach–altitud geopotencial ISA.** El estado ambiente cambia en cada
  fila y Mach en cada columna; son escenarios distintos, no motores
  comparados en idénticas condiciones. Sus extremos son descriptivos y no se
  construye un Pareto global.

Estos mapas **no** son mapas reales de funcionamiento del motor. No se
determinan línea de funcionamiento, gasto corregido, velocidad de giro,
componentes acoplados fuera de diseño ni geometría variable.

## 3. Validez, estados físicos y por qué «—» no significa cero

La clasificación científica procede de M38/M39:

| Código | Significado en la vista |
| --- | --- |
| `valido` | Existe expansión y empuje neto positivo; Fs y TSFC utilizables. |
| `empuje_no_positivo` | Se puede conocer Fs incluso si es negativo; no sirve para minimizar TSFC de propulsión útil. |
| `sin_expansion` | La presión total tras la turbina no permite expansión; Fs y TSFC quedan `None`. |
| `inadmisible` | Dominio físico o temperatura inválidos, o restricción incumplida. |
| `fallo_numerico` | La inversión numérica no encuentra una solución fiable. |

En las tablas, `None` se muestra como **«—»**. En los gráficos se marca con
**×**, y una curva OFAT se interrumpe al llegar a un punto sin estado válido.
Esto importa porque unir dos puntos válidos separados por un estado inadmisible
supondría que existe una trayectoria intermedia, justamente lo que no sabemos.
La tabla conserva un Fs no positivo cuando el cálculo efectivamente lo ha
obtenido, pero no lo transforma en propulsión útil.

La normalización de restricciones del milestone 39 sigue en su módulo original.
Relajar un filtro puede cambiar `cumple_restricciones`, pero no reescribe un
estado físico `inadmisible` como `valido` ni lo introduce artificialmente en
extremos o Pareto.

## 4. Extremos discretos y compromiso de Pareto

Para `N` puntos calculados, «máximo Fs» significa `max(Fs_i)` **entre los
puntos válidos de la malla**, no máximo global continuo. Lo mismo se aplica a
`min(TSFC_i)`. El resumen M38 informa si la celda elegida está en la
**frontera de malla**; esto sugiere explorar otro rango, no demostrar un
óptimo absoluto.

Dos objetivos compiten:

- Maximizar Fs [N/(kg/s de aire)].
- Minimizar TSFC [kg/(N·h)].

La configuración A **domina** a B si `Fs_A >= Fs_B`,
`TSFC_A <= TSFC_B` y al menos una desigualdad es estricta. El frente de
Pareto reúne los puntos no dominados. Visualmente se representan todos los
puntos válidos en azul y los no dominados con círculos más grandes y borde;
la leyenda y los títulos indican su clase sin depender del color. La función
científica es `frente_pareto(puntos)` (M38), calculada por el resumen del
barrido rp–T3. No se usa para Mach–altitud.

## 5. PYTHON — Arquitectura y flujo HTTP

Se añade **un solo módulo de presentación**,
`prestaciones_turborreactor_web.py`. Su tarea no es calcular `cp(T)`, `f` ni
equilibrios de trabajo: utiliza los módulos que ya existen. El flujo es:

```text
Navegador /turborreactor
  ├─ GET → valores por defecto y 7 paneles
  └─ POST (accion)
       ├─ simular → lector M40 → solucionador M37 → resultados individuales
       ├─ sensibilidad → preparar_estudio → barrer_rp_t3 (M38) por cada punto
       └─ mapa → preparar_estudio → barrer_rp_t3 o barrer_mach_altitud (M38)
                           ↓
                  tabla / SVG / diagnósticos → plantilla Jinja
```

La ruta `turborreactor()` en `web_app.py` **cambia** de una operación POST a
tres acciones. Sigue recibiendo **cero argumentos explícitos** (Flask facilita
`request`), devuelve `(HTML, estado HTTP)` y captura `ValueError`,
`EstadoFueraDeRango` y `ErrorNumericoCiclo` para mostrarlos con lenguaje
comprensible. Cuando se solicita un estudio también se recalcula el caso
individual con los parámetros enviados, de modo que «Resultados» no desaparece
al visitar Sensibilidad o Mapas. Los informes históricos no reciben datos.

Los formularios de estudios son **hermanos** del formulario principal porque
HTML no permite un formulario dentro de otro. Cada uno tiene campos ocultos
con los valores de motor más recientemente renderizados. El callback de
`static/turborreactor.js` asociado a `submit` sustituye esos ocultos por las
entradas **actualmente editadas** antes del POST:

```javascript
estudio.querySelectorAll('input[data-motor-field]').forEach(oculto => {
  if (oculto.name === 'modo_ambiente') {
    oculto.value = modos.find(r => r.checked)?.value || 'directo';
  } else if (form.elements[oculto.name]) {
    oculto.value = form.elements[oculto.name].value;
  }
});
```

`forEach` recorre nodos de entrada, `dataset` permite identificar el
subformulario, `?.` consulta una propiedad aunque el elemento falte y
`||` proporciona un valor de respaldo. Sin JavaScript, los ocultos ya están
rellenos con los últimos valores del servidor; si se edita una nueva
configuración en Configuración, primero se debe pulsar «Simular» para
reflejarla en los estudios sin JS. Un selector de mapa alterna la visibilidad
de los rangos A/B; el servidor valida únicamente el rango utilizado.

### 5.1. Contratos de las funciones Python nuevas

Los helpers internos comienzan por `_`: significan «uso interno del módulo»,
no son ecuaciones nuevas. Las entradas numéricas indicadas como `float` son
números reales finitos; los valores del formulario son `str` hasta validación.

| Firma completa | Entrada, salida y unidades; papel/casos especiales |
| --- | --- |
| `valores_estudios(formulario=None)` | `None` o mapping `str→str`; devuelve `dict[str,str]` con mínimos/máximos, selector y tamaños; **sin convertir unidades**. Copia `DEFAULT_ESTUDIOS` y conserva texto inválido para redisplay en POST. Llamada por Flask y `preparar_estudio`. |
| `_real(valores, clave, minimo, maximo)` | Dict de cadenas, nombre y límites `float` de igual unidad → `float` finito, o `ValueError` por texto/no finito/fuera de rango. Llamada por `_eje`. |
| `_entero(valores, clave, minimo, maximo)` | Dict de cadenas, nombre, límites enteros → `int`; rechaza valores fraccionarios y mallas fuera de 2–31 (OFAT) o 2–15 por eje (mapa). Llamada por `preparar_estudio`. |
| `_eje(valores, clave_min, clave_max, limite_min, limite_max, n)` | Controles, claves, cotas `float` y número `int` ≥2 → `list[float]` creciente, con extremos incluidos en la misma unidad del parámetro; lanza `ValueError` si mínimo≥máximo. Llamada por `preparar_estudio`. |
| `_argumentos_comunes(datos)` | Diccionario científico de `leer_turborreactor` → nuevo dict con `eta_c,eta_t,eta_m,eta_n,eta_b,PCI,pi_d,delta` [fracciones salvo PCI en kJ/kg]. No muta entradas. Llamada por `preparar_estudio`. |
| `_ambiente_mapa(datos)` | Dict científico con `altitud_geopotencial` [m] **o** `T_amb` [K] y `p_amb` [kPa] → dict que conserva sólo la alternativa activa. Llamada por `preparar_estudio`. |
| `_base_svg(ancho, alto, cuerpo, descripcion)` | Enteros de dimensiones gráficas en unidades SVG, lista de fragmentos `str`, descripción `str` → SVG completo `str` con `width`, `height`, `viewBox`, etiqueta accesible; usa `html.escape` para texto descriptivo. Llamado por los tres generadores SVG. |
| `_svg_curva(puntos, parametro, unidad_x, clave, titulo, unidad_y)` | Lista de `{valor_parametro:float,punto:dict M38}` y cadenas de identificadores/unidades → SVG `str` de Fs o TSFC. `None`/estado no válido rompe segmentos; marcas × para ausencias. La llama `preparar_estudio`. |
| `_color(valor, minimo, maximo, clave)` | Prestación válida y extremos `float` en las mismas unidades + clave `Fs`/`TSFC_kg_N_h` → `str` CSS `hsl(...)`. Sólo dibuja escala, no evalúa ciencia; si máximo=mínimo toma tono intermedio. Lo llama `_svg_mapa`. |
| `_svg_mapa(mapa, clave, titulo)` | Diccionario del barrido M38, clave física y etiqueta → SVG `str` de celdas con unidades, escala, ejes, valores y × para `None`. Lee dimensiones de la malla y estado de cada celda; llama `_color`, `_base_svg`. La llama `preparar_estudio`. |
| `_svg_pareto(mapa)` | Mapa M38 **comparable** rp–T3 → SVG `str` de dispersión, marco, ejes, puntos válidos y los no dominados; toma `mapa['pareto']` calculado por M38 (no recalcula dominancia). Devuelve aviso SVG si no hay válidos. La llama `preparar_estudio` sólo para mapa A. |
| `preparar_estudio(accion, formulario, valores_motor)` | `accion:str` (`'sensibilidad'` o `'mapa'`), controles `dict[str,str]`, motor `dict[str,str]` → dict de vista. Para OFAT contiene `tipo,parametro,etiqueta,unidad,puntos,grafico_Fs,grafico_TSFC,cuenta_validos,total`; para mapa `tipo,nombre,datos,grafico_Fs,grafico_TSFC,grafico_pareto,filas`. Invoca `leer_turborreactor`, validadores, constructor de ejes y barridos M38. `ValueError` ante selector, número o dominio no permitido. La llama Flask. |

**Funciones JavaScript locales:** `mostrarMapa()` no recibe argumentos, alterna
fieldset según `selectorMapa.value` y no devuelve valor; `sync()` preservado
de M40 habilita sólo el modo ambiental elegido. Sus eventos `change` y
`submit` reciben eventos HTML, no datos físicos. La selección OFAT cambia
rangos **sugeridos**, siempre editables. Las funciones de navegación
`elegir(id,moverFoco=false)`, `porUrl()` y `sincronizarHistoria()` siguen
operando sobre los siete `.turbo-section[id]`: no se duplica lógica de scroll
ni se altera la navegación del dashboard Brayton.

### 5.2. Ejemplos de Python y conceptos nuevos

```python
from prestaciones_turborreactor_web import preparar_estudio
from turborreactor_web import valores_turborreactor

motor = valores_turborreactor()  # dict con valores como cadenas
controles = {"sens_parametro":"rp", "sens_min":"4", "sens_max":"20",
             "sens_n":"9"}
resultado = preparar_estudio("sensibilidad", controles, motor)
print(resultado["total"])               # 9 puntos (no nueve motores distintos)
print(resultado["puntos"][0]["punto"]["estado"])  # diagnóstico científico
```

El operador `**fijos` pasa pares de un dict como argumentos nombrados a
`barrer_rp_t3`, por ejemplo `mach=0` y `pi_d=1`; `dict.copy()` o `{**a,**b}`
evita cambiar la configuración original. La comprensión
`[inferior+(superior-inferior)*i/(n-1) for i in range(n)]` construye `n`
valores, **incluidos los extremos**; su división por `n-1` exige que `n>=2`.
`enumerate` aporta índices y los pares `indices=(iy,ix)` relacionan cada
punto con su celda. El módulo científico ya devuelve un `dict` estructurado,
que Jinja recorre con `{% for ... %}` y formatea numéricamente sólo cuando
existe un número. `None` no debe convertirse en `0`.

### 5.3. SVG sin dependencias

Los gráficos se construyen como cadenas con elementos SVG (`<line>`,
`<polyline>`, `<circle>`, `<rect>`, `<text>` y `<title>`). Una curva OFAT
inicia una nueva polilínea después de un `None`: el cierre de segmento
evita interpolar sobre un estado imposible. En mapas, cada celda contiene
un número redondeado o ×; la escala se calcula sólo con valores válidos.
Un `<title>` aporta la descripción de la celda al lector/navegador.
`html.escape` se aplica a etiquetas textuales interpoladas; los SVG de
producción sólo incluyen números ya validados y etiquetas conocidas.

Las zonas contenedoras tienen `tabindex="0"`, `role="region"`, etiqueta
accesible y `overflow-x:auto`. Un SVG de 15 columnas conserva anchura legible
y se desplaza **dentro de su tarjeta**, incluso con flechas horizontales de
teclado; no ensancha el documento entero.

## 6. Límites didácticos de entradas y tiempo de servidor

El usuario configura mínimo, máximo y muestras; se validan **antes** de llamar
al módulo M38. OFAT permite entre 2 y 31 valores (11 por defecto). Los mapas
permiten entre 2 y 15 por eje (5×5 por defecto, máximo 225 puntos). `int`
rechaza `3.5`, `float` más `isfinite` rechaza `NaN` e infinito, y `_eje`
rechaza intervalos invertidos o constantes. En esta interfaz se acota:

| Variable | Intervalo disponible en web | Unidad |
| --- | --- | --- |
| `rp` | 1,01–40 | – |
| `T3` | 200–2000 | K |
| `mach` | 0–0,95 | – |
| `eta_c` y `eta_t` | 0,2–1 | – |
| `pi_d` | 0,5–1 | – |
| `delta_pct` | 0–30 | % de pérdida, que se convierte a fracción `delta` |
| Altitud ISA (sólo mapa B) | 0–20000 | m geopotenciales |

Son límites prácticos de formulario, **no** garantías de viabilidad ni límites
certificados de un motor. `T3=200 K` puede cumplir el dominio de propiedades
pero resultar imposible en un compresor que ya entrega aire más caliente.
También puede existir empuje no positivo con temperaturas admitidas.

## 7. Reproducción de las tres referencias

Las pruebas usan las **mismas** pérdidas y eficiencias por defecto M38:
`eta_c=.85`, `delta=.04`, `eta_t=.9`, `eta_m=.98`, `eta_n=.95`,
`eta_b=.99`, `PCI=43000 kJ/kg`, salvo el `pi_d` explícito del caso B.

| Caso | Ejes y condiciones | Resultados numéricos |
| --- | --- | --- |
| A | rp=[5,7.5,10,12.5,15], T3=[1400,1500,1600,1700,1800] K; T∞=288.15 K, p∞=100 kPa, Mach=0, πd=1 | 25/25 válidos; Fs máximo **1077.684377** en (15,1800 K); TSFC mínimo **0.086202290** en (15,1400 K); **7** no dominados |
| B | Mach=[0,.2,.4,.6,.8], ISA=[0,5000,10000,15000,20000] m; rp=10,T3=1600 K; **πd=.98** | 25/25 válidos; Fs máximo **1030.247814** en Mach=0 y 15 km; TSFC mínimo **0.105830471** en Mach=0 y 0 m; sin Pareto global |
| C | rp=[4,6,8,10,12,14,16,18,20], T3=1600 K; T∞=288.15 K, p∞=100 kPa, Mach=0, πd=1 | 9/9 válidos; Fs máximo **966.084294** en rp=14; TSFC mínimo **0.092158889** en rp=20; 4 puntos Pareto entre los evaluados |

Los casos A y C parten del preset web M40 (difusor ideal con `pi_d=1`).
Para repetir B debe escribirse **0.98** en la recuperación del difusor del
formulario principal; si se deja `pi_d=1`, los números cambian. Reproducir
estos valores es una comprobación de integración contra referencias de
software M38, no un contraste experimental independiente.

## 8. Pruebas, ejercicios y límites

En esta iteración se desarrollaron `tests/test_prestaciones_turborreactor_web_41.py`
(25 pruebas) y se ejecutaron junto con las 27 pruebas del milestone 40.
Se comprueban rutas, valores retenidos, formularios separados, navegación,
límites, rechazos antes de resolver, ambos barridos, Casos A/B/C, estado
inadmisible sin cero inventado, coste de 31/225 evaluaciones, Pareto aplicable
sólo en A, regresión del simulador individual e invariancia del historial.
La suite completa se ejecutó una vez al cierre: **557 pruebas descubiertas,
548 superadas, nueve omitidas opcionalmente y cero fallos**, con
`python -m unittest discover -s tests -q` en Linux/Python 3.12 con el entorno
aislado preexistente. Las omisiones corresponden a contrastes opcionales y no
se presentan como pruebas correctas ejecutadas.

**Experimentos educativos:**

1. Ejecuta OFAT de rp en [4,20] con 9 puntos y T3=1600 K. Localiza el
   máximo Fs y el menor TSFC: son puntos distintos. Explica por qué.
2. Ejecuta rp–T3 con 5×5. Aumenta a 9×9, si el tiempo de cómputo lo permite.
   ¿Se mantienen los extremos? ¿Qué indica un extremo en frontera?
3. Ejecuta Mach–altitud con πd=0,98 y después con πd=1. ¿Qué cambia si el
   difusor se idealiza? ¿Por qué no es una comparación de diseño Pareto?
4. Baja T3 hasta una combinación inviable. Comprueba que aparece × y un
   estado, no un supuesto Fs=0 que podría falsear una optimización.

**Verificación ≠ validación.** Los tests verifican conservación de contratos,
filtros, aritmética y presentación, más regresión frente a valores antes
calculados. La predicción física de un turborreactor real exigiría mediciones
experimentales con geometría, caudales, mapas de compresor/turbina, composición
variable de gases, combustión real, enfriamientos, regulación y límites de
funcionamiento. Este trabajo no incorpora nada de eso ni abre el milestone 42.

## 9. Archivos y publicación

- **Nuevo:** `prestaciones_turborreactor_web.py`, la prueba M41, el documento
  técnico y esta guía.
- **Actualizados:** `web_app.py`, `templates/turborreactor.html`, CSS/JS del
  turborreactor, la expectativa de paneles de la prueba M40,
  `.github/workflows/verificacion_web_cp_variable.yml`, `README.md` y
  `CODE_WALKTHROUGH.md`.
- **Intactos:** módulos científicos 34–39, `ciclo_cp_variable.py`, el
  dashboard convencional y código de informes históricos.
- **Estado Git:** base indicada arriba; un commit del milestone 41 aún
  pendiente en el momento de preparar este documento. Su hash definitivo
  sólo puede conocerse después de crearlo, por lo que no se inventa aquí.

Para detalles actualizados del flujo HTTP y las firmas véase la sección
**4.76** de [CODE_WALKTHROUGH.md](../../CODE_WALKTHROUGH.md) y el
[milestone técnico 41](41_prestaciones_web_turborreactor_cp.md).
