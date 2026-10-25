# Milestone 39 — Verificación científica independiente del turborreactor cp(T)

## Estado anterior y alcance

Base remota verificada el 25-10-2026: `66a35f9dfae9078b97c58ec7c796492ff94b1351`
en `mejoras/cp-variable`. Los módulos 34–38 producían compresor, combustor
energético, turbina, tobera, vuelo subsónico, empuje y mapas paramétricos.
La referencia de regresión era 493 pruebas (485 correctas, 8 omitidas).

La fase 39 audita ecuaciones, contrasta un **modelo de gas caloríficamente
perfecto implementado aparte** y añade pruebas de límites y mapas. No se
han modificado las ecuaciones de los módulos físicos 34–37; no hay nueva
capacidad termodinámica ni integración Flask.

## Matriz de ecuaciones auditadas

| Componente | Ecuación/criterio de producción | Referencia independiente y observación |
|---|---|---|
| Compresor | `p2=p1*rp`; `s(T2s,p2)=s(T1,p1)`; `eta_c=(h2s-h1)/(h2-h1)`; `wc=h2-h1` | Gas perfecto: `T2s=T1*rp^((gamma-1)/gamma)` y `T2=T1+(T2s-T1)/eta_c`; cp variable exige inversión de s/h |
| Cámara | `h2+f*eta_b*PCI=(1+f)*h3` | Se despeja algebraicamente `f=(h3-h2)/(eta_b*PCI-h3)`; referencia de `h(298.15 K)=0` y combustible sensible nulo **en esa misma referencia** |
| Turbina | `eta_m*(1+f)*(h3-h4)=wc`, `eta_t=(h3-h4)/(h3-h4s)`, `s(T4s,p4)=s(T3,p3)` | Gas perfecto: `T4=T3-wc/[cp*eta_m*(1+f)]`, `T4s=T3-(T3-T4)/eta_t`, `p4=p3*(T4s/T3)^(gamma/(gamma-1))` |
| Tobera | `ht-he=Ve²/2000`, `M=Ve/sqrt(gamma(Te)*R*Te)`; se busca Mach 1 | Gas perfecto: Te real = `Tt/[1+gamma*R/(2000*cp)]` en Mach=1 (cp en kJ/kg/K). Presión crítica deducida de Tes y entropía constante; continuidad verificada cerca de pcrit |
| Vuelo y difusor | `Vinf=M sqrt(gamma(T)*R*T)`, `h(Tt0)=h(T)+Vinf²/2000`, igualdad s en remanso, `pt2=pi_d*pt0` | Gas perfecto: `Tt0=T*(1+(gamma-1)M²/2)` y `pt0=p*(Tt0/T)^(gamma/(gamma-1))`; se diferencia p total de entrada del p exterior estático |
| Empuje y TSFC | `Fs=(1+f)*Ve-Vinf+(1+f)*1000*(pe-pinf)/(rho*Ve)`; `TSFC=f/Fs` | Balance de cantidad de movimiento, continuidad, kPa→Pa (factor 1000), hora→segundo (factor 3600). Solo TSFC con Fs positivo |
| Mapas | Estados físicos; Pareto `Fs↑` y `TSFC↓`, mejora estricta en ≥1 | Dataset sintético con Pareto conocido y máximos/mínimos independientes; Mach–altitud no admite Pareto global entre ambientes diferentes |

No se deduce que dos modelos correctos con distinto cp deban producir
exactamente la misma temperatura, gasto ni prestaciones.

## Referencia analítica y métricas

Implementada en `tests/test_verificacion_independiente_turborreactor_39.py`
como `referencia_perfecta(...)`: no llama a solucionadores ni inversores de
producción. Define `cp=1.08 kJ/(kg K)` constante y mantiene
`R=R_AIRE` del gas equivalente; por coherencia, `gamma=cp/(cp-R/1000)`.
La entalpía es `cp*(T-298.15)` y no una función de propiedades variables.

Para cada magnitud se reporta:

\[
\varepsilon_{abs}=|x_{cp(T)}-x_{ref}|,\qquad
\varepsilon_{rel}=\frac{\varepsilon_{abs}}{|x_{ref}|}\times100\%.
\]

