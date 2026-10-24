# Aprendizaje de Fase 2C — Viabilidad y dos óptimos con cp(T)

**Base verificada:** `76aef1973ba1d655f584386ed41d59259c326047` en `mejoras/cp-variable`, 24/10/2026. Se añade un módulo independiente al solucionador 2B. El modelo antiguo permanece intacto.

## Ingeniería: qué cambia

Con cp variable hay que resolver las temperaturas con entropía y entalpía, no con potencias de presión basadas en gamma constante. Para cada `rp`, 2B devuelve cuatro estados, trabajo, calores y viabilidad. En lugar de aceptar cualquier `rp>0`, el nuevo módulo calcula primero dónde los estados caben entre 200 y 2000 K y dónde los calores tienen sus signos físicos.

La variable `x=ln(rp)` facilita la búsqueda porque las relaciones de entropía son lineales en x. Las derivadas de los estados isentrópicos se obtienen de `ds0/dT=cp(T)/(1000 T)` y `dh/dT=cp(T)/1000`:

- `d h2s/dx = R_kJ*T2s`.
- `d h4s/dx = -R_kJ*T4s`.
- `d wnet/dx = R_kJ*(eta_t*T4s - T2s/eta_c)`.

Por ello el trabajo tiene máximo global único en su dominio motor conexo. El rendimiento usa otra condición; en general `rp_A != rp_B`.

Para justificar B sin confiar en una malla, define `q=h3-h2`, `v=h4-h1`, `a=R_kJ*T2s/eta_c`, `b=R_kJ*eta_t*T4s`. Entonces `eta=1-v/q` y el signo de su derivada es `F=b*q-a*v`. Como `F'=b'*q-a'*v` y se exige `q,v>0`, `F` decrece estrictamente. Si cambia de signo de positivo a negativo hay máximo interior; si no, sólo un límite en frontera abierta.

## Programación: funciones y estructuras

- `_real_positivo(x)`: auxiliar `Real` finito y positivo → `bool`, sin unidades; filtro de apoyo, no entrada principal.
- `_raiz_monotona(funcion,inferior,superior,*,creciente=True,tol=1e-11)`: función real y cotas de `ln(rp)` → raíz aproximada de la ecuación `f(x)=0`; usa bisección hasta 100 iteraciones. `ValueError` si no hay cambio de signo, `ArithmeticError` si no converge. La llama `estudiar_cp_variable` para raíces de trabajo y de derivada del rendimiento. `creciente` es parámetro informativo no utilizado por el algoritmo de signos.
- `_maximo_acotado(funcion,inferior,superior,tolerancia)`: objetivo numérico y cotas de `ln(rp)` → abscisa aproximada del máximo; usa sección áurea, hasta 160 pasos; requiere unimodalidad (probada para el trabajo). Eleva `ArithmeticError` si no converge. No se usa para decidir A desde el cierre: queda como auxiliar para contrastes numéricos de prueba.
- `estudiar_cp_variable(T1,T3,p1=100.,eta_c=.85,eta_t=.9,delta=.05,*,tolerancia=1e-9,muestras=160)`: reales físicos, tolerancia adimensional y entero de discretización → diccionario con `dominio_motor`, `A`, `B`, `limites_calculables`, `tipo`. Contiene puntos originales de 2B en los máximos, con unidades iguales a las de 2B. `ValueError` para entradas inválidas y las excepciones numéricas de 2B si se producen estados irrepresentables. Llama al solucionador y a los dos algoritmos anteriores.

Ejemplo:

```python
from optimizacion_cp_variable import estudiar_cp_variable
estudio = estudiar_cp_variable(288.15, 1600)
print(estudio['dominio_motor'])
print(estudio['A']['rp'], estudio['B']['rp'])
```

## Resultados y honestidad científica

El caso base da `rp_A≈15.878`, `wmax≈414.086 kJ/kg`, `rp_B≈46.819`, `eta_max≈43.745 %`. Las dos relaciones de presión no coinciden. Una frontera abierta no pertenece al dominio: en el caso reversible el rendimiento puede tener un supremo sin máximo. El balance de primera ley es una identidad de las entalpías; no constituye validación experimental.

**Pruebas realizadas en esta reconstrucción:** 13/13 específicas correctas sobre los archivos originales recuperados de GitHub; la suite completa de Flask no se ha ejecutado aquí. No se introdujeron dependencias, integraciones HTML ni nuevos modelos químicos.


## Cierre técnico del 24/10/2026: fronteras abiertas

**PYTHON.** El algoritmo comprueba el signo de `derivada_trabajo` en los extremos interiores. Si cambia de positivo a negativo, busca la raíz con `_raiz_monotona`. Si no cambia, el resultado no se etiqueta artificialmente como óptimo interior. La función retorna un diccionario diferenciando `maximo_interior`, `supremo_frontera` y `sin_motor`.

**INGENIERÍA.** La concavidad del trabajo en `ln(rp)` se deduce de la disminución de `T4s` y el aumento de `T2s`. Para el modelo actual, una frontera térmica excluida no puede albergar un supremo de trabajo positivo: en `q_in=0`, el balance daría `w=-q_out<0`; en `T4s=200 K`, la pendiente es no positiva. Por eso un motor existente tiene máximo A interior. Para el rendimiento B, la unicidad interior requiere simultáneamente `q_in>0` y `q_out>0`; fuera de ese dominio no debe proclamarse. La reversibilidad puede situar su supremo B en una frontera abierta.

**Verificación actual.** 13/13 pruebas nuevas correctas ejecutadas con los archivos originales 2A/2B idénticos a los publicados (hashes Git `f7ab17eae7498f400115419d8e08a0e257f176c8` y `a71bbbb7b666e8008c4ee16070e8657cdb3e17e5`). No se considera validación experimental.