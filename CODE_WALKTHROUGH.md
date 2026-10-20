# Guía educativa de Brayton Simulator

Guía del estado actual, actualizada el 20 de octubre de 2026. El simulador identifica los dominios motores, optimiza trabajo específico y rendimiento térmico y compara ambos criterios con intervalos recalculados por ejecución. Se mantienen los nueve parámetros, Flask local, siete gráficas por informe HTML (las seis anteriores y una de compromiso), metadatos Git y retención de cuatro informes.

**Lectura por fases:** la [guía de aprendizaje de Fase 1](docs/milestones/03_dominio_viable_APRENDIZAJE.md) explica sus novedades respecto al commit de partida. La [guía de aprendizaje de Fase 2](docs/milestones/04_optimizacion_noideal_APRENDIZAJE.md) desarrolla la optimización y los intervalos dinámicos. La [guía de aprendizaje de Fase 3](docs/milestones/05_optimizacion_rendimiento_APRENDIZAJE.md) explica su física, algoritmos, integración y verificación de cierre. Este manual describe todo el código actual; `Evolution of the project` resume los grandes hitos, sin historial acumulativo de iteraciones.

Verificación previa de Fase 2, del 20 de octubre de 2026: **55 pruebas superadas** con `python -B -m unittest discover -s tests -v` (40.481 s en esta ejecución).

Hay seis módulos (`main.py`, `viabilidad.py`, `optimizacion.py`, `optimizacion_rendimiento.py`, `reporting.py`, `web_app.py`) y seis archivos de pruebas. `.venv` contiene dependencias, no código propio. Se distinguen dominio físico, ventana numérica y ventana visual (§14). La suite actual tiene **83 pruebas**: las 55 de Fase 2, 20 unitarias de rendimiento y ocho de integración. Cierre verificado el 20 de octubre de 2026: 83/83 OK en 51.733 s; las comprobaciones previas se identifican como tales en §4.38–4.39. La verificación interna no constituye validación experimental de un motor.

La verificación de esta fase se realiza con informes en carpetas temporales; los seis PNG históricos permanecen intactos. No se crean commits automáticamente. La base verificada de Fase 2 es `f9f9a0495c4231a4d48399fba4bccdcc0f6bcf6f` en `feature/fase-2-optimizacion-noideal`; la implementación de Fase 2 está registrada en el commit `c2f4bff84a173f3b354a5d0f76c2b7bd2ee1fa21` (`Implement non-ideal Brayton work optimization with dynamic intervals`).

La ejecución normal no lee ni sobrescribe los PNG históricos. Los ejemplos que guardan un PNG explícitamente son usos opcionales. Las referencias se dan mediante archivo y nombre de función para no depender de líneas que cambian al editar.

**Alcance actual de Fase 3:** `main` llama al estudio ideal y al optimizador no ideal de rendimiento, compara A/B y añade la curva de compromiso. Flask mantiene nueve campos y recalcula todos los estudios por POST. La revisión final y la guía de aprendizaje están completadas; la fase permanece sin commit en `feature/fase-3-optimizacion-rendimiento`, sobre la base `5629eb076d10ad54852f74a438fda8a970db5f04`.

## 1. Visión general del programa

El programa estudia un ciclo Brayton ideal y otro no ideal simplificado. Usa gas ideal con `cp` y `gamma` constantes, equipos adiabáticos en régimen estacionario y cambios despreciables de energía cinética y potencial. No calcula caudal másico, potencia, combustible, empuje ni mapas de máquinas.

| Estado | Lugar físico |
|---|---|
| 1 | Entrada del compresor |
| 2 | Salida del compresor |
| 3 | Entrada de la turbina |
| 4 | Salida de la turbina |

**INTERPRETACIÓN FÍSICA.** Los procesos ideales son dos isentrópicas y dos isóbaras. El no ideal incorpora eficiencias de compresor y turbina y pérdida de presión del combustor. Se calculan los máximos de trabajo de ambos modelos y, por separado, el máximo de rendimiento no ideal cuando hay pérdidas y dominio motor. El ideal/reversible tiene sólo un supremo no alcanzado de rendimiento; no se crea un punto B ficticio.

**PYTHON.** Los nueve parámetros predeterminados están en `PARAMETROS_PREDETERMINADOS`. `main()` copia esa configuración y admite cambios por argumento. Flask convierte el formulario y llama a esa misma función; las funciones numéricas calculan; Matplotlib dibuja en buffers `BytesIO`; `reporting.py` compone HTML con CSS e imágenes Base64 y publica un archivo completo en `outputs/`. No se genera un TXT intermedio. La terminal muestra tres líneas de éxito; los detalles van al informe.

```text
Imports y definiciones
↓
Terminal: main() con valores predeterminados
O navegador: GET formulario → POST → validación → main(parametros=...)
↓
Fecha, versión Git y copia de configuración
↓
Validación de entradas → dominios actuales → clasificación de referencia → optimización de ambos modelos → barrido
↓
Estados, balance y comprobaciones ideales
↓
Resultados analíticos y numéricos de ambos máximos de trabajo
↓
Ciclo no ideal y límite reversible
↓
Siete gráficas nuevas en memoria; puntos excluidos interrumpen curvas con NaN
↓
Tablas + CSS + imágenes Base64 → HTML en memoria
↓
Escritura temporal → publicación del HTML completo
↓
Conservación de los cuatro informes propios completos más recientes
↓
Resumen breve en terminal
```

El informe contiene cabecera con commit Git y estado local, parámetros, dominio físicamente viable, ciclo ideal, diagramas ideales, optimización ideal/no ideal, estados no ideales en el máximo, ciclo no ideal, comparaciones y comprobaciones. Los resultados siguen siendo **505.619018 kJ/kg y 48.205253 %** en el ideal, y **369.476301 kJ/kg y 36.898732 %** en el no ideal.

| Clave de imagen en memoria | Contenido | Muestreo |
|---|---|---|
| `rendimiento_brayton.png` | Rendimiento exclusivamente ideal | Malla adaptada compartida; sólo interior motor |
| `diagrama_ts_brayton.png` | T-s exclusivamente ideal | Caso de referencia |
| `diagrama_pv_brayton.png` | P-v exclusivamente ideal | Caso de referencia |
| `trabajo_neto_vs_rp.png` | Trabajo y máximo exclusivamente ideales | Malla de dibujo adaptada; máximo contrastado con búsqueda logarítmica y sección áurea |
| `comparacion_ideal_noideal.png` | Rendimiento ideal/no ideal | Malla adaptada compartida ideal/no ideal |
| `trabajo_neto_ideal_noideal.png` | Trabajo ideal/no ideal y criterios A/B | Mismo barrido; NaN y marcadores |
| `compromiso_trabajo_rendimiento.png` | W frente a eta no ideal; rp como parámetro | Mismo barrido, sin unir muestras excluidas; no toda la curva es frontera de Pareto |

Estos nombres son claves: no implican que se escriban siete PNG. Las imágenes van dentro de un único `brayton_fecha_hora_microsegundos_uuid.html`, sin Internet ni archivos externos.

## 2. Estructura completa del repositorio

```text
Brayton_Simulator/
├── AGENTS.md                   instrucciones permanentes
├── CODE_WALKTHROUGH.md         explicación educativa actual
├── main.py                     modelo, gráficas y coordinación
├── viabilidad.py               estados comunes, clasificación, fronteras y barridos
├── optimizacion.py             candidatos, búsqueda interior y contraste de máximos
├── optimizacion_rendimiento.py rendimiento y comparación A/B
├── reporting.py                HTML y conservación de informes
├── web_app.py                  servidor Flask de acceso local
├── Abrir_Brayton_Simulator.cmd acceso por doble clic al formulario local
├── templates/index.html        formulario Jinja/HTML
├── static/style.css            estilos locales del formulario
├── tests/test_viabilidad.py    pruebas de dominio, fronteras, máscaras y regresión HTTP
├── tests/test_optimizacion.py  máximos, intervalos dinámicos y regresión Flask
├── tests/test_optimizacion_rendimiento.py  pruebas unitarias de rendimiento
├── tests/test_integracion_rendimiento.py  gráficas, informe, recálculo Flask y criterios
├── tests/test_reporting.py     pruebas de informes
├── tests/test_web_app.py       pruebas HTTP y compatibilidad
├── README.md                   instalación y uso
├── requirements.txt            numpy, matplotlib y Flask
├── .gitignore
├── docs/milestones/            informes técnicos y guías de aprendizaje por fase
├── outputs/                    informes generados, excluidos de Git
└── *.png                       seis imágenes históricas conservadas
```

`outputs/` se crea al guardar el primer informe si no existe. `.venv` es el entorno local y `.vscode/settings.json` configura el editor; no participan en las ecuaciones. `.gitignore` excluye entorno, cachés, temporales, configuración local y resultados generados. Git conserva versiones de código y documentación cuando se solicitan commits; no se crean copias numeradas del walkthrough.

| Archivo/bloque | Responsabilidad actual |
|---|---|
| `viabilidad.py` | Validación, ecuaciones de estados/energías compartidas, clasificación sin excepciones físicas, bisección y barridos |
| `optimizacion.py` | Máximo analítico y numérico de trabajo; reutiliza estados y dominio de Fase 1 |
| `optimizacion_rendimiento.py` | Supremo ideal, máximo de rendimiento y comparación A/B integrados en main |
| `main.py`: funciones de ciclo | API estricta de cálculo motor, comprobaciones, entropía/P-v y óptimo ideal |
| `main.py`: funciones `guardar_*` y `marcar_dominio` | Siete PNG en memoria; bandas/fronteras, compromiso y NaN en curvas de rp |
| `main.py`: `main` y punto de entrada | Copia de parámetros, coordinación y ejecución directa protegida |
| `reporting.py` | Git, tablas/Base64, dominio, documento completo y publicación/retención |
| `web_app.py` | Formulario, entradas, errores diferenciados, vista/descarga y servidor local |
| `templates/index.html`, `static/style.css` | Plantilla Jinja y presentación adaptable |
| `tests/test_*.py` | Referencia, dominio físico, integración CLI/HTTP, informes y fallos |

El formulario usa un servidor Flask local; los informes siguen siendo documentos estáticos autocontenidos. No se añade una API general, cuentas, base de datos ni despliegue público.

## 3. Explicación bloque por bloque

### A. Imports y preparación

**Qué hace:** importa herramientas y selecciona Agg antes de `pyplot`.

**PYTHON:** `from ... import ...` incorpora nombres concretos; `as np` y `as plt` son aliases. `reporting.py` es un módulo propio, no una dependencia externa.

**INTERPRETACIÓN FÍSICA:** todavía no hay cálculos; las bibliotecas permiten implementar y representar ecuaciones.

### B. Cálculos ideales y balances

**Qué hace:** obtiene eficiencia, temperaturas, trabajos y calor; agrupa el ciclo.

**PYTHON:** `def`, argumentos, `return`, `if`, `all`, generadores, tuplas, diccionarios y desempaquetado `*`/`**`; `raise ValueError` rechaza datos inválidos.

**INTERPRETACIÓN FÍSICA:** relaciones isentrópicas y `cp·ΔT`; consumo de compresor positivo que se resta de turbina; paso J/kg a kJ/kg.

### C. No ideal y comparaciones

**Qué hace:** calcula estados no ideales, comprueba tendencias y límite reversible.

**PYTHON:** bucles que desempaquetan parejas, f-strings, diccionarios anidados y tolerancias.

**INTERPRETACIÓN FÍSICA:** menor eficiencia aumenta consumo o reduce producción; perder presión reduce expansión. `T2s` y `T4s` son referencias diferenciadas.

### D. Optimización y estudios

**Qué hace:** contrasta cada máximo analítico con una búsqueda independiente en su dominio actual y compara los modelos.

**PYTHON:** `np.linspace`, comprensiones, arrays, `argmax`, índices, listas y `append`.

**INTERPRETACIÓN FÍSICA:** cambia `rp` con condiciones extremas fijas. El dominio físico se calcula antes del muestreo. Los puntos excluidos se clasifican conservando motivos simultáneos y no se dibujan como motores. La optimización usa malla logarítmica más sección áurea para ambos modelos (§14), sin SciPy.

### E. Entropía, P-v y gráficas

**Qué hace:** obtiene propiedades ideales y representa siete imágenes; las cuatro curvas frente a rp comparten una malla adaptada y máscaras físicas.

**PYTHON:** `zip`, `enumerate`, arrays, objetos gráficos y `BytesIO`. `ruta` puede ser un buffer. `savefig(..., format="png")` indica el formato sin necesitar extensión.

**INTERPRETACIÓN FÍSICA:** logaritmos T-s y leyes `Pv=RT`, `Pv^gamma=constante`. Las flechas indican sentido, no tiempo.

### F. Coordinación en `main()`

**Qué hace:** copia los parámetros predeterminados, aplica los recibidos, realiza cálculos, registra comprobaciones y solicita HTML.

**PYTHON:** `dict.copy`, `update`, variables locales, lista de mensajes, `try/except` limitado a validar entradas y `try/finally` para liberar buffers y figuras. `is None` selecciona `outputs/`. Devuelve una ruta y muestra tres líneas tras guardar.

**INTERPRETACIÓN FÍSICA:** coordina resultados sin ecuaciones nuevas. Añadir un mensaje después de superar una llamada registra esa comprobación; no constituye otra prueba física.

### G. HTML y Base64

**Qué hace:** forma tablas, secciones y CSS, incorporando las siete imágenes de la ejecución.

**PYTHON:** `str`, `escape`, `join`, f-strings multilínea, `b64encode(...).decode("ascii")`. CSS usa llaves dobles para obtener llaves literales en una f-string.

**INTERPRETACIÓN FÍSICA:** conserva unidades e identificación ideal/no ideal. La presentación no mejora la fidelidad física.

### H. Publicación y conservación

**Qué hace:** escribe un temporal, publica el HTML completo y conserva cuatro informes propios.

**PYTHON:** `Path`, `mkdir`, apertura exclusiva `"x"`, `with`, `try/finally`, `rename`, expresiones regulares, UUID, `lambda`, `[4:]` y `unlink`. Errores posteriores de limpieza se notifican con advertencia.

**INTERPRETACIÓN FÍSICA:** no contiene ecuaciones; mantiene juntos parámetros, números y gráficas de una ejecución.

### I. Servidor y formulario

**Qué hace:** muestra nueve campos agrupados, valida el POST, invoca el simulador y redirige a su informe. Los parámetros enviados se conservan cuando hay errores.

**PYTHON:** objeto `Flask`, decoradores `@app.route`, `request`, `float`, diccionarios de errores y `render_template`. La pérdida se divide por 100 una sola vez antes de llamar al simulador.

**INTERPRETACIÓN FÍSICA:** no hay ecuaciones nuevas. Los rangos de campos, la combinación física, el límite numérico y el error interno se distinguen. El formulario conserva los valores rechazados y muestra todos los motivos físicos y el intervalo permitido cuando existe.

### J. Pruebas

**Qué hace:** comprueba referencias, cinco ejecuciones, errores y colisiones.

**PYTHON:** clases de `unittest`, `self`, `assert*`, `patch`, directorios temporales y parser HTML. Las excepciones propias heredan de tipos estándar; los resultados físicos siguen siendo diccionarios.

**INTERPRETACIÓN FÍSICA:** verifica el cálculo conocido; no compara con datos externos de un motor.

## 4. Explicación función por función

### Cómo leer las firmas

```python
def calcular_rendimiento(gamma, relacion_presiones):
```

**PYTHON.** `def` crea una función con ese nombre. Los identificadores entre paréntesis son parámetros locales; al llamar a la función les llegan argumentos. Los dos puntos y la sangría definen su cuerpo. La firma actual no contiene anotaciones de tipo. Por eso Python no comprueba automáticamente unidades ni tipos esperados antes de entrar.

`return expresion` termina esa llamada y entrega un objeto. Varias expresiones separadas por comas forman una tupla. No tener `return` explícito equivale a devolver `None` al llegar al final. Una función puede producir un efecto, como guardar una imagen, y devolver `None`.

`calcular_rendimientos` utiliza un iterable por defecto y `main` una carpeta y un diccionario de parámetros opcionales con valor `None`. Su tupla `(5, 10, 15, 20, 25)` es inmutable. Las firmas partidas en dos líneas siguen siendo una única definición gracias a los paréntesis abiertos.

En las fichas siguientes, «principal» se refiere a `main()`, la función que coordina la ejecución. «Llama» y «la llaman» indican relaciones **directas entre funciones propias**; las bibliotecas se explican en §6–10. Todos los ejemplos usan nombres disponibles una vez definidas las funciones. Importar `main` carga definiciones sin ejecutar la simulación; el punto de entrada protegido se explica en §12.

### 4.1. `calcular_rendimiento` — main.py

```python
def calcular_rendimiento(gamma, relacion_presiones):
```

- **Problema físico:** rendimiento térmico del Brayton ideal, `η=1−rp**(−(gamma−1)/gamma)`.
- **Entrada y tipos:** dos escalares numéricos reales; `gamma=cp/cv` y `relacion_presiones=p2/p1`, ambos adimensionales. Admite los `int`, `float` y escalares NumPy utilizados por el programa; no está diseñada para arrays completos.
- **Salida:** escalar de rendimiento como fracción adimensional, aproximadamente `0.4820525321` para el caso actual.
- **Validación:** ambos finitos; `gamma>1`, `rp>1`. No recibe `T1` ni `T3`, así que no comprueba disponibilidad de calor o trabajo para temperaturas fijadas.
- **Llama:** ninguna función propia; usa `isfinite`.
- **La llaman:** `calcular_rendimientos`, `calcular_temperaturas`, `calcular_relacion_optima`, `calcular_estados_pv` y `main()`.
- **Ejemplo:** `calcular_rendimiento(1.4, 10)`.
- **Errores:** `ValueError` para dominio inválido; entradas de tipo incompatible pueden provocar `TypeError`; potencias extremas pueden provocar `OverflowError`. No hay captura interna.

### 4.2. `calcular_rendimientos` — main.py

```python
def calcular_rendimientos(gamma, relaciones_presiones=(5, 10, 15, 20, 25)):
```

- **Problema físico:** preparar una tabla de eficiencias ideales para varias relaciones de presiones.
- **Entrada y tipos:** `gamma` escalar adimensional y un iterable de relaciones numéricas adimensionales que se puedan ordenar.
- **Salida:** lista de parejas `(relacion, rendimiento_en_porcentaje)`, ordenada de menor a mayor relación. La segunda componente está en %, no en fracción.
- **Ecuación:** la de §4.1 multiplicada por 100.
- **Validación:** delegada a `calcular_rendimiento` para cada elemento. Si el iterable está vacío, no se llama a esa función y tampoco se valida `gamma`.
- **Llama:** `calcular_rendimiento`.
- **La llaman:** `main()`.
- **Ejemplo:** `calcular_rendimientos(1.4, (10, 5))` devuelve aproximadamente `[(5, 36.8615), (10, 48.2053)]`.
- **Errores:** propaga los del rendimiento; `sorted` puede generar `TypeError` con elementos no comparables. Una colección vacía devuelve `[]`.

### 4.3. `calcular_temperaturas` — main.py

```python
def calcular_temperaturas(T1, T3, gamma, relacion_presiones):
```

- **Problema físico:** obtener las temperaturas de salida isentrópicas a partir de las temperaturas extremas.
- **Entrada y tipos:** cuatro escalares; `T1`, `T3` en K; `gamma`, `rp` adimensionales.
- **Salida:** tupla `(T1, T2, T3, T4)` en K. Devuelve también las temperaturas de entrada recibidas.
- **Ecuaciones:** `factor=rp**((gamma−1)/gamma)`, `T2=T1*factor`, `T4=T3/factor`.
- **Validación:** `gamma` y `rp` por delegación; temperaturas de entrada positivas y finitas, salidas finitas y `T3>T2`. Con estas relaciones ideales y `rp>1`, esa desigualdad corresponde a un ciclo motor con aporte de calor positivo.
- **Llama:** `calcular_rendimiento` para validar y `calcular_estados` para reutilizar las ecuaciones con eficiencias unidad y p1 auxiliar igual a 1 kPa. También exige T3>T1. Puede propagar `ErrorNumerico`.
- **La llaman:** `calcular_ciclo_ideal`, `calcular_trabajo_neto` y `main()`.
- **Ejemplo:** `calcular_temperaturas(288.15, 1600, 1.4, 10)` → aproximadamente `(288.15, 556.330551, 1600, 828.715949)`.
- **Errores:** `ValueError` si no hay calentamiento admisible, o si un dato no es finito/positivo; también puede propagar errores de tipo o de desbordamiento.

### 4.4. `calcular_balance_energetico` — main.py

```python
def calcular_balance_energetico(T1, T2, T3, T4, cp):
```

- **Problema físico:** calcular trabajos, calor aportado y rendimiento con los estados dados, ideales o no ideales.
- **Entrada y tipos:** cinco escalares numéricos; temperaturas en K, `cp` en J/(kg·K).
- **Salida:** diccionario con `trabajo_compresor`, `trabajo_turbina`, `trabajo_neto`, `calor_aportado` en kJ/kg y `rendimiento` adimensional.
- **Ecuaciones:** `wc=cp*(T2−T1)/1000`, `wt=cp*(T3−T4)/1000`, `wn=wt−wc`, `qin=cp*(T3−T2)/1000`, `η=wn/qin`.
- **Validación:** `cp>0` finito; temperaturas positivas y finitas; orden que permite los cuatro procesos; trabajos y calor finitos y estrictamente positivos; `0<η<1`.
- **Llama:** `calcular_energias` para compartir el balance con signo, añadiendo validaciones motoras estrictas y rendimiento.
- **La llaman:** `calcular_ciclo_ideal`, `calcular_trabajo_neto`, `calcular_entropias` y `main()`.
- **Ejemplo:** `calcular_balance_energetico(288.15, 556.3305505777084, 1600, 828.7159486769939, 1005)["trabajo_neto"]` → `505.619018...`.
- **Errores:** `ValueError` si el ciclo no es motor aunque las temperaturas sean positivas; posibles `TypeError` por tipos inadecuados. No comprueba por sí sola presiones, gas ideal ni isentropicidad.

### 4.5. `calcular_ciclo_ideal` — main.py

```python
def calcular_ciclo_ideal(T1, T3, gamma, cp, relacion_presiones, p1):
```

- **Problema físico:** ofrecer una descripción agrupada del ciclo ideal para poder compararlo con el no ideal.
- **Entrada y tipos:** seis escalares: `T1`, `T3` [K], `cp` [J/(kg·K)], `p1` [kPa], `gamma` y `rp` [adimensionales].
- **Salida:** diccionario con `temperaturas` y `presiones` como tuplas, `T2s`, `T4s` [K], las cinco claves del balance y `back_work_ratio=wc/wt` adimensional. No devuelve volúmenes ni entropías, aunque los calcula indirectamente durante validaciones.
- **Ecuaciones:** combina temperaturas ideales, estados P-v y balance; en el ideal `T2s=T2` y `T4s=T4`.
- **Validación:** delegada íntegramente en las funciones de cálculo.
- **Llama:** `calcular_temperaturas`, `calcular_estados_pv`, `calcular_balance_energetico`.
- **La llaman:** `main()` y las pruebas.
- **Ejemplo:** `calcular_ciclo_ideal(288.15, 1600, 1.4, 1005, 10, 100)["back_work_ratio"]` → `0.347706594...`.
- **Errores:** propaga las excepciones de sus tres funciones. El diccionario se devuelve solo si todas terminan correctamente.

### 4.6. `calcular_ciclo_noideal` — main.py

```python
def calcular_ciclo_noideal(T1, T3, gamma, cp, relacion_presiones, p1,
                          eta_c, eta_t, perdida_presion_combustor):
```

- **Propósito físico:** API estricta para un ciclo motor no ideal con las ecuaciones comunes de §14 y §4.32.
- **Entradas:** nueve escalares reales. Temperaturas [K], cp [J/(kg·K)], p1 [kPa]; gamma, rp, eficiencias y pérdida [fracciones adimensionales].
- **Retorno:** diccionario de `evaluar_punto`: temperaturas/presiones, T2s/T4s, cuatro energías [kJ/kg], rendimiento/BWR [fracción], `viable`, `motivos`, `fronteras`, `margenes` y `tolerancias`. Conserva todas las claves anteriores y añade la clasificación.
- **Validación/errores:** parámetros inválidos → `ValueError`; cálculo no representable → `ErrorNumerico`; punto fuera del interior motor → `ErrorModelo` con todos los motivos y límites. Para consultar un punto sin rechazar su inviabilidad, usa `evaluar_punto`.
- **Llama:** `evaluar_punto`; si falla la viabilidad, `calcular_dominios` y `describir_inviabilidad`. La llama `main`, incluido el límite reversible, y las pruebas.
- **PYTHON:** consulta de booleanos y retorno directo de un diccionario, sin recalcular ecuaciones.
- **Ejemplo:** `calcular_ciclo_noideal(288.15, 1600, 1.4, 1005, 10, 100, .85, .90, .05)['rendimiento']` → `0.3689873237`.

### 4.7. `comprobar_comparacion_ciclos` — main.py

```python
def comprobar_comparacion_ciclos(ideal, noideal, eta_c, eta_t, perdida_presion_combustor):
```

- **Problema físico:** verificar que los resultados respeten las tendencias esperadas y recuperen el ideal en el límite reversible.
- **Entrada y tipos:** dos diccionarios con el esquema de ciclo; tres escalares de pérdidas adimensionales coherentes con esos cálculos. Las unidades están dentro de los diccionarios.
- **Salida:** `None` si todo es coherente; no devuelve un booleano.
- **Relaciones comprobadas:** si `eta_c<1`, aumentan `T2` frente a `T2s` y `wc` frente al ideal; si `eta_t<1`, `T4>T4s`; las pérdidas de turbina o presión reducen `wt`; cualquier pérdida reduce el rendimiento. Sin pérdidas, temperaturas y balances deben coincidir dentro de tolerancias.
- **Validación:** compara resultados; no vuelve a validar exhaustivamente los parámetros ni todas las claves. Tampoco realiza una comprobación explícita de igualdad de las presiones en el límite reversible.
- **Llama:** ninguna propia; usa `np.allclose` e `isclose`.
- **La llaman:** `main()` y las pruebas.
- **Ejemplo:** tras obtener `ideal` y `real` con las llamadas anteriores, `comprobar_comparacion_ciclos(ideal, real, 0.85, 0.90, 0.05)` termina sin valor visible.
- **Errores:** `ValueError` si falla una comparación; `KeyError` con claves ausentes, `IndexError` con temperaturas incompletas u otros errores si la estructura no es la esperada. Comparaciones estrictas pueden ser delicadas con pérdidas extremadamente pequeñas.

