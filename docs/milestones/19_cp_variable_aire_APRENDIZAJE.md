# Fase 2A — Aprendizaje: propiedades del aire con cp(T)

Fecha de preparación: **23 de octubre de 2026**. Base Git verificada: `96449ca4960778ec7de6b910330b148dc5ece4d3` (`mejoras/verificacion-numerica`); desarrollo aislado en `mejoras/cp-variable`. El repositorio de conservación del modelo de propiedades constantes no se ha tocado. Esta fase crea solamente un módulo de propiedades y pruebas/documentación; no modifica los motores de cálculo actuales.

## 1. Punto de partida y problema

El Brayton existente estudia gas ideal y obtiene saltos de temperatura, trabajos, calor, entropía y óptimos con dos constantes: `cp=1005 J/(kg·K)` y `gamma=1.4`. Eso funciona como **modelo educativo caloríficamente perfecto**, pero cp de N₂ y O₂ varía cuando aumenta la temperatura; por tanto gamma también varía.

Queremos preparar, **antes de integrar nada**, seis funciones independientes que den propiedades de aire ideal. Así se podrán contrastar las propiedades por separado y no confundir futuros fallos de un solucionador con errores en sus datos termodinámicos.

## 2. Modelo y referencias

**INGENIERÍA.** Composición fija por fracción **molar**: 0,78 N₂, 0,21 O₂, 0,01 Ar. El aire se trata como mezcla ideal; la masa molar media es:

```text
M = 0.78·0.0280134 + 0.21·0.0319988 + 0.01·0.039948
  = 0.02896968 kg/mol
R = 8.31446261815324 / M = 287.005677 J/(kg K)
```

Los valores de masa molar, tramos y coeficientes proceden de [N₂ NIST](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Mask=1), [O₂ NIST](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7782447&Mask=1) y [Ar NIST](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7440371&Mask=1), consultados el 23/10/2026. Las correlaciones de N₂ cambian en 500 K; las de O₂, en 700 K. El argón monoatómico ideal tiene `cp,m = 5·Ru/2`. El intervalo del **módulo** está limitado expresamente a 200–2000 K, aunque NIST también proporciona datos a otras temperaturas.

**PYTHON.** `_ESPECIES` es una tupla de ternas inmutables `(nombre, y, M_i)`. `_SHOMATE` es un diccionario; cada valor guarda `(frontera, tupla_A_H_baja, tupla_A_H_alta)`. Recuperar la tupla apropiada con `if` es más sencillo y verificable que dispersar muchos números por funciones diferentes.

## 3. Calor específico, entalpía y entropía

Con `t=T/1000`, la correlación Shomate define la capacidad calorífica molar:

```text
cp,m = A + B*t + C*t² + D*t³ + E/t²            J/(mol K)
```

Su primitiva de entalpía de NIST es `A*t+B*t²/2+C*t³/3+D*t⁴/4−E/t+F−H` (kJ/mol). La de entropía es `A ln(t)+B*t+C*t²/2+D*t³/3−E/(2t²)+G` (J/(mol·K)). El código convierte primero la entalpía a J/mol y trabaja con **diferencias** desde 298,15 K. No se presentan magnitudes absolutas:

```text
h(Tref)=0       s0(Tref)=0      Tref=298.15 K
h(T)=∫(Tref→T)cp(u)du / 1000                kJ/kg
s0(T)=∫(Tref→T)cp(u)/u du / 1000            kJ/(kg K)
s(T,p)=s0(T) − (R/1000) ln(p/100 kPa)       kJ/(kg K)
gamma(T)=cp(T)/(cp(T)−R)                     adimensional
```

**Las fracciones molares son importantes:** se calcula primero `Σ y_i cp,m,i`, luego se divide por `M` para expresar J/(kg·K). Si se multiplicaran directamente capacidades molares por fracciones másicas, el resultado sería incorrecto. La entropía ideal de mezcla constante no altera los cambios de entropía de una composición fija; por ello `s0` es relativa a `(298,15 K; 100 kPa)`.

### Empalmes de dos polinomios

**INGENIERÍA.** Cada correlación Shomate es un ajuste independiente: al pasar de 499,999 a 500,001 K, los coeficientes de N₂ cambian. Las constantes publicadas de entalpía/entropía pueden producir diferencias numéricas minúsculas entre ambos tramos. La función `_incremento_molar` calcula la primera integral desde Tref hasta la frontera y, sólo por encima de ésta, añade la integral del segundo tramo desde la frontera. Así el valor de h y s0 **se une sin saltos**; no se falsea el calor específico para obligar a coincidir las derivadas.

**PYTHON.** Una función puede recibirse como argumento. `_incremento_molar(nombre, T, primitiva)` acepta `_h_shomate` o `_s_shomate` sin duplicar la lógica de empalme. Cada primitiva tiene las unidades indicadas en §4.57 del manual.

## 4. API pública: firmas, unidades y errores

Todas las funciones son escalares; `T` en K debe ser un número real finito entre 200 y 2000 K, inclusive.

| Función | Entradas y resultado | Llama a / la invoca | Ejemplo |
|---|---|---|---|
| `cp(T)` | T real → `float` J/(kg·K) | `_temperatura`, `_coeficientes`, `_cp_shomate`; la usan `gamma` y tests | `cp(300)≈1004.414` |
| `h(T)` | T real → `float` kJ/kg relativo | `_temperatura`, `_incremento_molar`, `_h_shomate`; la usa `T_desde_h` | `h(1000)≈747.4853` |
| `s0(T)` | T real → `float` kJ/(kg·K) relativo | `_temperatura`, `_incremento_molar`, `_s_shomate`; la usa `s` | `s0(1000)≈1.271674` |
| `s(T,p)` | T real K, p real positiva kPa → `float` kJ/(kg·K) | `_temperatura`, `_real_finito`, `s0`, `log`; pruebas y usuarios | `s(298.15,100)=0` |
| `gamma(T)` | T real → `float` adimensional | `cp`; pruebas y usuarios | `gamma(300)≈1.400059` |
| `T_desde_h(entalpia)` | h real finita kJ/kg dentro de rango → `float` K | `_real_finito`, `h`, bisección; pruebas y usuarios | `T_desde_h(h(1000))≈1000` |

