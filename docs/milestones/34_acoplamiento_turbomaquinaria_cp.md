# Milestone 34 — Acoplamiento mecánico compresor–turbina con cp(T)

## Alcance

Primer modelo científico independiente de núcleo de turborreactor estático, sin tobera, empuje, adición de combustible ni dinámica de vuelo. Conserva intacto el ciclo Brayton `ciclo_cp_variable.py` y no añade interfaz web. Base: `8ca5fe74519478ab3735763f8c466f0795553445`, rama `mejoras/cp-variable`.

## Hipótesis y balances

Aire ideal seco de composición fija y gasto másico uniforme; proceso estacionario; compresor y turbina adiabáticos; un solo eje sin carga accesoria adicional. El aporte energético de la cámara es exclusivamente `h3-h2` (kJ/kg), con pérdida relativa de presión `delta`. No es combustión química.

1. `p2=p1*rp`, `s0(T2s)=s0(T1)+R ln(rp)`, `h2=h1+(h(T2s)-h1)/eta_c`.
2. `p3=p2*(1-delta)`, `q_in=h3-h2`; se exige `q_in>0`.
3. `wc=h2-h1`; `eta_m*wt=wc`; `h4=h3-wt`. El rendimiento mecánico representa pérdidas del eje, sin modelar su mecanismo.
4. `h4s=h3-wt/eta_t`; `s(T4s,p4)=s(T3,p3)` implica `ln(p4)=ln(p3)+(s0(T4s)-s0(T3))/(R_AIRE/1000)`.

Las temperaturas se recuperan de entalpías con la inversión del modelo cp(T), sin suponer gamma constante; las presiones son kPa y R se transforma de J/(kg K) a kJ/(kg K). `p4` se determina, **no** se impone igual a `p_amb`. Se preserva el signo positivo de trabajos consumido/producido y el residuo `eta_m*wt-wc`.

## Contrato y diagnóstico

`resolver_acoplamiento(T_amb,p_amb,rp,eta_c,T3,delta,eta_t,eta_m)` devuelve un diccionario con las cuatro temperaturas, presiones, entalpías y entropías, estados isentrópicos, trabajos, aporte térmico, rendimientos de eje/turbina, residuos, presión relativa `p4/p_amb`, margen en kPa y `diagnostico_tobera` (`con_margen`, `limite` o `sin_margen`). El límite es una banda relativa de 1e-10 en la razón de presiones; no equivale a un cálculo de empuje. Si la razón es inferior a 1, el núcleo no conserva presión para una expansión en una futura tobera ideal hasta ambiente.

Entradas no finitas, eficiencias fuera de `(0,1]`, `rp<=1`, `delta` fuera de `[0,1)`, calor no positivo o inexistencia de trabajo compresor positivo generan `ValueError`. Las temperaturas fuera de 200–2000 K generan `EstadoFueraDeRango` cuando se llega a invertir un estado. Presiones no representables o incompatibles con expansión positiva producen `ErrorNumericoCiclo`. El resultado nunca inventa un estado fuera del dominio tabulado.

## Verificación y límites

`tests/test_acoplamiento_turbomaquinaria_34.py` comprueba cierre del eje, ideal reversible, evolución con rendimientos, identidades de entalpía, conservación isentrópica, fórmula independiente de presión de gas ideal, presión positiva, diagnóstico a ambos lados del ambiente y entradas imposibles. El contraste cp constante es únicamente una aproximación de referencia con tolerancia explícita. La suite previa se ejecuta sin modificar módulos históricos. Son pruebas de ecuaciones y código, **no validación experimental** de turborreactores.

El modelo no contiene tobera, empuje, TSFC, flujo de combustible, variación de composición, pérdida real de combustión, tomas de aire, velocidad de vuelo ni mapas de componentes; presión disponible no significa empuje garantizado. Revisar visualmente en Windows no aplica a este módulo sin interfaz.