### 4.8. `guardar_comparaciones_ciclos` — main.py

```python
def guardar_comparaciones_ciclos(T1, T3, gamma, cp, p1, eta_c, eta_t,
                                perdida_presion_combustor, imagenes, barrido=None,
                                optimizaciones=None, estudio_rendimiento=None):
```

- **Propósito físico:** comparar rendimiento [%] y trabajo [kJ/kg] sólo en el interior motor de cada modelo; los ejes rp son logarítmicos.
- **Entradas:** ocho escalares con las unidades de §4.6, `imagenes` diccionario mutable de `BytesIO` y `barrido` opcional con el contrato de §4.32. Si es `None`, se calcula con esos parámetros; quien lo suministre debe mantener esa coherencia.
- **Optimizaciones:** diccionario opcional con entradas `ideal`/`noideal` (§4.35); se representan sus máximos analíticos de trabajo con círculo azul y rombo naranja. Las dos comparaciones añaden un segundo panel con escalas propias si la anchura logarítmica total supera cuatro veces la real o el máximo trabajo ideal supera veinte veces el real. La vista completa conserva fronteras y máximos. Con `estudio_rendimiento` opcional (entradas ideal/noideal, §4.38), ambas comparaciones marcan también la estrella verde B de máximo rendimiento; los marcadores de trabajo se dibujan tanto en eta como en W. Sin máximo interior, un texto indica ausencia de B. No se recalcula física en el dibujador.
- **Retorno/efecto:** `None`; añade buffers `comparacion_ideal_noideal.png` y `trabajo_neto_ideal_noideal.png`. El llamador debe cerrarlos.
- **Llama:** `construir_barrido` si falta y `marcar_dominio`; `main` le entrega el barrido ya clasificado y verificado. No llama al ciclo estricto para cada punto.
- **PYTHON:** arrays multiplicados por 100, bucle de dos magnitudes, NaN que interrumpe cada línea. El muestreo está separado del dibujo.
- **Errores:** propaga errores de entrada, numéricos, estructura o dibujo. No hay captura genérica de `ValueError` para ocultar un fallo. La inviabilidad normal está en las máscaras.
- **Ejemplo:** `imagenes={}`; `guardar_comparaciones_ciclos(288.15,1600,1.4,1005,100,.85,.9,.05,imagenes)`; consulta bytes y cierra los dos buffers.

### 4.9. `calcular_trabajo_neto` — main.py

```python
def calcular_trabajo_neto(T1, T3, gamma, cp, relacion_presiones):
```

- **Problema físico:** obtener solo el trabajo neto ideal para estudiar su dependencia con `rp`.
- **Entrada y tipos:** cinco escalares, temperaturas [K], `cp` [J/(kg·K)], `gamma` y `rp` adimensionales.
- **Salida:** escalar en kJ/kg.
- **Ecuaciones:** las temperaturas isentrópicas seguidas de `wt−wc`.
- **Validación:** delegada a temperaturas y balance.
- **Llama:** `calcular_temperaturas`, `calcular_balance_energetico`.
- **La llaman:** `buscar_optimo_numerico` y las pruebas; el flujo normal reutiliza las energías de `evaluar_punto`.
- **Ejemplo:** `calcular_trabajo_neto(288.15, 1600, 1.4, 1005, 10)` → `505.619018...`.
- **Errores:** propaga las excepciones de las funciones utilizadas. La selección `...["trabajo_neto"]` extrae un valor del diccionario temporal y devuelve ese valor.

### 4.10. `calcular_relacion_optima` — main.py

```python
def calcular_relacion_optima(T1, T3, gamma):
```

- **Problema físico:** relación de presiones que maximiza el trabajo ideal con temperaturas extremas fijas.
- **Entrada y tipos:** escalares `T1`, `T3` [K] y `gamma` adimensional.
- **Salida:** escalar `rp_optima`, adimensional.
- **Ecuación:** `(T3/T1)**(gamma/(2*(gamma−1)))`. La derivación se desarrolla en §15.
- **Validación:** valida `gamma` llamando al rendimiento con una relación auxiliar igual a 2; exige temperaturas finitas con `T3>T1>0`; resultado finito y mayor que 1.
- **Llama:** `calcular_rendimiento`.
- **La llaman:** `buscar_optimo_numerico` y las pruebas; el flujo normal usa `optimizar_trabajo_neto` para ambos modelos.
- **Ejemplo:** `calcular_relacion_optima(288.15, 1600, 1.4)` → `20.0852562921...`.
- **Errores:** `ValueError` para entradas/resultados no admisibles, posibles errores de tipo o desbordamiento. El 2 auxiliar no es una búsqueda ni una hipótesis sobre el óptimo.

### 4.11. `buscar_optimo_numerico` — main.py

```python
def buscar_optimo_numerico(T1, T3, gamma, cp):
```

- **Propósito físico:** API ideal heredada conservada sin cambios. `main()` ya no la llama; la búsqueda normal de ambos modelos se explica en §4.35.
- **Entradas:** cuatro escalares reales; temperaturas [K], gamma [adimensional], cp [J/(kg·K)].
- **Retorno:** `(relaciones, trabajos, indice_maximo)`: dos arrays de 100001 puntos [rp adimensional, kJ/kg] e índice `int`.
- **Método:** calcula el límite ideal `L`; usa `inferior=min(1.01,1+.01*(L−1))` y `superior=min(L−1e−8*(L−1),max(50,1.25*rp_opt))`. La malla es interior y contiene el óptimo. En el ejemplo conserva exactamente [1.01,50] y el resultado `20.0852363`.
- **Validación/errores:** `ErrorNumerico` si no puede representar una malla interior; propaga errores de funciones llamadas, sin silenciarlos. Su retorno permite comparar el máximo discreto con el analítico dentro del paso de esta malla heredada.
- **Llama:** `calcular_dominios`, `calcular_relacion_optima`, `calcular_trabajo_neto`. La llaman las pruebas y usuarios directos de esta API heredada.
- **PYTHON:** `min`/`max` acotan la malla; comprensión, array, `int(np.argmax(...))`. La malla de optimización y la de las figuras tienen propósitos distintos.
- **Ejemplo:** `r,w,i=buscar_optimo_numerico(288.15,400,1.4,1005)` evita el antiguo fallo de evaluar ciclos por encima de su dominio.

### 4.12. `guardar_grafica_trabajo_neto` — main.py

```python
def guardar_grafica_trabajo_neto(relaciones, trabajos, rp_optima, trabajo_maximo, ruta, dominio=None):
```

- **Problema físico:** representar el trabajo ideal y ubicar el máximo analítico suministrado.
- **Entrada y tipos:** dos secuencias numéricas de igual longitud, `rp_optima` adimensional, `trabajo_maximo` [kJ/kg] y destino `Path`, cadena o buffer binario aceptado por Matplotlib; `main()` usa `BytesIO`.
- **Salida:** `None`; guarda el PNG en el destino recibido: buffer en el flujo normal, archivo si se entrega una ruta.
- **Ecuaciones:** no calcula el ciclo ni verifica el máximo; representa datos ya obtenidos. La etiqueta de verificación se justifica por las comprobaciones previas de principal.
- **Validación:** recibe datos ya clasificados; `main` entrega la malla de dibujo con NaN y el dominio ideal opcional. Si el máximo queda fuera de la vista, se indica con texto sin ampliar el eje.
- **Llama:** `marcar_dominio` si `dominio` no es `None`. Este argumento es un diccionario de fronteras sin unidades, no una nueva ecuación.
- **La llaman:** `main()`.
- **Ejemplo con efecto en disco:** después de §4.11, `guardar_grafica_trabajo_neto(relaciones, trabajos, 20.085256292117077, 532.8022301186, Path("trabajo_ejemplo.png"))`.
- **Errores:** `ValueError` de Matplotlib si los tamaños son incompatibles, errores de tipo o de escritura. La función cierra la figura tras guardarla si la operación termina bien.

### 4.13. `calcular_entropias` — main.py

```python
def calcular_entropias(T1, T2, T3, T4, cp):
```

- **Problema físico:** entropías relativas del ciclo ideal y coherencia de sus saltos isóbaros.
- **Entrada y tipos:** cinco escalares, temperaturas [K] y `cp` [J/(kg·K)].
- **Salida:** tupla `(s1,s2,s3,s4)` en kJ/(kg·K), con `s1=s2=0`.
- **Ecuaciones:** `Δs23=(cp/1000)*ln(T3/T2)` y `Δs14=(cp/1000)*ln(T4/T1)`; exige que coincidan y asigna `s3=s4=Δs23`.
- **Validación:** primero valida el balance motor y después la igualdad de incrementos con tolerancias. Esta comprobación de temperaturas no sustituye una validación completa de presiones e isentropicidad: la función no recibe presiones.
- **Llama:** `calcular_balance_energetico`.
- **La llaman:** `calcular_estados_pv`, `guardar_diagrama_ts` y `main()`.
- **Ejemplo:** `calcular_entropias(*calcular_temperaturas(288.15, 1600, 1.4, 10), 1005)` → aproximadamente `(0.0, 0.0, 1.061678257, 1.061678257)`.
- **Errores:** `ValueError` por balance inválido o incrementos distintos; errores de tipo. No es una función general para entropía del ciclo no ideal. Su mensaje sobre isentropicidad debe leerse dentro del modelo ideal que presupone.

### 4.14. `guardar_diagrama_ts` — main.py

```python
def guardar_diagrama_ts(temperaturas, entropias, cp, ruta):
```

- **Problema físico:** dibujar el recorrido ideal T-s con procesos, estados y flechas.
- **Entrada y tipos:** secuencia de cuatro temperaturas [K], secuencia de cuatro entropías [kJ/(kg·K)], `cp` escalar [J/(kg·K)] y destino `Path`, cadena o buffer binario; `main()` usa `BytesIO`.
- **Salida:** `None`; PNG en el destino recibido, normalmente un buffer en memoria.
- **Ecuaciones:** en las isóbaras `s(T)=s_inicio+(cp/1000)*ln(T/T_inicio)` con 100 muestras; las isentrópicas son segmentos a entropía constante.
- **Validación:** calcula las entropías esperadas y compara las cuatro suministradas, incluida la referencia `s1=0`.
- **Llama:** `calcular_entropias`.
- **La llaman:** `main()`.
- **Ejemplo con efecto en disco:** `guardar_diagrama_ts((288.15, 556.3305505777084, 1600, 828.7159486769939), (0, 0, 1.0616782565800615, 1.0616782565800615), 1005, Path("ts_ejemplo.png"))`.
- **Errores:** `ValueError` si temperaturas no tienen cuatro elementos al desempaquetar, si falla el cálculo o las entropías no coinciden; posibles errores de tipo y escritura. No adapta el diagrama a equipos irreversibles.

### 4.15. `comprobar_estados_pv` — main.py

```python
def comprobar_estados_pv(temperaturas, presiones, volumenes, R, gamma):
```

- **Problema físico:** comprobar consistencia de cuatro estados del Brayton ideal.
- **Entrada y tipos:** tres secuencias de longitud cuatro; temperaturas [K], presiones [kPa], volúmenes específicos [m³/kg]; `R` [J/(kg·K)] y `gamma` adimensional, ambos escalares.
- **Salida:** `None` si pasa todas las comprobaciones.
- **Ecuaciones:** `p*1000*v=R*T`; igualdad de las dos presiones altas y las dos bajas; constancia de `p*v**gamma` en 1→2 y 3→4; orden de volúmenes del ciclo motor.
- **Validación:** longitudes, finitud, positividad, `gamma>1` y las relaciones anteriores. No recibe `cp`, por tanto no comprueba por sí sola `R=cp*(1−1/gamma)`.
- **Llama:** ninguna propia.
- **La llaman:** `calcular_estados_pv`, `guardar_diagrama_pv`.
- **Ejemplo:** con `temperaturas` ideales y `R, presiones, volumenes` de §4.16, `comprobar_estados_pv(temperaturas, presiones, volumenes, R, 1.4)`.
- **Errores:** `ValueError` con la condición que no se cumple; `TypeError` si los argumentos no tienen la estructura o tipos esperados. Las tolerancias evitan exigir igualdad binaria exacta.

### 4.16. `calcular_estados_pv` — main.py

```python
def calcular_estados_pv(temperaturas, cp, gamma, relacion_presiones, p1):
```

- **Problema físico:** obtener presiones y volúmenes específicos ideales coherentes con las temperaturas.
- **Entrada y tipos:** secuencia de cuatro temperaturas [K] y escalares `cp` [J/(kg·K)], `gamma`, `rp` [adimensionales], `p1` [kPa].
- **Salida:** tupla `(R, presiones, volumenes)`: escalar [J/(kg·K)], tupla de cuatro valores [kPa] y tupla de cuatro valores [m³/kg].
- **Ecuaciones:** `R=cp*(1−1/gamma)`; presiones `(p1,rp*p1,rp*p1,p1)`; `v=R*T/(p*1000)`.
- **Validación:** rendimiento valida `gamma` y `rp`; entropías valida temperaturas y balance; valida `p1`; finalmente verifica todos los estados P-v.
- **Llama:** `calcular_rendimiento`, `calcular_entropias`, `comprobar_estados_pv`.
- **La llaman:** `calcular_ciclo_ideal` y `main()`.
- **Ejemplo:** `temperaturas = calcular_temperaturas(288.15, 1600, 1.4, 10)`; `R, presiones, volumenes = calcular_estados_pv(temperaturas, 1005, 1.4, 10, 100)`.
- **Resultado del ejemplo:** `R≈287.142857`; presiones `(100,1000,1000,100)`; volúmenes aproximadamente `(0.827402143,0.159746344,0.459428571,2.379598653)`.
- **Errores:** propaga validaciones; `ValueError` si las temperaturas no corresponden a las relaciones isentrópicas y presiones propuestas; posibles errores de estructura, tipo o desbordamiento.

### 4.17. `guardar_diagrama_pv` — main.py

```python
def guardar_diagrama_pv(temperaturas, presiones, volumenes, R, gamma, ruta):
```

- **Problema físico:** visualizar el ciclo ideal en P-v con procesos termodinámicos curvos.
- **Entrada y tipos:** tres secuencias de cuatro estados con las unidades de §4.15, `R` y `gamma` escalares, y destino `Path`, cadena o buffer binario; `main()` usa `BytesIO`.
- **Salida:** `None`; PNG en el destino recibido, normalmente un buffer en memoria.
- **Ecuaciones:** `p(v)=p_inicio*(v_inicio/v)**gamma` en las isentrópicas y `p` constante en las isóbaras; 200 muestras por proceso.
- **Validación:** `comprobar_estados_pv` antes de representar. No vuelve a calcular los estados.
- **Llama:** `comprobar_estados_pv`.
- **La llaman:** `main()`.
- **Ejemplo con efecto en disco:** con los resultados de §4.16, `guardar_diagrama_pv(temperaturas, presiones, volumenes, R, 1.4, Path("pv_ejemplo.png"))`.
- **Errores:** propaga fallos físicos y de estructura; puede fallar la escritura o la representación. La temperatura se utiliza para validar, aunque los ejes dibujados sean `v` y `p`.

### 4.18. `guardar_grafica_rendimiento` — main.py

```python
def guardar_grafica_rendimiento(gamma, ruta, barrido=None):
```

- **Propósito físico:** representar únicamente el rendimiento ideal motor, con bandas y fronteras; no prolonga la fórmula ideal fuera del dominio de temperaturas.
- **Entradas:** gamma escalar adimensional, destino `Path`/cadena/buffer binario y barrido opcional (§4.32). `main` entrega el barrido de sus nueve parámetros. Con dos argumentos mantiene compatibilidad: usa T1/T3/cp/p1 predeterminados y el gamma recibido.
- **Salida:** `None`, PNG de 1350 × 900 píxeles, 9 × 6 pulgadas a 150 dpi.
- **Llama:** `construir_barrido` si no se recibe; `marcar_dominio`. La llaman `main` y las pruebas.
- **Validación/errores:** los del barrido o de escritura/dibujo; no convierte inviabilidad esperada en excepción.
- **PYTHON:** objetos `Figure`/`Axes`, producto del array de fracciones por 100 y NaN para interrumpir la curva.
- **Ejemplo:** `buffer=BytesIO()`; `guardar_grafica_rendimiento(1.4,buffer)`; `png=buffer.getvalue()`; `buffer.close()`.

### 4.19. `main` — main.py

```python
def main(carpeta_salida=None, parametros=None):
```

- **Propósito:** coordina la ejecución completa; los nueve valores predeterminados están en la constante del módulo y pueden sustituirse desde el formulario.
- **Argumentos:** `carpeta_salida` es `Path`, cadena o `None`; `None` usa `outputs/` junto al script. `parametros` es un diccionario opcional con cualquiera de las nueve claves conocidas y unidades de §5. Las claves omitidas conservan sus valores predeterminados; la pérdida se recibe como fracción, no porcentaje. No se modifica el diccionario recibido ni la configuración predeterminada.
- **Salida:** `Path` al HTML completo; efectos: guardar, conservar cuatro y mostrar tres líneas.
- **Llama directamente:** `validar_parametros`, `calcular_dominios`, `evaluar_punto`, `construir_barrido`, `describir_inviabilidad`, rendimiento, temperaturas, balance, entropías, estados P-v, `optimizar_trabajo_neto` dos veces, `estudiar_rendimiento_ideal`, `optimizar_rendimiento`, `comparar_criterios`, ambos ciclos, comprobación comparativa, seis funciones gráficas `guardar_*`, tabla de rendimientos, `crear_informe_html`, `guardar_informe_html` y `obtener_version_git`.
- **La llaman:** punto de entrada protegido, ruta `index()` de Flask y pruebas de terminal/web.
- **Validación física:** las existentes de los modelos, igualdad de rendimientos y concordancia de óptimos. Registra mensajes después de superar comprobaciones.
- **Errores:** claves desconocidas producen `ValueError`. El `ValueError` se captura únicamente alrededor de la validación explícita de entradas. El caso de referencia físicamente inviable genera `ErrorModelo` con motivos y límites antes de crear buffers o publicar. `ErrorNumerico` distingue cálculos no representables. Errores inesperados de cálculo/dibujo/HTML/publicación se propagan sin reclasificarse como físicos. La retención no empieza antes de publicar; sus fallos posteriores se advierten.
- **PYTHON:** copia y actualización de diccionarios, `.items()`, `any`, `try/except`, `raise ... from error`, `try/finally`, `is None` y retorno.
- **Ejemplo con escritura:** `ruta = main()` o `main(Path("outputs_prueba"), parametros={"T3": 1700})`; la carpeta alternativa tiene su propio historial. El primer argumento posicional sigue siendo la carpeta, conservando compatibilidad con las llamadas anteriores.

### 4.20. `tabla_html` — reporting.py

```python
def tabla_html(encabezados, filas):
```

- **Propósito/interpretación:** presentar valores ya calculados, sin ecuaciones nuevas.
- **Argumentos:** iterable de encabezados e iterable de filas con valores ya formateados; unidades en etiquetas/celdas, sin conversiones aquí.
- **Retorno:** `str` con tabla y contenedor de desplazamiento horizontal.
- **Llama:** ninguna función propia; usa `str`, `escape` y `join`. La llaman `crear_informe_html`, `seccion_optimizacion_html`, `seccion_rendimiento_html` y la prueba de escape.
- **Validación/errores:** escapa texto HTML; no valida longitudes de filas ni física. Entradas no iterables pueden producir `TypeError`.
- **PYTHON:** generadores y concatenación.
- **Ejemplo:** `tabla_html(("T [K]",), [("288.15",)])`.

### 4.21. `imagen_html` — reporting.py

```python
def imagen_html(imagen, titulo):
```

- **Propósito:** convertir PNG de esta ejecución en figura HTML autocontenida.
- **Argumentos:** `imagen`, bytes PNG sin unidad; `titulo`, cadena con significado físico y unidades cuando corresponda.
- **Retorno:** `str` con `figure`, `img`, `figcaption` y URL `data:image/png;base64,...`.
- **Validación/errores:** comprueba firma binaria PNG; `ValueError` si no coincide. No decodifica exhaustivamente los píxeles; las pruebas sí decodifican las siete imágenes actuales.
- **Llama:** ninguna propia; usa `b64encode`, `.decode` y `escape`. La llaman `crear_informe_html` y la prueba de imagen inválida.
- **PYTHON:** literal de bytes, `.startswith`, conversión binario→texto. No cambia física ni comprime adicionalmente el PNG.
- **Ejemplo:** `imagen_html(buffer.getvalue(), "Diagrama T-s ideal")` con una gráfica recién dibujada.

### 4.22. `crear_informe_html` — reporting.py

```python
def crear_informe_html(parametros, ideal, noideal, detalles_ideal, optimo,
                       rendimientos, comprobaciones, imagenes, fecha, version, barrido=None,
                       optimizaciones=None, *, estudio_rendimiento=None, comparacion_criterios=None):
```

- **Propósito:** reunir secciones y siete imágenes en un HTML; no escribe ni recalcula el ciclo.
- **Argumentos:** cinco diccionarios físicos detallados en §5; `rendimientos`, lista de parejas `(rp, porcentaje_o_None)`; `comprobaciones`, lista de textos; `imagenes`, diccionario de siete claves actuales con valores `bytes` (seis en el formato previo sin estudios de rendimiento); `fecha`, `datetime` con zona local; `version`, diccionario con `commit` (hash o `None`) y `modificado` (`True`, `False` o `None`).
- **Barrido opcional:** diccionario de §4.32 al final de la firma, manteniendo los argumentos anteriores compatibles. `main` siempre lo entrega: añade sección de condiciones, límites, estado viable de referencia y recuentos de motivos simultáneos. Sin barrido, una llamada antigua conserva el formato básico. `None` en la tabla ideal se presenta como fuera del dominio motor.
- **Unidades:** las de §5; solo convierte fracciones a porcentaje al presentar. No modifica los diccionarios recibidos.
- **Retorno:** `str` HTML con CSS interno, UTF-8 declarado y marcas inicial/final.
- **Optimizaciones opcionales:** diccionario de los dos estudios (§4.35). `main` lo entrega siempre; `seccion_optimizacion_html` presenta resultados y ventanas sin recalcularlos. Las llamadas anteriores sin este argumento siguen admitidas.
- **Llama:** `tabla_html`, `imagen_html`, `seccion_optimizacion_html`, `seccion_rendimiento_html`. La llama `main()`; la prueba de integración intercepta esta llamada para contrastar bytes.
- **Validación/errores:** exige las seis claves originales y, cuando recibe estudios de rendimiento, la séptima de compromiso; valida las firmas PNG por delegación. Las llamadas antiguas sin esos estudios siguen admitiendo seis imágenes. Puede dar `ValueError`, `KeyError` o errores de tipo para datos incompletos. Las comprobaciones mostradas son las registradas por `main`, no verificaciones inventadas aquí.
- **PYTHON:** f-string multilínea, llaves dobles de CSS, `join`, generadores y `strftime`.
- **Ejemplo de contrato:** `crear_informe_html(parametros, ciclo_ideal, ciclo_noideal, detalles_ideal, optimo, calcular_rendimientos(gamma), comprobaciones, pngs, fecha, version)`, con los datos reunidos por `main`; `pngs` representa bytes, no rutas a archivos históricos.

### 4.23. `guardar_informe_html` — reporting.py

```python
def guardar_informe_html(contenido, carpeta, fecha):
```

- **Propósito:** publicar un informe completo y conservar cuatro; sin ecuaciones físicas.
- **Argumentos:** `contenido`, `str` con marcas completas; `carpeta`, `Path` o cadena; `fecha`, `datetime`. Sin unidades termodinámicas.
- **Retorno:** `Path` del HTML publicado; puede ser relativo si la carpeta recibida lo era. `main` imprime su forma absoluta.
- **Llama:** ninguna función propia. La llaman `main` y pruebas de publicación, colisión y documento incompleto.
- **Validación:** marcas, apertura exclusiva del temporal, destino ausente y filtro de informes propios. En Windows `rename` también rechaza destino existente.
- **Errores:** escritura/cierre/publicación fallidos se propagan; `finally` intenta retirar el temporal propio. Fallos de limpieza posteriores producen advertencia: ya existe informe válido, pero pueden quedar más de cuatro.
- **PYTHON:** `with`, modo `"x"`, `try/finally`, `except ... as error`, regex, UUID, `lambda`, ordenación y `[4:]`.
- **Ejemplo:** `guardar_informe_html(contenido, Path("outputs"), fecha)` tras construir el HTML con la función anterior.

### 4.24. `obtener_version_git` — reporting.py

```python
def obtener_version_git(carpeta):
```

- **Propósito:** identificar la base Git y avisar de cambios locales al inicio de ejecución; no calcula física.
- **Argumento:** `carpeta`, ruta `Path` o cadena dentro del repositorio, sin unidades.
- **Retorno:** diccionario `{"commit": hash_completo, "modificado": booleano}`; ambos valores son `None` si Git falta, no hay commit o falla la consulta.
- **Llama:** ninguna función propia; ejecuta dos consultas con `subprocess.run`. La llaman `main()` y las pruebas de Git limpio, modificado y no disponible.
- **Operaciones:** `git -C carpeta rev-parse --verify HEAD` obtiene el commit; `git -C carpeta status --porcelain --untracked-files=normal` detecta cambios preparados, sin preparar y archivos nuevos no ignorados. No modifica Git ni crea commits.
- **Validaciones/errores:** cada comando debe terminar correctamente en cinco segundos. `OSError` y `subprocess.SubprocessError` se capturan y se devuelve estado desconocido para no impedir el informe; desconocido nunca se etiqueta como limpio.
- **PYTHON:** lista de argumentos, `.stdout`, `.strip()`, `bool`, excepciones y tres estados lógicos (§9). `True` significa que hay cambios, `False` que no se detectaron, `None` que no se sabe.
- **Ejemplo:** `obtener_version_git(Path(__file__).resolve().parent)`. El resultado refleja el momento de consulta; no incluye un archivo con el código modificado ni permite reconstruirlo solo a partir del hash.

### 4.25. Métodos de las pruebas

Son métodos de clases; `self` referencia la instancia, no un estado físico. Todos devuelven `None`, sin unidades ni ecuaciones nuevas. Las aserciones fallidas generan `AssertionError`; `unittest` registra también errores inesperados. Los errores esperados se verifican con `assertRaises`.