La tabla reproduce los casos A (estático 288.15 K/100 kPa), B (mismas
condiciones con Mach .7 y pi_d .97) y C (ISA 10000 m, Mach .5, pi_d .98),
con `rp=10`, `eta_c=.85`, `T3=1600 K`, `delta=.04`, `eta_t=.9`, `eta_m=.98`,
`eta_n=.95`, `eta_b=.99`, `PCI=43000 kJ/kg`.

| Caso | Magnitud | cp(T) | Gas perfecto cp constante | Error absoluto | Error relativo |
|---|---|---:|---:|---:|---:|
| A | T2 [K] | 597.692837 | 574.244525 | 23.448311 K | 4.0833 % |
| A | f [kg/kg] | 0.028028208 | 0.026912250 | 0.001115958 | 4.1467 % |
| A | p4 [kPa] | 415.514766 | 419.628386 | 4.113620 kPa | 0.9803 % |
| A | Ve [m/s] | 662.729111 | 659.910765 | 2.818346 m/s | 0.4271 % |
| A | Fs [N/(kg/s aire)] | 958.257683 | 945.391986 | 12.865698 | 1.3609 % |
| A | TSFC [kg/(N h)] | 0.105296884 | 0.102480348 | 0.002816536 | 2.7484 % |
| B | T2 [K] | 653.400115 | 625.163935 | 28.236181 K | 4.5166 % |
| B | f [kg/kg] | 0.026596503 | 0.025576302 | 0.001020201 | 3.9889 % |
| B | p4 [kPa] | 510.069350 | 515.059258 | 4.989908 kPa | 0.9688 % |
| B | Ve [m/s] | 656.469917 | 653.456467 | 3.013449 m/s | 0.4612 % |
| B | Fs [N/(kg/s aire)] | 752.661603 | 742.120041 | 10.541562 | 1.4205 % |
| B | TSFC [kg/(N h)] | 0.127211763 | 0.124069803 | 0.003141960 | 2.5324 % |
| C | T2 [K] | 489.299648 | 464.827154 | 24.472494 K | 5.2649 % |
| C | f [kg/kg] | 0.030764617 | 0.029782981 | 0.000981636 | 3.2960 % |
| C | p4 [kPa] | 151.396017 | 152.870261 | 1.474244 kPa | 0.9644 % |
| C | Ve [m/s] | 674.489940 | 673.515539 | 0.974401 m/s | 0.1447 % |
| C | Fs [N/(kg/s aire)] | 895.165541 | 884.446835 | 10.718706 | 1.2119 % |
| C | TSFC [kg/(N h)] | 0.123723059 | 0.121226880 | 0.002496180 | 2.0591 % |

Ambos modelos predicen tobera **bloqueada** en los tres casos. Las diferencias
son principalmente **de modelo** (cp variable frente a constante), no errores
por falta de cierre de las ecuaciones. El valor constante de cp es una
referencia elegida para la prueba, no ajuste exacto de aire caliente.

## Verificación de límites y residuos

- Compresor/turbina ideales, `eta_m=1`, `pi_d=1`, `eta_n=1`: se recuperan
  los límites reversibles aplicables; el residuo de eje es despreciable.
- A `PCI=10^12 kJ/kg` (exclusivamente **límite matemático**) `f→0` y se
  recupera el empuje del modelo anterior sin combustible.
- Cerca de presión crítica `pcrit*(1±10^-6)` se verifica la transición
  continua entre Mach 1 y flujo subsónico en tobera convergente.
- A Mach .9, rp 3, pi_d .7, T3=500 K no hay margen de presión; a T3=600 K
  el modelo devuelve `Fs=-137.6369 N/(kg/s aire)` y TSFC no definido.
- En `T3=200 K` el aporte térmico es inadmisible; `T3=2000 K` es un límite
  **cerrado** que se acepta o rechaza según el estado calculado.
- El cierre energético de cámara, eje, inversión isentrópica y tobera se
  comprueba dentro de las tolerancias numéricas de las pruebas.

## Hallazgo puntual en milestone 38 y corrección

