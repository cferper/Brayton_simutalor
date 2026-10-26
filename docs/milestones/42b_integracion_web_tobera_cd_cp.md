# Milestone 42.B — Integración web de la tobera convergente-divergente

## Alcance

Se integra el solucionador científico del milestone 42.A en la interfaz del
turborreactor, sin modificar `tobera_convergente_divergente_cp.py`.

- `tipo_tobera=convergente` reproduce el modelo histórico y usa `eta_n`.
- `tipo_tobera=convergente_divergente` utiliza `epsilon=Ae/Ag >= 1` y expansión
  isentrópica ideal: `eta_n` no interviene en ese cálculo, aunque la API y el
  formulario **siempre lo validan** en `0 < eta_n <= 1`. Se acepta `eta_n=.95`
  de los barridos previos y no se interpreta como eficiencia real de la C-D.
  El campo permanece visible y editable en ambos modos: un valor inválido
  puede corregirse sin cambiar el selector de tobera.
- Los estados de salida en regímenes de choque interno o en salida **no se
  resuelven**. Se mantiene el estado de garganta que sí se conoce y se presentan
  como indefinidos velocidad de salida, empuje y TSFC.
- Los estudios OFAT y mapas heredan tipo y geometría fijos, en lugar de barrer
  el área; los puntos no resueltos se excluyen de optimización. El estado
  `tobera_no_resuelta` señala choque posible con garganta conocida, mientras
  `sin_expansion` significa ausencia de margen total frente al ambiente.

## Empuje y consumo

Con el dosado `f` del motor y las salidas del solucionador de tobera:

\[
F_{s}=(1+f)\left(V_e+1000\frac{p_e-p_\infty}{G_e}\right)-V_\infty,
\qquad TSFC=\frac{3600f}{F_s}\quad(F_s>0).
\]

`G_e = rho_e V_e` es el flujo másico superficial en kg/(m²·s). El empuje
es **específico**, N/(kg/s de aire); no se ha añadido un gasto másico total.

## Calculadora de adaptación

Se indican dos magnitudes independientes para el mismo estado total tras
turbina: la presión ambiente que adaptaría la geometría `Ae/Ag` fijada, y la
relación de áreas que adaptaría la presión ambiente actual. La inversión usa
`relacion_areas_adaptada` de 42.A y una bisección de contrapresión en el
adaptador de presentación: no existe cálculo termodinámico en JavaScript.
Si la rama supersónica exige temperaturas fuera del modelo, se presenta el
motivo de indisponibilidad.

### Bisección acotada y caso contrastado

Para `epsilon>1` se halla primero la presión crítica sónica `p*` con `_sonico`
de 42.A. En la rama supersónica `Ae/Ag(p)` decrece al crecer `p`. Se elige
una presión inferior compatible con el límite `T=200 K`, cuya área debe ser
igual o mayor que el objetivo; el extremo superior `p*` tiene área **límite
1**, inferior al objetivo. Sólo entonces se biseca. `epsilon=1` retorna
directamente `p*`. Una geometría mayor que la máxima admisible provoca
`ValueError` con un diagnóstico, nunca una presión inventada.

El algoritmo previo buscaba el primer punto que aceptase la función de
adaptación supersónica y lo usaba como extremo superior sin comprobar el
signo del residuo. Cerca de `epsilon=1` ese punto podía tener **área mayor**
que la pedida: no encerraba la raíz y el resultado era incorrecto.

Para `Tt=1200 K`, `pt=500 kPa`, `Ae/Ag=1.001`:

- Antes: presión aproximada `250.3537 kPa`; área reconstruida `1.00334`.
- Después: `259.119611 kPa`; área reconstruida `1.0010000001`.

La presión es un resultado de inversión del modelo isentrópico de 42.A, no
una presión verificada experimentalmente. El método reconoce el límite de
temperatura de las correlaciones `cp(T)` de 200 a 2000 K.

No se predicen posición ni intensidad real de choques, separación de capa
límite, flujo bidimensional o prestaciones de un motor ensayado. La cota de
choque en la salida de 42.A es únicamente aproximada.

## Verificación y publicación

Pruebas nuevas y ampliadas: `tests/test_turborreactor_web_42b.py`, con áreas
`1`, `1.0001`, `1.001`, `1.01`, `1.5` y valores mayores, ida y vuelta de la
relación de áreas, contrato `eta_n`, estados y máscaras de mapas.

Resultados reales en Linux/Python 3.12, con dependencias existentes:

| Ejecución | Ejecutadas | Superadas | Omitidas | Fallidas |
| --- | ---: | ---: | ---: | ---: |
| Pruebas específicas 42.B | 16 | 16 | 0 | 0 |
| Pruebas de integración/estudios 41 | 25 | 25 | 0 | 0 |
| Regresión completa | **592** | **591** | **1** | **0** |

La omisión de la suite global es una comparación científica opcional sin
Cantera; no constituye validación experimental del modelo.
La corrección final de interfaz conserva visible y editable `eta_n` en C-D y
añade dos pruebas del formulario, incluida la respuesta HTTP 400 para un valor
inválido. La rama de publicación autorizada es `mejoras/cp-variable`.