| Firma | Propósito y llamadas | Quién la llama |
|---|---|---|
| `InformeParser.__init__(self)` | Inicializa parser y listas mediante `super().__init__()` | Prueba de integración al crear parser |
| `InformeParser.handle_starttag(self, tag, attrs)` | Recibe etiqueta `str` y parejas de atributos; decodifica Base64 o registra referencias externas | `HTMLParser.feed` al encontrar etiquetas |
| `InformesTests.test_referencia_fisica(self)` | Llama a ambos ciclos y óptimo; compara resultados conocidos | `unittest` |
| `InformesTests.test_cinco_ejecuciones_completas_html_e_imagenes(self)` | Cinco llamadas a `main`; analiza tablas, imágenes y archivos conservados | `unittest` |
| `InformesTests.test_fallo_de_calculo_no_toca_informes_anteriores(self)` | Llama a `main` con un cálculo sustituido para fallar | `unittest` |
| `InformesTests.test_fallo_de_publicacion_no_limpia_ni_deja_html_parcial(self)` | Sustituye `Path.rename` y llama al guardado | `unittest` |
| `InformesTests.test_nombre_repetido_no_sobrescribe(self)` | Fija UUID/fecha, llama al guardado y exige conservar destino | `unittest` |
| `InformesTests.test_html_escapa_texto_y_rechaza_imagen_invalida(self)` | Llama a tabla, imagen y guardado con datos inválidos | `unittest` |
| `InformesTests.test_temporal_ajeno_con_nombre_repetido_se_conserva(self)` | Simula colisión del temporal al guardar y exige conservarlo | `unittest` |
| `InformesTests.test_version_git_limpia_y_con_cambios(self)` | Simula salidas de `subprocess.run`; comprueba cambios preparados, sin preparar y sin seguimiento | `unittest` |
| `InformesTests.test_git_no_disponible_no_se_presenta_como_limpio(self)` | Simula Git ausente, fallo de comando y timeout; exige estado desconocido | `unittest` |
| `InformesTests.test_cabecera_distingue_git_limpio_modificado_y_desconocido(self)` | Reutiliza datos de `main`; genera HTML con tres estados y comprueba los avisos | `unittest` |
| `InformesTests.test_grafica_en_memoria_refleja_gamma(self)` | Dibuja con dos valores de gamma y compara bytes | `unittest` |

**Ejemplo:** `python -B -m unittest discover -s tests -v` desde la raíz. No se invocan estos métodos a mano. La lectura de atributos con `HTMLParser` y la inyección de fallos con `patch` se explican en §10–11.

### 4.26. `valores_formulario` — web_app.py

```python
def valores_formulario():
```

- **Propósito:** preparar valores para GET sin modificar la constante del simulador; no calcula estados.
- **Argumentos:** ninguno. **Retorno:** diccionario con las nueve claves; unidades de §5 salvo pérdida expresada en %.
- **Llama:** ninguna función propia; usa `.copy()` y multiplica la pérdida por 100. La llaman `index`, `error_interno` y las pruebas de formulario/conversión.
- **Validación/errores:** no valida: parte de la configuración conocida. Una clave ausente en esa configuración sería un error de programación, no una entrada inviable.
- **PYTHON:** copia superficial suficiente para valores numéricos; `*=` actualiza solo la copia.
- **Ejemplo:** `valores_formulario()["perdida_presion_combustor"]` devuelve `5.0`.

### 4.27. `leer_parametros` — web_app.py

```python
def leer_parametros(formulario):
```

- **Propósito:** convertir nueve cadenas a números y verificar campos/rangos, sin duplicar ecuaciones ni estudiar dominios.
- **Entrada:** objeto con `.get(nombre, defecto)`, como `request.form` de Flask o un diccionario de cadenas. La pérdida está en %; temperaturas en K, presión en kPa y cp en J/(kg·K).
- **Salida:** tupla `(parametros, errores)`. El primer diccionario contiene valores aceptados y pérdida como fracción; el segundo contiene mensajes por campo. Si hay errores, el primer diccionario puede estar incompleto y **no debe ejecutarse** el simulador.
- **Validación:** campo presente/no vacío, `float`, finitud y rangos individuales. Cada error deja avanzar el bucle para mostrar todos los campos inválidos. La factibilidad del conjunto se comprueba después con el simulador.
- **Llama:** ninguna función propia; usa `isfinite`. La llaman `index` y las pruebas de conversión y simulación web.
- **Errores:** captura solo el `ValueError` esperado de `float`; errores de programación inesperados no se convierten silenciosamente en un resultado correcto.
- **PYTHON:** `.get`, `.strip`, `continue`, `try/except`, comparaciones encadenadas y expresión condicional `valor / 100 if ... else valor`.
- **Ejemplo:** `leer_parametros({nombre: str(valor) for nombre, valor in valores_formulario().items()})` devuelve parámetros predeterminados con pérdida `0.05` y errores `{}`.

### 4.28. `index` — web_app.py

```python
def index():
```

- **Propósito:** atender GET/POST de `/`. No recibe argumentos posicionales; obtiene método y formulario del contexto HTTP.
- **Retorno:** para GET, pareja `(HTML, 200)`; ante entradas inválidas/modelo rechazado, `(HTML, 400)`; con éxito, respuesta de redirección HTTP 303 al informe recién creado.
- **Llama:** `valores_formulario`, `leer_parametros`, `main`. Flask la llama por el decorador de ruta; las pruebas lo hacen mediante `test_client`.
- **Unidades:** respeta el contrato de `leer_parametros`; no calcula ecuaciones.
- **Validación/errores:** no invoca `main` si hay errores de campos. Captura `ErrorModelo` y `ErrorNumerico` con mensajes distintos durante la ejecución; conserva `request.form.to_dict()` para volver a mostrar valores. Otros errores llegan al tratamiento de HTTP 500 de Flask.
- **PYTHON:** decorador `@app.route("/", methods=["GET", "POST"])`, condicionales y `try/except/else`. Ese `else` se ejecuta solo si la llamada no lanzó una excepción.
- **Ejemplo:** `client.get("/")` muestra el formulario; `client.post("/", data=datos)` simula un envío en una prueba. Fuera de una petición no se llama manualmente a `index()`.

### 4.29. `ver_informe` — web_app.py

```python
def ver_informe(nombre):
```

- **Propósito:** devolver un informe propio completo o su descarga, sin ofrecer un explorador de archivos locales.
- **Entrada:** `nombre`, cadena de nombre base incluida en la URL, sin unidad física.
- **Salida:** `Response` HTML; con `?descargar=1`, añade cabecera de descarga y devuelve el contenido guardado intacto. La vista normal añade enlaces al formulario y a la descarga solo a su copia en memoria.
- **Llama:** ninguna función propia; Flask la llama para `/informes/<nombre>`.
- **Validación:** patrón completo de informes, archivo regular no simbólico, ruta resuelta dentro de `OUTPUTS_DIR` y marcas inicial/final. Nombre/ruta/archivo inexistente, no UTF-8 o informe incompleto devuelven 404 mediante `abort`.
- **Errores:** fallos inesperados de lectura o código se registran como 500. Un informe antiguo eliminado por retención devuelve 404; no se inventa una copia de su contenido.
- **PYTHON:** `.resolve`, `.read_text`, `.replace(..., 1)`, argumentos de URL, f-string, `Response` y cabeceras HTTP.
- **Ejemplo:** `client.get("/informes/" + nombre)` y `client.get("/informes/" + nombre + "?descargar=1")`, usando un nombre real generado.
- **INTERPRETACIÓN FÍSICA:** no recalcula; sirve exactamente la ejecución guardada. El contenido del dominio ya está calculado al servir el archivo.

### 4.30. `error_interno` — web_app.py

```python
def error_interno(error):
```

- **Propósito:** presentar un fallo inesperado sin exponer trazas al navegador ni llamarlo inviabilidad física.
- **Argumento:** excepción HTTP 500 que entrega Flask; sin unidad física. **Retorno:** formulario HTML y estado 500.
- **Llama:** `valores_formulario` cuando no es un POST; Flask llama a este manejador, registrado con `@app.errorhandler(500)`.
- **Comportamiento:** Flask ya registra el traceback en terminal. La respuesta dice que es un error interno y conserva las entradas POST si existen. No se genera un informe nuevo desde este manejador.
- **PYTHON:** decorador de errores, renderizado de plantilla y expresión condicional. No se captura todo como `ErrorModelo`.
- **Ejemplo:** la prueba sustituye una función de dibujo por una que falla; `client.post` recibe 500 mientras el registro conserva el detalle técnico.

### 4.31. `iniciar_servidor` — web_app.py

```python
def iniciar_servidor():
```

- **Propósito:** arrancar el servidor local; no calcula física. Sin argumentos ni unidades.
- **Retorno:** `None` al detenerse; mientras está activo la llamada permanece atendiendo peticiones.
- **Llama:** ninguna función propia; invoca `app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=False)`.
- **La llaman:** punto de entrada de `web_app.py` y prueba que inspecciona los argumentos sin abrir un socket.
- **Validación/errores:** si el puerto está ocupado o faltan permisos, el servidor puede no arrancar y lo indica en terminal. No cambia a una interfaz pública automáticamente.
- **PYTHON:** argumentos nombrados y punto de entrada protegido. No se inicia al importar `web_app`.
- **Ejemplo:** `python web_app.py`, y Ctrl+C para detenerlo. Se usa el servidor de desarrollo Flask solo para esta herramienta local, sin depurador interactivo ni recarga automática.

### Clase `ErrorModelo` — main.py

```python
class ErrorModelo(ValueError):
    """El caso de referencia no pertenece al dominio motor."""
```

Hereda de `ValueError` y no define métodos. `main` la utiliza para entradas rechazadas o caso no motor, y `calcular_ciclo_noideal` conserva así su API estricta. No se lanza por cada punto inviable del barrido. Flask la muestra con HTTP 400; los errores inesperados se registran con HTTP 500. Para distinguir la inviabilidad esperada de un fallo de representación numérica se usa `ErrorNumerico(ArithmeticError)` (§4.32).

### Métodos de `WebTests` — tests/test_web_app.py

Todos reciben `self`, devuelven `None` y no añaden ecuaciones ni unidades. El ejecutor `unittest` los llama; las aserciones pueden fallar con `AssertionError`. `setUp` se ejecuta antes de cada prueba y registra limpiezas con `addCleanup`.

| Firma | Propósito y llamadas principales |
|---|---|
| `setUp(self)` | Crea carpeta temporal, sustituye `OUTPUTS_DIR` con `patch.dict`, crea `test_client` y datos de formulario |
| `test_formulario_predeterminados_y_restablecer(self)` | GET del formulario y CSS; comprueba nueve campos y ausencia de simulación |
| `test_validacion_de_todos_los_campos_sin_informes(self)` | POST con vacíos, no números, no finitos y límites inválidos; exige que `main` no se llame |
| `test_conversion_porcentaje_y_limites_admitidos(self)` | Llama a `leer_parametros` con pérdidas cero y 5 %, y eficiencias unidad |
| `test_referencia_y_otro_caso_con_seis_imagenes_actuales(self)` | Envía dos casos reales; compara resultados y bytes de las siete imágenes, vista y descarga |
| `test_cinco_ejecuciones_mezcladas_terminal_web(self)` | Alterna `main` y POST cinco veces; conserva cuatro y devuelve 404 para el eliminado |
| `test_casos_no_admisibles_conservan_datos_e_historial(self)` | Envía T3=400 y 500 K, con caso de referencia no motor; comprueba errores y archivos intactos |
| `test_error_inesperado_se_registra_y_no_se_presenta_como_fisico(self)` | Inyecta fallo de dibujo; exige 500, registro de traza y ausencia de detalle privado en respuesta |
| `test_no_se_exponen_archivos_ajenos_o_rutas_locales(self)` | GET de rutas y archivos no autorizados; espera 404 |
| `test_servidor_se_configura_solo_para_loopback_sin_debug(self)` | Sustituye `app.run`, llama a `iniciar_servidor` y verifica sus opciones |
| `test_importar_modulos_no_ejecuta_ni_escucha(self)` | Importa módulos en un proceso Python aparte y prohíbe generar informes o arrancar servidor |
| `test_main_directo_con_valores_predeterminados(self)` | Ejecuta el punto de entrada mediante `runpy`, sustituyendo solo destino de prueba; comprueba resumen y referencia |

El pequeño helper `guardar_en_prueba(contenido, carpeta, fecha)` del proceso de esa última prueba conserva la firma del guardado, devuelve su ruta y llama a `reporting.guardar_informe_html` con carpeta temporal. No participa en el programa normal ni modifica cálculos.

**Ejemplo de todas las pruebas:** `python -B -m unittest discover -s tests -v`. Las comprobaciones web no necesitan navegador ni puerto abierto, porque `test_client` despacha las peticiones dentro de Flask.

### 4.32. Funciones del módulo `viabilidad.py`

**Contrato común.** Los argumentos físicos son escalares reales (`int`, `float` o escalares NumPy); T1/T3 en K, cp en J/(kg·K), p1 en kPa. `gamma`, `rp`, `eta_c`, `eta_t`, `delta` y tolerancias relativas no tienen unidades. No se aceptan arrays como temperaturas de entrada de estas funciones escalares. Las tuplas de estados siempre siguen 1,2,3,4. Los errores de tipos o estructuras mal usados se propagan; la API no los oculta como inviabilidad física.

#### `validar_parametros(T1, T3, gamma, cp, p1, eta_c=1, eta_t=1, delta=0)`

- **Propósito físico:** comprobar la familia de modelos antes de analizar su dominio: finitud, T3>T1>0, gamma>1, cp/p1>0, eficiencias en (0,1] y pérdida en [0,1). La relación T3>T1 es una condición de entrada del estudio motor, no prueba suficiente de viabilidad.
- **Retorno:** `None`; `ValueError` si se incumple. No recibe rp ni decide sobre un punto del barrido.
- **Llama:** ninguna función propia. La llaman `calcular_estados`, `evaluar_punto`, `calcular_dominios`, `main` y los módulos de optimización de trabajo/rendimiento (§4.35, §4.38).
- **PYTHON:** argumentos por defecto, `all` sobre un generador y comparaciones encadenadas. No instala dependencias.
- **Ejemplo:** `validar_parametros(288.15,1600,1.4,1005,100,.85,.9,.05)` termina sin valor visible.

#### `calcular_estados(T1, T3, gamma, rp, p1, eta_c=1, eta_t=1, delta=0)`

- **Propósito físico:** evaluar exactamente las ecuaciones de temperaturas y presiones de §14, sin exigir qin o wn positivos. Centraliza la física ideal/no ideal: eficiencias unidad y delta cero recuperan el ideal.
- **Retorno:** diccionario `temperaturas` (tupla de cuatro K), `presiones` (cuatro kPa), `T2s`/`T4s` [K]. El ideal usa la expresión algebraicamente equivalente T3*(p1/p3)**a; puede diferir en el último bit de T3/rp**a.
- **Validación/errores:** llama a `validar_parametros` con cp auxiliar=1; exige rp positivo finito y estados positivos finitos. `ValueError` corresponde a entradas inválidas. Desbordamiento, división por subdesbordamiento o estados no representables generan `ErrorNumerico`, que hereda de `ArithmeticError`. Las ecuaciones de equipos se interpretan como compresor/turbina motores sólo tras clasificarlas.
- **Llama:** `validar_parametros`; la llaman `evaluar_punto` y `calcular_temperaturas`. No importa `main`, evitando dependencias circulares.
- **PYTHON:** potencias, tuplas, diccionario y captura limitada de `OverflowError`/`ZeroDivisionError` alrededor de las operaciones.
- **Ejemplo:** `calcular_estados(288.15,1600,1.4,10,100,.85,.9,.05)['presiones']` → `(100,1000,950,100)`.

#### `calcular_energias(temperaturas, cp)`

- **Propósito físico:** balance cp·ΔT con signo; un trabajo negativo es un resultado matemático interpretable, no una excepción de Python. Comparte las cuatro ecuaciones de energía con la API estricta antigua.
- **Entradas:** secuencia de cuatro temperaturas positivas finitas [K] y cp positivo finito [J/(kg·K)].
- **Retorno:** diccionario `trabajo_compresor`, `trabajo_turbina`, `trabajo_neto`, `calor_aportado`, todos [kJ/kg]. No divide entre qin ni calcula rendimiento.
- **Llama:** ninguna propia; la llaman `evaluar_punto` y `calcular_balance_energetico`.
- **Errores:** `ValueError` para cp/temperaturas inválidos o longitud incorrecta; `ErrorNumerico` para energías no finitas; errores de tipo se propagan.
- **PYTHON:** desempaquetado de cuatro elementos, resta y `.values()` para comprobar resultados.
- **Ejemplo:** `calcular_energias((300,500,450,350),1000)` devuelve wc=200, wt=100, wn=−100, qin=−50 kJ/kg; no es un ciclo motor.

#### `evaluar_punto(T1, T3, gamma, cp, rp, p1, eta_c=1, eta_t=1, delta=0, tolerancia=TOL_REL)`

- **Propósito físico:** consultar un punto sin lanzar excepciones por inviabilidad esperada. Exige márgenes positivos para compresión, expansión, calor y trabajo, con las tolerancias de §14.
- **Retorno:** estados y energías anteriores más `viable` booleano, `motivos` y `fronteras` como tuplas de códigos, diccionarios `margenes`/`tolerancias` con unidades de cada condición, `rendimiento=wn/qin` y `back_work_ratio=wc/wt` sólo si es viable; fuera del motor ambos cocientes son `None`.
- **Motivos:** `compresion`, `expansion`, `calor_aportado`, `trabajo_neto`; se conservan TODOS. `fronteras` identifica condiciones dentro de la banda de cero, aunque otra condición falle lejos de cero.
- **Llama:** `validar_parametros`, `calcular_estados`, `calcular_energias`. La llaman `construir_barrido`, `calcular_ciclo_noideal`, `buscar_maximo_numerico`, `optimizar_trabajo_neto`, `buscar_maximo_rendimiento_numerico`, `optimizar_rendimiento`, `main` (referencia y tabla ideal) y pruebas.
- **Errores:** parámetros inválidos o tolerancia fuera de [0,1) → `ValueError`; estados, energía o escala numéricamente no representables → `ErrorNumerico`. Una lista de motivos no vacía es una devolución normal.
- **PYTHON:** `tuple(c for ... if ...)` filtra códigos; `not motivos` es `True` para tupla vacía; `**estados` y `**energias` reúnen diccionarios. La expresión condicional evalúa el cociente sólo en la rama viable, evitando divisiones engañosas.
- **Ejemplo:** `evaluar_punto(288.15,1600,1.4,1005,200,100,.85,.9,.05)` da calor positivo y trabajo negativo: `motivos=('trabajo_neto',)` y `rendimiento=None`.

#### `bisectar_raiz(funcion, inferior, superior, tolerancia=1e-12, iteraciones=100)`

- **Propósito:** resolver una raíz, no optimizar trabajo. `funcion` es un objeto invocable de un escalar a otro; los extremos, la raíz x y Q no tienen unidades en este uso. El número máximo de iteraciones es un entero positivo.
- **Retorno:** escalar con raíz aproximada. Acepta una raíz exacta en los extremos; si no, exige signos opuestos. Repite el punto medio y conserva la mitad con cambio de signo hasta ancho <= tolerancia*max(abs(medio),1), o residuo exactamente cero.
- **Llama:** el callback recibido; la llama `calcular_dominios` dos veces cuando hay dos raíces distintas. Usar una función como argumento es pasar una operación sin ejecutarla todavía.
- **Errores:** `ValueError` para controles/intervalo inválidos o ausencia de cambio de signo; `ErrorNumerico` para función no finita o agotamiento de iteraciones. Ninguno se silencia en el barrido.
- **PYTHON:** `for _ in range(iteraciones)` repite un número acotado de veces; `_` indica que el índice no se usa. `(fm>0)==(fi>0)` compara signos sin multiplicar números que podrían desbordarse.
- **Ejemplo:** `bisectar_raiz(lambda x: x*x-2,1,2)` → aproximadamente `1.41421356237`. `lambda` crea una función corta; no es una ecuación adicional del simulador.

#### `calcular_dominios(T1, T3, gamma, cp, p1, eta_c=1, eta_t=1, delta=0)`

- **Propósito físico:** obtener fronteras independientemente del intervalo representado. La demostración de §14 prueba un dominio abierto, único o vacío para ESTE modelo. cp y p1 no alteran sus límites, aunque se validan y sí cambian energías/presiones dimensionales.
- **Retorno:** diccionario con `ideal` y `noideal`; cada uno contiene `intervalo=(inferior,superior)` o `()`, `expansion` (cota inferior), `calor` (cota superior) y `trabajo` (raíces ordenadas o `()`). Todos son rp adimensionales. El no ideal añade `discriminante`; el contenedor añade `tolerancia_puntos=1e-10` y `tolerancia_biseccion=1e-12`.
- **Método:** cotas de expansión/calor analíticas; discriminante y convexidad establecen dónde puede haber Q<0; bisección en [0,centro] y [centro,1+h] localiza sus dos ceros. Se convierten x a rp y se intersecta con rp>1, expansión y calor. Si h<=1, no hay motor para x>=k>=1, evitando intervalos ficticios por redondeo de la raíz x=1.
- **Función local `Q(x)`:** cierre dentro de `calcular_dominios` que recibe x adimensional, devuelve `(x−1)*(x−h)+h*(k−1)` y utiliza h/k del ámbito exterior. No llama a funciones propias; la llama `bisectar_raiz`. No es una nueva API pública. Ejemplo conceptual con h=4 y k=1: Q(2)=−2. Un resultado no finito lo rechaza la bisección.
- **Llama:** `validar_parametros`, `bisectar_raiz`. La llaman `construir_barrido`, `calcular_ciclo_noideal` en rechazos, `buscar_optimo_numerico`, las funciones de `optimizacion.py` cuando no reciben dominio, `estudiar_rendimiento_ideal`, `buscar_maximo_rendimiento_numerico`, `optimizar_rendimiento`, `main` y pruebas.
- **Errores:** entradas inválidas → `ValueError`; fronteras/cuadrática no representables o dominio ideal indistinguible de rp=1 → `ErrorNumerico`. Dominio no ideal vacío → resultado normal `intervalo=()`, no excepción.
- **PYTHON:** función anidada, tupla vacía y `max`/`min` para intersecar intervalos; `**` es potencia al convertir x a rp.
- **Ejemplo:** `calcular_dominios(288.15,1600,1.4,1005,100,.85,.9,.05)['noideal']['intervalo']` → aproximadamente `(1.0696541023,155.4543260392)`.

#### `describir_inviabilidad(punto, dominio)`

- **Propósito:** explicación de todas las condiciones fallidas y de los límites físicos; no recalcula ecuaciones. `punto` procede de `evaluar_punto`; `dominio` es el subdiccionario ideal/noideal de `calcular_dominios`.
- **Retorno:** `str` con motivos traducidos mediante `MOTIVOS`, intervalo abierto o aviso de dominio vacío, y exclusión de fronteras/banda numérica. rp no tiene unidad; los estados conservan las suyas.
- **Llama:** ninguna propia; la llaman `main`, `calcular_ciclo_noideal` y pruebas.
- **PYTHON:** `'; '.join(...)` une todos los motivos; `or` permite texto de punto viable con tupla vacía.
- **Errores:** un diccionario mal formado puede producir `KeyError`/`TypeError`, que se propagan; no captura fallos de programación.
- **Ejemplo:** `describir_inviabilidad(punto, dominios['noideal'])`, tras las llamadas anteriores, incluye `1.069654102 < rp < 155.454326`.

#### `construir_barrido(T1, T3, gamma, cp, p1, eta_c=1, eta_t=1, delta=0, relaciones=None, dominios=None, puntos_interes=())`

- **Propósito físico:** separar el estudio numérico del dibujo, mantener puntos inviables con motivos y ofrecer curvas exclusivamente motoras.
- **Entradas:** ocho escalares del contrato común; `relaciones` opcional, secuencia 1D finita, positiva, estrictamente creciente con al menos dos puntos; `dominios` opcional, resultado coherente de `calcular_dominios` para esos mismos parámetros. Si se aportan dominios, el llamador debe garantizar su coherencia.
- **Retorno:** diccionario `relaciones` (array rp), `dominios`, `ideal` y `noideal`. Cada modelo contiene lista `puntos` con todos los estados/energías y clasificación, máscara booleana `viable`, lista `motivos`, arrays `rendimiento` [fracción] y `trabajo_neto` [kJ/kg] que valen `np.nan` fuera del motor. El trabajo firmado original permanece en `puntos`.
- **Muestreo:** 500 puntos geométricos + 500 lineales entre 1 y `1.05*limite_ideal`, sin tope fijo (se evita desbordar al multiplicar). Añade fronteras y vecinos relativos ±1e−6, 101 puntos por intervalo motor y 17 puntos geométricos alrededor de cada `rp` de `puntos_interes`, además del punto exacto. `main` suministra referencia y dos máximos: menos de 1300 puntos en los casos comprobados, sin crecer con la extensión física del dominio. `np.unique` ordena/elimina duplicados. El radio de cada detalle es el 1.5 % de la amplitud logarítmica de la vista, limitado a sus extremos. El contrato permite más puntos de interés a usuarios directos, aumentando el coste proporcionalmente.
- **Entradas nuevas y retorno:** `puntos_interes` es un iterable opcional de rp finitos en la vista (adimensionales); sólo interviene al construir la malla automática. El resultado añade `intervalo_visual=(rp_min,rp_max)`. Con `relaciones` explícitas se conserva la malla suministrada. Dominio y datos suministrados deben corresponder a los mismos parámetros.
- **Llama:** `calcular_dominios` si no se recibe y `evaluar_punto` para cada modelo y rp. La llaman `main`, las dos funciones gráficas que admiten barrido opcional y pruebas. `main` verifica comparaciones sólo donde ambos modelos son motores.
- **Errores:** malla inválida → `ValueError`; problemas numéricos → `ErrorNumerico`; errores inesperados se propagan. No captura `ValueError` para saltar puntos. Inviabilidad → máscara falsa y motivos.
- **PYTHON:** `np.asarray(...,dtype=float)` normaliza el contenedor; `.ndim`/`np.diff` revisan forma/orden; `np.geomspace` multiplica por un factor constante; `.extend` incorpora muestras; `np.unique` ordena y deduplica. `mascara` es array de booleanos y `~mascara` lo invierte elemento a elemento. NaN es un valor flotante especial que interrumpe un trazo de Matplotlib; no equivale a trabajo cero.
- **Ejemplo:** `b=construir_barrido(288.15,1600,1.4,1005,100,.85,.9,.05,relaciones=[1,2,10,200,500])`; `b['noideal']['motivos'][3]` indica sólo trabajo no positivo.

