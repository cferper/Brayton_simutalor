# Nuevo Plan de Mejoras — Fase 1, Tarea 1.1: verificación analítica del Brayton ideal

Documento educativo del **22 de octubre de 2026**. No debe confundirse esta **nueva Fase 1 de verificación numérica y comparación de modelos** con la **antigua Fase 1 de dominio físicamente viable** ([milestone 03](03_dominio_viable.md)).

**Base comprobada:** `27d4519094d5eb74f5009a1889a1e74dc8dddb94` (rama remota `main`, merge de segunda ley). La copia local estaba inicialmente en `main`, sin cambios ajenos: sólo `CODE_WALKTHROUGH.md` modificado y `tests/test_verificacion_analitica.py` sin seguimiento. La implementación de esta tarea se conserva en la rama de desarrollo `mejoras/verificacion-numerica`. **Commit asociado:** pendiente de registrar; el hash de la base no es el de esta tarea.

## 1. Estado anterior y propósito

Antes de la tarea, el simulador calculaba ciclos ideales y no ideales, clasificaba el dominio motor, buscaba óptimos analíticos y numéricos, estudiaba sensibilidad, mapas y segunda ley. Ya existían pruebas de referencias físicas, límite reversible, fronteras, relación óptima, búsqueda numérica independiente del candidato analítico e integración. No se han duplicado esas verificaciones de forma aislada.

Faltaba contrastar **sistemáticamente varios puntos motores ideales** con expresiones escritas directamente en el propio test y medir los residuos de conservación. El objetivo es detectar errores de implementación en estados, unidades, signos, energía y rendimiento **antes** de añadir modelos más complejos. Se añade únicamente `tests/test_verificacion_analitica.py` y se actualiza el manual; las funciones de producción, constantes, optimizadores, HTML, Flask y dependencias **no cambian**.

## 2. Interpretación física y referencias independientes de implementación

Hipótesis: gas ideal con `cp` y `gamma` constantes; compresión y expansión isentrópicas, calentamiento y enfriamiento isóbaros; ciclo motor abierto en relación de presiones (`rp>1` y aporte/trabajo positivos). `T1` y `T3` son temperaturas absolutas en K; `cp` se recibe en J/(kg·K), `rp` y `gamma` son adimensionales.

Las referencias se construyen **sin llamar a `calcular_estados`, `calcular_temperaturas` ni `calcular_ciclo_ideal`** para obtener los valores esperados:

```python
a = (gamma - 1) / gamma
T2_ref = T1 * rp**a
T4_ref = T3 / rp**a
wc_ref = cp * (T2_ref - T1) / 1000
wt_ref = cp * (T3 - T4_ref) / 1000
qin_ref = cp * (T3 - T2_ref) / 1000
qout_ref = cp * (T4_ref - T1) / 1000
```

**INGENIERÍA.** `wc` representa consumo positivo de compresor; `wt`, trabajo positivo de turbina; `qin`, calor aportado, y `qout`, calor rechazado positivo. Dividir por 1000 convierte J/kg a **kJ/kg**. El código devuelve `wc`, `wt`, `wneto` y `qin`, pero **no** devuelve `qout`: en las pruebas se obtiene a partir de las temperaturas.

Se comprueban las identidades de primera ley:

\[
w_{neto}=w_t-w_c=q_{in}-q_{out},\qquad
R_E=w_{neto}-(q_{in}-q_{out})\quad [\mathrm{kJ/kg}].
\]

La comparación de estados y energías con ecuaciones escritas en el test es una referencia **separada del código de producción**, aunque algebraicamente usa el **mismo modelo físico**. Las igualdades de trabajo y primera ley, incluido `R_E`, son **controles internos de consistencia**; no constituyen dos experimentos independientes ni prueban que el modelo describa un motor real.

El rendimiento ideal se contrasta como fórmula analítica y como cociente, siempre en **puntos motores** previamente clasificados por `evaluar_punto`:

\[
\eta_{ideal}=1-r_p^{-a}=\frac{w_{neto}}{q_{in}},\qquad q_{in}>0.
\]

Las fronteras con aporte nulo y los puntos no motores quedan deliberadamente fuera de esta tarea; no se divide entre cero ni se inventa un rendimiento motor.

En el **máximo de trabajo específico** para `T1`, `T3` constantes se cumple:

\[
r_{p,*}=\left(\frac{T_3}{T_1}\right)^{1/(2a)},
\qquad T_{2,*}=T_{4,*}=\sqrt{T_1T_3}.
\]

