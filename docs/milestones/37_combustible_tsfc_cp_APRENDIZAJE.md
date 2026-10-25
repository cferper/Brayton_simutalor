# Aprendizaje — Milestone 37: combustible y TSFC con cp(T)

**Fecha:** 25-10-2026. **Rama:** `mejoras/cp-variable`.
**Base remota verificada:** `5f5cd6e8195eddd6857112f3417d7f81f3deebe5`.
**Publicación de esta fase:** pendiente hasta comprobar el commit y CI.

## 1. Antes y después

Los milestones 34–36 daban un núcleo, una tobera convergente y empuje neto
subsónico. En la cámara se imponía `T3` y el flujo de aire mantenía el mismo
caudal a través de todas las turbomáquinas. Ahora incorporamos **combustible
como aporte de energía y de masa**, manteniendo aquellas funciones y su
comportamiento original. La nueva función pública vive en un archivo distinto;
no se ha integrado en Flask.

## 2. Ingeniería: ¿qué significa f?

`f = m_dot_combustible/m_dot_aire` es adimensional (kg/kg). Si `f=0.028`,
por cada 1 kg/s de aire entran 0.028 kg/s de combustible y salen aproximadamente
1.028 kg/s de mezcla equivalente. La aproximación ignora pérdidas de masa y
describe la mezcla como si siguiera siendo aire seco, con las mismas funciones
`cp(T)`, `h(T)` y `s(T,p)`.

**Cámara de combustión — primer principio por kg de aire:**

\[
h_2+f\eta_b PCI=(1+f)h_3,
\qquad
f=\frac{h_3-h_2}{\eta_b PCI-h_3}.
\]

La identidad necesita *la misma convención* de energía sensible: el aire de
`propiedades_aire.py` toma `h(298.15 K)=0`, y aquí se desprecia la entalpía
sensible del combustible a esa referencia. PCI es energía química disponible
por kg de combustible; `eta_b` es la fracción útil del PCI. Esto es una
**convención simplificada del balance**, no una demostración de equivalencia
entre entalpías de reactivos y productos reales. La cámara pierde además la
fracción `delta` de presión total: `p3=p2*(1-delta)`.

**Acoplamiento del eje:** el compresor recibe 1 kg/s de aire; la turbina procesa
`1+f` kg/s. Por eso la potencia por kg/s de aire cumple

\[
w_c=h_2-h_1,\quad w_t=h_3-h_4,\quad
\eta_m(1+f)w_t=w_c.
\]

Ojo: `w_t` es **por kg de gas**, no por kg de aire. Para despejar `T4`,
hallamos primero `h4=h3-wc/[eta_m*(1+f)]` y luego invertimos `h(T)`.
El rendimiento isentrópico de la turbina proporciona `h4s=h3-(h3-h4)/eta_t`.
De `s(T4s,p4)=s(T3,p3)` deducimos `p4`; no imponemos presión exterior en la
turbina, pues es la tobera la que descarga frente al ambiente estático.

**Tobera, vuelo y prestaciones:**

\[
F_{s,\mathrm{salida}}=(1+f)V_e,\qquad
F_{s,\mathrm{presion}}=(1+f)\frac{1000(p_e-p_\infty)}{\rho_eV_e},
\]
\[
F_{s,\mathrm{neto}}=F_{s,\mathrm{salida}}
 +F_{s,\mathrm{presion}}-V_\infty.
\]

Los empujes específicos están en N/(kg/s aire) = m/s. El **empuje bruto** es
la suma de las dos aportaciones positivas de salida (momento y presión); la
resistencia de entrada resta `V_infinito` por kg/s de aire admitido.

\[
TSFC=\frac{\dot m_f}{F}=\frac{f}{F_{s,\mathrm{neto}}}
\quad [\mathrm{kg/(N\,s)}],\qquad
TSFC_{\mathrm{hora}}=3600\,TSFC.
\]

Si la tobera carece de expansión, no existe `Fs` calculable y devolvemos
`None`; si el neto es cero o negativo, devolvemos el neto con signo y
`TSFC=None`, ya que no indica propulsión útil. Tampoco calculamos empuje o
caudal de combustible **absolutos** sin especificar caudal másico de aire.

