# Guía educativa de Brayton Simulator

Guía del estado actual, actualizada el 18 de octubre de 2026. El modelo termodinámico no ha cambiado; la salida normal ahora es un informe HTML autocontenido por ejecución, con seis gráficas creadas en memoria.

Hay tres módulos del programa (`main.py`, `reporting.py`, `web_app.py`) y dos archivos de pruebas (`tests/test_reporting.py`, `tests/test_web_app.py`). Se añaden una plantilla HTML y un CSS local. `.venv` contiene dependencias, no código propio. Las funciones de cálculo conservan las ecuaciones anteriores.

Se han superado 22 pruebas, incluidas las de Flask `test_client`, ejecuciones mezcladas de terminal y web, parámetros modificados, archivos ajenos, fallos, imágenes y estados Git. Las 13 funciones físicas se han comparado por AST antes y después de esta tarea y permanecen idénticas. Se ha ejecutado además un caso real desde el botón del navegador y vuelto al formulario sin reiniciar el servidor. Se ha iniciado el servidor real exclusivamente en `127.0.0.1:5000` y revisado el formulario en el navegador integrado. Las seis gráficas usan 1350 × 900 píxeles. Estas comprobaciones verifican implementación y presentación, no validación experimental de un motor.

Los ejemplos que guardan PNG explícitamente son usos opcionales de las funciones gráficas; la ejecución normal no lee ni sobrescribe los PNG históricos. Las referencias de líneas del inventario corresponden al código actual.

## 1. Visión general del programa

El programa estudia un ciclo Brayton ideal y otro no ideal simplificado. Usa gas ideal con `cp` y `gamma` constantes, equipos adiabáticos en régimen estacionario y cambios despreciables de energía cinética y potencial. No calcula caudal másico, potencia, combustible, empuje ni mapas de máquinas.

| Estado | Lugar físico |
|---|---|
| 1 | Entrada del compresor |
| 2 | Salida del compresor |
| 3 | Entrada de la turbina |
| 4 | Salida de la turbina |

**INTERPRETACIÓN FÍSICA.** Los procesos ideales son dos isentrópicas y dos isóbaras. El no ideal incorpora eficiencias de compresor y turbina y pérdida de presión del combustor. El óptimo sigue siendo exclusivamente ideal y maximiza trabajo específico, no rendimiento.

**PYTHON.** Los nueve parámetros predeterminados están en `PARAMETROS_PREDETERMINADOS`. `main()` copia esa configuración y admite cambios por argumento. Flask convierte el formulario y llama a esa misma función; las funciones numéricas calculan; Matplotlib dibuja en buffers `BytesIO`; `reporting.py` compone HTML con CSS e imágenes Base64 y publica un archivo completo en `outputs/`. No se genera un TXT intermedio. La terminal muestra tres líneas de éxito; los detalles van al informe.

```text
Imports y definiciones
↓
Terminal: main() con valores predeterminados
O navegador: GET formulario → POST → validación → main(parametros=...)
↓
Fecha, versión Git y copia de configuración
↓
Estados, balance y comprobaciones ideales
↓
Optimización ideal analítica y numérica
↓
Ciclo no ideal y límite reversible
↓
Seis gráficas nuevas en memoria y validación del barrido
↓
Tablas + CSS + imágenes Base64 → HTML en memoria
↓
Escritura temporal → publicación del HTML completo
↓
Conservación de los cuatro informes propios completos más recientes
↓
Resumen breve en terminal
```

El informe contiene cabecera con commit Git y estado local, parámetros, ciclo ideal, diagramas ideales, optimización ideal, ciclo no ideal, comparaciones y comprobaciones. Los resultados siguen siendo **505.619018 kJ/kg y 48.205253 %** en el ideal, y **369.476301 kJ/kg y 36.898732 %** en el no ideal.

| Clave de imagen en memoria | Contenido | Muestreo |
|---|---|---|
| `rendimiento_brayton.png` | Rendimiento exclusivamente ideal | 100 relaciones entre 2 y 30 |
| `diagrama_ts_brayton.png` | T-s exclusivamente ideal | Caso de referencia |
| `diagrama_pv_brayton.png` | P-v exclusivamente ideal | Caso de referencia |
| `trabajo_neto_vs_rp.png` | Trabajo y máximo exclusivamente ideales | 100001 relaciones entre 1.01 y 50 |
| `comparacion_ideal_noideal.png` | Rendimiento ideal/no ideal | 300 relaciones entre 2 y 30 |
| `trabajo_neto_ideal_noideal.png` | Trabajo ideal/no ideal | Mismo barrido de 300 puntos |

Estos nombres son claves: no implican que se escriban seis PNG. Las imágenes van dentro de un único `brayton_fecha_hora_microsegundos_uuid.html`, sin Internet ni archivos externos.

## 2. Estructura completa del repositorio

```text
Brayton_Simulator/
├── AGENTS.md                   instrucciones permanentes
├── CODE_WALKTHROUGH.md         explicación educativa actual
├── main.py                     modelo, gráficas y coordinación
├── reporting.py                HTML y conservación de informes
├── web_app.py                  servidor Flask de acceso local
├── templates/index.html        formulario Jinja/HTML
├── static/style.css            estilos locales del formulario
├── tests/test_reporting.py     pruebas de informes
├── tests/test_web_app.py       pruebas HTTP y compatibilidad
├── README.md                   instalación y uso
├── requirements.txt            numpy, matplotlib y Flask
├── .gitignore
├── docs/milestones/            resúmenes de avances importantes
├── outputs/                    informes generados, excluidos de Git
└── *.png                       seis imágenes históricas conservadas
```

`outputs/` se crea al guardar el primer informe si no existe. `.venv` es el entorno local y `.vscode/settings.json` configura el editor; no participan en las ecuaciones. `.gitignore` excluye entorno, cachés, temporales, configuración local y resultados generados. Git conserva versiones de código y documentación cuando se solicitan commits; no se crean copias numeradas del walkthrough.

| Archivo/bloque | Líneas actuales aproximadas | Responsabilidad |
|---|---:|---|
| `main.py`: imports | 1–18 | Rutas, fecha, memoria y bibliotecas |
| Configuración y `ErrorModelo` | 19–27 | Valores predeterminados y excepción de rechazo esperado |
| Rendimiento y temperaturas | 30–63 | Funciones ideales y tabla |
| Balance y ciclo ideal | 66–107 | Energías y diccionario del ciclo |
| No ideal y comparación | 110–170 | Irreversibilidades y verificaciones |
| Barrido comparativo | 173–207 | Dos gráficas en memoria |
| Trabajo y optimización | 210–254 | Trabajo, óptimo y gráfica |
| Entropía y T-s | 257–321 | Estados relativos y diagrama |
| P-v | 324–395 | Validación, estados y diagrama |
| Rendimiento gráfico | 398–412 | Primera gráfica |
| `main()` | 415–519 | Parámetros y coordinación |
| Punto de entrada | 522–523 | Llama a `main` solo al ejecutar el script |
| `reporting.py`: constantes e imports | 1–16 | Módulos estándar, marcas y patrón de nombres |
| Consulta Git | 19–33 | Metadatos de versión, sin modificar el repositorio |
| Tablas e imágenes HTML | 36–55 | Escape, tablas y Base64 |
| Documento completo | 58–208 | Secciones, datos y CSS |
| Publicación y retención | 211–251 | Temporal, HTML final y cuatro informes |
| `web_app.py` | 1–132 | Formulario, validación, informes, errores y arranque local |
| `templates/index.html` y `static/style.css` | Archivos completos | Plantilla Jinja y presentación adaptable |
| Archivos `tests/test_*.py` | Véanse §4 y §10 | Pruebas de referencia, HTTP, integración y fallos |

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

**Qué hace:** contrasta el máximo analítico con una malla y compara familias de ciclos.

**PYTHON:** `np.linspace`, comprensiones, arrays, `argmax`, índices, listas y `append`.

**INTERPRETACIÓN FÍSICA:** cambia `rp` con condiciones extremas fijas. No se implementa dominio viable ni se saltan puntos inválidos. La optimización es exclusivamente ideal.

### E. Entropía, P-v y gráficas

**Qué hace:** obtiene propiedades ideales y representa seis imágenes con las mismas curvas anteriores.

**PYTHON:** `zip`, `enumerate`, arrays, objetos gráficos y `BytesIO`. `ruta` puede ser un buffer. `savefig(..., format="png")` indica el formato sin necesitar extensión.

**INTERPRETACIÓN FÍSICA:** logaritmos T-s y leyes `Pv=RT`, `Pv^gamma=constante`. Las flechas indican sentido, no tiempo.

### F. Coordinación en `main()`

**Qué hace:** copia los parámetros predeterminados, aplica los recibidos, realiza cálculos, registra comprobaciones y solicita HTML.

**PYTHON:** `dict.copy`, `update`, variables locales, lista de mensajes, `try/except` en cálculo y `try/finally` para liberar buffers y figuras. `is None` selecciona `outputs/`. Devuelve una ruta y muestra tres líneas tras guardar.

**INTERPRETACIÓN FÍSICA:** coordina resultados sin ecuaciones nuevas. Añadir un mensaje después de superar una llamada registra esa comprobación; no constituye otra prueba física.

### G. HTML y Base64

**Qué hace:** forma tablas, secciones y CSS, incorporando las seis imágenes de la ejecución.

**PYTHON:** `str`, `escape`, `join`, f-strings multilínea, `b64encode(...).decode("ascii")`. CSS usa llaves dobles para obtener llaves literales en una f-string.

**INTERPRETACIÓN FÍSICA:** conserva unidades e identificación ideal/no ideal. La presentación no mejora la fidelidad física.

### H. Publicación y conservación

