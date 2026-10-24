# Fase 2G — Aprendizaje: segunda ley y exergía con cp(T)

Fecha de esta fase: 24/10/2026. Rama: `mejoras/cp-variable`.
Base comprobada: `0726a11e22c7a60cec98ca4cfc175131b1c61bfc`.
El commit que incluya este documento queda pendiente hasta publicar el árbol
completo. [Resumen técnico de la fase](26_segunda_ley_cp_variable.md).

## 1. Qué teníamos y qué faltaba

El simulador podía hallar los cuatro estados con aire de cp(T), obtener
trabajos y rendimiento térmico, optimizar, estudiar sensibilidad y construir
mapas. El panel Segunda ley existía, pero no ejecutaba el modelo variable.
`segunda_ley.py` solo sirve como antecedente **histórico** para el simulador
caloríficamente perfecto, no como calculadora de esta fase.

Ahora añadimos un **postprocesado de los cuatro estados existentes**. Si el
solucionador 2B ya conoce \((T_i,p_i,h_i,s_i)\), calcular exergía no requiere
resolver por segunda vez ninguna compresión o expansión al cambiar el ambiente.

## 2. Primera ley frente a segunda ley

La primera ley comprueba que \(w_{neto}=w_t-w_c=q_{in}-q_{out}\).
Si ambas partes dan 402,071 kJ/kg, la energía está contabilizada, pero eso no
nos dice cuánto *trabajo útil potencial* se ha perdido irreversiblemente.

La segunda ley cuantifica esa degradación mediante la entropía generada.
Una máquina adiabática sin irreversibilidades conservaría la entropía de la
corriente entre entrada y salida: \(s_{gen}=0\). Una real normalmente la
aumenta. En la compresión, el trabajo real supera al de una compresión
reversible equivalente; en expansión, la turbina real produce menos.

## 3. De entropía a exergía física

Una referencia ambiental es el llamado *estado muerto*: temperatura T0 y
presión p0 del entorno. No debe confundirse T0 con T1 ni p0 con p1;
pueden coincidir para un caso particular, pero son parámetros distintos.

`propiedades_aire.py` proporciona:

- `h(T)` [kJ/kg] y `s(T,p)` [kJ/(kg·K)].
- `s0(T)` [kJ/(kg·K)] e `R_AIRE` [J/(kg·K)].
- Temperaturas admisibles de 200 a 2000 K.

La relación para gas ideal es:

\[
s(T,p)=s^\circ(T)-R\ln(p/p_{ref}),\qquad
e_i=[h_i-h(T_0)]-T_0[s_i-s(T_0,p_0)].
\]

En el programa, R se expresa en kJ/(kg·K) al multiplicarlo por el logaritmo.
No interpolamos cp ni usamos una sola gamma. Como h y s son magnitudes
*relativas*, el cero escogido es arbitrario, pero se cancela al restar.

La exergía es la posibilidad de obtener trabajo útil al llevar reversiblemente
la corriente al estado ambiente, bajo las hipótesis del modelo. **No** es la
energía total ni añade exergía química, cinética o potencial.

## 4. Gouy–Stodola y balances alternativos

Para compresor/turbina **adiabáticos y estacionarios**:

\[
s_{gen,c}=s_2-s_1,\quad s_{gen,t}=s_4-s_3;
\qquad e_{D,j}=T_0s_{gen,j}.
\]

¿Por qué aparece T0? Convierte la entropía generada en la capacidad de trabajo
destruida *respecto a ese ambiente*. Tiene unidades:

\[
\mathrm K\times\frac{\mathrm{kJ}}{\mathrm{kg\,K}}=
\frac{\mathrm{kJ}}{\mathrm{kg}}.
\]

No basta con programar `T0 * diferencia_s`; usamos un segundo camino para
contrastar errores de signo, energía o referencia:

\[
e_{D,c}=w_c-(e_2-e_1),\qquad
e_{D,t}=(e_3-e_4)-w_t.
\]

Se ha elegido **wc positivo absorbido** y **wt positivo producido**. Una
reversibilidad ideal daría destrucción cero y rendimiento exergético 100 %, si
el trabajo y la diferencia de exergía tienen denominadores bien definidos.

Los rendimientos de componentes son:

\[
\eta_{ex,c}=\frac{e_2-e_1}{w_c},\qquad
\eta_{ex,t}=\frac{w_t}{e_3-e_4}.
\]

Para un ciclo no motor o un componente con trabajo o caída de exergía nula,
no debemos mostrar «0 %»: mostramos **No definido**. El rendimiento
\(w_{neto}/q_{in}\) sigue siendo el térmico de primera ley; no se usa como
rendimiento exergético global sin especificar fuente de calor o combustible.

## 5. Resultados que puedes reproducir

