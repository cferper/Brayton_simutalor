# Aprendizaje — Milestone 38: explorar diseño con mapas paramétricos

**Fecha de implementación:** 25-10-2026. **Rama:** `mejoras/cp-variable`.
**Punto de partida verificado:** `bdb869d609d34712b824d9a80006d9dd1b5c0bc0`.
**Commit de la fase:** pendiente de su publicación y CI.

## 1. Qué existía y qué resolvemos ahora

El milestone 37 calculaba un único turborreactor con combustible, empuje neto
y TSFC. Queremos aprender qué ocurre al **variar entradas del modelo** y
comparar objetivos que pueden competir. Creamos
`mapas_prestaciones_turborreactor_cp.py`; este archivo **no reimplementa**
las turbomáquinas: llama al solucionador existente en cada combinación.

Un barrido paramétrico no es una simulación real fuera de diseño. Cambiar
`rp` y `T3` independientemente equivale a preguntar por **configuraciones
prescritas distintas**. Un motor concreto también tendría mapas de compresor
y turbina, geometría, velocidad de giro, caudal, bombeo y límites de material;
ninguno de ellos se calcula aquí.

## 2. Ingeniería: qué significan las tendencias

Para cada `rp`, el compresor obtiene `h2` y consume
`wc=h2-h1` [kJ/kg aire]. Aumentar la relación de compresión a igualdad
de condiciones de entrada normalmente eleva `wc`. La turbina debe aportar
el trabajo requerido mediante

\[
\eta_m(1+f)(h_3-h_4)=h_2-h_1.
\]

Esto puede reducir la entalpía y presión de la turbina a la salida, por lo
que no hay garantía de que subir `rp` siempre aumente empuje. Subir `T3`
afecta al calor químico demandado, `f`, la expansión de turbina y la tobera:
el empuje suele crecer dentro de algunos intervalos, pero también puede
empeorar el TSFC. **No extrapoles estas tendencias a cualquier dominio.**

En vuelo, el empuje específico neto se calcula con

\[
F_s=(1+f)V_e-V_\infty+(1+f)\frac{1000(p_e-p_\infty)}{\rho_eV_e}.
\]

Cambiar Mach modifica `V_inf`, presión total de remanso y difusión; cambiar
altitud ISA altera la presión y temperatura ambiente. Sin gasto másico
absoluto, un aumento de `Fs` por kg/s **no** asegura aumento del empuje
total de un motor dado: `F=Fs*mdot_aire` y `mdot_aire` es desconocido.

## 3. Evaluación discreta, extremos y Pareto

Elegimos dos vectores, por ejemplo `rp=[5,10,15]`, `T3=[1400,1600]`.
El programa evalúa 3×2=6 casos. Una **malla** no resuelve derivadas ni busca
un óptimo continuo: entre sus muestras podrían existir puntos mejores.
Si un máximo está en el borde, no sabemos si aumentar el dominio lo mejora.

De los puntos **válidos con empuje positivo** obtenemos:

- El de mayor `Fs` (preferible para empuje por unidad de aire).
- El de menor `TSFC` [kg/(N·h)] (preferible para consumo por unidad de empuje).

Puede que no coincidan. Para no elegir arbitrariamente un peso entre ambas
metas, utilizamos la **dominancia de Pareto**. A domina B cuando:

\[
F_{s,A}\ge F_{s,B},\quad TSFC_A\le TSFC_B,
\]

y al menos una desigualdad es estricta. Los puntos no dominados forman un
conjunto de compromisos: no puedes mejorar un objetivo sin empeorar el otro
dentro de las muestras. El método compara cada punto con todos los demás,
coste aproximado O(n²) para n puntos: suficientemente sencillo para estas
mallas pequeñas. Dos configuraciones con **idénticos objetivos** se conservan
ambas, pues no existe mejora estricta.

Un frente de Pareto solo es interpretable **bajo condiciones comparables**.
Por eso el mapa `rp–T3` usa un ambiente y Mach fijos. El mapa `Mach–altitud`
resume valores extremos *descriptivos* en condiciones de vuelo distintas, y
establece `pareto=None`: no presenta una falsa competencia equivalente.

