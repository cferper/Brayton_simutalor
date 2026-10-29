# Milestone 47.1 — Guía de aprendizaje: una tobera fija determina el caudal

## Dos problemas distintos

**Dimensionar (modalidad A):** conocemos `mdot_a`, el dosado `f` y el régimen de expansión. Calculamos `mdot_g=(1+f)mdot_a`, luego las áreas necesarias para pasar ese gas.

**Analizar una geometría existente (modalidad B):** conocemos `Ag`, `Ae` (si es C-D), el remanso `Tt,pt` y el ambiente `p∞`. Primero se resuelve el régimen de expansión y después `mdot_g=Gg Ag`. El aire es `mdot_a=mdot_g/(1+f)`. **No se debe introducir un caudal adicional**, pues sobredeterminaría el problema.

## ¿Por qué aparece un caudal máximo?

El remanso describe el estado que tendría el fluido al frenarlo isentrópicamente: almacena la información energética (`ht`) y la entropía de referencia (`st`). Al acelerar el gas, una parte de la entalpía se transforma en velocidad:

\[h(T_t)=h(T)+\frac{V^2}{2000}\quad\text{(h en kJ/kg, V en m/s)}\]

La continuidad exige `mdot = rho V A`. Al disminuir la presión de salida, `V` aumenta, pero `rho` disminuye. En el cuello aparece una condición límite `V=a(T)` o `M=1`: con `Tt`, `pt` y `Ag` fijados, se alcanza el gasto másico crítico; seguir reduciendo la contrapresión no puede aumentar el caudal más allá de ese máximo en el modelo considerado.

Nuestro simulador no usa una `gamma` constante para esto. Obtiene la temperatura sónica de `h(Tt)-h(Tg)=a(Tg)²/2000`, su presión mediante igualdad de entropía isentrópica, `rho_g=1000 pg/(R Tg)` (si `pg` en kPa) y `mdot_g = rho_g a(Tg) Ag`.

Con contrapresión suficientemente alta en una C-D, la garganta **no** está bloqueada: su flujo superficial es menor que el crítico y varía con el ambiente. En un choque normal se pierde presión total y Mach cae bruscamente; el gasto de masa se conserva. Por ello hay que usar los estados de choque que el solucionador ya calculó, sin interpolarlos ni fabricar estados.

## Ejemplo con valores del código

Fija una tobera C-D con `Ag = 0,010 m²`, `Ae = 0,015 m²`, `Tt = 1200 K` y `pt = 500 kPa`:

- Con `p∞ = 350 kPa`, la garganta se bloquea, hay choque normal interno y el gasto de gases es aproximadamente **5,729832 kg/s**.
- Con `p∞ = 490 kPa`, la solución es subsónica no bloqueada y el gasto desciende a **2,526861 kg/s**.

Si el combustible fuese `f=0,025` kg/kg de aire en el primer caso, `mdot_a≈5,590080 kg/s` y `mdot_f≈0,139752 kg/s`. Se cumple que la suma es `mdot_g`. Este valor de `f` es ilustrativo: en la web se utiliza el dosado **calculado por el núcleo**.

## Python: evitar duplicar física

La función `resolver_caudal_tobera_fija` llama al solucionador C-D o convergente existente. Después, `caudal_desde_estado_tobera` escala por área y verifica que `Gg Ag ≈ Ge Ae`. En la ruta web se resuelve el núcleo **una única vez** y se reutilizan sus datos; no aparecen dos juegos de estados de turbina distintos.

Se usan diccionarios con `disponible` y `motivo` porque una configuración físicamente no resuelta no equivale a un resultado numérico cero. Se valida área positiva y finita, `Ae≥Ag` para C-D, y que en una convergente `Ae=Ag`.

## Qué significa (y qué no significa) el resultado

La nueva modalidad calcula el caudal compatible con **esa tobera y ese remanso impuesto**. Todavía no sabemos si el compresor, el eje y la turbina podrían sostener simultáneamente ese caudal. Para cerrar el motor fuera de diseño se necesitarán mapas de componentes y acoplamiento iterativo (milestones posteriores). Tampoco se han incorporado separación de flujo ni pérdidas nuevas, ni se ha contrastado una tobera real: eso sería **validación experimental**, distinta de la verificación numérica de ecuaciones.

Para practicar, duplica `Ag` y `Ae` manteniendo su proporción: a igual régimen y remanso, se duplicará el caudal. Luego aumenta la contrapresión hasta pasar de garganta bloqueada a subsónica y observa que **ya no basta con la fórmula del gasto crítico**.
