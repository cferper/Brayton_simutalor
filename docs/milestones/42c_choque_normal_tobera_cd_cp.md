# Milestone 42.C — Choque normal en tobera C-D con cp(T) variable

## Estado anterior

42.A resolvía las ramas isentrópicas C-D; 42.B las mostraba en el
turborreactor. Las contrapresiones compatibles con choque interno
conservaban la garganta, pero no ofrecían el estado de salida.

## Qué se ha añadido

- `choque_normal_cp.py`: solución de salto mediante masa, momento y energía,
  evaluando `h(T)`, `s(T,p)` y `gamma(T)` del aire existente.
- Localización en `tobera_convergente_divergente_cp.py` mediante bisección
  físicamente acotada de `Achoque/Ag`; salida subsónica posterior.
- Dict `choque_normal`, régimen `choque_normal_interno` o
  `choque_normal_salida`, empuje calculado cuando las ecuaciones convergen.
- Visualización de propiedades del choque y distinción de puntos válidos con
  choque mediante marcadores ocres en sensibilidad y mapas.
- Se han adaptado las expectativas de pruebas antiguas que antes exigían un
  estado no resuelto y ahora poseen solución física dentro del modelo.

## Nuevos conceptos de ingeniería

En un choque normal estacionario se conserva `j=rho*V`, la cantidad de
movimiento `p+j*V/1000` [kPa] y la entalpía total
`h(T)+V²/2000` [kJ/kg]. Para `cp(T)` variable no se utilizan en producción
las expresiones de salto con gamma constante. La segunda ley exige
`s2>s1`, `pt2<pt1` y el salto `M1>1>M2`. La geometría aporta Ae/Ag,
pero no `A(x)`: sólo puede publicarse `Achoque/Ag`, no una posición [m].

Se usa expansión isentrópica a ambos lados del choque, sin pérdidas
viscosas, separación, ondas oblicuas, desplazamiento de capa límite ni
composición real de gases de combustión. En la salida el flujo puede
ajustar la contrapresión sin salto interno si la solución lo permite.

## Nuevos conceptos de Python y cálculo numérico

La ecuación de momento elimina `p2` y deja una raíz escalar `T2` en la
rama subsónica, que se encierra entre el estado sónico y el de remanso.
La pérdida de presión total se calcula a partir de entropía y temperatura
total, sin interpolación en gamma. La segunda bisección busca la sección
de choque de garganta a salida. Se valida el intervalo de contrapresiones
antes de bisecar, protegiendo contra la extrapolación de 200–2000 K.

## Ejemplo reproducible

`Tt=1200 K`, `pt=500 kPa`, `Ae/Ag=1.5`:

| Contrapresión [kPa] | Régimen | Mach salida | Achoque/Ag | Presión salida [kPa] |
| ---: | --- | ---: | ---: | ---: |
| 100 | Supersónico sobreexpandido ideal | 1.82457 | — | 84.1222 |
| 312.5526 | Choque normal en salida | 0.60473 | 1.50000 | 312.5526 |
| 350 | Choque normal interno | 0.54316 | 1.36206 | 350.0000 |
| 400 | Choque normal interno | 0.47788 | 1.18237 | 400.0000 |
| 480 | Subsónico no bloqueado | 0.24891 | — | 480.0000 |

Para el choque en la sección de salida, `M1≈1.82457`, `T1≈763.654 K`,
`p1≈84.1222 kPa`, `M2≈0.604732`, `T2≈1132.480 K`, `p2≈312.553 kPa`,
`pt1≈500 kPa`, `pt2≈395.656 kPa`, `Δs≈0.067178 kJ/(kg K)`.
En ese salto los residuos absolutos de masa y momento son inferiores a
`1e-6` en sus respectivas unidades, y el de energía inferior a `1e-7 kJ/kg`.

## Verificación frente a validación

### Ajustes finales tras la revisión independiente

- Se corrigieron dos textos web que confundían los choques normales ya
  resueltos con fenómenos que siguen fuera del modelo.
- `residuo_entropia_salida` mide ahora el error isentrópico **posterior**
  al choque respecto a `s(Tt,pt2)`; debe tender a cero. La generación
  irreversible física, `choque_normal.generacion_entropia` [kJ/(kg·K)],
  permanece positiva y no es un error de convergencia. Para `1200 K`,
  `500 kPa`, `Ae/Ag=1.5`, `p_amb=350 kPa`, es `≈0.04750419`.
- Las tolerancias de las fronteras de bloqueo y choque se acotan también
  mediante la anchura física de sus intervalos de presión. Cuando dos
  regímenes quedan por debajo de la resolución numérica, las fronteras
  se tratan como degeneradas; no se presume una distinción arbitraria.
  Se cubren `Ae/Ag=1.000001`, `1.00001`, `1.0001` y `1.001`.
- Una prueba Flask exige que el HTML muestre posición, Mach y presión
  a ambos lados, pérdida de presión total y entropía generada, con unidades
  y valores coincidentes con el cálculo.

`tests/test_choque_normal_42c.py` contrasta residuos, segunda ley, ramas,
transiciones y las relaciones analíticas de gas caloríficamente perfecto
calculadas dentro del test como referencia **aproximada independiente**.
No se han comparado resultados con experimentos reales de toberas.

Verificación efectuada: los 19 tests heredados de 42.A y 16 de 42.B
adaptados a la nueva capacidad pasan. El módulo 42.C completo pasó
**11/11** tests. La regresión global final, con esos once incluidos,
comprendió **604 tests: 603 correctos, 1 omitido (Cantera opcional),
0 fallidos**.

Referencias: [NASA Glenn — Normal Shock](https://www.grc.nasa.gov/WWW/BGH/normal.html)
y [NACA Report 1135](https://www.nasa.gov/wp-content/uploads/2023/03/equations-tables-charts-compressibleflow-report-1135.pdf).

## Limitaciones que siguen existiendo

Flujo cuasi-1D de composición constante; intervalo térmico 200–2000 K;
sin viscosidad, separación, fricción, onda oblicua o longitud axial del
divergente. Un fallo de dominio o convergencia mantiene resultados
no resueltos en `None`.

## Commit asociado

Pendiente de autorización. Base publicada: `54ff50841020774b0a41ca1ed03fb657b5f6ff52`.
