# Milestone 42.A — Tobera convergente-divergente ideal con cp(T)

## Estado anterior

Base comprobada: rama `mejoras/cp-variable`, commit `7a8ce0c87247a9cb1b52a855b68e2167397b6713`, árbol limpio. La tobera del milestone 35 es convergente, con eficiencia opcional; se conserva sin cambios. La suite de referencia tiene 557 pruebas (548 correctas, 9 omitidas).

## Qué se ha añadido

`tobera_convergente_divergente_cp.py` es un solucionador **independiente** y reversible de una tobera C-D de aire seco ideal de composición fija con cp(T). Acepta `Tt` [K], `pt` y `p_amb` [kPa] y `epsilon=Ae/Ag` [-]; no acepta eficiencia no ideal. Devuelve estados estáticos, diagnósticos, residuos y empuje **específico** [N/(kg/s) = m/s]. No cambia las ecuaciones de los milestones 34–41 ni añade interfaz o gastos másicos absolutos.

## Hipótesis, unidades y ecuaciones

- Flujo 1D estacionario, adiabático, sin trabajo, isentrópico solamente fuera de choques, sin fricción, pérdidas totales o separación; `eta_n=1` implícito.
- Aire de `propiedades_aire.py`: `200<=T<=2000 K`, R=R_AIRE [J/(kg K)], h [kJ/kg], s [kJ/(kg K)], presiones [kPa]. El fluido de combustión real **no** se simula.
- `h(Tt)=h(T)+V²/2000`; `s(T,p)=s(Tt,pt)`; `p=pt exp[(s0(T)-s0(Tt))/(R/1000)]`.
- `a=sqrt(gamma(T)*R*T)` [m/s], `M=V/a`, `rho=1000p/(RT)` [kg/m³] y `G=rho V` [kg/(m² s)].
- Garganta crítica: encontrar `M=1` por bisección en temperatura; `G*=rho* a*` (el asterisco designa el estado sónico).
- Si está bloqueada, `Ag=A*` y `epsilon=G*/Ge`. En flujo **no** bloqueado, `Ag>A*`: se recupera la temperatura de salida desde p ambiente y se halla la garganta subsónica usando `Gg=epsilon Ge`.
- Empuje específico ideal en estados resueltos: `Fs=Ve+1000(pe-p_amb)/(rho_e Ve)` [N/(kg/s)]; conserva el término de presión con signo. **No es empuje total en N ni empuje neto de un turborreactor completo.**

## Algoritmos y condiciones de existencia

1. Validación estricta de cuatro reales finitos (sin `bool`), `200<Tt<=2000`, `pt>p_amb>0` y `epsilon>=1`.
2. Bisección del estado crítico si `M(T_MIN)>=1`. Si no existe, solo puede resolverse una rama no bloqueada representable en el intervalo de propiedades.
3. Bisección de la raíz **subsónica** de `Ge=G*/epsilon` para obtener el umbral de contrapresión de comienzo de bloqueo; por encima, solución subsónica mediante `pe=p_amb` y continuidad en garganta. En el límite la garganta es sónica y la salida sigue subsónica.
4. Por debajo del umbral, raíz **supersónica** distinta de `Ge=G*/epsilon`. Si se requiere `Te<200 K`, se lanza `EstadoFueraDeRango` en vez de extrapolar.
5. **Choques:** se calcula una referencia orientativa `p2,exit≈pe[1+2 gamma(Te)(Me²-1)/(gamma(Te)+1)]`, que *no* es una solución de choque con cp(T), pues congela localmente gamma. Si `p_amb` alcanza esa referencia, se responde `resuelto=False`, régimen `choque_interno_o_salida_no_resuelto` y salida, Mach, residuos y empuje `None`. No se predice el punto del choque, su efecto termodinámico ni la rama subsónica posterior. La frontera diagnóstica es **aproximada y no apta para diseño**.
   **La garganta sí permanece definida**: temperatura, presión, densidad, velocidad y Mach=1 se conservan porque el bloqueo ya se ha determinado antes del posible choque aguas abajo. Los residuos que necesitan conocer la salida siguen siendo `None`.
6. En sobreexpansión por debajo del umbral aproximado se informa `supersonico_sobreexpandido_ideal`: el estado interior es la hipótesis isentrópica, **no** una predicción de separación, estabilidad o estructura de choques fuera de la tobera. El ajuste de presión externo no se simula.
7. La adaptación supersónica se obtiene mediante `relacion_areas_adaptada(Tt,pt,p_amb) = G*/Ge` solo para salida `M>1` representable. Para contrapresión subsónica o temperaturas fuera del dominio, excepción controlada.