### 4.33. `marcar_dominio(ejes, dominio, etiqueta, color)` — main.py

- **Propósito:** añadir escala logarítmica de rp, fronteras discontinuas visibles y banda tenue del intervalo motor; dominio vacío se indica en leyenda. Es presentación de límites ya calculados.
- **Entradas:** `Axes` de Matplotlib, subdiccionario de dominio (rp adimensional), etiqueta y color como cadenas.
- **Retorno:** `None`; modifica los ejes, conserva su intervalo visible y no calcula estados ni optimiza.
- **Llama:** ninguna función propia. La llaman `guardar_grafica_rendimiento`, `guardar_grafica_trabajo_neto` y `guardar_comparaciones_ciclos`.
- **PYTHON:** `axvline` dibuja vertical, `axvspan` banda horizontal entre dos abscisas, `set_xscale('log')` cambia escala; `.get_xlim()`/`.set_xlim()` conservan límites. Estos métodos no cambian muestras ni unidades.
- **Errores:** estructuras/objetos incorrectos y errores de Matplotlib se propagan.
- **Ejemplo:** `marcar_dominio(ejes,dominios['ideal'],'ideal','tab:blue')` tras dibujar los datos.

### 4.34. Métodos de `ViabilidadTests` — tests/test_viabilidad.py

Todos los métodos de prueba reciben sólo `self`, devuelven `None` y los llama `unittest`. Las aserciones fallidas producen `AssertionError`; las excepciones esperadas se comprueban con `assertRaises`. No son nuevas funciones del simulador. Ejemplo común: `python -B -m unittest discover -s tests -v`.

- `setUp(self)`: inicializa parámetros de referencia y dominios antes de cada prueba.
- `punto(self,rp,ideal=False,**cambios)`: helper llamado por las pruebas, devuelve el diccionario de `evaluar_punto`; rp adimensional y cambios con unidades del contrato común. `**cambios` recoge argumentos nombrados en un diccionario; actualiza sólo la copia local de parámetros. Propaga errores de evaluación. Ejemplo: `self.punto(200)` obtiene trabajo negativo.
- `test_limites_ideales_y_optimo_distintos`: llama a dominios, punto y óptimo; verifica frontera y ambos lados.
- `test_expansion_con_perdidas_y_motivos_simultaneos`: evalúa la frontera 1/(1−delta) y conserva expansión/trabajo fallidos.
- `test_frontera_calor`: evalúa calor cero y trabajo negativo.
- `test_raices_trabajo_y_vecindades`: comprueba residuos de bisección y ambos lados de cada raíz.
- `test_calor_positivo_no_basta_para_motor`: comprueba rp=200, qin>0 y wn<0.
- `test_limite_reversible_en_estados_dominios_y_barrido`: contrasta diccionarios, límites, máscaras y arrays con pérdidas cero.
- `test_dominio_vacio_sin_perdida_y_con_perdida`: comprueba ejemplos sin motor, incluido h=1 y discriminante cero.
- `test_dominios_coinciden_con_clasificacion_en_combinaciones`: contrasta interior calculado y evaluación en familias de eficiencias/pérdidas.
- `test_invariancia_limites_con_cp_y_presion`: verifica independencia de fronteras respecto a factores dimensionales.
- `test_barrido_mixto_conserva_motivos_y_nan`: inspecciona arrays y clasificación con puntos motores y excluidos; coste de malla.
- `test_graficas_reciben_nan_sin_puentear_zonas_excluidas`: intercepta figuras y comprueba NaN en las líneas reales de ambas comparaciones. Su función local `capturar(*args,**kwargs)` recibe los argumentos de `plt.subplots`, llama al original, registra (Figure,Axes) y devuelve esa pareja; no tiene unidades, ecuaciones ni captura errores. Se usa sólo dentro de `patch` y se cierran recursos en `finally`.
- `test_parametros_invalidos_no_son_inviabilidad`: verifica `ValueError` en entradas/malla inválidas.
- `test_limite_numerico_no_se_clasifica_como_inviabilidad`: exige `ErrorNumerico` en potencias/estados no representables.
- `test_biseccion_y_errores_de_acotacion`: contrasta raíz de x²−2, mal intervalo, NaN y agotamiento de iteraciones.
- `test_texto_con_todos_los_motivos_y_limites`: verifica mensaje completo, no un motivo arbitrario.
- `test_flask_acepta_caso_motor_con_antiguo_barrido_inviable`: POST real con T3=800 K, HTML completo y nuevo contenido físico.
- `test_flask_muestra_limite_numerico_y_conserva_datos`: inyecta `ErrorNumerico`, exige HTTP 400 y entradas conservadas.
- `test_busqueda_ideal_se_adapta_sin_optimizar_noideal`: verifica malla interior y máximo ideal para T3=400 K.

### 4.35. Optimización — `optimizacion.py`

Las unidades comunes son T [K], cp [J/(kg·K)], p1 [kPa]; gamma, eficiencias, delta y rp son adimensionales. Se reciben escalares reales. `dominio` es el diccionario `ideal` o `noideal` de `calcular_dominios` **para esos mismos parámetros**, no un resultado persistido. Sin él, las funciones lo recalculan. Para el ideal se pasan eficiencias unidad y delta cero. §14 deriva las ecuaciones; la guía independiente de Fase 2 desarrolla el algoritmo paso a paso.

#### `calcular_candidato_analitico(T1, T3, gamma, eta_c=1, eta_t=1, delta=0)`

- **Propósito físico:** punto estacionario matemático del trabajo. No garantiza viabilidad por sí solo; puede ser menor que 1 o existir sin motor.
- **Argumentos/retorno:** seis escalares en las unidades anteriores → `float` rp positivo finito, sin unidades. cp y p1 no aparecen en la condición estacionaria.
- **PYTHON:** calcula `exponente=(log(T3)-log(T1)+log(eta_c)+log(eta_t)-a*log(1-delta))/(2*a)` y `exp(exponente)`. Las identidades logarítmicas evitan productos intermedios desbordados; no eliminan los límites de representación del resultado.
- **Llama:** `validar_parametros` con cp=p1=1 auxiliares (validación, no un nuevo supuesto físico). La llaman `optimizar_trabajo_neto` y pruebas/usuarios directos.
- **Errores:** `ValueError` de parámetros; `ErrorNumerico` encadena `OverflowError` o rechaza candidato no representable. No transforma un fallo numérico en dominio vacío.
- **Ejemplo:** `calcular_candidato_analitico(288.15,1600,1.4,.85,.9,.05)` → 12.8950516696. Sólo el coordinador comprueba que sea motor.

#### `buscar_maximo_numerico(T1, T3, gamma, cp, p1, eta_c=1, eta_t=1, delta=0, dominio=None, muestras=257, tolerancia_log=1e-9, max_iteraciones=100)`

- **Propósito físico:** máximo motor obtenido sin consultar el candidato analítico. Usa exclusivamente el dominio y las energías de Fase 1. El trabajo con signo guía el refinamiento, pero sólo se acepta un punto con `viable=True`.
- **Argumentos:** ocho parámetros físicos comunes; `dominio` opcional coherente; `muestras` entero de 5 a 4097; `0<tolerancia_log<1` finita, adimensional, anchura de parada en log(rp); `max_iteraciones` entero de 1 a 1000. El coste está limitado por estos controles.
- **Retorno:** `None` si el dominio físico está vacío; en otro caso, diccionario con `rp`, `ciclo` (contrato íntegro de `evaluar_punto`), `intervalo_fisico` abierto, `intervalo_busqueda` interior, `intervalo_final` del refinamiento (parejas de rp), `paso_log_inicial`, `tolerancia_log`, `resolucion_rp` (rp), `evaluaciones`, `iteraciones` y `muestras_iniciales` (enteros). La resolución es una escala conservadora, no un certificado de error.
- **PYTHON:** `np.linspace` en log(rp), comprensión de evaluaciones escalares, `int(np.argmax(trabajos))`, sección áurea con `for/else` y asignaciones múltiples. `max(aceptados,key=lambda par:par[1]['trabajo_neto'])` elige el mejor trabajo registrado, no el mayor rp ni la fórmula analítica. `np.finfo(float).eps` describe el redondeo de la representación numérica.
- **Función local `evaluar(y)`:** recibe un escalar `y=ln(rp)` adimensional, devuelve trabajo firmado [kJ/kg]. Cierra sobre parámetros, límites y `registros`; comprueba interior estricto y memoriza `evaluar_punto` en un diccionario local indexado por rp. La llaman la comprensión y el refinamiento, nunca persiste entre ejecuciones. Errores de interior/estado se propagan. Ejemplo interno: `evaluar(log(10))` evalúa rp=10 si pertenece al intervalo.
- **Llama:** `validar_parametros`, `calcular_dominios` si falta dominio, `evaluar_punto` mediante la función local. La llaman `optimizar_trabajo_neto` y pruebas/usuarios directos; `main` la alcanza a través del coordinador.
- **Errores:** `ValueError` de parámetros/controles; `ErrorNumerico` si la ventana no es representable, argmax cae en un extremo de la malla interior, no converge o ningún punto supera la banda de viabilidad. Propaga errores de evaluación sin ocultarlos.
- **Ejemplo:** `n=buscar_maximo_numerico(288.15,1600,1.4,1005,100,.85,.9,.05)`; `n['rp']≈12.8950517350` y `n['ciclo']['trabajo_neto']≈373.210827` kJ/kg.

#### `optimizar_trabajo_neto(T1, T3, gamma, cp, p1, eta_c=1, eta_t=1, delta=0, dominio=None)`

- **Propósito:** separar candidato, máximo motor y ausencia de motor; evaluar estados y contrastar los dos métodos con tolerancias (§14).
- **Entradas:** ocho escalares físicos y dominio opcional coherente, en las unidades comunes.
- **Retorno:** `estado` (`disponible`/`sin_dominio`), `motivo`, `candidato` matemático, `dominio`, `analitico` (`rp` y `ciclo`), `numerico` (contrato anterior) y `concordancia` (`diferencia_rp`, `tolerancia_rp`, `diferencia_trabajo` y `tolerancia_trabajo`). Los dos últimos valores de trabajo se expresan en kJ/kg, los de rp son adimensionales. Con dominio vacío, analítico, numérico y concordancia son `None`; no llama a la búsqueda ni propone cero como óptimo.
- **Validación/errores:** parámetros comunes, candidato interior estricto y motor según Fase 1. Lanza `ErrorNumerico` si el máximo no se resuelve por encima de la banda cero o si los métodos discrepan; propaga los demás errores sin inventar máximos en fronteras.
- **Llama:** `calcular_dominios` o `validar_parametros`, `calcular_candidato_analitico`, `evaluar_punto` y `buscar_maximo_numerico`. La llaman `main` dos veces por ejecución y las pruebas.
- **PYTHON:** retornos tempranos para dominio vacío, diccionarios anidados, comparaciones de tolerancias y nombres locales. No modifica los parámetros ni mantiene estado global.
- **Ejemplo:** `r=optimizar_trabajo_neto(288.15,1600,1.4,1005,100,.85,.9,.05)`; `r['analitico']['ciclo']['temperaturas'][1]≈652.972971` K.

### 4.36. `seccion_optimizacion_html(parametros, referencias, optimizaciones, barrido)` — reporting.py

- **Propósito:** presentar resultados ya calculados, sin ecuaciones físicas nuevas.
- **Entradas:** `parametros` diccionario de nueve entradas; `referencias={'ideal':ciclo_i,'noideal':ciclo_r}`; `optimizaciones` con los dos estudios anteriores; `barrido` opcional para describir la vista (§4.32). Las claves de referencia sólo se consultan si ese estudio está disponible. Unidades de los diccionarios físicos: rp sin unidades, trabajo kJ/kg, T K, p kPa; rendimiento fracción que se presenta multiplicada por 100.
- **Retorno:** cadena HTML con encabezado «Optimización del trabajo específico neto», tablas, estados del óptimo no ideal, diferencias ideal menos no ideal y diagnósticos numéricos. Sin motor muestra «No disponible» y su motivo.
- **Llama:** `tabla_html`; la llama `crear_informe_html` y pruebas directas. Utiliza `escape` en textos variables, f-strings, bucle, `continue`, `enumerate(zip(...),start=1)` y `join`. No cambia los datos recibidos.
- **Errores:** `KeyError`/`TypeError` si faltan datos o son incompatibles; recibe estructuras verificadas, no valida nuevamente el modelo.
- **Ejemplo:** con `r` y `i` ya calculados, `seccion_optimizacion_html({'relacion_presiones':10},{'ideal':ref_i,'noideal':ref_r},{'ideal':i,'noideal':r},b)` produce el fragmento incorporado al informe.

### 4.37. `OptimizacionTests` — tests/test_optimizacion.py

`setUp(self)` prepara ocho parámetros comunes; cada método `test_*(self)` devuelve `None` o lanza una aserción, y lo llama `unittest`. Las 15 pruebas cubren fórmula independiente, curvatura, resultados/estados, independencia numérica (parche de la fórmula), pertenencia interior para familias de parámetros, reversibilidad, vacío sin buscar, dominio estrecho/resolución cero, controles, máximos fuera de ventanas antiguas, efecto de cp/p1, muestreo completo y NaN, paneles/marcadores, HTML sin máximos ficticios y cuatro POST sucesivos con descarga. Usan la API física, optimizador, dibujado y cliente Flask; los efectos se aíslan en carpetas temporales. Los callbacks locales `capturar(figura,*args,**kwargs)` guardan las figuras inspeccionadas y delegan a `Figure.savefig`, retornando su valor; no implementan física. La prueba de informe anterior conserva su método, imágenes y referencias; sólo sustituye la expectativa del número discreto heredado por el resultado de la nueva búsqueda.

### 4.38. Rendimiento — `optimizacion_rendimiento.py`

La física de esta API se implementó en parte 1 y se reutiliza desde `main` en parte 2; también admite llamadas directas/pruebas. Sus resultados se pasan a gráficas, HTML y Flask sin copiar ecuaciones. Las funciones anteriores, sus contratos y resultados no cambian. El [documento provisional de Fase 3](docs/milestones/05_optimizacion_rendimiento_APRENDIZAJE.md) demuestra la existencia/unicidad y desarrolla las decisiones ya terminadas; la integración y la revisión documental están completadas, con la fase aún sin commit.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Unidades comunes: T1/T3 [K], cp [J/(kg·K)], p1 [kPa], energías [kJ/kg]; rp, gamma, eta_c, eta_t, delta y rendimiento (fracción) adimensionales. Con a=(gamma−1)/gamma>0, x=rp^a, theta=T3/T1, B=1+eta_c*(theta−1), h=eta_c*eta_t*theta, k=(1−delta)^(-a), H=h*k:

```text
qin = (cp/1000)*(T1/eta_c)*(B−x)
W   = (cp/1000)*(T1/eta_c)*N(x),  N(x)=1+h−x−H/x
eta = N(x)/(B−x)
F(x)=N'(x)*(B−x)+N(x)=A+H*B/x²−2*H/x, A=1+h−B
eta'(x)=F(x)/(B−x)²
F'(x)=−2*H*(B−x)/x³ < 0 para x<B
```

En el ideal `eta=1−rp^(-a)`, `deta/drp=a*rp^(-a−1)>0`: no hay máximo interior, sólo supremo `1−T1/T3` en la frontera `rp=theta^(1/a)`. Allí calor y trabajo son nulos, el cociente físico no se evalúa y la frontera no es motora.

Con cualquier pérdida estricta (eta_c<1, eta_t<1 o delta>0) se cumple `S=H−A*B=(B−1)*(B−h)+h*(k−1)>0`, pues `B−h=(1−eta_c)+eta_c*theta*(1−eta_t)≥0`. Si hay dominio motor, sus dos fronteras de trabajo tienen calor positivo, F es positiva en la inferior y negativa en la superior. Como F decrece estrictamente, existe un único máximo interior. En él `eta''(x)=−2*H/[x³*(B−x)]<0`. El candidato es la raíz racionalizada `x*=B/(1+sqrt(S/H))` de `A*x²−2*H*x+H*B=0`, válida también si A=0 o A<0. En el caso exactamente reversible S=0 esta raíz cae en B: es la frontera excluida, no un máximo. Dominio vacío y límite numérico se tratan por separado.

**PYTHON: contratos y llamadas.** Los parámetros físicos son escalares reales. Se reutilizan `calcular_dominios`, `validar_parametros` y `evaluar_punto`; no se copian ecuaciones de estados/balance ni se añade dependencia. `expm1(z)` calcula exp(z)−1 y `log1p(z)` calcula ln(1+z) con mejor comportamiento para z pequeño; se usan para no perder pérdidas diminutas por restas de números próximos. La reversibilidad exige igualdades exactas de parámetros, no una aproximación arbitraria.

#### `estudiar_rendimiento_ideal(T1, T3, gamma, cp, p1)`

- **Propósito/retorno:** identifica el supremo ideal sin evaluar la frontera. Devuelve diccionario `estado='supremo_no_alcanzado'`, `motivo`, `dominio` ideal de Fase 1, `candidato/analitico/numerico/concordancia=None` y `supremo={'rendimiento':1−T1/T3,'rp_frontera':limite,'alcanzado':False}`. La rp de frontera no es rp óptima.
- **Llama:** `calcular_dominios`, que valida los cinco escalares y calcula límites. La llaman `main`, ambas funciones de búsqueda/coordinación en el caso reversible y las pruebas/usuarios directos.
- **Errores/PYTHON:** propaga `ValueError` de entradas y `ErrorNumerico` de fronteras; división escalar y diccionario con `None`/`False` separan ausencia y no alcanzabilidad. No tiene efecto en archivos.
- **Ejemplo:** `estudiar_rendimiento_ideal(288.15,1600,1.4,1005,100)['supremo']` → rendimiento 0.81990625, frontera rp≈403.41752032, no alcanzado.

#### `calcular_candidato_rendimiento(T1, T3, gamma, eta_c=1, eta_t=1, delta=0)`

- **Propósito/retorno:** raíz estacionaria matemática, sin garantizar dominio. Seis escalares en las unidades comunes → float rp positivo finito; `None` sólo para reversibilidad exacta. Se usa S como suma no negativa para evitar la cancelación de H−A*B; rp se calcula como `exp((log(B)−log1p(sqrt(S/H)))/a)`.
- **Llama:** `validar_parametros` con cp=p1=1 auxiliares. La llama `optimizar_rendimiento` y pruebas/usuarios directos. No llama a la búsqueda numérica.
- **Errores/PYTHON:** `ValueError` de entrada; `ErrorNumerico` en coeficientes, desbordamiento o resultado no representable. `try/except` y `raise ... from error` conservan la causa de desbordamiento/división. El resultado debe comprobarse contra el dominio antes de aceptarlo.
- **Ejemplo:** `calcular_candidato_rendimiento(288.15,1600,1.4,.85,.9,.05)` → 35.4523235708.

#### `buscar_maximo_rendimiento_numerico(T1, T3, gamma, cp, p1, eta_c=1, eta_t=1, delta=0, muestras=257, tolerancia_log=1e-9, max_iteraciones=100)`

- **Argumentos:** ocho parámetros físicos comunes; entero `muestras` de 5 a 4097 (no booleano), tolerancia logarítmica finita 0<t<1 y entero `max_iteraciones` de 1 a 1000 (no booleano).
- **Retorno:** con vacío, `estado='sin_dominio'`, motivo/dominio y `rp/ciclo/supremo=None`; con reversibilidad, el contrato de `estudiar_rendimiento_ideal`, sin máximo numérico. Con máximo, `estado='maximo_interior'`, motivo, dominio, rp, ciclo íntegro de `evaluar_punto`, supremo=None, `intervalo_busqueda`, `intervalo_final` (parejas rp), `paso_log_inicial`, `tolerancia_log`, `resolucion_rp` (rp), `muestras_iniciales`, `evaluaciones` y `iteraciones` (enteros).
- **Método:** recalcula siempre `calcular_dominios` con las entradas actuales. En ln(rp), margen interior de `8*eps*max(1,abs(ylo),abs(yhi))`, 257 puntos y sección áurea entre vecinos del mejor. No consulta el candidato analítico. Se exige descenso admisible a ambos lados, mayor que 64*eps en rendimiento, para no aceptar una cima recortada por la banda numérica. Esto es una salvaguarda, no una garantía absoluta de error.
- **Función local `evaluar(y)`:** recibe ln(rp) escalar, devuelve rendimiento fraccionario sólo si `evaluar_punto` clasifica motor; en otro caso devuelve −infinito como marca de exclusión, nunca como resultado físico. Cierra sobre parámetros, dominio y diccionario `registros` de una sola búsqueda. La llaman la comprensión inicial y el refinamiento. Ejemplo interno: `evaluar(log(10))` consulta rp=10; no divide por qin inválido, porque usa el rendimiento ya protegido por Fase 1. Propaga errores de estados/energías.
- **Llama:** `validar_parametros`, `calcular_dominios`, `estudiar_rendimiento_ideal` si reversible y `evaluar_punto` mediante el cierre. La llama `optimizar_rendimiento` y pruebas/usuarios directos.
- **Errores:** `ValueError` de controles/entradas; `ErrorNumerico` de intervalo no representable, ausencia de muestras admisibles, máximo en extremo de malla, agotamiento de iteraciones o falta de testigos de descenso. No etiqueta esos fallos como supremos ni vacíos.
- **PYTHON:** arrays, `argmax`, cierre/caché local, `for/else`, asignaciones múltiples y `max(key=lambda...)` reutilizan conceptos de Fase 2; `-np.inf` permite excluir sin dividir ni aceptar puntos inviables.
- **Ejemplo:** `n=buscar_maximo_rendimiento_numerico(288.15,1600,1.4,1005,100,.85,.9,.05)`; `n['rp']≈35.4523219222`, 297 evaluaciones.

#### `optimizar_rendimiento(T1, T3, gamma, cp, p1, eta_c=1, eta_t=1, delta=0)`

- **Propósito:** identifica el tipo de solución antes de proponer un máximo; contrasta dos métodos independientes y entrega estados/balances en el óptimo admisible.
- **Argumentos/retorno:** ocho escalares comunes → diccionario `estado`, motivo, dominio, candidato, analítico, numérico, concordancia y supremo. Si reversible, contrato del estudio ideal; con vacío, candidato/analítico/numérico/concordancia/supremo=None. Con máximo, `analitico={'rp':...,'ciclo':...}`, `numerico` tiene el contrato anterior y `concordancia` contiene diferencias/tolerancias de rp y rendimiento más `condicion_cociente`.
- **Llama:** `calcular_dominios`, `estudiar_rendimiento_ideal` si reversible, `calcular_candidato_rendimiento`, `evaluar_punto` y `buscar_maximo_rendimiento_numerico`. La llaman `main` y pruebas/usuarios directos.
- **Comprobaciones:** candidato dentro del dominio abierto y `viable=True`; `|Δrp|≤2e−6*max(rp_a,rp_n)`. Para eta, `|Δeta|≤max(1e−10,64*eps*condicion)`, con `condicion=(cp/1000*T3)/min(qin_a,qin_n)`: estima amplificación del redondeo en W/qin cerca de calor nulo. Son tolerancias de concordancia, no incertidumbre experimental ni cotas rigurosas.
- **Errores:** propaga entradas inválidas y errores de cálculo; `ErrorNumerico` si el candidato no es interior/motor resoluble o si discrepan métodos. No se acepta un punto de frontera ni se transforma pérdida pequeña en reversibilidad.
- **Ejemplo:** `r=optimizar_rendimiento(288.15,1600,1.4,1005,100,.85,.9,.05)`; `r['analitico']['ciclo']['rendimiento']≈0.438931071631`, trabajo≈313.738915263 kJ/kg y calor≈714.779462063 kJ/kg. La rp numérica es≈35.4523219222, frente a analítica≈35.4523235708. En Fase 2 el máximo trabajo estaba en rp≈12.8950516696, con trabajo≈373.210827483 kJ/kg y rendimiento≈0.392126144220.

**Precisión y límites.** Paso inicial, parada en ln(rp) y precisión efectiva de rp son distintos. Se mantiene la escala conservadora `rp*max(tolerancia_log,32*sqrt(eps))` de Fase 2, sin prometer un certificado de error. El máximo devuelto es el mejor registro admisible; puede quedar fuera del intervalo final por empates de redondeo. Un dominio matemático muy estrecho o un máximo dentro de la banda cero produce error numérico, no un supremo ni otra hipótesis física.

**Pruebas:** `tests/test_optimizacion_rendimiento.py` añade `RendimientoTests`; `setUp(self)` prepara parámetros, y los 20 `test_*(self)` no retornan resultado físico: verifican monotonía/supremo ideal, fórmula por balance, estacionariedad/curvatura/unicidad, familias con pérdidas individuales y combinadas, coeficiente A nulo/negativo, vacío, casi reversibilidad, fronteras/bandas, independencia numérica, controles, cp/p1, recálculo y diferencia entre objetivos. `unittest` los invoca; usan módulos físicos/optimizadores, sin dibujar ni publicar. Los callbacks locales `comprobar(*args,**kwargs)` y `recortar(*args,**kwargs)` inspeccionan o restringen evaluaciones para comprobar no aceptación de fronteras; `alterar(*args,**kwargs)` simula discrepancia. Devuelven diccionarios de pruebas, no implementan nuevas ecuaciones. Verificación de esta parte el 20 de octubre de 2026: **75 pruebas superadas** (55 anteriores sin modificar y 20 nuevas), en 67.656 s con `python -B -m unittest discover -s tests -v`. Las pruebas de integración existentes usan carpetas temporales; no constituyen validación experimental.

### 4.39. Integración de rendimiento y comparación de criterios

#### `comparar_criterios(trabajo, rendimiento)` — optimizacion_rendimiento.py

