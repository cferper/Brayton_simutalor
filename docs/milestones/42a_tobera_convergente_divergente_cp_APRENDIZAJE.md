# Aprendizaje — Milestone 42.A: tobera convergente-divergente ideal

**Fecha de trabajo:** 25-10-2026. **Rama:** `mejoras/cp-variable`. **Base comprobada:** `7a8ce0c87247a9cb1b52a855b68e2167397b6713`, sin cambios previos al milestone. **Estado:** revisión final superada; publicación autorizada, asociación del commit pendiente de crear.

## 1. Estado previo y objetivo

Ya existía la tobera convergente del milestone 35 y la integración del motor del 41. Una convergente ideal acelera hasta **Mach 1 en su sección menor**; no dispone de sección divergente posterior para acelerar más un gas **supersónico** isentrópico. Este avance añade un solucionador **separado**, `tobera_convergente_divergente_cp.py`, con geometría en forma de relación de áreas. No introduce combustible, gasto absoluto, un motor nuevo ni interfaz web.

## 2. INTERPRETACIÓN FÍSICA / INGENIERÍA

### Energía, entropía, velocidades y unidades

Las condiciones de remanso `Tt,pt` representan el estado hipotético obtenido al detener reversiblemente la corriente; `T,p` son las propiedades **estáticas** del flujo en movimiento. La energía del fluido conserva `h(Tt)=h(T)+V²/2000` (h en kJ/kg, V en m/s). El factor 2000 incluye `1000 J/kJ` y el `1/2` cinético. En flujo isentrópico, `s(T,p)=s(Tt,pt)`; no se sustituyen estas igualdades por exponentes exactos de gamma constante.

En la garganta de **área mínima** un flujo bloqueado cumple `Vg=ag`, `Mg=1`; `ag=sqrt(gamma(Tg)*R*Tg)` [m/s]. El bloqueo limita el caudal **por área** `G*=rho_g*ag` [kg/(m² s)]. Una tobera no bloqueada tiene `Mg<1` y su área geométrica mínima `Ag` no es el área crítica ficticia `A*`. Cuando se bloquea, `Ag=A*`.

### ¿Por qué el divergente acelera en supersónico?

El resultado 1D, para flujo isentrópico, es `dA/A=(M²-1)dV/V`. Para `M<1`, acelerar exige área decreciente. Para `M>1`, acelerar exige área **creciente**. En el estado `M=1`, el cuello geométrico permite cruzar de una rama a otra de forma suave. La relación `epsilon=Ae/Ag` describe el diseño sin elegir metros cuadrados. Cuando la garganta está bloqueada, conservación de masa exige `epsilon=G*/Ge`; esta ecuación posee **dos raíces**, una subsónica y otra supersónica, y elegir la raíz no determina por sí solo qué ocurre físicamente.

### Adaptación, sobreexpansión, subexpansión y contrapresión

Una salida **adaptada** satisface `pe=p_amb`: desaparece la fuerza de presión adicional. Si `pe>p_amb` está **subexpandida**; si `pe<p_amb`, **sobreexpandida**. Para una salida supersónica adaptada hay que escoger el área que hace `Ge=G*/epsilon` al estado isentrópico de presión `p_amb`. Una sobreexpansión grande aumenta el riesgo de choques y separación: no es correcto tomar siempre la raíz supersónica y afirmar que el empuje está físicamente resuelto.

Un **choque normal** convierte una corriente supersónica en subsónica, aumenta su entropía y reduce su presión total. Si ocurre dentro del divergente, el modelo isentrópico de extremo a extremo deja de servir. Nuestro programa devuelve `resuelto=False` y `None` para Mach, presión y empuje de salida cuando detecta esa zona por un umbral orientativo. La estimación de presión tras choque al plano de salida usa gamma local como **aproximación**; no se resuelve un choque con cp(T), no se localiza el choque y la frontera estimada no es fiable para diseño real. Una salida nominalmente sobreexpandida por debajo de ese umbral se etiqueta **ideal** y requiere precaución ante separación y efectos externos.

### Empuje específico y dependencia con el ambiente

En un estado resuelto de esta **tobera aislada**:

`Fs=Ve+1000(pe-p_amb)/(rho_e Ve)` [N/(kg/s) = m/s].

La contribución de momento es `Ve`, y la presión añade o resta empuje según `pe-p_amb`. No se puede obtener `F [N]` sin caudal de masa; tampoco se deduce el empuje neto del motor completo sin restar momento de aire entrante, introducir factor de combustible cuando corresponda y acoplarlo expresamente. El ambiente influye incluso a `Tt,pt,epsilon` fijos, porque puede cambiar el régimen físico y el término de presión.

## 3. PYTHON — diseño y firmas completas

