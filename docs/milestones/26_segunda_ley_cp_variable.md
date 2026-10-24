# Milestone 26 — Fase 2G: segunda ley y exergía con cp(T)

Fecha de implementación: 24/10/2026. Rama de desarrollo: `mejoras/cp-variable`.
Base remota verificada: `0726a11e22c7a60cec98ca4cfc175131b1c61bfc` (Fase 2F).

## Estado anterior

La única interfaz Flask ya utilizaba cp(T) en Simulación, Resultados,
Optimización, Sensibilidad y Mapa. «Segunda ley» estaba temporalmente desactivada;
el módulo histórico `segunda_ley.py` calculaba con cp y gamma constantes.

## Qué se ha añadido

- `segunda_ley_cp_variable.py`: analiza **estados existentes** de `resolver_ciclo`
  sin reimplementar el solucionador, redefinir propiedades ni modificar 2A–2C.
- `cp_variable_web.py`: preparación de datos, una caché de los siete parámetros
  físicos de hasta 16 casos, y SVG de destrucciones de exergía reales.
- `web_app.py` y `templates/index.html`: acción POST `segunda_ley`, referencias
  independientes T0/p0, tablas, rendimientos por componente, balance doble,
  diagnóstico no motor y explicación física en la navegación original.
- Pruebas termodinámicas y Flask específicas; ampliación puntual de Actions.
- Los informes históricos de gas perfecto siguen siendo de solo lectura.

## Hipótesis y convenciones

Aire ideal N₂/O₂/Ar de composición fija, propiedades variables entre 200 y
2000 K; flujo estacionario sin cambios cinéticos/potenciales apreciables;
compresor y turbina adiabáticos. Presiones en kPa, temperaturas en K, trabajo,
entalpía y exergía en kJ/kg, entropía en kJ/(kg·K).

`propiedades_aire.h` y `s` establecen **valores relativos** a 298,15 K y 100 kPa,
no entalpía/entropía absolutas. No altera las diferencias ni los balances.

Referencias independientes del ciclo: T0=288,15 K y p0=100 kPa por defecto;
T0∈[200,2000] K, p0>0, números reales finitos y no booleanos.

\[
s(T,p)=s^\circ(T)-\frac{R_{aire}}{1000}\ln\frac{p}{p_{ref}},\quad
e_i=(h_i-h(T_0))-T_0\bigl(s_i-s(T_0,p_0)\bigr).
\]

\[
s_{gen,c}=s_2-s_1,\quad s_{gen,t}=s_4-s_3,\quad
e_{D,c}=T_0s_{gen,c},\quad e_{D,t}=T_0s_{gen,t}.
\]

Trabajo **absorbido** por compresor positivo; trabajo **producido** por turbina
positivo. Las verificaciones adicionales, independientes de multiplicar T0·sgen:

\[
e_{D,c}=w_c-(e_2-e_1),\qquad e_{D,t}=(e_3-e_4)-w_t.
\]

Solo para funcionamiento motor y denominadores físicos positivos:
\(\eta_{ex,c}=(e_2-e_1)/w_c\),
\(\eta_{ex,t}=w_t/(e_3-e_4)\).
No se define un rendimiento exergético global ni se confunde con
\(w_{neto}/q_{in}\), que es rendimiento térmico.

La tolerancia para normalizar un negativo de generación compatible con
redondeo es `1e-10 kJ/(kg·K)`; se conserva también el valor bruto para
trazabilidad. Un negativo mayor permanece visible y se marca inconsistente.
Los residuos exergéticos tienen banda numérica `1e-8 × max(1, |wc|, |wt|, |e_i|)`
en kJ/kg. Son tolerancias de **verificación de software**, no incertidumbres
experimentales. La caché no altera las ecuaciones: su clave contiene solo los
siete parámetros del ciclo; T0 y p0 se aplican al mismo estado ya resuelto.

## Caso base reproducible

