# Aprendizaje — Milestone 44.4: curvas de flujo físicamente calculadas

## 1. De un punto de salida a una curva

El 44.2 mostraba garganta, antes y después de choque, y salida cuando el motor los resolvía. Una tobera convergente podía producir solo un punto. Para la tobera convergente-divergente (C-D), conocemos la proporción entre garganta y salida y podemos plantear áreas intermedias **sin conocer ninguna distancia axial**.

El eje nuevo es `A/Ag`: `1` en garganta y, por ejemplo, `1,5` en salida. Para cada relación de áreas se obtiene **una solución nueva** de las ecuaciones, no un valor interpolado de un dibujo.

## 2. Las propiedades del gas importan

No se fija γ=1,4 a todas las temperaturas. `propiedades_aire.py` ofrece `cp(T)`, `h(T)`, `s0(T)`, `s(T,p)` y `gamma(T)`, con constante de gas coherente. Para flujo adiabático sin trabajo, en unidades del proyecto:

\[
h(T_t)-h(T)=\frac{V^2}{2000}.
\]

Aquí T es temperatura **estática** y Tt la temperatura **de remanso**. Conocer Tt y elegir una T estática define V. La densidad se obtiene de la ecuación del gas ideal, y el número de Mach de `M=V/\sqrt{\gamma(T)RT}`. La relación isentrópica de presión no usa la potencia de γ constante: se impone `s(T,p)=s(Tt,pt)` mediante `s0(T)` y el término `R ln(p)`.

Un gas calóricamente perfecto usaría relaciones cerradas de potencias, por ejemplo `Tt/T=1+(γ−1)M²/2` con γ constante. Son útiles en comprobaciones límite, **pero no sustituyen** al modelo de cp variable del código.

## 3. Cómo se encuentra un estado en cada área

La ecuación de masa es:

\[
\dot m=\rho V A,\qquad G(T)=\rho(T)V(T),\qquad
G(T)\frac{A}{A_g}=G_g.
\]

1. El solucionador proporciona Tt, pt y caudal por área en la garganta `Gg`.
2. Para cada nueva área relativa `r=A/Ag`, el flujo másico superficial buscado es `Gobjetivo=Gg/r`.
3. Se resuelve numéricamente `G(T)−Gobjetivo=0` en **la rama correcta** de temperatura: supersónica o subsónica.
4. Una vez hallada T, se calculan presión, densidad, velocidad, Mach, entalpía y entropía.
5. Se comprueban la conservación de `G·r`, de entalpía total y de entropía en esa región.

El mismo `Gobjetivo` puede tener dos soluciones físicas cuando hay bloqueo: una subsónica y otra supersónica. Escoger la rama requiere conocer el régimen, **no elegir la raíz con el dibujo más bonito**. El código usa los algoritmos de bisección ya existentes.

## 4. Qué se verá en las dos gráficas

En una sección **divergente supersónica**, aumentar área permite acelerar el gas: Mach aumenta y la presión estática disminuye.

En una sección **divergente subsónica**, aumentar área desacelera el gas: Mach disminuye y la presión estática crece. La garganta no bloqueada **no alcanza M=1**. Existe también una frontera delicada: garganta exactamente sónica con salida subsónica; está ensayada por separado.

Las dos curvas comparten las **mismas áreas**; cambiar parámetros altera las soluciones y los perfiles. La línea horizontal del gráfico de Mach representa M=1, y la del gráfico de presión, la presión ambiente. Son referencias, no condiciones que deban cumplirse en cada estado.

## 5. El choque normal: una discontinuidad real

Antes del choque la corriente suele ser supersónica. En una capa muy delgada, el salto lleva a:

- Mach supersónico → subsónico.
- Presión y temperatura **estáticas** mayores.
- Entropía mayor (irreversibilidad).
- Presión **total** menor.
- Entalpía **total** conservada para choque adiabático sin trabajo.

El módulo `choque_normal_cp.py` resuelve sus condiciones de masa, cantidad de movimiento y energía con cp variable. El perfil reutiliza esos dos estados **en la misma `A/Ag`**. Son dos segmentos separados unidos visualmente por una marca punteada vertical; no se calcula una falsa trayectoria continua a través del choque. Aguas abajo, el nuevo valor de presión total `pt2` determina la solución isentrópica subsónica.

Si el choque está en la salida, se representa su salto allí, sin inventar una tobera adicional exterior.

## 6. Por qué A* cambia aunque la tobera no se mueva

