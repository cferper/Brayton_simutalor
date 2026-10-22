# Nuevo Plan de Mejoras — Fase 1: verificación numérica

Documento educativo del **22 de octubre de 2026**. No debe confundirse esta **nueva Fase 1 de verificación numérica y comparación de modelos** con la **antigua Fase 1 de dominio físicamente viable** ([milestone 03](03_dominio_viable.md)).

**Base histórica de la fase:** `27d4519094d5eb74f5009a1889a1e74dc8dddb94` (rama `main` en el inicio de la Tarea 1.1). La Tarea 1.1 está publicada en la rama `mejoras/verificacion-numerica`, commit `275e7558b7d05322054f89ecd672ed5563c59469`. La Tarea 1.2 también se publicó allí, en `143d10fd25ebd23ddb897722b7843bddabfd16a5`. **La Tarea 1.3 parte exactamente de ese segundo commit remoto**; sus cambios están sólo en una nueva copia de trabajo y pendientes de revisión, sin commit.

## 1. Estado anterior y propósito

Antes de la tarea, el simulador calculaba ciclos ideales y no ideales, clasificaba el dominio motor, buscaba óptimos analíticos y numéricos, estudiaba sensibilidad, mapas y segunda ley. Ya existían pruebas de referencias físicas, límite reversible, fronteras, relación óptima, búsqueda numérica independiente del candidato analítico e integración. No se han duplicado esas verificaciones de forma aislada.

Faltaba contrastar **sistemáticamente varios puntos motores ideales** con expresiones escritas directamente en el propio test y medir los residuos de conservación. El objetivo es detectar errores de implementación en estados, unidades, signos, energía y rendimiento **antes** de añadir modelos más complejos. Se añade únicamente `tests/test_verificacion_analitica.py` y se actualiza el manual; las funciones de producción, constantes, optimizadores, HTML, Flask y dependencias **no cambian**.

## 2. Interpretación física y referencias independientes de implementación

Hipótesis: gas ideal con `cp` y `gamma` constantes; compresión y expansión isentrópicas, calentamiento y enfriamiento isóbaros; ciclo motor abierto en relación de presiones (`rp>1` y aporte/trabajo positivos). `T1` y `T3` son temperaturas absolutas en K; `cp` se recibe en J/(kg·K), `rp` y `gamma` son adimensionales.

Las referencias se construyen **sin llamar a `calcular_estados`, `calcular_temperaturas` ni `calcular_ciclo_ideal`** para obtener los valores esperados:

```python
a = (gamma - 1) / gamma
T2_ref = T1 * rp**a
T4_ref = T3 / rp**a
wc_ref = cp * (T2_ref - T1) / 1000
wt_ref = cp * (T3 - T4_ref) / 1000
qin_ref = cp * (T3 - T2_ref) / 1000
qout_ref = cp * (T4_ref - T1) / 1000
```

**INGENIERÍA.** `wc` representa consumo positivo de compresor; `wt`, trabajo positivo de turbina; `qin`, calor aportado, y `qout`, calor rechazado positivo. Dividir por 1000 convierte J/kg a **kJ/kg**. El código devuelve `wc`, `wt`, `wneto` y `qin`, pero **no** devuelve `qout`: en las pruebas se obtiene a partir de las temperaturas.

Se comprueban las identidades de primera ley:

\[
w_{neto}=w_t-w_c=q_{in}-q_{out},\qquad
R_E=w_{neto}-(q_{in}-q_{out})\quad [\mathrm{kJ/kg}].
\]

La comparación de estados y energías con ecuaciones escritas en el test es una referencia **separada del código de producción**, aunque algebraicamente usa el **mismo modelo físico**. Las igualdades de trabajo y primera ley, incluido `R_E`, son **controles internos de consistencia**; no constituyen dos experimentos independientes ni prueban que el modelo describa un motor real.

El rendimiento ideal se contrasta como fórmula analítica y como cociente, siempre en **puntos motores** previamente clasificados por `evaluar_punto`:

