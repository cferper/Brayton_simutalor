# Milestone 36 — Condiciones de vuelo, difusor y empuje neto cp(T)

## Estado anterior

La rama `mejoras/cp-variable` partía del commit `c1fc5b5d36066d7ec5741b070b0d4721fbc5da69`: el núcleo monoeje (34) y tobera convergente (35) calculaban condiciones estáticas, pero no velocidad de vuelo ni difusión de entrada. El ciclo Brayton histórico, sus contratos y el dashboard no se alteran.

## Qué se ha añadido

Módulo científico `vuelo_cp_variable.py` con ambiente directo o ISA 0–20 km geopotenciales, condiciones de remanso por propiedades variables, difusor adiabático con recuperación de presión, encadenamiento del núcleo y tobera, y cálculo de empuje específico neto. No modela supersónico, shocks, combustible, TSFC ni geometría de entrada.

## Nuevos conceptos de ingeniería

**Atmósfera estándar simplificada**: condiciones de referencia `T0=288.15 K`, `p0=101.325 kPa`, `g0=9.80665 m/s²`, `R_ISA=287.05287 J/(kg K)`, gradiente `L=-0.0065 K/m`. Para `0<=z<=11000 m`: `T=T0+L*z`, `p=p0*(T/T0)^(-g0/(L*R_ISA))`. En `11000<z<=20000 m`: `T=T11=216.65 K`, `p=p11 exp(-g0(z-11000)/(R_ISA*T11))`. Ambos tramos comparten exactamente `T11,p11`, por lo que son continuos. `R_ISA` es constante de la referencia atmosférica, ligeramente distinta de `R_AIRE` del modelo termodinámico de mezcla N2/O2/Ar; esto es una aproximación de estándares acoplados, no un aire real de composición variable. No predice el tiempo meteorológico.

**Flujo y remanso**: `a∞=sqrt(gamma(T∞)*R_AIRE*T∞)` [m/s], `V∞=M∞a∞`, `h(Tt0)=h(T∞)+V∞²/2000` [kJ/kg]. Se obtiene `pt0=p∞exp((s0(Tt0)-s0(T∞))/(R_AIRE/1000))`, que conserva entropía para una desaceleración ideal. En difusor adiabático de salida lenta, `Tt2=Tt0` y `pt2=pi_d*pt0`, con `0<pi_d<=1`; la pérdida de presión total engloba irreversibilidades de la entrada como un parámetro, sin mapa ni mecanismo geométrico. Solo `0<=M∞<1`.

**Acoplamiento correcto**: el argumento `p_amb` del milestone 34 es realmente la presión **de entrada al compresor**; en vuelo se le pasa `pt2`, mientras la presión ambiente de descarga de tobera sigue siendo la estática `p∞`. La copia del diccionario del núcleo recalcula sus campos de diagnóstico `relacion_salida_ambiente`, `margen_presion_kpa`, `diagnostico_tobera` frente a `p∞` y añade `presion_referencia_diagnostico`: no transmite al usuario el diagnóstico anterior calculado frente a `pt2`. La función original del milestone 34 queda inalterada.

**Empuje neto** (sin masa de combustible ni caudal absoluto): `Fs=Ve-V∞+1000(pe-p∞)/(rho_e*Ve)` [N/(kg/s)=m/s]. Se devuelven por separado momento saliente, resistencia de entrada (magnitud positiva que se resta), presión y total. `empuje_neto_positivo=False` si es cero o negativo; nunca se trunca a cero. Si `p4<=p∞`, no existe expansión disponible para el solucionador de tobera 35, por lo que `tobera=None`, `Fs=None` y diagnóstico `sin_expansion_disponible`; no se simula empuje inexistente. Los errores de dominio físico se propagan.

## Nuevos conceptos de Python

Funciones públicas `atmosfera_estandar(z)`, `calcular_remanso(T_estatica,p_estatica,mach)`, `aplicar_difusor(remanso,pi_d)` y `resolver_turborreactor_vuelo(...)`; se reutilizan funciones de entalpía, entropía, gamma, el inversor de entalpía y los dos solucionadores publicados. Se emplean diccionarios con campos estructurados, opciones de entrada excluyentes (`altitud_geopotencial` **o** pareja `T_amb,p_amb`), validadores contra `bool`/NaN/inf y excepciones explícitas. El solucionador de núcleo se invoca una sola vez. No se añaden dependencias.

## Qué hemos aprendido y verificación

El remanso incorpora energía de vuelo y el difusor puede perder presión total sin cambiar la entalpía de remanso. El empuje bruto de la tobera no es el empuje neto del motor en vuelo: hay que descontar `V∞`. Las 12 pruebas nuevas (`test_vuelo_cp_variable_36.py`) comprueban ISA, continuidad a 11 km, conservación, referencia caloríficamente perfecta aproximada, pérdidas, Mach cero, diagnóstico corregido, empuje negativo, falta de expansión, llamada única a núcleo, límites y ausencia de regresiones mediante suite completa. Son pruebas del **modelo y software**, no validación experimental. Las fuentes de referencia atmosférica se documentan en el documento educativo.

## Limitaciones

Atmósfera seca estándar, 0–20 km geopotenciales, gas ideal con composición fija en el motor, eficiencia de difusor prescrita, flujo 1D estacionario, sin ondas de choque, combustible, variación de gasto másico, trabajo accesorio, empuje absoluto o consumo específico. La presión total recuperada y los estados de remanso requieren idealizaciones; comparaciones con prestaciones de motores reales serían validación adicional independiente.
