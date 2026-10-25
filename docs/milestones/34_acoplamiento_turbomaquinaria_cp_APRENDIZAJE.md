# Milestone 34 — Aprendizaje: el eje de un turborreactor

Base de trabajo: `8ca5fe7`, rama `mejoras/cp-variable`. [Documento técnico](34_acoplamiento_turbomaquinaria_cp.md).

## 1. ¿Por qué no sirve directamente el Brayton anterior?

En el ciclo Brayton energético se suele fijar la salida de turbina a presión ambiente y obtener trabajo neto `wt-wc`: un eje podría entregar ese excedente al exterior. En un **turborreactor monoeje idealizado**, la turbina debe suministrar precisamente el trabajo que necesita el compresor más las pérdidas de transmisión. El propósito posterior del gas residual será una tobera; por eso necesitamos averiguar **qué presión queda al salir de la turbina**. Todavía no determinamos la expansión en la tobera ni el empuje.

## 2. El rendimiento mecánico

El compresor consume `wc=h2-h1` kJ/kg. Si `eta_m=0.98`, de cada 100 kJ/kg de trabajo generado en la turbina solo 98 kJ/kg llegan al compresor. En el modelo sin cargas auxiliares:

\[
\eta_m w_t=w_c,\quad w_t=w_c/\eta_m,\quad h_4=h_3-w_t.
\]

Un rendimiento menor obliga a la turbina a extraer más energía del flujo para alimentar el mismo compresor. Ese aumento suele reducir la presión restante aguas abajo.

## 3. ¿Por qué p4 se calcula y no se impone?

El compresor fija `p2=p1*rp` y la cámara simplificada `p3=p2*(1-delta)`. A partir de la temperatura de entrada `T3` conocemos `h3`; el balance del eje fija `h4` y, mediante `T_desde_h`, fija `T4`.

Después, el rendimiento isentrópico de turbina se interpreta como

\[
\eta_t=\frac{h_3-h_4}{h_3-h_{4s}}.
\]

Así recuperamos `h4s` y `T4s`. La transformación isentrópica ficticia cumple `s(T3,p3)=s(T4s,p4)`, con la relación del aire ideal:

\[
s(T,p)=s^\circ(T)-R\ln(p/p_{ref}),
\quad p_4=p_3\exp\left(\frac{s^\circ(T_{4s})-s^\circ(T_3)}{R}\right).
\]

**Unidades:** `R_AIRE` se proporciona en J/(kg·K), por eso el código lo divide entre 1000 al combinarlo con `s0` en kJ/(kg·K). Nunca restamos entalpía (kJ/kg) y entropía (kJ/(kg·K)) sin multiplicar por una temperatura.

El programa clasifica `p4/p_amb`: mayor que uno significa margen ideal de presión; menor que uno, ausencia de ese margen; aproximadamente uno, límite numérico. La clasificación no predice aceleración ni fuerza propulsiva.

## 4. ¿Cómo se programa?

Archivo `acoplamiento_turbomaquinaria_cp.py`:

- `resolver_acoplamiento(T_amb, p_amb, rp, eta_c, T3, delta, eta_t, eta_m)`: recibe ocho reales finitos, temperaturas en K, presión en kPa, relación y eficiencias sin unidades. Retorna el diccionario de estados, trabajos, diagnósticos y residuos descrito en el documento técnico. La validación rechaza booleanos, rangos incorrectos, compresión y aporte energético no positivos. Llama a `s0`, `s`, `h`, `T_desde_h` y a la inversión monótona de entropía ya disponible en `ciclo_cp_variable`.
- `_real(valor)`: auxiliar booleano; comprueba que una entrada es real, finita y no booleana. No hace cálculos físicos. Se llama desde el solucionador.
- `_invertir_h(valor, descripcion)`: recibe entalpía en kJ/kg y una etiqueta de error; retorna temperatura K usando `T_desde_h`. Distingue fallo de representabilidad de entalpía fuera de 200–2000 K. Se llama para `T2`, `T4` y `T4s`.

Python utiliza una **tupla** para conservar los cuatro estados en orden y un **diccionario** para asociar nombres legibles a resultados. Por ejemplo:

```python
from acoplamiento_turbomaquinaria_cp import resolver_acoplamiento
r = resolver_acoplamiento(288.15, 100, 10, .85, 1600, .04, .9, .98)
print(r['presiones'][3])          # p4 [kPa]
print(r['diagnostico_tobera'])    # categoría, no empuje
print(r['residuo_eje'])           # kJ/kg; próximo a cero
```

Usamos `ValueError` para parámetros físicamente inadmisibles, `EstadoFueraDeRango` para extrapolación de temperatura y `ErrorNumericoCiclo` si un resultado no es representable. No forzamos valores a 200 K ni fijamos p4 a la presión ambiente.

## 5. Aprendizaje y límites

Prueba cambiar solamente `eta_m` de 1 a 0.9 y compara `wt`, `T4` y `p4`: el compresor mantiene sus estados, pero la turbina debe extraer más trabajo. Cambia luego `eta_t`: con el mismo balance mecánico la temperatura real de salida se mantiene, pero la expansión isentrópica equivalente y la presión requerida cambian.

La composición del aire sigue fija; los gases calientes reales y el combustible no se modelan. Los tests reproducen identidades termodinámicas y examinan casos límite, pero **no** comparan con mediciones de un motor real. Esta distinción es verificación de software frente a validación física.
