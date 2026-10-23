# Fase 2B — Aprendizaje: resolver Brayton con cp(T)

**Preparación:** 23 de octubre de 2026. Rama activa `mejoras/cp-variable`; base remota y árbol de la copia independiente verificados contra `d5f818aa7f5a2880e414211950f8396830222308`. Las modificaciones de esta fase se preparan sobre esa base. El repositorio de conservación con gas caloríficamente perfecto y el ordenador Windows permanecen fuera del trabajo.

## 1. De dónde venimos y qué problema resuelve esta fase

En **2A** preparamos propiedades de un gas ideal **térmicamente imperfecto**: `cp(T)`, `h(T)` y `s0(T)` para aire fijo N₂/O₂/Ar entre 200 y 2000 K. El simulador anterior obtiene temperaturas isentrópicas con un exponente constante `a=(gamma−1)/gamma` y trabajos como `cp·DeltaT`. Ese razonamiento supone **cp constante**: a 1600 K nuestro `cp(T)` ya es sensiblemente mayor que a 300 K.

En **2B** añadimos un segundo camino, explícitamente independiente de `main.py` y `viabilidad.py`. El usuario llama `resolver_ciclo(...)` directamente desde Python. No hay nuevos botones, ni resultados HTML, ni nuevos optimizadores. Los resultados del simulador anterior permanecen reproducibles.

## 2. La física: de potencias de temperatura a integrales

### Entropía de gas ideal con cp variable

Una transformación isentrópica ideal obedece:

\[
\Delta s = \int_{T_a}^{T_b}\frac{c_p(T)}{T}\,dT - R\ln\frac{p_b}{p_a} =0.
\]

En nuestro código, `s0(T)` ya contiene la integral respecto a `Tref`; los términos de referencia se cancelan al restar. Como `R_AIRE` está en **J/(kg·K)**, se divide entre mil cuando el resultado se expresa en **kJ/(kg·K)**:

```python
R_kJ = R_AIRE / 1000.0
T2s = _temperatura_desde_s0(s0(T1) + R_kJ * log(rp))
T4s = _temperatura_desde_s0(s0(T3) + R_kJ * (log(p4) - log(p3)))
```

La entropía térmica `s0` crece porque `ds0/dT=cp(T)/(1000*T)>0`; por ello la ecuación tiene **como máximo una raíz** en 200–2000 K. Sólo existe **dentro de nuestro modelo** si el objetivo está entre `s0(200)` y `s0(2000)`. Cuando la raíz real exigiría otro intervalo, se devuelve `EstadoFueraDeRango`: truncar T a 200 o 2000 falsearía el balance.

### Trabajos, eficiencias y balances

Para compresor y turbina adiabáticos, despreciando cambios cinéticos y de altura:

```text
h2−h1 = [h(T2s)−h1]/eta_c
h3−h4 = eta_t·[h3−h(T4s)]
wc=h2−h1                   (positivo para compresión)
wt=h3−h4                   (positivo para expansión)
wn=wt−wc
qin=h3−h2                  (aporte externo de calor al aire)
qout=h4−h1                 (calor rechazado)
eta=wn/qin                 (únicamente para motor viable)
```

Estas cantidades están en **kJ/kg**, porque `propiedades_aire.h` ya trabaja en kJ/kg. No se introduce una segunda conversión por mil. Una eficiencia de compresor menor que 1 aumenta el salto real de entalpía requerido; una eficiencia de turbina menor que 1 reduce el salto extraído. No son cocientes de diferencias de temperaturas salvo en el modelo antiguo de cp constante.

La entalpía base `h(298.15)=0` no perjudica los resultados: todas las ecuaciones usan **diferencias**. Una presión absoluta diferente, manteniendo el mismo `rp` y `delta`, no cambia las temperaturas de esta mezcla ideal; sí cambia cada `s(T,p)` por un término logarítmico, que desaparece en los saltos pertinentes.

### Primera y segunda ley

El solucionador presenta el residuo:

```text
r1 = (wt−wc) − [(h3−h2)−(h4−h1)]
```