**Qué hace:** escribe un temporal, publica el HTML completo y conserva cuatro informes propios.

**PYTHON:** `Path`, `mkdir`, apertura exclusiva `"x"`, `with`, `try/finally`, `rename`, expresiones regulares, UUID, `lambda`, `[4:]` y `unlink`. Errores posteriores de limpieza se notifican con advertencia.

**INTERPRETACIÓN FÍSICA:** no contiene ecuaciones; mantiene juntos parámetros, números y gráficas de una ejecución.

### I. Servidor y formulario

**Qué hace:** muestra nueve campos agrupados, valida el POST, invoca el simulador y redirige a su informe. Los parámetros enviados se conservan cuando hay errores.

**PYTHON:** objeto `Flask`, decoradores `@app.route`, `request`, `float`, diccionarios de errores y `render_template`. La pérdida se divide por 100 una sola vez antes de llamar al simulador.

**INTERPRETACIÓN FÍSICA:** no hay ecuaciones nuevas. Los rangos de campos y el rechazo de combinaciones se distinguen del análisis de dominio viable, que sigue pendiente. No se amplían los barridos existentes.

### J. Pruebas

**Qué hace:** comprueba referencias, cinco ejecuciones, errores y colisiones.

**PYTHON:** clases de `unittest`, `self`, `assert*`, `patch`, directorios temporales y parser HTML. El modelo no introduce clases propias.

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

### 4.1. `calcular_rendimiento`, main.py:L30–38

```python
def calcular_rendimiento(gamma, relacion_presiones):
```

- **Problema físico:** rendimiento térmico del Brayton ideal, `η=1−rp**(−(gamma−1)/gamma)`.
- **Entrada y tipos:** dos escalares numéricos reales; `gamma=cp/cv` y `relacion_presiones=p2/p1`, ambos adimensionales. Admite los `int`, `float` y escalares NumPy utilizados por el programa; no está diseñada para arrays completos.
- **Salida:** escalar de rendimiento como fracción adimensional, aproximadamente `0.4820525321` para el caso actual.
- **Validación:** ambos finitos; `gamma>1`, `rp>1`. No recibe `T1` ni `T3`, así que no comprueba disponibilidad de calor o trabajo para temperaturas fijadas.
- **Llama:** ninguna función propia; usa `isfinite`.
- **La llaman:** `calcular_rendimientos`, `calcular_temperaturas`, `calcular_relacion_optima`, `calcular_estados_pv`, `guardar_grafica_rendimiento` y `main()`.
- **Ejemplo:** `calcular_rendimiento(1.4, 10)`.
- **Errores:** `ValueError` para dominio inválido; entradas de tipo incompatible pueden provocar `TypeError`; potencias extremas pueden provocar `OverflowError`. No hay captura interna.

### 4.2. `calcular_rendimientos`, main.py:L41–46

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

### 4.3. `calcular_temperaturas`, main.py:L49–63

```python
def calcular_temperaturas(T1, T3, gamma, relacion_presiones):
```

- **Problema físico:** obtener las temperaturas de salida isentrópicas a partir de las temperaturas extremas.
- **Entrada y tipos:** cuatro escalares; `T1`, `T3` en K; `gamma`, `rp` adimensionales.
- **Salida:** tupla `(T1, T2, T3, T4)` en K. Devuelve también las temperaturas de entrada recibidas.
- **Ecuaciones:** `factor=rp**((gamma−1)/gamma)`, `T2=T1*factor`, `T4=T3/factor`.
- **Validación:** `gamma` y `rp` por delegación; temperaturas de entrada positivas y finitas, salidas finitas y `T3>T2`. Con estas relaciones ideales y `rp>1`, esa desigualdad corresponde a un ciclo motor con aporte de calor positivo.
- **Llama:** `calcular_rendimiento`; aquí se aprovecha su validación y se descarta su resultado.
- **La llaman:** `calcular_ciclo_ideal`, `calcular_ciclo_noideal`, `calcular_trabajo_neto` y `main()`.
- **Ejemplo:** `calcular_temperaturas(288.15, 1600, 1.4, 10)` → aproximadamente `(288.15, 556.330551, 1600, 828.715949)`.
- **Errores:** `ValueError` si no hay calentamiento admisible, o si un dato no es finito/positivo; también puede propagar errores de tipo o de desbordamiento.

### 4.4. `calcular_balance_energetico`, main.py:L66–93

```python
def calcular_balance_energetico(T1, T2, T3, T4, cp):
```

- **Problema físico:** calcular trabajos, calor aportado y rendimiento con los estados dados, ideales o no ideales.
- **Entrada y tipos:** cinco escalares numéricos; temperaturas en K, `cp` en J/(kg·K).
- **Salida:** diccionario con `trabajo_compresor`, `trabajo_turbina`, `trabajo_neto`, `calor_aportado` en kJ/kg y `rendimiento` adimensional.
- **Ecuaciones:** `wc=cp*(T2−T1)/1000`, `wt=cp*(T3−T4)/1000`, `wn=wt−wc`, `qin=cp*(T3−T2)/1000`, `η=wn/qin`.
- **Validación:** `cp>0` finito; temperaturas positivas y finitas; orden que permite los cuatro procesos; trabajos y calor finitos y estrictamente positivos; `0<η<1`.
- **Llama:** ninguna propia.
- **La llaman:** `calcular_ciclo_ideal`, `calcular_ciclo_noideal`, `calcular_trabajo_neto`, `calcular_entropias` y `main()`.
- **Ejemplo:** `calcular_balance_energetico(288.15, 556.3305505777084, 1600, 828.7159486769939, 1005)["trabajo_neto"]` → `505.619018...`.
- **Errores:** `ValueError` si el ciclo no es motor aunque las temperaturas sean positivas; posibles `TypeError` por tipos inadecuados. No comprueba por sí sola presiones, gas ideal ni isentropicidad.

### 4.5. `calcular_ciclo_ideal`, main.py:L96–107

```python
def calcular_ciclo_ideal(T1, T3, gamma, cp, relacion_presiones, p1):
```

- **Problema físico:** ofrecer una descripción agrupada del ciclo ideal para poder compararlo con el no ideal.
- **Entrada y tipos:** seis escalares: `T1`, `T3` [K], `cp` [J/(kg·K)], `p1` [kPa], `gamma` y `rp` [adimensionales].
- **Salida:** diccionario con `temperaturas` y `presiones` como tuplas, `T2s`, `T4s` [K], las cinco claves del balance y `back_work_ratio=wc/wt` adimensional. No devuelve volúmenes ni entropías, aunque los calcula indirectamente durante validaciones.
- **Ecuaciones:** combina temperaturas ideales, estados P-v y balance; en el ideal `T2s=T2` y `T4s=T4`.
- **Validación:** delegada íntegramente en las funciones de cálculo.
- **Llama:** `calcular_temperaturas`, `calcular_estados_pv`, `calcular_balance_energetico`.
- **La llaman:** `guardar_comparaciones_ciclos` y `main()`.
- **Ejemplo:** `calcular_ciclo_ideal(288.15, 1600, 1.4, 1005, 10, 100)["back_work_ratio"]` → `0.347706594...`.
- **Errores:** propaga las excepciones de sus tres funciones. El diccionario se devuelve solo si todas terminan correctamente.

### 4.6. `calcular_ciclo_noideal`, main.py:L110–146

```python
def calcular_ciclo_noideal(T1, T3, gamma, cp, relacion_presiones, p1,
                          eta_c, eta_t, perdida_presion_combustor):
```

- **Problema físico:** estimar las penalizaciones de compresor y turbina irreversibles y del combustor con caída de presión.
- **Entrada y tipos:** las seis magnitudes de §4.5 y tres escalares adimensionales: `eta_c`, `eta_t`, pérdida relativa `δ`.
- **Salida:** mismo esquema de diccionario que el ideal. Sus temperaturas son las reales simplificadas; sus `T2s` y `T4s` son referencias isentrópicas.
- **Ecuaciones:** `p2=p1*rp`, `p3=p2*(1−δ)`, `p4=p1`; `T2=T1+(T2s−T1)/eta_c`; `T4s=T3*(p4/p3)**a`; `T4=T3−eta_t*(T3−T4s)`; balance mediante `cp·ΔT`.
- **Validación:** `0<eta_c,eta_t<=1`; `0<=δ<1`; presión inicial y presiones derivadas positivas y finitas; `p3>p4`. Valida `gamma`, `rp`, temperaturas ideales de referencia y finalmente el balance real. No acepta trabajo neto nulo o negativo.
- **Llama:** `calcular_temperaturas`, `calcular_balance_energetico`.
- **La llaman:** `guardar_comparaciones_ciclos` y `main()`, incluido el caso límite.
- **Ejemplo:** `calcular_ciclo_noideal(288.15, 1600, 1.4, 1005, 10, 100, 0.85, 0.90, 0.05)["rendimiento"]` → `0.3689873237...`.
- **Errores:** `ValueError` por pérdidas o eficiencias inválidas, expansión imposible o balance no motor; propaga errores numéricos y de tipo. Una eficiencia válida por sí sola no garantiza que el conjunto forme un ciclo admisible.

### 4.7. `comprobar_comparacion_ciclos`, main.py:L149–170

```python
def comprobar_comparacion_ciclos(ideal, noideal, eta_c, eta_t, perdida_presion_combustor):
```

