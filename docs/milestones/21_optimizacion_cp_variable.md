# Fase 2C — Viabilidad y optimización Brayton con cp(T)

Base verificada en GitHub: `76aef1973ba1d655f584386ed41d59259c326047`, rama `mejoras/cp-variable` (24/10/2026). Desarrollo independiente, sin Flask ni HTML.

## Contrato científico

`estudiar_cp_variable(T1,T3,p1=100.,eta_c=.85,eta_t=.9,delta=.05,*,tolerancia=1e-9,muestras=160)` usa el solucionador de 2B. Temperaturas K, presión kPa, trabajo kJ/kg, rendimiento adimensional.

El cálculo primero limita `x=ln(rp)` por expansión efectiva, `T2<=2000`, `T4s>=200`, aporte de calor `h3-h2>0` y rechazo `h4-h1>0`. No extrapola Shomate y retorna `tipo='sin_motor'` si los límites no se intersectan o el máximo trabajo no es positivo. Las fronteras del conjunto motor son abiertas. Un óptimo interior es un punto alcanzado; un supremo en frontera se informa sin asignar `rp` óptimo.

La función de trabajo es estrictamente cóncava en `x`: `dw/dx=R_kJ(eta_t*T4s-T2s/eta_c)`. Como `dT4s/dx<0` y `dT2s/dx>0`, su derivada decrece. El signo de la derivada en ambos extremos decide si existe un máximo interior; sólo entonces se resuelve la raíz de la derivada por bisección. Si la derivada sigue siendo positiva al alcanzar una frontera abierta, A se clasifica como supremo y no como máximo. Las raíces de trabajo neto se localizan también mediante bisección. El antiguo auxiliar de sección áurea sigue disponible para comparaciones en tests, pero no decide el máximo A.

Para B, con `q_in=h3-h2`, `q_out=h4-h1`, `a=R_kJ*T2s/eta_c` y `b=R_kJ*eta_t*T4s`, la derivada de eta tiene el signo de `F=b*q_in-a*q_out`. En el dominio con ambos calores positivos, `F'=b'*q_in-a'*q_out<0`, lo que permite buscar como máximo una raíz: si existe, da el máximo global interior; si no, el mejor rendimiento sólo se aproxima a una frontera abierta. El parámetro `muestras` se reserva para compatibilidad y controles de discretización; la búsqueda certificada utiliza cotas y raíces, no máximo de malla.

## Caso base no ideal

`T1=288.15 K, T3=1600 K, p1=100 kPa, eta_c=.85, eta_t=.9, delta=.05`:

- Dominio motor: `1.069645 < rp < 229.221073`.
- Objetivo A: `rp≈15.87795`, `w_neto≈414.08583 kJ/kg`, `eta≈0.39052`.
- Objetivo B: `rp≈46.81910`, `eta≈0.43745`, `w_neto≈347.74304 kJ/kg`.

## Verificación y límites

Se ejecutaron **13/13 pruebas específicas correctas** (24/10/2026) con los módulos `propiedades_aire.py` y `ciclo_cp_variable.py` recuperados íntegros de GitHub, con SHA Git `f7ab17eae7498f400115419d8e08a0e257f176c8` y `a71bbbb7b666e8008c4ee16070e8657cdb3e17e5`, respectivamente, con casos motores y no motores, invariantes energéticos, reversibilidad, frontera abierta, estabilidad de muestras, máximo frente a barrido de 500 puntos y controles numéricos. La ejecución se realizó con archivos 2A/2B exactamente idénticos a los blobs publicados; no equivale a verificar toda la aplicación. Suite Flask histórica: no ejecutada. No se realiza validación experimental.

El método admite aire ideal de composición fija N₂/O₂/Ar y propiedades válidas sólo de 200 a 2000 K. No representa química, mapas de turbomáquinas, recuperación de calor ni pérdidas mecánicas. Un dominio sin motor no equivale a un error numérico. Se requiere contrastar los tests contra el repositorio íntegro antes de publicar si no está disponible una copia exacta.

## Fronteras térmicas y naturaleza de A

En el dominio motor normal, el límite inferior de expansión tiene trabajo de turbina nulo y trabajo neto negativo (salvo caso degenerado). En la frontera de aporte de calor nulo, `w = -q_out < 0` si se exige `q_out>0`. Cuando limita `T4s=200 K`, `w'(x)=R_kJ*(eta_t*200 - T2s/eta_c) <= 0`, pues `T2s>=T1>=200 K` y `eta_t<=1<=1/eta_c`. La frontera de compresor `T2=2000 K` no antecede a `q_in=0` dado `T3<=2000 K`. Por tanto, bajo todas estas hipótesis, **si existe dominio motor, A necesariamente tiene máximo interior**; el camino alternativo `supremo_frontera` se conserva defensivamente ante cambios posteriores de restricciones, sin denominarlo máximo. No se exhibe un caso físico de supremo de A porque no lo permite este conjunto de hipótesis.

Para B, la prueba de `F'<0` exige que `q_in>0`, `q_out>0`, `eta_c,t>0`, sentido nominal de las máquinas, composición fija y gas ideal con `cp(T)>0`. No se extrapola la unicidad fuera de ese dominio. Para el ciclo reversible, B presenta un **supremo**, no un máximo interior.