- **Propósito:** comparar resultados existentes, sin recalcular temperaturas, presiones ni balances. Recibe dos diccionarios: optimización de trabajo de Fase 2 y estudio no ideal de rendimiento de §4.38; los datos deben corresponder a los mismos parámetros.
- **Retorno:** `estado='disponible'`, `motivo`, `punto_a` (máximo trabajo), `punto_b` (máximo eta), `diferencia_rp`=rp_B−rp_A, `ganancia_rendimiento_pp`=100(eta_B−eta_A), `reduccion_trabajo_porcentaje`=100(W_A−W_B)/W_A y `diferencia_calor`=qin_B−qin_A [kJ/kg]. rp es adimensional; ganancia en puntos porcentuales y reducción en porcentaje son distintos. Cada punto conserva `rp/ciclo` sin copiar ni modificar sus campos. Si falta uno de los máximos, `estado='no_disponible'`, B y diferencias=None; A se conserva si está disponible. Un supremo nunca crea B.
- **PYTHON/llamadas:** diccionarios, retorno temprano y operaciones escalares; no llama a funciones propias. La llaman `main` y pruebas. Supone contrato motor verificado W_A>0; datos mal formados pueden dar KeyError/TypeError y no se ocultan.
- **Ejemplo:** `comparar_criterios(optimizar_trabajo_neto(288.15,1600,1.4,1005,100,.85,.9,.05),optimizar_rendimiento(288.15,1600,1.4,1005,100,.85,.9,.05))` devuelve Δrp≈22.5572719011, ganancia≈4.6804927411 pp, reducción W≈15.9352054763 % y Δqin≈−236.9827016782 kJ/kg.

#### `guardar_grafica_compromiso(barrido, comparacion, ruta)` — main.py

- **Entradas:** barrido de Fase 1/2 de esta ejecución; comparación anterior; destino Path/cadena/buffer binario. W [kJ/kg] horizontal y eta [%] vertical, convertida desde fracción. rp es parámetro y determina el orden de las muestras, no otro eje.
- **Salida/propósito:** None, PNG 1350×900 (9×6 pulgadas, 150 dpi). Curva no ideal con NaN en ambas coordenadas para las muestras excluidas, rombo naranja A y estrella verde B si existen. Si B no está disponible lo explica sin inventar un marcador. No afirma que toda la curva sea una frontera de Pareto: hay tramos dominados y las ramas pueden volver hacia trabajos menores.
- **PYTHON/llamadas:** selecciona arrays ya clasificados, plot/scatter, bucle sobre puntos disponibles, f-string, guardado y cierre. No calcula física ni llama a otras funciones propias. La llaman main y pruebas; propaga errores de estructura/dibujo/escritura.
- **Ejemplo:** `buffer=BytesIO(); guardar_grafica_compromiso(barrido,comparacion,buffer)`; consultar `buffer.getvalue()` y cerrar el buffer.

#### `seccion_rendimiento_html(estudios, comparacion)` — reporting.py

- **Entradas:** diccionario estudios con claves ideal/noideal de §4.38 y comparación de criterios. Unidades recibidas: rp adimensional, T K, p kPa, W/qin kJ/kg, eta fracción; sólo presenta eta multiplicada por 100.
- **Retorno/propósito:** str HTML de «Optimización del rendimiento térmico»: supremo ideal no alcanzado, estado no ideal, resultados analítico/numérico y concordancia, estados óptimos, tabla A/B y diferencias, símbolos y limitaciones. Vacío o supremo se muestran sin máximo físico ficticio ni ceros sustitutivos.
- **Llama:** tabla_html; la llaman crear_informe_html y pruebas. Usa listas, bucles, f-strings, escape, enumerate/zip y join; no contiene ecuaciones nuevas ni modifica diccionarios. Datos ausentes/incompatibles producen KeyError/TypeError.
- **Ejemplo:** `seccion_rendimiento_html(estudio_rendimiento,comparacion_criterios)` con los datos reunidos por main produce el fragmento; la imagen de compromiso la incorpora crear_informe_html mediante imagen_html.

**Flujo y compatibilidad.** main obtiene ambos estudios de rendimiento después de los máximos de trabajo, añade rp_B al iterable de puntos de interés sólo si existe y reutiliza construir_barrido. No cambia la rp del formulario ni usa ésta como límite. Los cálculos siempre parten de los nueve parámetros actuales y las cachés de los optimizadores son locales. Flask permanece con nueve campos, loopback y descarga/retención existentes. El rechazo de referencia inviable precede a la optimización: una referencia motora con dominio vacío sería contradictoria. Las API/presentadores independientes sí permiten estudiar el vacío.

crear_informe_html mantiene sus doce argumentos posicionales y añade `*, estudio_rendimiento=None, comparacion_criterios=None`: el asterisco obliga a pasar esos dos por nombre, evitando desplazar contratos anteriores. main los entrega siempre. Sin ellos se admite el formato previo de seis claves PNG; con ellos se requieren las siete claves, se incorpora la sección y se obtiene el número de gráficas de len(imagenes) en cabecera/pie/terminal. Deben suministrarse juntos. No cambia publicación, Git ni protección de archivos ajenos.

Las ocho pruebas de `IntegracionRendimientoTests`, en `tests/test_integracion_rendimiento.py`, reutilizan un informe predeterminado generado en `setUpClass(cls)` con carpeta temporal. Verifican datos físicos/HTML, siete PNG sin recursos externos y dimensiones, puntos de interés, marcadores/NaN, curva paramétrica, supremo reversible sin B, vacío sin informe, cinco POST sucesivos con cambios en los nueve parámetros/descarga/retención y compatibilidad del presentador previo. Los callbacks locales capturan figuras sin calcular física. Las pruebas existentes se conservan, actualizando sólo expectativas de seis a siete imágenes y el replay de kwargs del generador. Verificación previa de parte 2: **83 pruebas superadas**, 51.473 s. Verificación final del 20 de octubre de 2026: **83/83 OK**, 51.733 s. No se han cambiado algoritmos en este cierre; README, milestone y guía A–J se han revisado contra fuentes y resultados.

## 5. Variables principales

Python no añade unidades a sus tipos. El diccionario global `PARAMETROS_PREDETERMINADOS` conserva las entradas; `main()` crea una copia local por ejecución. Un `int` puede producir `float` al operar; Flask convierte todos los campos a `float`, y NumPy utiliza también sus escalares.

### Parámetros de entrada

| Variable | Significado | Unidad | Valor | Tipo inicial |
|---|---|---|---:|---|
| `T1` | Entrada compresor | K | 288.15 | `float` |
| `T3` | Entrada turbina | K | 1600 | `int` |
| `cp` | Calor específico a presión constante | J/(kg·K) | 1005 | `int` |
| `gamma` | `cp/cv` | — | 1.4 | `float` |
| `relacion_presiones` | `p2/p1` | — | 10 | `int` |
| `p1` | Presión inicial | kPa | 100 | `int` |
| `eta_c`, `eta_t` | Eficiencias isentrópicas | — | 0.85, 0.90 | `float` |
| `perdida_presion_combustor` | Fracción de `p2` perdida | — | 0.05 | `float` |

### Estados y resultados físicos

| Variable o clave real | Significado | Unidad | Tipo |
|---|---|---|---|
| `a`, `theta`, `k`, `h`, `discriminante` | Exponente y auxiliares de la cuadrática de viabilidad (§14) | — | escalares |
| `T2`, `T4`, `T2s`, `T4s` | Salidas y referencias isentrópicas | K | escalar |
| `temperaturas`, `temperaturas_optimas` | Estados ordenados 1,2,3,4 | K | `tuple` |
| `presiones`, `p2`, `p3`, `p4` | Presiones | kPa | tupla/escalares |
| `R` | Constante específica del gas | J/(kg·K) | escalar |
| `volumenes`, `v1`, `v2`, `v3`, `v4` | Volúmenes específicos ideales | m³/kg | tupla/escalares |
| `cp_kj` | `cp/1000` | kJ/(kg·K) | escalar |
| `s1`, `s2`, `s3`, `s4`, `entropias` | Entropías relativas ideales | kJ/(kg·K) | escalares/tupla |
| `incremento_23`, `incremento_14` | Saltos positivos de entropía | kJ/(kg·K) | escalares |
| `trabajo_compresor`, `trabajo_turbina`, `trabajo_neto`, `calor_aportado` | Energías específicas | kJ/kg | escalares |
| `rendimiento`, `rendimiento_balance`, `rendimiento_optimo` | Eficiencias fraccionarias | — | escalares |
| `back_work_ratio` | Clave con `wc/wt` | — | escalar |
| `barrido[modelo]["rendimiento"]` | Fracción térmica o NaN fuera del motor | — | `ndarray` |
| `balance`, `balance_optimo`, `energias` | Energías y rendimiento | varias | `dict` |
| `ciclo_ideal`, `ciclo_noideal`, `ciclo_limite_ideal` | Estados y balances | varias | `dict` |
| `rp_optima_analitica`, `rp_optima_numerica` | Relaciones del máximo trabajo | — | escalar |
| `trabajo_maximo` | Trabajo en el óptimo analítico | kJ/kg | escalar |

### Auxiliares numéricas, gráficas y de informe

| Nombre real | Función | Tipo y unidad |
|---|---|---|
| `relaciones` | Malla visual o malla de la API heredada | arrays de rp, adimensionales |
| `trabajos` | Trabajos de la malla numérica | array, kJ/kg |
| `indice_maximo` (heredada), `indice` (actual) | Posición del máximo de una malla inicial | `int`, sin unidad |
| `paso_busqueda` | Alias actual de `resolucion_rp` ideal, no separación de malla | `float`, rp adimensional |
| `optimizaciones`, `estudio_ideal` | Resultados de ambos métodos por modelo | diccionarios (§4.35) |
| `ylo`, `yhi`, `malla`, `paso_inicial` | Ventana y muestras en ln(rp), paso logarítmico | escalares/array adimensionales |
| `registros`, `aceptados` | Evaluaciones locales y puntos motores aceptables | diccionario y lista |
| `B`, `h`, `H`, `S` | Coeficientes de la ecuación estacionaria de rendimiento (§4.38) | escalares adimensionales |
| `estudio_rendimiento` | Estudios ideal/noideal y disponibilidad | dict (§4.38) |
| `comparacion_criterios` | Puntos A/B y diferencias de diseño | dict (§4.39), rp, pp, %, kJ/kg |
| `barrido`, `dominios`, `referencia` | Estudios, límites y puntos de referencia | diccionarios, véase §4.32 |
| `viable`, `motivos`, `fronteras` | Estado y condiciones simultáneas | booleano, tuplas de códigos |
| `margenes`, `tolerancias` | rp−1; p3−p1; qin; wn y banda de cero | diccionarios: —, kPa, kJ/kg, kJ/kg |
| `temperaturas_23`, `temperaturas_41`, `entropias_23`, `entropias_41` | Coordenadas T-s | arrays, K y kJ/(kg·K) |
| `volumenes_12`, `volumenes_34`, `presiones_12`, `presiones_34` | Coordenadas P-v | arrays, m³/kg y kPa |
| `procesos`, `inicio`, `fin` | Coordenadas, etiquetas y flechas | tuplas |
| `figura`, `ejes`, `linea` | Objetos gráficos | `Figure`, `Axes`, `Line2D` |
| `fecha` | Inicio de ejecución, zona local del equipo | `datetime` |
| `version` | Commit base y presencia de cambios al inicio | `dict` con `str`/`None` y `bool`/`None` |
| `PARAMETROS_PREDETERMINADOS` | Nueve entradas predeterminadas del módulo | `dict` |
| `parametros`, `configuracion` | Copia local con sustituciones de la ejecución | `dict` |
| `valores` | Texto del formulario, con pérdida en porcentaje | `dict` |
| `errores` | Mensajes por campo, modelo o servidor | `dict` de cadenas |
| `CAMPOS`, `GRUPOS` | Etiquetas, unidades, ayudas y agrupación | diccionario y tupla |
| `app` | Aplicación Flask; crearla no abre un socket | objeto `Flask` |
| `detalles_ideal` | R, volúmenes, entropías, rendimiento de fórmula e incrementos | `dict`, unidades anteriores |
| `optimo` | `rp_analitica`, `rp_numerica`, `intervalo_busqueda`, `paso`, `trabajo_analitico`, `trabajo_numerico`, `temperaturas`, `rendimiento` | `dict`, unidades anteriores |
| `comprobaciones` | Mensajes de verificaciones superadas | lista de `str` |
| `imagenes` | Nombre → buffer; se pasa a HTML como nombre → bytes | `dict` de `BytesIO` / `bytes` |
| `contenido` | HTML completo en memoria | `str` |
| `carpeta_salida`, `ruta_informe`, `ruta`, `temporal` | Destinos y temporal | `Path` o entrada convertible |
| `MARCA_INICIO`, `MARCA_FINAL` | Marcas de informe propio completo | constantes `str` |
| `PATRON_INFORME` | Nombre reconocido para retención | patrón regular |

Una clave `.png` en `imagenes` no es una ruta de lectura. `getvalue()` obtiene bytes del dibujo nuevo. Base64 es una representación textual de esos bytes, sin unidades físicas.

## 6. Imports y librerías

### Imports del programa

| Import real | Origen | Uso concreto |
|---|---|---|
| `from pathlib import Path` | Estándar | Rutas, carpetas, publicación y retención |
| `from datetime import datetime` | Estándar | Fecha y hora con zona local |
| `from io import BytesIO` | Estándar | PNG en memoria |
| `from math import isclose, isfinite, log` | Estándar | Tolerancias, finitud y entropía escalar |
| `from viabilidad import ...` | Módulo propio | Estados y balances comunes, dominios y clasificación |
| `import numpy as np` | Dependencia existente | Mallas, arrays, máximo y operaciones por elemento |
| `import matplotlib` | Dependencia existente | Selección de Agg |
| `import matplotlib.pyplot as plt` | Matplotlib | Figuras, dibujo, guardado y cierre |
| `from reporting import crear_informe_html, guardar_informe_html, obtener_version_git` | Módulo propio | Presentación separada del cálculo |
| `from base64 import b64encode` | Estándar | PNG binario a Base64 |
| `from html import escape` | Estándar | Proteger textos del HTML |
| `import subprocess` | Estándar | Consultar Git, con salida capturada, control de errores y timeout |
| `import re` | Estándar | Reconocer nombres de informes |
| `from uuid import uuid4` | Estándar | Identificadores que evitan colisiones |
| `from warnings import warn` | Estándar | Advertir de retención incompleta después de guardar |

`Path` aparece en los módulos que gestionan rutas. `as np` y `as plt` son aliases. `import re` deja un módulo y exige `re.compile(...)`; `from html import escape` deja directamente `escape(...)`. Los módulos estándar acompañan a Python; no se instalan con pip.

Se añade Flask a NumPy y Matplotlib. Flask instala sus dependencias necesarias (Werkzeug, Jinja2, MarkupSafe, Click, ItsDangerous y Blinker); no hay frameworks frontend. Una vez instaladas, el servidor y los informes funcionan sin Internet.

El módulo `optimizacion.py` importa `exp`, `log`, `isfinite` y `sqrt` de `math` para el candidato, coordenada logarítmica y sección áurea; `numpy` para malla/argmax y `finfo(float).eps` para describir redondeo. `main` importa `optimizar_trabajo_neto`. No se añade dependencia ni SciPy; el cálculo físico sigue en `viabilidad`.

`optimizacion_rendimiento` añade `expm1` y `log1p` de la biblioteca estándar para coeficientes casi reversibles; no introduce SciPy. La optimización numérica usa NumPy ya instalado.

### Imports de Flask

`from flask import Flask, Response, abort, redirect, render_template, request, url_for` incorpora la aplicación, respuesta HTTP, errores de ruta, redirecciones, renderizado Jinja, petición actual y construcción de URLs. `request` representa la petición activa: se consulta dentro de las rutas, no al importar el módulo.

`web_app.py` importa `main`, sus parámetros predeterminados, `ErrorModelo` y `ErrorNumerico`; también las marcas y patrón de informes de `reporting`. No copia las ecuaciones. En las nuevas pruebas `sys.executable` identifica el intérprete actual y `runpy.run_path` ejecuta el punto de entrada en un proceso aislado de prueba.

### Imports de las pruebas

`unittest` aporta pruebas y aserciones; `unittest.mock.patch` sustituye temporalmente operaciones para simular fallos; `tempfile` aísla archivos; `redirect_stdout` y `StringIO` capturan terminal; `HTMLParser` inspecciona etiquetas; `b64decode` comprueba la codificación; `sha256` compara los PNG históricos; `matplotlib.image` decodifica imágenes. También se importan fechas, zona UTC, rutas y bytes en memoria, y los módulos propios `main` y `reporting`.

Estas herramientas verifican implementación, almacenamiento y rutas HTTP, no datos experimentales del modelo.

## 7. NumPy: uso real

### `np.linspace(inicio, fin, numero)`

Se usa en `construir_barrido`, `buscar_maximo_numerico`, `buscar_optimo_numerico` (API heredada), `guardar_diagrama_ts` y `guardar_diagrama_pv`. Produce muestras uniformes e incluye ambos extremos con los argumentos usados.

```python
np.linspace(2, 6, 3)  # array([2., 4., 6.])
```

El tercer argumento es el **número de puntos**, no el paso. En la búsqueda heredada del óptimo:

```text
paso = (50 - 1.01) / (100001 - 1) = 0.0004899  # sólo API heredada §4.11
```

`np.linspace(T4, T1, 100)` también funciona si el extremo final es menor: genera una secuencia descendente y respeta el recorrido del enfriamiento.

### `np.array(...)`

Se usa en las búsquedas numéricas y en `construir_barrido` para convertir listas en arrays. Fragmento real:

```python
mascara = np.array([p["viable"] for p in puntos], dtype=bool)
```

**PYTHON.** La comprensión extrae un booleano por punto. `dtype=bool` fija el tipo de sus elementos. `valores[mascara]` selecciona los motores y `valores[~mascara]` los excluidos. `~` invierte cada elemento booleano del array; no debe sustituirse por `not mascara`, que no define un único resultado para varios elementos. `np.isnan` permite comprobar los cortes de la curva en las pruebas.

`np.geomspace(1,100,3)` produce aproximadamente [1,10,100]: factor constante, útil para varios órdenes de magnitud. `np.unique` elimina duplicados y ordena las muestras combinadas. `np.asarray` normaliza una secuencia a array; `np.diff` calcula diferencias entre vecinos para exigir orden creciente.

### Indexación y `np.argmax`

`buscar_optimo_numerico` (API heredada):

```python
indice_maximo = int(np.argmax(trabajos))
```

`np.argmax` retorna la posición del primer máximo si hay empate. El índice 0 corresponde al primer elemento. Con ese mismo índice, `relaciones[indice_maximo]` y `trabajos[indice_maximo]` seleccionan un punto de la curva. En la llamada heredada predeterminada el índice es 38937. En `buscar_maximo_numerico` la variable es `indice`, corresponde a 257 muestras logarítmicas y sólo inicia el refinamiento; no es el resultado final. No se utiliza `np.max` en el código.

### Operaciones vectorizadas

En `guardar_diagrama_ts`, la división del array de temperaturas entre `T2`, el logaritmo, la multiplicación por `cp_kj` y la suma con `s2` actúan elemento a elemento:

```python
entropias_23 = s2 + cp_kj * np.log(temperaturas_23 / T2)
```

Ejemplo mínimo de sintaxis:

```python
valores = np.array([2.0, 4.0])
valores / 2  # array([1., 2.])
```

En cambio, una lista Python multiplicada por un entero repite sus elementos. Por eso conviene distinguir una lista de un array aunque ambos puedan contener números. La malla es un array, pero el balance escalar sigue evaluándose mediante un bucle de comprensión.

### `np.log`, `np.full` y `np.allclose`

- `np.log` aplica logaritmo natural a los arrays de T-s, `guardar_diagrama_ts`. `math.log` se utiliza en valores escalares.
- `np.full(200, p2)` crea un array constante para una isóbara, `guardar_diagrama_pv`; análogamente se utiliza `p4` en `guardar_diagrama_pv`.
- `np.allclose` comprueba las cuatro temperaturas del límite reversible, `comprobar_comparacion_ciclos`. Devuelve un único resultado lógico: exige que todos los pares cumplan la tolerancia.

No aparecen matrices multidimensionales, álgebra lineal, integración numérica ni algoritmos de optimización de NumPy. La búsqueda actual evalúa una malla inicial de una dimensión y refina localmente por sección áurea, implementada con Python; sólo la API ideal heredada conserva su barrido exhaustivo de 100001 puntos.

## 8. Matplotlib

### Figuras y ejes

**PYTHON.** `Figure` es el contenedor completo; `Axes` es el área donde se representan coordenadas. Aunque la variable se llame `ejes`, en estas llamadas representa **un solo objeto `Axes`**, porque `plt.subplots(figsize=(9, 6))` no solicita varias filas ni columnas.

```python
figura, ejes = plt.subplots(figsize=(9, 6))
ejes.plot(relaciones, trabajos, label="Trabajo específico neto")
```

`figsize=(9,6)` expresa tamaño en pulgadas. Todas las funciones gráficas usan el estilo explícito de objetos `Figure`/`Axes`. En las curvas de rp, `plot` interrumpe la línea al encontrar NaN: filtrar eliminando esas muestras y unir los puntos restantes podría ocultar una región excluida. Las máscaras de cada modelo se conservan por separado.

### Operaciones que aparecen

| Operación real | Función en el simulador |
|---|---|
| `plt.subplots(...)` | Crea contenedor y área de dibujo juntos |
| `plot(x,y,...)` | Une puntos de curvas y procesos; devuelve una lista de líneas |
| `scatter(x,y,...)` | Marca estados y máximo como puntos |
| `ejes.set_title` | Títulos |
| `ejes.set_xlabel` | Nombre y unidad del eje horizontal |
| `ejes.set_ylabel` | Nombre y unidad del eje vertical |
| `grid(True)` | Cuadrícula |
| `legend(...)` | Leyenda a partir de los `label` de las series |
| `annotate(...)` | Números de estado, texto del máximo o flechas |
| `margins(x=...,y=...)` | Añade espacio proporcional alrededor de los datos |
| `tight_layout()` | Ajusta espacios entre elementos para reducir recortes |
| `savefig(...)` | Escribe la imagen |
| `plt.close(...)` | Cierra y libera el registro de la figura |

`label=` nombra una serie; `legend` dibuja su leyenda en las siete figuras. En rp, `set_xscale("log")` permite ver el entorno de rp=1 y límites de cientos; no cambia las magnitudes. `axvline` señala fronteras visibles y `axvspan` sombrea el intervalo motor. La vista completa alcanza todas las fronteras motoras y añade un 5 % sobre el límite ideal; los paneles de detalle conservan esa vista general.

### Puntos, anotaciones y flechas

`color="black"` selecciona negro, `s=70` fija el área del marcador en puntos cuadrados y `zorder=5` lo coloca por encima de elementos con menor prioridad de dibujo.

En `annotate`, `xy` es la posición señalada. `xytext` indica dónde empieza el texto o flecha; con `textcoords="offset points"`, la posición del texto es un desplazamiento en puntos tipográficos desde `xy`. No son unidades de temperatura o presión. Sin ese ajuste, las flechas de los procesos usan las coordenadas de datos. `arrowprops` contiene estilo, color y anchura `lw`.

```python
linea, = ejes.plot(valores_s, valores_T, label=etiqueta)
```

El resultado de `plot` es una lista con una línea en este caso. La coma en `linea,` pide exactamente un elemento y asigna ese objeto. Así `linea.get_color()` recupera el color de la curva y la flecha coincide con ella.

**INTERPRETACIÓN FÍSICA.** Las flechas muestran el sentido del ciclo. Las isóbaras T-s se curvan por la relación logarítmica; las isentrópicas P-v se curvan por la potencia `gamma`. No se unen indiscriminadamente los cuatro estados con segmentos rectos.

### Guardado y cierre

Las siete gráficas usan 9 × 6 pulgadas y `dpi=150`: 1350 × 900 píxeles. Las pulgadas fijan el tamaño de la figura y dpi los píxeles por pulgada; el tamaño mostrado en pantalla lo adapta el CSS sin reducir los píxeles originales. `savefig(..., format="png")` escribe ahora en buffers `BytesIO`: el flujo normal no crea ni sobrescribe PNG. `plt.close()` cierra la figura actual; `plt.close(figura)` cierra la indicada. Si se entrega explícitamente una ruta a una función gráfica que la admite, todavía se puede guardar un PNG; es un uso opcional distinto de `main()`.

### Qué hace `matplotlib.use("Agg")`

`matplotlib.use("Agg")`, al nivel del módulo, selecciona un backend de renderizado no interactivo antes de importar `pyplot`. `Agg` permite crear PNG sin abrir ventanas y evita depender de una interfaz gráfica basada en Tkinter para este flujo. El comentario del código documenta precisamente esa finalidad.

El repositorio actual no conserva aquí una traza de un fallo anterior; no puede deducirse qué mensaje de error concreto hubo. Lo que sí puede afirmarse es que esta selección resuelve la necesidad de guardar gráficos sin inicializar ventanas ni utilizar Tkinter. No modifica las ecuaciones ni acelera el cálculo del ciclo por sí misma.

## 9. Gestión de archivos, HTML, Base64 e historial

### Rutas y consulta desde VS Code

```python
if carpeta_salida is None:
    carpeta_salida = Path(__file__).resolve().parent / "outputs"
```

**PYTHON.** `None` indica ausencia de una carpeta alternativa; `is None` comprueba identidad. `__file__` identifica el script; `Path` lo representa como ruta; `.resolve()` obtiene su ruta absoluta resuelta; `.parent` obtiene su carpeta. `/ "outputs"` compone una ruta, no divide números. El destino no depende de la carpeta desde la que se lance el script.

`mkdir(parents=True, exist_ok=True)` crea carpetas necesarias y admite que ya existan. Un problema de permisos sigue siendo un error.

En VS Code, ejecuta `python main.py` con el entorno activo. Expande `outputs/` en el explorador: la ruta exacta aparece también en terminal. Puedes abrir el HTML como texto para estudiar sus etiquetas, o usar «Mostrar en el Explorador de archivos» y abrirlo con Chrome/Edge. Para verlo renderizado necesitas navegador o una vista previa HTML instalada; el editor de texto muestra el código. No hace falta servidor, extensión ni Internet para abrirlo en un navegador.

### Interfaz local: navegador → Flask → simulador

Desde el Explorador de Windows, haz doble clic en **`Abrir_Brayton_Simulator.cmd`**, en la raíz del proyecto. Arranca el formulario y abre el navegador predeterminado en `http://127.0.0.1:5000/` cuando responde. Mantén abierta la ventana del servidor; Ctrl+C lo detiene. Si el formulario ya estaba activo, reutiliza esa instancia, abre el navegador y termina el nuevo lanzador; la ventana del servidor original sigue controlándolo.

