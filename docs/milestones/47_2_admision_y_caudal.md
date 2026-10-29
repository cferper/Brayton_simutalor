# Milestone 47.2 — Admisión, continuidad y vuelo

## Propósito y límite de determinación

Se añade un **diagnóstico condicional** de admisión `admision_caudal_cp.py` que utiliza el ambiente, remanso y difusor ya calculados. No pretende convertir un área exterior en un caudal real del motor cuando faltan condiciones del compresor. Se conserva la recuperación `pi_d` de presión total y el modelo `cp(T)`.

Las secciones se distinguen explícitamente:

1. **Área de captación exterior `A_cap`**: área de corriente exterior interceptada en vuelo, a condiciones de corriente libre.
2. **Área de entrada del compresor `A_2`**: sección interna, con condiciones locales posteriores al difusor. No es necesariamente igual a `A_cap`.
3. La geometría de conductos entre ambas y una sección adicional de referencia del compresor requerirían datos que aún no tenemos: no se atribuyen a estas secciones pérdidas nuevas.

## Ecuaciones

Para corriente libre en vuelo subsónico (`M∞>0`): `V∞ = M∞ sqrt(gamma(T∞) R T∞)`; `rho∞=1000 p∞/(R T∞)` con p en kPa; el caudal de la corriente exterior **geométricamente interceptada** es `rho∞ V∞ A_cap`. Si ya se conoce el caudal de aire compatible, el área requerida de captación es `mdot_a/(rho∞ V∞)`. Esta igualdad no impone que la admisión capture efectivamente esa corriente: necesitaríamos modelar su interacción con el motor.

En la entrada de compresor, el usuario puede proporcionar un **Mach estático local**, que es un dato independiente, no una predicción. Con el remanso del difusor `Tt2`, `pt2`, se resuelve:

\[h(T_{t2})=h(T_2)+\frac{M_2^2\gamma(T_2)RT_2}{2000}\]

\[p_2=p_{t2}\exp\left(\frac{s^0(T_2)-s^0(T_{t2})}{R/1000}\right)\]

\[\dot m_2=\frac{1000p_2}{RT_2}\,M_2\sqrt{\gamma(T_2)RT_2}\,A_2\]

El cálculo resuelve la temperatura estática por bisección y conserva el modelo variable. La condición `pt2=pi_d*pt∞` ya procede del modelo anterior; no se atribuye una distribución interna de pérdidas sin datos.

## Caso estático y condiciones de solución

Cuando `M∞=0`, **no se evalúa como caudal real `rho∞ V∞ A_cap = 0`**. El compresor puede aspirar en estático. Sin condición local del compresor o un caudal proporcionado por otro componente, el contrato devuelve `aspiracion_no_determinada`, con caudales `None`.

Si se suministran `A_2` y `M_2`, se calcula un caudal **condicionado** por esa entrada; si simultáneamente hay un caudal compatible con tobera, se verifica continuidad y se reporta incompatibilidad cuando no coinciden. No se reajusta automáticamente un dato impuesto.

## Ejemplo reproducible

```python
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor
v = {**DEFAULTS_TURBO, 'mach':'0.5', 'gasto_masico_aire':'20',
     'area_captacion':'0.1', 'area_entrada_compresor':'0.1',
     'mach_entrada_compresor':'0.3'}
r = simular_turborreactor(v)
print(r['estudio_admision'])
```

Los valores de áreas y Mach local **son parámetros de ensayo ilustrativos**, no datos identificados para un motor real. Variar el área de captación a velocidad y ambiente constantes duplica linealmente la masa de corriente exterior interceptada; variar `pi_d` modifica el flujo local en la sección interna a `M_2` dado.

## Verificación y límites

`tests/test_admision_caudal_47_2.py` cubre motor estático sin aspiración inventada y con condición interna, vuelo, presión y temperatura, variación de áreas, recuperación del difusor, continuidad, incompatibilidad, dominios e integración web. El control de igualdad de caudal usa tolerancia relativa `2e-6`, coherente con el resto del proyecto; los residuos de energía del cálculo local se comprueban numéricamente.

Esto es **verificación matemática de un modelo condicional**, no validación con medidas. Falta dependencia de flujo y velocidad de compresor, geometría de conducto, campo de entrada estático real, captura/derrame y efectos viscosos. Estos elementos requieren mapas o datos de diseño; no se han supuesto silenciosamente.
