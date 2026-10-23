# Fase 2B — Solucionador Brayton independiente con cp(T)

## Estado anterior

Base remota comprobada el **23/10/2026**: commit `d5f818aa7f5a2880e414211950f8396830222308`, rama `mejoras/cp-variable` de `cferper/Brayton_simutalor`. La Fase 2A ya contenía `propiedades_aire.py`, con correlaciones NIST para N₂/O₂ y cp monoatómico del Ar. El Brayton histórico seguía usando `cp=1005 J/(kg·K)` y `gamma=1.4`; aún no había un ciclo con propiedades variables.

## Qué se ha añadido

- `ciclo_cp_variable.py`: solución de cuatro estados con `resolver_ciclo(...)`, usando `s0(T)` y `h(T)` existentes. Calcula estados isentrópicos, estados reales, trabajos, calores, entropías y residuos, y distingue motor de no motor sin inventar rendimientos.
- `tests/test_ciclo_cp_variable.py`: referencias independientes por integración numérica de cp(T), eficiencias, irreversibilidad, balance de energía, extremos y tipos erróneos.
- `CODE_WALKTHROUGH.md` §4.58 y [aprendizaje de Fase 2B](20_ciclo_cp_variable_APRENDIZAJE.md).

**Aislamiento:** no se modifica `main.py`, `viabilidad.py`, `propiedades_aire.py`, los optimizadores, `segunda_ley.py`, sensibilidad, mapa, dashboard, Flask, HTML, CSS ni dependencias. No se modifica el repositorio `Brayton_simutalor-gas_perfecto` ni la copia Windows.

## Nuevos conceptos de ingeniería

Para el aire ideal de composición constante, `cp` depende de T. La compresión y expansión de referencia se resuelven con:

```text
s0(T2s)−s0(T1) = (R/1000) ln(p2/p1)
s0(T4s)−s0(T3) = (R/1000) ln(p4/p3)
p2=rp·p1, p3=p2(1−delta), p4=p1
h2=h1+[h(T2s)−h1]/eta_c
h4=h3−eta_t[h3−h(T4s)]
```

Se invierte la entropía térmica para hallar las temperaturas isentrópicas; se invierte la entalpía con la función publicada en 2A para obtener las temperaturas reales. **No** se sustituye `gamma` por un valor promedio arbitrario ni se aplican las fórmulas de exponente constante.

Con h relativa a 298,15 K, se calculan `wc=h2−h1`, `wt=h3−h4`, `wn=wt−wc`, `qin=h3−h2`, `qout=h4−h1`, `eta=wn/qin` sólo en funcionamiento motor. La identidad `wn=qin−qout` se expone con su residuo. La generación de entropía adiabática de compresor/turbina es `s2−s1`/`s4−s3`; esto **no** constituye el balance entropía/exergía del conjunto o del aporte de calor.

Las entradas inválidas (`ValueError`), un estado requerido fuera de 200–2000 K (`EstadoFueraDeRango`), errores de representación/convergencia (`ErrorNumericoCiclo`) y un cálculo válido que no es motor (`viable=False`, `motivos`, `rendimiento=None`) se separan explícitamente. Las fórmulas de eficiencia pierden su interpretación física si las máquinas trabajan con el signo de presión contrario; se señala también cualquier generación negativa significativa y no se afirma que el punto es motor.

## Nuevos conceptos de Python

- **Reutilización y separación:** `ciclo_cp_variable.py` importa `s0`, `s`, `h`, `T_desde_h` y constantes de `propiedades_aire.py`, sin alterar el módulo de propiedades ni activar rutas anteriores.
- **Bisección monótona y acotada:** `_temperatura_desde_s0` comprueba la imagen de `s0` entre 200 y 2000 K antes de iterar; no permite extrapolación ni usa SciPy.
- **Excepciones específicas:** dos subclases de errores estándar comunican si falló el dominio térmico o la representación numérica.
- **Diccionario de salida verificable:** se conservan temperaturas, presiones, entalpías, entropías, residuos, márgenes y motivos, útiles para futuras integraciones sin ejecutarlas ahora.
- **Pruebas no tautológicas:** los estados isentrópicos se contrastan frente a cuadratura del cp/T y una segunda bisección sólo en tests, distinta de la primitiva `s0` de producción.

