# Milestone 24 — Aprendizaje: sensibilidad OFAT con propiedades variables

## 1. Por qué esta fase

Después de 2A (propiedades del aire), 2B (ciclo), 2C (optimizaciones A/B) y el dashboard unificado, la sección Sensibilidad aún correspondía al gas perfecto antiguo. La Fase 2E permite preguntar **qué cambia si modificamos solo una entrada** del modelo cp(T) actual. «OFAT» significa *one factor at a time*. El método muestra tendencias con seis entradas fijas; **no** mide interacciones ni vuelve a optimizar rp para cada caso.

## 2. Física: de la muestra a la curva

El ciclo se define por siete entradas: `T1,T3,rp,p1,eta_c,eta_t,delta`. Por ejemplo, al variar T3 de 1200 a 1750 K, mantenemos T1=288.15 K, rp=10, p1=100 kPa, eta_c=.85, eta_t=.90 y delta=.05. Para cada T3, el módulo llama al solucionador que ya calcula entalpías y entropías variables, no `cp * ΔT` con cp constante.

Comprobamos la primera ley en cada estado calculable:

\[
w_{\mathrm{neto}}=w_t-w_c=q_{\mathrm{in}}-q_{\mathrm{out}}
\]

La eficiencia térmica \(\eta=w_\mathrm{neto}/q_\mathrm{in}\) solo se interpreta como prestación cuando el ciclo cumple todas las condiciones motoras del solucionador. Un ciclo con trabajo no positivo puede tener números de estado coherentes pero no es un punto operativo válido. Si el solucionador necesita una temperatura fuera de 200–2000 K, no se extrapolan correlaciones de propiedades. Si una entrada es inválida o hay fallo numérico, el diagnóstico también queda diferenciado.

Los gráficos **interrumpen la línea** cada vez que una muestra no está disponible como ciclo motor. Así se evita dibujar una trayectoria falsa entre regiones desconectadas. El punto base se señala con una línea vertical, no se obliga a que coincida con un nodo de malla.

## 3. Física: qué significa la sensibilidad local

\[
S_x^Y=\frac{x}{Y}\frac{dY}{dx}
\]

Es una **elasticidad adimensional**. Si vale 1.85, una pequeña subida de x del 1 % se asocia aproximadamente con una subida de Y del 1.85 % cerca del punto considerado (si las demás entradas siguen fijas). No son 1.85 puntos porcentuales del rendimiento.

Si se puede perturbar el parámetro en ambas direcciones y ambos puntos son motores, usamos la diferencia central

\[
\frac{dY}{dx}\approx\frac{Y(x+h)-Y(x-h)}{2h}.
\]

Si una perturbación sale del dominio motor, utilizamos una diferencia **unilateral**. Comparamos la estimación obtenida con h y con h/2. Una diferencia considerable indica que la derivada no es fiable para ese paso. Si x=0, Y=0 o el punto base no es motor, no existe normalización válida; mostramos un motivo en lugar de inventar un valor.

## 4. PYTHON — flujo y firmas

1. `PARAMETROS_CP: dict` organiza etiquetas, unidades y rangos iniciales; en un `dict`, `catalogo['T3']['rango']` accede a `(1200, 1750)`.
2. `barrido_cp_variable(entradas, parametro, minimo, maximo, muestras=41) -> dict` verifica selección, límites y número de muestras. El bucle `for` crea una copia del diccionario de parámetros con `{**entradas, parametro: x}`: esta sintaxis sustituye una sola clave **sin mutar** los otros valores. No se modifica `DEFAULTS`.
3. `_evaluar(entradas) -> dict` delega el cálculo en `resolver_ciclo(**entradas)`, donde `**` convierte las claves del diccionario en argumentos con nombre. `try/except` separa casos inválidos, fuera de rango y fallo numérico; `viable` distingue el no motor. Se devuelve `None` en `operativas` para cualquier punto no motor, y así el presentador de gráficos no lo trata como válido.
4. `sensibilidad_local(entradas, parametro, paso_relativo=1e-3) -> dict` perturba x, comprueba viabilidad en los vecinos y contrasta `h` con `h/2`. Devuelve por objetivo un estado `disponible`, `inestable` o `no_disponible`, el esquema de diferencias y, si procede, la elasticidad.
5. `preparar_sensibilidad(entradas,parametro,minimo,maximo,muestras) -> dict` separa presentación y física. `svg_sensibilidad(barrido,claves,etiqueta,unidad_y) -> str|None` toma filas ya calculadas y produce texto SVG; no necesita Matplotlib, ni resuelve ecuaciones.
6. `web_app.index()` reconoce el botón `accion='sensibilidad'`. Convierte campos `sens_cp_*` y llama al preparador. `dashboard.renderizar_dashboard` pasa el resultado a `templates/index.html`; el motor de plantillas Jinja inserta tablas, mensajes y SVG. `static/dashboard.js` solo cambia mínimos y máximos sugeridos cuando elegimos un parámetro diferente.

