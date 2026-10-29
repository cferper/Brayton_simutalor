# Milestone 47.1 — Caudal de una tobera de geometría fija

## Alcance y estado

Se incorpora **sin sustituir** la modalidad de caudal de aire impuesto un segundo problema: dadas las condiciones de remanso `Tt`, `pt`, presión ambiente y áreas físicas, calcular el gasto de gases. Se conserva el solucionador `cp(T)` de las toberas convergente (M35) y C-D (M42–M44.4), incluido choque normal interno o de salida cuando está resuelto. No se modifican sus ecuaciones ni se introducen mapas de componentes.

## Contratos y ecuaciones

- Convergente: `Ae=Ag`; se conserva `eta_n` del modelo y la salida coincide con la garganta.
- C-D: `epsilon=Ae/Ag >= 1`; el solucionador determina régimen y flujo superficial `Gg` y `Ge`.
- Continuidad: `G = rho V` [kg/(s m²)]; `mdot_g = Gg Ag`, que se coteja con `Ge Ae`.
- En convergente: `mdot_g = rho_e V_e Ag`.
- En garganta bloqueada: `Mg=1`, `mdot_g = rho_g a_g Ag`, con estado sónico obtenido por el solucionador existente mediante entalpía, entropía, ecuación de estado y `gamma(T)`.
- En C-D no bloqueada se usa el `Gg` subsónico **real**: no se impone por error el valor crítico.
- Combustible: `mdot_a=mdot_g/(1+f)` y `mdot_f=f mdot_a`.
- Empuje: se reutiliza `calcular_prestaciones_absolutas` (momento del gas, velocidad del aire de entrada y presión en la sección de salida). No se altera el empuje específico.

`caudal_tobera_geometria_fija.py` contiene un adaptador independiente de tobera (`resolver_caudal_tobera_fija`) y una función de escalado y cotejo de continuidad (`caudal_desde_estado_tobera`). El adaptador web utiliza **los estados que ya ha calculado el núcleo una sola vez**, sin crear otro punto termodinámico. Si el modelo C-D señala un régimen sin salida resuelta, se muestran motivo y caudales indefinidos (`None`), no cero.

## Ejemplo reproducible

Con `Tt=1200 K`, `pt=500 kPa`, `Ag=0.010 m²`, `Ae=0.015 m²` y tobera C-D:

| Contrapresión | Régimen calculado | Gases [kg/s] | Garganta |
| --- | --- | ---: | --- |
| 350 kPa | Choque normal interno | 5.72983233749 | Sónica |
| 490 kPa | Subsónico no bloqueado | 2.52686088021 | Subsónica |

Reproducción:

```python
from caudal_tobera_geometria_fija import resolver_caudal_tobera_fija
for p in (350, 490):
    salida = resolver_caudal_tobera_fija(1200, 500, p, .01,
        area_salida=.015, tipo_tobera="convergente_divergente")
    print(p, salida["regimen"], salida["gasto_masico_gases"])
```

En estos casos, los residuos de continuidad en masa son inferiores a `7e-12 kg/s`. El caudal bloqueado no cambia con la contrapresión dentro de las ramas bloqueadas representadas; el no bloqueado depende de ella.

## Verificación, hipótesis y limitaciones

`python -m unittest discover -s tests -p 'test_caudal_geometria_fija_47_1.py' -v` verifica casos bloqueado, no bloqueado, continuidad, proporcionalidad de área, choque interno/salida, separaciones de caudales, entradas inválidas y compatibilidad web. El contraste con gas caloríficamente perfecto es solo una **referencia independiente aproximada**, no una sustitución del modelo variable. Se coteja `|mdot_g-mdot_e| ≤ 2·10⁻⁶ max(mdot_g,mdot_e)` como margen numérico conservador compatible con el dimensionamiento M45. No se aceptan discrepancias materiales de geometría; la coincidencia de áreas se exige dentro de `2·10⁻⁸` relativo (por propagación numérica de relaciones).

No se valida una tobera real ni se calcula el punto operativo de un motor real: `Tt` y `pt` se **prescriben** y pueden no ser compatibles con los mapas y el caudal admisible de compresor/turbina. El modelo C-D sigue sin resolver configuraciones con fenómenos fuera de sus hipótesis (p. ej., separación viscosa, choques oblicuos o pérdidas de contorno). No se propone extrapolar una región no resuelta. La modalidad anterior de caudal impuesto permanece, incluido el caso sin caudal absoluto.

## Fuentes físicas y continuidad

- [NASA Glenn, Mass Flow Rate Equations](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/mass-flow-rate-equations/) — continuidad y límite sónico (comparación de gas perfecto).
- [NASA Glenn, Nozzle Design](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/nozzle-design/) — expansión y efectos de contrapresión.
- M45: `docs/milestones/45_gasto_masico_dimensionamiento_turborreactor.md`; M46: documentos `46_*`; M44.4: `44_4_perfiles_cuasidimensionales_tobera.md`.

## Pendiente para 47.2 y siguientes

Acoplar la continuidad de admisión y el gasto admitido por el compresor; posteriormente mapas de compresor/turbina, compatibilidad de velocidades y solución iterativa. No se ha empezado ese trabajo. La regresión histórica completa e inspección visual final se harán al integrar en Windows.
