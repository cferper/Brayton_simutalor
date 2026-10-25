# Milestone 35 — Tobera convergente con cp(T) y empuje específico estático

## Estado anterior

La rama `mejoras/cp-variable` partía de `2300aabcc6bb56c2b638238925dd2427f2123946`: un núcleo monoeje calculaba la presión y temperatura en la salida de la turbina, pero no tenía tobera ni empuje. El Brayton clásico y su dashboard permanecen separados.

## Qué se ha añadido

El módulo autónomo `tobera_cp_variable.py` resuelve una expansión convergente en aire de composición fija y cp(T), identifica bloqueo sónico, calcula velocidad, densidad, área por caudal y empuje específico como suma de cantidad de movimiento y presión. `resolver_nucleo_con_tobera(...)` encadena el núcleo de milestone 34 sin cambiar su contrato. No hay caudal absoluto, combustible, vuelo, TSFC, tobera convergente-divergente ni interfaz nueva.

## Nuevos conceptos de ingeniería

**Convención remanso/estático.** Los estados termodinámicos del milestone 34 no incorporan energía cinética ni presión dinámica; interpretamos su estado 4 como **remanso** de entrada de tobera, hipótesis adicional equivalente a despreciar la velocidad axial en ese plano y las pérdidas del conducto hasta tobera. No es una igualdad universal entre estado estático y de remanso en una turbina real. La temperatura y presión de salida de la tobera sí son **estáticas**.

Para una presión estática de salida propuesta `pe`, el estado isentrópico ficticio satisface `s(Tes,pe)=s(Tt,pt)`. La caída real se modela por `h_e=h_t-eta_n*(h_t-h_es)`, `Ve=sqrt(2000*(ht-he))` en m/s, y `Me=Ve/sqrt(gamma(Te)*R_AIRE*Te)`. En esta definición efectiva de eficiencia, se calcula una raíz numérica `Me=1` en la temperatura isentrópica de referencia, dentro de 200–2000 K; NO se utiliza una presión crítica exacta de gamma constante. Si `pamb>=pcrit`, `pe=pamb` y la salida es subsónica o justo crítica; si `pamb<pcrit`, `pe=pcrit` y `Me=1`, con exceso de presión que puede generar empuje adicional. Cuando la condición sónica no está representable en el intervalo de temperaturas y sí lo está el estado ambiente, solo se calcula el régimen subsónico válido.

Continuidad: `rho_e=1000 pe/(R_AIRE Te)` kg/m³, `Ae/mdot=1/(rho_e Ve)` m²/(kg/s). Para estático y caudal de aire conservado, `Fs=Ve+1000(pe-pamb)/(rho_e Ve)` en N/(kg/s), numéricamente m/s. Este segundo término es positivo cuando la tobera convergente está bloqueada y `pe>pamb`, y cero cuando adapta su presión a ambiente. No hay empuje absoluto sin mdot. El área/caudal es una consecuencia del punto de salida y no define una geometría diseñada: en bloqueo la continuidad proporciona el área de garganta necesaria para transportar el caudal elegido.

El modelo de pérdidas es de eficiencia entálpica **efectiva**, sin distribución espacial de irreversibilidades ni variación de presión de remanso; la condición M=1 se impone coherentemente sobre su estado estático calculado. No constituye un mapa de tobera real. Las expresiones analíticas de gamma constante, como `pcrit/pt=(2/(gamma+1))^(gamma/(gamma-1))`, son solo referencias aproximadas para el caso reversible.

## Nuevos conceptos de Python

El algoritmo evalúa propiedades por sus funciones existentes, invierte entropía y entalpía con bisectores, y usa una segunda bisección acotada para el Mach crítico. Devuelve un diccionario con estados, aportaciones al empuje, residuos de energía/isentropía y diagnóstico. Rechaza `pt<=pamb`, rendimientos inválidos y velocidades prácticamente nulas; `EstadoFueraDeRango` identifica temperaturas que exigirían extrapolación; `ErrorNumericoCiclo` distingue contradicciones y falta de convergencia. No se ocultan resultados no representables.

## Qué hemos aprendido y verificación

Una tobera convergente no continúa acelerando indefinidamente al reducir el ambiente: aparece el bloqueo, fijando la presión de salida a la crítica, mientras el desajuste residual contribuye al empuje por presión. Las pruebas `tests/test_tobera_cp_variable_35.py` examinan régimen subcrítico, crítico, continuidad, pérdidas, unidades, frontera térmica, referencia analítica e integración con milestone 34; el workflow CI repite la suite vigente. Las pruebas verifican implementación y relaciones del modelo, **no validan un motor con mediciones**.

Referencias técnicas: [NASA Glenn — Thrust Equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/thrust-force/) y [NASA Glenn — Thrust Equations Summary](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/thrust-equations-summary/).

## Limitaciones

Gas ideal de aire fijo, sin combustible ni mezcla, calor externo idealizado, flujo estacionario unidimensional, sin geometría ni pérdidas aerodinámicas detalladas, sin caudal absoluto, sin vuelo ni TSFC. Temperaturas restringidas a 200–2000 K. Tampoco calcula shocks, separación ni tobera CD.