El test comprueba ambas temperaturas en la solución analítica y también en los estados que devuelve una llamada **directa** a `buscar_maximo_numerico`. Este buscador explora un dominio interior y refina mediante sección áurea, sin consultar el candidato analítico para localizar el máximo. La igualdad de temperaturas es una propiedad adicional, distinta de volver a comprobar solamente `rp_*`.

## 3. PYTHON — cómo están organizadas las pruebas

La clase `VerificacionAnaliticaIdealTests(unittest.TestCase)` reúne cuatro métodos. Cada uno recibe sólo `self`, no devuelve resultados físicos (retorno implícito `None`) y `unittest` lo invoca automáticamente. Las cinco tuplas de `CASOS` contienen `(nombre, T1, T3, gamma, cp, rp, p1)` con unidades del apartado anterior y `p1` en kPa. Todos son moderados, representables y motores. El último método utiliza sólo los tres primeros para las búsquedas.

| Firma del método | Qué comprueba | Funciones existentes llamadas |
|---|---|---|
| `test_estados_con_referencias_isentropicas(self)` | T1–T4, T2s y T4s [K] contra potencias isentrópicas directas | `main.calcular_ciclo_ideal` |
| `test_balances_con_referencias_y_residuo(self)` | Cuatro energías [kJ/kg], `wn=wt-wc`, `wn=qin-qout`, residuo y comparación con calor de referencia | `main.calcular_ciclo_ideal` |
| `test_rendimiento_analitico_frente_a_balance_motor(self)` | Viabilidad, `qin>0`, rendimiento [fracción] como fórmula y cociente | `evaluar_punto`, `main.calcular_rendimiento` |
| `test_temperaturas_coinciden_en_maximo_ideal_analitico_y_numerico(self)` | T2=T4=raíz geométrica [K] en candidato y búsqueda numérica motor interior | `main.calcular_relacion_optima`, `main.calcular_temperaturas`, `calcular_dominios`, `buscar_maximo_numerico` |

**Errores y validación.** Los cinco casos se seleccionan en el dominio admisible; por ello las funciones no deberían lanzar `ValueError` o `ErrorNumerico` en su uso normal. Un resultado que supere una tolerancia produce una aserción fallida (`AssertionError`) con nombre de caso, magnitud, error y tolerancia. Otras excepciones de producción se propagan para que `unittest` las muestre como errores, no como resultados físicos.

### ¿Qué aporta `unittest.subTest()`?

```python
for nombre, T1, T3, gamma, cp, rp, p1 in self.CASOS:
    with self.subTest(caso=nombre):
        # Calcular referencia y resultado; comprobar tolerancias.
        ...
```

**PYTHON.** `for` desempaqueta cada tupla, y `with` abre un contexto que identifica el caso. Si falla una aserción, el informe señala, por ejemplo, `caso='gamma_133'`, y se siguen examinando los demás casos. No se crean cinco métodos distintos ni se cambia el modelo por usar `subTest`. La salida de `unittest` cuenta **cuatro métodos**, con **18 casos parametrizados** (5+5+5+3), no 18 métodos independientes.

## 4. Errores y tolerancias

- **Error absoluto:** `abs(calculado-referencia)`, con la unidad de la magnitud (K, kJ/kg o fracción).
- **Error relativo:** `error_absoluto/abs(referencia)`, adimensional y sólo definido para referencia distinta de cero. El test de energías lo calcula para diagnosticar fallos, pero no guarda un máximo relativo agregado.
- **Residuo de identidad física:** cuánto se aparta de cero una igualdad como `wn-(qin-qout)`. Se expresa en **kJ/kg** y se compara con la escala energética del caso, no con una tolerancia térmica.

Se exige:

\[
|x-x_{ref}|\leq \varepsilon_{abs}+\varepsilon_{rel}|x_{ref}|.
\]

| Magnitud | Tolerancia absoluta | Relativa |
|---|---:|---:|
| Temperatura | `1e-9 K` | `2e-12` |
| Energía / residuo | `1e-10 kJ/kg` | `2e-12` |
| Rendimiento | `2e-13` (fracción) | `2e-12` |

Para residuos, la parte relativa multiplica `max(abs(wc),abs(wt),abs(wn),abs(qin),abs(qout))` del caso. Son tolerancias para redondeos en doble precisión y magnitudes moderadas; **no representan errores de medición** ni tolerancias universales para fronteras o extremos.

