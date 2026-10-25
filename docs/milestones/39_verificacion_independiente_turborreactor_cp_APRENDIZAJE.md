# Aprendizaje — Milestone 39: verificar científicamente un turborreactor

**Fecha:** 25-10-2026. **Rama:** `mejoras/cp-variable`.
**Base remota:** `66a35f9dfae9078b97c58ec7c796492ff94b1351`.
**Publicación:** pendiente hasta el commit y GitHub Actions.

## 1. Verificación no significa validación experimental

**Verificar** significa investigar si hemos programado correctamente las
ecuaciones del modelo: por ejemplo, comprobar que la turbina desarrolla la
potencia necesaria para mover el compresor. **Validar** requiere comprobar
si el modelo representa suficientemente bien un fenómeno real para un uso
definido, por ejemplo contrastar datos medidos de consumo, empuje y condiciones
de funcionamiento de un motor identificado.

Un resultado numérico plausible no demuestra ni una cosa ni otra: una fórmula
equivocada puede producir cifras próximas a las esperadas. Por eso usamos
ecuaciones **independientes** del código a verificar, casos límite y balances
de unidades. Ni la coincidencia con una referencia teórica más sencilla ni
493 pruebas anteriores constituyen validación experimental.

## 2. Dos modelos termodinámicos correctos pueden diferir

El turborreactor desarrollado usa propiedades variables del aire con
`cp(T)`, `h(T)`, `s(T,p)`, `gamma(T)` entre 200 y 2000 K. Para contrastarlo,
`referencia_perfecta` usa gas caloríficamente perfecto:

\[
h(T)=c_p(T-298.15),\qquad s(T_2,p_2)-s(T_1,p_1)
=c_p\ln(T_2/T_1)-R\ln(p_2/p_1).
\]

Se impone `cp=1.08 kJ/(kg K)` constante, `R=R_AIRE` en J/(kg K) y
`gamma=cp/(cp-R/1000)`. La relación `gamma` se calcula con cp en **kJ** y
R convertido a **kJ**; mezclar `cp=1.08` con `R=287` sin dividir por 1000
sería un error dimensional grave.

La temperatura isentrópica del compresor resulta explícita:

\[
T_{2s}=T_1\,rp^{(\gamma-1)/\gamma},\qquad
T_2=T_1+\frac{T_{2s}-T_1}{\eta_c}.
\]

En el modelo variable es necesario invertir entropía y entalpía por métodos
numéricos. Ambos procedimientos pueden estar bien implementados y discrepar
porque el calor específico varía con T en uno y se aproxima como constante
en el otro.

## 3. Referencias de entalpía y combustión

`propiedades_aire.py` establece `h(298.15 K)=0`. Al añadir combustible,
el balance por kg de aire entrante es

\[
h_2+f\eta_bPCI=(1+f)h_3,
\qquad f=\frac{h_3-h_2}{\eta_bPCI-h_3}.
\]

Para interpretar esta ecuación debemos fijar **una referencia coherente**:
el modelo trata la entalpía sensible del combustible como despreciable en
298.15 K y conserva una energía química representada por PCI. Si se sumara
sin criterio un valor absoluto de entalpía química a una entalpía sensible
relativa, cambiaría artificialmente f. En gases reales hay diferencias de
composición y entalpías de formación que todavía no hemos modelado.

Además el caudal de turbina es mayor que el del compresor:

\[
\eta_m(1+f)(h_3-h_4)=h_2-h_1.
\]

El factor `1+f` es imprescindible. Por último, se comprueba que en el
estado isentrópico ficticio la entropía de turbina se conserva y que su
salida permite la tobera correspondiente.

## 4. Por qué un residuo es útil, pero insuficiente

Un **residuo** es la diferencia entre ambos lados de una ecuación evaluada
con la solución calculada. Por ejemplo:

\[
\varepsilon_{eje}=\eta_m(1+f)(h_3-h_4)-(h_2-h_1),
\]

en kJ por kg de aire. Si tiende a cero, el balance está cerrado. Sin embargo,
el programa puede haber resuelto correctamente **una ecuación equivocada**.
La referencia independiente y las pruebas de límites intentan encontrar
esa clase de fallos ocultos.

El error absoluto y relativo entre modelos se mide como
`abs(x_modelo-x_ref)` y `abs(x_modelo-x_ref)/abs(x_ref)` cuando la referencia
no es cero. En los casos A/B/C, las discrepancias de empuje específico son
aproximadamente 1.36 %, 1.42 % y 1.21 %. El error es pequeño, pero no
representa una incertidumbre certificada del motor: es la diferencia entre
**dos hipótesis caloríficas elegidas**.

## 5. Tobera y vuelo: verificaciones independientes

En gas perfecto la temperatura de remanso es

\[
T_{t0}=T_\infty\left[1+\frac{\gamma-1}{2}M_\infty^2\right],
\]

y la presión total ideal sigue de la isentropía. El difusor conserva Tt
y utiliza `pt2=pi_d*pt0`. Por eso **pt2 no es p estática exterior**: la
presión del exterior sirve de contrapresión de tobera.

La tobera verifica energía `Ve²=2000*(ht-he)`, Mach calculado con la
temperatura **estática de salida**, continuidad de flujo y el término de
presión. La prueba próxima al bloqueo usa presiones ligeramente inferiores
y superiores a la crítica para comprobar la transición continua, sin
introducir una fórmula exacta de gamma constante en producción.