## 3. Python: organización y contratos

Archivo nuevo: `combustible_cp_variable.py`. Las funciones precedidas por `_`
son auxiliares de implementación; la función pública es `resolver_...`.

| Función y firma | Parámetros, unidades | Retorno y llamadas | Validación |
|---|---|---|---|
| `_validar_entradas(rp, eta_c, T3, delta, eta_t, eta_m, eta_n, eta_b, PCI)` | rp, eficiencias, delta [-]; T3 [K]; PCI [kJ/kg] | `None`. La llama el solucionador público; comprueba `_finito` | `ValueError` por NaN, infinito, booleanos, dominios erróneos |
| `_compresor(T1, p1, rp, eta_c)` | T1 [K], p1 [kPa], rp/eta_c [-] | Dict T1,p1,h1,T2s,h2s,T2,p2,h2,trabajo, residuo. Usa `s0`, `h`, `_temperatura_desde_s0`, `_invertir_h`, `s` | Error fuera de 200–2000 K o presión inválida |
| `_combustor(h2, T3, p2, delta, eta_b, PCI)` | h2 [kJ/kg aire], T3 [K], p2 [kPa], eficiencias [-], PCI [kJ/kg combustible] | Dict T3,p3,h3,h2,delta,eta_b,PCI,f,factor_masico,aporte_quimico_efectivo,residuo_energia,referencia_entalpia. Usa `h` | `T3>T2`, denominador y presión positivos; `ValueError`/`ErrorNumericoCiclo` |
| `_turbina(T3, p3, h3, wc, f, eta_m, eta_t)` | T3 [K], p3 [kPa], h3 y wc [kJ/kg], f y eta [-] | Dict T4,p4,h4,T4s,h4s,trabajos,rendimientos,residuos. Usa `_invertir_h`, `s0`, `s` | Rechaza rango térmico, presión no física y potencia no positiva |
| `resolver_turborreactor_con_combustible(mach, rp, eta_c, T3, delta, eta_t, eta_m, eta_n=1.0, pi_d=1.0, eta_b=0.99, PCI=43000.0, *, T_amb=None, p_amb=None, altitud_geopotencial=None)` | Mach, relaciones, eficiencias [-]; T3/T_amb [K], p_amb [kPa], ISA [m], PCI [kJ/kg] | Dict `origen_ambiente`, `ambiente`, `remanso`, `difusor`, `compresor`, `combustor`, `turbina`, `tobera`, `prestaciones`, `diagnosticos`. Llama a las cuatro funciones anteriores y a las de milestones 35 y 36 | Ambiente directo o ISA exclusivamente; Mach en [0,1), dominios físicos; errores explícitos |

Las funciones auxiliares se invocan desde la función pública; esta es el
punto de entrada del modelo científico nuevo, y la llaman los tests o un
programa de usuario, no Flask. `None` señala resultados que no se pueden
definir; no representa el número cero. Los **diccionarios** (`dict`) facilitan
consultar por nombre las unidades y los residuos sin depender de posiciones.
Los **argumentos con valor por defecto** permiten usar parámetros razonables
sin forzar la llamada a rellenar todo. El `*` en la firma convierte T/p o
altitud en **argumentos solo por palabra clave**: obliga a escribir
`T_amb=288.15`, evitando confundir posición, altitud y presión.

**Ejemplo reproducible:**

```python
from combustible_cp_variable import resolver_turborreactor_con_combustible

caso = resolver_turborreactor_con_combustible(
    mach=0, rp=10, eta_c=0.85, T3=1600, delta=0.04,
    eta_t=0.90, eta_m=0.98, eta_n=0.95, pi_d=1,
    eta_b=0.99, PCI=43000, T_amb=288.15, p_amb=100)
print(caso["combustor"]["f"])
print(caso["prestaciones"]["TSFC_kg_N_h"])
```