\[
\eta_{ideal}=1-r_p^{-a}=\frac{w_{neto}}{q_{in}},\qquad q_{in}>0.
\]

Las fronteras con aporte nulo y los puntos no motores quedan deliberadamente fuera de esta tarea; no se divide entre cero ni se inventa un rendimiento motor.

En el **máximo de trabajo específico** para `T1`, `T3` constantes se cumple:

\[
r_{p,*}=\left(\frac{T_3}{T_1}\right)^{1/(2a)},
\qquad T_{2,*}=T_{4,*}=\sqrt{T_1T_3}.
\]

El test comprueba ambas temperaturas en la solución analítica y también en los estados que devuelve una llamada **directa** a `buscar_maximo_numerico`. Este buscador explora un dominio interior y refina mediante sección áurea, sin consultar el candidato analítico para localizar el máximo. La igualdad de temperaturas es una propiedad adicional, distinta de volver a comprobar solamente `rp_*`.

## 3. PYTHON — cómo están organizadas las pruebas

La clase `VerificacionAnaliticaIdealTests(unittest.TestCase)` reúne cuatro métodos. Cada uno recibe sólo `self`, no devuelve resultados físicos (retorno implícito `None`) y `unittest` lo invoca automáticamente. Las cinco tuplas de `CASOS` contienen `(nombre, T1, T3, gamma, cp, rp, p1)` con unidades del apartado anterior y `p1` en kPa. Todos son moderados, representables y motores. El último método utiliza sólo los tres primeros para las búsquedas.

| Firma del método | Qué comprueba | Funciones existentes llamadas |
|---|---|---|
| `test_estados_con_referencias_isentropicas(self)` | T1–T4, T2s y T4s [K] contra potencias isentrópicas directas | `main.calcular_ciclo_ideal` |
| `test_balances_con_referencias_y_residuo(self)` | Cuatro energías [kJ/kg], `wn=wt-wc`, `wn=qin-qout`, residuo y comparación con calor de referencia | `main.calcular_ciclo_ideal` |
| `test_rendimiento_analitico_frente_a_balance_motor(self)` | Viabilidad, `qin>0`, rendimiento [fracción] como fórmula y cociente | `evaluar_punto`, `main.calcular_rendimiento` |
| `test_temperaturas_coinciden_en_maximo_ideal_analitico_y_numerico(self)` | T2=T4=raíz geométrica [K] en candidato y búsqueda numérica motor interior | `main.calcular_relacion_optima`, `main.calcular_temperaturas`, `calcular_dominios`, `buscar_maximo_numerico` |

**Errores y validación.** Los cinco casos se seleccionan en el dominio admisible; por ello las funciones no deberían lanzar `ValueError` o `ErrorNumerico` en su uso normal. Un resultado que supere una tolerancia produce una aserción fallida (`AssertionError`) con nombre de caso, magnitud, error y tolerancia. Otras excepciones de producción se propagan para que `unittest` las muestre como errores, no como resultados físicos.

### ¿Qué aporta `unittest.subTest()`?

```python
for nombre, T1, T3, gamma, cp, rp, p1 in self.CASOS:
    with self.subTest(caso=nombre):
        # Calcular referencia y resultado; comprobar tolerancias.
        ...
```

**PYTHON.** `for` desempaqueta cada tupla, y `with` abre un contexto que identifica el caso. Si falla una aserción, el informe señala, por ejemplo, `caso='gamma_133'`, y se siguen examinando los demás casos. No se crean cinco métodos distintos ni se cambia el modelo por usar `subTest`. La salida de `unittest` cuenta **cuatro métodos**, con **18 casos parametrizados** (5+5+5+3), no 18 métodos independientes.

## 4. Errores y tolerancias

- **Error absoluto:** `abs(calculado-referencia)`, con la unidad de la magnitud (K, kJ/kg o fracción).
- **Error relativo:** `error_absoluto/abs(referencia)`, adimensional y sólo definido para referencia distinta de cero. El test de energías lo calcula para diagnosticar fallos, pero no guarda un máximo relativo agregado.
- **Residuo de identidad física:** cuánto se aparta de cero una igualdad como `wn-(qin-qout)`. Se expresa en **kJ/kg** y se compara con la escala energética del caso, no con una tolerancia térmica.