- **Problema físico:** verificar que los resultados respeten las tendencias esperadas y recuperen el ideal en el límite reversible.
- **Entrada y tipos:** dos diccionarios con el esquema de ciclo; tres escalares de pérdidas adimensionales coherentes con esos cálculos. Las unidades están dentro de los diccionarios.
- **Salida:** `None` si todo es coherente; no devuelve un booleano.
- **Relaciones comprobadas:** si `eta_c<1`, aumentan `T2` frente a `T2s` y `wc` frente al ideal; si `eta_t<1`, `T4>T4s`; las pérdidas de turbina o presión reducen `wt`; cualquier pérdida reduce el rendimiento. Sin pérdidas, temperaturas y balances deben coincidir dentro de tolerancias.
- **Validación:** compara resultados; no vuelve a validar exhaustivamente los parámetros ni todas las claves. Tampoco realiza una comprobación explícita de igualdad de las presiones en el límite reversible.
- **Llama:** ninguna propia; usa `np.allclose` e `isclose`.
- **La llaman:** `guardar_comparaciones_ciclos` y `main()`.
- **Ejemplo:** tras obtener `ideal` y `real` con las llamadas anteriores, `comprobar_comparacion_ciclos(ideal, real, 0.85, 0.90, 0.05)` termina sin valor visible.
- **Errores:** `ValueError` si falla una comparación; `KeyError` con claves ausentes, `IndexError` con temperaturas incompletas u otros errores si la estructura no es la esperada. Comparaciones estrictas pueden ser delicadas con pérdidas extremadamente pequeñas.

### 4.8. `guardar_comparaciones_ciclos`, main.py:L173–207

```python
def guardar_comparaciones_ciclos(T1, T3, gamma, cp, p1, eta_c, eta_t,
                                perdida_presion_combustor, imagenes):
```

- **Problema físico:** visualizar el efecto de `rp` en ambos modelos para una familia de ciclos.
- **Entrada y tipos:** escalares físicos con las unidades anteriores; `imagenes` es un diccionario mutable de nombres a buffers `BytesIO`; la función añade sus dos buffers al diccionario recibido.
- **Salida:** `None`; efecto: añade dos PNG nuevos en memoria al diccionario, bajo las claves `comparacion_ideal_noideal.png` y `trabajo_neto_ideal_noideal.png`.
- **Ecuaciones:** delegadas a los modelos; representa `100*η` y `wn` frente a 300 relaciones entre 2 y 30.
- **Validación:** cada punto atraviesa los dos modelos y la comparación. No comprueba anticipadamente que todo el intervalo sea válido. `main()` libera los buffers incluso ante fallos.
- **Llama:** `calcular_ciclo_ideal`, `calcular_ciclo_noideal`, `comprobar_comparacion_ciclos`.
- **La llaman:** `main()`.
- **Ejemplo en memoria:** `imagenes = {}`; `guardar_comparaciones_ciclos(288.15, 1600, 1.4, 1005, 100, 0.85, 0.90, 0.05, imagenes)`. Después se obtiene `imagenes["comparacion_ideal_noideal.png"].getvalue()` y se cierran ambos buffers.
- **Errores:** un rechazo numérico detiene el barrido y se envuelve como `ErrorModelo` indicando el intervalo fijo rp=2 a 30; los errores del dibujo se propagan aparte. No devuelve los arrays ni listas calculadas ni escribe archivos externos.

### 4.9. `calcular_trabajo_neto`, main.py:L210–213

```python
def calcular_trabajo_neto(T1, T3, gamma, cp, relacion_presiones):
```

- **Problema físico:** obtener solo el trabajo neto ideal para estudiar su dependencia con `rp`.
- **Entrada y tipos:** cinco escalares, temperaturas [K], `cp` [J/(kg·K)], `gamma` y `rp` adimensionales.
- **Salida:** escalar en kJ/kg.
- **Ecuaciones:** las temperaturas isentrópicas seguidas de `wt−wc`.
- **Validación:** delegada a temperaturas y balance.
- **Llama:** `calcular_temperaturas`, `calcular_balance_energetico`.
- **La llaman:** `buscar_optimo_numerico` y `main()`.
- **Ejemplo:** `calcular_trabajo_neto(288.15, 1600, 1.4, 1005, 10)` → `505.619018...`.
- **Errores:** propaga las excepciones de las funciones utilizadas. La selección `...["trabajo_neto"]` extrae un valor del diccionario temporal y devuelve ese valor.

### 4.10. `calcular_relacion_optima`, main.py:L216–225

```python
def calcular_relacion_optima(T1, T3, gamma):
```

- **Problema físico:** relación de presiones que maximiza el trabajo ideal con temperaturas extremas fijas.
- **Entrada y tipos:** escalares `T1`, `T3` [K] y `gamma` adimensional.
- **Salida:** escalar `rp_optima`, adimensional.
- **Ecuación:** `(T3/T1)**(gamma/(2*(gamma−1)))`. La derivación se desarrolla en §15.
- **Validación:** valida `gamma` llamando al rendimiento con una relación auxiliar igual a 2; exige temperaturas finitas con `T3>T1>0`; resultado finito y mayor que 1.
- **Llama:** `calcular_rendimiento`.
- **La llaman:** `main()`.
- **Ejemplo:** `calcular_relacion_optima(288.15, 1600, 1.4)` → `20.0852562921...`.
- **Errores:** `ValueError` para entradas/resultados no admisibles, posibles errores de tipo o desbordamiento. El 2 auxiliar no es una búsqueda ni una hipótesis sobre el óptimo.

### 4.11. `buscar_optimo_numerico`, main.py:L228–236

```python
def buscar_optimo_numerico(T1, T3, gamma, cp):
```

- **Problema físico:** contrastar el máximo ideal con una búsqueda discreta.
- **Entrada y tipos:** cuatro escalares con las unidades habituales. El intervalo y tamaño de malla están fijados dentro de la función.
- **Salida:** tupla `(relaciones, trabajos, indice_maximo)`: dos arrays NumPy de longitud 100001, adimensional y kJ/kg respectivamente, más un entero Python.
- **Método:** evalúa todos los puntos entre 1.01 y 50; toma el índice del mayor trabajo. No calcula derivadas ni interpola el máximo entre puntos.
- **Validación:** delegada por punto al cálculo de trabajo. No verifica por sí misma que el máximo continuo esté dentro del intervalo; principal lo hace después.
- **Llama:** `calcular_trabajo_neto`.
- **La llaman:** `main()`.
- **Ejemplo:** `relaciones, trabajos, indice = buscar_optimo_numerico(288.15, 1600, 1.4, 1005)`; `relaciones[indice]` → `20.0852363...`, con `indice=38937`.
- **Errores:** un solo punto inválido interrumpe toda la comprensión. Un máximo en un extremo no prueba que sea el máximo global del problema continuo.

### 4.12. `guardar_grafica_trabajo_neto`, main.py:L239–254

```python
def guardar_grafica_trabajo_neto(relaciones, trabajos, rp_optima, trabajo_maximo, ruta):
```

- **Problema físico:** representar el trabajo ideal y ubicar el máximo analítico suministrado.
- **Entrada y tipos:** dos secuencias numéricas de igual longitud, `rp_optima` adimensional, `trabajo_maximo` [kJ/kg] y destino `Path`, cadena o buffer binario aceptado por Matplotlib; `main()` usa `BytesIO`.
- **Salida:** `None`; guarda el PNG en el destino recibido: buffer en el flujo normal, archivo si se entrega una ruta.
- **Ecuaciones:** no calcula el ciclo ni verifica el máximo; representa datos ya obtenidos. La etiqueta de verificación se justifica por las comprobaciones previas de principal.
- **Validación:** ninguna física explícita dentro de esta función.
- **Llama:** ninguna propia.
- **La llaman:** `main()`.
- **Ejemplo con efecto en disco:** después de §4.11, `guardar_grafica_trabajo_neto(relaciones, trabajos, 20.085256292117077, 532.8022301186, Path("trabajo_ejemplo.png"))`.
- **Errores:** `ValueError` de Matplotlib si los tamaños son incompatibles, errores de tipo o de escritura. La función cierra la figura tras guardarla si la operación termina bien.

### 4.13. `calcular_entropias`, main.py:L257–270

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

### 4.14. `guardar_diagrama_ts`, main.py:L273–321

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

### 4.15. `comprobar_estados_pv`, main.py:L324–347

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

### 4.16. `calcular_estados_pv`, main.py:L350–360

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

### 4.17. `guardar_diagrama_pv`, main.py:L363–395

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

### 4.18. `guardar_grafica_rendimiento`, main.py:L398–412

```python
def guardar_grafica_rendimiento(gamma, ruta):
```

- **Propósito:** curva ideal antes dibujada al nivel del módulo. Conserva sus 100 puntos, ecuación y etiquetas; usa 9 × 6 pulgadas y 150 dpi, equivalentes a 1350 × 900 píxeles.
- **Argumentos/tipos/unidades:** `gamma` escalar adimensional; `ruta` buffer binario o ruta compatible con Matplotlib.
- **Salida:** `None`; PNG escrito en el destino. No calcula estados no ideales.
- **Validación/errores:** delega el dominio a `calcular_rendimiento`; propaga sus errores y los de Matplotlib/escritura.
- **Llama:** `calcular_rendimiento`; la llaman `main()` y la prueba de cambio de gamma.
- **PYTHON:** comprensión, array, `plt.figure`, formato PNG explícito y cierre.
- **Ejemplo:** `buffer = BytesIO()`; `guardar_grafica_rendimiento(1.4, buffer)`; `png = buffer.getvalue()`; `buffer.close()`.

### 4.19. `main`, main.py:L415–519

```python
def main(carpeta_salida=None, parametros=None):
```