El lanzador es un archivo de comandos de Windows, sin funciones Python nuevas ni ecuaciones. `%~dp0` obtiene su propia carpeta; `cd /d` cambia también de unidad para que `.venv` y `web_app.py` se resuelvan correctamente aunque lo abras desde otra ubicación. Usa el Python de `.venv` con `-B` para evitar cachés; comprueba Flask/NumPy/Matplotlib antes de iniciar. `start ""` reserva un título vacío y abre la URL o el proceso de espera. PowerShell consulta el formulario mediante GET, comprueba que contiene formulario y el campo de relación de presiones, y sólo entonces abre el navegador; la espera auxiliar se ejecuta oculta y tiene 30 intentos acotados. No envía datos ni genera informes.

Si faltan entorno o dependencias, muestra un mensaje y pausa. Si Flask no arranca, deja visible el error; un puerto 5000 ocupado por otra aplicación debe liberarse antes de reintentar. No instala paquetes ni cambia el puerto o la dirección local. Requiere Windows, PowerShell, navegador predeterminado y las dependencias ya instaladas. Si no se abre el navegador tras arrancar, puedes visitar la URL manualmente. Un servidor ya activo se identifica por su respuesta HTML, no por una comprobación de la versión Git que tiene cargada.

Desde el terminal de VS Code situado en la raíz:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe web_app.py
```

Abre `http://127.0.0.1:5000` en Chrome o Edge. Con el entorno activado bastan `python web_app.py` y, para la modalidad anterior, `python main.py`. Ctrl+C detiene el servidor. Si no está activo, la URL local no responde. Al ejecutar directamente `python web_app.py` no se abre el navegador automáticamente; el lanzador por doble clic sí lo hace. No hay instalación ni despliegue en Internet. La instalación inicial de dependencias sí requiere paquetes disponibles localmente o conexión para descargarlos.

**HTTP GET:** solicita una representación, por ejemplo el formulario o un informe guardado. No ejecuta una simulación al visitar `/`. **HTTP POST:** envía los campos mediante el cuerpo de la petición para ejecutar un caso. Los valores llegan como cadenas, aunque el navegador dibuje controles numéricos.

```text
GET / → valores_formulario → render_template → formulario
POST / → request.form → leer_parametros
                         ├─ errores de campos → formulario + 400
                         └─ números válidos → main(parametros=...)
                                               ├─ ErrorModelo → causas/intervalo y formulario + 400
                                               ├─ ErrorNumerico → límite numérico y formulario + 400
                                               ├─ error inesperado → registro + 500
                                               └─ informe completo → 303 → GET /informes/nombre
```

`float(texto)` convierte un número escrito; `.strip()` quita espacios. `isfinite` rechaza NaN e infinitos antes de evaluar el modelo. `5` en el campo de pérdida significa 5 %, y se convierte en `0.05` una sola vez. Los otros parámetros conservan sus unidades. No se multiplican eficiencias por 100: se introducen como fracciones.

Después del éxito, HTTP 303 indica al navegador que debe consultar por GET el informe recién generado. Así recargar la vista no reenvía el POST ni genera otra simulación. El servidor solo acepta nombres con el patrón del sistema y marcas completas dentro de `outputs/`; no recibe una ruta local libre del usuario. Si la retención ya eliminó ese informe, devuelve 404.

La vista añade «Volver al formulario» y «Descargar informe HTML». La descarga y el archivo original no contienen esos enlaces al servidor: siguen funcionando sin conexión ni servidor. «Restablecer valores» es un enlace GET que carga los valores predeterminados; un botón HTML `reset` restauraría los valores iniciales de la página actual, que podrían ser datos inválidos reenviados, por eso aquí se utiliza un enlace.

El servidor se enlaza exclusivamente a `127.0.0.1`. Con `debug=False` no se ofrece depurador interactivo; `use_reloader=False` evita procesos de recarga y `threaded=False` procesa una petición cada vez. Durante una simulación otras peticiones esperan. No es una cola de trabajos ni un servidor de producción. Una ejecución de terminal en otro proceso aún puede coincidir con Flask: no se añade bloqueo entre procesos en esta tarea.

### Plantilla Jinja, campos HTML y CSS

`templates/index.html` es una plantilla, no un informe. Flask/Jinja sustituye `{{ valores.get(nombre, '') }}` por texto escapado; `{% for ... %}`, `{% if ... %}` y `{% set ... %}` controlan repetición, condiciones y asignación en la plantilla. Estas expresiones no se ejecutan en el navegador: Python renderiza el resultado antes de enviarlo. No deben confundirse con las llaves de las f-strings ni de CSS.

`<form method="post" action="...">` define destino y método; el atributo `name` de cada `<input>` será la clave de `request.form`. `label for` y `id` enlazan etiqueta y campo. `type="number"`, `step="any"`, `required`, `min` y `max` ayudan en el navegador, pero no sustituyen el servidor; límites estrictos como mayor que cero o pérdida menor que 100 se comprueban en Python. Los mensajes muestran además el valor recibido para conservar información incluso si un control numérico no puede representar texto inválido.

`fieldset` y `legend` agrupan los tres bloques. `aria-describedby`, `aria-invalid` y `role="alert"` relacionan ayudas y errores para accesibilidad. El CSS local usa una cuadrícula de dos columnas, que pasa a una en pantallas estrechas. `url_for('static', filename='style.css')` construye la URL del CSS; este recurso sirve solo al formulario. El informe no depende de él.

### Qué es HTML y cómo lo genera Python

HTML estructura texto con etiquetas: `<h2>` es título; `<table>`, tabla; `<tr>`, fila; `<th>`, cabecera; `<td>`, celda; `<img>`, imagen. CSS define presentación. Todo el CSS va en `<style>`; no hay frameworks, fuentes descargadas ni JavaScript.

`crear_informe_html` retorna una f-string multilínea. Python sustituye expresiones `{...}` por texto formateado. Las reglas CSS requieren escribir `{{` y `}}` para producir llaves literales. `html.escape` convierte caracteres como `<` y `&` a entidades para no interpretar datos como etiquetas. `"".join(...)` une fragmentos de tablas sin separador.

### De Matplotlib al PNG incorporado

```python
buffer = BytesIO()
# La función gráfica escribe con savefig(buffer, format="png").
png = buffer.getvalue()
contenido = b64encode(png).decode("ascii")
```

`BytesIO` es un archivo binario en memoria. Matplotlib escribe el PNG allí y `getvalue()` recupera los bytes. `b64encode` produce bytes de caracteres Base64; `.decode("ascii")` los convierte a `str` para el HTML. Esto cambia la representación binaria a texto, no las ecuaciones ni los píxeles.

```html
<img src="data:image/png;base64,..." alt="Diagrama T-s ideal">
```

`data:` indica contenido dentro de la propia URL; `image/png`, el formato; `base64`, la codificación. Los puntos suspensivos de este ejemplo se sustituyen por todos los datos en el HTML real. Base64 aumenta el tamaño aproximadamente un tercio. No es cifrado ni compresión; permite trasladar un único archivo sin siete PNG externos.

**INTERPRETACIÓN FÍSICA.** Los dibujos proceden de estados y arrays de esa ejecución, nunca de los PNG históricos. El formato no añade fidelidad física.

### Publicar antes de limpiar

1. Terminan cálculos, comprobaciones y siete gráficas; todo el HTML se construye en memoria.
2. Se verifican marcas de documento completo y se crea la carpeta si hace falta.
3. El nombre incorpora fecha/hora, seis cifras de microsegundos y `uuid4().hex`. UUID no es una versión física del modelo.
4. Se abre un temporal oculto `.html.tmp` con `"x"`: falla si existe. El bloque que lo retira comienza solo tras crearlo; nunca debe borrar un temporal ajeno si esa apertura falla.
5. `with archivo:` garantiza el cierre. Tras escribir y cerrar se renombra como `.html`, comprobando que no exista el destino. En Windows `rename` también rechaza destinos existentes.
6. `finally` intenta retirar el temporal propio si queda. Un cierre abrupto del proceso podría dejar un `.tmp`, pero no un HTML parcial con nombre final.
7. Solo tras publicar comienza la retención del historial.

La implementación está dirigida a Windows. No se usa `replace`, que reemplazaría destinos. Si se porta a otros sistemas, debe revisarse la semántica de colisión de `rename`.

`fecha.strftime("%Y-%m-%d_%H-%M-%S-%f")` convierte fecha a texto: `%Y` año, `%m` mes, `%d` día, `%H` hora, `%M` minuto, `%S` segundo y `%f` microsegundos. La cabecera añade `%z` para el desfase horario. `.astimezone()` incorpora la zona local del equipo. `uuid4()` crea el identificador; `.hex` es su atributo textual de 32 caracteres hexadecimales, sin paréntesis.

### Identificación Git del informe

La cabecera muestra el hash completo de `HEAD`, capturado al iniciar `main`. Es el commit base del código. Se consultan cambios preparados, sin preparar y archivos sin seguimiento; los archivos ignorados por Git, como `outputs/`, no activan el aviso.

`subprocess.run` ejecuta Git mediante una lista de argumentos, sin construir una cadena de shell. `capture_output=True` recoge salida y error; `text=True` entrega texto; `check=True` convierte un código de salida no cero en excepción; `timeout=5` limita cada consulta. `.stdout.strip()` retira saltos/espacios exteriores; `bool(texto)` es verdadero si el estado contiene líneas. `git -C` permite consultar el repositorio del script aunque se ejecute desde otra carpeta.

`elif` comprueba el segundo caso solo si el primer `if` no se cumple. El HTML distingue `modificado is True`, `is False` y desconocido (`None`). Un estado limpio declara que Git no detecta cambios. Un estado modificado avisa de que el hash identifica la base y no reproduce exactamente esos resultados: para reconstruir el código local haría falta conservar también los cambios. Si Git no existe, no hay commit o falla la consulta, el informe sigue funcionando con «No disponible» y un aviso de estado desconocido.

**INTERPRETACIÓN FÍSICA.** El commit facilita comparar versiones de implementación, no certifica las hipótesis físicas ni equivale a validación experimental. El estado es una observación al inicio, no un bloqueo frente a ediciones simultáneas del código.

### Cómo se conservan cuatro informes

Un candidato debe cumplir nombre completo con fecha/microsegundos/UUID, ser archivo regular sin enlace simbólico y tener ambas marcas de informe propio completo. Un HTML cualquiera no se elimina; tampoco nombres parecidos sin marcas, archivos no UTF-8, temporales o PNG.

`re.compile(...)` prepara el patrón. El prefijo `r"..."` conserva las barras invertidas para la expresión regular; `\d{4}` significa cuatro dígitos, `[0-9a-f]{32}` significa 32 caracteres hexadecimales y `\.` representa un punto literal. `PATRON_INFORME.fullmatch(nombre)` exige coincidencia completa. `carpeta.iterdir()` recorre entradas; `.name` es solo el nombre; `.is_file()` y `.is_symlink()` distinguen el tipo. `read_text(encoding="utf-8")` lee el contenido para comprobar las marcas. Las marcas son comentarios HTML invisibles para el lector. Son identificadores de formato, no firmas criptográficas: un archivo que imite deliberadamente nombre y marcas sería indistinguible de un informe propio.

Se ordena por `st_mtime_ns`, fecha de modificación correspondiente al final de escritura, y nombre como desempate. `reverse=True` coloca los recientes primero; `[4:]` selecciona desde el quinto; `unlink()` los elimina. Editar manualmente un informe puede cambiar su posición al modificar su fecha.

Si falla cálculo, dibujo, HTML o publicación, no se ejecuta la retención. Si falla limpieza después de publicar, se advierte y el informe nuevo sigue siendo válido; pueden quedar más de cuatro. No hay una transacción que deshaga eliminaciones ya realizadas si el sistema falla durante la limpieza.

Los nombres evitan colisiones entre ejecuciones próximas. No se introduce bloqueo multiproceso: se han verificado cinco ejecuciones secuenciales, no una transacción de retención concurrente. Los PNG históricos se conservan intactos.

## 10. Manejo de errores y validaciones

### `raise ValueError(...)`

**PYTHON.** `raise ValueError("mensaje")` construye y lanza una excepción. El llamador se interrumpe salvo que capture ese tipo. `main` captura `ValueError` sólo durante `validar_parametros` y la revisión explícita de rp; no envuelve cualquier fallo de cálculo como si fuera un dato físico incorrecto. Las API estrictas de ciclo conservan rechazo por excepción. La consulta `evaluar_punto` devuelve normalmente los puntos inviables con sus motivos.

### Entradas del formulario frente a errores del programa

1. Campos vacíos, texto, NaN/infinito y rangos individuales inválidos: mensajes por campo, HTTP 400; no se llama al simulador.
2. Combinación no motora en la referencia: `ErrorModelo`, HTTP 400 con TODOS los motivos y límites disponibles; no se genera informe ni se toca el historial. Se exige referencia motora en ambos modelos para poder conservar los diagramas y tablas comparativas.
3. Parámetros admisibles pero operación no representable: `ErrorNumerico`, HTTP 400 con aviso numérico distinto de una conclusión física. Se conservan las entradas y el historial.
4. Fallo inesperado en ecuaciones, diccionarios, gráficos, HTML o disco: se propaga; Flask registra traceback y muestra HTTP 500 genérico sin detalles privados.

Los barridos mezclan puntos motores e inviables sin lanzar `ErrorModelo` por estos últimos. No se usa un `except ValueError` genérico en su recorrido. T3=800 K y rp=10 es ahora un ejemplo aceptado: no debe rechazarse porque el antiguo intervalo fijo contuviera otros puntos fuera del motor. Si falla una fórmula o un contrato, se debe corregir el error, no saltar el punto silenciosamente.

`finally` cierra figuras y buffers; la publicación sigue precediendo a la retención. Un fallo de limpieza posterior conserva su semántica de advertencia. Los tipos incompatibles de una llamada Python manual aún pueden producir `TypeError`: no hay un validador exhaustivo de tipos.

### `isfinite`, `all` y cortocircuito

```python
if not all(isfinite(T) and T > 0 for T in (T1, T3)):
```

Para cada temperatura, se exige que sea finita **y** positiva. `all` devuelve verdadero si todos los resultados son verdaderos. Se detiene al encontrar uno falso. El generador no necesita construir primero una lista.

`and` evalúa su segundo operando solo si el primero permite continuar; `or` se detiene cuando ya tiene una condición verdadera. En la comprobación de entropías de `guardar_diagrama_ts`, si la longitud no es cuatro, el `or` evita evaluar la comparación elemento a elemento.

### `isclose` y `np.allclose`

Los flotantes representan aproximaciones binarias; dos expresiones algebraicamente equivalentes pueden diferir ligeramente. Para números finitos, `math.isclose(a,b)` comprueba:

```text
|a-b| <= max(rel_tol * max(|a|, |b|), abs_tol)
```

`rel_tol=1e-9` es una tolerancia proporcional al tamaño del valor; `abs_tol=1e-12` da un margen absoluto útil cerca de cero. Las unidades de `abs_tol` son las de la magnitud comparada. No es una incertidumbre experimental del modelo: es un criterio de coherencia numérica.

`np.allclose(a,b,rtol=...,atol=...)` comprueba elemento a elemento con el criterio aproximado `|a-b| <= atol + rtol*|b|` y exige que todos pasen. No tiene exactamente la misma fórmula simétrica de `math.isclose`.

En algunas verificaciones P-v solo se especifica `rel_tol`: allí sigue vigente el valor por defecto de `abs_tol`, que es cero. En el contraste actual de máximos se comparan diferencias absolutas con escalas explícitas de rp y energía (§14); el criterio de un paso sólo describe la búsqueda heredada. El redondeo de pantalla se hace después; no se comparan cadenas con dos decimales.

### Cuatro situaciones diferentes

| Categoría | Ejemplo relacionado con el código | Qué significa |
|---|---|---|
| Error de programación | Consultar `balance["trabajo"]` cuando la clave real es `"trabajo_neto"` | El contrato del código se ha usado mal; puede dar `KeyError` |
| Entrada inválida | `eta_c=0`, `gamma=1`, `p1=-100` | El modelo no admite ese dato; se lanza `ValueError` |
| Inviabilidad física esperada | Temperaturas positivas pero `wt<=wc` | `evaluar_punto` devuelve motivos; el caso de referencia se rechaza con mensaje y el barrido continúa clasificado |
| Error/efecto numérico | Pequeña diferencia entre dos rendimientos, o desbordamiento para potencias extremas | La representación tiene límites; las tolerancias cubren diferencias pequeñas, no desbordamientos arbitrarios |

Un trabajo negativo no es imposible en toda la termodinámica: significa que ese conjunto no corresponde al ciclo motor que este programa acepta. Tampoco una excepción garantiza que el usuario se haya equivocado: puede revelar un error en una ecuación, un dato incoherente o un contrato mal utilizado.

Las comprobaciones de ejecución no demuestran todos los casos posibles. Existen `tests/test_reporting.py`, `tests/test_web_app.py` y `tests/test_viabilidad.py`, ejecutables mediante `python -B -m unittest discover -s tests -v`.

Verifican referencias numéricas, cinco simulaciones que dejan cuatro informes propios, siete PNG decodificables e idénticos a los bytes de la ejecución, ausencia de recursos externos, archivos ajenos y PNG históricos intactos, fallo de cálculo/publicación, colisiones de HTML/temporal, escape HTML, cambio gráfico con gamma, dimensiones exactas de las siete imágenes y metadatos Git limpios, modificados o desconocidos. Se usan carpetas temporales para no consumir el historial de `outputs/`.

`assertAlmostEqual` contrasta números; `assertEqual` compara contenido; `assertRaises` exige un error esperado; `patch` sustituye una operación temporalmente y la restaura. `TemporaryDirectory` crea y retira los archivos de prueba. Si Windows restringe su carpeta temporal, hay que resolver los permisos del entorno para ejecutar las pruebas; no es un fallo termodinámico.

## 11. Sintaxis de Python que deberías dominar

### Básicos

| Concepto | Qué estudiar | Dónde |
|---|---|---|
| Variables, enteros, flotantes, `=` | Nombres, valores y aproximaciones | Parámetros y balances |
| Operadores `+ - * / **` | Aritmética, potencia y precedencia | Ecuaciones |
| Comparaciones `==`, `<`, `<=`, `>` | Distinguir comparar de asignar | Validaciones y entrada |
| `if`, `elif`, `else`, `and`, `or`, `not` | Control y cortocircuito | Cálculos y retención |
| `def`, argumentos, valores por defecto, `return` | Contratos y llamadas | Funciones |
| `for ... in ...` | Iteración | Tablas, curvas y validaciones |
| Cadenas, comentarios, f-strings | Formato `.2f`/`.6f`, saltos y texto | HTML y gráficos |
| Listas, tuplas, diccionarios e índices | Agrupar y seleccionar datos | Estados y balances |

### Intermedios

| Concepto real | Significado | Dónde |
|---|---|---|
| `*temperaturas`, `**balance` | Desempaquetado, distinto de potencia | Funciones de ciclo |
| Comprensiones y generadores | Construir/recorrer sin duplicar lógica | Arrays, buffers y tablas |
| `all`, `sorted`, `.sort`, `zip`, `enumerate` | Comprobar, ordenar, emparejar y numerar | Validaciones y resultados |
| `[4:]` | Slice desde el quinto elemento | Retención |
| `lambda archivo: ...` | Función breve que calcula clave de ordenación | Informes por fecha y nombre |
| `None`, `is None`, `is True`, `is False`, `is not False` | Ausencia, identidad y estado desconocido | Carpeta y metadatos Git |
| `try`, `finally` | Ejecutar limpieza con éxito o error | Buffers, figuras, temporal |
| `except (...) as error` | Capturar tipos concretos y nombrar excepción | Retención y lectura |
| `with` | Cerrar recursos al abandonar bloque | HTML y pruebas |
| Módulos, aliases, `__name__` | Separar y controlar ejecución al importar | Inicio y final de `main.py` |
| `bytes`, `.decode("ascii")` | Datos binarios frente a texto | Base64 |
| `.getvalue()`, `.items()`, `.join()` | Obtener bytes, recorrer parejas y unir texto | Generación del informe |
| `mkdir`, `open("x")`, `rename`, `unlink` | Crear, publicar y eliminar archivos concretos | Almacenamiento |
| Regex, `compile`, `fullmatch` | Reconocer formato completo | Nombres de informe |
| Arrays y vectorización | Operaciones por elemento e índice máximo | NumPy |
| Decoradores `@app.route`, `@app.errorhandler` | Registrar funciones que Flask llamará después | `web_app.py` |
| `.copy()`, `.update()` | Configuración nueva por ejecución | `main` y valores del formulario |
| `continue` | Saltar al campo siguiente tras detectar un error | `leer_parametros` |
| `except ErrorModelo`, `except ErrorNumerico`, `raise ... from error` | Captura específica y causa original conservada | Flask y coordinación |
| `.to_dict()`, `.get()` | Conservar texto y consultar campos con defecto | Petición y plantilla |
| Tupla `(html, estado)` | Cuerpo y código HTTP para Flask | Formulario/error |
| `try/except/else` | Redirigir solo cuando la llamada fue satisfactoria | `index` |

### Conceptos que aún no necesitas dominar profundamente

- Backend Agg, internals de arrays y renderizado de Matplotlib.
- Precisión binaria: entender tolerancias sin implementar la aritmética.
- UUID: entender su finalidad sin programar su generación.
- Herencia de clases de prueba: `class InformeParser(HTMLParser)` redefine un método; `class InformesTests(unittest.TestCase)` agrupa pruebas. `self` es la instancia y `super().__init__()` inicializa la parte heredada. El cálculo físico no introduce clases propias.
- Callbacks del parser: `feed` invoca `handle_starttag` al encontrar una etiqueta. `patch` cambia una operación durante el contexto de prueba, sin editar el modelo.

En el código de producción no hay `while`, división entera `//` ni parámetros declarados como `*args`/`**kwargs`. Los helpers de pruebas sí usan `**cambios` y `*args, **kwargs`: recogen argumentos posicionales en tupla y nombrados en diccionario para reenviarlos a una función original. `in` también comprueba pertenencia de códigos de motivos.

## 12. Flujo completo de una ejecución

1. Ejecutas `python main.py`. Se importan biblioteca estándar, `reporting`, `viabilidad`, `optimizacion`, `optimizacion_rendimiento`, NumPy y Matplotlib. Agg se selecciona antes de `pyplot`.
2. Python crea funciones con `def`, sin ejecutar sus cuerpos. Cargar `reporting` tampoco guarda archivos.
3. `if __name__ == "__main__":` llama a `main()` al ejecutar el script. Con `import main` no se cumple: no empieza una simulación.
4. `main` captura fecha y zona del equipo con `datetime.now().astimezone()`. Esa fecha identifica el inicio de ejecución. Consulta también el commit y estado local de Git. Copia `PARAMETROS_PREDETERMINADOS`, valida las claves y aplica el diccionario opcional de entrada; después asigna los nombres físicos locales.
5. Valida parámetros, calcula los dominios físicos y evalúa la referencia en ambos modelos. Si no es motora, se detiene antes de publicar. Optimiza trabajo en ambos modelos, estudia el supremo ideal y el máximo de rendimiento no ideal, y compara A/B; después construye una malla adaptada que incluye referencia y todos los máximos disponibles y clasifica todos los puntos y verifica la comparación donde ambos son motores. Después calcula rendimiento, temperaturas, balance, entropías, R, presiones y volúmenes ideales. `T2≈556.33 K`, `T4≈828.72 K`, `wn≈505.619018 kJ/kg`.
6. Valida estados y balances; registra mensajes de los grupos de comprobaciones que han terminado. Compara rendimiento de fórmula y balance sin redondear.
7. Recupera los dos estudios ya calculados antes del barrido: máximo ideal analítico `rp≈20.0852562921`, numérico `20.0852560217`; no ideal analítico `12.8950516696`, numérico `12.8950517350`.
8. Cada estudio verifica interior motor y concordancia con tolerancias separadas para rp y trabajo (§14). El ideal tiene `T2=T4≈678.999264 K`, `wn≈532.802230 kJ/kg`; el no ideal `wn≈373.210827 kJ/kg` y rendimiento en ese punto `39.212614 %`.
9. Calcula diccionarios ideal, no ideal y límite reversible. Contrasta tendencias con pérdidas y recuperación del ideal con eficiencias unidad y pérdida cero.
10. Crea cuatro buffers `BytesIO` y dibuja rendimiento, T-s, P-v y trabajo exclusivamente ideales.
11. Las dos gráficas comparativas reutilizan el barrido ya clasificado, con NaN en puntos excluidos, bandas, fronteras y marcadores de trabajo y de máximo rendimiento no ideal B cuando existe; pueden añadir paneles de detalle dentro de las mismas imágenes. Añaden dos buffers; `guardar_grafica_compromiso` escribe el séptimo con W frente a eta no ideal. Se registra la comprobación del estudio.
12. Reúne `detalles_ideal` y `optimo`. Una comprensión sobre `.items()` obtiene bytes de las siete imágenes. Calcula la tabla de cinco rendimientos; un punto no motor se muestra con `None` como «Fuera del dominio motor».
13. `crear_informe_html` forma tablas, convierte PNG a Base64 y retorna HTML con CSS, secciones de dominio físicamente viable y optimización del trabajo específico neto y del rendimiento térmico, comparación A/B, commit, aviso de estado Git y marcas completas. No se ha publicado todavía ningún informe.
14. `finally` cierra buffers y figuras también si falla dibujo/HTML. El texto generado ya contiene los bytes codificados y no necesita mantener abiertos los buffers.
15. Elige `outputs/` junto al script, o la carpeta alternativa de pruebas. El guardado crea la carpeta si hace falta.
16. Escribe UTF-8 en un temporal abierto con `"x"`; tras cerrarlo lo renombra a HTML final. Si falla esta etapa, propaga el error sin limpiar el historial.
17. Filtra informes propios completos, ordena por fecha de finalización de escritura y elimina los que exceden cuatro. Archivos ajenos y PNG quedan fuera. Una limpieza fallida después de publicar produce advertencia.
18. Muestra tres líneas: ejecución completada, ruta absoluta y siete gráficas incorporadas. Devuelve la ruta y termina; las tablas se consultan en el HTML.

**Memoria.** Cada ejecución copia la configuración predeterminada; no conserva parámetros de otra petición en variables físicas globales. Cada llamada tiene nombres locales. Listas y diccionarios conservan referencias, no copias profundas automáticas. Los arrays de búsqueda viven durante `main`; no se exportan como CSV/JSON. El HTML permanente contiene valores formateados y dibujos. Importar el módulo no ejecuta esta secuencia.