Se exige:

\[
|x-x_{ref}|\leq \varepsilon_{abs}+\varepsilon_{rel}|x_{ref}|.
\]

| Magnitud | Tolerancia absoluta | Relativa |
|---|---:|---:|
| Temperatura | `1e-9 K` | `2e-12` |
| Energía / residuo | `1e-10 kJ/kg` | `2e-12` |
| Rendimiento | `2e-13` (fracción) | `2e-12` |

Para residuos, la parte relativa multiplica `max(abs(wc),abs(wt),abs(wn),abs(qin),abs(qout))` del caso. Son tolerancias para redondeos en doble precisión y magnitudes moderadas; **no representan errores de medición** ni tolerancias universales para fronteras o extremos.

En el máximo numérico, si `epsilon_rp=resolucion_rp/rp`, la sensibilidad local ideal es aproximadamente `|dT|/T≈a*|drp|/rp`. La comparación usa un margen en K proporcional a `a*sqrt(T1*T3)*epsilon_rp`, más la tolerancia térmica anterior, con factor conservador para comparar simultáneamente T2, T4 y su diferencia. La `resolucion_rp` del buscador es una **escala conservadora informada, no una cota formal demostrada**.

## 5. Comprobaciones realmente ejecutadas

Ejecutadas el **22 de octubre de 2026** en una copia local del commit base, con dependencias del proyecto instaladas **fuera del repositorio**:

```bash
PYTHONPATH=/tmp/brayton_task_1_1_pkgs MPLCONFIGDIR=/tmp/mpl_brayton_task_1_1 python -B -m unittest discover -s tests -p 'test_verificacion_analitica.py' -v
```

**Resultado:** cuatro métodos nuevos correctos, cero fallos, cero errores (`Ran 4 tests ... OK`). Cuatro métodos anteriores directamente relacionados también pasaron por separado:

- `OptimizacionTests.test_limite_reversible_recupera_optimo_ideal`
- `OptimizacionTests.test_busqueda_numerica_no_utiliza_candidato_analitico`
- `ViabilidadTests.test_limites_ideales_y_optimo_distintos`
- `InformesTests.test_referencia_fisica`

El total focalizado es **8 métodos superados**, sin ejecutar de nuevo la suite completa. El último cierre integral histórico anotado en §4.44 del manual fue **178/178** (anterior a las seis pruebas de guías contextuales y a esta tarea); no debe atribuirse a esta ejecución.

Con cinco casos motores, máximos errores absolutos observados en un cálculo adicional:

| Comprobación | Máximo observado |
|---|---:|
| Temperaturas contra referencia | `1.1368683772161603e-13 K` |
| Energías contra referencia | `1.1368683772161603e-13 kJ/kg` |
| Rendimiento contra fórmula | `1.1102230246251565e-16` |
| Residuo de primera ley | `1.1368683772161603e-13 kJ/kg` |

**No se registró un máximo agregado de errores relativos**; no se atribuye uno al experimento.

Caso base (`T1=288.15 K`, `T3=1600 K`, `gamma=1.4`, `cp=1005 J/(kg·K)`, `rp=10`): `T2≈556.330550578 K`, `T4≈828.715948677 K`, `wn≈505.619018249 kJ/kg`, `eta≈0.482052532`. En su óptimo **numérico**: `rp≈20.085256021667`, `sqrt(T1*T3)≈678.999263623 K` y `|T2−T4|≈5.22445e-6 K`. La diferencia térmica del óptimo es mayor que el redondeo de un cálculo directo, como corresponde a la resolución de la búsqueda.

## 6. Limitaciones, próximos pasos y trazabilidad