- **Propósito:** coordina la ejecución completa; los nueve valores predeterminados están en la constante del módulo y pueden sustituirse desde el formulario.
- **Argumentos:** `carpeta_salida` es `Path`, cadena o `None`; `None` usa `outputs/` junto al script. `parametros` es un diccionario opcional con cualquiera de las nueve claves conocidas y unidades de §5. Las claves omitidas conservan sus valores predeterminados; la pérdida se recibe como fracción, no porcentaje. No se modifica el diccionario recibido ni la configuración predeterminada.
- **Salida:** `Path` al HTML completo; efectos: guardar, conservar cuatro y mostrar tres líneas.
- **Llama directamente:** rendimiento, temperaturas, balance, entropías, estados P-v, relación óptima, búsqueda numérica, trabajo neto, ambos ciclos, comprobación comparativa, cinco funciones gráficas `guardar_*`, tabla de rendimientos, `crear_informe_html`, `guardar_informe_html` y `obtener_version_git`.
- **La llaman:** punto de entrada protegido, ruta `index()` de Flask y pruebas de terminal/web.
- **Validación física:** las existentes de los modelos, igualdad de rendimientos y concordancia de óptimos. Registra mensajes después de superar comprobaciones.
- **Errores:** claves desconocidas producen `ValueError`. Solo los rechazos `ValueError`, `OverflowError` y `ZeroDivisionError` de la etapa numérica se envuelven como `ErrorModelo`; los fallos de dibujo/HTML/publicación se propagan sin etiquetarlos como inviabilidad física. La retención no empieza antes de publicar; sus fallos posteriores se advierten.
- **PYTHON:** copia y actualización de diccionarios, `.items()`, `any`, `try/except`, `raise ... from error`, `try/finally`, `is None` y retorno.
- **Ejemplo con escritura:** `ruta = main()` o `main(Path("outputs_prueba"), parametros={"T3": 1700})`; la carpeta alternativa tiene su propio historial. El primer argumento posicional sigue siendo la carpeta, conservando compatibilidad con las llamadas anteriores.

### 4.20. `tabla_html`, reporting.py:L36–43

```python
def tabla_html(encabezados, filas):
```

- **Propósito/interpretación:** presentar valores ya calculados, sin ecuaciones nuevas.
- **Argumentos:** iterable de encabezados e iterable de filas con valores ya formateados; unidades en etiquetas/celdas, sin conversiones aquí.
- **Retorno:** `str` con tabla y contenedor de desplazamiento horizontal.
- **Llama:** ninguna función propia; usa `str`, `escape` y `join`. La llaman `crear_informe_html` y la prueba de escape.
- **Validación/errores:** escapa texto HTML; no valida longitudes de filas ni física. Entradas no iterables pueden producir `TypeError`.
- **PYTHON:** generadores y concatenación.
- **Ejemplo:** `tabla_html(("T [K]",), [("288.15",)])`.

### 4.21. `imagen_html`, reporting.py:L46–55

```python
def imagen_html(imagen, titulo):
```

- **Propósito:** convertir PNG de esta ejecución en figura HTML autocontenida.
- **Argumentos:** `imagen`, bytes PNG sin unidad; `titulo`, cadena con significado físico y unidades cuando corresponda.
- **Retorno:** `str` con `figure`, `img`, `figcaption` y URL `data:image/png;base64,...`.
- **Validación/errores:** comprueba firma binaria PNG; `ValueError` si no coincide. No decodifica exhaustivamente los píxeles; las pruebas sí decodifican las seis imágenes.
- **Llama:** ninguna propia; usa `b64encode`, `.decode` y `escape`. La llaman `crear_informe_html` y la prueba de imagen inválida.
- **PYTHON:** literal de bytes, `.startswith`, conversión binario→texto. No cambia física ni comprime adicionalmente el PNG.
- **Ejemplo:** `imagen_html(buffer.getvalue(), "Diagrama T-s ideal")` con una gráfica recién dibujada.

### 4.22. `crear_informe_html`, reporting.py:L58–208

```python
def crear_informe_html(parametros, ideal, noideal, detalles_ideal, optimo,
                       rendimientos, comprobaciones, imagenes, fecha, version):
```

- **Propósito:** reunir secciones y seis imágenes en un HTML; no escribe ni recalcula el ciclo.
- **Argumentos:** cinco diccionarios físicos detallados en §5; `rendimientos`, lista de parejas `(rp, porcentaje)`; `comprobaciones`, lista de textos; `imagenes`, diccionario de seis claves con valores `bytes`; `fecha`, `datetime` con zona local; `version`, diccionario con `commit` (hash o `None`) y `modificado` (`True`, `False` o `None`).
- **Unidades:** las de §5; solo convierte fracciones a porcentaje al presentar. No modifica los diccionarios recibidos.
- **Retorno:** `str` HTML con CSS interno, UTF-8 declarado y marcas inicial/final.
- **Llama:** `tabla_html`, `imagen_html`. La llama `main()`; la prueba de integración intercepta esta llamada para contrastar bytes.
- **Validación/errores:** exige seis imágenes y valida sus firmas por delegación. Puede dar `ValueError`, `KeyError` o errores de tipo para datos incompletos. Las comprobaciones mostradas son las registradas por `main`, no verificaciones inventadas aquí.
- **PYTHON:** f-string multilínea, llaves dobles de CSS, `join`, generadores y `strftime`.
- **Ejemplo de contrato:** `crear_informe_html(parametros, ciclo_ideal, ciclo_noideal, detalles_ideal, optimo, calcular_rendimientos(gamma), comprobaciones, pngs, fecha, version)`, con los datos reunidos por `main`; `pngs` representa bytes, no rutas a archivos históricos.

### 4.23. `guardar_informe_html`, reporting.py:L211–251

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

### 4.24. `obtener_version_git`, reporting.py:L19–33

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

### 4.26. `valores_formulario`, web_app.py:L34–38

```python
def valores_formulario():
```

- **Propósito:** preparar valores para GET sin modificar la constante del simulador; no calcula estados.
- **Argumentos:** ninguno. **Retorno:** diccionario con las nueve claves; unidades de §5 salvo pérdida expresada en %.
- **Llama:** ninguna función propia; usa `.copy()` y multiplica la pérdida por 100. La llaman `index`, `error_interno` y las pruebas de formulario/conversión.
- **Validación/errores:** no valida: parte de la configuración conocida. Una clave ausente en esa configuración sería un error de programación, no una entrada inviable.
- **PYTHON:** copia superficial suficiente para valores numéricos; `*=` actualiza solo la copia.
- **Ejemplo:** `valores_formulario()["perdida_presion_combustor"]` devuelve `5.0`.

### 4.27. `leer_parametros`, web_app.py:L41–67

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

### 4.28. `index`, web_app.py:L71–84

```python
def index():
```

- **Propósito:** atender GET/POST de `/`. No recibe argumentos posicionales; obtiene método y formulario del contexto HTTP.
- **Retorno:** para GET, pareja `(HTML, 200)`; ante entradas inválidas/modelo rechazado, `(HTML, 400)`; con éxito, respuesta de redirección HTTP 303 al informe recién creado.
- **Llama:** `valores_formulario`, `leer_parametros`, `main`. Flask la llama por el decorador de ruta; las pruebas lo hacen mediante `test_client`.
- **Unidades:** respeta el contrato de `leer_parametros`; no calcula ecuaciones.
- **Validación/errores:** no invoca `main` si hay errores de campos. Captura únicamente `ErrorModelo` durante la ejecución; conserva `request.form.to_dict()` para volver a mostrar valores. Otros errores llegan al tratamiento de HTTP 500 de Flask.
- **PYTHON:** decorador `@app.route("/", methods=["GET", "POST"])`, condicionales y `try/except/else`. Ese `else` se ejecuta solo si la llamada no lanzó una excepción.
- **Ejemplo:** `client.get("/")` muestra el formulario; `client.post("/", data=datos)` simula un envío en una prueba. Fuera de una petición no se llama manualmente a `index()`.

### 4.29. `ver_informe`, web_app.py:L88–113

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
- **INTERPRETACIÓN FÍSICA:** no recalcula; sirve exactamente la ejecución guardada. `reporting.py` permanece sin cambios en esta tarea.

### 4.30. `error_interno`, web_app.py:L117–123

```python
def error_interno(error):
```

- **Propósito:** presentar un fallo inesperado sin exponer trazas al navegador ni llamarlo inviabilidad física.
- **Argumento:** excepción HTTP 500 que entrega Flask; sin unidad física. **Retorno:** formulario HTML y estado 500.
- **Llama:** `valores_formulario` cuando no es un POST; Flask llama a este manejador, registrado con `@app.errorhandler(500)`.
- **Comportamiento:** Flask ya registra el traceback en terminal. La respuesta dice que es un error interno y conserva las entradas POST si existen. No se genera un informe nuevo desde este manejador.
- **PYTHON:** decorador de errores, renderizado de plantilla y expresión condicional. No se captura todo como `ErrorModelo`.
- **Ejemplo:** la prueba sustituye una función de dibujo por una que falla; `client.post` recibe 500 mientras el registro conserva el detalle técnico.

### 4.31. `iniciar_servidor`, web_app.py:L126–128

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
    """El caso o alguno de los estudios fijos no es admisible para el modelo."""