Su valor debe ser cercano a cero. ¡Ojo!: la identidad es en gran medida **algebraica** porque las energías proceden de las mismas cuatro entalpías; por eso también verificamos integrales numéricas **independientes** de cp(T) en las pruebas. Un residuo pequeño **no** equivale a una medida de rendimiento real.

En los equipos adiabáticos:

```text
sg,c = s(T2,p2)−s(T1,p1)
sg,t = s(T4,p4)−s(T3,p3)
```

Para compresor/turbina funcionando en su sentido nominal, ambas deben ser no negativas. Con eficiencias unitarias se aproximan a cero, también cuando la cámara pierde presión; esa pérdida no se atribuye indebidamente a ninguno de los dos equipos. No se ha calculado la generación de entropía propia del aporte de calor ni la del sistema completo.

## 3. Qué significa «viable» y por qué no es una excepción

Un programa científico debe separar cuatro estados de ejecución:

1. **Entrada incorrecta:** `rp=0`, `eta_c=1.2`, `T1=NaN` o `T1=199 K` → `ValueError`.
2. **Modelo sin rango suficiente:** las entradas son admisibles, pero una raíz isentrópica o real queda fuera de 200–2000 K → `EstadoFueraDeRango(ValueError)`.
3. **Problema numérico:** por ejemplo `p1·rp` se desborda a infinito o subdesborda a cero → `ErrorNumericoCiclo(ArithmeticError)`.
4. **Ciclo calculable, pero no motor:** `rp=1`, falta de expansión, `qin<=0` o `wn<=0` → `dict` con `viable=False`, `motivos`, `rendimiento=None`; no se esconde el signo real.

También se revisa generación de entropía negativa significativa. Si se intenta usar la **definición de eficiencia de turbina** con una relación de presiones que exige comprimir en vez de expandir, puede resultar una entropía generada negativa: eso señala que la ley de eficiencia **está fuera de su régimen físico**. El cálculo algebraico se conserva para diagnosticar, pero el punto no se declara motor. La banda numérica `tolerancia=1e-10` afecta a compresión, expansión y balances; para pequeñas diferencias de entropía se impone un umbral mínimo de `1e-11 kJ/(kg·K)` para no atribuir significado físico al redondeo.

## 4. Aprendizaje de Python: funciones, contratos y errores

El archivo `ciclo_cp_variable.py` contiene dos clases de excepción y cinco funciones. **No cambia** las firmas del proyecto histórico. Todas las funciones privadas se marcan con guion bajo inicial porque su contrato está pensado para ser utilizado **desde** la API pública, no directamente por Flask.

| Función exacta | Parámetros, salida y unidades | Cómo funciona, quién la llama y qué errores produce |
|---|---|---|
| `_numero_finito(valor)` | Objeto arbitrario → `bool` | Usa `numbers.Real` y `math.isfinite` y excluye expresamente `bool`. Rechaza `NaN`, infinito, texto, complejos y enteros inmensos con posible `OverflowError`. La llama `_validar_entradas`. `True` → `False`. |
| `_validar_entradas(T1, T3, rp, p1, eta_c, eta_t, delta, tolerancia)` | K, K, –, kPa, –, –, –, – → `None` | Llama a `_numero_finito`; garantiza temperaturas en `[200,2000]`, presiones/relación positivas, eficiencias `(0,1]`, pérdida `[0,1)` y tolerancia `[0,1)`. La llama `resolver_ciclo`; falla con `ValueError`. Ej.: `_validar_entradas(288.15,1600,10,100,.85,.9,.05,1e-10)`. |
| `_temperatura_desde_s0(objetivo)` | Diferencia de entropía térmica relativa `float` kJ/(kg·K) → `float` K | Invocada dos veces por `resolver_ciclo`. Usa `s0` y bisección hasta anchura `1e-10 K`, máximo 80 pasos; `EstadoFueraDeRango` cuando la meta queda fuera del dominio y `ErrorNumericoCiclo` si no converge. `_temperatura_desde_s0(s0(700))≈700`. |
| `_temperatura_desde_h_acotada(entalpia)` | h relativa `float` kJ/kg → `float` K | Reutiliza `T_desde_h` de la Fase 2A, acotando su dominio y separando `EstadoFueraDeRango`. Invocada para T2 y T4. Ej.: `_temperatura_desde_h_acotada(h(1000))≈1000`. |
| `resolver_ciclo(T1, T3, rp, p1, eta_c=1.0, eta_t=1.0, delta=0.0, tolerancia=1e-10)` | K, K, –, kPa, –, –, –, – → diccionario | **Punto de entrada independiente** de Fase 2B; invoca los cuatro auxiliares y funciones de `propiedades_aire`. Devuelve cuatro estados, referencias 2s/4s, entalpías, entropías, trabajos, calores, residuos, motivos y límites de verificación; su `rendimiento` es fracción o `None`. Puede elevar las tres categorías de error explicadas arriba. |