1. Se han contrastado cinco casos interiores moderados, no todos los valores admisibles. No se han estudiado condicionamiento, límites de representación, puntos degenerados ni fronteras abiertas.
2. En esta **Tarea 1.1** aún no se había comparado ningún algoritmo con SciPy; esa comparación se añade posteriormente en la Tarea 1.3 (§8). Los estudios sistemáticos de mallas y convergencia siguen pendientes.
3. No hay datos experimentales ni comparación con una correlación de un motor real: esto es **verificación de software** y de consistencia bajo el modelo de gas ideal con propiedades constantes, **no validación física**.
4. No se modifica `qout` como salida pública ni se añaden funciones de producción para los tests.
5. Esta tarea no crea un milestone **técnico de cierre** de la Fase 1 completa. El documento se ampliará en futuras tareas de esta fase, sin presentar como realizados sus resultados pendientes.

**Archivos de la Tarea 1.1:** `tests/test_verificacion_analitica.py`, `CODE_WALKTHROUGH.md` (§4.45, estructura y conceptos de pruebas) y este documento. Los archivos de las fases anteriores permanecen en su contexto histórico. La publicación de 1.1 corresponde al commit `275e755`. La Tarea 1.2 se preparó inicialmente sin commit y fue **publicada después** en `143d10f`.

### Experimentos de aprendizaje sugeridos (no ejecutados)

- Cambia una sola entrada de `CASOS` en una copia y calcula a mano T2, T4, wc y wt antes de ejecutar el método.
- Introduce deliberadamente una referencia incorrecta y observa cómo `subTest` identifica el caso sin detener los demás.
- Compara la magnitud de un residuo en kJ/kg con la escala del trabajo: no confundas un residuo diminuto con un error de modelo despreciable para cualquier motor real.

## 7. Iteración del 22 de octubre de 2026 — Tarea 1.2

### Estado, objetivo y referencia matemática

**Estado de partida verificado:** rama remota `mejoras/verificacion-numerica`, commit `275e7558b7d05322054f89ecd672ed5563c59469`, copia de trabajo limpia antes de editar. El simulador ya construía fronteras de compresión, expansión, calor y trabajo, y `test_viabilidad.py` comprobaba cambios de signo, vecindades de la raíz y clasificación. Faltaba una comparación sistemática de **ambas raíces calculadas por bisección** con su posición exacta según la ecuación cuadrática. Esta tarea sólo añade `tests/test_verificacion_raices.py` y actualiza estas explicaciones; las ecuaciones y las funciones de producción no cambian.

Con `a=(gamma−1)/gamma>0`, `x=rp**a`, `theta=T3/T1`, `h=theta*eta_c*eta_t`, `k=(1−delta)**(−a)`, la condición de trabajo motor es:

\[
Q(x)=x^2-(1+h)x+hk<0,\qquad D=(h-1)^2-4h(k-1).
\]

Si `D>0`, las raíces matemáticas independientes son `x_±=((1+h)±sqrt(D))/2` y `rp_±=x_±**(1/a)`. El test las calcula con operaciones aritméticas y `math.sqrt` **sin llamar a `bisectar_raiz()` ni a `calcular_dominios()` para determinar las referencias**. Después consulta `calcular_dominios()` para compararlas. Es independencia **de implementación**, no un modelo físico independiente.

**INTERPRETACIÓN FÍSICA.** El signo de Q se obtiene multiplicando el trabajo específico neto por un factor positivo; por eso `Q<0` equivale a trabajo positivo. Deben cumplirse simultáneamente las cuatro condiciones:

1. Compresión: `rp>1`.
2. Expansión: `rp>1/(1−delta)`.
3. Calor aportado positivo: `x<1+eta_c*(theta−1)`.
4. Trabajo neto positivo: `Q(x)<0`.

El intervalo motor es su **intersección abierta**, que puede ser vacía. Las raíces de Q por sí solas no certifican un motor. El ensayo utiliza un punto central y puntos a distancia relativa `1e−5` en los dos lados de cada frontera: esto supera la banda `1e−10` de clasificación en `evaluar_punto`. En la frontera exacta se excluye el estado porque la condición es estricta y la pequeña banda numérica lo clasifica como no motor; **la banda no es parte de la ecuación física**.