`Ag` es un área **geométrica** (física) y permanece fija. `A*` es el área teórica que tendría una sección sónica para las **condiciones de remanso de una región isentrópica**. Si la garganta está bloqueada antes del choque, `Ag=A*1`.

En el choque disminuye la presión total y la capacidad de flujo másico por área de una sección sónica ideal. Para transportar el mismo caudal, el área crítica asociada al flujo posterior aumenta: `A*2>A*1`. Por tanto, después del choque `A/A*2` no coincide con `A/Ag`. Mostrar ambos lados del salto con una única `A/A*` mezclando referencias sería un error físico. Por eso los gráficos usan **siempre `A/Ag`**.

## 7. Organización del código

- `perfil_tobera_cp_variable.py`: `perfil_tobera_cp_variable(resultado, *, puntos_por_region=41)` selecciona regímenes, calcula las áreas y estados, separa el choque y verifica balances. `_malla`, `_punto`, `_subsonico`, `_desde_choque` y `_validar_perfil` son auxiliares internos del módulo (no funciones anidadas). No modifica los solucionadores anteriores.
- `turborreactor_web.py`: `svg_perfil_tobera(datos, magnitud)` presenta el mismo conjunto físico para `mach` o `presion`. `preparar_vista_turborreactor` añade el perfil y ambos SVG a la vista.
- `templates/turborreactor.html`: explicaciones sencillas y gráficas nuevas; las estaciones discretas de 44.2 siguen para comparar.
- `tests/test_perfiles_tobera_44_4.py`: 16 métodos verifican ramas, choques, integridad física, extremos, ausencia de datos y compatibilidad con los milestones anteriores.

## 8. Qué significan las pruebas

Para casos C-D a Tt=1200 K, pt=500 kPa, Ae/Ag=1,5 y distintas contrapresiones, la suite verifica:

1. `ρVA` constante en todos los puntos.
2. `h(T)+V²/2000` constante en tramos adiabáticos.
3. `s(T,p)` constante en cada región isentrópica; salto positivo de entropía donde hay choque.
4. Garganta sónica solo donde corresponde.
5. Monotonía de ramas y extremos idénticos al solver.
6. Discontinuidad normal, pt posterior y nueva A*.
7. Consistencia con 11 frente a 61 puntos y ausencia de datos falsos.
8. SVG bien formados y preservación de la integración 44.1–44.3.

Resultado previo del entorno de desarrollo: **16/16 específicas y 140/141 en regresión relacionada**, con una omisión legítima por Cantera opcional ausente y **ningún fallo ni error**. En ese entorno no estaban instalados Flask/Jinja2. La revisión Windows posterior sí utiliza las dependencias existentes y se describe al final.

Estas son pruebas de **verificación de implementación**; la validación física externa requeriría resultados experimentales o modelos independientes adecuados.

## 9. Límites que conviene recordar

El modelo no conoce la coordenada axial de la tobera, un choque exterior ni la separación de capa límite. Las curvas no son fotografías de un motor real. Una tobera convergente sin mapa de áreas mantiene la gráfica discreta del 44.2. No se extrapola si el solucionador no encuentra un estado físico dentro de 200–2000 K.


## 10. Integración Windows y aprendizaje de revisión — cierre 28/10/2026

**Estado anterior verificado.** La rama `mejoras/cp-variable` estaba en
`d61ef3795ae58027927adc5077409bb3dfe6b018` (M43), con 44.1/44.2 sin commit
pero ya revisados en Windows. Se incorporan 44.3/44.4 desde el ZIP completo,
no desde versiones anteriores. Se conservan el ajuste de T–s y los cuatro
documentos anteriores. El hash base no contiene el milestone 44; sigue sin
commit propio ni publicación. Esta sección fecha la revisión, no reconstruye
una supuesta fecha de implementación de las funciones.

**PYTHON — estructura y contratos.** El nuevo módulo ofrece
`perfil_tobera_cp_variable(resultado, *, puntos_por_region=41)`: recibe un
`dict` científico y un entero 3–121; devuelve un diccionario de disponibilidad,
regiones y estados descritos en §7 y en el manual. El `*` obliga a pasar el
control por nombre: `perfil_tobera_cp_variable(r, puntos_por_region=11)`.
Los valores de T están en K, p en kPa, V en m/s, h en kJ/kg, s en kJ/(kg·K)
y G en kg/(m²·s). A/Ag, Mach y factores de área son adimensionales.