### Bisección y reutilización

La idea de `_temperatura_desde_s0` es análoga a la inversión de entalpía que aprendimos en 2A:

```python
inferior, superior = T_MIN, T_MAX
medio = (inferior + superior) / 2.0
if s0(medio) < objetivo:
    inferior = medio
else:
    superior = medio
```

La decisión `if` funciona porque `s0` es monótona. Antes se verifica si el objetivo está dentro de `[s0(T_MIN), s0(T_MAX)]`. No se usa `viabilidad.bisectar_raiz`: importarla acoplaría este módulo a la antigua dependencia NumPy y a ecuaciones del modelo anterior, mientras que aquí conocemos una función estrictamente creciente y un intervalo físico fijo. No se ha instalado SciPy.

En cambio, **sí** se reutiliza `T_desde_h`: duplicar su inversor sería innecesario. Para transparencia, después de recuperarse T2 y T4 se recalculan `h(T2)` y `h(T4)`; así una diferencia numérica no queda ocultada sustituyendo el resultado por la meta inicial.

### Diccionarios, tuplas y comprensión de motivos

La función devuelve, entre otras, estas claves:

```python
{
    "temperaturas": (T1, T2, T3, T4),  # tupla, K
    "presiones": (p1, p2, p3, p4),      # tupla, kPa
    "entalpias": (h1, h2, h3, h4),      # tupla, kJ/kg
    "entropias": (s1, s2, s3, s4),      # tupla, kJ/(kg K)
    "viable": viable,                  # bool
    "motivos": motivos,                # tupla de textos
    "rendimiento": wnet/qin if viable else None,
}
```

Una **tupla** mantiene el orden físico de los cuatro estados; un **diccionario** da nombres estables a los campos para futuras tareas. El código usa `tuple(clave for clave, margen in margenes.items() if ...)`: recorre un diccionario, evalúa cada condición y conserva *todos* los motivos, no sólo el primero. Para informar una causa de Segunda Ley se compara contra un umbral negativo, no contra el mismo cero positivo de los márgenes motores. Este `dict` no se envía todavía a ninguna plantilla web.

## 5. Experimento reproducible y resultados

Ejecuta desde la raíz del proyecto:

```python
from ciclo_cp_variable import resolver_ciclo

p = resolver_ciclo(288.15, 1600., 10., 100., .85, .9, .05)
print(p["temperaturas"])
print(p["trabajo_compresor"], p["trabajo_turbina"])
print(p["trabajo_neto"], p["rendimiento"] * 100)
print(p["generacion_entropia_compresor"], p["generacion_entropia_turbina"])
```

Se obtiene, aproximadamente:

| Magnitud | Fase 2B, cp(T) | Modelo anterior, cp y γ constantes |
|---|---:|---:|
| T2 | 597.692837 K | 603.656530 K |
| T4 | 993.581041 K | 916.855359 K |
| Trabajo compresor | 316.235549 kJ/kg | depende de cp constante |
| Trabajo turbina | 718.306347 kJ/kg | depende de cp constante |
| Trabajo neto | 402.070798 kJ/kg | 369.476301 kJ/kg |
| Rendimiento | 34.893428 % | 36.898732 % |