## 4. Cómo se programa: funciones y datos

La siguiente tabla explica **todas las funciones nuevas**. Los auxiliares
empiezan por `_`, convención Python que indica uso interno, no prohibición
absoluta de acceso.

| Firma | Entrada y unidades | Salida / llamadas | Control y error |
|---|---|---|---|
| `_eje(valores, nombre, minimo, maximo, incluir_maximo=True)` | Secuencia de reales y límites del eje (unidades según variable: rp/Mach [-], T3 [K], ISA [m]) | Tupla creciente de valores; la llaman los barridos públicos | `ValueError` por vacíos, duplicados, no finitos y fuera de rango |
| `_restricciones(configuracion)` | Dict opcional con T3_max [K], rp/Mach [-], ISA [m], dos booleanos | Dict con restricciones normalizadas; lo llama `_barrer` | `ValueError` por nombres y límites incoherentes |
| `_incumplimiento(entradas, config)` | Dict de inputs de un punto y restricciones | Nombre de límite incumplido o `None`; lo llama `_punto` | Comprueba antes del cálculo, evita invocar el motor fuera de diseño admitido |
| `_punto(entradas, indices, config)` | Parámetros del solucionador, índices `(fila,columna)`, límites | Dict de estado, motivo, métricas o `None`, y resultado completo. Lo llama `_barrer`; invoca milestone 37 | `ValueError`/`EstadoFueraDeRango` → inadmisible; `ErrorNumericoCiclo` → fallo_numerico; errores de programación se propagan |
| `frente_pareto(puntos)` | Lista de dicts con `estado`, `Fs` [N/(kg/s)] y `TSFC_kg_N_h` [kg/(N h)] | Lista de los dicts originales no dominados; la llama `_resumen` | Rechaza datos incoherentes marcados válidos, `ValueError` |
| `_resumen(puntos, nx, ny, comparar)` | Lista plana de puntos, dimensiones, flag de comparabilidad | Dict de contadores, extremos y Pareto o `None`; lo llama `_barrer` | Si no hay puntos válidos, extremos `None`, Pareto `[]` solo si comparable |
| `_barrer(nombre, eje_x, eje_y, fijo, nombre_x, nombre_y, restricciones, comparar)` | Tuplas de ejes, parámetros fijos, nombres, límites, flag | Dict de filas, máscaras, contadores, extremos, unidades; lo llaman las funciones públicas | Clasifica cada punto sin inventar ceros |
| `barrer_rp_t3(valores_rp, valores_T3, *, mach=0, pi_d=1, T_amb=None, p_amb=None, altitud_geopotencial=None, eta_c=.85, delta=.04, eta_t=.9, eta_m=.98, eta_n=.95, eta_b=.99, PCI=43000, restricciones=None)` | Ejes rp [-], T3 [K], ambiente fijo directo (288.15 K/100 kPa por defecto) o ISA [m]; resto según milestone 37 | Mapa comparable con Pareto; llama `_eje` y `_barrer` | Valida ejes; rechaza combinar ISA y ambiente directo |
| `barrer_mach_altitud(valores_mach, valores_altitud, *, rp=10, T3=1600, pi_d=.98, eta_c=.85, delta=.04, eta_t=.9, eta_m=.98, eta_n=.95, eta_b=.99, PCI=43000, restricciones=None)` | Mach [-] en [0,1), ISA [m] en [0,20000], resto según milestone 37 | Mapa descriptivo `pareto=None`; llama `_eje` y `_barrer` | Valida dominios de ambos ejes |

**Python básico:** `enumerate(eje)` devuelve `(índice,valor)` para guardar
posiciones y valores sin contadores manuales. `dict(fijo)` copia parámetros
constantes en cada iteración; al asignar `parametros[nombre_x]=x` no se
modifica el diccionario original. Las **comprensiones de listas** construyen
filas del mapa y filtran los puntos válidos. `Counter` contabiliza cuántas
configuraciones hay por estado sin escribir cinco contadores independientes.
`None` representa valor no definido y es diferente de `0`, que sería un
resultado numérico válido. Un diccionario con `"estado":"inadmisible"`
puede conservar algunos valores pero no inventa empuje ni TSFC.