### PYTHON y algoritmo de bisección

La clase `VerificacionRaicesTests(unittest.TestCase)` declara cuatro casos no ideales moderados en tuplas y cinco métodos con firma `metodo(self)` y retorno implícito `None`. Sus entradas físicas son T1/T3 [K], gamma/eficiencias/delta [adimensional], cp [J/(kg·K)] y p1 [kPa]. Cada método llama a `calcular_dominios` y, cuando comprueba clasificación, a `evaluar_punto`. `for` recorre los parámetros; `zip` empareja raíces y resultados; `with self.subTest(caso=..., raiz=... o punto=...)` identifica un fallo concreto, sin interrumpir el resto. Una aserción falsa produce `AssertionError`; parámetros inesperadamente inválidos podrían propagar `ValueError` o `ErrorNumerico`. Ejemplo de ejecución:

```bash
python -B -m unittest discover -s tests -p 'test_verificacion_raices.py' -v
```

La **bisección** parte de un intervalo donde una función continua toma signos contrarios y, en cada iteración, elige la mitad que mantiene el cambio de signo. Por el teorema del valor intermedio, esa mitad conserva alguna raíz; el ancho disminuye geométricamente (`ancho_inicial/2**n`). `bisectar_raiz()` detiene la búsqueda cuando el ancho es suficientemente pequeño respecto a `max(abs(x_medio),1)` (tolerancia relativa `1e−12`) o encuentra un cero exacto. Esa condición es un criterio de parada en **x**, no una garantía universal sobre `rp` o sobre toda raíz mal condicionada.

La comparación evalúa tres clases de error diferentes:

| Medida | Definición | Unidad |
|---|---|---|
| Error absoluto de raíz | `abs(x_num−x_ref)` o `abs(rp_num−rp_ref)` | adimensional |
| Error relativo de raíz | error absoluto dividido por `abs(referencia)` no nula | adimensional |
| Residuo de función | `abs(Q(x_num))` | adimensional (escala de términos de Q) |

El residuo mide cuán cerca está `Q(x_num)` de cero, **no directamente la distancia hasta la raíz**; cuando `Q'(x)` es pequeño, una posición imprecisa puede dar un residuo pequeño. Además, `rp=x**(1/a)` amplifica en primer orden el error relativo aproximadamente `1/a` veces. Por eso los umbrales de posición se separan por variable: en x, `atol=2e−12` y `rtol=2e−12`; en rp, `atol=1e−9` y `rtol=2e−11`. Para el residuo se exige `abs(Q)≤2e−11*max(1,x²,abs((1+h)x),hk)`. Son tolerancias conservadoras para doble precisión y raíces simples moderadas; no se aplica un único umbral indiscriminado.

### Casos especiales y pruebas realmente ejecutadas

Las cinco comprobaciones nuevas son: (1) raíces analíticas y residuos para cuatro combinaciones no ideales (ocho raíces); (2) intersección de restricciones, punto interior, vecindades exteriores e interiores y exclusión de las fronteras; (3) límite reversible con `Q=(x−1)(x−theta)`, fronteras `rp=1` y `rp=theta**(1/a)`; (4) `D<0` y raíz doble exacta `D=0` con `theta=2`, `eta_c=.5`, `eta_t=1`, `delta=0`, de modo que `Q=(x−1)²`; (5) `D=.25>0` con `h=.5,k=1`, raíces `x=.5` y `x=1`, pero toda la región de `Q<0` exige `rp<1`, incompatible con compresión. No se han confundido estos tres últimos fenómenos con límites de representación numérica.

**Ejecución real, 22/10/2026.** Los cinco métodos nuevos pasaron (`5/5`); también siete métodos de `ViabilidadTests` directamente relacionados (raíces y vecindades, calor, expansión, reversible, dominios vacíos, clasificación combinada y errores de bisección), `7/7`. **Total focalizado: 12/12; cero fallos y cero errores**. No se ejecutó de nuevo la suite general ni se modificó un módulo físico.