### Si se ejecuta `python web_app.py`

1. Importa Flask, `main` y `reporting`. Se construye `app` y se registran rutas mediante decoradores; todavía no hay simulación.
2. El punto de entrada llama a `iniciar_servidor`, que escucha solo en loopback y permanece activo.
3. Un GET a `/` carga los valores predeterminados en porcentaje para el formulario y renderiza la plantilla.
4. Un POST llama a `leer_parametros`; si no hay errores, llama a `main` con el diccionario convertido y la carpeta compartida.
5. `main` sigue el flujo numérico y gráfico anterior. Cada llamada copia la configuración; no modifica los valores de otra petición.
6. La ruta redirige al informe nuevo con 303. Un GET devuelve la copia de visualización con enlaces locales; la descarga devuelve el original autocontenido.
7. El servidor sigue esperando peticiones. Puedes volver al formulario y generar otro caso sin reiniciarlo. Los errores esperados devuelven 400 y los internos 500; el proceso continúa.

## 13. Seguimiento de un cálculo concreto: trabajo neto

### Camino del caso ideal de referencia

**INTERPRETACIÓN FÍSICA.** Con `rp=10` y `gamma=1.4`, se define `a=(gamma−1)/gamma≈0.285714286` para explicar la ecuación. `viabilidad.py` almacena el exponente en `a`.

```text
Parámetros de `main`
        ↓
calcular_temperaturas(T1, T3, gamma, relacion_presiones)
        ↓
(288.15, 556.3305505777084, 1600, 828.7159486769939)
        ↓
calcular_balance_energetico(T1, T2, T3, T4, cp)
        ↓
diccionario balance["trabajo_neto"]
        ↓
tabla HTML con seis decimales: 505.619018 kJ/kg
```

1. `factor=10**(0.4/1.4)≈1.930697729`.
2. `T2=288.15*factor≈556.330550578 K`.
3. `T4=1600/factor≈828.715948677 K`.
4. `wc=1005*(556.330550578−288.15)/1000≈269.521453331 kJ/kg`.
5. `wt=1005*(1600−828.715948677)/1000≈775.140471580 kJ/kg`.
6. `wn=wt−wc≈505.619018249 kJ/kg`.
7. `qin=1005*(1600−556.330550578)/1000≈1048.887796669 kJ/kg`.
8. `η=wn/qin≈0.482052532077`, presentado en las tablas principales como `48.205253 %`.

**PYTHON.** `wc`, `wt`, `wn`, `qin` y `η` son abreviaturas de esta explicación. En `calcular_energias` los nombres locales son `wc`, `wt` y las claves del diccionario `trabajo_compresor`, `trabajo_turbina`, `trabajo_neto`, `calor_aportado`; `calcular_balance_energetico` añade `rendimiento_balance`. Se construye un diccionario y se devuelve. `crear_informe_html` selecciona `"trabajo_neto"` del ciclo y usa `:.6f` en la tabla. El cálculo conserva su precisión; solo cambia el texto presentado.

### El mismo resultado en otros caminos

En `calcular_trabajo_neto`, las temperaturas se guardan como una tupla local y se pasan mediante `*temperaturas`. El resultado del balance se indexa directamente y solo se devuelve el trabajo. Ese camino se repite en la búsqueda numérica.

En `calcular_ciclo_ideal`, las temperaturas y el balance se agrupan con presiones en otro diccionario. Por eso `ciclo_ideal["trabajo_neto"]` contiene el mismo valor que `balance["trabajo_neto"]` para el mismo caso, aunque los cálculos se hayan repetido.

### Comparación con el no ideal

La función `calcular_ciclo_noideal` utiliza `T2s≈556.330551 K`, pero con `eta_c=0.85` obtiene `T2≈603.656530 K`. La pérdida de presión deja `p3=950 kPa`, frente a `p4=100 kPa`, de modo que `T4s≈840.950399 K`. Con `eta_t=0.90`, `T4≈916.855359 K`.

`evaluar_punto` utiliza `calcular_energias` con esas temperaturas y devuelve `wc≈317.084063`, `wt≈686.560364`, `wn≈369.476301 kJ/kg`. No se aplica simplemente un factor al trabajo ideal: se reconstruyen los estados, los dos trabajos y el calor aportado. El rendimiento real resulta `36.898732 %`.

## 14. Relación entre código y ecuaciones

Notación de esta tabla: `rp=p2/p1`, `a=(gamma−1)/gamma`, `δ=perdida_presion_combustor`. `a` es variable local de `viabilidad.py`; `delta` es su argumento de pérdida, llamado `perdida_presion_combustor` en la interfaz de `main`.

| Concepto físico | Ecuación | Función Python |
|---|---|---|
| Rendimiento ideal | `η=1−rp^(−a)` | `calcular_rendimiento` |
| Compresión ideal | `T2=T1·rp^a` | `calcular_estados`, utilizado por `calcular_temperaturas` |
| Expansión ideal | `T4=T3/rp^a` | `calcular_estados`, utilizado por `calcular_temperaturas` |
| Trabajo consumido por compresor | `wc=cp(T2−T1)/1000` | `calcular_energias`; API estricta `calcular_balance_energetico` |
| Trabajo producido por turbina | `wt=cp(T3−T4)/1000` | `calcular_energias`; API estricta `calcular_balance_energetico` |
| Trabajo específico neto | `wn=wt−wc` | `calcular_energias`, API estricta y `calcular_trabajo_neto` |
| Calor específico aportado | `qin=cp(T3−T2)/1000` | `calcular_energias`; API estricta `calcular_balance_energetico` |
| Rendimiento por balance | `η=wn/qin` sólo motor | `evaluar_punto` y API estricta `calcular_balance_energetico` |
| Fracción de trabajo para compresor | `BWR=wc/wt` | `calcular_ciclo_ideal`, `evaluar_punto` (sólo motor) |
| Eficiencia de compresor | `eta_c=(T2s−T1)/(T2−T1)` | Despejada para `T2` en `calcular_estados` |
| Presión tras el combustor | `p3=p1·rp·(1−δ)` | `calcular_estados`, utilizado por `calcular_ciclo_noideal` |
| Referencia isentrópica de turbina real | `T4s=T3(p4/p3)^a` | `calcular_estados`, utilizado por `calcular_ciclo_noideal` |
| Eficiencia de turbina | `eta_t=(T3−T4)/(T3−T4s)` | Despejada para `T4` en `calcular_estados` |
| Entropía en isóbara ideal | `Δs=(cp/1000) ln(Tfinal/Tinicial)` | `calcular_entropias`, `guardar_diagrama_ts` |
| Entropías isentrópicas | `s2=s1`, `s4=s3` | `calcular_entropias` |
| Constante específica | `R=cp−cv=cp(1−1/gamma)` | `calcular_estados_pv` |
| Gas ideal y volumen específico | `v=RT/(1000p)` con `p` en kPa | `calcular_estados_pv`, verificación en `comprobar_estados_pv` |
| Isentrópica en P-v | `p·v^gamma=constante` | `comprobar_estados_pv`, `guardar_diagrama_pv` |
| Curva P-v isentrópica | `p(v)=p_inicio(v_inicio/v)^gamma` | `guardar_diagrama_pv` |
| Máximo de trabajo ideal | `rp_opt=(T3/T1)^[gamma/(2(gamma−1))]` | `calcular_relacion_optima` |
| Máximo discreto | `i=argmax(wn(rp_i))` | `buscar_optimo_numerico` |

El calor rechazado podría deducirse físicamente de los estados, pero **el programa no devuelve una variable `calor_rechazado`** ni lo imprime. Tampoco calcula potencia: necesitaría caudal másico. No conviene atribuir esas salidas al balance existente.

Con `cp` y `gamma` constantes, la identidad del rendimiento ideal se obtiene sustituyendo temperaturas en el balance. Si `x=rp^a`, entonces `T2=T1*x`, `T4=T3/x`, y `wt−wc=(1−1/x)*cp*(T3−T1*x)/1000`. Dividiendo entre `qin=cp*(T3−T1*x)/1000`, queda `η=1−1/x`, siempre que el denominador sea positivo. Así se entiende por qué deben coincidir las dos rutas del código.

**Precaución de ingeniería con P-v.** En un ciclo cerrado reversible, el área `∮p dv` corresponde al trabajo del ciclo. El simulador calcula los trabajos de compresor y turbina con balances de entalpía de flujo estacionario. No debe sustituirse el trabajo individual de uno de esos equipos por el área de su tramo `∫p dv` sin distinguir trabajo de frontera y trabajo de eje. La figura representa estados y procesos; el código no integra su área.

### Dominio motor ideal: derivación y fronteras

**INTERPRETACIÓN FÍSICA.** Sea x=rp^a y theta=T3/T1>1. Con rp>1, x>1. El calor es positivo si T3>T1*x, es decir x<theta. El trabajo ideal factoriza como:

```text
wn = (cp/1000) * (1−1/x) * (T3−T1*x)
```

Los dos factores son positivos exactamente para 1<x<theta. Por tanto:

```text
1 < rp < theta**(gamma/(gamma−1))
```

En rp=1 no hay compresión, expansión ni trabajo. En la frontera superior qin=wn=0; el cociente de balance sería 0/0. Prolongar la fórmula ideal de rendimiento hasta allí o más allá sin clasificar estados daría una interpretación motora falsa. El máximo de trabajo está DENTRO: rp_opt=sqrt(rp_limite), no en la frontera.

### Dominio motor no ideal: prueba del intervalo o vacío

**INTERPRETACIÓN FÍSICA.** Define a=(gamma−1)/gamma>0, theta=T3/T1, x=rp^a, k=(1−delta)^(−a)>=1 y h=theta*eta_c*eta_t>0. Las condiciones independientes son:

```text
Compresión:  rp > 1
Expansión:   rp > 1/(1−delta)               ⇔ x > k
Calor:       rp < [1+eta_c*(theta−1)]**(1/a)
Trabajo:     (1000/cp)*wn = eta_t*T3*(1−k/x)−T1*(x−1)/eta_c
```

Multiplica la última expresión por eta_c*x/T1, que es POSITIVO. No cambia el signo y se obtiene:

```text
wn > 0 ⇔ Q(x) = x²−(1+h)*x+h*k < 0
Q(x) = (x−1)*(x−h)+h*(k−1)
D = (h−1)²−4*h*(k−1)
x_± = [1+h ± sqrt(D)]/2, si D>0
```

La segunda forma de Q y D reduce cancelaciones con pérdidas pequeñas. Una cuadrática con coeficiente principal positivo es negativa sólo ENTRE dos raíces reales distintas: D<=0 implica ausencia de interior con wn>0; D=0 sólo permite un cero tangente. Si h<=1, para x>=k>=1 todos los factores de la segunda forma son no negativos: no existe motor, incluso si hay dos raíces menores o iguales a 1. Si D>0, la transformación x→rp=x^(1/a) es creciente; la intersección con compresión, expansión y calor positivos es un intervalo ABIERTO o vacío. Esta prueba corresponde a las ecuaciones de este modelo; no se presupone que valga con propiedades variables o mapas de componentes.

El código usa el vértice `centro=(1+h)/2` como punto interior negativo y las cotas Q(0)=Q(1+h)=hk>0 para acotar ambas raíces mediante bisección. El vértice sólo acota raíces de Q; no se usa como óptimo de trabajo no ideal. La fórmula de x_± permite un contraste analítico independiente. El criterio de parada es relativo en x (1e−12) y tiene 100 iteraciones como máximo. Las fronteras de rp se obtienen elevando x a 1/a. Si las escalas dejan de ser representables, se informa de límite numérico y no de ausencia física de motor.

Con eta_c=eta_t=1 y delta=0, k=1, h=theta y Q=(x−1)(x−theta): se recuperan exactamente las condiciones ideales, salvo redondeo y la banda de clasificación.

### Tolerancias y ejemplos numéricos de Fase 1

**PYTHON / NUMÉRICA.** `evaluar_punto` compara un margen con una tolerancia en SU unidad. Un margen debe superar la banda positiva para ser interior motor. La frontera se reconoce por `abs(margen)<=tolerancia`. No se redondean primero las magnitudes:

| Condición | Margen | Tolerancia absoluta usada |
|---|---|---|
| Compresión | rp−1 [—] | 1e−10*max(rp,1) |
| Expansión | p3−p1 [kPa] | 1e−10*max(p3,p1) |
| Calor | qin [kJ/kg] | 1e−10*escala |
| Trabajo | wn [kJ/kg] | 1e−10*escala |

`escala=max(abs(wc),abs(wt),(cp/1000)*max(T1,T3))`, en kJ/kg, evita comparar un residuo cercano a cero con una tolerancia también nula. Para la referencia la tolerancia energética es aproximadamente 1.608e−7 kJ/kg. El modelo matemático conserva fronteras abiertas; la clasificación computacional excluye además una banda diminuta. No es incertidumbre experimental. Un intervalo tan estrecho que no contenga puntos por encima de esa banda puede tener interior matemático y carecer de muestras motoras resolubles; no se inventa viabilidad para llenarlo.

| Límite / resultado con los nueve valores predeterminados | rp |
|---|---:|
| Frontera inferior ideal | 1 |
| Frontera superior ideal | 403.4175203200 |
| Expansión no ideal: 1/(1−delta) | 1.0526315789 |
| Calor positivo no ideal: cota superior | 254.8459320044 |
| Raíz inferior del trabajo no ideal | 1.0696541023 |
| Raíz superior del trabajo no ideal | 155.4543260392 |
| Óptimo de trabajo IDEAL (no frontera de motor) | 20.0852562921 |

Así, el dominio no ideal es `(1.0696541023,155.4543260392)`. En rp=10 ambos modelos son motores y conservan wn ideal≈505.619018 y no ideal≈369.476301 kJ/kg. En rp=200 el no ideal tiene expansión y calor positivos, pero consume más trabajo de compresión del que produce la turbina: sólo falla `trabajo_neto` y el rendimiento es `None`. En rp=1 fallan simultáneamente compresión, expansión y trabajo; no se escoge una causa arbitraria.

Las cuatro gráficas de rp usan la malla compartida enriquecida alrededor de referencia y máximos; T-s y P-v conservan el caso ideal de referencia. La vista predeterminada va de 1 a 423.5883963360, un 5 % más allá del límite ideal. Las búsquedas normales de máximos alcanzados usan 257 puntos logarítmicos interiores más refinamiento; el ideal/reversible no se busca como máximo de rendimiento (§14 siguiente). Los 100001 puntos pertenecen sólo a la API heredada §4.11. Dominio físico, intervalo numérico y vista son distintos.

**Limitaciones físicas.** Se mantienen gas ideal, cp/gamma constantes, régimen estacionario, equipos adiabáticos y pérdida relativa fija; no hay química, propiedades variables, combustible añadido, potencia, empuje ni mapas. Los dos objetivos se optimizan por separado; T-s/P-v siguen describiendo únicamente el ideal de referencia. Las pruebas de referencia, signos, bisección y límites verifican el código; no validan el modelo frente a datos experimentales.

### Máximo de trabajo no ideal y garantía de interior motor

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Definimos `a=(gamma−1)/gamma>0`, `C=cp/1000>0` [kJ/(kg·K)], `x=rp^a>0`, `theta=T3/T1`, `h=theta*eta_c*eta_t`, `k=(1−delta)^(-a)≥1`. x, theta, h y k son adimensionales; W es trabajo específico neto [kJ/kg]. La expresión de §14 para estados/balance da:

```text
W(x) = C [eta_t*T3*(1−k/x) − (T1/eta_c)*(x−1)]
dW/dx = C [eta_t*T3*k/x² − T1/eta_c]
d²W/dx² = −2*C*eta_t*T3*k/x³ < 0
x* = sqrt(h*k)
rp* = [eta_c*eta_t*T3/(T1*(1−delta)^a)]^(1/(2*a))
```

Respecto a la variable pedida rp, la regla de la cadena proporciona:

```text
dW/drp = C*a*rp^(−a−1) [eta_t*T3*k − (T1/eta_c)*rp^(2*a)]
d²W/drp² evaluada en rp* = −2*C*a²*(T1/eta_c)*rp*^(a−2) < 0
```

La concavidad global demostrada es en x, no necesariamente en rp. Como x crece estrictamente con rp, existe un único máximo estacionario positivo. En `y=ln(rp)` también hay concavidad estricta: `d²W/dy²=−C*a²*[eta_t*T3*k*exp(−a*y)+(T1/eta_c)*exp(a*y)]<0`. Eso justifica el refinamiento unimodal numérico.

**Por qué el candidato está dentro si hay motor.** Si existe un rp>1 con W>0, la turbina debe producir trabajo positivo: x>k. Además `Q(x)=(x−1)(x−h)+h(k−1)<0` (polinomio de Fase 1). Como x>1 y k≥1, se deduce h>x>1. El máximo global x*=sqrt(hk)>1 alcanza trabajo al menos tan positivo como ese punto. Aplicando el mismo razonamiento al candidato, x*>k y 1<x*<h. Por otra parte `h=theta*eta_c*eta_t≤theta*eta_c≤1+eta_c*(theta−1)`, que es la cota de calor positivo. Así el candidato satisface compresión, expansión, calor y trabajo positivos; está entre las raíces de trabajo y en el interior del intervalo motor abierto. No se añade una restricción física. Si ese intervalo es vacío, la fórmula puede seguir dando un número, pero no existe máximo motor admisible. En las fronteras de trabajo el valor es cero, excluido.

Esta prueba es matemática. En coma flotante el máximo puede caer dentro de la banda cero de Fase 1: se declara un límite numérico explícito, no un motor resoluble ni una nueva hipótesis termodinámica.

### Intervalos dinámicos, búsqueda independiente y precisión

**PYTHON.** En cada `main`, `calcular_dominios` recibe los ocho parámetros físicos actuales (la novena entrada es rp de referencia). Se pasan sus dos resultados al optimizador, sin caché global. La caché `registros` vive sólo dentro de una búsqueda. No se reutilizan límites ni óptimos del POST anterior.

| Intervalo | Construcción | Finalidad |
|---|---|---|
| Físico | Abierto (lo,hi) calculado en Fase 1 | Conjunto motor, no es una malla |
| Numérico | ylo=ln(lo), yhi=ln(hi); se quita 10⁻⁶ de la anchura logarítmica en cada lado | Ventana de búsqueda estrictamente interior; 257 muestras por defecto |
| Refinamiento | Vecinos del mejor punto de la malla; sección áurea en y | Localización con hasta 100 iteraciones por defecto, sin fórmula analítica |
| Visual | 1 hasta 1.05 veces el límite ideal, sin tope fijo | Mostrar dominios, fronteras y máximos; máscaras y detalles propios |

El número de muestras de dibujo no crece con hi. Una malla geométrica resuelve rp cercano a 1 y escalas grandes; otra lineal y puntos interiores resuelven el resto; fronteras y vecinos evitan perder cortes, y 17 puntos locales alrededor de cada máximo/referencia dan resolución adicional. La figura puede tener un panel no ideal ampliado sin suprimir la visión general (§4.8). No se mezclan ventana gráfica y numérica.

En la búsqueda, `np.argmax` elige el mejor valor inicial; si cae en un extremo, se rechaza por falta de máximo interior resoluble. Se toman sus vecinos y la razón áurea `(sqrt(5)−1)/2` reduce el intervalo conservando una evaluación en cada paso. El criterio de parada es anchura en y≤10⁻⁹. Se devuelve el mayor trabajo de todos los puntos aceptados: cerca de un máximo plano varios puntos pueden empatar por redondeo, y el mejor registro puede estar fuera del último intervalo de refinamiento. Ese intervalo no es un certificado de precisión del rp devuelto.

Se informa `resolucion_rp=rp*max(tolerancia_log,32*sqrt(eps))` (aprox. 4.77·10⁻⁷ rp en doble precisión). Es una escala conservadora para hacer visible el límite del redondeo, no una cota rigurosa de error. El contraste exige `|Δrp|≤2·10⁻⁶*max(rp_analitico,rp_numerico)` y `|ΔW|≤10⁻⁹*max(|W_analitico|,(cp/1000)*T3)`. La escala térmica evita exigir error relativo imposible cuando W es pequeño por cancelación; la banda motora de Fase 1 se comprueba aparte. Ni el paso inicial ni la tolerancia de parada equivalen a fidelidad física.

**Ejemplo actual:** ideal rp analítico 20.0852562921, numérico 20.0852560217, W=532.8022301186 kJ/kg; no ideal rp analítico 12.8950516696, numérico 12.8950517350, W=373.2108274827 kJ/kg. El rendimiento no ideal **en** ese máximo es 39.2126144220 %. Estados no ideales óptimos: T=(288.15,652.9729714016,1600,863.8229714016) K y p=(100,1289.5051669624,1225.0299086143,100) kPa. Las diferencias ideal menos no ideal son Δrp=7.1902046225 y ΔW=159.5914026359 kJ/kg. cp escala energías y p1 escala presiones; no desplazan rp*. El rp introducido es referencia, no límite de optimización.

**Flask y vacío:** un punto de referencia motor no ideal implica dominio no vacío por definición. `main` conserva el rechazo de referencia inviable de Fase 1 antes de optimizar. La API independiente admite vacío y el presentador puede mostrar «No disponible»; el flujo normal no fuerza un informe exitoso con una referencia físicamente contradictoria.

### Rendimiento térmico y compromiso entre objetivos

La derivación vigente completa está en §4.38; la comparación y las unidades de diferencias están en §4.39. Su correspondencia es: `calcular_candidato_rendimiento` evalúa la raíz racionalizada de P(x)=0; `evaluar_punto` suministra eta=W/qin únicamente en motores; `buscar_maximo_rendimiento_numerico` contrasta sin usar la raíz para elegir la solución; `comparar_criterios` calcula diferencias de esos resultados. El ideal tiene sólo supremo 1−T1/T3, no máximo interior. Cualquier pérdida estricta con dominio motor no vacío da una cima única en matemáticas exactas; las bandas cero se comprueban aparte.

Para el caso actual B tiene rp≈35.4523235708 y eta≈43.8931071631 %, frente a A rp≈12.8950516696 y eta≈39.2126144220 %. Se ganan 4.6804927411 pp, se reduce W un 15.9352054763 % y qin cambia −236.9827016782 kJ/kg. La curva de compromiso muestra ambas decisiones, sin declarar toda la curva frontera de Pareto. El barrido actual predeterminado contiene 1282 muestras; su cantidad procede de deduplicar las mallas, no es una constante física ni una promesa de precisión.

## 15. Partes más difíciles del código

### 15.1. Desempaquetar argumentos con `*`

Fragmento real de `calcular_ciclo_ideal`:

```python
balance = calcular_balance_energetico(*temperaturas, cp)
```

**PYTHON.** Si `temperaturas` contiene cuatro valores, la llamada equivale a:

```python
balance = calcular_balance_energetico(
    temperaturas[0], temperaturas[1], temperaturas[2], temperaturas[3], cp
)
```

El asterisco no multiplica, porque aquí está delante de una expresión dentro de los argumentos. Despliega un iterable en argumentos posicionales. El `cp` posterior es el quinto argumento. Si la tupla tiene tres o cinco temperaturas, el número de argumentos no coincide con la firma y puede aparecer `TypeError`.

**INTERPRETACIÓN FÍSICA.** El orden 1,2,3,4 es esencial. Desplegar cuatro temperaturas desordenadas es sintácticamente válido pero puede ser físicamente incorrecto. Las validaciones ayudan a detectarlo, aunque no sustituyen entender el convenio.

### 15.2. Incorporar un diccionario con `**`

En `calcular_ciclo_ideal`:

```python
return {
    "temperaturas": temperaturas,
    "presiones": presiones,
    "T2s": temperaturas[1],
    "T4s": temperaturas[3],
    **balance,
    "back_work_ratio": balance["trabajo_compresor"] / balance["trabajo_turbina"],
}
```

**PYTHON.** Crea un nuevo diccionario. `**balance` incorpora cada pareja clave-valor del balance al mismo nivel; no crea una clave llamada `balance`. Por eso se consulta `ciclo["trabajo_neto"]`, no `ciclo["balance"]["trabajo_neto"]`. Si hubiera claves repetidas, prevalecería la incorporada después. Esta operación no es una copia profunda de todos los objetos anidados.

`**` tiene otro significado en `rp ** exponente`: ahí es potencia. El contexto gramatical decide cuál se usa. No hay una definición con `**kwargs` en este proyecto.

**INTERPRETACIÓN FÍSICA.** El contenedor reúne información de naturaleza distinta: estados, energías y cocientes. El diccionario es una organización de datos, no una ecuación nueva.

### 15.3. Comprensiones y generadores

```python
return [
    (relacion, calcular_rendimiento(gamma, relacion) * 100)
    for relacion in sorted(relaciones_presiones)
]
```

**PYTHON.** Primero se ordenan las relaciones. Para cada una se calcula una pareja y se añade a una nueva lista. Los paréntesis internos forman una tupla; los corchetes externos construyen la lista. Es equivalente en lógica a crear una lista vacía, recorrer las relaciones y usar `append`.

Un generador como `isfinite(T) and T > 0 for T in (T1,T3)` produce resultados a medida que `all` los pide. No almacena una lista completa antes de revisarla. En `comprobar_estados_pv`:

```python
for valores in (temperaturas, presiones, volumenes) for valor in valores
```

El primer `for` elige una secuencia y el segundo recorre sus números: primero las temperaturas, después las presiones y luego los volúmenes. Hay doce verificaciones escalares si todas pasan.

**INTERPRETACIÓN FÍSICA.** Las comprensiones suelen construir estudios o extraer magnitudes. Los generadores de las validaciones exigen que cada dato cumpla una condición.

### 15.4. `zip`, `enumerate` y desempaquetado anidado

Fragmento `comprobar_estados_pv`:

```python
for estado, (T, p, v) in enumerate(zip(temperaturas, presiones, volumenes), start=1):
```

**PYTHON.** `zip` entrega primero `(T1,p1,v1)`, luego `(T2,p2,v2)`, etc. `enumerate` añade un contador: `(1,(T1,p1,v1))`. La parte izquierda asigna el primer elemento a `estado` y descompone la terna en `T,p,v`. `start=1` fija el contador, pero los índices de las secuencias siguen empezando en cero.

`zip` se detiene en la secuencia más corta. En esta función la comprobación previa de longitudes evita que datos de sobra queden sin validar silenciosamente. En el código principal las secuencias utilizadas tienen cuatro elementos conocidos.

**INTERPRETACIÓN FÍSICA.** Agrupa propiedades de un mismo estado para verificar su ecuación de gas ideal. Evita mezclar, por ejemplo, `T2` con `p3` y `v1`.