Los nuevos elementos son funciones puras (no leen Flask, ficheros ni estado global mutable). Todas las temperaturas están en K, presiones en kPa, entalpías en kJ/kg y velocidades en m/s. Las funciones de apoyo empiezan por `_`: convención de interfaz interna, no restricción automática de Python.

| Función (firma completa) | Argumentos y retorno | Llamadas y errores |
|---|---|---|
| `_biseccion(funcion, inferior, superior, *, iteraciones=110)` | Callable real→real, dos límites reales y máximo entero; `float` raíz. `*` obliga a pasar `iteraciones` por nombre. | Llamada por inversores/sonicidad/áreas; lanza `ErrorNumericoCiclo` si no encierra raíz o no converge. |
| `_estado(T, Tt, pt)` | Tres reales (K,K,kPa) → dict `T,p,V,a,M,rho,G` (K,kPa,m/s,m/s,–,kg/m³,kg/(m² s)). | Usa `h,s0,gamma` del módulo común; llamada por `_sonico`, `_salida_area` y las dos públicas; error de dominio procedente de propiedades. |
| `_sonico(Tt, pt)` | K,kPa → dict de `_estado` a Mach 1 o `None` si no representable. | Llama a `_estado` y `_biseccion`; utilizada por las públicas. |
| `_temperatura_para_presion(Tt, pt, p)` | K,kPa,kPa → T [K] isentrópica. | Llama a `s0,_biseccion`; `EstadoFueraDeRango` para T fuera de 200–2000 K. |
| `_salida_area(Tt, pt, critico, epsilon, *, supersonica)` | K,kPa,dict sónico,ratio y booleano de rama → dict de `_estado`. | Llama a `_estado,_biseccion`; valida existencia de raíz en rama y dominio; `EstadoFueraDeRango`/`ErrorNumericoCiclo`. |
| `_validar(Tt, pt, p_amb, epsilon)` | Cuatro reales → `None` tras validar. | Llamada por las públicas; `ValueError` para tipos, temperaturas, contrapresión o geometría inválidos. |
| `_resultado(Tt, pt, p_amb, epsilon, critico, garganta, salida, regimen, *, motivo=None, umbral_choque=None)` | Reales de entrada, estados `dict/None`, cadena y diagnósticos → dict homogéneo de resultados y residuos. | Llamada por `resolver_tobera_convergente_divergente`; convierte estados desconocidos en `None` sin fabricar ceros. |
| `resolver_tobera_convergente_divergente(Tt, pt, p_amb, epsilon)` | 4 reales → dict con entradas, `regimen`, `resuelto`, diagnóstico; estados de garganta/salida, área por caudal [m²/(kg/s)], flujo por área [kg/(m² s)], residuos de energía [kJ/kg], masa [kg/(m² s)], entropía [kJ/(kg K)] y empuje [N/(kg/s)] si procede. | Entrada pública para tests/código futuro; llama a todos los auxiliares. `ValueError` por entradas, `EstadoFueraDeRango` si expansión exige T fuera, `ErrorNumericoCiclo` si no convergen raíces. |
| `relacion_areas_adaptada(Tt, pt, p_amb)` | Tres reales (K,kPa,kPa) → epsilon `float` adimensional de salida supersónica adaptada. | Entrada pública para tests/futuro cálculo educativo; llama a `_validar,_sonico,_temperatura_para_presion,_estado`; `ValueError` si la rama no es supersónica, `EstadoFueraDeRango` por dominio, `ErrorNumericoCiclo` por inconsistencia. |

Un `dict` de Python contiene pares clave–valor: `r['mach_salida']` accede al Mach; si hay choque no resuelto, devuelve `None`, no `0`. La expresión `float(...)` normaliza tipos numéricos una vez validados; `isinstance(x, Real)` y `isfinite(x)` rechazan texto, infinitos y NaN, y se rechaza específicamente `bool` porque en Python `True` se comporta como `1`. La llamada `_biseccion(..., supersonica=True)` no existe: el indicador de rama se pasa a `_salida_area` por nombre. Una **excepción** indica una entrada imposible o cálculo fuera de dominio; un **resultado no resuelto** indica que las entradas pueden ser físicas, pero faltan ecuaciones (choque).

### Revisión final: robustez y conservación de estados parciales

**PYTHON.** `math.isfinite()` puede lanzar `OverflowError` con un entero como `10**10000`, demasiado grande para convertirlo a `float`. La validación ahora usa `try/except (OverflowError, TypeError, ValueError)` para transformar esa incidencia en un `ValueError` estable. No se atrapan errores arbitrarios ajenos a la conversión. Se comprueban las cuatro posiciones, además de las tres de la función inversa.