**Error de implementación, impacto bajo en los óptimos publicados:**
`exigir_empuje_positivo` y `exigir_margen_tobera` se aceptaban, pero no
intervenían en la salida. Se conserva el significado físico de `estado` y
el contrato previo, y se añade por punto **`cumple_restricciones`** y por
mapa **`cumplen_restricciones`**. Los indicadores ahora gobiernan ese
filtro de elegibilidad declarada, sin alterar `estado`:

- `Fs<=0` cumple el filtro solo si `exigir_empuje_positivo=False`.
- Sin expansión se requiere relajar **ambas** restricciones, porque no
  se puede certificar empuje positivo sin resolver la tobera.
- Una configuración sin TSFC positivo definido no entra jamás en máximos,
  mínimos ni Pareto, incluso si el filtro está relajado.

Los casos reales anteriores verifican la distinción: ambos son descartados
por el filtro estricto y ambos pasan un filtro completamente relajado, pero
no se convierten en puntos `valido`. El nuevo campo distingue claramente
*cumplir condiciones prescritas* de *ser elegible para optimizar empuje y
consumo*. Los 34–37 y los valores de objetivos positivos del 38 no cambian.

## Grupo Cantera opcional

`test_propiedades_cantera_opcional` usa `importlib.util.find_spec` y
`@skipUnless`: si Cantera falta, la prueba queda omitida explícitamente.
Al instalarlo opcionalmente, intenta `air.yaml` con N2/O2/AR en composición
molar 0.78/0.21/0.01. Compara `cp` en J/(kg K) y *diferencias* de h/s
armonizadas a 298.15 K con las unidades SI de Cantera. Coeficientes de
ajuste y referencias químicas diferentes pueden producir discrepancias.
No se usa Cantera en los módulos de producción ni en `requirements.txt`.

## Clasificación final de discrepancias

| Clase | Hallazgo | Importancia / acción |
|---|---|---|
| Implementación | Banderas `exigir_*` inertes en M38 | Corregido de forma compatible, sin alterar estados físicos ni objetivos |
| Numérico | Sin inestabilidad significativa en los casos de auditoría | Seguimiento en límites y correlaciones |
| Diferencia de modelo | Gas perfecto constante vs cp(T), errores hasta ~5.3 % en T2 de casos reproducibles | Esperable; no extrapolar como error físico |
| Limitación conocida | Gas equivalente sin química, rendimientos prescritos, sin fuera de diseño real | Etiquetada; no corregida por estar fuera de alcance |
| Pendiente de validación | Datos experimentales de motor/cámara/tobera y comparaciones de propiedades Cantera no ejecutadas | Requiere fuentes/datos independientes y validación adicional |

## Referencias externas oficiales

- [NASA Glenn — Burner Thermodynamics](https://www.grc.nasa.gov/www/k-12/airplane/burnth.html): ecuación de cámara con f y factor de eficiencia.
- [NASA Glenn — Specific Fuel Consumption](https://www.grc.nasa.gov/www/k-12/airplane/sfc.html): TSFC como caudal de combustible por empuje.
- [NACA/NASA — Performance Charts for a Turbojet System](https://ntrs.nasa.gov/citations/19930093534): variables de ciclo y prestaciones; sus hipótesis no sustituyen al modelo actual.
- [Cantera — Thermodynamic Properties](https://cantera.org/stable/python/thermo.html) y [Python Tutorial](https://cantera.org/stable/userguide/python-tutorial.html): API de mezcla ideal, cp/h/s y unidades.

## Conclusiones y trabajo científico pendiente

Se han contrastado algebraicamente balances y un modelo analítico ajeno al
software de producción; las predicciones cp(T) difieren del gas perfecto por
las hipótesis empleadas, sin indicios de defecto grave en 34–37. **Esto es
verificación, no validación experimental.** Serían necesarios datos de
producto de combustión, mapas de turbomáquinas, geometría, gasto másico y
validación externa para realizar predicción real de prestaciones.

## Pruebas y publicación

La ejecución específica M39 contiene 12 métodos (uno opcional Cantera, omitido
cuando falta). Los resultados de la suite completa y CI constarán en el
informe final. El commit asociado queda pendiente hasta su publicación.