Si hay `True`, `False`, texto, `None`, número complejo, `NaN`, infinito o temperatura/entalpía fuera del rango, se eleva `ValueError`. La presión, además, debe ser estrictamente positiva. El módulo no trata una temperatura fuera de 200–2000 K como un resultado científico válido ni extrapola en silencio.

## 5. Aprendizaje de programación: validación y bisección

**`numbers.Real` y `bool`.** En Python `bool` es subclase de `int`: `True==1`. Por eso no basta `isinstance(T, (int,float))`; `_real_finito` comprueba primero `isinstance(valor,bool)` y después si es un real finito, capturando también un `OverflowError` para enteros de tamaño absurdo. `_temperatura` comprueba el intervalo y convierte el escalar a `float`. Las funciones públicas llaman al validador al principio, no después de calcular un logaritmo.

**Bisección.** `T_desde_h` no conoce una fórmula despejada de T porque cp depende de T. Primero comprueba `h(200)<=h_obj<=h(2000)`; después calcula la temperatura media y conserva la mitad cuyo intervalo contiene el objetivo. `cp>0` garantiza que h crece estrictamente y el método no converge a una raíz equivocada:

```python
inferior, superior = 200.0, 2000.0
medio = (inferior + superior)/2
if h(medio) < entalpia:
    inferior = medio
else:
    superior = medio
```

Se repite con límite de 80 iteraciones y se detiene cuando el intervalo de temperatura mide como máximo `1e-10 K`. Esa cifra describe un **criterio numérico**, no precisión física de las correlaciones. No hace falta SciPy porque h es monótona en todo el dominio.

**Logaritmos estables.** La forma `log(p)-log(P_REF)` es algebraicamente equivalente a `log(p/P_REF)` para p positiva, pero soporta presiones muy pequeñas para las que la división podría redondearse a cero.

## 6. Recorrido práctico, experimentos y comprobaciones

Abre Python en la carpeta del proyecto (sin ejecutar Flask):

```python
import propiedades_aire as aire

temperatura = 1000.0
print(aire.cp(temperatura))          # J/(kg K)
print(aire.gamma(temperatura))       # sin unidades
print(aire.h(temperatura))           # kJ/kg respecto a 298.15 K
print(aire.s(temperatura, 200.0))    # kJ/(kg K), a 200 kPa
print(aire.T_desde_h(aire.h(temperatura)))  # vuelve a 1000 K
```

Prueba además temperaturas justo por debajo/encima de 500 y 700 K. Observa que **h y s0** son continuas y que pequeñas discrepancias en cp entre polinomios no equivalen a una discontinuidad física grande. Compara `gamma(300)` y `gamma(1000)`: no puede suponerse un gamma fijo si cp cambia, aunque el gas siga obedeciendo `pV=nRT`.

### Pruebas verificadas, 23/10/2026

Se ejecutaron **17/17 métodos nuevos correctos** en Python estándar; cubren los coeficientes A–H extraídos de NIST, referencias cp, conversión molar, derivadas centradas, cuadratura trapezoidal, empalmes, presión, cp positivo, monotonía/inversión, límites cerrados y errores controlados. Un caso directo de `viabilidad.evaluar_punto` reprodujo `505,619018249` y `369,476301045 kJ/kg` de trabajo ideal/no ideal de referencia; el nuevo módulo no participa en él. La única tentativa de descubrimiento de toda la suite contabilizó 88 métodos y terminó con **19 errores de importación** de tests históricos porque falta `jinja2`/Flask en el intérprete disponible; no es una regresión física reproducible y no se declara superada la suite. No se instalaron dependencias. Las pruebas del módulo aislado no necesitan esas bibliotecas.

## 7. Qué no hemos hecho y qué vendrá en 2B

No se ha cambiado `main`, los nueve parámetros físicos, las raíces de viabilidad, los óptimos, las gráficas o Flask. No se han creado nuevas rutas, reportes ni dependencias. Los informes HTML existentes siguen perteneciendo al modelo de propiedades constantes.

**Siguiente paso propuesto, no implementado:** definir balances con `h(Tj)−h(Ti)` en lugar de `cp·ΔT`; resolver estados isentrópicos como raíces de `s(Tsalida,psalida)=s(Tentrada,pentrada)`, y estudiar límites y robustez. Las eficiencias de compresor y turbina deberán reinterpretarse como diferencias de **entalpías**, no temperaturas. Eso requiere nueva autorización y pruebas separadas.

## 8. Limitaciones y estado Git

El aire es ideal de composición fija 78/21/1, sin humedad, combustión, mezcla cambiante ni disociación. No se cuantifica el error de los ajustes NIST ni se contrastan prestaciones de un motor; la coherencia entre ecuaciones es **verificación matemática**, no validación experimental. Las fronteras Shomate garantizan continuidad de integrales, pero cp puede tener diferencias pequeñas entre lados.

**Estado de preparación:** rama `mejoras/cp-variable`, base `96449ca4960778ec7de6b910330b148dc5ece4d3`; commit final pendiente al redactar. La autoría y el hash de publicación deberán verificarse después sin editar históricos ajenos.