| Máximo observado entre 8 raíces no ideales | Valor | Caso y raíz |
|---|---:|---|
| Error absoluto en x | `9.1304741545e−13` | entrada_fria, superior |
| Error relativo en x | `3.7747594652e−13` | entrada_fria, inferior |
| Error absoluto en rp | `1.1246470422e−10` | entrada_fria, superior |
| Error relativo en rp | `1.4261261054e−12` | entrada_fria, inferior |
| Mayor `abs(Q(x_num))` | `2.2444268666e−12` | entrada_fria, superior |

Estos números se obtuvieron además con un cálculo diagnóstico separado, sobre los mismos cuatro casos, y **no** son límites universales del método. La verificación sólo confirma la implementación y la interpretación de su **modelo termodinámico simplificado**; validar físicamente un motor requeriría datos o referencias externas. Continúan pendientes el condicionamiento junto a raíces casi dobles, límites de representación y estudios de convergencia. Las comparaciones con SciPy se añadieron posteriormente (§8). La Tarea 1.2 se ejecutó primero sin commit y **fue publicada después** en la rama de desarrollo, commit `143d10f`.

## 8. Iteración del 22 de octubre de 2026 — Tarea 1.3: comparación opcional con SciPy

### Qué había antes y qué se contrasta

**Punto de partida:** rama `mejoras/verificacion-numerica`, commit remoto exacto `143d10fd25ebd23ddb897722b7843bddabfd16a5`. Las Tareas 1.1 y 1.2 ya verificaban identidades físicas, raíces cuadráticas y fronteras abiertas mediante ecuaciones directas. Todavía no se habían contrastado los **algoritmos propios** de raíces y máximos con implementaciones numéricas distintas.

Se añade `tests/test_comparacion_scipy.py` y se documenta en [§4.47 del manual](../../CODE_WALKTHROUGH.md). No se modifica ninguna función física ni de optimización; no se añade SciPy a `requirements.txt`. La comparación usa SciPy únicamente si está instalado. Si no, seis pruebas quedan marcadas como **omitidas** con `unittest.skipIf`; otras dos siguen ejecutándose sin SciPy.

### INGENIERÍA Y MATEMÁTICAS — tres métodos para encontrar raíces

Se comparan `bisectar_raiz` propio, `scipy.optimize.bisect` y `scipy.optimize.brentq` aplicados al **mismo intervalo con cambio de signo** y a la misma función:

- `f(x)=x²−2` en `[1,2]`: referencia matemática independiente `sqrt(2)`.
- `Q(x)=(x−1)(x−h)+h(k−1)` de tres ciclos no ideales, en dos intervalos que encierran respectivamente cada raíz. La fórmula cuadrática directa proporciona las referencias, como en la Tarea 1.2.

La **bisección** divide repetidamente el intervalo que contiene el cambio de signo; es robusta por continuidad, pero reduce el ancho a un ritmo fijo. **Brent** también mantiene un intervalo válido y combina pasos seguros con interpolación para acelerar cuando es conveniente. No se utiliza ninguno si los extremos tienen el mismo signo: los tres rechazan `f(x)=x²+1` en `[1,2]` con `ValueError`.

La variable termodinámica es `x=rp**a`, donde `a=(gamma−1)/gamma`. La posición buscada es `rp=x**(1/a)`: una pequeña desviación relativa de x puede aumentar en rp aproximadamente por el factor `1/a`. Por ello se registran **errores absolutos y relativos en ambas variables** y, por separado, el **residuo** `|Q(x)|`. Un residuo pequeño no garantiza una raíz bien localizada si la pendiente cerca de ella es pequeña.

### INGENIERÍA Y PYTHON — máximos de trabajo y rendimiento