Entradas: T1=288,15 K, T3=1600 K, p1=100 kPa, rp=10, ηc=0,85,
ηt=0,90, δ=0,05, T0=288,15 K y p0=100 kPa.

| Magnitud | Resultado cp(T) |
|---|---:|
| Trabajo neto | 402,070798 kJ/kg |
| Rendimiento térmico (primera ley) | 34,893428 % |
| Entropías s1, s2, s3, s4 | −0,034254422; 0,048280925; 1,181022688; 1,264336212 kJ/(kg·K) |
| sgen compresor / turbina | 0,082535347 / 0,083313524 kJ/(kg·K) |
| Exergía e1, e2, e3, e4 | 0,000000; 292,452989; 1118,335756; 376,022617 kJ/kg |
| eD compresor / turbina | 23,782560 / 24,006792 kJ/kg |
| **Suma parcial de turbomáquinas** | **47,789352 kJ/kg** |
| Participación compresor / turbina | 49,7654 / 50,2346 % |
| Rendimientos exergéticos compresor / turbina | 92,479479 / 96,765948 % |
| Balance alternativo compresor / turbina | 23,782560 / 24,006792 kJ/kg |
| Residuo alternativo − Gouy-Stodola | ≈2,49×10⁻¹⁴ / 1,88×10⁻¹³ kJ/kg |

En el caso base, la turbina destruye ligeramente más exergía específica que el
compresor; este resultado concreto no debe extrapolarse a otros diseños.

## Nuevos conceptos de ingeniería

La primera ley expresa conservación de energía y la segunda identifica pérdida
de capacidad de producir trabajo. La presión de referencia p0 puede cambiar las
exergías **individuales**, pero a T0 fija añade el mismo desplazamiento a
todos los estados, por lo que sus **diferencias y destrucciones** no cambian.
Al cambiar T0 varían la referencia termodinámica y eD por Gouy–Stodola,
sin modificar los cuatro estados ni la generación de entropía calculada.

La suma eD,c+eD,t **no es la destrucción total del ciclo**. No se modela una
cámara química real ni variaciones de composición; las condiciones de fuente
externa/entorno de aporte o rechazo de calor son desconocidas. En especial,
`s3−s2` y `s1−s4` NO son generaciones de entropía de esos intercambios:
falta incluir la transferencia de entropía por calor. La caída de presión entre
2 y 3 modifica los estados, pero sin definir volumen de control e intercambios
no autoriza cuantificar una destrucción atribuida aisladamente a esa pérdida.

## Nuevos conceptos de Python

`functools.lru_cache(maxsize=16)` memoriza una función determinista mediante
la tupla de siete números inmutables; los cambios solo ambientales no provocan
una nueva solución. Un diccionario estructurado reúne magnitudes, residuos,
porcentajes y diagnósticos con unidades explícitas. `None` representa un
rendimiento no definido, en lugar de sustituirlo engañosamente por cero.
La plantilla Jinja recorre los cuatro estados y solo coloca SVG generado a
partir de resultados numéricos, no calcula termodinámica.

## Verificaciones y estado de publicación

Pruebas específicas: `tests/test_segunda_ley_cp_variable.py` y
`tests/test_segunda_ley_cp_web.py` (14 y 7 métodos). Contrastes directos de
propiedades, ecuaciones alternativas y límites reversibles; estados no motores,
errores de formulario, reutilización de ciclo y SVG. Regresiones del workflow
anterior: 64 métodos. La ejecución GitHub Actions del commit preparado y la
publicación deben confirmarse externamente tras terminar la fase; no se
atribuyen aquí comprobaciones visuales reales.

## Limitaciones que siguen existiendo

No incluye exergía química, cinética o potencial; ni condiciones de fuentes
térmicas, destrucción de intercambiadores, combustión real, mapas de componentes
o rendimiento exergético global. El gráfico es de barras de valores resueltos,
no una trayectoria termodinámica interpolada. Es verificación interna, no
validación experimental. Revisión visual en Windows: pendiente.

## Commit asociado

Pendiente de identificación al crear el commit único autorizado de esta fase.