**Ejemplo rápido:**

```python
from cp_variable_web import DEFAULTS
from sensibilidad_cp_variable import barrido_cp_variable

estudio = barrido_cp_variable(DEFAULTS, 'T3', 1200, 1750, 41)
print(estudio['conteos'])
# {'motor': 41}
print(estudio['local']['trabajo_neto']['valor'])
# aproximadamente 1.848248
```

## 5. Interpretación del caso base

Con T1=288.15 K, T3=1600 K, rp=10, p1=100 kPa, eta_c=.85, eta_t=.9 y delta=.05, el trabajo neto es aproximadamente **402.071 kJ/kg** y el rendimiento **34.893 %**. La elasticidad con respecto a T3 es aproximadamente **1.848** para trabajo neto y **0.155** para rendimiento; tienen magnitudes distintas y son relaciones **relativas**, no porcentajes absolutos ni puntos porcentuales.

Si varías **p1** a temperatura y rp fijas, se modifica la presión absoluta de cada estado, pero en el modelo de aire ideal los saltos de entalpía dependen de las temperaturas y de las **relaciones** de presión. Por eso trabajo y rendimiento permanecen prácticamente constantes. Esto sería distinto si se introdujeran fenómenos dependientes de presión, que aquí no modelamos.

Si varías **rp**, la máxima producción neta y el mayor rendimiento se alcanzan en general en puntos diferentes. Las referencias de 2C para este caso están cerca de rp=15.878 (máximo trabajo) y rp=46.819 (máximo rendimiento). El barrido OFAT permite visualizarlo, pero la posición de un nodo de la malla **no prueba** dónde está el óptimo continuo.

## 6. Ejercicios de aprendizaje

1. Ejecuta el barrido p1=80–120 kPa. ¿Por qué son constantes trabajo y rendimiento, pero no lo serían necesariamente las entropías con referencia a presión?
2. Cambia el barrido a `rp` desde 0.5 hasta 30. Identifica filas no motoras y explica por qué hay huecos al principio de la gráfica.
3. Selecciona `eta_c` con valor base exactamente 1. ¿Por qué la derivada no puede calcularse con un paso central dentro del dominio permitido?
4. Modifica T1 hasta acercarte a 2000 K. ¿Cuál es la diferencia entre la entrada T1 válida y un T2 resultante fuera de rango?
5. Reduce el paso relativo de 1e-3 a 5e-4 en `sensibilidad_local`. ¿Cuándo esperarías valores parecidos? ¿Por qué cerca de una frontera o un extremo una elasticidad puede ser menos robusta?

## 7. Pruebas y límites

`tests/test_sensibilidad_cp_variable.py` tiene diez casos; `tests/test_sensibilidad_cp_web.py`, seis. La batería web existente añade 32 regresiones relacionadas, para un total objetivo de 48. GitHub Actions registra por separado el resultado definitivo y puede revelar diferencias ambientales. No son una calibración del aire, un análisis de incertidumbres ni una validación experimental de una turbina real.

La interfaz continúa teniendo una sola plantilla: `templates/index.html`. El panel Mapa de diseño y el de Segunda ley siguen desactivados hasta fases posteriores. No se eliminan archivos históricos ni se modifica el repositorio de gas perfecto.