```

Hereda de `ValueError`, por eso los usos anteriores que esperan ese tipo siguen reconociéndola. No define métodos propios ni cambia ecuaciones. `main` la lanza al envolver rechazos en su etapa numérica y `guardar_comparaciones_ciclos` al rechazarse un punto de su barrido numérico; Flask la captura como error esperado del modelo. `raise ErrorModelo(...) from error` conserva la excepción original como causa para depurar en terminal. Las excepciones de dibujo, HTML o escritura no se envuelven como un error físico.

### Métodos de `WebTests` — tests/test_web_app.py

Todos reciben `self`, devuelven `None` y no añaden ecuaciones ni unidades. El ejecutor `unittest` los llama; las aserciones pueden fallar con `AssertionError`. `setUp` se ejecuta antes de cada prueba y registra limpiezas con `addCleanup`.

| Firma | Propósito y llamadas principales |
|---|---|
| `setUp(self)` | Crea carpeta temporal, sustituye `OUTPUTS_DIR` con `patch.dict`, crea `test_client` y datos de formulario |
| `test_formulario_predeterminados_y_restablecer(self)` | GET del formulario y CSS; comprueba nueve campos y ausencia de simulación |
| `test_validacion_de_todos_los_campos_sin_informes(self)` | POST con vacíos, no números, no finitos y límites inválidos; exige que `main` no se llame |
| `test_conversion_porcentaje_y_limites_admitidos(self)` | Llama a `leer_parametros` con pérdidas cero y 5 %, y eficiencias unidad |
| `test_referencia_y_otro_caso_con_seis_imagenes_actuales(self)` | Envía dos casos reales; compara resultados y bytes de las seis imágenes, vista y descarga |
| `test_cinco_ejecuciones_mezcladas_terminal_web(self)` | Alterna `main` y POST cinco veces; conserva cuatro y devuelve 404 para el eliminado |
| `test_casos_no_admisibles_conservan_datos_e_historial(self)` | Envía T3 baja e insuficiente para estudios fijos; comprueba errores y archivos intactos |
| `test_error_inesperado_se_registra_y_no_se_presenta_como_fisico(self)` | Inyecta fallo de dibujo; exige 500, registro de traza y ausencia de detalle privado en respuesta |
| `test_no_se_exponen_archivos_ajenos_o_rutas_locales(self)` | GET de rutas y archivos no autorizados; espera 404 |
| `test_servidor_se_configura_solo_para_loopback_sin_debug(self)` | Sustituye `app.run`, llama a `iniciar_servidor` y verifica sus opciones |
| `test_importar_modulos_no_ejecuta_ni_escucha(self)` | Importa módulos en un proceso Python aparte y prohíbe generar informes o arrancar servidor |
| `test_main_directo_con_valores_predeterminados(self)` | Ejecuta el punto de entrada mediante `runpy`, sustituyendo solo destino de prueba; comprueba resumen y referencia |

El pequeño helper `guardar_en_prueba(contenido, carpeta, fecha)` del proceso de esa última prueba conserva la firma del guardado, devuelve su ruta y llama a `reporting.guardar_informe_html` con carpeta temporal. No participa en el programa normal ni modifica cálculos.

**Ejemplo de todas las pruebas:** `python -B -m unittest discover -s tests -v`. Las comprobaciones web no necesitan navegador ni puerto abierto, porque `test_client` despacha las peticiones dentro de Flask.

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
| `factor` | Factor térmico isentrópico | — | escalar |
| `T2`, `T4`, `T2s`, `T4s`, `T2_real`, `T4_real` | Salidas y referencias isentrópicas | K | escalar |
| `temperaturas`, `temperaturas_reales`, `temperaturas_optimas` | Estados ordenados 1,2,3,4 | K | `tuple` |
| `presiones`, `presiones_reales`, `p2`, `p3`, `p4` | Presiones | kPa | tupla/escalares |
| `R` | Constante específica del gas | J/(kg·K) | escalar |
| `volumenes`, `v1`, `v2`, `v3`, `v4` | Volúmenes específicos ideales | m³/kg | tupla/escalares |
| `cp_kj` | `cp/1000` | kJ/(kg·K) | escalar |
| `s1`, `s2`, `s3`, `s4`, `entropias` | Entropías relativas ideales | kJ/(kg·K) | escalares/tupla |
| `incremento_23`, `incremento_14` | Saltos positivos de entropía | kJ/(kg·K) | escalares |
| `trabajo_compresor`, `trabajo_turbina`, `trabajo_neto`, `calor_aportado` | Energías específicas | kJ/kg | escalares |
| `rendimiento`, `rendimiento_balance`, `rendimiento_optimo` | Eficiencias fraccionarias | — | escalares |
| `back_work_ratio` | Clave con `wc/wt` | — | escalar |
| `rendimientos_porcentaje` | Eficiencias de la curva | % | `ndarray` |
| `balance`, `balance_optimo`, `balance_real` | Energías y rendimiento | varias | `dict` |
| `ciclo_ideal`, `ciclo_noideal`, `ciclo_limite_ideal` | Estados y balances | varias | `dict` |
| `rp_optima_analitica`, `rp_optima_numerica` | Relaciones del máximo trabajo | — | escalar |
| `trabajo_maximo` | Trabajo en el óptimo analítico | kJ/kg | escalar |

### Auxiliares numéricas, gráficas y de informe

| Nombre real | Función | Tipo y unidad |
|---|---|---|
| `relaciones`, `relaciones_presiones`, `relaciones_busqueda` | Mallas de `rp` | arrays adimensionales |
| `trabajos`, `trabajos_busqueda` | Trabajos en la malla | arrays, kJ/kg |
| `indice_maximo`, `indice_optimo` | Posición del máximo | `int`, sin unidad |
| `paso_busqueda` | Separación entre puntos | `float`, adimensional |
| `ciclos_ideales`, `ciclos_noideales` | Barrido comparativo | listas de diccionarios |
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
| `optimo` | `rp_analitica`, `rp_numerica`, `paso`, `trabajo_analitico`, `trabajo_numerico`, `temperaturas`, `rendimiento` | `dict`, unidades anteriores |
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

`Path` aparece en ambos módulos. `as np` y `as plt` son aliases. `import re` deja un módulo y exige `re.compile(...)`; `from html import escape` deja directamente `escape(...)`. Los módulos estándar acompañan a Python; no se instalan con pip.

Se añade Flask a NumPy y Matplotlib. Flask instala sus dependencias necesarias (Werkzeug, Jinja2, MarkupSafe, Click, ItsDangerous y Blinker); no hay frameworks frontend. Una vez instaladas, el servidor y los informes funcionan sin Internet.

### Imports de Flask

`from flask import Flask, Response, abort, redirect, render_template, request, url_for` incorpora la aplicación, respuesta HTTP, errores de ruta, redirecciones, renderizado Jinja, petición actual y construcción de URLs. `request` representa la petición activa: se consulta dentro de las rutas, no al importar el módulo.

`web_app.py` importa `main`, sus parámetros predeterminados y `ErrorModelo`; también las marcas y patrón de informes de `reporting`. No copia las ecuaciones. En las nuevas pruebas `sys.executable` identifica el intérprete actual y `runpy.run_path` ejecuta el punto de entrada en un proceso aislado de prueba.

### Imports de las pruebas

`unittest` aporta pruebas y aserciones; `unittest.mock.patch` sustituye temporalmente operaciones para simular fallos; `tempfile` aísla archivos; `redirect_stdout` y `StringIO` capturan terminal; `HTMLParser` inspecciona etiquetas; `b64decode` comprueba la codificación; `sha256` compara los PNG históricos; `matplotlib.image` decodifica imágenes. También se importan fechas, zona UTC, rutas y bytes en memoria, y los módulos propios `main` y `reporting`.

Estas herramientas verifican implementación, almacenamiento y rutas HTTP, no datos experimentales del modelo.

## 7. NumPy: uso real

### `np.linspace(inicio, fin, numero)`

Se usa en `guardar_comparaciones_ciclos`, `buscar_optimo_numerico`, `guardar_diagrama_ts`, `guardar_diagrama_pv` y `guardar_grafica_rendimiento`. Produce muestras uniformes e incluye ambos extremos con los argumentos usados.

```python
np.linspace(2, 6, 3)  # array([2., 4., 6.])
```

El tercer argumento es el **número de puntos**, no el paso. En la búsqueda del óptimo:

```text
paso = (50 - 1.01) / (100001 - 1) = 0.0004899
```

`np.linspace(T4, T1, 100)` también funciona si el extremo final es menor: genera una secuencia descendente y respeta el recorrido del enfriamiento.

### `np.array(...)`

Se usa en `buscar_optimo_numerico` y `guardar_grafica_rendimiento`. Convierte una lista en un array. En el código, primero se ejecuta una comprensión Python y después NumPy recibe la lista resultante.

```python
rendimientos_porcentaje = np.array([
    calcular_rendimiento(gamma, relacion) * 100
    for relacion in relaciones_presiones
])
```

**PYTHON.** `[` abre la comprensión. Su expresión es la llamada multiplicada por 100. El `for` asigna cada elemento del iterable a `relacion`. `]` termina la lista; `)` termina la llamada a `np.array`. No es una función nueva ni una llamada simultánea del modelo para todo el array.

### Indexación y `np.argmax`

`buscar_optimo_numerico` y `main`:

```python
indice_maximo = int(np.argmax(trabajos))
```

`np.argmax` retorna la posición del primer máximo si hay empate. El índice 0 corresponde al primer elemento. Con ese mismo índice, `relaciones[indice_maximo]` y `trabajos[indice_maximo]` seleccionan un punto de la curva. El máximo numérico actual tiene índice 38937. No se utiliza `np.max` en el código.

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

No aparecen matrices multidimensionales, álgebra lineal, integración numérica ni algoritmos de optimización de NumPy. La búsqueda es una evaluación exhaustiva de una malla de una dimensión.

## 8. Matplotlib

### Figuras y ejes

**PYTHON.** `Figure` es el contenedor completo; `Axes` es el área donde se representan coordenadas. Aunque la variable se llame `ejes`, en estas llamadas representa **un solo objeto `Axes`**, porque `plt.subplots(figsize=(9, 6))` no solicita varias filas ni columnas.

```python
figura, ejes = plt.subplots(figsize=(9, 6))
ejes.plot(relaciones, trabajos, label="Trabajo específico neto")
```

`figsize=(9,6)` expresa tamaño en pulgadas. Las funciones gráficas propias usan este estilo de objetos. La función `guardar_grafica_rendimiento` utiliza el estado actual de `plt`:

```python
plt.figure(figsize=(9, 6))
plt.plot(relaciones_presiones, rendimientos_porcentaje)
```

Ambas formas pertenecen a la misma biblioteca, pero la segunda depende de cuál sea la figura activa.

### Operaciones que aparecen

| Operación real | Función en el simulador |
|---|---|
| `plt.figure(figsize=(9, 6))` | Crea la figura de rendimiento con el mismo tamaño que las demás |
| `plt.subplots(...)` | Crea contenedor y área de dibujo juntos |
| `plot(x,y,...)` | Une puntos de curvas y procesos; devuelve una lista de líneas |
| `scatter(x,y,...)` | Marca estados y máximo como puntos |
| `plt.title`, `ejes.set_title` | Títulos |
| `plt.xlabel`, `ejes.set_xlabel` | Nombre y unidad del eje horizontal |
| `plt.ylabel`, `ejes.set_ylabel` | Nombre y unidad del eje vertical |
| `grid(True)` | Cuadrícula |
| `legend(...)` | Leyenda a partir de los `label` de las series |
| `annotate(...)` | Números de estado, texto del máximo o flechas |
| `margins(x=...,y=...)` | Añade espacio proporcional alrededor de los datos |
| `tight_layout()` | Ajusta espacios entre elementos para reducir recortes |
| `savefig(...)` | Escribe la imagen |
| `plt.close(...)` | Cierra y libera el registro de la figura |

`label=` nombra una serie, pero no dibuja por sí solo la caja de leyenda. La primera curva de rendimiento no llama a `legend`; las funciones de los otros gráficos sí.

### Puntos, anotaciones y flechas

`color="black"` selecciona negro, `s=70` fija el área del marcador en puntos cuadrados y `zorder=5` lo coloca por encima de elementos con menor prioridad de dibujo.

En `annotate`, `xy` es la posición señalada. `xytext` indica dónde empieza el texto o flecha; con `textcoords="offset points"`, la posición del texto es un desplazamiento en puntos tipográficos desde `xy`. No son unidades de temperatura o presión. Sin ese ajuste, las flechas de los procesos usan las coordenadas de datos. `arrowprops` contiene estilo, color y anchura `lw`.

```python
linea, = ejes.plot(valores_s, valores_T, label=etiqueta)
```

El resultado de `plot` es una lista con una línea en este caso. La coma en `linea,` pide exactamente un elemento y asigna ese objeto. Así `linea.get_color()` recupera el color de la curva y la flecha coincide con ella.

**INTERPRETACIÓN FÍSICA.** Las flechas muestran el sentido del ciclo. Las isóbaras T-s se curvan por la relación logarítmica; las isentrópicas P-v se curvan por la potencia `gamma`. No se unen indiscriminadamente los cuatro estados con segmentos rectos.

### Guardado y cierre

Las seis gráficas usan 9 × 6 pulgadas y `dpi=150`: 1350 × 900 píxeles. Las pulgadas fijan el tamaño de la figura y dpi los píxeles por pulgada; el tamaño mostrado en pantalla lo adapta el CSS sin reducir los píxeles originales. `savefig(..., format="png")` escribe ahora en buffers `BytesIO`: el flujo normal no crea ni sobrescribe PNG. `plt.close()` cierra la figura actual; `plt.close(figura)` cierra la indicada. Si se entrega explícitamente una ruta a una función gráfica que la admite, todavía se puede guardar un PNG; es un uso opcional distinto de `main()`.

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

Desde el terminal de VS Code situado en la raíz:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe web_app.py
```