Se compara cada buscador propio de malla logarítmica y **sección áurea** con `scipy.optimize.minimize_scalar(method="bounded")`. Dado que `minimize_scalar` busca un *mínimo*, el callback devuelve `-trabajo_neto` [kJ/kg] o `-rendimiento` [fracción]: minimizar `-W` equivale a maximizar `W`, y análogamente para eta.

Ambos algoritmos buscan en `y=log(rp)`, con `rp=exp(y)`. Así el intervalo representa **razones multiplicativas** de presión y evita comparar una búsqueda en escala lineal con otra logarítmica. Se recorta sólo para la búsqueda una fracción `1e−6` en cada extremo del intervalo logarítmico abierto; **las fronteras físicas no cambian**. Se prueban cuatro máximos interiores de trabajo (uno ideal y tres no ideales) y tres máximos interiores de rendimiento **no ideal**.

Para aceptar un máximo de SciPy se exige, además de `result.success` y números finitos, estar dentro del dominio, superar `evaluar_punto(...)["viable"]` y presentar valores menores del objetivo en dos puntos interiores a ambos lados. Este último control es una evidencia local de máximo, **no una demostración global para funciones arbitrarias**. El rendimiento ideal constituye un contraejemplo deliberado: crece hacia una frontera de aporte nulo y sólo tiene **supremo no alcanzado**. SciPy puede informar éxito junto a la frontera; el filtro descarta correctamente la etiqueta de máximo motor interior. Cuando no existe dominio motor, la búsqueda propia informa ausencia de solución en vez de atribuirla a fallo de convergencia.

**PYTHON.** `for` y `unittest.subTest()` reutilizan combinaciones de parámetros sin crear docenas de métodos. Una función interna `contado(x)` utiliza un cierre sobre una lista `[0]` para contar cada evaluación; en SciPy se coteja con `function_calls` (raíces) o `nfev` (máximos). `types.SimpleNamespace` fabrica cuatro resultados falsos (`success=False`, frontera, NaN, punto sin máximo) para verificar el filtro sin necesitar provocar fallos reales inestables. Las firmas y retornos de los dos auxiliares, junto a los ocho tests, están descritos en el manual §4.47.

### Tolerancias, precisión y resultados observados

Se fijan explícitamente `xtol=rtol=1e−12` en `bisect`/`brentq`; el método propio usa `tolerancia=1e−12`, que detiene por **anchura relativa del intervalo en x**. No son criterios matemáticamente idénticos. Para las referencias analíticas se comprueba:

| Magnitud | Límite de error/residuo |
|---|---|
| Raíz x, adimensional | `|Δx|≤2e−12+3e−12|x_ref|` |
| Raíz rp, adimensional | `|Δrp|≤1e−9+2e−11|rp_ref|` |
| Residuo de Q, adimensional | `|Q(x)|≤2e−11·max(1,x²,|(1+h)x|,hk)` |
| Posición rp del máximo, adimensional | `|Δrp|≤1e−6+2e−6·max(rp_propio,rp_SciPy)` |
| Trabajo máximo, kJ/kg | `|ΔW|≤1e−8+1e−10·max(|W_propio|,|W_SciPy|,cp*T3/1000)` |
| Rendimiento máximo, fracción | `|Δeta|≤1e−10+1e−10·|eta_SciPy|` |

En máximos se fija `xatol=1e−9` en `y=log(rp)` para SciPy y `tolerancia_log=1e−9` para el buscador propio. Cerca de un máximo plano, los valores de W o eta varían **cuadráticamente** con la desviación de posición; por tanto, pueden coincidir casi a precisión de máquina mientras rp difiere en varias millonésimas. Las tolerancias permiten esa geometría, sin ser márgenes experimentales. `resolucion_rp` informa una escala de precisión interna, no una cota formal del error frente a SciPy.

**Ejecución real (22/10/2026, SciPy 1.17.0):** ocho métodos nuevos superados, ninguno fallido u omitido; ocho pruebas preexistentes de raíces/optimización también superadas. **Total focalizado: 16/16.** En un ensayo separado que simula ausencia de SciPy, se ejecutaron **2 métodos correctos y 6 omitidos**. No se ejecutó la suite completa.

