# Milestone 35 — Aprendizaje: de la turbina a una tobera convergente

Base comprobada: `2300aabcc6bb56c2b638238925dd2427f2123946`, rama `mejoras/cp-variable`. Véase el [documento técnico](35_tobera_cp_variable.md).

## 1. ¿Qué ocurre con la energía de salida del núcleo?

En el milestone 34 calculamos `T4` y `p4` al dar trabajo la turbina al compresor. Allí no consideramos energía cinética en el plano 4. Para estudiar ahora una tobera idealizada, **interpretamos** estos datos como condiciones **de remanso** `Tt,pt`: entalpía que tendría el aire si se frenase adiabáticamente hasta velocidad cero y presión de remanso equivalente. Esta interpretación necesita la hipótesis adicional de velocidad del flujo despreciable en el plano de turbina. En la salida de la tobera distinguimos propiedades **estáticas** `Te,pe`, ligadas a temperatura y presión que mediría un sensor moviéndose con el aire.

En flujo adiabático sin trabajo del eje, la entalpía de remanso se transforma en energía cinética:

\[
h_t=h_e+\frac{V_e^2}{2000}\quad [\mathrm{kJ/kg}].
\]

El factor `2000` procede de pasar J/kg a kJ/kg y del `1/2` cinético. El estado isentrópico `Tes` se calcula de `s(Tes,pe)=s(Tt,pt)`, con `s(T,p)=s0(T)-R ln(p/p_ref)` y `R=R_AIRE/1000` si la entropía está en kJ/(kg K). El rendimiento `eta_n` fija `h_e=h_t-eta_n*(h_t-h(Tes))`. Cuando `eta_n=1`, `Te=Tes` exactamente; una eficiencia menor conserva menos conversión cinética para una misma presión elegida.

## 2. ¿Por qué se bloquea una convergente?

El sonido local viaja a `a=sqrt(gamma(Te)*R_AIRE*Te)`. Dividiendo `Ve/a` obtenemos el Mach; al acercarse a uno, una tobera solo convergente no puede seguir aumentando el Mach por debajo del valor crítico de presión ambiente. Con cp(T), gamma cambia al cambiar `Te`, por lo que resolvemos la raíz `M=1` con bisección para el **modelo de eficiencia que hemos definido**. Una fórmula clásica con gamma constante sirve para comprobar órdenes de magnitud, no para imponer una respuesta exacta.

Cuando `pamb` supera la crítica, la tobera puede adaptarse a ambiente y `pe=pamb`. Cuando `pamb` está por debajo, la salida convergente permanece sónica con `pe=pcrit>pamb`.

## 3. Del flujo al empuje

La ecuación estática simplificada es

\[
F=\dot m V_e+(p_e-p_{amb})A_e,\qquad
\frac{A_e}{\dot m}=\frac{1}{\rho_eV_e}.
\]

Las presiones del programa están en kPa: para el término de empuje hay que multiplicar `pe-pamb` por 1000 para convertir a Pa. Dividiendo por el caudal:

\[
F_s=V_e+\frac{1000(p_e-p_{amb})}{\rho_e V_e}\quad [\mathrm{N/(kg/s)}=\mathrm{m/s}].
\]

Separamos en el diccionario `empuje_especifico_momento`, `empuje_especifico_presion` y `empuje_especifico_total`. Un número específico de 900 m/s no significa 900 N: sin `mdot` no hay empuje absoluto. No modelamos combustible, de modo que hemos supuesto artificialmente caudal de aire idéntico en todas las secciones.

## 4. Python: funciones y tratamiento numérico

En `tobera_cp_variable.py`:

- `_validar_real(x)`: recibe un valor; devuelve `True` si es real, finito y no `bool`; no tiene unidades ni efectos secundarios. Lo usa el solucionador para rechazar entradas ambiguas.
- `_estado_desde_isentropica(Tt,ht,Tes,eta_n)`: K, kJ/kg, K y eficiencia adimensional; devuelve `(Te [K], Ve [m/s], Mach [-])`. Llama a `h`, `T_desde_h` (si `eta_n<1`) y `gamma`, y lanza excepciones por energía o dominio inválidos. Es auxiliar de los dos solvers siguientes.
- `_estado_critico(Tt,ht,eta_n)`: K, kJ/kg, eficiencia; devuelve `Tes` crítica [K] o `None` si M=1 no se encuentra dentro del dominio. Usa `_estado_desde_isentropica` y un bucle `for` con bisección de intervalos. Falla explícitamente si no converge.
- `resolver_tobera_convergente(Tt,pt,p_amb,eta_n=1.0)`: K, kPa, kPa, eficiencia; devuelve un `dict` con régimen, estado estático y de remanso, presión crítica, Mach, velocidad, densidad, área/caudal, empuje específico desglosado y residuos. Llama a las funciones anteriores y a la inversión `_temperatura_desde_s0` de Fase 2B para el caso no bloqueado. Puede levantar `ValueError`, `EstadoFueraDeRango` o `ErrorNumericoCiclo`.
- `resolver_nucleo_con_tobera(T_amb,p_amb,rp,eta_c,T3,delta,eta_t,eta_m,eta_n=1.0)`: temperaturas K, presión kPa, rendimientos y relaciones adimensionales; llama una sola vez a `resolver_acoplamiento`, recoge `temperaturas[3]` y `presiones[3]` como remanso de tobera, y devuelve `{'nucleo': {...}, 'tobera': {...}}`. Propaga los errores físicos sin fabricar salida.

Ejemplo de ejecución:

```python
from tobera_cp_variable import resolver_nucleo_con_tobera
resultado = resolver_nucleo_con_tobera(288.15, 100, 10, .85, 1600, .04, .9, .98, .95)
tobera = resultado['tobera']
print(tobera['regimen'], tobera['mach_salida'])
print(tobera['empuje_especifico_total'])  # N/(kg/s)
```

El `dict` agrupa resultados con claves expresivas. `None` distingue una raíz sónica que queda fuera del intervalo de propiedades, nunca una presión crítica igual a cero. Los residuos de energía e isentropía permiten detectar errores. Prueba variar `eta_n` y después elevar `p_amb` hasta superar la presión crítica para observar cómo desaparece el término de presión.

## 5. Qué validan las pruebas (y qué no)

Los diez métodos de `test_tobera_cp_variable_35.py` cubren energía, reversibilidad, eficiencia, raíz sónica, cambio de régimen, continuidad, presión residual, unidades, errores e integración. La fórmula de presión crítica con gamma constante se usa como comparación **aproximada**. La suite histórica sirve para detectar regresiones. Ninguna de estas pruebas sustituye datos experimentales de una tobera o turborreactor.

Referencia conceptual: [NASA Glenn — Thrust Equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/thrust-force/).