El empuje neto en vuelo, por kg/s de aire, es

\[
F_s=(1+f)V_e-V_\infty+(1+f)
\frac{1000(p_e-p_\infty)}{\rho_eV_e}.
\]

El factor 1000 pasa de kPa a Pa. El consumo es
`TSFC_kg_N_h=3600*f/Fs` solo si `Fs>0`: el factor 3600 convierte segundos
a horas, no incrementa físicamente el consumo.

## 6. Fallo concreto detectado en el mapa: física frente a filtro

El milestone 38 admitía `exigir_empuje_positivo` y
`exigir_margen_tobera`, pero **su valor no modificaba la salida**.
La corrección es pequeña: conservar `estado` (verdad física calculada) y
añadir `cumple_restricciones` (booleano) y `cumplen_restricciones` (conteo).

Ejemplo a Mach .9, rp 3, pi_d .7, T ambiente 288.15 K, p ambiente 100 kPa:

- A T3=500 K no existe presión de expansión suficiente: `sin_expansion`.
- A T3=600 K el empuje neto es -137.6369 N/(kg/s): `empuje_no_positivo`.
- Con las restricciones exigidas, ninguno cumple el filtro.
- Con ambos `exigir_*` en `False`, los dos cumplen el **filtro relajado**,
  pero siguen sin ser candidatos a máximos de empuje positivo o mínimos TSFC.

Separar *estado físico*, *cumplimiento de preferencias* y *elegibilidad
para optimizar* es un concepto útil en programación científica. Nunca se
debe cambiar un estado no motor a `valido` por relajar una restricción.

## 7. Cómo se ha implementado en Python

Se añade `tests/test_verificacion_independiente_turborreactor_39.py`.
Sus dos funciones auxiliares nuevas son:

| Firma | Propósito y unidades | Salida y uso | Validación |
|---|---|---|---|
| `referencia_perfecta(*, mach, rp, eta_c, T3, delta, eta_t, eta_m, eta_n, eta_b, PCI, pi_d, T_amb, p_amb)` | Calcula de forma **independiente** gas perfecto para A/B/C. T [K], p [kPa], trabajo [kJ/kg], PCI [kJ/kg combustible], Fs [N/(kg/s)] | Dict con estados, Ve/Mach, empuje y TSFC. La llaman pruebas y comparación; no usa funciones de producción | `ValueError` si no hay expansión física bajo los parámetros elegidos; en pruebas solo casos compatibles |
| `comparar(valor_cp, referencia)` | Calcula errores de magnitudes con **mismas unidades** | `(error_absoluto, error_relativo)` en valor y razón [-]. La llaman pruebas y tablas de contraste | `ValueError` si hay valor no finito; denominador protegido ante cero |

Los tests usan `unittest.TestCase`, `subTest`, `@unittest.skipUnless`
e `importlib.util.find_spec('cantera')`. Un decorador (`@`) cambia la forma
en que el framework ejecuta una función sin cambiar sus ecuaciones: si
Cantera no está instalado, la prueba aparece **omitida**, no superada.
`unittest.mock.patch` sustituye temporalmente una función por un resultado
controlado para verificar filtros: luego restaura el original. Así
comprobamos defectos de programación sin inventar resultados científicos.

En el archivo existente `mapas_prestaciones_turborreactor_cp.py` se modifica
solo `_punto(entradas,indices,config)` para registrar
`cumple_restricciones`, y `_resumen(puntos,nx,ny,comparar)` para contar el
nuevo campo. Las firmas, entradas y magnitudes anteriores permanecen.

**Ejemplo:**

```python
from mapas_prestaciones_turborreactor_cp import barrer_rp_t3

m = barrer_rp_t3([3], [500, 600], mach=.9, pi_d=.7,
                 T_amb=288.15, p_amb=100,
                 restricciones={"exigir_empuje_positivo": False,
                                "exigir_margen_tobera": False})
print(m["estados"])
print(m["cumplen_restricciones"], m["validos"])
```

El primer valor lista `sin_expansion` y `empuje_no_positivo`. Los conteos
son dos que cumplen el filtro relajado y cero válidos para optimización.

## 8. Verificación frente a validación pendiente

Los 12 métodos específicos prueban compresión/expansión ideales, balances,
remanso, crítica de tobera, límites térmicos, propulsión con y sin combustible,
referencia de gas perfecto, Pareto sintético y la discrepancia de restricciones.
Una de las pruebas depende opcionalmente de Cantera; si no está disponible,
se omite y no se incorpora a `requirements.txt`.

No hemos contrastado todavía curvas experimentales de un motor real, mapas
de turbomáquinas ni propiedades de gas quemado. Tampoco se infiere fiabilidad
estadística de que un residuo sea casi cero. Para pasar a validación harían
falta datos externos, incertidumbres conocidas y condiciones de ensayo.

### Referencias oficiales

- [NASA Glenn — Burner Thermodynamics](https://www.grc.nasa.gov/www/k-12/airplane/burnth.html).
- [NASA Glenn — Specific Fuel Consumption](https://www.grc.nasa.gov/www/k-12/airplane/sfc.html).
- [NASA/NACA — Performance Charts for a Turbojet System](https://ntrs.nasa.gov/citations/19930093534).
- [Cantera — propiedades](https://cantera.org/stable/python/thermo.html) y [tutorial](https://cantera.org/stable/userguide/python-tutorial.html).