Abre `http://127.0.0.1:5000` en Chrome o Edge. Con el entorno activado bastan `python web_app.py` y, para la modalidad anterior, `python main.py`. Ctrl+C detiene el servidor. Si no está activo, la URL local no responde. No se abre el navegador automáticamente y no hay instalación ni despliegue en Internet. La instalación inicial de dependencias sí requiere paquetes disponibles localmente o conexión para descargarlos.

**HTTP GET:** solicita una representación, por ejemplo el formulario o un informe guardado. No ejecuta una simulación al visitar `/`. **HTTP POST:** envía los campos mediante el cuerpo de la petición para ejecutar un caso. Los valores llegan como cadenas, aunque el navegador dibuje controles numéricos.

```text
GET / → valores_formulario → render_template → formulario
POST / → request.form → leer_parametros
                         ├─ errores de campos → formulario + 400
                         └─ números válidos → main(parametros=...)
                                               ├─ ErrorModelo → formulario + 400
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

`data:` indica contenido dentro de la propia URL; `image/png`, el formato; `base64`, la codificación. Los puntos suspensivos de este ejemplo se sustituyen por todos los datos en el HTML real. Base64 aumenta el tamaño aproximadamente un tercio. No es cifrado ni compresión; permite trasladar un único archivo sin seis PNG externos.

**INTERPRETACIÓN FÍSICA.** Los dibujos proceden de estados y arrays de esa ejecución, nunca de los PNG históricos. El formato no añade fidelidad física.

### Publicar antes de limpiar

1. Terminan cálculos, comprobaciones y seis gráficas; todo el HTML se construye en memoria.
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

**PYTHON.** `ValueError` es un tipo de excepción. `ValueError("mensaje")` construye un objeto con una explicación; `raise` lo lanza. La llamada actual se interrumpe y la excepción asciende por las funciones que la invocaron. Las 13 funciones físicas siguen lanzando sus errores originales. `main()` envuelve los rechazos de su etapa numérica como `ErrorModelo` y usa `finally` para liberar gráficos y buffers; en terminal se conserva el traceback. El guardado limpia temporales y captura fallos de retención posteriores a la publicación para emitir una advertencia. Un `return` normal no produce ese comportamiento.

Hay validaciones antes de hacer operaciones peligrosas: `gamma>1` evita denominadores problemáticos y un modelo fuera de dominio; temperaturas positivas permiten logaritmos de razones positivas; presión y eficiencia positivas evitan divisiones físicamente inadmisibles. No es un sistema completo de comprobación de tipos. Por ejemplo, `isfinite("frío")` puede lanzar `TypeError` antes de que el código alcance su propio `raise ValueError`.

### Entradas del formulario frente a errores del programa

El servidor distingue campos vacíos, texto no numérico, NaN/infinito y rangos individuales inválidos con mensajes junto a cada campo. Conserva los valores POST y no llama al simulador mientras exista un error. Un dato individual válido no garantiza que se complete un caso: los estudios fijos de 100001 y 300 puntos pueden rechazar combinaciones que sí funcionen en la relación de presiones de referencia.

`ErrorModelo` recoge esos rechazos numéricos en puntos de cálculo concretos, sin modificar las 13 funciones originales. La web responde 400 y muestra la causa. Un error de dibujo, HTML, acceso a disco o programación no se presenta como inviabilidad: Flask lo registra con traceback y responde 500 con un mensaje genérico. La prueba provoca expresamente un `ValueError` de dibujo para verificar esta separación.

No se implementa una búsqueda de dominio viable, filtrado de puntos ni una recomendación automática de rangos. Antes de publicar el HTML no se elimina ningún informe. Los fallos de retención posteriores conservan su semántica de advertencia del sistema anterior.

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

En algunas verificaciones P-v solo se especifica `rel_tol`: allí sigue vigente el valor por defecto de `abs_tol`, que es cero. En el máximo se fuerza `rel_tol=0` y el margen absoluto es el paso de malla. El redondeo de pantalla se hace después; no se comparan cadenas con dos decimales.

### Cuatro situaciones diferentes

| Categoría | Ejemplo relacionado con el código | Qué significa |
|---|---|---|
| Error de programación | Consultar `balance["trabajo"]` cuando la clave real es `"trabajo_neto"` | El contrato del código se ha usado mal; puede dar `KeyError` |
| Entrada inválida | `eta_c=0`, `gamma=1`, `p1=-100` | El modelo no admite ese dato; se lanza `ValueError` |
| Resultado no admisible para este simulador | Temperaturas positivas pero `wt<=wc` | Puede describir condiciones fuera del régimen motor; el programa las rechaza |
| Error/efecto numérico | Pequeña diferencia entre dos rendimientos, o desbordamiento para potencias extremas | La representación tiene límites; las tolerancias cubren diferencias pequeñas, no desbordamientos arbitrarios |

Un trabajo negativo no es imposible en toda la termodinámica: significa que ese conjunto no corresponde al ciclo motor que este programa acepta. Tampoco una excepción garantiza que el usuario se haya equivocado: puede revelar un error en una ecuación, un dato incoherente o un contrato mal utilizado.

Las comprobaciones de ejecución no demuestran todos los casos posibles. Ahora existe además `tests/test_reporting.py`, con 22 pruebas independientes ejecutables mediante `python -B -m unittest discover -s tests -v`.

Verifican referencias numéricas, cinco simulaciones que dejan cuatro informes propios, seis PNG decodificables e idénticos a los bytes de la ejecución, ausencia de recursos externos, archivos ajenos y PNG históricos intactos, fallo de cálculo/publicación, colisiones de HTML/temporal, escape HTML, cambio gráfico con gamma, dimensiones exactas de las seis imágenes y metadatos Git limpios, modificados o desconocidos. Se usan carpetas temporales para no consumir el historial de `outputs/`.

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
| `except ErrorModelo`, `raise ... from error` | Captura específica y causa original conservada | Flask y coordinación |
| `.to_dict()`, `.get()` | Conservar texto y consultar campos con defecto | Petición y plantilla |
| Tupla `(html, estado)` | Cuerpo y código HTTP para Flask | Formulario/error |
| `try/except/else` | Redirigir solo cuando la llamada fue satisfactoria | `index` |

### Conceptos que aún no necesitas dominar profundamente

- Backend Agg, internals de arrays y renderizado de Matplotlib.
- Precisión binaria: entender tolerancias sin implementar la aritmética.
- UUID: entender su finalidad sin programar su generación.
- Herencia de clases de prueba: `class InformeParser(HTMLParser)` redefine un método; `class InformesTests(unittest.TestCase)` agrupa pruebas. `self` es la instancia y `super().__init__()` inicializa la parte heredada. El cálculo físico no introduce clases propias.
- Callbacks del parser: `feed` invoca `handle_starttag` al encontrar una etiqueta. `patch` cambia una operación durante el contexto de prueba, sin editar el modelo.

No hay `while`, división entera `//` ni parámetros declarados como `*args` o `**kwargs`. `in` se usa para iterar y en las pruebas como pertenencia a una tupla de atributos.