Devuelve `f=0.028028207807639125 kg/kg` y
`TSFC=0.10529688397094178 kg/(N h)` bajo el modelo actual.
Sustituye ambiente directo por `altitud_geopotencial=10000` (eliminando
`T_amb` y `p_amb`) para usar ISA. Para vuelo usa `mach=0.7` y `pi_d=0.97`.

## 4. Recorrido del programa

1. La función pública valida el motor y selecciona ambiente directo o ISA.
2. Calcula remanso con `h(T)` y `s(T,p)` a partir de Mach y aplica difusor.
3. `_compresor` encuentra `T2s` por entropía y `T2` por entalpía.
4. `_combustor` determina `f` y `p3` y registra el residuo energético.
5. `_turbina` ajusta el trabajo por `1+f`, invierte entalpías y obtiene p4.
6. Comprueba `p4` frente a presión **estática** exterior; si es viable llama
   al solucionador de tobera del milestone 35.
7. Suma el empuje de salida, resta la entrada y calcula TSFC si `Fs>0`.

El uso de **funciones puras** para calcular cada componente evita modificar
globales o los módulos anteriores. Esto reduce las regresiones y permite
probar un balance aislado antes de integrar todo el ciclo.

## 5. Verificación matemática y validación física

El archivo `tests/test_combustible_cp_variable_37.py` contiene 15 métodos
`unittest`. Comparan balances por álgebra independiente, tendencias de PCI y
`eta_b`, expansión isentrópica, energía de tobera, factor másico de empuje,
TSFC, condiciones ambientales, entradas inválidas y regresión del milestone 36.

Dos comprobaciones de referencia requieren cuidado:

- `PCI=10^12 kJ/kg`: provoca `f` muy pequeño y recupera el modelo sin
  combustible. Es **únicamente un límite matemático**, sin combustible real.
- Con `gamma=1.4` y `cp=1.0045 kJ/(kg K)`, la compresión isentrópica
  perfecta y la estimación de f resultan próximas, pero no iguales a cp(T).
  Es una **comprobación externa aproximada**; no sustituye pruebas de datos.

Ejecución específica realizada: `python -m unittest discover -s tests -p
'test_combustible_cp_variable_37.py' -q`: 15 pruebas, 0 fallos.
La ejecución de la suite completa y CI se comunicarán con sus resultados
efectivos en el informe final. La precisión del balance del eje no demuestra
exactitud de temperaturas o consumos de una turbina real.

## 6. Experimentos propuestos

1. Aumenta `PCI` de 40 000 a 46 000 kJ/kg manteniendo todo lo demás.
   **Comprueba:** `f` disminuye, porque cada kg de combustible aporta más energía.
2. Reduce `eta_b` de 0.99 a 0.80. **Comprueba:** sube `f`.
3. Cambia Mach de 0 a 0.7 con el ambiente fijo. El difusor eleva la presión
   total, pero aparece resistencia de entrada `V_inf`: el empuje bruto y el
   neto no varían de la misma manera.
4. Prueba `PCI=1000`: el solucionador rechaza el balance para alcanzar T3
   si el denominador es negativo, sin devolver un consumo ficticio.

## 7. Limitaciones honestas

El modelo utiliza el mismo aire equivalente para compresor, cámara, turbina y
tobera: se ignora el cambio real de `cp`, `R`, `gamma`, entropías de mezcla,
química y gases quemados. El tratamiento del PCI requiere la referencia de
entalpía explicada. No se calcula dosado estequiométrico ni temperatura de
llama adiabática química. La recuperación del difusor y pérdidas son factores
prescritos; vuelo solo subsónico e ISA simplificada hasta 20 km. No se calcula
gasto de combustible absoluto, emisiones ni rendimiento propulsivo.

Fuentes para interpretar conceptos, sin incorporar sus correlaciones:
[NASA Burner Thermodynamics](https://www.grc.nasa.gov/www/k-12/airplane/burnth.html),
[NASA Specific Fuel Consumption](https://www.grc.nasa.gov/www/k-12/airplane/sfc.html),
[NASA Fuel Mass Flow Rate](https://www.grc.nasa.gov/www/BGH/fuelfl.html).