Con T1=288,15 K, T3=1600 K, rp=10, p1=100 kPa, ηc=0,85,
ηt=0,90, δ=0,05 y ambiente T0=288,15 K, p0=100 kPa:

| Observación | Valor |
|---|---:|
| s1; s2 | −0,034254; 0,048281 kJ/(kg·K) |
| s3; s4 | 1,181023; 1,264336 kJ/(kg·K) |
| sgen compresor | 0,082535347 kJ/(kg·K) |
| sgen turbina | 0,083313524 kJ/(kg·K) |
| e1; e2 | 0; 292,452989 kJ/kg |
| e3; e4 | 1118,335756; 376,022617 kJ/kg |
| eD compresor | 23,782560 kJ/kg |
| eD turbina | 24,006792 kJ/kg |
| Suma **parcial** eD | 47,789352 kJ/kg |
| ηex compresor / turbina | 92,479 % / 96,766 % |

La turbina representa aproximadamente un 50,235 % de la destrucción en esas
**dos** máquinas y el compresor un 49,765 %. No sabemos qué porcentaje
representan del total de toda la instalación.

Como ejercicio, cambia **solo** p0 de 100 a 120 kPa: cada exergía de estado
cambia en la misma cantidad, pero las diferencias e2−e1 y e3−e4 quedan
iguales. Cambia **solo** T0 a 300 K: las generaciones de entropía siguen
iguales y eD cambia en proporción 300/288,15. Los estados T, p, h y s del ciclo
no cambian en ninguno de esos dos experimentos.

## 6. Python: funciones reales introducidas

### `segunda_ley_cp_variable._ambiente_valido(T0, p0)`

Argumentos: dos reales T0 [K], p0 [kPa]; retorna `None` o lanza `ValueError`
si son booleanos, no finitos, T0 fuera de 200–2000 K o p0≤0. No llama a
otras funciones del proyecto. La llama `analizar_segunda_ley_cp_variable`
para proteger las fórmulas y logaritmos. Ejemplo: `_ambiente_valido(288.15,100)`
finaliza sin error. Es una función auxiliar: el guion bajo señala que no es
la API principal, aunque Python no impide importarla.

### `segunda_ley_cp_variable.analizar_segunda_ley_cp_variable(ciclo, T0=288.15, p0=100.0)`

Argumentos: diccionario `ciclo` de `resolver_ciclo`, con cuatro T [K], cuatro
p [kPa], h [kJ/kg], s [kJ/(kg·K)], trabajos [kJ/kg] y viabilidad; referencias
ambientales opcionales. Devuelve `dict` con `entropias`, `exergias`,
`generacion`, `generacion_bruta`, `destruccion`, `suma_turbomaquinas`,
`aportaciones_porcentaje`, `balances_exergia`, `residuos_balances`,
`eta_ex_compresor`, `eta_ex_turbina`, `estado`, `diagnosticos`, tolerancias y
referencias h0/s0/T0/p0. Las eficiencias no definidas son `None`. Generación
en kJ/(kg·K), exergía y residuos en kJ/kg, porcentaje de suma parcial en %.
Errores: `ValueError` para ambiente o estructura inválidos, y propagación
de errores de propiedades si el estado es inconsistente. Llama a
`_ambiente_valido`, `propiedades_aire.h` y `s`. La llama `preparar_segunda_ley`
y los tests.

Ejemplo real:

```python
from ciclo_cp_variable import resolver_ciclo
from segunda_ley_cp_variable import analizar_segunda_ley_cp_variable
ciclo = resolver_ciclo(288.15, 1600, 10, 100, .85, .90, .05)
estudio = analizar_segunda_ley_cp_variable(ciclo, 288.15, 100)
print(estudio['destruccion'])  # aprox. (23.78256, 24.00679) kJ/kg
```

`zip(entalpias,entropias)` empareja propiedades del **mismo estado**.
`tuple(...)` conserva cuatro valores ordenados. `None` distingue un resultado
matemáticamente no aplicable del número cero. `diagnosticos` permite advertir
de una generación negativa significativa sin falsearla como valor cero.

### `cp_variable_web._ciclo_para_segunda_ley(T1, T3, rp, p1, eta_c, eta_t, delta)`

Siete números reales con K/kPa/fracciones, retorna el `dict` de 2B.
La llama `preparar_segunda_ley`, y ella llama `resolver_ciclo`, con sus
excepciones originales. La decoración `@lru_cache(maxsize=16)` conserva hasta
16 resultados identificados por estos **siete** argumentos. Como no recibe
T0/p0, modificar solo el ambiente no resuelve otra vez el ciclo. Ejemplo:
`_ciclo_para_segunda_ley(288.15,1600,10,100,.85,.9,.05)`.
Importante: el diccionario cacheado se trata como **solo lectura**; el
postprocesado no lo muta. No es una caché permanente de archivos.