Las tolerancias son 1e-9 K en bisección, 1e-6 del máximo de presiones totales/ambiente para adaptación, y 1e-6 relativo en el diagnóstico de choque aproximado. Estas tolerancias son criterios numéricos, no incertidumbres físicas.

**Validación numérica reforzada:** `_validar()` comprueba los tipos y captura `OverflowError`, `TypeError` y `ValueError` de la comprobación de finitud. Así, incluso `10**10000` en cualquiera de las cuatro entradas produce un `ValueError` explícito y no una excepción de conversión inesperada.

## Casos reproducibles

Entradas comunes: `Tt=1200 K`, `pt=500 kPa`, `epsilon=relacion_areas_adaptada(1200,500,70)=1.652764798`, aire cp(T) fijo. `M_g` y `M_e` adimensionales; `Ve` y `Fs` en m/s=N/(kg/s). Todos los números corresponden a la ejecución local del módulo.

| p ambiente [kPa] | Régimen | M garganta | M salida | p salida [kPa] | Ve [m/s] | Fs [N/(kg/s)] |
|---:|---|---:|---:|---:|---:|---:|
| 40 | Supersónica subexpandida ideal | 1.000000 | 1.939449 | 70.000000 | 1033.989343 | 1120.524064 |
| 70 | Supersónica adaptada ideal | 1.000000 | 1.939449 | 70.000000 | 1033.989343 | 1033.989343 |
| 140 | Supersónica sobreexpandida **ideal** | 1.000000 | 1.939449 | 70.000000 | 1033.989343 | 832.074996 |
| 400 | Choque interno/salida posible: **no resuelto** | — | — | — | — | — |
| 480 | Subsónica no bloqueada | 0.444129 | 0.248913 | 480.000000 | 167.268622 | 167.268622 |

En el caso sobreexpandido, el término de presión es **−201.914348 N/(kg/s)**; en el subexpandido **+86.534720**. La presión posterior estimada de un choque normal en la salida ideal es ≈292.887710 kPa **solo como umbral aproximado**. En el caso no resuelto no se conocen estados de garganta/salida reales, y no se usa la rama matemática como predicción.

## Verificación y alcance

`tests/test_tobera_convergente_divergente_42a.py` separa balances y límites internos de una referencia analítica independiente de gas perfecto (relación área–Mach con gamma constante). Esa referencia ahora invierte **por bisección propia**, sin invocar producción, la fórmula de área–Mach para calcular un Mach supersónico independiente. La tolerancia del 3 % permite diferencias por cp(T) frente a cp fijo a temperatura moderada, no representa incertidumbre experimental. Se prueban además enteros gigantes en las cuatro entradas, conservación de estado crítico con choque no resuelto y clasificación a ambos lados del **umbral aproximado**, sin declararlo exacto. También se comprueba la tobera M35, sin modificarla.

**Historial de verificación:** antes de estas correcciones, 16 pruebas específicas y 573 globales (564 correctas, 9 omitidas, 0 fallidas). Tras las correcciones, **19 pruebas específicas correctas**; seis archivos de regresión relacionados suman **78 ejecutadas, 77 correctas y 1 omitida**. Suite global ejecutada con Python 3.12, SciPy disponible y Flask/Jinja2 en directorio temporal: **576 pruebas, 575 correctas, 1 omitida opcional (Cantera no instalada), 0 fallidas**. Ocho pruebas de comparación SciPy que antes se omitían se ejecutan en este entorno. Una primera invocación sin configurar la ruta temporal de Flask/Jinja2 falló por importaciones; se corrigió el entorno y la ejecución final pasó por completo. GitHub Actions se comprobará después de publicar.

NASA Glenn Research Center ofrece explicaciones de la garganta crítica y relación área–Mach en [Mass Flow Rate Equations](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/mass-flow-rate-equations/) y [Nozzle Design](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/nozzle-design/); son referencias físicas del gas perfecto, no certificación de este código.

## Limitaciones que siguen existiendo

No se resuelven choques internos, presión de salida real cuando hay choque, capa límite, separación, pérdidas de presión total, transición de regímenes con histéresis, combustión/gases calientes reales, geometrías y gastos absolutos, empuje total ni operación fuera de diseño. El diagnóstico de sobreexpansión usa una cota de choque aproximada: no equivale a un solver de flujo con choque y no valida experimentalmente prestaciones.

## Commit asociado

**Pendiente de revisión y autorización**; ningún commit o push de M42.A realizado.