| Comparación | Mayor error absoluto observado | Mayor error relativo observado |
|---|---:|---:|
| Raíces Q, posición x frente a fórmula cuadrática (3 métodos) | `3.3155700e−12` | `1.1178260e−12` |
| Raíces Q, posición rp frente a fórmula cuadrática (3 métodos) | `4.2663828e−10` | `4.5051234e−12` |
| Máximo trabajo, posición rp propia frente a SciPy | `7.2124703e−7` | `5.9060284e−8` |
| Máximo trabajo, W propio frente a SciPy [kJ/kg] | `2.2737368e−13` | `4.8875800e−16` |
| Máximo rendimiento no ideal, posición rp | `1.7468397e−6` | `6.9062480e−8` |
| Máximo rendimiento no ideal, eta [fracción] | `3.3306691e−16` | `8.5944239e−16` |

El mayor residuo en las seis raíces de Q y tres métodos fue `|Q(x)|=1.0637699e−11` (SciPy `bisect`, raíz superior del caso de referencia). La mayor diferencia **entre bisección propia y SciPy bisect**, sin fórmula intermedia, fue `3.5766945e−12` en x y `4.6023274e−10` en rp; frente a `brentq` fue `1.6404655e−12` en x y `2.0206414e−10` en rp.

Para el ejemplo `x²−2=0`, con referencia `sqrt(2)≈1.4142135623730951`, los errores absolutos fueron `2.1605e−13` (propia, 43 llamadas), `1.5803e−12` (`bisect`, 41 llamadas) y `4.1300e−14` (`brentq`, 8 llamadas). Sólo describen ese caso, no la rapidez garantizada de cada algoritmo.

| Ejemplo no ideal de referencia | Método propio | SciPy bounded | Evaluaciones propia / SciPy |
|---|---:|---:|---:|
| rp para máximo trabajo | `12.89505173504` | `12.89505166962` | 297 / 6 |
| Trabajo máximo [kJ/kg] | `373.2108274827` | `373.2108274827` | — |
| rp para máximo rendimiento | `35.45232192220` | `35.45232299066` | 297 / 11 |
| Rendimiento máximo [fracción] | `0.4389310716313` | `0.4389310716313` | — |

Los contadores de raíces variaron de **43 a 45** evaluaciones propias, **41 a 43** en `bisect` y **10 a 11** en `brentq` para estos seis intervalos; los ejemplos de máximos propios usaron 297 evaluaciones (malla y refinamiento) frente a **6–24** de SciPy para trabajo y **11–14** para rendimiento. Se cuentan funciones **en estrategias distintas**: no se concluye superioridad universal de velocidad ni se exigen iteraciones exactas en los tests.

**Caso límite observado:** SciPy devuelve `success=True` y `rp≈403.4151` para el rendimiento ideal. `evaluar_punto` aún considera motor ese punto interior, pero su rendimiento sigue aumentando al acercarse a la frontera: **no es un máximo interior**, y el filtro lo rechaza. El buscador propio conserva `estado="supremo_no_alcanzado"`.

### Qué hemos aprendido y qué queda pendiente

Los resultados son consistentes en estos ejemplos **moderados y con máximos interiores resolubles**. No se ha detectado una discrepancia que justifique alterar por ahora los algoritmos propios. La diferencia de evaluaciones sugiere estudiar su coste en futuras tareas, pero **sin benchmarks exhaustivos aquí**. En casos cercanos a raíces dobles, fronteras abiertas o máximos muy planos podría ser necesario estudiar precisión y criterios de aceptación con mayor cuidado.

Esta es **verificación cruzada de implementaciones que comparten el mismo modelo**; no valida los supuestos termodinámicos frente a datos experimentales. Siguen pendientes los estudios sistemáticos de tolerancia, malla, convergencia, condicionamiento y límites numéricos, así como la validación física externa. La Tarea 1.3 permanece **sin commit ni publicación**, a la espera de revisión; no se ha modificado `main`.