## Qué hemos aprendido

1. Un gas puede cumplir la ecuación de estado ideal sin tener cp constante.
2. La eficiencia isentrópica de turbomáquinas se define por **entalpías**; sustituirla por cocientes de temperaturas sólo sirve con cp constante.
3. Una raíz físicamente requerida puede quedar fuera del dominio de la correlación, sin que sea correcto devolver la frontera artificialmente.
4. El balance algebraico verifica implementación, pero no demuestra autenticidad ni validación experimental; referencias integradas separadamente refuerzan la verificación.
5. La existencia de un punto calculable no garantiza producción neta de trabajo ni validez de una máquina con relación de presiones invertida.

### Resultados de referencia: `T1=288.15 K`, `T3=1600 K`, `rp=10`, `p1=100 kPa`

| Modelo | ηc / ηt / δ | T2 (K) | T4 (K) | Trabajo neto (kJ/kg) | η térmico |
|---|---|---:|---:|---:|---:|
| cp(T), Fase 2B | 1 / 1 / 0 | 552.284478 | 911.064835 | 542.818426 | 45.245515 % |
| cp,γ constantes (histórico) | 1 / 1 / 0 | 556.330551 | 828.715949 | 505.619018 | 48.205253 % |
| cp(T), Fase 2B | .85 / .90 / .05 | 597.692837 | 993.581041 | 402.070798 | 34.893428 % |
| cp,γ constantes (histórico) | .85 / .90 / .05 | 603.656530 | 916.855359 | 369.476301 | 36.898732 % |

Las diferencias son propias de los **dos modelos**, no errores del HTML histórico. En el caso no ideal cp(T), el compresor consume `316.235549 kJ/kg`, la turbina produce `718.306347 kJ/kg`, `qin=1152.282306 kJ/kg`, `qout=750.211508 kJ/kg`, y las generaciones de entropía adiabáticas son `0.082535347` y `0.083313524 kJ/(kg·K)`.

## Pruebas y estado de verificación

**23/10/2026, copia Linux independiente:** 21/21 pruebas específicas de Fase 2B correctas, 17/17 pruebas de propiedades de Fase 2A correctas y 2/2 puntos de regresión directa del motor constante reprodujeron los trabajos conocidos (ideal `505.619018249`, no ideal `369.476301045 kJ/kg`). La ejecución de `python -B -m unittest discover -s tests -q` **no pasó**: contabilizó 110 entradas de prueba y terminó con **19 errores de importación** de módulos históricos por `ModuleNotFoundError: jinja2` (Flask tampoco estaba disponible en el entorno previo). Ningún fallo de aserción se notificó entre los ejecutables. No se instalaron dependencias y **no** se declara superada la suite completa. Estas pruebas se ejecutaron una sola vez al cierre; no sustituyen la verificación en un entorno completo.

Las referencias calculadas con cp/T y cp integrados por regla del punto medio verifican independencia del algoritmo de producción para los estados y saltos térmicos, **no son medidas experimentales**. El residuo de primera ley también es una identidad de las h conservadas; no basta por sí solo como validación física.

## Limitaciones que siguen existiendo

- Aire ideal de composición fija 78/21/1; no hay combustión química, variación de especies, humedad, disociación ni combustibles.
- Sólo 200–2000 K para **todos** los estados, incluidos los isentrópicos de referencia; puede rechazarse un juego de entradas válido cuando no está representado por las correlaciones elegidas.
- Sin modelos de turbomáquinas fuera de su sentido nominal, mapas de componentes o pérdidas mecánicas; p3 se obtiene de una pérdida relativa fijada externamente.
- No se completa el balance de entropía de la cámara ni el de toda la instalación y no se cuantifica incertidumbre/validación experimental.
- No se ha integrado en optimización, sensibilidad, mapa, segunda ley histórica, diagnóstico o informes HTML. La Fase 2C requiere revisión y autorización independientes.

## Commit asociado

Publicación pendiente mientras se prepara el commit de esta fase. Base verificada `d5f818aa7f5a2880e414211950f8396830222308`; el hash definitivo de un commit no puede escribirse dentro del mismo sin modificarlo.