**FÍSICA / INGENIERÍA.** Un choque en el divergente invalida la predicción isentrópica de **salida**, pero no borra el hecho previo de que la garganta está bloqueada. Por eso la llamada a `_resultado()` ahora recibe el `dict` crítico como `garganta` incluso en `resuelto=False`; su Mach es 1 y conserva las cinco propiedades estáticas conocidas. `salida=None` impide deliberadamente calcular presión, temperatura, velocidad, Mach, residuos de salida, masa entre planos o empuje. Los residuos de garganta permanecen sin informar en este contrato para no confundirlos con el cierre global.

**PYTHON — referencia independiente.** La prueba de gas perfecto calcula la relación de áreas con `gamma` constante y usa una **bisección construida dentro del propio test** entre Mach 1 y 5 para invertir la fórmula. No llama a `_salida_area`, `_sonico` ni otros auxiliares de producción. Se compara el Mach así obtenido con el de cp(T) y se admite un 3 % relativo a 600 K, margen de comparación entre modelos caloríficos diferentes, no banda de validación experimental. Otra prueba toma el umbral de choque aproximado que informa el modelo y evalúa presiones apenas a ambos lados: comprueba el diagnóstico previsto, la presencia de propiedades críticas y la ausencia de empuje ficticio. Esa prueba verifica **lógica implementada**, no la ubicación física exacta de un choque con propiedades variables.

### Ejemplo ejecutable

```python
from tobera_convergente_divergente_cp import (
    relacion_areas_adaptada, resolver_tobera_convergente_divergente,
)

epsilon = relacion_areas_adaptada(1200, 500, 70)
r = resolver_tobera_convergente_divergente(1200, 500, 70, epsilon)
assert r['resuelto'] and r['adaptacion'] == 'adaptada'
print(epsilon, r['mach_garganta'], r['mach_salida'])
# 1.652764797975252, 1.0, 1.939449112467219 (aprox.)

choque = resolver_tobera_convergente_divergente(1200, 500, 400, epsilon)
assert not choque['resuelto'] and choque['empuje_especifico_total'] is None
```

## 4. Procedimientos numéricos y verificación

La **bisección** exige una función continua con valores de distinto signo a ambos extremos; es más lenta que Newton, pero no necesita una derivada de `cp(T)` y mantiene las raíces dentro del intervalo permitido. `T_desde_h` del módulo común existe, aunque aquí la temperatura de salida se despeja cómodamente desde `s0` con bisección para imponer una presión dada. El sistema no interpola gamma ni usa la ecuación de área–Mach de gas perfecto como ecuación exacta.

El archivo `tests/test_tobera_convergente_divergente_42a.py` comprueba cierre de masa, entropía y energía, presión contra ambiente, Mach y límites, errores, choque sin salida ficticia, comparación con tobera M35 y **referencia analítica independiente de gas perfecto**. La versión inicial tenía 16 pruebas específicas y una suite global de 573 (564 correctas, 9 omitidas). Después de esta revisión hay **19 pruebas específicas correctas**, seis módulos de regresión relacionados con **78 pruebas (77 correctas, 1 omitida)**, y **576 globales (575 correctas, 1 omitida, 0 fallidas)** en Python 3.12. Solo se omite Cantera opcional; SciPy está disponible. Un primer intento global sin configurar Flask/Jinja2 temporal falló por importación, no por física; la suite completa corregida terminó correctamente.

## 5. Experimentos propuestos

1. Conserva `epsilon≈1.652765` y cambia `p_amb` entre 40, 70, 140, 400 y 480 kPa. Observa cuándo varía `pe`, cuándo cambia solo el término de presión, cuándo no se puede calcular empuje y cuándo la garganta deja de estar bloqueada.
2. Calcula `epsilon_adaptada` a 50, 70 y 100 kPa. ¿Qué ocurre con la relación de áreas necesaria a medida que baja la presión exterior?
3. Contrasta la fórmula área–Mach analítica con `gamma(600 K)` constante y la solución a cp(T). Justifica por qué las magnitudes son próximas pero no idénticas.

## 6. Alcance y fuentes

Son verificaciones del programa y del modelo escogido, **no validación experimental**. No se modela gas de combustión real, fricción, separación, choques o empuje absoluto. Lectura complementaria de NASA Glenn: [Mass Flow Rate Equations](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/mass-flow-rate-equations/) y [Nozzle Design](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/nozzle-design/). Esas relaciones didácticas suelen presuponer gas perfecto de gamma constante: distinguir siempre esa hipótesis de nuestra inversión cp(T).

Detalles de resultados en [documento técnico 42.A](42a_tobera_convergente_divergente_cp.md) y descripción del código actual en [`CODE_WALKTHROUGH.md`](../../CODE_WALKTHROUGH.md).