En el máximo numérico, si `epsilon_rp=resolucion_rp/rp`, la sensibilidad local ideal es aproximadamente `|dT|/T≈a*|drp|/rp`. La comparación usa un margen en K proporcional a `a*sqrt(T1*T3)*epsilon_rp`, más la tolerancia térmica anterior, con factor conservador para comparar simultáneamente T2, T4 y su diferencia. La `resolucion_rp` del buscador es una **escala conservadora informada, no una cota formal demostrada**.

## 5. Comprobaciones realmente ejecutadas

Ejecutadas el **22 de octubre de 2026** en una copia local del commit base, con dependencias del proyecto instaladas **fuera del repositorio**:

```bash
PYTHONPATH=/tmp/brayton_task_1_1_pkgs MPLCONFIGDIR=/tmp/mpl_brayton_task_1_1 python -B -m unittest discover -s tests -p 'test_verificacion_analitica.py' -v
```

**Resultado:** cuatro métodos nuevos correctos, cero fallos, cero errores (`Ran 4 tests ... OK`). Cuatro métodos anteriores directamente relacionados también pasaron por separado:

- `OptimizacionTests.test_limite_reversible_recupera_optimo_ideal`
- `OptimizacionTests.test_busqueda_numerica_no_utiliza_candidato_analitico`
- `ViabilidadTests.test_limites_ideales_y_optimo_distintos`
- `InformesTests.test_referencia_fisica`

El total focalizado es **8 métodos superados**, sin ejecutar de nuevo la suite completa. El último cierre integral histórico anotado en §4.44 del manual fue **178/178** (anterior a las seis pruebas de guías contextuales y a esta tarea); no debe atribuirse a esta ejecución.

Con cinco casos motores, máximos errores absolutos observados en un cálculo adicional:

| Comprobación | Máximo observado |
|---|---:|
| Temperaturas contra referencia | `1.1368683772161603e-13 K` |
| Energías contra referencia | `1.1368683772161603e-13 kJ/kg` |
| Rendimiento contra fórmula | `1.1102230246251565e-16` |
| Residuo de primera ley | `1.1368683772161603e-13 kJ/kg` |

**No se registró un máximo agregado de errores relativos**; no se atribuye uno al experimento.

Caso base (`T1=288.15 K`, `T3=1600 K`, `gamma=1.4`, `cp=1005 J/(kg·K)`, `rp=10`): `T2≈556.330550578 K`, `T4≈828.715948677 K`, `wn≈505.619018249 kJ/kg`, `eta≈0.482052532`. En su óptimo **numérico**: `rp≈20.085256021667`, `sqrt(T1*T3)≈678.999263623 K` y `|T2−T4|≈5.22445e-6 K`. La diferencia térmica del óptimo es mayor que el redondeo de un cálculo directo, como corresponde a la resolución de la búsqueda.

## 6. Limitaciones, próximos pasos y trazabilidad

1. Se han contrastado cinco casos interiores moderados, no todos los valores admisibles. No se han estudiado condicionamiento, límites de representación, puntos degenerados ni fronteras abiertas.
2. No se ha comparado aún ningún algoritmo con SciPy ni se han estudiado mallas o convergencia: serán otras tareas de la nueva fase, sujetas a su propia autorización.
3. No hay datos experimentales ni comparación con una correlación de un motor real: esto es **verificación de software** y de consistencia bajo el modelo de gas ideal con propiedades constantes, **no validación física**.
4. No se modifica `qout` como salida pública ni se añaden funciones de producción para los tests.
5. Esta tarea no crea un milestone **técnico de cierre** de la Fase 1 completa. El documento se ampliará en futuras tareas de esta fase, sin presentar como realizados sus resultados pendientes.

**Archivos de la tarea:** `tests/test_verificacion_analitica.py`, `CODE_WALKTHROUGH.md` (§4.45, estructura y conceptos de pruebas) y este documento. Los archivos de las fases anteriores permanecen en su contexto histórico. **Commit propio de la fase:** pendiente hasta el commit autorizado; no insertar su hash en el propio commit.

### Experimentos de aprendizaje sugeridos (no ejecutados)

- Cambia una sola entrada de `CASOS` en una copia y calcula a mano T2, T4, wc y wt antes de ejecutar el método.
- Introduce deliberadamente una referencia incorrecta y observa cómo `subTest` identifica el caso sin detener los demás.
- Compara la magnitud de un residuo en kJ/kg con la escala del trabajo: no confundas un residuo diminuto con un error de modelo despreciable para cualquier motor real.