### `cp_variable_web.svg_exergia_destruida(estudio)`

Recibe el `dict` anterior, entrega `str` con SVG o `None` si una contribución
es negativa. Las dos magnitudes de entrada son eD,c y eD,t [kJ/kg]. Devuelve
exactamente dos barras con alturas proporcionales a esos números, etiquetas,
unidades, texto alternativo (`aria-label`) y datos `<title>`.
La llama `preparar_segunda_ley`. No llama a métodos termodinámicos.
Ejemplo: `svg_exergia_destruida(estudio)` entrega una cadena SVG de dos barras
si ambas destrucciones son no negativas. `f'{valor:.3f}'` representa un
número con tres decimales **sin modificar el valor físico original**.

### `cp_variable_web.preparar_segunda_ley(entradas, T0=288.15, p0=100.0)`

`entradas`: `dict` con siete parámetros físicos; T0 [K], p0 [kPa]. Devuelve
`{'ciclo': ..., 'estudio': ..., 'svg_destruccion': ...}`. Llama a las tres
funciones anteriores —caché, postprocesado y SVG— y propaga sus errores. La
llama `web_app.index` en la acción `segunda_ley`. No llama al optimizador 2C
ni recorre una malla; un análisis ambiental no debería repetir otro estudio.
Ejemplo: `preparar_segunda_ley(cp_variable_web.DEFAULTS,300,120)`.

### Funciones existentes adaptadas

- `web_app.index()` sigue sirviendo `GET/POST /`: acepta la acción
  `segunda_ley`, convierte T0/p0 y conserva el mismo formulario de siete
  valores del ciclo. Un `ValueError` del ambiente responde 400 sin cálculo
  engañoso. Ejemplo: POST con `accion=segunda_ley`, T0=300 y p0=120.
- `dashboard.renderizar_dashboard(..., segunda_datos=None, segunda_config=None)`
  acepta dos argumentos opcionales y los comunica mediante Jinja a la plantilla
  `templates/index.html`. No calcula física. Los informes anteriores siguen
  usando la rama de plantilla `modo_cp=False` sin cambios de modelo.
- `templates/index.html` usa `{% if segunda_datos.estudio %}` para mostrar los
  resultados existentes, y `{% for indice in range(4) %}` para renderizar las
  cuatro filas; no puede crear nuevos estados físicos con JavaScript.

## 7. Qué hemos verificado y qué no

`test_segunda_ley_cp_variable.py`: 14 casos de propiedades, límites
reversibles, referencias, casos degenerados, generaciones negativas,
Gouy–Stodola y balances alternativos independientes.
`test_segunda_ley_cp_web.py`: 7 casos de GET/POST, valores, errores,
no motor, SVG, caché y rutas preservadas. Workflow GitHub Actions:
64 regresiones previas + 21 nuevas, cuando se ejecute sobre el árbol final.
Estos ensayos comprueban **implementación y coherencia matemática**;
no contrastan experimentalmente un aerorreactor ni sustituyen la inspección
visual de un navegador Windows, todavía pendiente.

## 8. Ejercicios y limitaciones

1. Calcula a mano `23.782560 / 288.15`: ¿qué unidad resulta? Compárala con
   `s2−s1` y explica la coincidencia.
2. Repite los balances de compresor `wc−(e2−e1)` y turbina
   `(e3−e4)−wt`. ¿Por qué tienen signos de trabajo opuestos?
3. Cambia p0 manteniendo T0: demuestra algebraicamente que `e2−e1` no varía.
4. Prueba `eta_c=eta_t=1` con un ciclo motor. Comprueba que ambas generaciones
   se anulan aproximadamente y explica el significado, sin decir que todos
   los procesos térmicos son reversibles.
5. Intenta formar `s3−s2` como supuesta generación de la cámara. ¿Qué término
   de entropía transportada por calor faltaría? ¿De qué fuente térmica?

La cámara es un aporte de calor **abstracto**, sin química; composición fija,
sin velocidades o cotas, sin datos de fuentes externas. Por eso la suma de
destrucciones solo cubre compresor y turbina, no la instalación completa; y no
podemos formar un rendimiento exergético global defendible. La pérdida de
presión se refleja en estados, pero no se atribuye una destrucción separada sin
definir intercambios y volumen de control.

## 9. Iteración de esta fase

- **24/10/2026:** introducción del postprocesado cp(T), referencias T0/p0,
  doble balance, diagnósticos, presentación SVG/Flask, tests y actualización
  educativa. El commit definitivo se asocia en el registro de publicación
  una vez GitHub Actions haya validado exactamente el árbol preparado.
