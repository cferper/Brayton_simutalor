# Milestone 36 — Aprendizaje: vuelo subsónico, difusor y empuje neto

Base: `c1fc5b5d36066d7ec5741b070b0d4721fbc5da69`, rama `mejoras/cp-variable`. [Documento técnico](36_condiciones_vuelo_cp.md).

## 1. Presión estática frente a presión de remanso

La corriente libre tiene temperatura y presión **estáticas** `T∞,p∞`: las que mediría un sensor que viaja con el aire. Al frenar idealmente ese flujo hasta velocidad cero, su energía cinética pasa a entalpía y la temperatura de **remanso** crece. Usamos `h(Tt0)=h(T∞)+V∞²/2000`, no `Tt/T=1+(gamma-1)M²/2` como identidad exacta, porque `cp` depende de temperatura. La presión de remanso `pt0` resulta de la igualdad isentrópica `s(Tt0,pt0)=s(T∞,p∞)`. Una relación de gamma constante solo sirve como referencia aproximada.

La velocidad de vuelo se obtiene de `V∞=M∞sqrt(gamma(T∞)*R_AIRE*T∞)`. `R_AIRE` está en J/(kg K), mientras `h` y `s` están en kJ/kg y kJ/(kg K); el factor 2000 lleva a J/kg e incluye 1/2. Solo aceptamos `0<=M∞<1`.

## 2. Atmósfera 0–20 km

El modelo usa **altitud geopotencial** `z` en metros. Entre 0 y 11 km la temperatura baja `6.5 K/km` y la presión se obtiene integrando equilibrio hidrostático con gas ideal. De 11 a 20 km, `T=216.65 K` y la presión disminuye exponencialmente. Se utilizan referencias `T0=288.15 K`, `p0=101.325 kPa`, `g0=9.80665 m/s²`, `R_ISA=287.05287 J/(kg K)`; se construye la presión a 11 km desde el primer tramo para que no exista salto. La atmósfera estándar representa un perfil convencional, **no** un pronóstico meteorológico. `R_ISA` es el valor estándar del perfil hidrostático, distinto en unas centésimas de por ciento de la mezcla simplificada `R_AIRE` empleada dentro del motor.

Como referencia general, consulta [NASA Glenn — Earth Atmosphere Equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/earth-atmosphere-equation-metric/). Las expresiones implementadas integran las ecuaciones por capas con constantes ISA declaradas, no reproducen sin más los ajustes redondeados de NASA.

## 3. Difusor y núcleo monoeje

La recuperación prescrita `pi_d=pt2/pt0` expresa qué fracción de la presión total ideal llega al compresor; con `pi_d=1`, no hay pérdida. El difusor se aproxima adiabático y sin trabajo, por lo que conserva `Tt2=Tt0`, aunque una pérdida de presión total implique irreversibilidad. **No** damos al compresor la presión ambiente estática en vuelo: le damos `pt2`. La tobera sí descarga frente a `p∞` y no frente a `pt2`.

El módulo 34 tenía una etiqueta de diagnóstico relativa al argumento `p_amb` (que representaba su presión de entrada). Por eso la integración construye una copia de su diccionario y recalcula el margen de presión usando la verdadera presión exterior `p∞`; no modifica la función pública 34 ni su contrato para casos estáticos.

## 4. El empuje neto y el término que se resta

En vuelo, el aire entra en el motor con momento longitudinal. El balance simplificado, sin combustible ni diferencia de caudales, es:

\[
F_s=V_e-V_\infty+\frac{1000(p_e-p_\infty)}{\rho_eV_e}.
\]

`Ve` representa el empuje específico bruto de cantidad de movimiento, `V∞` es la resistencia asociada al aire ingerido (*ram drag*) y el último término es el empuje específico por presión. El resultado puede ser negativo; no significa que el algoritmo deba cambiar el signo ni inventar potencia. Un estado sin presión de expansión suficiente da empuje **indefinido**, no cero. No calculamos newtons absolutos al no conocer `mdot`.

## 5. Python: funciones, unidades, validaciones y flujo

Archivo `vuelo_cp_variable.py`:

- `_finito(valor)`: recibe un objeto, devuelve booleano; rechaza booleanos y números no finitos. No tiene unidades; se llama desde validadores de atmósfera, remanso, difusor e integración.
- `atmosfera_estandar(altitud_geopotencial)`: recibe altura [m] entre 0–20000; devuelve diccionario `{altitud_geopotencial [m], temperatura [K], presion [kPa], densidad [kg/m³], capa [texto]}`. Aplica la potencia troposférica o la exponencial isotérmica; lanza `ValueError` fuera de rango.
- `calcular_remanso(T_estatica,p_estatica,mach)`: recibe K, kPa y Mach adimensional; devuelve temperaturas/presiones estáticas y de remanso, `velocidad_sonido`, `velocidad_vuelo` [m/s], residuos de energía [kJ/kg] y entropía [kJ/(kg K)]. Llama a `gamma`, `h`, `T_desde_h`, `s0`, `s` y maneja `ValueError`, `EstadoFueraDeRango` y `ErrorNumericoCiclo`.
- `aplicar_difusor(remanso,pi_d)`: recibe el diccionario anterior y `0<pi_d<=1`, devuelve temperatura/presión total de salida, presión total ideal y recuperación; no realiza otro ciclo. Lanza `ValueError` o `ErrorNumericoCiclo` si un parámetro/presión es inválido.
- `resolver_turborreactor_vuelo(mach,rp,eta_c,T3,delta,eta_t,eta_m,eta_n=1.0,pi_d=1.0,*,T_amb=None,p_amb=None,altitud_geopotencial=None)`: los primeros siete parámetros son Mach, relación de presión, rendimientos y temperaturas K; `eta_n`, `pi_d` son adimensionales. Con `*`, Python exige que ambiente/altitud se indiquen por **nombre** para evitar intercambiar presión con altura. Se acepta altitud ISA o pareja T/p, nunca mezcla de ambas. Devuelve diccionarios `ambiente`, `remanso`, `difusor`, `nucleo`, `tobera` y contribuciones de empuje [m/s], bandera de empuje positivo y diagnóstico. Si no hay margen, `tobera=None`, las contribuciones desconocidas y empuje neto son `None`. Llama una sola vez a `resolver_acoplamiento` y después, si es posible, a `resolver_tobera_convergente`; reutiliza sus excepciones.

Ejemplo reproducible:

```python
from vuelo_cp_variable import resolver_turborreactor_vuelo

r = resolver_turborreactor_vuelo(.7, 10, .85, 1600, .04, .9, .98,
                                eta_n=.95, pi_d=.97, T_amb=288.15, p_amb=100)
print(r['remanso']['velocidad_vuelo'])       # m/s
print(r['difusor']['presion_remanso'])       # kPa, entrada compresor
print(r['empuje_especifico_neto'])           # N/(kg/s)
```

Aprendizaje en programación: los diccionarios mantienen resultados asociados por nombre; `None` representa una magnitud no calculable; copiar `dict` permite corregir una referencia de diagnóstico sin cambiar el contrato del componente original. Las pruebas comparan casos analíticos atmosféricos y el límite caloríficamente perfecto con tolerancias explícitas, además de contrastar balances internos. Esto es **verificación**, no validación física con experimentos.
