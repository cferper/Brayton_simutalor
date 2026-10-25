# Milestone 37 — Combustible energético y consumo específico de empuje

## Estado anterior

Los milestones 34–36 calculaban compresor–turbina, tobera convergente y vuelo
subsónico, con un calentamiento prescrito y sin flujo másico de combustible.
Base verificada: `5f5cd6e8195eddd6857112f3417d7f81f3deebe5`, rama
`mejoras/cp-variable`, 25-10-2026.

## Qué se ha añadido

`combustible_cp_variable.py`: un solucionador separado de turborreactor
subsónico con f, balance energético de cámara, nuevo trabajo específico de
turbina, empuje neto y TSFC. Reutiliza atmósfera, remanso, difusor, función
de propiedades y tobera sin modificar sus contratos. La interfaz web no cambia.

## Nuevos conceptos de ingeniería

La referencia de entalpía del aire es `h(298.15 K)=0`, con entalpía sensible
de combustible despreciada *en esa misma referencia*. Bajo la convención
simplificada usada aquí, con PCI en kJ/kg de combustible:

\[
h_2+f\eta_b PCI=(1+f)h_3,\qquad
f=\frac{h_3-h_2}{\eta_b PCI-h_3}.
\]

Cada entalpía de gas se expresa por kg del fluido correspondiente, aunque se
aproxime la entalpía de los productos con `h_aire(T)`. Esto **no** modela
composición, entalpía de formación, sensible real del combustible, ni química;
el PCI y esta convención de referencia deben interpretarse conjuntamente.
Para el eje, por kg/s de **aire entrante**:

\[
\eta_m(1+f)(h_3-h_4)=h_2-h_1.
\]

Se calcula `T4s` usando `eta_t`, y `p4` mediante
`s(T4s,p4)=s(T3,p3)` con `cp(T)` variable. La tobera converge a Mach 1
cuando su relación de presiones lo requiere. Con `Ve` y `p_e` estáticos:

\[
F_s=(1+f)V_e-V_\infty+(1+f)
\frac{1000(p_e-p_\infty)}{\rho_e V_e},\qquad
TSFC=\frac{f}{F_s}\;\mathrm{kg/(N\,s)}.
\]

`TSFC_kg_N_h = 3600*TSFC_kg_N_s`; para `Fs<=0` o sin expansión,
TSFC es `None` y se conserva un diagnóstico, sin crear empuje ficticio.

## Casos reproducibles

Parámetros comunes: `rp=10`, `eta_c=0.85`, `T3=1600 K`, `delta=0.04`,
`eta_t=0.90`, `eta_m=0.98`, `eta_n=0.95`, `eta_b=0.99`, `PCI=43000 kJ/kg`.

| Caso | Ambiente | Mach, pi_d | f [kg/kg] | Ve [m/s] | Fs bruto [N/(kg/s)] | Fs neto [N/(kg/s)] | TSFC [kg/(N h)] | Tobera |
|---|---|---|---:|---:|---:|---:|---:|---|
| A | 288.15 K, 100 kPa | 0, 1 | 0.02802821 | 662.729111 | 958.257683 | 958.257683 | 0.105296884 | Bloqueada |
| B | 288.15 K, 100 kPa | 0.7, 0.97 | 0.02659650 | 656.469917 | 990.880238 | 752.661603 | 0.127211763 | Bloqueada |
| C | ISA 10000 m | 0.5, 0.98 | 0.03076462 | 674.489940 | 1044.958200 | 895.165541 | 0.123723059 | Bloqueada |

`Ve` es la velocidad de la tobera, mientras que el término de momento
contribuye `(1+f)Ve`; valores redondeados para presentación. Se deben
recalcular si cambian las correlaciones de propiedades.

Comparación con milestone 36: `Fs_neto` sin combustible era aproximadamente
923.449, 718.885 y 857.709 N/(kg/s), respectivamente. Al aumentar el
caudal másico de gases, disminuye el salto de entalpía requerido por kg de
gas en la turbina y queda más energía y presión disponibles para la tobera.
Esto no valida predicciones experimentales de un motor.

## Nuevos conceptos de Python

Funciones pequeñas `_compresor`, `_combustor`, `_turbina`, validaciones
separadas y diccionarios por componente. La función pública única encadena
los módulos; retorna `prestaciones` y `diagnosticos` para representar
explícitamente estados definidos, no positivos o físicamente imposibles.
Valores inválidos dan `ValueError`; inversión fuera del dominio de propiedades,
`EstadoFueraDeRango`; presión o cálculo no representable, `ErrorNumericoCiclo`.

## Qué hemos aprendido

- Un motor con combustible tiene caudales distintos antes y después de la cámara.
- TSFC necesita empuje neto positivo y siempre debe expresarse con sus unidades.
- Un balance correcto con propiedades variables depende también de las referencias.
- Un residuo pequeño verifica las ecuaciones **del modelo**, no la física real.

## Verificación y validación

15 pruebas específicas de balances, propiedades, comparación aproximada con
gas caloríficamente perfecto, límite matemático `PCI -> infinito` y regresión
de modelos anteriores. `python -m unittest discover -s tests -p
'test_combustible_cp_variable_37.py' -q` ejecutó 15/15 correctas.
Suite completa y CI: registrar el resultado efectivo en el informe de entrega.
La comparación analítica y las pruebas son **verificación**, no validación
experimental ni caracterización certificable de un motor.

## Limitaciones que siguen existiendo

Aire seco equivalente también después de la combustión, sin productos ni
equilibrio químico; PCI representativo, entrada subsónica, ISA simplificada,
recuperaciones y rendimientos prescritos, tobera exclusivamente convergente.
No se modelan postcombustión, límites de estabilidad, enfriamiento de álabes,
gasto másico real, dimensiones, emisiones ni empuje absoluto.

## Fuentes primarias

- [NASA Glenn — Burner Thermodynamics](https://www.grc.nasa.gov/www/k-12/airplane/burnth.html): balance energético con f.
- [NASA Glenn — Specific Fuel Consumption](https://www.grc.nasa.gov/www/k-12/airplane/sfc.html): definición de TSFC.
- [NASA Glenn — Fuel Mass Flow Rate](https://www.grc.nasa.gov/www/BGH/fuelfl.html): caudal de combustible; la URL histórica redirige.

## Commit asociado

Pendiente hasta su publicación. No se incluye anticipadamente el hash del
commit que contiene este documento.
