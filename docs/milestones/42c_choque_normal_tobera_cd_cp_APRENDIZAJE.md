# Aprendizaje 42.C — Choques normales dentro de una tobera C-D

## 1. ¿Qué es un choque normal?

Una onda de choque normal está perpendicular a la corriente local y
representa una compresión rápida. El gas llega supersónico (`M1>1`),
atraviesa el choque y sale de él subsónico (`M2<1`). No es una expansión
isentrópica: genera entropía incluso si suponemos flujo adiabático y
ausencia de trabajo externo.

El impulso `p+rho*V²` se mantiene entre las dos caras de la sección
cuasiunidimensional, al igual que el flujo superficial `rho*V` y la
entalpía de remanso `h+V²/2`. En este simulador, la entalpía está en
**kJ/kg** y por eso se emplea `V²/2000`; la presión está en **kPa**
y por eso el término `rho*V²` se divide entre `1000`.

## 2. ¿Por qué aparece en una C-D?

Una vez bloqueada la garganta, el divergente acelera la corriente hasta
supersónico si puede expandirse isentrópicamente. Si la contrapresión
exterior es suficientemente elevada para impedir esa salida ideal, el
flujo puede ajustarse mediante un choque normal dentro del divergente.
Tras el choque, la corriente se desacelera de forma subsónica al aumentar
el área. La posición ajustable es `Achoque/Ag` y está entre `1` y `Ae/Ag`.
Sin una relación entre área y longitud `A(x)` **no conocemos los metros**
desde la garganta hasta el choque.

## 3. Choque interno y en la salida

- **Choque en la salida:** `Achoque/Ag=Ae/Ag`. Hasta el borde hay
  expansión supersónica; el salto ocurre allí mismo.
- **Choque interno:** `1<Achoque/Ag<Ae/Ag`. El gas se comprime dentro del
  divergente y continúa hasta la salida a Mach subsónico.
- **Rama subsónica no bloqueada:** una contrapresión aún más alta puede
  hacer que la garganta ya no alcance Mach 1.

Al acercarse el choque a la garganta, su intensidad tiende a cero.
La transición límite debe calcularse cuidadosamente: no se inventa
una raíz supersónica cuando `M1≈1`.

## 4. Segunda ley y caída de presión total

La energía de remanso se conserva: `h(Tt1)=h(Tt2)`. Como la temperatura
total es la misma y la entropía crece, la presión total necesariamente
disminuye. Con el gas ideal del modelo:

`s(T,p) = s0(T) - R*ln(p/100 kPa)`.

El estado posterior tiene mayor entropía aunque su energía total no haya
cambiado. La presión estática puede aumentar mucho durante el choque,
pero la **presión total** disminuye: son conceptos distintos.

## 5. Cómo lo resuelve Python

En `choque_normal_cp.py`, `resolver_choque_normal(T1,p1,V1,*,tolerancia=1e-9)`
recibe tres números físicos y una tolerancia opcional por palabra clave.

1. Calcula `M1`, `rho1`, `j=rho1*V1` y `H=h(T1)+V1²/2000`.
2. Calcula el Mach sónico compatible con la energía total `H`.
3. Para cada temperatura candidata `T2`, calcula `V2` por energía y
   `p2` por momento.
4. Evalúa la continuidad `rho2*V2-j` como **función residual**.
5. Biseca la raíz **subsónica** dentro de un intervalo con signos opuestos.
6. Comprueba que `M2<1`, `s2>s1`, `pt2<pt1` y los tres residuos son pequeños.

La palabra `dict` representa los resultados con nombres (`'T2'`, `'M2'`,
`'residuos'`) y `None` expresa una magnitud no calculable, nunca cero.
El bloque `try/except` del solucionador C-D sólo captura errores físicos
y numéricos previstos, sin ocultar errores de programación.

## 6. Cómo localizamos el choque

`_salida_tras_choque` usa la expansión supersónica existente hasta
`Achoque/Ag`, llama al solucionador nuevo y continúa isentrópicamente con
la menor presión total posterior. Obtiene así la presión de escape para
cada ubicación candidata. `_choque_en_divergente` primero comprueba que
la contrapresión objetivo está entre los valores de los extremos;
después biseca el área hasta ajustarla.

La bisección **no funciona por magia**: necesita que los extremos
encierren la raíz. Es la misma lección aprendida al corregir la calculadora
de adaptación del milestone 42.B.

## 7. ¿Cómo obtenemos el empuje?

En cada salida físicamente resuelta:

`F_específico_tobera = Ve + 1000*(pe-p_amb)/(rho_e*Ve)`.

En el turborreactor, la masa de gas aumenta por combustible (`1+f`) y
además hay que restar la velocidad de entrada `V∞` para el empuje neto.
Sólo cuando `Fs_neto>0` se presenta `TSFC=3600*f/Fs_neto`.
Un choque disminuye generalmente las prestaciones, aunque su efecto
depende del estado de operación.

## 8. Experimento guiado

Con `Tt=1200 K`, `pt=500 kPa`, `Ae/Ag=1.5`:

| p exterior [kPa] | Régimen | A choque / Ag | Mach de escape |
| ---: | --- | ---: | ---: |
| 100 | Supersónico ideal | — | 1.82457 |
| 312.5526 | Choque en salida | 1.5 | 0.60473 |
| 350 | Choque interno | 1.36206 | 0.54316 |
| 400 | Choque interno | 1.18237 | 0.47788 |
| 480 | Subsónico no bloqueado | — | 0.24891 |

La visualización destaca puntos con choque resuelto sin expulsarlos de
los mapas ni de Pareto si el empuje neto es positivo. La calculadora
de adaptación 42.B sigue representando la **expansión ideal isentrópica**.

## 9. Qué se ha verificado y qué falta validar

En la corrección final distinguimos dos cantidades diferentes:

- **Generación de entropía**: aumento real debido a irreversibilidad en
  el choque normal; debe ser positivo y tiene unidades kJ/(kg·K).
- **Residuo de entropía**: diferencia numérica entre la entropía de salida
  y la del remanso **posterior** al choque (misma presión total `pt2`);
  debe aproximarse a cero porque ese último tramo es isentrópico.

Para geometrías `Ae/Ag` muy próximas a uno, el intervalo físico de
contrapresiones de choque interno se estrecha. Las tolerancias se limitan
por esa anchura, además de por la escala absoluta de presión. Si la
precisión no permite separar dos fronteras, se reconoce un límite
degenerado sin inventar precisión. La nueva prueba web compara los valores
renderizados del choque con los del módulo científico y sus unidades.

Se verifican las ecuaciones de conservación, la segunda ley, los extremos
de la rama, el cierre de presión y la comparación aproximada con relaciones
de salto para gas caloríficamente perfecto. Estas últimas no sustituyen
`cp(T)` variable porque la capacidad calorífica cambia con la temperatura.

Para **validación experimental**, harían falta mediciones reales de
presión total, presión de salida, Mach y posición del choque en una tobera
de geometría conocida; esas mediciones no forman parte de este milestone.
El flujo 1D excluye choques oblicuos, fricción y separación.

La regresión global final verificó **604 casos**: 603 correctos,
uno omitido por Cantera no disponible, cero fallos. Incluye las once
pruebas específicas del módulo 42.C, también superadas por separado.

Referencias: [NASA Glenn, choque normal](https://www.grc.nasa.gov/WWW/BGH/normal.html)
y [NACA Report 1135](https://www.nasa.gov/wp-content/uploads/2023/03/equations-tables-charts-compressibleflow-report-1135.pdf).