### 15.5. Lo escalar, lo vectorizado y la búsqueda numérica

**PYTHON.** Las funciones del ciclo reciben números individuales y utilizan `math.isfinite` y condiciones `if`. No se transforman automáticamente en funciones de arrays por importar NumPy. La búsqueda mantiene un bucle Python explícito dentro de una comprensión para evaluarlas.

Las curvas termodinámicas, en cambio, sí usan arrays directamente: una expresión como `p1*(v1/volumenes_12)**gamma` produce todas las ordenadas de esa curva. Hay que saber identificar dónde se repite una función completa y dónde NumPy repite operaciones aritméticas internamente.

**INTERPRETACIÓN FÍSICA.** `argmax` identifica el mejor punto muestreado, sin resolver exactamente la derivada. En el flujo actual, sus dos vecinos acotan un refinamiento por sección áurea en log(rp). La solución analítica se usa después para contrastar, nunca para elegir ese intervalo. La malla inicial, el criterio de parada y la incertidumbre debida al redondeo son conceptos diferentes (§14).

### 15.6. Derivación del óptimo de trabajo

**INTERPRETACIÓN FÍSICA.** Definimos solo para el razonamiento `x=rp^((gamma−1)/gamma)` y `c=cp/1000`. Con las temperaturas ideales:

```text
wn = c [T3(1−1/x) − T1(x−1)]
dwn/dx = c(T3/x² − T1)
d²wn/dx² = −2cT3/x³ < 0
```

La primera derivada es cero para `x=sqrt(T3/T1)` y la segunda es negativa: hay un máximo. Despejando `rp` resulta la expresión de `calcular_relacion_optima`. Como `c` es un factor positivo, el óptimo no depende de su valor. `p1` tampoco aparece: para este modelo las temperaturas dependen de cocientes de presión.

En ese punto, `T2=T1*sqrt(T3/T1)=sqrt(T1*T3)` y `T4=T3/sqrt(T3/T1)=sqrt(T1*T3)`. Que ambas temperaturas sean iguales **no** anula el aporte de calor, porque este depende de `T3−T2`, no de `T4−T2`.

El rendimiento ideal `1−1/x` crece con `x`: no tiene máximo interior; su supremo no alcanzado es distinto del máximo de trabajo. Al acercarse al límite `T2=T3`, desaparecen el calor aportado y el trabajo, y el código rechaza ese punto. Para los parámetros actuales el límite ideal es aproximadamente `rp=403.417520`, incluido en la nueva vista del dominio; no se confunde con el óptimo rp≈20.085256.

**PYTHON.** La API ideal original evalúa la fórmula con `**` y paréntesis. En el flujo actual `calcular_candidato_analitico` evalúa la generalización mediante logaritmos y `exp`; no hay derivación simbólica en ejecución. La búsqueda independiente verifica ambos casos (§14).

### 15.7. Referencias isentrópicas del no ideal

**INTERPRETACIÓN FÍSICA.** `T2s` describe una compresión reversible con las mismas presiones extremas del compresor real. Al dividir el incremento isentrópico entre `eta_c<1`, se obtiene un incremento real mayor.

Para la turbina, la presión inicial real es `p3=950 kPa`, no `1000 kPa`. Así su `T4s` es mayor que el del ideal incluso antes de introducir `eta_t<1`. Después, multiplicar el salto disponible por `eta_t` reduce la caída real de temperatura y hace subir todavía más `T4`.

**PYTHON.** `calcular_estados` devuelve `presiones` y `temperaturas` en tuplas dentro de un diccionario; `evaluar_punto` añade energía y clasificación. No modifica las tuplas del ideal. No calcula ni dibuja entropías no ideales.

### 15.8. Alcance de las comprobaciones y mensajes

**PYTHON.** Una función puede llamar a otra únicamente para provocar su validación, descartando el resultado. Sucede con el rendimiento en `calcular_temperaturas` y `calcular_relacion_optima`, y con el balance dentro del cálculo de entropía. Es legal, aunque obliga a seguir varias llamadas para entender qué se valida realmente.

**INTERPRETACIÓN FÍSICA.** La igualdad `ln(T3/T2)=ln(T4/T1)` implica una relación entre temperaturas, pero no certifica por sí sola la reversibilidad de máquinas reales: faltan presiones y supuestos. La validación P-v añade comprobaciones isentrópicas cuando se calculan estados ideales. Entender qué información recibe cada función impide atribuirle una comprobación más fuerte de la que hace.

### 15.9. Geometría de las flechas y estructuras de dibujo

**PYTHON.** `procesos` contiene cuatro ternas de coordenadas y etiqueta. El bucle las desempaqueta y usa el mismo algoritmo de dibujo. En T-s los segmentos verticales tienen solo dos puntos y se eligen posiciones al 40 % y 60 % de su altura. Las isóbaras tienen 100 puntos y se usan los índices 40 y 60. En P-v todos los procesos tienen 200 muestras y se usan 90 y 110.

**INTERPRETACIÓN FÍSICA.** Esas posiciones solo deciden dónde se ve la flecha. No son tiempos de proceso, fracciones de calor ni resultados termodinámicos. El orden ascendente o descendente de las muestras hace que las flechas sigan 1→2→3→4→1.

### 15.10. Contextos y propiedad del temporal

**PYTHON.** `with archivo:` garantiza el cierre. `finally` ejecuta limpieza aunque ascienda una excepción, sin capturarla por sí mismo. El temporal se abre con modo exclusivo antes de entrar en su bloque de retirada: si ya existía, no era nuestro y no debemos eliminarlo.

`{nombre: buffer.getvalue() for nombre, buffer in imagenes.items()}` crea un nuevo diccionario de bytes. Cerrar los buffers después no destruye los bytes incorporados al HTML.

**INTERPRETACIÓN FÍSICA.** Es integridad de salida, no comprobación de ecuaciones. El éxito se imprime al final para no anunciar un cálculo incompleto.

### 15.11. Texto HTML y bytes de imagen

**PYTHON.** PNG es binario; HTML es texto. Base64 permite representar los bytes con ASCII. `escape` protege texto dentro del marcado; Base64 transporta la imagen; `join` une fragmentos. Son operaciones diferentes.

**INTERPRETACIÓN FÍSICA.** El informe mantiene juntos parámetros y gráficas de una ejecución, sin aumentar precisión física. Las tablas se formatean; los PNG representan todas las muestras calculadas.

## 16. Qué código podrías escribir con tu base actual

| Nivel | Partes actuales | Objetivo |
|---|---|---|
| Básico | Parámetros, fórmulas, condiciones y f-strings | Escribirlas y explicar unidades y signos |
| Intermedio | Funciones encadenadas, diccionarios, comprensiones, arrays y gráficos | Seguir datos desde entradas hasta tablas/imágenes |
| Avanzado para tu situación | Desempaquetado, tolerancias, `finally`, buffers, Base64, publicación y retención | Explicar contratos y qué sucede ante cada fallo |
| Herramientas de verificación | Clases de prueba, parser, mocks y temporales | Ejecutar pruebas y entender qué propiedad verifica cada una |

HTML básico se aprende con tablas pequeñas; la dificultad principal es coordinar números correctos, imágenes actuales y retención segura. No necesitas implementar internamente Matplotlib, UUID o el parser para usarlos con criterio. La presentación profesional no sustituye justificar las ecuaciones.

## 17. Posibles mejoras del código, sin aplicarlas

### PROBLEMA REAL: límites con consecuencias concretas

| Observación | Consecuencia |
|---|---|
| Clasificación con tolerancia y redondeo cerca de un máximo plano | Un intervalo matemático extremadamente estrecho puede no tener puntos resolubles como motores; el ancho final no certifica la precisión en rp |
| API Python de `main` y contratos internos sin comprobación exhaustiva de tipos | La web valida sus campos; una llamada Python manual mal estructurada aún puede producir `TypeError` o `KeyError` |
| Retención por fecha de modificación y marcas | Editar informes cambia su orden; imitar deliberadamente formato y marcas los hace indistinguibles de un informe propio |
| Limpieza sin bloqueo multiproceso | Procesos simultáneos podrían interferir en la retención |
| Permisos o errores durante limpieza | Pueden quedar más de cuatro informes, con advertencia explícita |

### MEJORA OPCIONAL

- Reducir cálculos y validaciones repetidos entre estados, entropías y balance.
- Añadir anotaciones de tipos y contratos de datos si crece el proyecto.
- Revisar publicación y bloqueos si se soportan otros sistemas o procesos concurrentes.
- Fijar versiones de dependencias si se requiere reproducibilidad estricta; solo se ha añadido Flask y sus dependencias necesarias.

Ya existe punto de entrada protegido y el flujo normal no sobrescribe PNG históricos. La configuración predeterminada es global, pero cada ejecución trabaja con una copia local y las funciones físicas reciben argumentos. Las pruebas verifican implementación y almacenamiento, no todos los fallos de hardware ni datos físicos externos. La revisión de Fase 1 incluye un informe generado en una carpeta alternativa y la inspección visual de las curvas de rendimiento comparado y trabajo ideal; no se consumió el historial de `outputs/`.

## 18. Preguntas de autoevaluación

Intenta responder antes de abrir las soluciones. No hace falta memorizar las últimas cifras de los resultados.

1. ¿Cuáles son los nueve parámetros del caso actual y cuáles llevan unidades?
2. ¿Qué ocurre al ejecutar una línea `def`? ¿Se calculan ya las temperaturas?
3. ¿Qué diferencias hay entre la tupla de temperaturas, la lista de puntos y el diccionario de balance?
4. ¿Qué expresión física representa `relacion_presiones ** ((gamma - 1) / gamma)`?
5. ¿Por qué se exige `T3>T2`? ¿Basta con que todas las temperaturas sean positivas?
6. ¿Qué significa `calcular_balance_energetico(*temperaturas, cp)` y cuántos argumentos recibe?
7. ¿Qué incorpora `**balance` al diccionario del ciclo?
8. ¿Por qué el trabajo del compresor es positivo y aun así se resta?
9. ¿Cómo se convierte `cp·ΔT` a kJ/kg? ¿Y un rendimiento a porcentaje?
10. En la API heredada §4.11, ¿qué produce `np.linspace(1.01,50,100001)` y cuál es su paso aproximado?
11. ¿Qué devuelve `np.argmax(trabajos)` y cómo recuperas la relación de presiones correspondiente?
12. ¿Por qué el máximo numérico y el analítico no coinciden exactamente?
13. ¿Por qué `T2=T4` en el máximo de trabajo ideal? ¿Significa que no se aporta calor?
14. ¿Qué indica `s1=0`? ¿Por qué se comparan incrementos 2→3 y 1→4, y no directamente 2→3 y 4→1 con el mismo signo?
15. ¿Por qué el `T4s` del modelo no ideal difiere del ideal cuando hay pérdida de presión?
16. ¿Qué relación verifican `p*1000*v` y `R*T`, y por qué aparece 1000?
17. ¿Qué hace `linea, = ejes.plot(...)` y para qué se recupera el color?
18. ¿Qué aportan Agg y `plt.close(figura)`? ¿Qué consigue Base64 al incorporar cada PNG al HTML?
19. ¿Qué diferencia hay entre GET y POST en esta interfaz? ¿Cómo convierte Flask un 5 % de pérdida y qué ocurre si se importa `web_app`?
20. ¿Qué devuelve una comprobación cuando todo es correcto y qué ocurre si lanza un `ValueError` sin capturarlo?

21. ¿Por qué el dominio ideal termina en rp≈403.42 y el trabajo máximo ocurre cerca de rp≈20.09?
22. ¿Puede qin ser positivo y wn negativo? Clasifica el no ideal en rp=200 sin publicar un informe.
23. ¿Por qué Q(x)<0 sólo produce un intervalo o vacío en este modelo? ¿Qué ocurre si D=0 o h<=1?
24. ¿En qué se diferencian `None`, `np.nan` y cero en los resultados de Fase 1?
25. ¿Qué significan la tolerancia de bisección y la banda energética? ¿Son datos experimentales?
26. ¿Por qué un candidato estacionario no es por sí solo un máximo motor? ¿Qué garantiza su pertenencia interior si hay dominio?
27. ¿Por qué pueden cambiar las energías al duplicar cp sin cambiar rp*? ¿Qué intervalo usa la búsqueda frente al dibujo?

<details>
<summary>Soluciones de autoevaluación — abrir después de responder</summary>

1. `gamma`, `relacion_presiones`, `T1`, `T3`, `cp`, `p1`, `eta_c`, `eta_t`, `perdida_presion_combustor`. Temperaturas en K, `cp` en J/(kg·K), `p1` en kPa; los demás son adimensionales.
2. Se crea y nombra la función; su cuerpo espera a una llamada. Todavía no se calculan estados.
3. La tupla agrupa estados en orden y es inmutable; la lista se amplía con `append`; el diccionario permite buscar resultados por clave. Contienen tipos de objetos diferentes.
4. Es el factor térmico isentrópico `rp^a`. Multiplica `T1` para obtener `T2` y divide `T3` para obtener `T4` en el ideal.
5. Garantiza aporte de calor positivo en 2→3. Para temperaturas generadas por las relaciones ideales y `rp>1`, también conduce al régimen motor. En un conjunto arbitrario o no ideal, el balance comprueba además trabajo neto positivo. Positividad de temperaturas por sí sola no basta.
6. Despliega cuatro temperaturas en cuatro argumentos y añade `cp` como quinto argumento posicional.
7. Las cinco parejas clave-valor del balance se incorporan al mismo nivel del diccionario exterior.
8. Se define como magnitud del consumo. El trabajo útil disponible es la producción de turbina menos ese consumo.
9. `cp·ΔT` está en J/kg y se divide entre 1000. El rendimiento fraccionario se multiplica por 100 para expresarlo en %.
10. Un array de 100001 puntos uniformes con extremos incluidos; paso `0.0004899`.
11. La posición del mayor trabajo; `relaciones[indice]` obtiene su relación y `trabajos[indice]` su valor. El índice cuenta desde cero.
12. Se evalúa una cantidad finita de puntos y se refina con valores aproximados. Cerca de un máximo plano el redondeo limita la precisión de rp. La búsqueda actual contrasta con tolerancias separadas en rp y trabajo; un paso corresponde sólo a la API heredada.
13. En el óptimo el factor térmico es `sqrt(T3/T1)`, de modo que ambas son `sqrt(T1*T3)`. Sigue habiendo calor porque `T3>T2`; `T4` no es la temperatura inicial del calentamiento.
14. Es una referencia arbitraria de entropía relativa. El enfriamiento 4→1 reduce entropía; el incremento 1→4 es su opuesto y coincide con el aumento positivo 2→3 del ciclo ideal.
15. La turbina no ideal entra con `p3=p2(1−δ)`, menor que la presión alta ideal. Con la misma salida `p4`, su expansión isentrópica de referencia es menor y deja una temperatura mayor.
16. Ambos deben ser iguales por `Pv=RT`. La presión se almacena en kPa y se pasa a Pa para utilizar `R` en J/(kg·K).
17. Desempaqueta el único objeto de línea de la lista devuelta por `plot`. Su color se usa para que la flecha de ese proceso coincida con la curva.
18. Agg permite guardar sin ventanas ni Tkinter; `close` libera el registro de la figura. Base64 representa los bytes PNG como texto que puede incluirse en una URL de datos dentro del HTML. Ninguna operación cambia las ecuaciones.
19. GET solicita formulario/informe sin ejecutar un caso nuevo; POST envía datos y solicita una simulación. El campo llega como texto, se convierte a `float` y se divide entre 100: 5 pasa a 0.05. Importar `web_app` registra rutas pero no inicia el servidor ni una simulación.
20. Devuelve `None`. Un fallo de cálculo/publicación sin capturar conserva traceback; `finally` limpia recursos. Un fallo de retención posterior al guardado produce advertencia.

21. En el límite superior desaparecen calor y trabajo; el óptimo interior maximiza el trabajo positivo y su rp es la raíz cuadrada del límite ideal.
22. Sí: con pérdidas, parte del aporte de calor no basta para cubrir el consumo. `evaluar_punto(...,rp=200,...)` conserva expansión/calor positivos, wn negativo y rendimiento `None`.
23. Q tiene coeficiente principal positivo y sólo es negativa entre dos raíces distintas; las otras restricciones son intervalos y x→rp es creciente. D=0 no deja interior positivo; h<=1 tampoco permite motor para x>=k>=1.
24. `None` declara que el cociente motor no se ofrece; NaN ocupa una muestra excluida y corta el dibujo; cero es un valor energético que identifica una frontera, no interior motor.
25. La primera acota el error en x de una raíz; la segunda evita clasificar residuos de redondeo como trabajo/calor positivo. Ninguna mide incertidumbre de un motor real.
26. La fórmula sólo anula una derivada. Hace falta dominio no vacío y candidato motor resoluble; la concavidad, W>0 y la cota h inferior a la de calor prueban interior matemático (§14). La banda numérica se comprueba aparte.
27. cp es factor positivo de W y no cambia dónde se anula su derivada. La búsqueda está dentro de (lo,hi) de Fase 1; el dibujo va desde 1 hasta un margen sobre el límite ideal, con NaN fuera de cada motor.

</details>

## 19. Mini ejercicios de programación

Estos son ejercicios propuestos, **sin aplicar cambios al programa**. Practícalos cuando decidas hacerlo en una copia de trabajo. Cada uno indica qué deberías observar, sin incluir su implementación.

1. **Cambiar un parámetro.** Prueba `relacion_presiones=8` desde el formulario o con `main(parametros={"relacion_presiones": 8})`. Antes de ejecutar, predice el sentido de cambio de `T2`, `T4` y rendimiento ideal. Distingue este parámetro de las mallas independientes, que seguirán usando sus propios extremos.
2. **Modificar una celda del informe.** Presenta el rendimiento ideal con cuatro decimales en vez de seis usando una f-string. Comprueba que no cambia el cálculo.
3. **Crear una función pequeña.** Escribe una función que convierta J/kg a kJ/kg y úsala primero en ejemplos independientes de 1000 y 2500 J/kg. Explica qué devuelve y qué unidad espera.
4. **Practicar la validación del formulario.** Llama a `leer_parametros` con valores predeterminados y sustituye `p1` por cero, texto y `inf`. Explica en cada caso por qué no se debe llamar a `main` y dónde se muestra el error.
5. **Extraer información de un diccionario.** Obtén temperaturas y trabajo del ciclo ideal usando su función agrupadora. Imprime `T2` sin recalcularlo por separado y explica las dos indexaciones necesarias.
6. **Expandir una comprensión.** Reescribe en tu copia la construcción de `mascara` en `construir_barrido` mediante lista vacía, `for` y `append`, seguida de `np.array`. Comprueba que las curvas no cambian.
7. **Construir una tabla con `zip`.** Prepara cuatro filas de estado, T y p; pásalas a `tabla_html` e indica unidades. Verifica que las secuencias tengan cuatro elementos.
8. **Revisar unidades y energía.** Calcula en una función nueva de práctica el calor rechazado `cp*(T4−T1)/1000`, como magnitud positiva. Contrasta `qin−qout` con el trabajo neto del balance utilizando tolerancias. Esta magnitud sería una ampliación: el código actual no la devuelve.
9. **Explorar resolución numérica.** Llama a `buscar_maximo_numerico(288.15,1600,1.4,1005,100,.85,.9,.05,muestras=129)` y después con 257. Compara `paso_log_inicial`, `evaluaciones`, error en rp y trabajo frente al analítico. Mantén las tolerancias: más muestras iniciales no garantizan más dígitos fiables en un máximo plano.
10. **Separar cálculo y dibujo en un experimento pequeño.** Escribe una función que devuelva únicamente relaciones y trabajos de un barrido corto, sin imprimir ni guardar. Otra función de práctica debe representarlos con `figura,ejes`. Decide cómo se manejará un punto que no sea un ciclo motor y documenta esa decisión antes de programarla.

11. **Clasificar sin generar archivos.** Importa `evaluar_punto` y consulta rp=1, 10, 200 y 500 con los parámetros predeterminados. Imprime todos los códigos de `motivos`. Contrasta con §14; no llames a `main` para este ejercicio.
12. **Explorar ambas caras de una raíz.** Obtén `dominios['noideal']['trabajo'][1]`; evalúa esa rp y sus vecinos multiplicados por 1±1e−6. Espera motor sólo por debajo, banda de frontera en el centro y trabajo negativo por encima.
13. **Leer una máscara.** Construye un barrido corto con `[1,2,10,200,500]`. Cuenta `viable.sum()`, comprueba NaN en `rendimiento[~viable]` y recupera el trabajo firmado desde `puntos`. Explica por qué no debes sustituir NaN por cero ni eliminar muestras para unir la curva.

## 20. Resumen final

Deberías llegar a entender perfectamente las cuatro etapas, la numeración de estados, las hipótesis del gas, las unidades y el signo de cada balance. También las funciones que convierten entradas en temperaturas y energías, la diferencia entre rendimiento y trabajo máximo, y el sentido de las referencias isentrópicas del modelo no ideal.

En Python, practica definir y llamar funciones, leer retornos, manejar tuplas y diccionarios, escribir bucles, seguir excepciones y distinguir asignaciones de comparaciones. Después reproduce por separado una comprensión, una llamada con `*temperaturas`, una combinación con `**balance`, un `zip` y la selección de un máximo por índice. Debes poder explicar esos patrones con un ejemplo de dos o tres números.

Puedes utilizar Matplotlib y NumPy sin dominar todavía sus mecanismos internos, la implementación del backend o toda la teoría de aritmética flotante. Sí debes comprender qué secuencias reciben, qué coordenadas representan y por qué las comparaciones usan tolerancias.

Antes de ampliar el proyecto, conviene saber ejecutar y seguir una función de forma aislada, distinguir cálculo de presentación, definir el dominio físico admisible y comprobar un resultado por un segundo camino. Para ampliar la interfaz serán especialmente útiles el control de efectos al importar, los contratos de entrada y salida, el manejo de errores y la separación de datos y archivos por ejecución. El punto de entrada protegido, la presentación separada y la publicación del informe ya preparan parte de ese camino. La interfaz local y la validación del formulario ya están implementadas. El dominio viable está implementado para las ecuaciones actuales. Una web pública, autenticación y ejecución multiproceso siguen fuera del alcance.

Practica generar una tabla HTML pequeña, cerrar archivos con `with`, explicar PNG→Base64 y justificar por qué la retención ocurre después de publicar. Distingue errores de cálculo de advertencias de conservación.

Una buena prueba de comprensión será reconstruir a mano el camino `parámetros → temperaturas → balance → rendimiento`, justificar cada validación y explicar por qué el caso no ideal entrega menos trabajo sin recurrir solo a que «lo dice la gráfica».

## Evolution of the project

Estos hitos resumen capacidades ya implementadas en la versión analizada, sin atribuirles fechas ni reconstruir un historial de commits. Los detalles del funcionamiento actual se explican en las secciones anteriores.

- **Modelo Brayton ideal y balance energético.** Ingeniería: relaciones isentrópicas, rendimiento y trabajos específicos con unidades y signos coherentes. Python: funciones, parámetros, retornos, tuplas, diccionarios y validación de entradas.
- **Estados y diagramas termodinámicos ideales.** Ingeniería: entropía relativa, ecuación del gas ideal, isóbaras e isentrópicas en T-s y P-v. Python: arrays, operaciones vectorizadas, objetos de Matplotlib y rutas de guardado con `Path`.
- **Máximo de trabajo específico ideal.** Ingeniería: optimización analítica a temperaturas extremas fijas y distinción entre máximo trabajo y máximo rendimiento. Python: barrido discreto, comprensiones, selección con `np.argmax` y comprobaciones con tolerancias.
- **Eficiencias no ideales y pérdida de presión del combustor.** Ingeniería: referencias isentrópicas de compresor y turbina, irreversibilidades y reducción de la expansión disponible. Python: reutilización del balance, resultados agrupados en diccionarios y comprobación del límite reversible.
- **Comparación paramétrica de los dos modelos.** Ingeniería: evolución del rendimiento y trabajo neto al variar la relación de presiones. Python: listas de resultados, bucles con desempaquetado y generación de dos gráficas a partir de un mismo barrido.

- **Informes HTML autocontenidos e historial de cuatro ejecuciones.** Ingeniería: trazabilidad de parámetros, números y gráficas sin cambiar el modelo; verificación frente a validación física. Python: módulos, buffers, Base64, HTML/CSS, publicación mediante temporal, filtrado y pruebas de conservación. Véase `docs/milestones/01_html_reports.md`.

- **Interfaz local Flask para configurar ciclos.** Ingeniería: unidades, conversión de porcentaje y distinción entre rangos de entrada e inviabilidad de los estudios actuales, sin ecuaciones nuevas. Python: HTTP GET/POST, rutas, plantillas Jinja, configuración por copia, excepciones específicas y pruebas de integración sin sockets. Véase `docs/milestones/02_local_flask_interface.md`.

- **Fase 1: dominio físicamente viable.** Ingeniería: fronteras motoras ideales/no ideales, expansión, calor y trabajo positivos; prueba de intervalo o dominio vacío y distinción del óptimo ideal. Python: módulo físico común, clasificación con motivos simultáneos, bisección acotada, máscaras/NaN, muestreo adaptado y errores diferenciados en Flask. Véase `docs/milestones/03_dominio_viable.md`.

- **Fase 2: máximo de trabajo específico no ideal e intervalos dinámicos.** Ingeniería: derivación del punto estacionario, prueba de máximo interior cuando hay dominio motor y rendimiento evaluado en el máximo de trabajo. Python: módulo reutilizable, malla logarítmica, sección áurea, caché local y datos estructurados; gráficas e informes adaptados por ejecución. Véase [milestone técnico](docs/milestones/04_optimizacion_noideal.md) y [aprendizaje independiente](docs/milestones/04_optimizacion_noideal_APRENDIZAJE.md).

- **Fase 3: optimización del rendimiento y comparación de criterios.** Ingeniería: supremo ideal no alcanzado, máximo no ideal único con pérdidas y dominio motor, y distinción de objetivos. Python: raíz racionalizada, funciones estables cerca de cero, búsqueda independiente y contratos de disponibilidad. Integrada en main, gráficas, HTML y Flask con comparación A/B y curva de compromiso; documentación revisada y verificación de cierre. Véase [milestone técnico](docs/milestones/05_optimizacion_rendimiento.md) y [guía educativa](docs/milestones/05_optimizacion_rendimiento_APRENDIZAJE.md).