| Función auxiliar y firma | Papel, entradas, salida y relaciones |
|---|---|
| `_malla(inicio, fin, puntos)` | Dos reales A/Ag y entero → tupla ordenada; la llama el perfil. Ej.: `_malla(1,1.5,3)` retorna `(1.0,1.25,1.5)`. No interpola propiedades físicas. |
| `_punto(area, estado, Tt, pt, g_star, rama, papel="intermedio")` | Área [-], dict del solver, Tt [K], pt [kPa], G* [kg/(m²·s)] o `None`, y cadenas → dict de estado con residuos. Llama `h` y `s`; la llaman perfil y `_desde_choque`. |
| `_desde_choque(area, choque, lado, Tt, g_star)` | A/Ag, dict de choque, `'antes'`/`'despues'`, Tt y G* → estado exacto de ese lado mediante `_punto`; lo llama el perfil. No vuelve a resolver el choque. |
| `_subsonico(Tt, pt, temperatura_sonica, flujo_objetivo)` | K, kPa, K y kg/(m²·s) → dict `_estado`; reutiliza `_biseccion` y `_estado`. Lo llama el perfil para la raíz subsónica. |
| `_validar_perfil(segmentos, flujo_garganta, *, salto=None)` | Tuplas de estados, Gg y salto opcional → `None`; lo llama el perfil. Lanza `ErrorNumericoCiclo` ante incumplimiento de masa, energía, entropía o choque. |
| `ausente(motivo)` | Función anidada: cadena → dict con `disponible=False`, motivo, segmentos vacíos, choque `None` y régimen; la llama solo el perfil. |

Los auxiliares esperan estados del solver, no entradas arbitrarias. Las claves
obligatorias ausentes producen `KeyError`; los errores de dominio y numéricos
se propagan. La función pública rechaza controles de discretización inválidos
con `ValueError`. El manual §4.84 da el esquema completo y tolerancias: caudal
`2e-6 × max(1,abs(Gg))`, energía `1e-7`, entropía regional `1e-8`, y salto en
la misma área con tolerancia `1e-12`. No se ajustan los resultados para que
la gráfica parezca cerrar.

`svg_perfil_tobera(datos, magnitud)` recibe ese dict y `'mach'` o `'presion'`,
retorna `str` SVG o `None` si no hay perfil, y rechaza otras magnitudes con
`ValueError`. La llama `preparar_vista_turborreactor`, después de calcular el
perfil una vez; Flask usa la vista tras POST. Cada tupla regional se transforma
en una polilínea: el salto es un trazo vertical separado, sin fabricar estados.
Ejemplo: `svg_perfil_tobera(perfil_tobera_cp_variable(r), 'mach')` para un `r`
C-D ya calculado. Los ejes de dibujo son coordenadas gráficas, no metros.

**INGENIERÍA — experimentos reproducidos.** El formulario inicial también
es la convergente bloqueada: no hay perfil de área. Mach=0,9, rp=3, πd=0,7 y
T3=600 K da convergente no bloqueada; con C-D y Ae/Ag=1,5 da rama subsónica.
El motor inicial con C-D y Ae/Ag=1,5 da salida supersónica; con Ae/Ag=6,
choque interno. La geometría Ae/Ag≈5.206112788473547 sitúa el choque en salida
según la contrapresión umbral del solucionador, sin prolongar una rama exterior.
Reducir T3 a 500 K en el caso Mach=0,9/rp=3/πd=0,7 elimina la expansión:
los perfiles desaparecen y la energía cinética de salida es «No disponible».
No confundir estas ocho configuraciones con el ejemplo de tobera aislada de §8.

**Pruebas y resultado real del 27/10/2026.** 42/42 específicas acumuladas,
74/74 web y 651 de regresión vigente: 641 correctas, 0 fallos, 0 errores,
diez omisiones (8 SciPy, 1 Cantera y 1 subcaso de enlace simbólico). El primer
recuento falló por exigir 7 SVG cuando el balance añade el octavo; el usuario
autorizó esa corrección en M40 y se repitió la suite. Un HTTP 500 de una
instancia anterior se resolvió reiniciando el servidor actualizado, sin cambiar
el modelo ni corregir código. La revisión de seis secciones, teoría, OFAT,
mapa, tamaño grande/estrecho y teclado está completada para los casos indicados.
Comandos y resultados iniciales/finales: [técnico 44.4](44_4_perfiles_cuasidimensionales_tobera.md).
Es verificación interna y de integración, no validación experimental. No se
instalan dependencias ni se modifican los solucionadores; quedan las limitaciones
cuasi-1D y de composición equivalente descritas en §9.