## 12. Flujo completo de una ejecución

1. Ejecutas `python main.py`. Se importan biblioteca estándar, módulo `reporting`, NumPy y Matplotlib. Agg se selecciona antes de `pyplot`.
2. Python crea funciones con `def`, sin ejecutar sus cuerpos. Cargar `reporting` tampoco guarda archivos.
3. `if __name__ == "__main__":` llama a `main()` al ejecutar el script. Con `import main` no se cumple: no empieza una simulación.
4. `main` captura fecha y zona del equipo con `datetime.now().astimezone()`. Esa fecha identifica el inicio de ejecución. Consulta también el commit y estado local de Git. Copia `PARAMETROS_PREDETERMINADOS`, valida las claves y aplica el diccionario opcional de entrada; después asigna los nombres físicos locales.
5. Calcula rendimiento, temperaturas, balance, entropías, R, presiones y volúmenes ideales. `T2≈556.33 K`, `T4≈828.72 K`, `wn≈505.619018 kJ/kg`.
6. Valida estados y balances; registra mensajes de los grupos de comprobaciones que han terminado. Compara rendimiento de fórmula y balance sin redondear.
7. Calcula óptimo analítico `rp≈20.0852562921`; evalúa 100001 relaciones y obtiene índice 38937, `rp≈20.0852363`.
8. Comprueba intervalo y concordancia dentro del paso `≈0.0004899`. Obtiene `T2=T4≈678.999264 K` y `wn≈532.802230 kJ/kg` en el óptimo.
9. Calcula diccionarios ideal, no ideal y límite reversible. Contrasta tendencias con pérdidas y recuperación del ideal con eficiencias unidad y pérdida cero.
10. Crea cuatro buffers `BytesIO` y dibuja rendimiento, T-s, P-v y trabajo exclusivamente ideales.
11. El barrido comparativo calcula y comprueba 300 pares de ciclos y añade dos buffers. Solo al terminar se registra esa comprobación.
12. Reúne `detalles_ideal` y `optimo`. Una comprensión sobre `.items()` obtiene bytes de las seis imágenes. Calcula la tabla de cinco rendimientos con la función existente.
13. `crear_informe_html` forma tablas, convierte PNG a Base64 y retorna HTML con CSS, commit, aviso de estado Git y marcas completas. No se ha publicado todavía ningún informe.
14. `finally` cierra buffers y figuras también si falla dibujo/HTML. El texto generado ya contiene los bytes codificados y no necesita mantener abiertos los buffers.
15. Elige `outputs/` junto al script, o la carpeta alternativa de pruebas. El guardado crea la carpeta si hace falta.
16. Escribe UTF-8 en un temporal abierto con `"x"`; tras cerrarlo lo renombra a HTML final. Si falla esta etapa, propaga el error sin limpiar el historial.
17. Filtra informes propios completos, ordena por fecha de finalización de escritura y elimina los que exceden cuatro. Archivos ajenos y PNG quedan fuera. Una limpieza fallida después de publicar produce advertencia.
18. Muestra tres líneas: ejecución completada, ruta absoluta y seis gráficas incorporadas. Devuelve la ruta y termina; las tablas se consultan en el HTML.

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

**INTERPRETACIÓN FÍSICA.** Con `rp=10` y `gamma=1.4`, se define `a=(gamma−1)/gamma≈0.285714286` para explicar la ecuación. El código no almacena una variable llamada `a`.

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

**PYTHON.** `wc`, `wt`, `wn`, `qin` y `η` son abreviaturas de esta explicación. Los nombres reales dentro de la función son `trabajo_compresor`, `trabajo_turbina`, `trabajo_neto`, `calor_aportado` y `rendimiento_balance`. Se construye un diccionario y se devuelve. `crear_informe_html` selecciona `"trabajo_neto"` del ciclo y usa `:.6f` en la tabla. El cálculo conserva su precisión; solo cambia el texto presentado.

### El mismo resultado en otros caminos

En `calcular_trabajo_neto`, las temperaturas se guardan como una tupla local y se pasan mediante `*temperaturas`. El resultado del balance se indexa directamente y solo se devuelve el trabajo. Ese camino se repite en la búsqueda numérica.

En `calcular_ciclo_ideal`, las temperaturas y el balance se agrupan con presiones en otro diccionario. Por eso `ciclo_ideal["trabajo_neto"]` contiene el mismo valor que `balance["trabajo_neto"]` para el mismo caso, aunque los cálculos se hayan repetido.

### Comparación con el no ideal

La función `calcular_ciclo_noideal` utiliza `T2s≈556.330551 K`, pero con `eta_c=0.85` obtiene `T2_real≈603.656530 K`. La pérdida de presión deja `p3=950 kPa`, frente a `p4=100 kPa`, de modo que `T4s≈840.950399 K`. Con `eta_t=0.90`, `T4_real≈916.855359 K`.

El mismo balance recibe ahora esas temperaturas y devuelve `wc≈317.084063`, `wt≈686.560364`, `wn≈369.476301 kJ/kg`. No se aplica simplemente un factor al trabajo ideal: se reconstruyen los estados, los dos trabajos y el calor aportado. El rendimiento real resulta `36.898732 %`.

## 14. Relación entre código y ecuaciones

Notación de esta tabla: `rp=p2/p1`, `a=(gamma−1)/gamma`, `δ=perdida_presion_combustor`. `a` y `δ` son abreviaturas explicativas; los nombres Python reales se conservan en las funciones.

| Concepto físico | Ecuación | Función Python |
|---|---|---|
| Rendimiento ideal | `η=1−rp^(−a)` | `calcular_rendimiento` |
| Compresión ideal | `T2=T1·rp^a` | `calcular_temperaturas` |
| Expansión ideal | `T4=T3/rp^a` | `calcular_temperaturas` |
| Trabajo consumido por compresor | `wc=cp(T2−T1)/1000` | `calcular_balance_energetico` |
| Trabajo producido por turbina | `wt=cp(T3−T4)/1000` | `calcular_balance_energetico` |
| Trabajo específico neto | `wn=wt−wc` | `calcular_balance_energetico`, extraído por `calcular_trabajo_neto` |
| Calor específico aportado | `qin=cp(T3−T2)/1000` | `calcular_balance_energetico` |
| Rendimiento por balance | `η=wn/qin` | `calcular_balance_energetico` |
| Fracción de trabajo para compresor | `BWR=wc/wt` | `calcular_ciclo_ideal`, `calcular_ciclo_noideal` |
| Eficiencia de compresor | `eta_c=(T2s−T1)/(T2_real−T1)` | Despejada para `T2_real` en `calcular_ciclo_noideal` |
| Presión tras el combustor | `p3=p1·rp·(1−δ)` | `calcular_ciclo_noideal` |
| Referencia isentrópica de turbina real | `T4s=T3(p4/p3)^a` | `calcular_ciclo_noideal` |
| Eficiencia de turbina | `eta_t=(T3−T4_real)/(T3−T4s)` | Despejada para `T4_real` en `calcular_ciclo_noideal` |
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

**INTERPRETACIÓN FÍSICA.** Encontrar el mayor de 100001 valores significa localizar el mejor punto de esa malla, no resolver exactamente la derivada. Se acepta una diferencia de un paso respecto a la solución analítica. La malla no convierte el modelo en más realista; solo aproxima una búsqueda dentro del mismo modelo ideal.

### 15.6. Derivación del óptimo de trabajo

**INTERPRETACIÓN FÍSICA.** Definimos solo para el razonamiento `x=rp^((gamma−1)/gamma)` y `c=cp/1000`. Con las temperaturas ideales:

```text
wn = c [T3(1−1/x) − T1(x−1)]
dwn/dx = c(T3/x² − T1)
d²wn/dx² = −2cT3/x³ < 0
```

La primera derivada es cero para `x=sqrt(T3/T1)` y la segunda es negativa: hay un máximo. Despejando `rp` resulta la expresión de `calcular_relacion_optima`. Como `c` es un factor positivo, el óptimo no depende de su valor. `p1` tampoco aparece: para este modelo las temperaturas dependen de cocientes de presión.

En ese punto, `T2=T1*sqrt(T3/T1)=sqrt(T1*T3)` y `T4=T3/sqrt(T3/T1)=sqrt(T1*T3)`. Que ambas temperaturas sean iguales **no** anula el aporte de calor, porque este depende de `T3−T2`, no de `T4−T2`.

El rendimiento ideal `1−1/x` crece con `x`. Su máximo no coincide con el máximo de trabajo. Al acercarse al límite `T2=T3`, desaparecen el calor aportado y el trabajo, y el código rechaza ese punto. Para los parámetros actuales el límite ideal es aproximadamente `rp=403.417520`, muy por encima de los intervalos usados.