Los estados son:

1. `valido`: empuje neto positivo y tobera resuelta.
2. `empuje_no_positivo`: el modelo calcula neto cero/negativo; TSFC no aplicable.
3. `sin_expansion`: p4 no supera presión ambiente; la tobera no se resuelve.
4. `inadmisible`: restricción o condición física/térmica rechazada.
5. `fallo_numerico`: error de inversión/representación conocido; se reporta.

No se captura `Exception` genérica: un `TypeError` por error de programación
no debería disfrazarse como un punto de diseño imposible.

## 5. Ejemplos para reproducir

```python
from mapas_prestaciones_turborreactor_cp import barrer_rp_t3, barrer_mach_altitud

A = barrer_rp_t3([5,7.5,10,12.5,15],[1400,1500,1600,1700,1800])
B = barrer_mach_altitud([0,.2,.4,.6,.8],[0,5000,10000,15000,20000])
C = barrer_rp_t3([4,6,8,10,12,14,16,18,20],[1600])

print(A['validos'], A['maximo_Fs']['valor'], len(A['pareto']))
print(B['minimo_TSFC']['valor'], B['pareto'])
print(C['maximo_Fs']['punto']['entradas']['rp'])
```

Resultados calculados: A tiene 25/25 válidos, máximo Fs=1077.68437665
en (rp=15,T3=1800 K), mínimo TSFC=0.08620228954 en (15,1400 K) y siete
no dominados. B tiene 25/25 válidos, mínimo descriptivo de TSFC=0.10583047074
en Mach=0, ISA=0 y **ningún Pareto global** (`None`). C tiene 9/9 válidos,
máximo Fs=966.08429353 en rp=14, mientras que TSFC mínimo=0.09215888895
ocurre en rp=20; son dos configuraciones distintas.

Prueba también:

```python
D = barrer_rp_t3([5,10],[1400,1600], restricciones={'T3_max':1500})
print(D['por_estado'], D['puntos'][1][0]['Fs'])
```

Los valores con T3=1600 K se descartan como `inadmisible` y `Fs` queda
`None`; 1500 K aquí es un **límite de diseño escogido por el usuario**, no
una temperatura de daño demostrada de un material aeroespacial.

## 6. Verificación y ejercicios

`tests/test_mapas_prestaciones_turborreactor_38.py` prueba el contrato con
el solucionador 37, las formas y unidades, la clasificación física, los
extremos independientes usando `max/min`, el Pareto sintético con puntos
duplicados, el vacío, los bordes de malla, la repetibilidad, restricciones,
los errores numéricos deliberados y que un `TypeError` no se oculta.

Prueba específica ejecutada: 15 métodos correctos. La suite completa y
CI se registrarán en el informe final tras ejecutarlas. Son **pruebas de
software**, no validación de un turborreactor físico real.

**Ejercicios sugeridos:** (i) amplía el rango de rp y comprueba si cambia
el extremo; (ii) compara curvas de Fs y TSFC a T3 fija; (iii) fija
`T3_max=1500 K` y observa la nueva frontera; (iv) calcula a mano la
dominancia de cuatro puntos sintéticos. En todos los casos, no atribuyas
factibilidad real a los parámetros: no hay compatibilidad de caudales,
velocidad de giro ni límites de bombeo.

## 7. Referencias y limitaciones

El enfoque recuerda a los [gráficos de prestaciones NACA/NASA](https://ntrs.nasa.gov/citations/19930093534),
pero no reutiliza sus datos. Definición de consumo:
[NASA Glenn, TSFC](https://www.grc.nasa.gov/www/k-12/airplane/sfc.html).
Las correlaciones del gas equivalente están restringidas a 200–2000 K,
Mach subsónico y altitud ISA hasta 20 km. Sin caudal no existe predicción
de empuje absoluto o prestaciones reales fuera de diseño.