Para cp(T), `T2s≈552.284478 K`, `T4s≈923.078435 K`, `qin≈1152.282306 kJ/kg`, `qout≈750.211508 kJ/kg`. La producción de entropía en compresor/turbina es respectivamente `0.082535347` y `0.083313524 kJ/(kg·K)`; los residuos de referencia isentrópica son menores de `1e−10 kJ/(kg·K)` en las pruebas.

**¿Por qué cambia el resultado?** La temperatura de salida de turbina con cp(T) es más alta porque su caída de entalpía no se traduce linealmente en una diferencia de temperaturas con un cp fijo. No debemos interpretar que los valores sean *más fieles* a un motor concreto sin compararlos con datos/propiedades de trabajo adecuadas.

## 6. Verificación independiente y casos límite

`tests/test_ciclo_cp_variable.py` construye `_integral_cp(a,b, sobre_T=False, divisiones=5000)` y `_raiz_referencia_sin_s0(T_entrada,cambio_presion)` **sólo en el test**. Integran cp(T) con regla del punto medio y hallan una segunda raíz por bisección, sin usar `s0`, `h` ni los inversores productivos para producir esas referencias. Sus entradas/salidas son `a,b` en K, indicador `sobre_T` booleano y número de divisiones entero; devuelve kJ/kg para cp o kJ/(kg·K) para cp/T. La función de raíz recibe T en K y relación de presiones adimensional y devuelve K. Ambas son auxiliares docentes de contraste, no API productiva.

Otros tests verifican primera ley, eficiencias de entalpía, diferencia frente a cocientes de temperatura, límite reversible con/sin delta, presión absoluta, generación de entropía adiabática, frontera abierta de trabajo neto, ausencia de calor aportado, tipos (incluidos `True`, `NaN` y números enormes), 200–2000 K y errores de representación. El test de frontera localiza independientemente un cero de trabajo neto y comprueba los dos lados, sin añadir un optimizador de Fase 2B al código productivo.

**Resultados verificados el 23/10/2026:** 21/21 nuevos tests correctos, 17/17 tests de propiedades de Fase 2A correctos, y regresión directa de 2/2 puntos ideales/no ideales constantes reproduciendo el trabajo conocido. Se intentó una sola ejecución de la suite histórica: **110 pruebas contabilizadas, 19 errores de importación** originados por falta de `jinja2` (e indirectamente Flask) en este intérprete. No se reportaron fallos de aserción en pruebas que alcanzaron ejecución; **la suite completa no ha pasado**. No se instalaron bibliotecas. Los resultados numéricos no son validación experimental, ni verificación de combustión real.

## 7. Límites y siguientes decisiones pendientes

- El intervalo de validez es cerrado `[200,2000] K` para **cualquier estado**, también 2s y 4s. No se obliga a todas las combinaciones físicamente interesantes a caber en él.
- La composición N₂/O₂/Ar **no cambia** al aportar calor; no se simula combustible, productos, pérdidas mecánicas, humedad ni disociación.
- Las eficiencias dadas son parámetros impuestos, no mapas de máquinas. Las relaciones de presión invertidas pueden producir resultados sólo algebraicos y se etiquetan no motores.
- No hay exergía global, pérdidas de calor de la cámara ni inferencias sobre su generación de entropía.
- Los tests usan correlaciones y cálculos matemáticos; falta validación con medidas independientes de funcionamiento de motores.
- La siguiente fase requerirá decidir cómo aislar e integrar el nuevo modelo con informes, optimizaciones, sensibilidad, mapa, Segunda Ley y diagnóstico. **No se ha implementado esa fase.**

**Estado de Git:** desarrollo independiente en `mejoras/cp-variable`, base remota verificada `d5f818aa7f5a2880e414211950f8396830222308`. El commit 2B es *pendiente* mientras se preparan las verificaciones y publicación autorizadas; no se anticipa su hash.