**PYTHON.** La fórmula se evalúa con `**` y paréntesis; no hay una biblioteca de derivación simbólica. El barrido verifica esa fórmula numéricamente para el caso actual.

### 15.7. Referencias isentrópicas del no ideal

**INTERPRETACIÓN FÍSICA.** `T2s` describe una compresión reversible con las mismas presiones extremas del compresor real. Al dividir el incremento isentrópico entre `eta_c<1`, se obtiene un incremento real mayor.

Para la turbina, la presión inicial real es `p3=950 kPa`, no `1000 kPa`. Así su `T4s` es mayor que el del ideal incluso antes de introducir `eta_t<1`. Después, multiplicar el salto disponible por `eta_t` reduce la caída real de temperatura y hace subir todavía más `T4_real`.

**PYTHON.** La función mantiene `presiones_reales` y `temperaturas_reales` en tuplas locales y las devuelve en un diccionario separado. No modifica las tuplas del ideal. No calcula ni dibuja entropías no ideales.

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
| Intervalos fijos sin captura de puntos no motores | Otros parámetros pueden detener un barrido; no se ha implementado dominio viable |
| API Python de `main` y contratos internos sin comprobación exhaustiva de tipos | La web valida sus campos; una llamada Python manual mal estructurada aún puede producir `TypeError` o `KeyError` |
| Retención por fecha de modificación y marcas | Editar informes cambia su orden; imitar deliberadamente formato y marcas los hace indistinguibles de un informe propio |
| Limpieza sin bloqueo multiproceso | Procesos simultáneos podrían interferir en la retención |
| Permisos o errores durante limpieza | Pueden quedar más de cuatro informes, con advertencia explícita |

### MEJORA OPCIONAL

- Reducir cálculos y validaciones repetidos entre estados, entropías y balance.
- Separar en el futuro el muestreo comparativo del dibujo; ahora se conserva esa combinación para limitar la refactorización.
- Añadir anotaciones de tipos y contratos de datos si crece el proyecto.
- Unificar el estilo global `plt` de la primera curva y los objetos `Axes` del resto.
- Revisar publicación y bloqueos si se soportan otros sistemas o procesos concurrentes.
- Fijar versiones de dependencias si se requiere reproducibilidad estricta; solo se ha añadido Flask y sus dependencias necesarias.

Ya existe punto de entrada protegido y el flujo normal no sobrescribe PNG históricos. La configuración predeterminada es global, pero cada ejecución trabaja con una copia local y las funciones físicas reciben argumentos. Las pruebas verifican implementación y almacenamiento, no todos los fallos de hardware ni datos físicos externos.

## 18. Preguntas de autoevaluación

Intenta responder antes de abrir las soluciones. No hace falta memorizar las últimas cifras de los resultados.

1. ¿Cuáles son los nueve parámetros del caso actual y cuáles llevan unidades?
2. ¿Qué ocurre al ejecutar una línea `def`? ¿Se calculan ya las temperaturas?
3. ¿Qué diferencias hay entre la tupla de temperaturas, la lista de ciclos y el diccionario de balance?
4. ¿Qué expresión física representa `relacion_presiones ** ((gamma - 1) / gamma)`?
5. ¿Por qué se exige `T3>T2`? ¿Basta con que todas las temperaturas sean positivas?
6. ¿Qué significa `calcular_balance_energetico(*temperaturas, cp)` y cuántos argumentos recibe?
7. ¿Qué incorpora `**balance` al diccionario del ciclo?
8. ¿Por qué el trabajo del compresor es positivo y aun así se resta?
9. ¿Cómo se convierte `cp·ΔT` a kJ/kg? ¿Y un rendimiento a porcentaje?
10. ¿Qué produce `np.linspace(1.01,50,100001)` y cuál es su paso aproximado?
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
12. El barrido solo evalúa puntos discretos y el óptimo continuo normalmente queda entre dos. También hay aproximación flotante. Se comprueba un margen de un paso.
13. En el óptimo el factor térmico es `sqrt(T3/T1)`, de modo que ambas son `sqrt(T1*T3)`. Sigue habiendo calor porque `T3>T2`; `T4` no es la temperatura inicial del calentamiento.
14. Es una referencia arbitraria de entropía relativa. El enfriamiento 4→1 reduce entropía; el incremento 1→4 es su opuesto y coincide con el aumento positivo 2→3 del ciclo ideal.
15. La turbina no ideal entra con `p3=p2(1−δ)`, menor que la presión alta ideal. Con la misma salida `p4`, su expansión isentrópica de referencia es menor y deja una temperatura mayor.
16. Ambos deben ser iguales por `Pv=RT`. La presión se almacena en kPa y se pasa a Pa para utilizar `R` en J/(kg·K).
17. Desempaqueta el único objeto de línea de la lista devuelta por `plot`. Su color se usa para que la flecha de ese proceso coincida con la curva.
18. Agg permite guardar sin ventanas ni Tkinter; `close` libera el registro de la figura. Base64 representa los bytes PNG como texto que puede incluirse en una URL de datos dentro del HTML. Ninguna operación cambia las ecuaciones.
19. GET solicita formulario/informe sin ejecutar un caso nuevo; POST envía datos y solicita una simulación. El campo llega como texto, se convierte a `float` y se divide entre 100: 5 pasa a 0.05. Importar `web_app` registra rutas pero no inicia el servidor ni una simulación.
20. Devuelve `None`. Un fallo de cálculo/publicación sin capturar conserva traceback; `finally` limpia recursos. Un fallo de retención posterior al guardado produce advertencia.

</details>

## 19. Mini ejercicios de programación

Estos son ejercicios propuestos, **sin aplicar cambios al programa**. Practícalos cuando decidas hacerlo en una copia de trabajo. Cada uno indica qué deberías observar, sin incluir su implementación.

1. **Cambiar un parámetro.** Prueba `relacion_presiones=8` desde el formulario o con `main(parametros={"relacion_presiones": 8})`. Antes de ejecutar, predice el sentido de cambio de `T2`, `T4` y rendimiento ideal. Distingue este parámetro de las mallas independientes, que seguirán usando sus propios extremos.
2. **Modificar una celda del informe.** Presenta el rendimiento ideal con cuatro decimales en vez de seis usando una f-string. Comprueba que no cambia el cálculo.
3. **Crear una función pequeña.** Escribe una función que convierta J/kg a kJ/kg y úsala primero en ejemplos independientes de 1000 y 2500 J/kg. Explica qué devuelve y qué unidad espera.
4. **Practicar la validación del formulario.** Llama a `leer_parametros` con valores predeterminados y sustituye `p1` por cero, texto y `inf`. Explica en cada caso por qué no se debe llamar a `main` y dónde se muestra el error.
5. **Extraer información de un diccionario.** Obtén temperaturas y trabajo del ciclo ideal usando su función agrupadora. Imprime `T2` sin recalcularlo por separado y explica las dos indexaciones necesarias.
6. **Expandir una comprensión.** Reescribe en tu copia la construcción de `rendimientos_porcentaje` mediante lista vacía, `for` y `append`, seguida de `np.array`. Comprueba que las curvas no cambian.
7. **Construir una tabla con `zip`.** Prepara cuatro filas de estado, T y p; pásalas a `tabla_html` e indica unidades. Verifica que las secuencias tengan cuatro elementos.
8. **Revisar unidades y energía.** Calcula en una función nueva de práctica el calor rechazado `cp*(T4−T1)/1000`, como magnitud positiva. Contrasta `qin−qout` con el trabajo neto del balance utilizando tolerancias. Esta magnitud sería una ampliación: el código actual no la devuelve.
9. **Explorar resolución numérica.** En una copia, reduce la malla del óptimo de 100001 a 1001 puntos manteniendo sus extremos. Calcula el nuevo paso y compara el error en `rp` y en trabajo respecto al máximo analítico. No confundas mejorar la precisión de la malla con mejorar las hipótesis del modelo.
10. **Separar cálculo y dibujo en un experimento pequeño.** Escribe una función que devuelva únicamente relaciones y trabajos de un barrido corto, sin imprimir ni guardar. Otra función de práctica debe representarlos con `figura,ejes`. Decide cómo se manejará un punto que no sea un ciclo motor y documenta esa decisión antes de programarla.

## 20. Resumen final

Deberías llegar a entender perfectamente las cuatro etapas, la numeración de estados, las hipótesis del gas, las unidades y el signo de cada balance. También las funciones que convierten entradas en temperaturas y energías, la diferencia entre rendimiento y trabajo máximo, y el sentido de las referencias isentrópicas del modelo no ideal.

En Python, practica definir y llamar funciones, leer retornos, manejar tuplas y diccionarios, escribir bucles, seguir excepciones y distinguir asignaciones de comparaciones. Después reproduce por separado una comprensión, una llamada con `*temperaturas`, una combinación con `**balance`, un `zip` y la selección de un máximo por índice. Debes poder explicar esos patrones con un ejemplo de dos o tres números.

Puedes utilizar Matplotlib y NumPy sin dominar todavía sus mecanismos internos, la implementación del backend o toda la teoría de aritmética flotante. Sí debes comprender qué secuencias reciben, qué coordenadas representan y por qué las comparaciones usan tolerancias.

Antes de ampliar el proyecto, conviene saber ejecutar y seguir una función de forma aislada, distinguir cálculo de presentación, definir el dominio físico admisible y comprobar un resultado por un segundo camino. Para ampliar la interfaz serán especialmente útiles el control de efectos al importar, los contratos de entrada y salida, el manejo de errores y la separación de datos y archivos por ejecución. El punto de entrada protegido, la presentación separada y la publicación del informe ya preparan parte de ese camino. La interfaz local y la validación del formulario ya están implementadas. Una web pública, autenticación y ejecución multiproceso siguen fuera del alcance.

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
