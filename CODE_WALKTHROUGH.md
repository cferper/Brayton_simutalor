# Guía educativa de Brayton Simulator

Guía del estado actual (28 de octubre de 2026). La interfaz Flask principal utiliza exclusivamente aire ideal con propiedades caloríficas variables cp(T), siete entradas físicas, optimización A/B (§4.61), sensibilidad OFAT (§4.62), mapas de diseño rp–T3 (§4.63) y segunda ley/exergía parcial de turbomáquinas (§4.64). El dashboard conserva ocho secciones en la única plantilla `templates/index.html`, sin selector ni página secundaria. El estado ambiente T0/p0 es independiente de los siete parámetros del ciclo. El flujo histórico con cp y gamma constantes permanece implementado en los módulos de `main.py` y su documentación de fases anteriores, y puede ejecutarse por terminal; los informes antiguos solo se consultan o descargan con identificación explícita de su modelo. La validación experimental no está incluida.

**Lectura por fases:** la [guía de aprendizaje de Fase 1](docs/milestones/03_dominio_viable_APRENDIZAJE.md) explica sus novedades respecto al commit de partida. La [guía de aprendizaje de Fase 2](docs/milestones/04_optimizacion_noideal_APRENDIZAJE.md) desarrolla la optimización y los intervalos dinámicos. La [guía de aprendizaje de Fase 3](docs/milestones/05_optimizacion_rendimiento_APRENDIZAJE.md) explica su física, algoritmos, integración y verificación de cierre. Este manual describe todo el código actual; `Evolution of the project` resume los grandes hitos, sin historial acumulativo de iteraciones.

Verificación previa de Fase 2, del 20 de octubre de 2026: **55 pruebas superadas** con `python -B -m unittest discover -s tests -v` (40.481 s en esta ejecución).

Los módulos se enumeran en §2; los tres dedicados al diagnóstico separan controles, selección/agregación y HTML. `.venv` contiene dependencias, no código propio. Se distinguen dominio físico, ventana numérica y ventana visual (§14). Los resultados históricos de las pruebas conservan sus entornos y fechas en §§4.45–4.55; las comprobaciones realizadas para el panel se registran en §4.56 y en su [milestone técnico](docs/milestones/18_diagnostico_fisico.md). Una prueba histórica satisfactoria no se presenta como un control ejecutado al generar cada informe.

La verificación de esta fase se realiza con informes en carpetas temporales; los seis PNG históricos permanecen intactos. No se crean commits automáticamente. La base verificada de Fase 2 es `f9f9a0495c4231a4d48399fba4bccdcc0f6bcf6f` en `feature/fase-2-optimizacion-noideal`; la implementación de Fase 2 está registrada en el commit `c2f4bff84a173f3b354a5d0f76c2b7bd2ee1fa21` (`Implement non-ideal Brayton work optimization with dynamic intervals`).

La ejecución normal no lee ni sobrescribe los PNG históricos. Los ejemplos que guardan un PNG explícitamente son usos opcionales. Las referencias se dan mediante archivo y nombre de función para no depender de líneas que cambian al editar.

**Alcance actual de Fase 3:** `main` llama al estudio ideal y al optimizador no ideal de rendimiento, compara A/B y añade la curva de compromiso. La simulación normal mantiene nueve entradas físicas y recalcula los estudios de ese caso por POST; el botón OFAT usa el flujo independiente de §4.40. La revisión final y la guía de aprendizaje están completadas; la implementación de la fase está registrada en `44145f3553ee502ed7d547762651d12ca1c41d40` (`Implement Brayton thermal efficiency optimization and work trade-off`), desarrollada en `feature/fase-3-optimizacion-rendimiento` sobre la base `5629eb076d10ad54852f74a438fda8a970db5f04`.

**Fase 4 registrada:** implementación `88c026395a9aba9cf72819305cfe2540f200e54a` (`Implement Brayton parametric sensitivity analysis with Flask integration`), desarrollada sobre `899024c518348fa48944041059aa885cc127af7e`. La asociación documental se incorpora durante el cierre Git autorizado, una vez conocido el hash. Su guía y milestone conservan el detalle de esta fase. Verificación previa al commit de este cierre, el 21 de octubre de 2026: 108/108 pruebas OK en 80.205 s.

## 1. Visión general del programa

La aplicación web actual estudia un ciclo Brayton con aire ideal de composición constante, pero con `cp(T)` y `gamma(T)` variables. El caso base Brayton utiliza siete entradas y entalpías/entropías dependientes del estado. La ruta independiente `/turborreactor` sí incorpora combustible energético equivalente, empuje específico y toberas convergente/C-D; sus cuatro nuevas representaciones se explican en §§4.81–4.82. Ninguna ruta representa un motor real de alta fidelidad. El modelo caloríficamente perfecto de nueve parámetros continúa existiendo en los módulos históricos y en el repositorio de conservación, pero no es seleccionable desde Flask.

`propiedades_aire.py`, `ciclo_cp_variable.py` y `optimizacion_cp_variable.py` constituyen el motor de la web actual. El presentador `cp_variable_web.py` prepara sus datos para `web_app.py` y `dashboard.py`, sin añadir ecuaciones. `main.py`, `viabilidad.py`, `sensibilidad.py`, `mapa_diseno.py` y `segunda_ley.py` conservan los cálculos anteriores para uso histórico/por Python, pero sus acciones no están activas en la nueva web.

| Estado | Lugar físico |
|---|---|
| 1 | Entrada del compresor |
| 2 | Salida del compresor |
| 3 | Entrada de la turbina |
| 4 | Salida de la turbina |

**INTERPRETACIÓN FÍSICA.** Los procesos ideales son dos isentrópicas y dos isóbaras. El no ideal incorpora eficiencias de compresor y turbina y pérdida de presión del combustor. Se calculan los máximos de trabajo de ambos modelos y, por separado, el máximo de rendimiento no ideal cuando hay pérdidas y dominio motor. El ideal/reversible tiene sólo un supremo no alcanzado de rendimiento; no se crea un punto B ficticio.

**PYTHON.** La ruta principal `/` de Flask usa siete entradas desde `cp_variable_web.DEFAULTS`: lee `request.form`, verifica números finitos y llama a `resolver_ciclo` y `estudiar_cp_variable` mediante `preparar_resultados`. `dashboard.renderizar_dashboard(..., modo_cp=True)` coloca resultados y optimizaciones en las secciones originales, sin generar informes. La rama histórica de la misma plantilla sigue permitiendo consultar informes antiguos; `main.py` continúa realizando cálculos de nueve parámetros y generando PNG/HTML solamente si se llama desde Python. El flujo clásico detallado a continuación es **histórico**, no la ejecución actual de `web_app.py`.

```text
Imports y definiciones
↓
Terminal: main() con valores predeterminados
O navegador: GET formulario → POST normal → validación → main(parametros=...)
POST sensibilidad → analizar_sensibilidad → R/A/B → tres PNG → HTML → publicación compartida
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
Resultados existentes → diagnóstico actual y agrupación → tablas + CSS + imágenes Base64 → HTML en memoria
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
├── propiedades_aire.py          aire ideal de cp(T), h(T), s(T,p), gamma(T) e inversión; aislado
├── tobera_convergente_divergente_cp.py  tobera C-D con cp(T), conectada a Flask y con choques (§§4.77–4.79)
├── ciclo_cp_variable.py         solucionador Brayton cp(T), usado por Flask
├── optimizacion_cp_variable.py  dominio y óptimos A/B de cp(T)
├── cp_variable_web.py           presentadores SVG y preparación del dashboard
├── optimizacion.py             candidatos, búsqueda interior y contraste de máximos
├── optimizacion_rendimiento.py rendimiento y comparación A/B
├── sensibilidad.py             OFAT, derivadas locales y tres gráficas independientes
├── mapa_diseno.py              mapa rp–T3, máscaras, trayectorias y cortes
├── segunda_ley.py              entropías, generación adiabática y destrucción parcial de exergía
├── diagnostico.py              controles científicos sobre resultados existentes
├── diagnostico_informe.py      alcance por modalidad y agrupación de los controles
├── diagnostico_html.py         presentación del diagnóstico, sin ecuaciones del ciclo
├── guias_educativas.py         resúmenes y fundamentos estáticos para cada sección
├── reporting.py                tablas técnicas y conservación de informes
├── dashboard.py                presentación compartida local/autónoma, sin física
├── web_app.py                  servidor Flask de acceso local
├── Abrir_Brayton_Simulator.cmd acceso por doble clic al formulario local
├── templates/index.html        única plantilla principal: cp(T) e informes históricos
├── static/style.css            diseño responsive y tipografías
├── static/dashboard.js         secciones, pestañas y modal progresivos
├── static/fonts/               tres WOFF2 IBM Plex, OFL y procedencia
├── static/images/              esquema original del motor y licencia CC0
├── tests/test_viabilidad.py    pruebas de dominio, fronteras, máscaras y regresión HTTP
├── tests/test_propiedades_aire.py  NIST, integrales, tramos, inversión y errores de entrada
├── tests/test_tobera_convergente_divergente_42a.py  masas, energía, entropía, ramas y gas perfecto
├── tests/test_ciclo_cp_variable.py estados, balances, fronteras y referencias independientes
├── tests/test_optimizacion.py  máximos, intervalos dinámicos y regresión Flask
├── tests/test_optimizacion_rendimiento.py  pruebas unitarias de rendimiento
├── tests/test_integracion_rendimiento.py  gráficas, informe, recálculo Flask y criterios
├── tests/test_reporting.py     pruebas de informes
├── tests/test_web_app.py       pruebas HTTP y compatibilidad
├── tests/test_dashboard.py     15 pruebas de presentación, datos y rutas
├── tests/test_mapa_diseno.py   21 pruebas del mapa e integración
├── tests/test_explicaciones.py 16 pruebas de textos educativos y conclusiones
├── tests/test_segunda_ley.py   18 pruebas de entropía/exergía e integración
├── tests/test_sensibilidad.py  19 pruebas de cálculo y seis de integración OFAT
├── tests/test_verificacion_analitica.py   referencias ideales y residuos de primera ley
├── tests/test_verificacion_raices.py       raíces analíticas, dominios y casos degenerados
├── tests/test_comparacion_scipy.py         contraste opcional con SciPy de raíces y máximos
├── tests/test_convergencia_numerica.py      tolerancias, mallas, coste y fronteras
├── tests/test_invariantes_fisicos.py        primera ley e invariantes del modelo
├── tests/test_verificacion_sensibilidad.py referencias independientes OFAT R/A/B
├── tests/test_verificacion_mapa_diseno.py  referencias independientes del mapa rp–T3 (V.2)
├── tests/test_verificacion_segunda_ley.py  referencias independientes de entropía/exergía (V.3)
├── tests/test_verificacion_simulacion.py  referencias, gráficas e informes (V.4)
├── tests/test_verificacion_integracion_web.py  formularios, historial y descarga (V.5)
├── README.md                   instalación y uso
├── requirements.txt            numpy, matplotlib y Flask
├── .gitignore
├── docs/milestones/            informes técnicos, guías y fases 2A/2B: milestones 19/20
├── outputs/                    informes generados, excluidos de Git
└── *.png                       seis imágenes históricas conservadas
```

`outputs/` se crea al guardar el primer informe si no existe. `.venv` es el entorno local y `.vscode/settings.json` configura el editor; no participan en las ecuaciones. `.gitignore` excluye entorno, cachés, temporales, configuración local y resultados generados. Git conserva versiones de código y documentación cuando se solicitan commits; no se crean copias numeradas del walkthrough.

| Archivo/bloque | Responsabilidad actual |
|---|---|
| `viabilidad.py` | Validación, ecuaciones de estados/energías compartidas, clasificación sin excepciones físicas, bisección y barridos |
| `propiedades_aire.py` | Propiedades termodinámicas de aire seco cp(T); invocado por el solucionador independiente de Fase 2B, no por el ciclo histórico (§4.57) |
| `ciclo_cp_variable.py` | Estados, energías, entropía y clasificación Brayton cp(T); sólo importado directamente y por sus pruebas, sin consumidores Flask/HTML (§4.58) |
| `optimizacion.py` | Máximo analítico y numérico de trabajo; reutiliza estados y dominio de Fase 1 |
| `optimizacion_rendimiento.py` | Supremo ideal, máximo de rendimiento y comparación A/B integrados en main |
| `main.py`: funciones de ciclo | API estricta de cálculo motor, comprobaciones, entropía/P-v y óptimo ideal |
| `main.py`: funciones `guardar_*` y `marcar_dominio` | Siete PNG en memoria; bandas/fronteras, compromiso y NaN en curvas de rp |
| `main.py`: `main` y punto de entrada | Copia de parámetros, coordinación y ejecución directa protegida |
| `reporting.py` | Git, tablas/Base64, dominio, documento completo y publicación/retención |
| `diagnostico.py`, `diagnostico_informe.py`, `diagnostico_html.py` | Controles sobre datos calculados, alcance/agregación por modalidad y panel HTML; contratos en §4.56 |
| `web_app.py` | Formulario, entradas, errores diferenciados, vista/descarga y servidor local |
| `templates/index.html`, `static/style.css` | Plantilla Jinja y presentación adaptable |
| `tests/test_*.py` | Referencia, dominio físico, verificación analítica del ideal, integración CLI/HTTP, informes y fallos |

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

**Qué hace:** forma tablas, secciones y CSS, incorporando siete imágenes normales o tres del estudio OFAT.

**PYTHON:** `str`, `escape`, `join`, f-strings multilínea, `b64encode(...).decode("ascii")`. La presentación técnica heredada sigue utilizando llaves dobles en sus f-strings; el CSS final del dashboard se lee desde static/style.css y se incorpora con sus llaves normales.

**INTERPRETACIÓN FÍSICA:** conserva unidades e identificación ideal/no ideal. La presentación no mejora la fidelidad física.

### H. Publicación y conservación

**Qué hace:** escribe un temporal, publica el HTML completo y conserva cuatro informes propios.

**PYTHON:** `Path`, `mkdir`, apertura exclusiva `"x"`, `with`, `try/finally`, `rename`, expresiones regulares, UUID, `lambda`, `[4:]` y `unlink`. Errores posteriores de limpieza se notifican con advertencia.

**INTERPRETACIÓN FÍSICA:** no contiene ecuaciones; mantiene juntos parámetros, números y gráficas de una ejecución.

### I. Servidor y formulario

**Qué hace:** muestra nueve campos físicos agrupados y una sección OFAT con selector y tres controles numéricos; valida la acción elegida, invoca el flujo correspondiente y redirige a su informe. Los parámetros enviados se conservan cuando hay errores.

**PYTHON:** objeto `Flask`, decoradores `@app.route`, `request`, `float`, diccionarios de errores y `render_template`. La pérdida se divide por 100 una sola vez antes de llamar al simulador.

**INTERPRETACIÓN FÍSICA:** no hay ecuaciones nuevas. Los rangos de campos, la combinación física, el límite numérico y el error interno se distinguen. El formulario conserva los valores rechazados y muestra todos los motivos físicos y el intervalo permitido cuando existe.

### J. Pruebas

**Qué hace:** comprueba referencias, cinco ejecuciones, errores y colisiones. Las baterías adicionales verifican estados/energías ideales (§4.45), raíces y fronteras (§4.46), y concordancia numérica opcional con SciPy (§4.47), sin introducirlo en el simulador.

**PYTHON:** clases de `unittest`, `self`, `assert*`, `subTest` (casos identificados dentro de un mismo método), `patch`, directorios temporales y parser HTML. Las excepciones propias heredan de tipos estándar; los resultados físicos siguen siendo diccionarios.

**INTERPRETACIÓN FÍSICA:** verifica el cálculo conocido; no compara con datos externos de un motor.

### K. Análisis OFAT independiente

**Qué hace:** compara R/A/B al variar una entrada, calcula derivadas locales y publica tres figuras. **PYTHON:** copias, callbacks y caché local, arrays NaN, estados explícitos y comprobación de pasos. **INTERPRETACIÓN FÍSICA:** escenarios a rp fija u optimizada, elasticidades condicionadas a una referencia, sin ecuaciones termodinámicas nuevas. Detalle y contratos en §4.40.

## 4. Explicación función por función

**Ámbito actual y legado:** los apartados anteriores a §4.57 describen principalmente funciones de gas perfecto que siguen existiendo en Python y en los informes históricos; **no** son operaciones disponibles desde el formulario Flask de cp(T). Los contratos vigentes de la interfaz única están en §4.61. Esta distinción es fundamental al leer las explicaciones de las antiguas rutas POST.

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
def main(carpeta_salida=None, parametros=None, *, T0=288.15):
```

- **Propósito:** coordina la ejecución completa; los nueve valores predeterminados están en la constante del módulo y pueden sustituirse desde el formulario.
- **Argumentos:** `carpeta_salida` es `Path`, cadena o `None`; `None` usa `outputs/` junto al script. `parametros` es un diccionario opcional con cualquiera de las nueve claves conocidas y unidades de §5. Las claves omitidas conservan sus valores predeterminados; la pérdida se recibe como fracción, no porcentaje. No se modifica el diccionario recibido ni la configuración predeterminada. `T0` es un argumento por nombre independiente de los nueve parámetros, en K, positivo y finito; sólo afecta la destrucción de exergía (§4.44).
- **Salida:** `Path` al HTML completo; efectos: guardar, conservar cuatro y mostrar tres líneas.
- **Llama directamente:** `validar_parametros`, `calcular_dominios`, `evaluar_punto`, `construir_barrido`, `describir_inviabilidad`, rendimiento, temperaturas, balance, entropías, estados P-v, `optimizar_trabajo_neto` dos veces, `estudiar_rendimiento_ideal`, `optimizar_rendimiento`, `comparar_criterios`, ambos ciclos, comprobación comparativa, seis funciones gráficas `guardar_*`, tabla de rendimientos, `validar_referencia`, `analizar_segunda_ley` sobre registros ya calculados y `crear_informe_html`, `guardar_informe_html` y `obtener_version_git`.
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
def imagen_html(imagen, titulo, explicacion=None):
```

- **Propósito:** convertir PNG de esta ejecución en figura HTML autocontenida.
- **Argumentos:** `imagen`, bytes PNG sin unidad; `titulo`, cadena con significado físico y unidades cuando corresponda; `explicacion`, str de texto plano opcional o None. Ambos textos se escapan con `escape`.
- **Retorno:** `str` con `figure`, `img`, `figcaption`, URL `data:image/png;base64,...` y, si se solicita, un párrafo explicativo. No modifica los bytes PNG.
- **Validación/errores:** comprueba firma binaria PNG; `ValueError` si no coincide. No decodifica exhaustivamente los píxeles; las pruebas sí decodifican las siete imágenes actuales.
- **Llama:** ninguna propia; usa `b64encode`, `.decode` y `escape`. La llaman los tres creadores de informes y las pruebas de presentación/PNG inválido.
- **PYTHON:** literal de bytes, `.startswith`, conversión binario→texto. No cambia física ni comprime adicionalmente el PNG.
- **Ejemplo:** `imagen_html(buffer.getvalue(), "Diagrama T-s ideal", "X: entropía relativa; Y: temperatura. Caso ideal fijo.")` con una gráfica recién dibujada.

### 4.22. `crear_informe_html` — reporting.py

```python
def crear_informe_html(parametros, ideal, noideal, detalles_ideal, optimo,
                       rendimientos, comprobaciones, imagenes, fecha, version, barrido=None,
                       optimizaciones=None, *, estudio_rendimiento=None, comparacion_criterios=None, segunda_ley=None):
```

- **Propósito:** reunir secciones, siete PNG y, cuando se suministra `segunda_ley`, dos SVG adicionales en un HTML; no escribe ni recalcula el ciclo.
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
- **Llama:** `valores_formulario`, `leer_parametros`, `validar_configuracion` para sensibilidad, `validar_mapa`, `validar_referencia`, `estudio_conservado`, `listar_informes`, `renderizar_dashboard` y, según el botón, uno de `main`, `ejecutar_sensibilidad`, `ejecutar_mapa` o `ejecutar_segunda_ley`. Flask la llama por el decorador de ruta; las pruebas lo hacen mediante `test_client`.
- **Unidades:** respeta el contrato de `leer_parametros`; no calcula ecuaciones.
- **Validación/errores:** no ejecuta cálculos si hay errores de campos. Para OFAT convierte mínimo/máximo a `float` y muestras a `int`, valida rangos y exige referencia `T3>T1`; las muestras del barrido sí pueden ser no motoras. Para mapa convierte límites/cortes a `float`, resoluciones a `int` y valida la configuración, sólo si esa acción está activa. Para normal y Segunda Ley exige `T0` positivo y finito; para mapa y OFAT ignora `T0`. Segunda Ley valida además entradas físicas y admite reutilizar un estudio previo sólo si el informe y los nueve parámetros coinciden. Los controles exclusivos de una acción no se validan en las demás. Captura `ErrorModelo` y `ErrorNumerico` con mensajes distintos durante la ejecución; conserva `request.form.to_dict()` para volver a mostrar valores. Otros errores llegan al tratamiento HTTP 500 de Flask.
- **PYTHON:** decorador `@app.route("/", methods=["GET", "POST"])`, condicionales y `try/except/else`. Ese `else` se ejecuta solo si la llamada no lanzó una excepción.
- **Ejemplo:** `client.get("/")` muestra el formulario; `client.post("/", data=datos)` simula un envío en una prueba. Fuera de una petición no se llama manualmente a `index()`.

### 4.29. `ver_informe` — web_app.py

```python
def ver_informe(nombre):
```

- **Propósito:** devolver un informe propio completo o su descarga, sin ofrecer un explorador de archivos locales.
- **Entrada:** `nombre`, cadena de nombre base incluida en la URL, sin unidad física.
- **Salida:** `Response` HTML; con `?descargar=1`, añade cabecera de descarga y devuelve el contenido guardado intacto. La vista normal recupera los paneles y parámetros del informe nuevo y renderiza el dashboard local editable, con historial y descarga; los informes anteriores conservan su presentación original con enlaces añadidos sólo en memoria.
- **Llama:** `separar_presentacion`, `listar_informes`, `renderizar_dashboard` para informes nuevos; Flask la llama para `/informes/<nombre>`.
- **Validación:** patrón completo de informes, archivo regular no simbólico, ruta resuelta dentro de `OUTPUTS_DIR` y marcas inicial/final. Nombre/ruta/archivo inexistente, no UTF-8 o informe incompleto devuelven 404 mediante `abort`.
- **Errores:** fallos inesperados de lectura o código se registran como 500. Un informe antiguo eliminado por retención devuelve 404; no se inventa una copia de su contenido.
- **PYTHON:** `.resolve`, `.read_bytes`, `.decode("utf-8")`, `.replace(..., 1)`, argumentos de URL, f-string, `Response` y cabeceras HTTP. `contenido_bytes` conserva los bytes del archivo y `contenido` es su representación de texto para validar/renderizar. La descarga usa los bytes originales: no normaliza CRLF de Windows a LF. La lectura y decodificación se hacen una sola vez; no se escribe ni recalcula el informe.
- **Ejemplo:** `client.get("/informes/" + nombre)` y `client.get("/informes/" + nombre + "?descargar=1")`, usando un nombre real generado.
- **INTERPRETACIÓN FÍSICA:** no recalcula; sirve exactamente la ejecución guardada. El contenido del dominio ya está calculado al servir el archivo.

### 4.30. `error_interno` — web_app.py

```python
def error_interno(error):
```

- **Propósito:** presentar un fallo inesperado sin exponer trazas al navegador ni llamarlo inviabilidad física.
- **Argumento:** excepción HTTP 500 que entrega Flask; sin unidad física. **Retorno:** formulario HTML y estado 500.
- **Llama:** `valores_formulario` cuando no es un POST, `listar_informes` y `renderizar_dashboard`; Flask llama a este manejador, registrado con `@app.errorhandler(500)`.
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
- **Llama:** ninguna función propia. La llaman `calcular_estados`, `evaluar_punto`, `calcular_dominios`, `main`, los módulos de optimización de trabajo/rendimiento (§4.35, §4.38) y `analizar_sensibilidad`.
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
- **Llama:** `validar_parametros`, `calcular_estados`, `calcular_energias`. La llaman `construir_barrido`, `calcular_ciclo_noideal`, `buscar_maximo_numerico`, `optimizar_trabajo_neto`, `buscar_maximo_rendimiento_numerico`, `optimizar_rendimiento`, `main` (referencia y tabla ideal), `evaluar_muestra` de sensibilidad y pruebas.
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
- **Llama:** `validar_parametros`, `bisectar_raiz`. La llaman `construir_barrido`, `calcular_ciclo_noideal` en rechazos, `buscar_optimo_numerico`, las funciones de `optimizacion.py` cuando no reciben dominio, `estudiar_rendimiento_ideal`, `buscar_maximo_rendimiento_numerico`, `optimizar_rendimiento`, `evaluar_muestra` de sensibilidad, `main` y pruebas.
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


**Relaciones con OFAT:** `evaluar_muestra` llama también a `calcular_candidato_analitico` en cada muestra con dominio y a `optimizar_trabajo_neto` para los contrastes seleccionados (§4.40); las firmas y ecuaciones de este módulo no cambian.

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
- **Llama:** `validar_parametros` con cp=p1=1 auxiliares. La llaman `optimizar_rendimiento`, `evaluar_muestra` de sensibilidad y pruebas/usuarios directos. No llama a la búsqueda numérica.
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
- **Llama:** `calcular_dominios`, `estudiar_rendimiento_ideal` si reversible, `calcular_candidato_rendimiento`, `evaluar_punto` y `buscar_maximo_rendimiento_numerico`. La llaman `main`, `evaluar_muestra` de sensibilidad en contrastes/reversibilidad y pruebas/usuarios directos.
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

### 4.40. Sensibilidad OFAT — `sensibilidad.py`, HTML y Flask

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** OFAT cambia una entrada x conservando las otras ocho. R mantiene rp; A reajusta rp para máximo W; B la reajusta para máximo eta. Se reutilizan §4.32, §4.35 y §4.38 sin copiar ecuaciones. Cada muestra calcula dominios ideal/no ideal nuevos. El dominio abierto de rp no es el rango de x del formulario; sólo las muestras seleccionadas realizan una búsqueda interior numérica. No hay ventanas fijas 2–30 ni 1.01–50.

`PARAMETROS_ESTUDIO` relaciona `delta` con `perdida_presion_combustor`, unidades y sugerencias: T1 250–350 K, T3 800–2000 K, eficiencias 0.6–1 y delta 0–0.2. No son límites físicos universales. `MAGNITUDES` enumera W, eta, Qin y rp; las energías son kJ/kg, eta fracción. El campo físico de pérdida conserva %, pero los extremos de delta usan fracción.

**PYTHON: estructura.** El estudio es un diccionario con `referencia`, `configuracion`, `valores` (array), `registros` (lista de muestras), `curvas` (escenario→magnitud→array), `sensibilidades`, `referencia_local`, `indices_verificacion`, `tendencias` y `segundos_calculo`. Una muestra contiene copia de parámetros, dominios o None, motivo del dominio y registros R/A/B. No se guarda estado físico entre llamadas; las constantes sólo describen opciones.

#### Contratos completos de las funciones nuevas

Las entradas numéricas son escalares reales salvo `muestras` int y `verificar` bool. `referencia/parametros` son diccionarios de las nueve claves de §5. Los tipos indicados son contratos esperados, no anotaciones automáticas. Errores de estructura/tipos incorrectos propagan sus excepciones Python; no se presentan como inviabilidad física.

1. **`validar_configuracion(parametro, minimo, maximo, muestras)`** → dict con las cuatro entradas normalizadas y `unidad`. `parametro` str entre cinco nombres; extremos reales finitos ordenados; temperaturas positivas, eficiencias (0,1], delta [0,1); muestras int 3–201, excluido bool. Lanza ValueError para estas restricciones. No calcula física; consultada por Flask, `analizar_sensibilidad` y `generar_malla`; no llama funciones propias. Comparaciones encadenadas e `isinstance` distinguen un entero de `True` (Python considera bool subclase de int). Ejemplo: `validar_configuracion('T3',800,2000,41)`.

2. **`generar_malla(configuracion)`** → ndarray float de n valores de x con extremos incluidos. Llama validación y `np.linspace`; `np.diff` debe ser estrictamente positivo para detectar extremos indistinguibles en coma flotante. ValueError por configuración/malla; la llama `analizar_sensibilidad`. Ejemplo: `generar_malla(validar_configuracion('delta',0,.2,3))` da `[0,.1,.2]`. No busca óptimos sobre esta malla: muestrea el parámetro OFAT.

3. **`construir_parametros(referencia, parametro, valor)`** → dict independiente con sólo una entrada sustituida. No valida física ni llama funciones propias; la llama el estudio tanto para muestras como perturbaciones. `.copy()` basta porque los valores son escalares inmutables. Ejemplo: `construir_parametros(PARAMETROS_PREDETERMINADOS,'delta',.1)` deja los otros ocho intactos. Nombre inexistente produce KeyError de contrato.

4. **`argumentos_fisicos(parametros)`** → tupla `(T1,T3,gamma,cp,p1,eta_c,eta_t,delta)` en las unidades de §5, sin rp. La llaman `evaluar_muestra` y `analizar_sensibilidad`; no llama funciones propias. Un generador con `tuple(...)` adapta nombres del formulario a las firmas heredadas; clave ausente produce KeyError. Ejemplo: `argumentos_fisicos(PARAMETROS_PREDETERMINADOS)` permite llamar `calcular_dominios(*args)`.

5. **`registro_escenario(estado, motivos=(), rp=None, ciclo=None, metodo='no aplicable', supremo=None, verificacion=None)`** → dict uniforme. Estado/método str; motivos secuencia str; rp real adimensional; ciclo dict de `evaluar_punto` o None; supremo y verificación dict o None. Sólo `estado='disponible'` publica magnitudes operativas; los otros dejan rp/W/eta/Qin None. `ciclo` puede conservar evaluación firmada de R excluido; HTML la identifica como diagnóstico, sin eta motora. `verificacion` guarda intervalos numéricos de búsqueda/final y concordancia, nunca se inventa para fórmulas no contrastadas. Función de apoyo sin física, llamada por `evaluar_muestra`; errores de contrato propagan. Ejemplo: `registro_escenario('sin_dominio',('Dominio motor vacío.',))`.

6. **`evaluar_muestra(parametros, verificar=False)`** → muestra estructurada descrita arriba. Llama adaptador, `evaluar_punto`, `calcular_dominios`, los candidatos de Fases 2/3 y, si se pide contraste, sus coordinadores completos. La llaman estudio y callback local; ejemplo `evaluar_muestra(PARAMETROS_PREDETERMINADOS, verificar=True)`. Si T3<=T1 registra `parametros_inviables` sin evaluar ecuaciones inválidas; R no motor conserva **todos** los códigos traducidos de `MOTIVOS`. Dominio vacío da `sin_dominio` sin optimizar; reversible B da `supremo_no_alcanzado` con valor/frontera y sin ciclo operativo. Los candidatos deben estar estrictamente dentro del dominio y superar las bandas de `evaluar_punto`. Sólo se captura `ErrorNumerico`, produciendo `limite_numerico` por escenario; un fallo en dominios conserva R si pudo evaluarse. ValueError inesperado y otros bugs propagan, no se maquillan como motor vacío. No cambia hipótesis ni duplica balances.

7. **`calcular_sensibilidad_local(funcion, x, limites, escala=1.)`** → dict `derivada`, `normalizada`, `metodo`, `paso`, `error_estimado`, `motivo`. Callback recibe x real y devuelve Y real o None; x/limites tienen unidades del parámetro y escala unidades de Y. Llamada por el estudio; sólo llama el callback recibido. Ejemplo: `calcular_sensibilidad_local(lambda x:x*x,2.,(0.,10.))` da dY/dx≈4 y S≈2. `lambda` crea una función pequeña anónima; no modifica x global. None indica indisponibilidad, no cero. Excepciones del callback propagan; los fallos de fiabilidad esperados son registros con motivo. Algoritmo y tolerancias debajo.

8. **`analizar_sensibilidad(referencia, parametro, minimo, maximo, muestras=41)`** → estudio completo, sin archivos. Valida referencia mediante `validar_parametros` y rp finita >1; la referencia debe cumplir T3>T1, aunque su R no tiene que ser motor. Llama validación, malla, copias, evaluador y derivadas. La llaman API/tests y `ejecutar_sensibilidad`. Ejemplo: `analizar_sensibilidad(PARAMETROS_PREDETERMINADOS,'T3',800,2000,41)`. Índices independientes: extremos, centro entero y vecino más próximo a x de referencia; conjunto evita duplicados (máximo cuatro). Los demás usan candidatos ya demostrados con control físico individual. `curvas` sustituye sólo resultados no disponibles por NaN. Las tendencias dan disponibilidad, número de tramos y mínimos/máximos muestreados; no atribuyen monotonicidad universal. `segundos_calculo` usa `perf_counter` e incluye derivadas, no gráficos/publicación. Error global de entrada ValueError; programación propaga. Caché exclusivamente local.

   Los cierres **`evaluar_local(x)`** y **`magnitud(x)`** viven dentro de esta función: el primero recibe x y devuelve la muestra desde un dict local indexado por x, llamando copias/evaluador; lo llama el segundo y la construcción de `referencia_local`. `magnitud` recibe x y retorna la magnitud k del escenario s o None cuando no hay motor o Qin<1e−7·cp·T3/1000; lo llama `calcular_sensibilidad_local` inmediatamente dentro del bucle, antes de cambiar s/k. Ejemplo interno: `magnitud(1600)` para A/W obtiene 373.210827 kJ/kg. Así se comparte cada perturbación entre 12 coeficientes sin variables globales ni errores de captura diferida.

9. **`crear_graficas_sensibilidad(estudio)`** → dict de tres claves W/eta/rp y bytes PNG 1350×900. Entradas con contrato del estudio; no recalcula física ni llama funciones propias. La llama ejecutor o tests/API. Ejemplo: `imagenes=crear_graficas_sensibilidad(estudio)`. NaN corta todas las curvas operativas, incluida rp de R. En la gráfica de rp, R muestra círculos sólo en muestras motoras y conserva NaN en las excluidas. Una cuarta línea gris de trazo punto-raya, etiquetada «Consigna rp de referencia (no indica viabilidad)», representa la entrada constante mediante `np.full`, aunque no exista motor. Es configuración, no resultado. El array operativo nunca se sustituye por esa constante; `datos_operativos` conserva los tres arrays para identificar ausencia de resultados incluso si se dibuja la consigna. La escala considera también la consigna para mantenerla visible. Se diferencian así visualmente la orden de diseño y su disponibilidad física; no cambian ecuaciones ni optimización. Eje x conserva **todo** el rango solicitado aunque sus extremos no tengan datos motores; y automático. Si cociente entre valores absolutos no nulos supera 100, usa escala `symlog` con umbral igual al menor valor y título explícito. Si faltan todos los datos, lo indica. `try/finally` cierra cada figura; `with BytesIO()` cierra el buffer. Un fallo inesperado de dibujo propaga.

10. **`ejecutar_sensibilidad(carpeta_salida, parametros, parametro, minimo, maximo, muestras=41)`** → Path del informe. Carpeta str/Path, resto según estudio. Llama `analizar_sensibilidad`, graficador, consulta Git, presentador nuevo y `guardar_informe_html`; Flask `index` y API/tests la llaman. Sin ecuaciones adicionales. Ejemplo: `ejecutar_sensibilidad('carpeta_de_prueba',PARAMETROS_PREDETERMINADOS,'T3',800,2000,41)`. Fecha con zona, errores de cálculo/dibujo/publicación propagan; no limpia anteriores antes de publicar.

11. **`crear_informe_sensibilidad_html(estudio, imagenes, fecha, version_git)`** — reporting.py → str HTML autocontenido. Estudio dict anterior; imágenes dict de exactamente tres claves y PNG válidos; fecha datetime; Git dict `commit` str/None, `modificado` bool/None. Llama `tabla_html` e `imagen_html`, lo llama el ejecutor. ValueError por claves o firma PNG; errores de contrato propagan. Ejemplo interno: `crear_informe_sensibilidad_html(estudio,imagenes,datetime.now(),{'commit':None,'modificado':None})`. Presenta parámetros, métodos/contraste, resultados, causas simultáneas, diagnóstico firmado, supremos excluidos, dominios, tendencias, coeficientes y límites. `escape` protege textos. Reutiliza marcas/nombres/publicación: el historial de cuatro mezcla ambos tipos, descarga/vista usan la misma ruta. No calcula física.

#### Diferencias finitas y fiabilidad

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Para Y(x), dY/dx tiene unidades de Y por unidad x; `S=(x/Y)*dY/dx` es adimensional. En eta se deriva la fracción; `100*deta/dx` representa pp por unidad x. Un S=0.67 implica aproximadamente +0.67 % relativo de eta ante +1 % relativo de x, conservando demás condiciones, no +0.67 pp. A/B incluyen el reajuste del óptimo: no son derivadas a rp fija. No es una clasificación universal.

**PYTHON / NUMÉRICO.** Paso inicial `h=cbrt(eps)*max(abs(x),1)` equilibra error de truncamiento de orden 2 y redondeo, con escala mínima de una unidad; el paso efectivo informado es h/2. Si x±h son admisibles usa `(Y(x+h)-Y(x-h))/(2*h)`. Cerca de extremos físicos usa `(-3Y0+4Y1-Y2)/(2h)` o su versión hacia atrás. Límites físicos: T1 en (0,T3), T3>T1, eficiencias (0,1], delta [0,1); `np.nextafter` aproxima extremos estrictos desde dentro. No limita derivadas al rango dibujado: se calculan en la referencia del formulario y HTML advierte si conceptualmente está fuera de él.

Se compara derivada a h y h/2; diferencia debe ser ≤`1e-3*abs(d_fina)+1e-7*abs(escala)/max(abs(x),1)`. Es un control heurístico de estabilidad, **no** una cota rigurosa de incertidumbre. Un cambio a indisponibilidad cancela el coeficiente; discontinuidades que causan inestabilidad también. Magnitud con |Y|≤1e−9·escala no ofrece coeficientes; escala energética cp·T3/1000, eta=1 y rp=rp de referencia. Si x=0, sólo derivada absoluta: elasticidad porcentual de una entrada nula no es interpretable. Un régimen muy estrecho puede no resolverse con el paso elegido; se informa, no se fuerza una cifra. Supremos sin punto B no tienen coeficientes operativos.

Ejemplo real T3=1600 K: dW_R/dT3=0.4291002274 kJ/(kg·K), S_W_R=1.858198650; dW_A/dT3=0.4624111961 y S_W_A=1.982412779. S_rpA=1.7499999997, que coincide con gamma/[2(gamma−1)]. S_etaB≈0.6743426771. Paso fino 0.00484436356 K. No redondear entradas antes de derivar.

#### Integración y controles de Fase 4

`index()` mantiene firma/contratos de §4.28 y ahora selecciona `accion` del botón. Normal no llama OFAT ni valida sus controles. Sensibilidad parsea sus campos, captura sólo ValueError de la conversión/configuración antes de llamar al ejecutor; un ValueError de código dentro del cálculo llega a HTTP 500, no a un aviso físico. `error_interno` pasa también opciones OFAT a la plantilla y conserva entradas. `valores_formulario` sigue devolviendo exactamente nueve valores, sin contaminar la configuración física con controles de presentación.

La plantilla usa un selector y tres inputs adicionales (12 numéricos en total), unidad visible y sugerencias. `tojson` entrega opciones a JavaScript local; el evento `change` rellena los extremos educativos con `this.value`. No se descarga una librería, no ejecuta simulaciones y no cambia el control físico de pérdida. Sin JavaScript se pueden escribir manualmente extremos; servidor valida siempre. Los errores conservan datos; tipos numéricos del navegador pueden no representar texto no numérico, igual que en los campos previos.

`tests/test_sensibilidad.py` contiene 19 métodos de cálculo y seis de integración, además de todos los 83 anteriores. Las clases `SensibilidadTests` e `IntegracionSensibilidadTests` heredan `unittest.TestCase`; sus `setUp(self)` inicializan copia física y cliente/carpeta temporal respectivamente; sin retornos físicos. Los métodos `test_*(self)` reciben sólo self y devuelven None: los llama unittest, verifican con asserts e inyección patch y no constituyen API del simulador. El nuevo `test_consigna_rp_separada_de_resultados_motores_con_t3_inviable(self)` estudia T3=200–1600 K con 15 muestras; intercepta `savefig` mediante el callback local `capturar(figura, *args, **kwargs)` para inspeccionar líneas reales antes de guardar el PNG. El callback devuelve el resultado del guardado original, sin física nueva. Comprueba igualdad de los nueve trazados operativos con los arrays/NaN, exclusión de muestras no disponibles, consigna constante gris y círculos R sólo en la figura de rp. Cubren validación/malla, OFAT, equivalencia independiente R/A/B, dominios dinámicos, motivos simultáneos, vacío, reversible, estrechos/bandas, errores diferenciados, derivadas con identidades y extremos, NaN/ejes/resolución, aislamiento/coste, Flask, HTML, retención mixta y publicación fallida. `test_web_app.py` sólo adapta su recuento de inputs; no se elimina ningún test previo.

Verificaciones previas del 20 de octubre de 2026: 107/107 OK en 93.103 s y 107/107 OK en 131.473 s tras fijar los límites visuales. Verificación actual del 21 de octubre de 2026: 108/108 pruebas correctas en 147.931 s con la suite completa, incluyendo la nueva prueba de consigna y máscaras. El primer intento aislado bajo sandbox encontró permisos denegados en temporales Windows; la suite con permisos adecuados utiliza carpetas temporales y no consume outputs. Revisión visual de figuras T3, puntos inviables y escalas grandes; informes completos y simulación normal generados fuera del proyecto. Tiempos de 41 muestras: cálculo 0.045–0.10 s y estudio completo aproximadamente 1.8–2.2 s en este equipo, sin garantías para otros equipos. Modelo sin validación externa.

### 4.41. Dashboard técnico independiente — presentación, sin cambios físicos

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** El rediseño, desarrollado sobre `ac37b9e0b93bcc0449e59fe04d5cfecb082f70ad` en `feature/rediseno-dashboard`, reorganiza Fases 1–4. Esa capa de presentación no cambia variables, ecuaciones, dominios, algoritmos ni píxeles de las gráficas anteriores. La incorporación actual de Fase 5 se describe en §4.42. Seis KPI del **caso no ideal actual** muestran rp, W, eta, Qin, máximo W y máximo eta alcanzado. None se presenta como No disponible, sin falsos ceros; el supremo no alcanzado conserva su explicación, nunca un punto B ficticio. Los conteos OFAT pueden valer cero como recuentos reales, distintos de magnitudes operativas ausentes.

**Arquitectura actual.** Sidebar de 232 px, barra superior y cabecera discreta con SVG original; ocho secciones: Simulación, Resultados, Optimización, Sensibilidad, Mapa de diseño, Segunda ley, Informes y Ayuda. La sección añadida y su flujo se explican en §4.42. Los formularios comparten las mismas nueve entradas y sus validaciones. Navegar usa fragmentos y JavaScript local, sin nuevas peticiones de cálculo. Informes mantiene lectura del historial propio completo sin modificar la retención: sigue ocurriendo únicamente en `guardar_informe_html`, tras publicar.

Resultados ofrece seis KPI, rango motor, visor y `Estados y balances detallados` cerrado por defecto. El visor normal tiene Rendimiento (dos PNG), Trabajo (dos), Diagramas termodinámicos (dos), Compromiso de diseño (uno) y Todas (los mismos siete en cuadrícula). No hay imágenes duplicadas: Todas sólo cambia el filtro de los mismos nodos figure. Optimización muestra tarjetas A/B y diferencias B−A, incluido pp frente a cambio relativo %. Sensibilidad conserva R/A/B, consigna y NaN: tres pestañas independientes, conteos por escenario, matriz compacta de elasticidades fiables, configuración reutilizable y tabla completa plegada.

#### PYTHON: contratos nuevos y relaciones

**Guías y pestañas educativas.** `guias_educativas.py` contiene el diccionario editorial `GUIAS`, sin cálculo físico. `construir_guias()` no recibe argumentos y devuelve un `dict[str, str]` con resúmenes y detalles plegables; `construir_pestanas()` tampoco recibe argumentos y devuelve `dict[str, dict[str, str]]`, con claves `resumen` y `teoria` por sección. Ambas recorren `GUIAS`, usan `html.escape` y comprensiones con `''.join(...)` para unir fragmentos; no tienen unidades ni validaciones físicas, y una clave editorial ausente produce `KeyError`. Las llama `renderizar_dashboard` y las pruebas, sin llamar evaluadores. Ejemplo: `construir_pestanas()['sensibilidad']['resumen']` obtiene HTML estático. Las ecuaciones explican el modelo existente; no modifican estados, óptimos ni mapas.

Las seis secciones técnicas tienen exactamente dos pestañas educativas: Uso y configuración (resumen visible, formularios y resultados) y Fundamentos y procedimiento (teoría). Informes y Ayuda conservan guías sin estas pestañas; no hay introducción global repetida. JavaScript limita los botones educativos a `:scope > .edu-tabbar > [role="tab"]`: los visores de gráficas anidados mantienen sus propios controles. El manejador local `select(index, moveFocus=false)` recibe índice entero y booleano, no devuelve valor y sólo cambia `hidden`, selección ARIA, tabulación y foco; lo llaman clics, flechas, Home/End e inicialización, sin solicitudes ni cálculos. Cambiar de vista conserva los mismos campos y valores en el DOM. Si la validación detecta un campo inválido en una vista oculta, el evento `invalid` abre su sección y pulsa la pestaña asociada mediante `aria-labelledby` antes de que el navegador enfoque el control. Sin JavaScript ambos niveles permanecen legibles y al imprimir se muestran también los fundamentos. CSS y JavaScript se incrustan en los informes autónomos.

Revisión del 21 de octubre de 2026: seis pruebas específicas y diez específicas/adaptadas correctas; suite completa final única **184/184 OK en 125.071 s**. Las pruebas anteriores cuentan ahora sólo botones de gráficas y comprueban la ausencia de introducción global. Navegador real: independencia de ambos niveles de pestañas, recuperación del campo inválido, resúmenes y controles de las seis secciones, teclado y valores conservados sin recalcular. La autonomía y descarga se verifican en la suite, sin regenerar informes del usuario ni afirmar validación experimental.

Los contratos físicos de parámetros/ciclos son los ya explicados. Estas funciones sólo presentan o recuperan datos; sus salidas no validan un motor real. HTML ya construido se marca seguro únicamente cuando procede de presentadores controlados; textos/valores se escapan. No se añaden dependencias: Jinja2 ya acompaña a Flask.

- **`json_seguro(datos)`** recibe estructuras JSON (dict/list/escalares finitos) y devuelve str ASCII con `<`/`&` escapados como secuencias Unicode. No calcula física ni llama funciones propias; la llama `renderizar_dashboard`. `allow_nan=False` rechaza NaN/inf con ValueError; tipos no serializables causan TypeError. Evita que un valor cierre el script inerte de metadatos. Ejemplo: `json_seguro({'x':'</script>'})` conserva el texto como datos, sin etiqueta ejecutable.
- **`renderizar_dashboard(valores, *, contenidos=None, metadata=None, informes=(), errores=None, modo_local=True, informe_actual='', seccion_inicial='simulacion')`** recibe dict de valores de formulario (delta en %), paneles HTML controlados, metadatos dict, secuencia de informes, errores dict, bool local, HTML de ficha actual y sección str. Devuelve HTML str. Lee plantilla/CSS/JS/SVG/OFL; llama `json_seguro` y Jinja Environment. La llaman `terminar_informe`, `index`, `ver_informe`, `error_interno` y pruebas. En local referencia `/static/`; en autónomo incrusta CSS/JS y tres fuentes Base64. Propaga errores de archivo, plantilla y contratos; no los confunde con inviabilidad. Ejemplo: `renderizar_dashboard(valores_formulario())`. Los argumentos tras `*` se pasan por nombre para no confundir opciones de presentación.
- **`tarjeta_kpi(clave, etiqueta, valor, unidad, explicacion, decimales=3)`** recibe identificador/etiquetas str, escalar o None, unidad str y precisión entera. Devuelve article HTML con data-kpi para pruebas, unidad y disponibilidad. Sólo formatea/escapa; no llama funciones propias y la llama `terminar_informe`. Magnitudes físicas usan tres decimales, recuentos cero; no se redondean cálculos originales. Contratos incorrectos propagan errores de formato. Ejemplo: `tarjeta_kpi('W','Trabajo',None,'kJ/kg','Sin motor')` muestra No disponible.
- **`plegable(titulo, contenido)`** recibe título str y HTML técnico ya escapado; devuelve details/summary cerrado. La llama `terminar_informe`; sin otras llamadas propias ni física. Ejemplo: `plegable('Estados',tabla_html(('T [K]',),[(300,)]))`. El contenido se conserva completo, no se elimina al plegar.
- **`separar_presentacion(contenido)`** recibe HTML str y retorna `(metadata,paneles)` o None si es histórico, JSON inválido o faltan marcadores. Busca script inerte `brayton-metadata` con esquema `dashboard=1` y tres bloques heredados delimitados por comentarios, más los paneles mapa/segunda ley opcionales cuando existen, sin ejecutar código. La llaman `ver_informe`, `listar_informes` y pruebas. No llama funciones propias; errores de tipo fuera de contrato propagan. Ejemplo: `separar_presentacion(html_guardado)`. La recuperación no recalcula ni modifica el archivo.
- **`visor_graficas(legado, imagenes, sensibilidad=False)`** recibe HTML técnico heredado y dict de bytes PNG existentes, bool OFAT; devuelve tupla `(visor,detalles,cabecera)`. Asocia cada figure a su PNG Base64 y grupo, sin volver a dibujar ni cambiar bytes. Exige conservar exactamente el número de imágenes; ValueError si no se conserva, errores de contrato si faltan asociaciones. La llama `terminar_informe`; no llama otras funciones propias. Ejemplo interno: `visor_graficas(legado,imagenes)` produce cinco botones y siete figure únicos; en OFAT, tres botones y tres figure. Se retiran sólo las figuras de la copia de detalles para evitar duplicados; sus tablas y textos se mantienen, convirtiendo section heredadas en div técnicos.
- **`terminar_informe(legado, parametros, imagenes, fecha, version, *, noideal=None, barrido=None, optimizaciones=None, estudio_rendimiento=None, comparacion=None, sensibilidad=None, segunda_ley=None, diagnosticos=None)`** recibe datos calculados por main o estudio OFAT, datetime y versión Git; retorna HTML str con las mismas marcas de informe completo. `diagnosticos` es `dict` de panel→diagnóstico o `None`; guarda esos registros en metadata y añade su HTML con `renderizar_diagnostico` (§4.56). Llama visor, KPI, plegables y renderizador; la llaman los creadores normal y OFAT de reporting. No llama evaluadores físicos. Construye KPI/A/B y elasticidades desde los diccionarios, nunca desde constantes de ejemplo. Convierte pérdida a % sólo para campos de formulario, conserva fracción en metadata. Errores de presentación/contrato propagan. Ejemplo de uso: ejecutar `main(carpeta_de_prueba)` lleva los resultados a esta función antes de guardar.
- **`listar_informes()`** — web_app: sin argumentos; lee `app.config['OUTPUTS_DIR']` y devuelve lista de dict `nombre/tipo/resumen/fecha/commit/mtime`, de más reciente a antiguo. Filtra patrón, archivos regulares no simbólicos, UTF-8 y marcas completas. Llama `separar_presentacion`; la llaman index, vista y manejador de errores. No elimina, escribe ni recalcula. Datos históricos no disponibles se identifican como tales; no se atribuyen parámetros/fechas inventados. Carpeta inexistente da lista vacía. Errores inesperados de E/S propagan; archivos desaparecidos durante lectura se omiten. Ejemplo: `listar_informes()` dentro de la configuración de pruebas.
- **`ver_documentacion(nombre)`** — web_app: recibe str y devuelve Response text/plain de README.md o CODE_WALKTHROUGH.md; cualquier otro nombre da 404. Flask la llama por `/documentacion/<nombre>`; sin otras funciones propias ni física. No ofrece rutas arbitrarias. Ejemplo HTTP: GET `/documentacion/README.md`.

`GRUPOS` y `CAMPOS` residen ahora en dashboard.py y se reexportan por los imports de web_app; claves, valores físicos predeterminados y validación se conservan. `index` usa el renderizador y listado; POST distingue main, OFAT, mapa y segunda ley, y redirige con 303; los dos flujos nuevos se detallan en §§4.42 y 4.44. `ver_informe` descarga exactamente el HTML original antes de cualquier transformación. En la vista nueva recupera paneles/entradas y vuelve a renderizar el formulario editable; en informes anteriores conserva el HTML original con navegación local. `error_interno` usa la misma plantilla compartida, conserva valores y sigue distinguiendo error de programa de rechazo físico.

`crear_informe_html` y `crear_informe_sensibilidad_html` mantienen firmas y datos; primero forman la presentación técnica existente y después llaman `terminar_informe`. Así no se descarta información académica ni se duplica la física. `guardar_informe_html`, verificación de PNG, consulta Git y política de cuatro permanecen intactas. Las 108 pruebas anteriores se conservan; el parser de pruebas ignora href de fragmentos internos (no son dependencias externas) y el test de escape OFAT distingue JS legítimo del dashboard de metadatos escapados.

#### CSS, JavaScript y accesibilidad reales

La paleta es #F5F7FA/#FFFFFF con azul petróleo #174A70, interacción #2563A6, texto #172B42, secundario #65768A y bordes #DFE6EE. IBM Plex Sans Regular/SemiBold para texto y Mono Regular para cifras, instaladas como WOFF2 locales de IBM/plex con SIL OFL 1.1 y commit de origen en static/fonts/SOURCE.md. El autónomo incluye los mismos archivos en CSS Base64 y copia de licencia en Ayuda; no solicita Google Fonts/CDN. El SVG es original geométrico, CC0-1.0, decorativo y no a escala: no añade modelo de tobera ni empuje.

Grid usa `minmax(0,1fr)` y contenedores con `min-width:0` para no ensanchar la página. Tres KPI por fila en escritorio amplio, dos por debajo de 1150 px, uno en teléfonos muy estrechos. Sidebar pasa a menú compacto por debajo de 760 px. Sólo `.table-wrap` tiene scroll horizontal para tablas técnicas; el resto adapta sus columnas. Focus visible y movimiento reducido se respetan.

El script local es mejora progresiva. Sólo añade clase `js` si hay paneles; CSS oculta inactivos únicamente bajo esa clase. Sin JS se muestran todas las secciones/figuras y details nativos siguen funcionando. `activateSection(id,focus=false)` activa panel y aria-current sin cálculos; `locationSection()` interpreta fragmento y pestaña. Los listeners delegados actualizan history.pushState sin saltos nativos innecesarios y manejan Atrás/Adelante. `selectTab(button)` filtra los mismos figure mediante clases, actualiza aria-selected/tabIndex/aria-labelledby; Flechas/Home/End recorren botones reales. El cierre por visor captura sus figuras/botones; todos esos callbacks son locales a su inicialización y no almacenan resultados entre simulaciones.

`enlarge(figure,button)` utiliza el src de una figura ya presente, abre dialog nativo y recuerda el botón. Escape/cerrar restauran foco al disparador; no descarga otra imagen. Los listeners de impresión abren details temporalmente y luego restauran su estado. El selector OFAT sólo propone rangos del catálogo JSON; cambiar pestaña no hace fetch ni una nueva optimización. La validación nativa de un campo oculto activa su sección antes de mostrar el error. En archivos autónomos se deshabilitan los controles de ejecución para no intentar POST al sistema de archivos: consultar no requiere Flask; ejecutar otro caso sí.

#### Verificación de esta intervención

Comprobación de cierre del rediseño (21 de octubre de 2026): suite completa **123/123 OK en 93.985 s**, sin cambiar el código. La primera ejecución en sandbox sufrió errores de permisos en carpetas temporales; la repetición fuera de esa restricción pasó. Se revisaron de nuevo simulación normal, navegación, pestañas por teclado, tablas y OFAT con muestras inviables desde Flask aislado. Descarga, retención de cuatro informes y ejecución directa se comprueban en la suite. La apertura interactiva `file://` sigue bloqueada por la política del navegador; los recursos autónomos se verifican mediante pruebas. Detalles del cierre en la guía de aprendizaje del rediseño.

Primera suite: 123/123 pruebas OK en 124.582 s (108 anteriores + 15 nuevas). Verificación final: 123/123 pruebas correctas en 70.814 s; se conservan las 108 previas y se añaden 15 de dashboard. Las nuevas pruebas comprueban datos/KPI no hardcodeados, None/supremos, seis secciones, nueve entradas, 7/3 PNG sin duplicados, plegables, recursos incrustados/licencias, JSON seguro, historial sólo lectura, descarga idéntica, compatibilidad histórica y documentos permitidos. Las pruebas estáticas de HTML/CSS/JS **no** se presentan como verificación de interactividad.

En navegador real: simulación normal, cambio de pestaña, comparación A/B, ampliación y Escape con retorno del foco; ejecución OFAT con muestras inviables y sus pestañas. Viewport de escritorio 1440 px y móvil 393 px; comprobación DOM de anchura sin overflow horizontal. Recursos e informes de revisión en carpeta aislada, servidor temporal sólo 127.0.0.1:5015; el puerto normal sigue en 5000. Comprobación adicional del autónomo y limitaciones de revisión en la guía del rediseño. Fuente física, algoritmos, dependencias, PNG históricos y guías de fases anteriores intactos. El rediseño quedó registrado en `2996ad9adb7b082ac36531bcf940b7e18986202a` y fusionado en `b6fdfbeb5aa63605734258449f05a9ff3f964946`; los resultados anteriores corresponden a su revisión, no a las pruebas de Fase 5.

### 4.42. Mapa bidimensional de diseño rp–T3 (Fase 5)

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Se varían rp y T3 simultáneamente, a T1, p1, cp, gamma, eta_c, eta_t y pérdida relativa fijas. Se reutilizan las ecuaciones, dominios abiertos, tolerancias y máximos de Fases 1–4. W y Qin se conservan con signo aun sin motor; eta sólo existe para puntos motores. La matriz de rendimiento está en %, los registros de evaluación en fracción. No se añaden combustible, caudal, potencia, empuje, tobera ni propiedades variables.

**PYTHON y estructura.** `mapa_diseno.py` devuelve un estudio dict: referencia/configuración, ejes rp/T3, filas con muestra de dominio/A/B y puntos completos, matrices W/Qin/eta, máscaras bool viable/limite_numerico, motivos object, fronteras, trayectorias, índices de contraste, cortes y tiempos. Todas las matrices tienen forma `(n_T3,n_rp)`; filas son temperaturas. `matrices['trabajo_neto'][i,j]` corresponde a `T3[i]` y `rp[j]`. El estudio es nuevo en cada llamada; sólo se reutilizan datos de su propia ejecución.

#### Contratos y relaciones de las funciones

Los tipos de referencia y parámetros son dict de escalares reales con las nueve claves de §5; configuración es dict, filas lista de dict, temperaturas/relaciones secuencias de números y estudio dict. T [K], rp sin dimensión, cp [J/(kg·K)], p1 [kPa], W/Qin [kJ/kg]; los tiempos son segundos. Los errores de contrato o programación propagan, no se renombran inviabilidad física. Los límites numéricos físicos se capturan como `ErrorNumerico` por celda o registro A/B.

| Firma completa | Contrato y relaciones |
|---|---|
| `validar_configuracion(referencia, rp_min=1., rp_max=100., T3_min=600., T3_max=2000., n_rp=100, n_T3=80, escala='log', cortes=())` | Devuelve dict normalizado; llama `argumentos_fisicos` y `validar_parametros`; Flask y `analizar_mapa` la llaman. Límites finitos, rp positiva ordenada, T1<T3min<T3max; enteros 3–401, hasta 20000 celdas, escala lineal/log, hasta cinco cortes incluidos. ValueError si falla. Cortes vacíos proponen extremos y centro. |
| `crear_malla(configuracion)` | Devuelve `(rp,T3)` como arrays 1D; la llama `analizar_mapa`; NumPy crea ejes. Rechaza pasos indistinguibles con ValueError. Ejemplo: `crear_malla(validar_configuracion(p,n_rp=3,n_T3=3))`. |
| `evaluar_fila(referencia, temperatura, relaciones, verificar=False)` | Devuelve dict `T3/muestra/puntos`. Llama `evaluar_muestra` una vez y `evaluar_punto` por columna. La llaman análisis y cortes. Captura sólo ErrorNumerico por celda (NaN y motivo), no RuntimeError ni defectos del programa. Ejemplo: `evaluar_fila(p,1600,[1,10,100])`. |
| `obtener_mascaras(filas)` | Devuelve dict de dos matrices bool: viable y limite_numerico. La llama análisis, sin otras llamadas propias; comprensión anidada sigue filas y puntos. Ejemplo: `obtener_mascaras([fila])` produce forma `(1,n_rp)`. |
| `extraer_fronteras(filas)` | Devuelve cuatro arrays de rp: inferior/superior motor, expansión y calor. Sin resolver otra vez dominios; análisis la llama. Sin dominio motor, fronteras motoras NaN; sin dominio calculable, todas NaN. Ejemplo: `extraer_fronteras([fila])['inferior']`. |
| `obtener_trayectorias(filas)` | Devuelve dict A/B con registros y arrays rp; no llama física, la llama análisis. Sólo `disponible` produce rp finita. Registros conservan estado, ciclo, supremo y contraste. Ejemplo: `obtener_trayectorias([fila])['B']['registros'][0]`. |
| `extraer_cortes(estudio, temperaturas)` | Devuelve lista de filas; reutiliza coincidencias exactas o llama `evaluar_fila` para nuevas T3. La llama análisis. Valida hasta cinco T3 finitas incluidas; ValueError fuera de rango. Ejemplo: `extraer_cortes(e,[1600])`. |
| `analizar_mapa(referencia, **configuracion)` | Orquesta validación, ejes, filas, máscaras, fronteras, trayectorias y cortes; devuelve estudio dict y segundos de cálculo. La llama `ejecutar_mapa`. `**` expande controles por nombre; `.copy()` evita modificar referencia. Ejemplo: `analizar_mapa(p,n_rp=9,n_T3=5)`. |
| `preparar_resultados(estudio)` | Devuelve prestaciones enmascaradas y recuentos motores/celdas/límites numéricos, sin recalcular. La llaman gráficas y reporting. Ejemplo: `preparar_resultados(e)['motores']`. |
| `crear_graficas_mapa(estudio)` | Devuelve dict nombre→bytes PNG, tres mapas más un PNG de dos ejes por corte. Llama preparación; la llama ejecución. `try/finally` cierra cada figura incluso ante error. Ejemplo: `crear_graficas_mapa(e)['mapa_viabilidad.png']`. |
| `ejecutar_mapa(carpeta_salida, parametros, **configuracion)` | Devuelve Path del HTML guardado. Llama análisis, gráficas, reporting/versión Git/guardado; Flask la llama. Mide cálculo y preparación; propaga errores de E/S, contrato y programa. Ejemplo: `ejecutar_mapa(carpeta_temporal,p,n_rp=9,n_T3=5)`. |
| `reporting.crear_informe_mapa_html(estudio, imagenes, fecha, version_git)` | Devuelve HTML str con marcas de informe completo; datetime y versión Git dict. Llama preparación, imagen/tabla/plegable y renderizador; la llama ejecución. Registra tiempo HTML en el estudio. KeyError por estructuras incompletas, ValueError por PNG inválido/JSON no finito, errores E/S de recursos propagan. Ejemplo: `crear_informe_mapa_html(e,imagenes,fecha,version)`. |


Ejemplo de validación: `c = validar_configuracion(p, n_rp=9, n_T3=5, cortes=(1600,))`; luego `e = analizar_mapa(p, **c)` conserva los parámetros originales. `**c` desempaqueta claves como argumentos por nombre. Las comprensiones anidadas recorren primero filas y luego columnas. `np.empty(..., dtype=object)` aloja tuplas de motivos, cuyo número puede variar sin cambiar la forma de la matriz. `np.ma.array(W, mask=~viable)` invierte la máscara motora para excluir celdas del color sin destruir sus energías con signo.

#### Dominio, búsqueda y ventana visual

La configuración inicial 1–100, 600–2000 K, 100×80 es una ventana, no una frontera. Se exigen límites finitos ordenados, rp>0, T3min>T1 y hasta 20000 celdas; 3–401 muestras por eje, escala lineal/log y uno a cinco cortes. Un rango parcialmente T3<=T1 se rechaza completo con explicación; no se recorta silenciosamente. Un dominio motor vacío dentro de un rango matemático válido es un resultado admitido.

Cada fila llama una vez a `sensibilidad.evaluar_muestra`: obtiene dominio fresco, candidatos analíticos y comprobación física de A/B. Sólo índices 0, n_T3//2 y n_T3−1 solicitan los contrastes numéricos independientes existentes, que pueden calcular dominios dentro de su propia API. No hay optimización por celda. La malla de búsqueda de los optimizadores sigue siendo independiente de las columnas. Un máximo fuera de ventana permanece completo en los datos y tablas; sólo su línea se corta mediante NaN en la imagen. Un supremo reversible conserva su registro sin punto B. No se busca el máximo por el color o por `argmax` de la malla.

Los mapas W/eta usan arrays enmascarados, fondo gris y `pcolormesh(shading='nearest')`, sin interpolación de contornos a través de puntos excluidos. Viabilidad muestra dos clases, con fronteras motoras, expansión y calor superpuestas desde los dominios, no inferidas de píxeles. Gris agrupa no motor y límite numérico: las máscaras, motivos y recuentos los distinguen. La discretización no determina una frontera exacta.

Los cortes guardan temperaturas exactas del rango (hasta cinco). Si coinciden con una fila se reutiliza esa fila; si no, se evalúa sólo esa temperatura adicional. W/eta son NaN fuera de motor, la banda muestra dominio abierto y los máximos A/B se marcan sólo cuando están alcanzados y dentro de vista. Un corte comparte el eje rp de la malla: refinarlo mejora la curva, no la precisión del óptimo.

#### Integración, recursos y ejecución

`web_app.index` añade acción mapa y validación independiente: seis números, escala y cortes. Sigue usando los nueve parámetros físicos existentes. `ejecutar_mapa` devuelve Path, el POST redirige con 303 y `ver_informe` recupera el formulario/mapa desde metadatos, sin calcular. `listar_informes` distingue Mapa de diseño. El panel opcional se extrae mediante `separar_presentacion`; un informe anterior sin él continúa siendo compatible. Se mantienen los tres paneles técnicos anteriores.

`crear_informe_mapa_html` compone siete parámetros fijos y unidades, configuración, máscaras/recuentos, tres PNG principales, cortes, A/B/Qin/estado/supremo/dominios y advertencias, con tabla plegada. Usa el renderizador compartido, JSON seguro, recursos incrustados, fuentes IBM Plex y metadatos Git. No escribe versiones antiguas. `guardar_informe_html` conserva la misma publicación y retención de cuatro documentos, compartida por los tres tipos de estudio.

La nueva sección reutiliza estilos y navegación. Sus pestañas reutilizan el visor existente; `selector-corte` filtra figure con `data-corte` mediante clases, sin fetch ni cálculo. Sin JS, todos quedan visibles. Los controles de cálculo se deshabilitan en el autónomo; consultar mapas y seleccionar cortes no requiere Flask ni Internet. `perf_counter` mide cálculo, preparación y HTML; el informe muestra tiempos anteriores a su composición, y el tiempo total se mide desde fuera para incluir HTML/guardado.

#### Verificación y resultados actuales

La prueba inicial del módulo detectó una comparación binaria sensible a CRLF de Windows; se ajustó a la comparación textual que utiliza la ruta heredada, sin cambiar el código de descarga. Las 21 pruebas específicas pasaron en 5.171 s. Se conservan los 123 métodos anteriores; únicamente dos expectativas de controles pasan de 12 a 18 por los seis nuevos campos numéricos. Verificación inicial del mapa, anterior a las mejoras educativas: **144/144 pruebas OK en 96.679 s**, ejecutada con `python -B -m unittest discover -s tests -q` fuera del sandbox por sus restricciones conocidas de permisos temporales. Verificación AST: los 123 métodos anteriores siguen presentes. Comprobación visual desde Flask aislado: envío de mapa, Trabajo/Rendimiento/Viabilidad, selector de cortes, ampliación y Escape con foco restaurado; simulación normal con siete PNG y OFAT con tres PNG y muestras inviables. Anchura DOM 1204 px dentro de viewport 1219 px, sin desbordamiento horizontal. El HTML autónomo se verifica mediante pruebas de recursos y descarga, no mediante una apertura interactiva file://. No se certifica revisión móvil adicional en esta tarea.

Revisión de cálculo del 21 de octubre de 2026: malla 80×100, 6482/8000 motores; cálculo 0.146 s, cálculo+seis PNG 3.381 s, HTML/guardado 0.380 s, total 3.761 s. A T3=1600 K se mantienen A rp=12.89505167, W=373.21082748 kJ/kg y eta=39.21261442 %; B rp=35.45232357, W=313.73891526 kJ/kg y eta=43.89310716 %. Con eta_c=.6, eta_t=.7, delta=.2, 30×15: 125/450 motores y seis filas vacías. Reversible: 399/450 motores y B supremo no alcanzado. Son comprobaciones internas, no validación externa ni garantías de velocidad.

La base es el merge `b6fdfbeb5aa63605734258449f05a9ff3f964946`; Fase 5 permanece sin commit en `feature/fase-5-mapa-rp-t3`. Véanse [milestone 08](docs/milestones/08_mapa_diseno_rp_t3.md) y [aprendizaje independiente](docs/milestones/08_mapa_diseno_rp_t3_APRENDIZAJE.md) para experimentos y revisión de esta fase.

### 4.43. Explicaciones educativas compartidas en los informes

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** La presentación explica el ciclo simplificado, trabajo de compresor/turbina, calor, trabajo neto y rendimiento; distingue energía específica [kJ/kg] de potencia [kW] y aclara que no se calcula empuje. No cambia física, sensibilidad, optimizadores, mapas, PNG ni resultados. Las explicaciones universales son textos técnicos estáticos; los parámetros y observaciones se incorporan a plantillas sencillas usando resultados existentes, sin IA ni motor de inferencia.

**PYTHON y ubicación.** `dashboard.py` concentra `INTRODUCCION` (str), `GLOSARIO` (tupla de pares término/definición), `EXPLICACIONES_GRAFICAS` (dict de nombres→str), `TEXTO_OPTIMIZACION` y `TEXTO_DISPONIBILIDAD` (str). No guardan datos de ejecuciones. `renderizar_dashboard` pasa esos textos y `tiene_informe=bool(metadata)` a la misma plantilla de Flask/HTML autónomo. La constante INTRODUCCION se conserva por compatibilidad, pero la plantilla ya no la representa como bloque global: los resúmenes y fundamentos proceden de `guias_educativas.py` y se separan por sección (§4.41). El glosario aparece una vez en Ayuda. No se añaden dependencias.

#### Funciones nuevas y contrato actualizado

- **`bloque_educativo(titulo, texto)`**: ambos argumentos str de texto plano, sin unidades propias; devuelve tarjeta HTML str. Sólo presenta, no calcula ni valida física. Usa `escape` en ambos textos; no admite HTML aportado por el llamador. La llaman `terminar_informe` y `crear_informe_mapa_html`; no llama otras funciones propias. Entradas no textuales fuera de contrato propagan TypeError/AttributeError. Ejemplo: `bloque_educativo('Objetivo','A maximiza trabajo por kilogramo.')`. Las f-strings insertan texto escapado en las etiquetas existentes.
- **`conclusiones_html(observaciones)`**: iterable de str ya derivados de datos, sin unidades impuestas por el helper; devuelve HTML con título y hasta cuatro elementos escapados. No decide tendencias ni calcula física. La llaman `terminar_informe` y el creador del mapa. Sin observaciones muestra una limitación de fiabilidad; tipos incorrectos propagan. Usa `list`, corte `[:4]`, comprensión y `join`; no llama funciones propias. Ejemplo: `conclusiones_html(['2 de 3 muestras tienen ciclo motor.'])`.
- **`parametros_fijos_texto(parametros, variables)`**: dict de parámetros físicos y colección de claves excluidas; devuelve str con nombres, valores y unidades de entradas no variables. T [K], p1 [kPa], cp [J/(kg·K)], rp/gamma sin dimensión, eficiencias/delta en fracción. La llama `terminar_informe` para OFAT; no llama física ni otras funciones propias. Claves desconocidas o valores no formateables propagan KeyError/TypeError/ValueError. Ejemplo: `parametros_fijos_texto(p,('T3','relacion_presiones'))` lista las otras siete entradas. El filtro `if k not in variables` evita declarar fija una entrada barrida o reajustada.
- **`imagen_html(imagen, titulo, explicacion=None)`** conserva su contrato anterior con un tercer argumento opcional, documentado en §4.21. El mapa añade el párrafo de su diccionario de textos; los cortes comparten una sola explicación junto al selector, evitando repetirla por PNG.

#### Gráficas y objetivos

`visor_graficas(legado, imagenes, sensibilidad=False)` identifica el PNG por su nombre ya asociado y añade una explicación escapada después de su figcaption. Conserva agrupación, datos Base64 y número de imágenes. Los siete textos normales explican ejes, variables/fijos, procesos ideales 1→2→3→4→1 y el distinto comportamiento de W y eta. Los tres OFAT aclaran R/A/B, consigna frente a puntos motores, % relativo frente a puntos porcentuales. Los tres mapas explican color, región gris (incluye límites numéricos), fronteras, trayectorias por T3 y que no se optimiza T3 globalmente.

Antes de resultados A/B se presentan los objetivos, máximo interior, supremo no alcanzado y dominio vacío. En el mapa se sitúan dentro de la tabla plegable existente, antes de los resultados; en Optimización, antes de las tarjetas. `terminar_informe` añade el parámetro/rango/unidad/muestras OFAT y las entradas fijas. Excluye del listado fijo la variable seleccionada y rp, que se reajusta en A/B; la consigna R se indica por separado. La explicación de sensibilidad S=(x/Y)dY/dx señala su carácter local, relativo y su posible indisponibilidad.

#### Conclusiones sin tendencias inventadas

Normal: informa W a la rp introducida, rp de A/B cuando existen y el sacrificio W[%]/ganancia eta[pp] desde `comparacion_criterios`, sólo si ambos cambios tienen signo compatible. Si B es supremo lo presenta como límite no operativo; si faltan datos indica la limitación. No declara diferentes dos rp por redondeo ni inventa un máximo.

OFAT: tres observaciones, una por escenario, cuentan disponibilidad/inviabilidad/supremos/límites desde los registros calculados. No deducen una tendencia global del primer/último punto. Mapa: cuenta celdas motoras, máximos alcanzados por temperatura y, cuando corresponde, filas vacías, supremos o máximos fuera de vista. La lista se limita a cuatro observaciones. No confunde un dominio vacío con una ventana que no intersecta al dominio.

Los bloques se guardan dentro de los paneles del informe. Flask los recupera sin duplicarlos; los resúmenes por sección, fundamentos y glosario se renderizan con la plantilla compartida. Los informes anteriores guardados no se reescriben ni se enriquecen retrospectivamente. HTML autónomo conserva fuentes, CSS/JS y PNG incrustados.

#### Verificación actual

**Ajuste final de legibilidad.** `static/style.css` distingue la introducción, notas, conclusiones y explicaciones de figuras mediante tipografía de 13 px, interlineado 1,65, borde lateral discreto y fondo suave. El glosario utiliza descripciones en IBM Plex Sans con columnas adaptativas, en lugar de mostrar definiciones largas como números monoespaciados. `tests/test_explicaciones.py` incluye una comprobación estática de estos estilos; no equivale a una prueba visual en navegador.

Las 16 pruebas educativas superaron la última comprobación de módulo en 7.443 s. Verifican explicaciones normales/OFAT/mapa, variables/fijos, supremos, conclusiones dependientes de datos y signos, escape, autonomía y textos compartidos con Flask. Las fixtures de presentación reutilizan PNG distintos de una simulación temporal; no redibujan las gráficas para cada prueba. No se confunden estas pruebas de texto con una revisión de píxeles o validación experimental. La suite previa al desarrollo de segunda ley superó **160/160 pruebas en 239.457 s**: 144 previas y 16 educativas. Esta mejora pertenece a Fase 5: véase la iteración correspondiente en la guía 08, sin milestone nuevo.

### 4.44. Segunda ley y destrucción parcial de exergía

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** `segunda_ley.py` recibe los estados clasificados existentes y no vuelve a resolver el ciclo. Para cada modelo usa R=cp(1−1/gamma) [J/(kg·K)] y s_j−s_i=[cp ln(Tj/Ti)−R ln(pj/pi)]/1000 [kJ/(kg·K)], con s1=0 arbitrario. No son entropías absolutas. En régimen estacionario adiabático, s_gen,c=s2−s1 y s_gen,t=s4−s3. Gouy–Stodola da eD=T0·s_gen [kJ/kg]. La suma es exclusivamente compresor+turbina: no destrucción de toda la instalación ni diferencia directa W_ideal−W_noideal.

La cámara muestra s3−s2 y contribuciones térmica/de presión, sin etiquetarlas como generación. Para cerrar su balance faltan transferencias de entropía con el calor y temperaturas de frontera, o combustión. No se inventa una fuente térmica, exergía absoluta de flujo o eficiencia exergética global. Se mantienen cp/gamma, eficiencias y pérdida relativa constantes, sin caudal ni empuje.

**PYTHON y datos.** El estudio contiene T0/cp/gamma y `modelos` ideal/noideal: clasificación, motivos, cuatro T/p/s, `componentes` con valor bruto/tolerancia/s_gen/eD, suma parcial y cámara descompuesta. Antes de reutilizar un JSON histórico, `validar_estudio_reutilizable` exige campos/tipos correctos, nueve entradas coincidentes y relaciones numéricas coherentes; si falla, `ejecutar_segunda_ley` calcula un estudio nuevo a partir de las entradas válidas. La comprobación no garantiza autenticidad de un HTML que alguien pueda modificar. `actualizar_T0` copia profundamente un estudio admisible y sólo cambia eD. No altera entradas, calor, trabajo, óptimos ni mapas. El nuevo T0 no pertenece a `PARAMETROS_PREDETERMINADOS` ni a los nueve parámetros físicos.

#### Firmas, argumentos, retorno, unidades y llamadas

Los argumentos reales son finitos salvo que se esté verificando su rechazo. T [K], p [kPa], cp [J/(kg·K)], gamma sin dimensión; s [kJ/(kg·K)], eD [kJ/kg]. `punto` es el dict original de `evaluar_punto`; `estados` contiene los dos puntos; estudio es un dict. Ejemplos de la tabla usan `p` para los nueve parámetros, `pi/pn` para puntos y `e` para estudio. No hay cálculo de potencia.

| Firma completa | Uso, argumentos, retorno, errores y relaciones |
|---|---|
| `validar_referencia(T0)` | Real → float positivo finito [K]; ValueError para cero, negativos, no finitos o bool. La llaman main, rutas/ejecución y funciones de análisis/actualización; no llama funciones propias. Ejemplo: `validar_referencia(288.15)`. |
| `cambio_entropia(Ti, pi, Tj, pj, cp, gamma)` | Seis reales → dict `termica/presion/total`. ValueError para estados/propiedades inválidos; ErrorNumerico ante escala no representable o resultado no finito. La llama `analizar_estados`; usa log e isfinite. Ejemplo: `cambio_entropia(300,100,600,100,1005,1.4)`. |
| `generacion_adiabatica(s_entrada, s_salida, escala=1.)` | Reales en unidades de s → dict `valor/bruto/tolerancia`. ValueError por no finitos/escala no positiva, ErrorNumerico por diferencia infinita, InconsistenciaSegundaLey por negativo importante. La llama análisis de estados; no llama funciones propias. Ejemplo: `generacion_adiabatica(0,.08,1.005)`. |
| `analizar_estados(punto, cp, gamma, T0=288.15)` | Registro clasificado y propiedades → dict de estado, entropías, componentes, suma y cámara; conserva motivos motores originales. Llama validación, cambio y generación. Inconsistencia: retorna diagnóstico con entropías y motivo, sin eD; errores de entrada/números propagan al agregador. Ejemplo: `analizar_estados(punto,1005,1.4)`. |
| `analizar_segunda_ley(estados, cp, gamma, T0=288.15)` | Dict ideal/noideal → estudio con T0/cp/gamma/modelos. Llama validación y análisis por modelo; registra límites numéricos separadamente, sin ocultar entradas inválidas. La llaman main y ejecución diagnóstica. Ejemplo: `analizar_segunda_ley({'ideal':pi,'noideal':pn},1005,1.4)`. |
| `validar_estudio_reutilizable(estudio, parametros)` | `dict` JSON con T0/cp/gamma, `modelos` ideal/noideal y sus cuatro T [K], cuatro p [kPa], entropías [kJ/(kg·K)], generaciones/exergías; `parametros: dict` con los nueve parámetros → `bool`, sin mutación. Rechaza ausencias, listas incorrectas, `bool` como número, valores no finitos, estados incompatibles con las entradas, clasificaciones, balances de entropía y exergía inconsistentes. Utiliza `type`, `isfinite`, `isclose`, `cambio_entropia`, `generacion_adiabatica` y la banda `TOL_REL`, pero **no llama** a `evaluar_punto` ni genera gráficas; la invocan `web_app.estudio_conservado` y `ejecutar_segunda_ley`. Las estructuras de límite numérico/inconsistencia sin estados completos no se reutilizan. Ejemplo: `validar_estudio_reutilizable(e, p)` → `True` para un caso íntegro, `False` para un componente ausente. No verifica autenticidad ni sustituye validación experimental. |
| `actualizar_T0(estudio, T0)` | Estudio y real → copia con T0 y eD nuevas. Validación y deepcopy; ErrorNumerico si desborda. Conserva modelos no cuantificables y no calcula física. La llama ejecución. Ejemplo: `actualizar_T0(e,300)`. |
| `crear_graficas_segunda_ley(estudio)` | Estudio → dict `estados_ts/exergia_componentes` con SVG str. La llama presentación; Matplotlib/StringIO, cierre en finally e identificadores separados entre SVG. No llama física. Ejemplo: `crear_graficas_segunda_ley(e)['estados_ts']`. |
| `ejecutar_segunda_ley(carpeta_salida, parametros, T0=288.15, estudio_previo=None)` | Path/str, dict de nueve parámetros, T0 y estudio opcional → Path del HTML. Revalida el estudio también ante llamadas directas; reutiliza sólo si es coherente y entonces llama `actualizar_T0`. Ante JSON inválido evalúa ideal/noideal una vez y analiza, sin optimizadores/barridos. Llama reporting/Git/guardado. Flask la llama; errores numéricos/entrada/E/S permanecen diferenciados. Ejemplo: `ejecutar_segunda_ley(d,p,300,e)`. |
| `web_app.estudio_conservado(nombre, parametros)` | Nombre propio str y dict físico → estudio previo válido o `None`. Comprueba patrón, ruta dentro de OUTPUTS_DIR, archivo no simbólico, marcas, nueve parámetros idénticos y `validar_estudio_reutilizable`; si algo no cumple, permite recalcular. Usa `separar_presentacion`, no vuelve a ejecutar el ciclo. La llama index. Ejemplo: `estudio_conservado(nombre,p)` dentro de configuración local. |
| `reporting.seccion_segunda_ley_html(estudio)` | Estudio → bloque HTML, dos SVG y tablas compactas. Llama gráficas, tablas y helpers educativos/plegable; la llaman informe específico y `terminar_informe`. Escapa textos dinámicos; no calcula estados. Ejemplo: `seccion_segunda_ley_html(e)`. |
| `reporting.crear_informe_segunda_ley_html(parametros, estudio, fecha, version)` | Dict físicos/estudio, datetime y Git dict → HTML autónomo con marcas. Llama sección, renderizador y helpers existentes; la llama ejecución. Propaga errores de contrato/E/S. Ejemplo: `crear_informe_segunda_ley_html(p,e,fecha,version)`. |


#### Estados y tolerancias

La clasificación previa se conserva: entrada inválida produce ValueError; un punto matemático calculable no motor permite entropías diagnósticas; un motor conserva su clasificación; un ErrorNumerico se registra como límite. Errores de programación como KeyError no se ocultan. `InconsistenciaSegundaLey(ValueError)` identifica generación negativa fuera de tolerancia. En ese caso el diagnóstico conserva T/p/s, sin publicar eD.

`generacion_adiabatica` usa tolerancia 1e−10·max(|s_entrada|,|s_salida|,cp/1000). Un negativo dentro de banda se convierte en cero para cuantificar, pero conserva `bruto` y tolerancia; los negativos importantes nunca se recortan. La banda expresa redondeo, no incertidumbre experimental. `log(Tj)-log(Ti)` evita el desbordamiento de cocientes extremos; resultados no finitos o escalas no representables se distinguen de entradas inválidas.

#### Integración y reutilización

`main(...,T0=288.15)` valida la referencia y llama análisis sobre los registros `referencia` existentes. `crear_informe_html(...,segunda_ley=None)` y `terminar_informe(...,segunda_ley=None)` mantienen las llamadas anteriores compatibles. Se añade el panel y los metadatos del estudio, además de los siete PNG originales. Dos gráficas SVG incrustadas muestran estados T-s y barras eD,c/eD,t; sus identificadores se aíslan y los glifos son internos. Las conexiones T-s son sólo guías, no trayectorias de procesos irreversibles. La curva ideal anterior sigue intacta en Resultados.

El campo T0 de la octava sección se valida para normal/segunda ley; no entra en OFAT ni mapas. La acción independiente llama `ejecutar_segunda_ley`: evalúa sólo dos puntos si no tiene resultados previos válidos. Desde un informe conservado, `estudio_conservado` verifica nombre/ruta/marcas, los nueve parámetros y la consistencia física interna del JSON. Las temperaturas se comprueban mediante las relaciones existentes de compresión/expansión, y las entropías, generaciones y eD se contrastan con sus ecuaciones y la referencia T0 **guardada**. Comparación numérica: `isclose` con tolerancia relativa `1e-9`, absoluta `1e-10` sólo en magnitudes entrópicas/derivadas; no representa incertidumbre experimental. La clasificación del punto usa la banda física `TOL_REL` existente. Un JSON inconsistente se descarta **para reutilización**, no se borra: la acción recalcula desde las entradas válidas. Para el JSON válido, actualizar T0 sólo copia entropías/generaciones y multiplica por la nueva referencia, sin invocar `evaluar_punto` en la reutilización. No optimiza ni repite los siete PNG. El diagnóstico se publica como informe propio descargable con recursos incrustados, compartiendo la retención de cuatro documentos. Los informes anteriores no se reescriben.

`dashboard.separar_presentacion(contenido)` devuelve `(metadata, paneles)` sólo si el JSON del script es legible y su envoltorio básico tiene tipos, nueve valores finitos y configuraciones de navegación compatibles; de lo contrario, devuelve `None`. `web_app.listar_informes()` identifica los documentos propios con metadatos dañados, mientras `web_app.ver_informe(nombre)` responde **422** al intentar reconstruir uno de ellos, ofreciendo la descarga intacta. Un informe antiguo **sin metadatos JSON** conserva la ruta de presentación legada; un informe con Segunda Ley interna no verificable se puede consultar con advertencia visible, pero no alimentar nuevos cálculos. La validación no acredita identidad del autor ni manipulación maliciosa detectable criptográficamente.

La corrección posterior de la limitación JSON de V.5 tiene **12/12 pruebas nuevas y 78/78 regresiones directamente relacionadas correctas**, total **90/90** en la ejecución del 23/10/2026 con dependencias aisladas. Comprueban la conservación de estados cuando sólo cambia T0, los nueve parámetros, datos dañados o no finitos, límites no motores, historial, consulta y descarga. No se repitieron las 144 pruebas anteriores del panel ni la suite histórica completa. [Milestone V.5, apartado 7](docs/milestones/17_verificacion_integracion_web.md) y [guía de aprendizaje, §13](docs/milestones/11_verificacion_numerica_APRENDIZAJE.md).

`seccion_segunda_ley_html` presenta dos tablas breves y deja la cámara en un plegable. La plantilla y navegación se reutilizan; únicamente se añade CSS para ancho adaptable de SVG. Sin dependencias nuevas. T0 supone el control numérico 19 (nueve físicos, tres OFAT, seis mapa y T0); estas expectativas y el panel adicional se actualizan en los métodos de prueba existentes, sin eliminarlos.

#### Ejemplo y verificación

Caso base T0=288.15 K, no ideal: s=(0,0.0820509581,1.0764067597,1.1632558923). s_gen,c=0.0820509581 y s_gen,t=0.0868491326 kJ/(kg·K); eD,c=23.6429835754, eD,t=25.0255775665 y suma cuantificada=48.6685611419 kJ/kg. Cámara: 0.9796272985 térmico + 0.0147285031 presión = 0.9943558016 kJ/(kg·K), sin atribución de generación total. El ideal da generaciones≈0. A T0=300 K, suma=50.6700272170, sin cambiar estados.

18 pruebas nuevas pasaron inicialmente en 2.591 s; incluyen contraste analítico independiente expresado en la guía 09. Suite completa final: **178/178 OK en 265.170 s**, con `python -B -m unittest discover -s tests -q`; 160 métodos previos conservados y 18 nuevos. Verificación AST confirma que no se han eliminado métodos anteriores. Los evaluadores físicos, ambos optimizadores, sensibilidad, mapa, dependencias y PNG históricos no tienen diferencias con la base. Revisión visual real: informe normal, dos SVG, actualización T0 288.15→300 y suma proporcional; ancho DOM 1204 dentro de viewport 1219 px, sin desbordamiento horizontal. No se afirma validación experimental ni revisión exhaustiva móvil/file://. Base Git `174ce4fb9ff2a68880c3c452d82c7c179b7e058f`, rama `feature/fase-6-segunda-ley-exergia`, sin commit. [Milestone 09](docs/milestones/09_segunda_ley_exergia.md) y [guía educativa](docs/milestones/09_segunda_ley_exergia_APRENDIZAJE.md).

### 4.45. Verificación analítica ideal — `tests/test_verificacion_analitica.py`

**Alcance actual.** Esta es la **Tarea 1.1 de la Fase 1 del nuevo Plan de Mejoras: verificación numérica**, distinta de la **antigua Fase 1 de dominio viable** (§4.32 y milestone 03). Sólo incorpora un archivo de pruebas: no modifica los modelos, los optimizadores, los informes ni sus parámetros. Su [guía de aprendizaje](docs/milestones/11_verificacion_numerica_APRENDIZAJE.md) desarrolla las referencias y las limitaciones.

**INGENIERÍA.** Se contrastan cinco puntos motores representables, no fronteras. Para cada uno se forman referencias analíticas directas, sin llamar a la función que se comprueba:

```python
a = (gamma - 1) / gamma
T2_ref, T4_ref = T1 * rp**a, T3 / rp**a
wc_ref = cp * (T2_ref - T1) / 1000
wt_ref = cp * (T3 - T4_ref) / 1000
qin_ref = cp * (T3 - T2_ref) / 1000
qout_ref = cp * (T4_ref - T1) / 1000
eta_ref = 1 - rp**(-a)
```

Los trabajos y calores son **kJ/kg**; cp se expresa en **J/(kg·K)** y T en **K**. Son referencias separadas de la implementación, pero **algebraicamente equivalentes dentro del mismo modelo ideal**, no datos experimentales. Se comprueban `wneto=wt-wc` y `wneto=qin-qout`; estas dos igualdades y el residuo `wneto-(qin-qout)` son **identidades internas de primera ley**. `qout` es una variable de prueba: la API pública de ciclo sigue sin devolver esa clave. En el máximo de trabajo se verifica `T2=T4=sqrt(T1*T3)` tanto para la relación analítica como para la búsqueda numérica directa por malla/sección áurea, sin pasar por el coordinador analítico. Las comprobaciones anteriores de rp óptima, dominio abierto y desacoplamiento de la búsqueda siguen en `test_optimizacion.py` y `test_viabilidad.py`, sin duplicarlas.

**PYTHON.** `class VerificacionAnaliticaIdealTests(unittest.TestCase)` hereda de la clase de pruebas de la biblioteca estándar. `CASOS` contiene tuplas de siete campos (nombre, T1, T3, gamma, cp, rp y p1); `for` desempaqueta cada tupla y `with self.subTest(caso=nombre):` informa qué caso falla sin interrumpir los demás. La clase define cuatro métodos, sin argumentos adicionales ni retorno físico; `unittest` los llama y fallan con `AssertionError` si una diferencia supera la tolerancia:

- `test_estados_con_referencias_isentropicas(self)`: llama `main.calcular_ciclo_ideal`; contrasta las cuatro temperaturas [K] y las referencias T2s/T4s con ecuaciones directas.
- `test_balances_con_referencias_y_residuo(self)`: llama `main.calcular_ciclo_ideal`; contrasta cuatro energías [kJ/kg] calculadas con temperaturas de referencia y evalúa residuos de trabajo/primera ley, sin atribuirles independencia física.
- `test_rendimiento_analitico_frente_a_balance_motor(self)`: llama `evaluar_punto` y `main.calcular_rendimiento`; exige punto motor y qin positivo antes de comparar el cociente trabajo/calor y la fórmula analítica, en fracción adimensional.
- `test_temperaturas_coinciden_en_maximo_ideal_analitico_y_numerico(self)`: llama `main.calcular_relacion_optima`, `main.calcular_temperaturas`, `calcular_dominios` y `buscar_maximo_numerico`; compara T2 y T4 con la media geométrica [K], incluidos los estados devueltos por la búsqueda numérica sin consultar su candidato analítico.

`abs(actual-esperado)` mide **error absoluto** en la unidad de la magnitud; dividirlo por `abs(esperado)` produce **error relativo**, sólo cuando la referencia es no nula. Los residuos se expresan en kJ/kg y se comparan con una escala de energías (máximo de trabajos y calores del caso). Las comparaciones usan `atol+rtol*abs(referencia)`: `rtol=2e-12`, `atol_T=1e-9 K`, `atol_E=1e-10 kJ/kg` y `atol_eta=2e-13` como fracción. Son márgenes de redondeo para casos moderados de doble precisión, no incertidumbres experimentales. La búsqueda utiliza una tolerancia térmica más amplia, derivada de `resolucion_rp/rp` y de la sensibilidad relativa aproximada `a` de T2/T4, pues un máximo plano puede localizarse con menos precisión en rp que en trabajo.

**Ejemplo real ejecutado el 22/10/2026:** T1=288.15 K, T3=1600 K, gamma=1.4, rp=10: T2≈556.330551 K, T4≈828.715949 K, trabajo≈505.619018 kJ/kg y rendimiento≈0.482052532. En el máximo numérico rp≈20.085256021667 se obtuvo `|T2-T4|≈5.22445e-6 K`. Entre los cinco casos, el mayor error absoluto observado frente a referencias directas fue ≈1.137e−13 K (temperaturas), ≈1.137e−13 kJ/kg (energías), ≈1.110e−16 en rendimiento, y el mayor residuo de primera ley ≈1.137e−13 kJ/kg. **Ejecución focalizada:** cuatro métodos nuevos y cuatro métodos existentes relacionados: **8/8 correctos**. No se ha vuelto a ejecutar toda la suite; las pruebas de SciPy, convergencia o condicionamiento no forman parte de esta tarea (ni se han añadido).

### 4.46. Verificación analítica de raíces — `tests/test_verificacion_raices.py`

**Alcance actual.** Es la **Tarea 1.2 de la nueva Fase 1 de verificación numérica**. No cambia `viabilidad.py`, los optimizadores ni el modelo físico. Las comprobaciones de clasificación y bisección previamente existentes permanecen en `tests/test_viabilidad.py`; este archivo añade contrastes explícitos frente a raíces algebraicas independientes. Véase la [guía de aprendizaje de la fase](docs/milestones/11_verificacion_numerica_APRENDIZAJE.md), sección 7.

**INGENIERÍA / MATEMÁTICAS.** Con `a=(gamma−1)/gamma`, `x=rp**a`, `theta=T3/T1`, `h=theta*eta_c*eta_t`, `k=(1−delta)**(−a)`, el signo del trabajo específico neto se reduce a `Q(x)=x*x−(1+h)*x+h*k<0`. Para `D=(h−1)**2−4*h*(k−1)>0` hay dos raíces `x_±=(1+h±sqrt(D))/2`, que se transforman en `rp_±=x_±**(1/a)`. **La referencia se calcula directamente en el test con `sqrt`**, sin llamar a `bisectar_raiz` ni a `calcular_dominios`; estas funciones sólo producen el resultado sometido a comprobación. Los valores analíticos se obtienen con las mismas hipótesis físicas del modelo, no con datos de motores reales.

El dominio motor es la **intersección abierta** de compresión `rp>1`, expansión `rp>1/(1−delta)`, calor `x<1+eta_c*(theta−1)` y trabajo `Q(x)<0`. Si `D<0`, no hay raíces reales; si `D=0`, sólo hay tangencia sin región negativa. Incluso con `D>0`, las raíces pueden estar en `x≤1` y no constituir motor. En el caso reversible `Q(x)=(x−1)*(x−theta)`, recuperando las fronteras ideales. La prueba comprueba puntos suficientemente separados (`1e−5` relativo) a ambos lados del intervalo y distingue esas fronteras matemáticas de la banda relativa `1e−10` que excluye `evaluar_punto`.

**PYTHON.** `class VerificacionRaicesTests(unittest.TestCase)` organiza cinco métodos ejecutados por `unittest`. Todos tienen **firma `metodo(self)`**, reciben sólo el objeto de prueba y retornan implícitamente `None`: los parámetros provienen de tuplas `CASOS_NO_IDEALES` (T1, T3 [K], gamma y eficiencias [—], cp [J/(kg·K)], p1 [kPa], delta [—]). `for`, `zip` y `with self.subTest(caso=..., raiz=... o punto=...)` permiten identificar cada combinación sin crear métodos separados. `assertLessEqual`, `assertEqual` y `assertGreater` producen un fallo de prueba (`AssertionError`); errores de validación inesperados de producción se propagan. Ningún método altera estados persistentes ni genera resultados gráficos.

| Método completo (`self` implícito) | Llamadas y comprobación |
|---|---|
| `test_raices_noideales_con_referencias_y_residuos(self)` | `calcular_dominios`; cuatro casos, raíces inferiores/superiores, errores absolutos/relativos en x y rp [—] y residuo adimensional de Q |
| `test_interseccion_de_restricciones_y_fronteras_abiertas(self)` | `calcular_dominios`, `evaluar_punto`; cotas analíticas de compresión, expansión, calor y trabajo, estado del punto central y de dos lados de cada frontera |
| `test_limite_reversible_factoriza_y_es_abierto(self)` | `calcular_dominios`, `evaluar_punto`; factorización, raíces `1` y `theta**(1/a)`, exclusión de fronteras |
| `test_discriminante_negativo_y_raiz_doble(self)` | `calcular_dominios`; D negativo y D exactamente nulo construido con h=k=1, ambos sin interior motor |
| `test_raices_reales_sin_dominio_motor(self)` | `calcular_dominios`, `evaluar_punto`; D positivo y Q negativa sólo para x entre 0,5 y 1, incompatible con compresión |

**ERROR NUMÉRICO.** Error de posición `abs(x_num−x_ref)` y `abs(rp_num−rp_ref)` (también relativos a referencias no nulas) no equivale al **residuo** `abs(Q(x_num))`. La bisección reduce a la mitad un intervalo con cambio de signo y se detiene con ancho relativo `1e−12` en **x**; para raíces simples de estos casos se comprueba `atol_x=2e−12`, `rtol_x=2e−12`. La transformación potencia puede amplificar el error relativo en aproximadamente `1/a`, por lo que en rp se usa `atol_rp=1e−9`, `rtol_rp=2e−11`. Para Q se exige `abs(Q)≤2e−11·max(1,x²,|(1+h)x|,hk)`, sin unidades. Son umbrales conservadores de redondeo/bisección, no garantías generales, especialmente si `D≈0`. Un residuo minúsculo por sí solo **no garantiza** poco error en la raíz cuando `Q'` es pequeño.

**Resultados de la Tarea 1.2 (22/10/2026):** cinco métodos nuevos correctos y siete métodos preexistentes directamente relacionados correctos; **12/12**, sin suite completa. Máximos observados entre las ocho raíces no ideales: error x absoluto `9.1304741545e−13`, relativo `3.7747594652e−13`; error rp absoluto `1.1246470422e−10`, relativo `1.4261261054e−12`; `|Q(x)|=2.2444268666e−12`. El contraste posterior con SciPy está documentado en §4.47; los estudios sistemáticos de convergencia siguen pendientes.

### 4.47. Comparación opcional con SciPy — `tests/test_comparacion_scipy.py`

**Alcance y ejecución.** La Tarea 1.3 contrasta los métodos propios con otras implementaciones numéricas **sin modificar** `viabilidad.py`, los optimizadores ni el simulador. SciPy se importa exclusivamente en el archivo de pruebas: `try: from scipy import optimize as scipy_optimize` y `except ImportError: scipy_optimize = None`. Seis métodos están decorados con `@unittest.skipIf(scipy_optimize is None, ...)`: si falta, se declaran **omitidos**, no superados. Otros dos métodos comprueban dominio vacío y filtros de viabilidad sólo con Python estándar y funciones propias. **SciPy no pasa a ser una dependencia obligatoria.** La [guía de aprendizaje](docs/milestones/11_verificacion_numerica_APRENDIZAJE.md), §8, desarrolla la interpretación.

**MATEMÁTICAS / INGENIERÍA.** En raíces, se aplica `bisectar_raiz`, `scipy.optimize.bisect` y `scipy.optimize.brentq` **al mismo callback continuo y al mismo intervalo con signos opuestos**: primero `f(x)=x²−2`, después las dos raíces de `Q(x)=(x−1)(x−h)+h(k−1)` de tres casos no ideales moderados (§4.46). `bisect` y la bisección propia conservan el cambio de signo; `brentq` combina acotación con interpolación para acelerar en situaciones favorables. Las referencias matemáticas `sqrt(2)` y la fórmula cuadrática se calculan directamente, sin usar el buscador verificado. La comparación conserva posiciones en `x=rp**a` y las transforma a `rp=x**(1/a)`; para errores pequeños, `|Δrp|/rp≈|Δx|/(a*x)`. El residuo `|Q(x)|` es distinto del error de localización de la raíz.

Para máximos, los métodos propios exploran una **malla logarítmica** y refinan mediante sección áurea; `scipy.optimize.minimize_scalar(..., method="bounded")` trabaja sobre el negativo de `trabajo_neto` [kJ/kg] o de `rendimiento` [fracción]. Se optimiza en `y=log(rp)`, transformando con `rp=exp(y)` y evitando comparar optimizaciones en coordenadas distintas. La ventana interior descarta `1e−6` de la anchura logarítmica en cada lado de las fronteras abiertas. SciPy recibe `options={"xatol": 1e-9, "maxiter": 500}`; el buscador propio usa `tolerancia_log=1e−9`. Un `success=True` sólo señala la parada del algoritmo: adicionalmente se comprueban **dominio abierto, punto motor, números finitos y descenso del objetivo a ambos lados** de la solución. El rendimiento ideal tiene **supremo de frontera no alcanzado**, por lo que su punto cercano al borde se rechaza como supuesto máximo interior, aunque `bounded` converja.

**PYTHON — clase y funciones nuevas.** `ComparacionSciPyTests(unittest.TestCase)` se descubre mediante `python -B -m unittest discover -s tests -p 'test_comparacion_scipy.py' -v`. Usa tuplas `CASOS_NO_IDEALES` / `CASO_IDEAL` con `(nombre, T1, T3, gamma, cp, p1, eta_c, eta_t, delta)`; temperaturas en K, `cp` en J/(kg·K), `p1` en kPa y el resto adimensional. `subTest(caso=..., raiz=..., metodo=...)` identifica combinaciones sin multiplicar métodos independientes. Sus dos auxiliares **sólo viven en las pruebas**:

- `_resolver_tres_raices(self, funcion, inferior, superior)`: recibe un callback `float→float` y extremos reales de un intervalo con cambio de signo; llama a `bisectar_raiz`, `scipy_optimize.bisect` y `scipy_optimize.brentq` con `xtol=1e−12` y, en SciPy, `rtol=1e−12`. Devuelve `dict[str, tuple[float,int]]`: raíz adimensional y número real de invocaciones del callback por método. Su función local `contado(x)` incrementa una lista de un elemento (contador mutable capturado por cierre). Es llamada por los dos tests de raíces; `ValueError` por intervalo inválido se comprueba en otro test y los errores de convergencia/aserción se propagan.
- `_aceptar_maximo_scipy(self, resultado, dominio, parametros, clave)`: recibe un objeto tipo `OptimizeResult` (`success`, `x`, `fun`), el diccionario de dominio, la tupla física de ocho parámetros y la clave `'trabajo_neto'` o `'rendimiento'`. Llama a `evaluar_punto` en `exp(x)` y en dos testigos logarítmicos interiores, separados `0.002` veces el ancho del intervalo. Retorna `(rp, punto)` (presión relativa adimensional y diccionario termodinámico con trabajo [kJ/kg] o rendimiento [fracción]) si se verifica máximo interior; en caso contrario `None`. Es llamada por ambos tests de máximos, por el caso ideal de supremo y por el test de resultados sintéticos. Un resultado sin `success`, no finito, no motor, próximo a frontera o sin descenso bilateral no se acepta; **no cambia la definición física de `evaluar_punto`**.

Ejemplo dentro de un método de la clase: `soluciones = self._resolver_tres_raices(lambda x: x*x-2, 1, 2)` y `raiz, llamadas = soluciones["propia"]`; para un resultado ya producido por `minimize_scalar`, `aceptado = self._aceptar_maximo_scipy(resultado, dominio, parametros, "trabajo_neto")`. Los callbacks locales `contado(x)` devuelven el valor de la función a partir de una abscisa adimensional y suman una llamada; `objetivo(y)` recibe `y=log(rp)` (adimensional) y devuelve `-W` [kJ/kg] o `-eta` [fracción] para que SciPy lo minimice.

Los ocho tests tienen firma completa `test_...(self)`, no reciben parámetros externos ni devuelven magnitudes (retorno `None`); `unittest` los llama, `AssertionError` informa diferencias fuera de tolerancia, y el decorador de omisión evita errores de importación si falta SciPy:

| Método de prueba | Comprobación y llamadas principales |
|---|---|
| `test_raiz_matematica_conocida(self)` | `_resolver_tres_raices`; tres métodos para `x²−2=0` en `[1,2]`, error/residuo y llamadas |
| `test_raices_del_dominio_con_bisect_y_brentq(self)` | `calcular_dominios`, `_resolver_tres_raices`; ambas raíces de Q en tres casos, errores/residuos en x y rp |
| `test_maximo_trabajo_con_bounded(self)` | `calcular_dominios`, `buscar_maximo_numerico`, `minimize_scalar`, `_aceptar_maximo_scipy`; cuatro máximos interiores, valores [kJ/kg], posiciones y evaluaciones |
| `test_maximo_rendimiento_noideal_con_bounded(self)` | `buscar_maximo_rendimiento_numerico`, `minimize_scalar`, `_aceptar_maximo_scipy`; tres máximos no ideales [fracción] |
| `test_rendimiento_ideal_es_supremo_no_maximo(self)` | `buscar_maximo_rendimiento_numerico`, `calcular_dominios`, `minimize_scalar` y filtro; rechaza máximo interior ficticio |
| `test_dominio_vacio_se_distingue_de_fallo_numerico(self)` | `calcular_dominios` y buscadores propios; exige `sin_dominio` y `None`, sin ejecutar SciPy |
| `test_intervalos_sin_cambio_de_signo(self)` | `assertRaises(ValueError)` en las tres bisecciones/acotaciones; no busca raíces sin cambio de signo |
| `test_convergencia_y_viabilidad_no_son_equivalentes(self)` | `types.SimpleNamespace` simula fallo de convergencia, frontera, NaN y punto no estacionario; comprueba el filtro sin SciPy real |

**Tolerancias y significado.** Raíces: SciPy recibe explícitamente `xtol=rtol=1e−12`; la bisección propia usa ancho de intervalo relativo `1e−12` en x, **criterios de parada no idénticos**. Frente a la referencia cuadrática, `|Δx|≤2e−12+3e−12|x_ref|`, `|Δrp|≤1e−9+2e−11|rp_ref|`, `|Q(x)|≤2e−11*max(1,x²,|(1+h)x|,hk)`. Máximos: en rp, `atol=1e−6`, `rtol=2e−6`; en trabajo, `atol=1e−8 kJ/kg`, `rtol=1e−10` multiplicado por la mayor de la escala del trabajo y `cp*T3/1000`; en eta, `atol=1e−10` y `rtol=1e−10`. Cerca de un máximo plano, el valor puede coincidir mucho más que la posición. `resolucion_rp` propia es una escala informativa, no garantía del error real. Los contadores `evaluaciones` y `nfev` miden objetivos bajo estrategias distintas (malla+refinamiento frente a búsqueda acotada), sin prometer superioridad universal ni exigir recuentos fijos.

**Resultados ejecutados (22/10/2026):** SciPy **1.17.0**, ocho métodos nuevos correctos y ocho regresiones existentes relacionadas correctas: **16/16**, sin suite completa. El ensayo adicional sin SciPy obtuvo **2 correctos y 6 omitidos explícitamente**. Entre seis raíces Q y tres métodos, máximo error absoluto en x `3.316e−12`, relativo `1.118e−12`; en rp absoluto `4.266e−10`, relativo `4.505e−12`; `|Q(x)|` máximo `1.064e−11`. Para trabajo (ideal y tres no ideales), las diferencias máximas frente a SciPy fueron `7.212e−7` en rp (relativa `5.906e−8`) y `2.274e−13 kJ/kg` (relativa `4.888e−16`). Para rendimiento (tres no ideales), `1.747e−6` en rp (relativa `6.906e−8`) y `3.331e−16` en rendimiento (relativa `8.594e−16`). En el caso no ideal de referencia, trabajo propio `rp≈12.89505173504`, SciPy `rp≈12.89505166962` (evaluaciones **297 frente a 6**); rendimiento propio `rp≈35.4523219222`, SciPy `rp≈35.45232299066` (**297 frente a 11**). Estos datos no validan un motor real; el estudio sistemático posterior corresponde a §4.48. **La Tarea 1.3 ya está publicada** en `mejoras/verificacion-numerica`, commit `8ecbc1bf75e7e68fc3377cbf97017f8480d32553`.

### 4.48. Convergencia y sensibilidad numérica — `tests/test_convergencia_numerica.py`

**Alcance y trazabilidad.** La Tarea 1.4 parte de la rama `mejoras/verificacion-numerica`, commit remoto `8ecbc1bf75e7e68fc3377cbf97017f8480d32553` (publicación de la Tarea 1.3). A diferencia de §4.47, no contrasta implementaciones externas: cambia **un control numérico cada vez** en los métodos existentes, observa sus errores frente a referencias matemáticas y verifica sus mensajes de parada. No modifica física, bisección, optimizadores, valores predeterminados ni dependencias. La [guía educativa §9](docs/milestones/11_verificacion_numerica_APRENDIZAJE.md) contiene tablas y límites del experimento.

**MATEMÁTICAS — bisección.** Para `f(x)=x²−2` se usa `sqrt(2)`; para las raíces de dos cuadráticas no ideales `Q(x)=(x−1)(x−h)+h(k−1)` se usa `x_±=((1+h)±sqrt(D))/2` (véase §4.46). Son referencias analíticas calculadas sin llamar al método comprobado. Se varía `tolerancia∈{1e−6,1e−8,1e−10,1e−12}` con 100 iteraciones disponibles y después sólo el máximo `iteraciones∈{1,5,12}` con tolerancia `1e−12`. Una función interna `contado(x)` recibe una abscisa adimensional, devuelve `f(x)` adimensional y registra cada llamada en `observaciones` o en `llamadas[0]`. A partir de la secuencia registrada, el test reconstruye el **intervalo con cambio de signo** y comprueba que el ancho se divide por dos a cada paso. Importa el ancho geométrico, **no que el error concreto se reduzca monótonamente**. Se registran errores absolutos y relativos de x y de `rp=x**(1/a)`, residuos `|f(x)|` y evaluaciones (dos extremos más puntos medios). `ErrorNumerico` por límite de iteraciones se espera sólo en ensayos insuficientes; `ValueError` identifica una acotación sin cambio de signo. Un fracaso de convergencia no representa una raíz obtenida.

**Mallas y refinamiento.** `buscar_maximo_numerico()` usa mallas de `17,33,65,129,257,513` muestras en `y=log(rp)` con `tolerancia_log=1e−9` y `max_iteraciones=100` fijos; los tres casos (ideal, referencia no ideal y gamma 1.33) tienen máximos motores interiores. Se verifica además, **sin dar al optimizador el candidato**, que el máximo analítico `calcular_candidato_analitico()` queda entre los vecinos del mejor nodo de la malla inicial. En una segunda serie, con `muestras=257` fijas, tanto el máximo de trabajo como el de rendimiento no ideal se ensayan con `tolerancia_log∈{1e−5,1e−7,1e−9,1e−11}` y después con presupuestos deliberadamente cortos `1,12,30` frente a 100. Trabajo se contrasta en rp y kJ/kg con `calcular_candidato_analitico()`; rendimiento en rp y fracción con `calcular_candidato_rendimiento()` cuando existe máximo interior. Los diccionarios de producción dan `evaluaciones`, `iteraciones`, `intervalo_final` y `resolucion_rp`; el test comprueba reducción del ancho logarítmico, viabilidad y precisión observada **sin exigir tendencias monótonas**. `resolucion_rp=rp·max(tolerancia_log,32√eps_maquina)` es una indicación conservadora de redondeo, **no una garantía** de error absoluto en rp ni una medida de convergencia observada.

**Fronteras abiertas.** Para el ciclo ideal y el no ideal de referencia se toman puntos interiores a `10−3,10−6,10−9,10−12` de cada extremo en rp, multiplicativamente. `evaluar_punto(..., tolerancia=0)` representa los signos físicos de los cuatro márgenes (no una validación externa); `evaluar_punto()` con tolerancia por defecto `1e−10` determina si el programa permite calcular rendimiento. En los casos ensayados, las distancias hasta `1e−9` son admitidas y las de `1e−12` son físicas por signo pero quedan **excluidas por la banda**. El trabajo tiende a cero en ambos extremos; el calor también tiende a cero en la frontera superior ideal, pero en la superior no ideal del ejemplo permanece ≈`218.522 kJ/kg`. Se comprueba `rendimiento is None` en puntos excluidos; el rendimiento ideal conserva sólo el estado `supremo_no_alcanzado`, no un máximo ficticio. Un dominio motor vacío (`intervalo=()`) se distingue de agotamiento de iteraciones o de un punto descartado por tolerancia.

**PYTHON — firmas, unidades y relaciones de llamada.** `ConvergenciaNumericaTests(unittest.TestCase)` contiene ocho métodos `test_...(self)` sin argumentos externos y retorno `None` (invocados por `unittest`, las excepciones de producción se propagan y las aserciones fallidas generan `AssertionError`). Los tres conjuntos de entradas son tuplas `(nombre,T1,T3,gamma,cp,p1,eta_c,eta_t,delta)`; `T1,T3` en K, `cp` en J/(kg·K), `p1` en kPa, los demás adimensionales. Sus constantes de clase enumeran tolerancias, mallas y distancias, y sus `subTest(caso=...,tolerancia=.../muestras=.../distancia=...)` identifican la combinación fallida. El único auxiliar propio de la clase es `_referencias_raices(self)`: recibe `self`, llama a `self.assertGreater(D,0)` para la discriminante, construye funciones con cierres `Q(x,h=h,k=k)` que fijan los coeficientes de cada caso, y **devuelve una lista de cinco tuplas** `(nombre,funcion,lo,hi,x_ref,a)` (abscisas y potencias adimensionales; `a=None` para `sqrt(2)`). Lo llaman `test_biseccion_tolerancias_anchuras_y_coste(self)` y `test_biseccion_agotamiento_e_intervalo_invalido(self)`; no invoca código de producción para obtener referencias. `contado(x)` dentro de esos dos métodos recibe x y devuelve `f(x)` mientras agrega la llamada al registro; `Q(x,h=h,k=k)` recibe x, usa `h,k` fijados (argumentos por defecto del cierre) y devuelve Q, sin llamadas externas. Ejemplo: `for nombre,f,lo,hi,x_ref,a in self._referencias_raices(): x_num=bisectar_raiz(f,lo,hi,tolerancia=1e-8)`.

| Método de prueba (`self` → `None`) | Funciones de producción implicadas y propiedad nueva |
|---|---|
| `test_biseccion_tolerancias_anchuras_y_coste` | `bisectar_raiz`: anchura geométrica, precisión, residuo y llamadas en 5 raíces × 4 tolerancias |
| `test_biseccion_agotamiento_e_intervalo_invalido` | `bisectar_raiz`: 1/5/12 iteraciones insuficientes y `ValueError` sin cambio de signo |
| `test_mallas_trabajo_acotacion_precision_y_coste` | `calcular_dominios`, `buscar_maximo_numerico`, `calcular_candidato_analitico`, `evaluar_punto`: 3 ciclos × 6 mallas, acotación y evaluaciones |
| `test_tolerancias_refinamiento_trabajo` | Las anteriores: 3 ciclos × 4 tolerancias logarítmicas con 257 nodos |
| `test_tolerancias_refinamiento_rendimiento` | `buscar_maximo_rendimiento_numerico`, `calcular_candidato_rendimiento`, `evaluar_punto`: 2 ciclos × 4 tolerancias |
| `test_agotamiento_controlado_en_ambos_optimizadores` | Ambos buscadores: excepción explícita con 1/12/30 iteraciones y éxito con 100 |
| `test_fronteras_abiertas_y_banda_de_viabilidad` | `calcular_dominios`, `evaluar_punto`, ambos buscadores: márgenes y supremo ideal |
| `test_dominio_vacio_separa_ausencia_de_fallo_numerico` | `calcular_dominios`, ambos buscadores: dominio vacío frente a fallo del método |

**Criterios de aceptación y resultado.** Por tratarse de raíces simples moderadas, se compara el error de x con el medio ancho de la última acotación reconstruida (más `5e−13·max(1,|x_ref|)` de redondeo); se verifica el criterio de parada por ancho relativo y no se fija un mismo umbral de posición para todas las tolerancias. La amplificación a rp se controla localmente por `4|Δx|/(a·x_ref)+1e−12` en error relativo. Para mallas de trabajo se exige `|Δrp|≤2e−7·rp_ref`, `|ΔW|≤1e−9 kJ/kg`; al variar `tolerancia_log`, trabajo `|Δrp|/rp_ref≤max(2e−7,3*tolerancia_log)` y rendimiento `≤max(2e−6,3*tolerancia_log)`, con `|Δeta|≤1e−10`. Son **umbrales de regresión** razonables para los casos probados y máximos planos, no garantías universales ni límites experimentales. Se comprueba por separado `ln(intervalo_final[1]/intervalo_final[0])≤tolerancia_log+1e−14` por redondeo de los extremos.

**Ejecución real (22/10/2026):** 8 métodos nuevos y 8 regresiones escogidas de raíces, SciPy y rendimiento **correctos (16/16), 0 fallos, 0 omitidos**; no se repitió la suite general. Entre cinco raíces y todas las tolerancias, máximos `|Δx|=3.281e−7`, `|Δrp|=4.222e−5`, residuo `1.053e−6`, todos con tolerancia más laxa `1e−6`. Con `1e−12`, máximos `|Δx|=3.191e−13`, `|Δrp|=3.359e−11`, residuo `8.397e−13`; 41–43 pasos de bisección. En mallas, el mayor error rp fue `8.492e−7` (ideal, 17 nodos), el mayor error en W `2.274e−13 kJ/kg`. Con refinamiento de rendimiento a `1e−5`, el error rp máximo fue `1.829e−5` (gamma 1.33), frente a `2.238e−14` en fracción de rendimiento; los límites de iteraciones 1/12/30 informaron agotamiento y 100 bastaron (hasta 48 iteraciones al exigir `1e−11`). De 257 a 513 nodos se pasó de 297 a 551–552 evaluaciones sin mejora monotónica; de `1e−9` a `1e−11` aumentaron las evaluaciones pero no mejoró necesariamente rp debido al redondeo y a la planitud. Ver tablas completas en la guía §9. Estas conclusiones no cubren casos casi degenerados ni benchmarking temporal.

**Estado Git posterior verificado:** la Tarea 1.4 se publicó en la rama de desarrollo, commit `c3b4bfea12cf6faa1dc90c8f8fb16fb9e8fe7131`. Este commit es la base de la Tarea 1.5.

### 4.49. Primera ley e invariantes físicos — `tests/test_invariantes_fisicos.py`

**Alcance actual.** La Tarea 1.5 añade **únicamente pruebas** que llaman a `evaluar_punto` y, en dos casos, a `calcular_dominios`. No modifica `calcular_estados`, `calcular_energias`, la clasificación motora ni el código de producción. Su [guía educativa, §10](docs/milestones/11_verificacion_numerica_APRENDIZAJE.md) contiene resultados y referencias. Partió de `c3b4bfe` y fue **publicada** en `mejoras/verificacion-numerica`, commit `57da73db01882ab32bd5d92d14bdbe739c272b79`.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Se modelan compresor y turbina adiabáticos, gas con `cp` y `gamma` constantes y pérdidas relativas de presión: `a=(gamma−1)/gamma`, `T2=T1[1+(rp**a−1)/eta_c]`, `T4=T3[1−eta_t(1−(rp(1−delta))**(−a))]`. Con `cp` [J/(kg·K)] y `T` [K], cada energía se divide entre **1000** para obtener kJ/kg:

\[
w_c=\frac{c_p(T_2-T_1)}{1000},\quad w_t=\frac{c_p(T_3-T_4)}{1000},\quad
q_{in}=\frac{c_p(T_3-T_2)}{1000},\quad q_{out}=\frac{c_p(T_4-T_1)}{1000}.
\]

Las dos identidades de la primera ley son `w_neto = wt−wc = qin−qout`; `qout` se **calcula dentro del test**, no se añade a la API. Las pruebas reconstruyen independientemente `T2_ref/T4_ref` desde las entradas (no obtienen la referencia mediante otra llamada a `evaluar_punto`) y contrastan estados y cuatro energías. El ideal ya tenía una batería analítica específica (§4.45); aquí figura un anclaje ideal y **cuatro casos adicionales**, incluido uno no motor. Estas comparaciones verifican la implementación y las identidades **dentro del mismo modelo**, no constituyen validación externa.

Al bajar `eta_c`, suben `T2` y `wc`; al bajar `eta_t`, sube `T4` y baja `wt`; al aumentar `delta`, la relación efectiva `p3/p4=rp(1−delta)` disminuye y baja `wt`. A `rp` fija las tres perturbaciones reducen `w_neto`. Si `eta_c,eta_t→1` y `delta→0`, las magnitudes se aproximan al caso reversible. En este modelo, multiplicar `cp` por un factor positivo escala trabajos y calores, **no** temperaturas ni rendimiento; multiplicar `p1` escala las cuatro presiones absolutas, pero deja invariantes las temperaturas, el balance específico y la eficiencia. Esas invariancias no se trasladan sin más a un gas con propiedades variables.

**Motor frente a álgebra.** `evaluar_punto` puede devolver estados positivos y energías con signo aun cuando falte compresión, expansión, aporte térmico o trabajo motor. Los cuatro `margenes` se comparan con sus `tolerancias`: un margen `<=` a su umbral incorpora el código en `motivos`; `fronteras` marca el que cae dentro de la banda, y `rendimiento/back_work_ratio` sólo existen cuando **todas** las restricciones se satisfacen. `tolerancia=0` sirve como testigo de signos físicos; `TOL_REL=1e−10` excluye estados demasiado cercanos a una frontera abierta, sin transformarlos en entrada inválida ni en fallo de cálculo. Las excepciones de entrada/representación se verifican en §4.32 y `tests/test_viabilidad.py`, sin duplicarlas aquí.

**PYTHON — estructura y funciones del archivo.** `InvariantesFisicosTests(unittest.TestCase)` utiliza `CASOS` (tuplas: nombre `str`, `T1,T3` [K], `gamma` [-], `cp` [J/(kg·K)], `rp` [-], `p1` [kPa], `eta_c,eta_t,delta` [-]) y bucles con `subTest()` para separar los diagnósticos por caso/factor. Los seis métodos `test_...(self)` son invocados automáticamente por `unittest`, no reciben parámetros exteriores y retornan `None`:

- `test_primera_ley_con_referencias_noideales_independientes`: construye temperaturas, presiones y energías de referencia para cinco casos; verifica `qout` y ambas formas del balance.
- `test_irreversibilidades_aisladas_reducen_trabajo`: cambia sólo `eta_c`, sólo `eta_t` o sólo `delta` y comprueba la dirección física de los cambios.
- `test_limite_reversible_converge_al_ideal`: compara cuatro perturbaciones decrecientes con el motor ideal a la misma `rp`.
- `test_escalado_cp_sin_cambio_de_temperaturas_ni_rendimiento` y `test_escalado_p1_sin_cambio_de_energias`: ensayan tres factores positivos en un ideal y un no ideal, sin variar el resto.
- `test_no_motores_conservan_balance_y_motivos`: comprueba cinco estados no motores, un dominio vacío y dos puntos próximos a la frontera superior.

Las únicas funciones auxiliares nuevas viven **en el test** y no tienen usuarios de producción:

- `_comparar(self, magnitud, obtenido, referencia, atol)` recibe etiqueta `str`, dos `float` de la **misma unidad** y tolerancia absoluta `float`; actualiza `MEDIDAS[magnitud]` con mayores errores absoluto y relativo (éste es `None` si la referencia es cero); llama `self.assertLessEqual` y retorna `None`. La usan los seis métodos (directa o indirectamente). La condición es `|obtenido−referencia|≤atol+2e−12|referencia|`, con `atol=1e−9 K/kPa` para estados, `1e−10 kJ/kg` para energías y escalas ajustadas en los cocientes sin dimensión.
- `_comprobar_balance(self, punto, cp)` recibe el `dict` devuelto por `evaluar_punto` y `cp` [J/(kg·K)]; recalcula las cuatro expresiones `cp·ΔT/1000`, compara salidas y tres residuos (`wn−(wt−wc)`, `wn−(qin−qout)` y sus dos formulaciones), y **retorna `qout` [kJ/kg]**. Llama `_comparar` y es utilizado por los tests de balances, irreversibilidad, reversibilidad, escalado cp y no motores. Si una comparación falla, se obtiene un `AssertionError` con etiqueta y diferencia, sin alterar el estado del simulador.

Ejemplo: `punto=evaluar_punto(288.15,1600,1.4,1005,10,100,.85,.9,.05)` y, dentro de una instancia del test, `qout=self._comprobar_balance(punto,1005)`. **Un residuo** mide el cierre algebraico en kJ/kg; el **error relativo** sólo se define para una referencia no nula. Las bandas de tolerancia de verificación permiten redondeo en `float`, no modelan incertidumbre física.

**Resultado ejecutado inicialmente (22/10/2026):** los seis métodos nuevos y seis regresiones de raíces, fronteras y dominios pasaron (**12/12**). Entre cinco conjuntos de parámetros, máximos observados frente a referencias: temperatura `2.274e−13 K`, energía `4.547e−13 kJ/kg` y error relativo de energía `5.452e−15` (trabajo neto); el mayor residuo de primera ley fue `2.842e−13 kJ/kg`. En escalado de `cp` el error máximo de energía fue `4.547e−13 kJ/kg` y el de rendimiento `1.110e−16`; al escalar `p1`, las energías y rendimiento coincidieron exactamente en los casos ensayados. **Verificación complementaria de aquella tarea:** después se resolvió el bloqueo de importación de `jinja2` mediante un entorno virtual aislado fuera del repositorio, instalando sólo `requirements.txt` (Flask incluye Jinja2). Las **nueve regresiones pendientes** finalizaron **9/9 correctas**. Total acumulado entonces: **21/21 correctos** en ejecuciones focalizadas. La suite completa se ejecutó **posteriormente** en la Etapa 6 (§4.50). Ninguno de esos resultados constituye validación experimental.

### 4.50. Cierre reproducible de la nueva Fase 1 — milestone 12

**Alcance.** El [cierre técnico publicado](docs/milestones/12_cierre_verificacion_numerica.md) recoge nuevas tablas físicas recalculadas, matrices de aceptación y pruebas de compatibilidad. Es una etapa **documental y de regresión**, sin funciones, dependencias obligatorias, ecuaciones ni algoritmos nuevos. Su copia de partida procede del commit remoto **`57da73db01882ab32bd5d92d14bdbe739c272b79`**; se publicó en `cd3349c59e85a0e34e48d9c49aefeb0a4014dd1f`.

**PYTHON — reproducibilidad y pruebas.** El entorno aislado se crea con `python3 -m venv` fuera del árbol de trabajo y las dependencias reales se instalan desde `requirements.txt` (NumPy, Matplotlib, Flask/Jinja2). SciPy 1.17.0 se instaló **sólo en ese entorno** para ejecutar los métodos opcionales; no se modifica el archivo de requisitos. `python -B -m unittest discover -s tests -q` busca los archivos `test_*.py`, llama a los métodos de prueba y devuelve un resumen único. Un ensayo separado interceptó `import scipy` y verificó que las rutas de cálculo de `main`, `viabilidad` y la importación de Flask siguen disponibles; el propio archivo de comparación informó seis `skipIf` y dos métodos correctos. No se añadieron métodos de prueba nuevos en este cierre.

**INGENIERÍA — resultados y aceptación.** Se recalcularon para esta versión un caso motor ideal (`rp=10`, `w_neto≈505.619018 kJ/kg`, `eta≈0.482052532`), dos no ideales (en el primero `w_neto≈369.476301 kJ/kg`, `eta≈0.368987324`), un dominio no ideal vacío y dos puntos cercanos a la frontera superior no ideal. A `1e−9` relativo del límite se admitió trabajo positivo `3.12295e−7 kJ/kg`; a `1e−12` se calculó `2.44427e−10 kJ/kg` pero se **excluyó por la banda de `1e−10`**, sin definir rendimiento motor. Las búsquedas de trabajo/rendimiento conservaron sus controles (`257` muestras, tolerancia logarítmica `1e−9`, `100` iteraciones máximas); en el ideal se informa sólo del supremo de eficiencia no alcanzado. La tabla completa y los parámetros de reproducción están en el milestone 12. Verificar el programa contra fórmulas y librerías numéricas no lo valida físicamente frente a un motor real.

**Ejecución real (22/10/2026):** Linux, Python 3.12.14, NumPy 2.5.4, Matplotlib 3.11.2, Flask 3.1.3, Jinja2 3.1.6 y SciPy 1.17.0: **215/215 pruebas superadas, 0 fallos, 0 omisiones y 0 errores de importación, en 69.358 s**. Fue **una sola ejecución de la suite completa**. Sin SciPy, el ensayo focalizado adicional hizo `8` métodos (`2` correctos, `6` omitidos). El contraste Git entre la base de la nueva fase y la tarea 1.5 sólo muestra cinco archivos de pruebas y dos documentos, sin cambios de HTML, Flask ni módulos físicos. La ejecución no acredita compatibilidad nativa con Windows, revisión visual de gráficos ni validación experimental.

### 4.51. V.1 — referencias independientes para Sensibilidad OFAT (milestone 13)

**Alcance y evidencia.** La [verificación V.1](docs/milestones/13_verificacion_sensibilidad.md), preparada desde `cd3349c59e85a0e34e48d9c49aefeb0a4014dd1f` y **publicada** en el commit `8d767b69858c4a3a055c11bbba3294124770d743`, aporta ocho métodos nuevos en `tests/test_verificacion_sensibilidad.py`. Sólo cambian pruebas y documentos; `sensibilidad.py`, balances, optimizadores, Flask e interfaz conservan exactamente los contratos de §4.40. Se verifican R a presión relativa fija, el óptimo de trabajo A, el óptimo de rendimiento B y los casos donde no existe punto operativo. No se atribuye a estas pruebas una funcionalidad nueva del simulador.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Con `a=(gamma−1)/gamma`, `u=rp**a`, `v=(rp*(1−delta))**(−a)` y `k=cp/1000`, la referencia R reconstruye directamente `T2=T1*(1+(u−1)/eta_c)`, `T4=T3*(1−eta_t*(1−v))`, `W=k*(T3−T4−T2+T1)`, `Qin=k*(T3−T2)` y `eta=W/Qin` **sólo en un punto motor**. A `rp` constante, las cinco derivadas del trabajo son:

| `x` | `∂W_R/∂x` | `∂Qin_R/∂x` |
|---|---|---|
| `T1` | `−k*(u−1)/eta_c` | `−k*(1+(u−1)/eta_c)` |
| `T3` | `k*eta_t*(1−v)` | `k` |
| `eta_c` | `k*T1*(u−1)/eta_c**2` | igual que `∂W/∂eta_c` |
| `eta_t` | `k*T3*(1−v)` | `0` |
| `delta` | `−k*eta_t*T3*a*v/(1−delta)` | `0` |

La derivada de `eta` usa la regla del cociente `deta=(dW*Qin−W*dQin)/Qin**2`; la elasticidad `S=x*dY/(Y*dx)` sólo tiene sentido si `x` y `Y` permiten el cociente. En `delta=0` se conserva `dY/ddelta`, pero `S_delta=None`. El máximo A se referencia mediante `rp_A**a=sqrt(eta_c*eta_t*(T3/T1)*(1−delta)**(−a))`, con dominio y margen motor obligatorios. La derivada de **valor óptimo A** cumple `dWmax/dx=∂W/∂x|rp_A` cuando el óptimo es suave e interior (teorema de la envolvente); no es la misma derivada que R a una `rp` arbitraria. Para B, SciPy minimiza `−eta` en `log(rp)` sin usar el candidato analítico de B, y exige convergencia **más viabilidad física**. El reversible ideal no tiene B interior: sólo supremo excluido. Las fórmulas y medidas completas están en el milestone 13; no hay validación experimental.

**PYTHON — auxiliares locales de las pruebas (sin API nueva de producción):**

- `referencia_independiente(p, rp)` recibe el `dict` de las nueve entradas y `rp` real adimensional. Devuelve un `dict` con tupla de cuatro temperaturas K, `trabajo_compresor`, `trabajo_turbina`, `trabajo_neto`, `calor_aportado` en kJ/kg, `rendimiento` como fracción o `None`, y `motor` booleano. No llama módulos físicos; la usan casi todos los métodos de la clase y `gradientes_r`. Calcula el oráculo algebraico y aplica signos estrictos para los casos moderados, sin pretender sustituir las bandas de `evaluar_punto`. Errores de claves o aritmética propagan, no se clasifican como «motor vacío». Ejemplo de prueba: `referencia_independiente(PARAMETROS_PREDETERMINADOS,10)['trabajo_neto']≈369.476301`.
- `gradientes_r(p, rp, parametro)` recibe el mismo `dict`, `rp` y un `str` entre `T1`, `T3`, `eta_c`, `eta_t`, `delta`. Devuelve tupla de tres `float`: `(dW/dx, dQin/dx, deta/dx)`, con unidades correspondientes a x. Llama `referencia_independiente`, utiliza el diccionario de derivadas y la regla del cociente. Lanza `ValueError` si no hay motor en el oráculo; nombre no previsto causa `KeyError`. La llaman pruebas de R, extremos y teorema de la envolvente. Ejemplo: `gradientes_r(PARAMETROS_PREDETERMINADOS,10,'T3')[0]≈0.429100227` kJ/(kg·K).
- `rp_max_trabajo_independiente(p)` recibe ese `dict` y devuelve `float` adimensional del **candidato matemático A**, sin comprobar dominio. No llama funciones externas de proyecto; la usan las pruebas de A. Requiere parámetros físicos válidos y representables (el test suministra casos moderados; una aritmética inválida propaga su excepción). Ejemplo: `rp_max_trabajo_independiente(PARAMETROS_PREDETERMINADOS)≈12.89505167`.

`VerificacionSensibilidadIndependiente(unittest.TestCase)` contiene ocho `test_*(self)` sin argumentos adicionales ni retorno útil: `unittest` los descubre y los ejecuta; `setUp(self)` copia el diccionario predeterminado antes de cada uno. `subTest` identifica parámetros/casos sin duplicar métodos. `@unittest.skipUnless(find_spec('scipy') is not None, ...)` omite **explícitamente sólo la prueba B** si SciPy no está instalado; no añade esa librería a `requirements.txt`. Dentro de B se importa `minimize_scalar` y se exige `success`, dominio abierto y magnitudes motoras. `assertAlmostEqual(obtenido,referencia,delta=tolerancia)` compara diferencias absolutas en unidades físicas, no igualdad exacta ni «número de decimales». Las regresiones de la propia sensibilidad (`25`) y cuatro de optimizadores se ejecutaron aparte, sin suite completa.

**Resultados reales (22/10/2026):** ocho pruebas nuevas y 29 regresiones relacionadas, **37/37 correctas**, sin fallos ni omisiones con SciPy 1.17.0 (Linux/Python 3.12.14). En R, las dos referencias físicas dieron errores máximos `1.137e−13 K`, `1.137e−13 kJ/kg` y `1.110e−16` en eta fraccionaria. El mayor error absoluto en 15 derivadas fue `3.439e−8` en `dW/ddelta` y el mayor relativo `2.882e−10` en `deta/dT3`. En B, la discrepancia de posición frente a SciPy llegó a `5.798e−7` en rp, mientras `|Δeta|≤2.220e−16`; máximos planos explican que diferencias de posición superen diferencias del valor. Se verificaron también R no motor, dominio vacío, fronteras unilaterales y supremo reversible ideal. Tolerancias y limitaciones detalladas en [13](docs/milestones/13_verificacion_sensibilidad.md). La suite **215/215 del cierre anterior no se volvió a ejecutar**.

### 4.52. V.2 — referencias independientes del Mapa de Diseño rp–T3 (milestone 14)

**Estado y alcance.** La [verificación técnica V.2](docs/milestones/14_verificacion_mapa_diseno.md) se preparó sobre la rama `mejoras/verificacion-numerica`, con base remota comprobada `8d767b69858c4a3a055c11bbba3294124770d743` y **se publicó** después como commit `d6f9dc9d9ebd14b3de991623cb9d5653195ed4e9`. Se incorporó `tests/test_verificacion_mapa_diseno.py`, con nueve métodos nuevos, sin tocar `mapa_diseno.py`, `viabilidad.py`, los optimizadores, dependencias, Flask o interfaz. Las 21 pruebas anteriores de `tests/test_mapa_diseno.py` siguen cubriendo dimensiones, ejecución, gráficos, informes y Flask; V.2 añade **ecuaciones de referencia reconstruidas sin delegar al código físico que se comprueba**. No añade funciones al programa.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Para cada par `(rp,T3)` se reconstruyen `a=(gamma−1)/gamma`, `rp_e=rp(1−delta)`, `k=cp/1000`, `T2=T1[1+(rp**a−1)/eta_c]` y `T4=T3[1−eta_t(1−rp_e**(−a))]`. De ahí, `wc=k(T2−T1)`, `wt=k(T3−T4)`, `W=wt−wc` y `Qin=k(T3−T2)` en kJ/kg; `eta=W/Qin` sólo se publica para un motor aceptado. `W` y `Qin` conservan sus signos aunque no exista motor. En el mapa, `matrices['rendimiento']` multiplica la fracción por 100, mientras `matrices['trabajo_neto']` y `matrices['calor_aportado']` no cambian de unidad. La fila `i` es `T3[i]` y la columna `j` es `rp[j]`: no se transponen los datos para dibujar.

La condición de trabajo se comprueba con `x=rp**a`, `theta=T3/T1`, `h=theta*eta_c*eta_t` y `b=(1−delta)**(−a)`. La identidad `W=−k*T1*Q(x)/(eta_c*x)` para `Q(x)=(x−1)(x−h)+h*(b−1)` convierte `W>0` en `Q(x)<0`. Las raíces `x±=(1+h±sqrt((h−1)**2−4*h*(b−1)))/2`, cuando son reales y distintas, delimitan trabajo positivo. El dominio motor abierto es la intersección con `rp>1`, `rp>1/(1−delta)` y `rp<(1+eta_c*(theta−1))**(1/a)`. **Discriminante positivo no basta**: en el perfil adverso N2, `T3=400 K`, se midió `D≈0.0461373` pero dominio vacío por falta de intersección física. El discriminante negativo de otras filas tampoco se convierte en «error numérico».

Las bandas `TOL_REL=1e−10` vigentes excluyen puntos con margen insuficiente, sin alterar las fronteras matemáticas. Por ejemplo, en N1, `T3=1600 K`, a distancia relativa `1e−12` por dentro de cada extremo se calcularon `W≈3.12e−10 kJ/kg`, menores que `tol(W)=1.608e−7 kJ/kg`: esos puntos no son motores, **aunque su trabajo matemático sea positivo**. A distancia `1e−6` ambos se admitieron. Ninguno se confundió con `ErrorNumerico`.

**PYTHON — nuevas funciones auxiliares, sólo en el archivo de pruebas:**

- `referencia_termodinamica(parametros, rp, T3)`: `parametros` es el `dict` de entradas físicas (`T1`, `cp`, `gamma`, `p1`, `eta_c`, `eta_t`, `perdida_presion_combustor`), `rp` adimensional y `T3` [K]. Devuelve un `dict` con tupla `temperaturas` [K], `trabajo_compresor`, `trabajo_turbina`, `trabajo_neto`, `calor_aportado` [kJ/kg], `rendimiento` fraccional o `None`, dos booleanos (`estrictamente_motor`, `admitido`), y dicts de márgenes/tolerancias y tupla `motivos`. No llama módulos del proyecto; lo utilizan las pruebas de celdas, bandas, trayectorias, invariantes y cortes y el objetivo local SciPy. Las entradas de los tests son finitas y moderadas; claves faltantes, divisiones inválidas o desbordamientos propagan las excepciones Python, sin inventar una clasificación. Ejemplo: `referencia_termodinamica(p,10,1600)['trabajo_neto']≈369.476301` para N1.
- `fronteras_cerradas(parametros, T3)`: mismas entradas físicas y temperatura [K]; devuelve `dict` con `discriminante`, coeficientes auxiliares `h`, `b`, `expansion`, `calor`, `trabajo` (tupla de extremos rp si `D>0`) e `intervalo` (par rp **abierto** o tupla vacía). Sólo usa aritmética y `sqrt`, sin llamar a `calcular_dominios`; lo usan las pruebas de fronteras, bandas, A y B. Sus fórmulas cerradas presuponen coeficientes representables, y no se usan para casi raíces dobles; valores o exponentes inválidos propagan excepciones. Ejemplo: `fronteras_cerradas(p,1600)['intervalo']≈(1.069654102,155.454326039)` en N1.
- `rp_max_trabajo(parametros, T3)`: recibe el mismo diccionario y `T3` [K], devuelve un `float` rp adimensional correspondiente al estacionario **matemático** `rp_A**a=sqrt(eta_c*eta_t*T3/T1*(1−delta)**(−a))`; **no** garantiza admisibilidad. Lo usan las pruebas de A y del reversible; sin llamadas a funciones del simulador. Parámetros fuera del contrato causan excepciones aritméticas o de claves. Ejemplo: `rp_max_trabajo(p,1700)≈14.338335212` para N1.

`VerificacionMapaIndependiente(TestCase)` contiene nueve métodos `test_*(self)`, sin argumentos adicionales ni retorno significativo: celdas/signos, frontera/discriminante, banda, A, B opcional con SciPy, ideal y ventana visual, mallas anidadas, invariantes y datos de gráficos/cortes. `subTest` da nombre a cada fila comparada. `@skipUnless(find_spec('scipy') is not None, ...)` omite **sólo B** si SciPy no está instalado, sin hacerlo obligatorio; ese método importa `minimize_scalar` dentro y optimiza `−eta(log(rp))` usando el oráculo. `patch.object(plt.Axes,'pcolormesh', ...)` y `patch.object(plt.Axes,'plot', ...)` observan matrices, máscara, `shading='nearest'`, ejes y trayectorias sin cambiar la implementación; las líneas A/B fuera de ventana usan `NaN` sólo para dibujarse, no modifican las posiciones físicas almacenadas.

**Resultados ejecutados el 22/10/2026.** En once celdas representativas el máximo error frente al oráculo fue `2.274e−13 K`, `4.547e−13 kJ/kg` y `4.996e−16` en eta fraccionaria. En diez filas y dos perfiles, el mayor error de frontera fue `3.359e−11 rp`. Para A (diez filas) el máximo error fue `2.132e−14 rp` y `2.842e−13 kJ/kg`; B frente a SciPy (cuatro filas) llegó a `2.703e−6 rp` pero sólo `6.661e−16` de error máximo en rendimiento como fracción. El máximo muestreado con malla anidada `7×3 → 13×5` no empeoró; en una fila el mejor rendimiento muestreado **no cambió**, sin que eso implique defecto. Se cumplieron los invariantes de escalado `cp`, independencia de `p1`, variación de `W` con `T3` y primera ley. **Nueve pruebas nuevas y 21 regresiones del mapa: 30/30 correctas**, sin fallos ni omisiones en Linux/Python 3.12.14 con SciPy 1.17.0. Las nueve nuevas se repitieron de forma focalizada tras reforzar las aserciones sobre raíces y trazas gráficas; no se sumaron dos veces. La suite histórica **215/215** pertenece al cierre anterior y no se ha repetido. Véanse tablas, márgenes y criterios del [documento 14](docs/milestones/14_verificacion_mapa_diseno.md). Ninguna comparación con fórmulas o SciPy equivale a validación experimental de un motor real, ni demuestra compatibilidad nativa con Windows.

### 4.53. Verificación independiente de Segunda Ley y Exergía — `tests/test_verificacion_segunda_ley.py`

**Alcance actual.** V.3 añade sólo nueve métodos de prueba y su [documento técnico educativo 15](docs/milestones/15_verificacion_segunda_ley.md), en una copia temporal de la rama `mejoras/verificacion-numerica` creada desde `d6f9dc9d9ebd14b3de991623cb9d5653195ed4e9`. **Pendiente de revisión; sin commit ni push.** Se conserva el módulo `segunda_ley.py` y su contrato documentado en §4.44: cuatro estados, entropías relativas, generación adiabática, destrucción de exergía sólo en compresor/turbina, diagnóstico no motor, inconsistencias y límites numéricos. V.3 **verifica esos cálculos con referencias nuevas**; no incorpora ecuaciones de producción, dependencias, nuevas gráficas ni parámetros de interfaz.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** El oráculo independiente emplea `Δs=cp/1000·ln(Tj/Ti)−R/1000·ln(pj/pi)`, `R=cp·(gamma−1)/gamma`, [kJ/(kg·K)], con presión en unidad común, y reconstruye `T2,T4,p2,p3` mediante ecuaciones isentrópicas y eficiencias, **sin llamar al código comprobado**. Contrasta los cuatro valores `s` y saltos sucesivos, y utiliza también las fórmulas cerradas para `s_gen,c` y `s_gen,t`. Una tercera identidad evita una comprobación circular de Gouy–Stodola: `eD,c=wc−[(h2−h1)−T0(s2−s1)]` y `eD,t=[(h3−h4)−T0(s3−s4)]−wt`, con `h_j−h_i=cp(Tj−Ti)/1000`. Se exige `eD=T0·s_gen` y concordancia de la suma **parcial** cuantificada, sin llamarla exergía destruida total del motor. Para `s3−s2` se contrastan términos térmicos y de presión sin declarar generación de la cámara; el punto no motor conserva sus entropías, pero no recibe rendimiento motor ficticio.

**PYTHON — funciones auxiliares exclusivas de pruebas.** `entropia_decimal(Ti, pi, Tj, pj, cp, gamma)` recibe seis números positivos (temperaturas K, presiones en kPa o unidad común, cp en J/(kg·K), gamma>1) y devuelve una tupla `(termica, presion, total)` de `float` en kJ/(kg·K). Usa `decimal.Decimal(str(valor))`, `localcontext` con precisión 70 y `.ln()`; el `map(lambda x: ..., ...)` convierte los seis argumentos a Decimal. No llama funciones del simulador y la invocan los tests de estados, límite reversible y exergía; las entradas inválidas pueden producir errores aritméticos de `Decimal`. Ejemplo: `entropia_decimal(300,100,600,100,1005,1.4)[2]≈0.6966`. `estados_referencia(parametros)` recibe el diccionario de nueve parámetros físicos y devuelve `dict(temperaturas=(T1,T2,T3,T4), presiones=(p1,p2,p3,p1), wc=..., wt=...)` con K, kPa y kJ/kg; lo usan las pruebas de estados, cámara y balances. No llama a `evaluar_punto` ni a `segunda_ley`; las claves ausentes o entradas fuera de su dominio matemático propagan excepciones Python. Ejemplo: `estados_referencia(PARAMETROS_PREDETERMINADOS)['temperaturas'][1]≈603.657 K`.

**PYTHON — clase y aserciones.** `VerificacionSegundaLeyIndependiente(TestCase)` define `setUp(self)` (sin argumentos adicionales ni valor devuelto, copia parámetros físicos) y `punto(self, parametros)` (recibe un `dict`, devuelve el `dict` de `evaluar_punto` con estados [K, kPa], energías [kJ/kg], motivos y rendimiento opcional; lo llaman sus tests). Nueve métodos `test_*(self)` sin valor de retorno cubren: entropías y telescopado, generaciones independientes, reversibilidad y banda de negativos, balances alternativos de exergía, cámara, invariantes T0/cp/p1, extremos/entradas inválidas, diagnósticos, y coordenadas T–s/barras/HTML. `subTest` diferencia perfiles sin duplicar métodos; `assertAlmostEqual(...,delta=...)` expresa tolerancia **absoluta**, especialmente importante cerca de `s_gen=0`. Los callbacks internos `capturar_traza(ejes,*args,**kwargs)` y `capturar_barras(ejes,*args,**kwargs)` registran datos destinados a Matplotlib y **devuelven la llamada original**; `patch.object` limita la interceptación al bloque de test. Estos callbacks reciben el objeto Axes y argumentos gráficos, devuelven los artistas Matplotlib, no calculan termodinámica; sólo los invoca el renderizador bajo prueba.

**Tolerancias y observaciones reales, 22/10/2026.** Para entropía decimal se acepta `3e−13 kJ/(kg·K)`, para generación analítica `5e−13`, para eD por balance alternativo `3e−10 kJ/kg`, y para generación bruta casi reversible `7e−13` absoluta. En cinco perfiles (base, otros dos motores, no motor y reversible) el máximo observado frente a Decimal fue `6.8002e−16 kJ/(kg·K)` para estados y `1.9185e−13 kJ/kg` para eD; en cuatro perfiles no ideales y magnitudes mayores que `1e−9`, errores relativos máximos `6.030e−15` y `1.122e−14` respectivamente. Son **errores observados**, no cotas universales. El caso base reconstruido dio `s_gen,c≈0.0820509581`, `s_gen,t≈0.0868491326 kJ/(kg·K)`, `eD,c≈23.6429836`, `eD,t≈25.0255776 kJ/kg` y suma parcial `≈48.6685611 kJ/kg`. En el perfil no motor T3=400 K y rp=50, `s3≈−0.778958` y `s4≈−0.594604` son diagnósticos relativos, no prestaciones motoras. Escalar T0 sólo cambia eD; cp escala s/eD; p1 no altera diferencias de entropía. Se ensayaron también números extremos `1e−300` y `1e300` (sin formar cocientes `float`), un incremento relativo de T de orden `1e−13`, entradas inválidas y desbordamiento identificado.

**Ejecuciones focalizadas:** 9/9 pruebas nuevas OK en 0.599 s (la primera pasada, 8/9, puso de manifiesto un supuesto **erróneo del test** sobre desbordamiento con `T0=1e308`; se corrigió el dato de entrada del test a `cp=20000`, sin cambios de producción). 22/22 regresiones distintas OK en 0.776 s: las 18 de `tests/test_segunda_ley.py`, dos de `test_verificacion_analitica.py` y dos de `test_invariantes_fisicos.py`. **31 métodos distintos correctos, cero fallos finales ni omisiones;** no se ha repetido la suite completa de 215 ni se ha ensayado Windows. Entorno Linux/Python 3.12.14, NumPy 2.5.4, Matplotlib 3.11.2, Flask 3.1.3 y Jinja2 3.1.6, aislado con `requirements.txt`; SciPy no fue necesario. Esto verifica la implementación de las ecuaciones, **no** su validez experimental como representación de un motor real.

### 4.54. Verificación V.4 de Simulación — `tests/test_verificacion_simulacion.py`

**Estado.** La [V.4 de Simulación, gráficos e informes](docs/milestones/16_verificacion_simulacion.md) se preparó el **23/10/2026**, sobre la copia limpia de `mejoras/verificacion-numerica` en el commit remoto `df8389207e53d22cb10474e96ec1a77e6650cf57`. Está **pendiente de revisión y commit**. Sólo añade un archivo de pruebas y su documentación; no cambia `main.py`, `viabilidad.py`, `reporting.py`, `dashboard.py`, `web_app.py` ni los siete gráficos que genera el programa. La nueva verificación complementa, sin sustituir, las pruebas originales de reporting, dashboard, web y optimización.

**INTERPRETACIÓN FÍSICA / INGENIERÍA — tres preguntas distintas.**

1. **¿Se calcula correctamente?** Se reconstruyen los estados del ideal y no ideal a partir de `a=(gamma−1)/gamma`, `p2=p1·rp`, `p3=p2·(1−delta)`, `T2=T1+(T1·rp**a−T1)/eta_c` y `T4=T3−eta_t·(T3−T3·(p1/p3)**a)`. Con `cp` en J/(kg·K), `wc=cp·(T2−T1)/1000`, `wt=cp·(T3−T4)/1000`, `W=wt−wc`, `Qin=cp·(T3−T2)/1000` en **kJ/kg**. `eta=W/Qin` es una fracción y `BWR=wc/wt`, sólo en puntos motores; los dos perfiles aceptados tienen resultados físicamente distintos.
2. **¿Se transmite correctamente?** Los datos de cada ejecución enviados a `crear_informe_html` se comparan con una referencia física separada, incluidos los cuatro estados y los valores de A/B. Los estados que recibe el bloque de Segunda Ley pertenecen a esa misma ejecución. `delta=0.12` viaja como **fracción** aunque el formulario muestre **12 %**; en las tarjetas, `eta` se multiplica por 100 antes del redondeo visible.
3. **¿Se representa correctamente?** Las siete gráficas usan coordenadas y unidades apropiadas: rendimiento en %, trabajos en kJ/kg, presión P–v en kPa y entropía T–s en kJ/(kg·K). T–s y P–v corresponden **sólo al ideal**. Las curvas en puntos no motores contienen `NaN`, no ceros ficticios; el compromiso es un barrido de `rp`, no una frontera de Pareto completa. Se cotejan series y marcadores de Matplotlib, y los siete PNG recibidos por el informe coinciden byte a byte con su incrustación Base64.

**PYTHON — utilidades locales, sin nueva API de producción:**

- `referencia_fisica(parametros, *, ideal=False, rp=None)`: recibe `parametros: dict` con nueve entradas físicas (`T1`, `T3` [K], `p1` [kPa], `cp` [J/(kg·K)], `gamma`, `relacion_presiones`, `eta_c`, `eta_t`, `perdida_presion_combustor` adimensionales); `ideal: bool` selecciona límite reversible y `rp: float | None` permite evaluar otra relación sin mutar el diccionario. Devuelve `dict` con `temperaturas` y `presiones` (tuplas de cuatro estados), `T2s`, `T4s` [K], `trabajo_compresor`, `trabajo_turbina`, `trabajo_neto`, `calor_aportado` [kJ/kg], `rendimiento` (fracción o `None`), `back_work_ratio` (adimensional o `None`) y `viable` (`bool`). Lo llaman los tests directamente y `comprobar_referencia`; usa exclusivamente aritmética Python, sin `main` ni `viabilidad`. No valida entradas genéricas, pues opera sobre perfiles finitos moderados; `KeyError`, divisiones u otros errores matemáticos se propagan. Ejemplo: `referencia_fisica(BASE)['trabajo_neto']≈369.476301 kJ/kg`.
- `capturar_figuras()`: gestor de contexto **sin argumentos**, producido mediante `@contextmanager`; ofrece una `list` de objetos `Figure` antes de cerrarse. Reemplaza temporalmente `Figure.savefig` con `unittest.mock.patch.object` y recopila la figura en lugar de escribir PNG. Los tests de trazado lo invocan `with capturar_figuras() as figuras:`. No calcula física ni altera permanentemente Matplotlib; devuelve/restaura el método al salir del `with`, incluso ante errores. Ejemplo: dentro del bloque, `figuras[0].axes[0].lines` permite leer una curva; la función original vuelve tras salir.
- `curva(ejes, etiqueta)`: recibe un objeto `Axes` de Matplotlib y `etiqueta: str` (prefijo de la leyenda). Devuelve exactamente una instancia `Line2D`, seleccionada semánticamente sin depender del orden de creación; lanza `AssertionError` si encuentra cero o varias. La usan pruebas de T–s, P–v, rendimiento, trabajo y compromiso. Ejemplo: `curva(figuras[0].axes[0], '1→2').get_xdata()` recupera las abscisas de compresión.
- `VerificacionSimulacionIndependiente.comprobar_referencia(self, observado, esperado, *, ideal=False)`: método auxiliar de la clase `unittest.TestCase`. `observado` y `esperado` son los diccionarios de resultados físicos descritos arriba, `ideal` etiqueta los `subTest`. No devuelve un valor útil: lanza `AssertionError` si hay discrepancia de temperaturas, presiones, referencias isentrópicas, balances, rendimiento, BWR o identidades energéticas. Lo llaman las pruebas de dos perfiles y de la cadena al HTML. Usa `np.testing.assert_allclose` para estados y `assertAlmostEqual(...,delta=...)` para magnitudes, no redondea antes de comparar.

Los ocho métodos públicos `test_*(self)`, sin argumentos adicionales y sin retorno útil, son invocados por `unittest`; cubren: dos perfiles de estados/energía, trayectorias T–s, trayectorias P–v, rendimiento/trabajo ideal, comparación ideal/no ideal, compromiso y B ausente, dos simulaciones completas con PNG/KPI/Segunda Ley, y formulario más punto no motor. `subTest` repite perfiles dentro de un método sin inflar el recuento. `patch.object` observa la **interfaz** entre módulos sin sustituir su física; `TemporaryDirectory` elimina sólo los archivos creados por la prueba, nunca informes reales.

**Resultados reales:** los 8 métodos nuevos pasaron en **3.572 s** y las **61** regresiones relacionadas de `test_reporting`, `test_dashboard`, `test_integracion_rendimiento`, `test_web_app` y `test_explicaciones` pasaron en **46.146 s**: **69 distintos correctos**, cero fallos, errores u omisiones. Después de ampliar las comprobaciones de KPI A/B y los estados del estudio de Segunda Ley se repitió **sólo ese método** (1/1 correcto, 3.611 s), sin ejecutar la suite completa. En los dos perfiles y ambos modelos, la diferencia máxima observada entre el oráculo `float` y los estados/balances de producción fue **0 a resolución de `float`**; al ser fórmulas equivalentes, esto no constituye una garantía general. Se aplicaron tolerancias numéricas `atol=3e−10` y `rtol=3e−13` a estados y hasta `4e−10` en series de energía, según la prueba; los HTML redondean de otra forma (2, 3 o 6 decimales). La matriz de gráficas, cifras, procedimiento y limitaciones se detallan en el milestone 16.

La **verificación de software** afirma que, dentro de los casos y tolerancias estudiados, el programa calcula, transmite y representa correctamente *las ecuaciones implementadas*. **Validación experimental** exigiría comparar esas ecuaciones con medidas reales o un modelo externo independiente de mayor fidelidad, lo cual no se ha hecho. La ejecución fue en Linux/Python 3.12.14 con dependencias declaradas; no se probó Windows. No se modifica producción ni se inicia una nueva etapa.

### 4.55. Verificación V.5 de integración web — contrato histórico conservado

**Situación vigente desde el milestone 30:** el archivo de esta etapa se
mantiene en `legacy_tests/test_verificacion_integracion_web.py`, con la adaptación de portabilidad del subcaso de enlace simbólico descrita a continuación.
El siguiente relato describe **la antigua fachada Flask de nueve parámetros**,
no la interfaz cp(T) actualmente conectada a `/`. El dashboard actual tiene
siete parámetros, devuelve HTTP 200 con los resultados y no crea informes
nuevos; su compatibilidad de lectura de los informes anteriores se comprueba
con `tests/test_web_app.py` y `tests/test_integridad_historica_actual.py`.
La organización y el comando de pruebas vigentes se explican en §4.68. La prueba histórica de listado mantiene sus comprobaciones de metadatos y filtrado. La creación del enlace simbólico se aísla en `with self.subTest(...)`: sólo si Windows devuelve `winerror == 1314`, `self.skipTest(...)` registra la omisión de ese subcaso y continúan las demás comprobaciones. Otros errores se propagan; no se cambia la protección de producción contra enlaces simbólicos.

**Estado.** La [verificación V.5](docs/milestones/17_verificacion_integracion_web.md)
se preparó el **23/10/2026**, desde `mejoras/verificacion-numerica` en el commit
`eae71fecab71ba6cd5877e0e81f4dd396c08cb43`, en una copia temporal
independiente. **Pendiente de revisión, sin commit ni push.** Contiene sólo
12 métodos nuevos de prueba, el documento 17 y esta actualización didáctica.
No añade rutas, funciones ni dependencias a producción; V.1–V.4 siguen
siendo responsables de la verificación de los modelos matemáticos.

**INTERPRETACIÓN FÍSICA / INGENIERÍA — qué se conserva al cruzar la web.**
Las nueve entradas se introducen como texto y `web_app.leer_parametros`
las convierte a `float`; las temperaturas son K, `p1` kPa, `cp`
J/(kg·K), `gamma`, `rp` y eficiencias son adimensionales. Sólo
`perdida_presion_combustor` cambia de convención: `7.5 %` visible
se entrega como fracción `0.075`. Esa conversión no significa añadir
o retirar una pérdida energética: se trata del mismo parámetro. La temperatura
`T0` [K] se usa en normal/Segunda Ley para exergía, **no** se usa en
sensibilidad OFAT ni mapa de diseño. En Segunda Ley,
`e_D=T0·s_gen` para los dos equipos adiabáticos estudiados; variar
`T0` con estados físicos idénticos puede actualizar la exergía destruida
sin resolver el ciclo otra vez. Si cambia una de las nueve entradas, el
estudio anterior no es compatible. Esta lógica es de **transporte y
reutilización de resultados**, no un nuevo modelo termodinámico.

**PYTHON / HTTP — el flujo completo:**

1. `Flask.test_client()` devuelve un cliente de pruebas sin abrir una
   conexión real. `client.post("/", data=datos)` construye el formulario;
   `request.form` contiene cadenas y el servidor usa un `dict` para
   las entradas. El campo `accion` elige `main`, `ejecutar_sensibilidad`,
   `ejecutar_mapa` o `ejecutar_segunda_ley` sin mezclar sus controles.
2. Antes de calcular, el servidor valida campos y configuración del modo.
   Un error esperado devuelve HTTP **400** con los mismos valores escritos
   y sin informe. El éxito devuelve HTTP **303**, redirigiendo a
   `/informes/<nombre>`; **303 no contiene en sí mismo el informe**.
   Una excepción inesperada se registra y devuelve **500** genérico,
   sin atribuirla equivocadamente a imposibilidad física.
3. `guardar_informe_html` escribe un documento con nombre y marcas
   propios, y el índice conserva un máximo de cuatro. `listar_informes`
   recupera información de fecha, parámetros y versión Git si existe
   metadata moderna, sin falsificarla en informes antiguos. No lee rutas
   arbitrarias ni sigue enlaces simbólicos.
4. `ver_informe` rehidrata en el dashboard los nueve campos, OFAT, mapa
   y `T0` guardados, sin ejecutar otra simulación. La ruta de descarga
   `?descargar=1` devuelve el **HTML original byte a byte**.
   Los informes anteriores pueden tener un enlace añadido **sólo a la
   respuesta en memoria**, nunca a su archivo guardado.
5. `estudio_conservado` comprueba nombre/ubicación/marcas,
   metadata y equivalencia de las nueve entradas. En una prueba real,
   `actualizar_T0` recibió un estudio completo guardado, conservó
   temperaturas/entropías y aplicó `e_D(310.5)=310.5·s_gen`.
   Las tuplas de Python se almacenan como listas en JSON: deben
   compararse como estructuras serializadas, sin confundir esa
   representación con un cambio físico.

**PYTHON — clases y auxiliares nuevos, exclusivos de pruebas:**

- `FormularioParser(HTMLParser)` guarda `campos: dict` a partir de
  controles HTML. `handle_starttag(self, tag, attrs)` recibe nombre
  del elemento y lista de pares atributo/valor, y registra los `input`
  y `select` con nombre, incluida la opción marcada `selected`.
  `handle_endtag(self, tag)` borra la selección en curso al cerrar
  un `select`. Ambos son callbacks de `html.parser` y no devuelven
  un valor útil; el parser **no interpreta JavaScript**. Ejemplo:
  `p = FormularioParser(); p.feed(html); p.campos["T1"]["value"]`
  obtiene el texto conservado por la plantilla.
- `VerificacionIntegracionWebV5.setUp(self)` no recibe entradas ajenas
  ni devuelve datos: crea `TemporaryDirectory`, cliente Flask,
  nueve parámetros de prueba y ajustes OFAT/mapa. Usa
  `patch.dict(app.config, ...)` y `addCleanup` para restaurar
  configuración y borrar sólo sus temporales, incluso si falla
  una aserción. No afecta `outputs/` real.
- `VerificacionIntegracionWebV5._informe(self, tipo, *, parametros=None,
  segunda_ley=None)`: recibe `tipo: str`, un diccionario opcional de
  nueve parámetros y un estudio opcional; devuelve
  `(ruta: Path, contenido: str, metadata: dict)`.
  Construye un informe **sintético marcado** para probar el índice,
  la rehidratación y la compatibilidad antigua, no para demostrar
  las ecuaciones. En el test de reutilización, el estudio asociado
  sí se calcula con `analizar_segunda_ley` sobre estados reales
  antes de insertarlo en el informe.
- Los doce métodos `test_*(self)`, sin retorno útil, comprueban:
  cuatro despachos/argumentos, rechazos y preservación de datos,
  cuatro ejecuciones reales, historial y formato anterior, recuperación
  y descarga sin recálculo, reutilización de T0, rutas malformadas,
  error inesperado y estructura de las ocho secciones.
  `self.subTest(...)` distingue los siete casos inválidos y las
  variantes sin multiplicar artificialmente el número de métodos.
  `patch.object` intercepta sólo durante el bloque `with` los
  ejecutores cuya llamada se quiere comprobar; después recuperan
  sus implementaciones normales.

**Resultados ejecutados en Linux, 23/10/2026.** Los **12 métodos nuevos**
pasaron en **4,442 s**. Una selección de **14 regresiones** (web 4,
dashboard 5, guías 3, Segunda Ley 1 y mapa 1) terminó correctamente
en **4,725 s** de tiempos `unittest` sumados; total **26 métodos
distintos correctos, cero fallos, errores u omisiones finales**.
Una expectativa del test sobre pestañas de Informes/Ayuda y otra
sobre tuplas convertidas en listas JSON se corrigieron durante
la preparación; tampoco los nombres mal escritos de dos clases
en una primera invocación de regresiones constituyen un fallo de
producción. No se ejecutaron las 69 pruebas completas de V.4 ni
la suite histórica. Se utilizó el entorno aislado preexistente con
Flask 3.1.3/Python 3.12.14, sin instalar dependencias.

**Límites.** `test_client` no prueba los controles JavaScript en navegador,
compatibilidad Windows, concurrencia, ni seguridad exhaustiva;
los informes sintéticos sólo verifican contratos de representación.
Durante la ejecución original de V.5, `estudio_conservado` no validaba el
esquema interno `segunda_ley` de un JSON manipulado; aquella batería ensayó
uno físicamente completo y fuentes incompatibles por entradas. La comprobación
posterior de integridad interna se describe en §4.44: no protege
contra toda falsificación coherente ni equivale a autenticación. La verificación
de software no implica validación experimental de un turbomotor.
Los métodos, datos, rechazos y límites se desglosan en el
[milestone 17](docs/milestones/17_verificacion_integracion_web.md).

### 4.56. Diagnóstico y coherencia física del informe actual

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** El diagnóstico consume los resultados de la ejecución y contrasta sus relaciones, restricciones y disponibilidad. No ejecuta las pruebas V.1–V.5 ni sustituye su evidencia histórica. Un estado **Cumple** significa que se satisface esa relación y su tolerancia con los datos indicados; **Atención** identifica una discrepancia, una restricción incumplida o un límite registrado; **No evaluable** identifica datos ausentes o una ecuación inaplicable. Ninguno constituye validación experimental. Las ecuaciones y los optimizadores de producción permanecen iguales.

#### Arquitectura, recorrido de datos y modalidades

```text
main / sensibilidad / mapa / segunda_ley → resultados existentes
    → reporting: elige paneles y llama diagnostico_informe
    → diagnostico: registros científicos por ciclo u óptimo
    → diagnostico_informe: resumen y, en estudios, agrupación
    → diagnostico_html: HTML escapado
    → dashboard: paneles guardados + metadata → vista local / autónomo
```

`diagnostico.py` contiene las relaciones científicas; `diagnostico_informe.py` conoce la estructura de los estudios; `diagnostico_html.py` sólo presenta. El motor utiliza las bandas motoras guardadas si son completas; cuando faltan y existen las energías, llama a `evaluar_punto` para recuperar **las bandas vigentes**. Los márgenes se calculan con los valores recibidos, y las magnitudes ausentes no se reemplazan por las que pudiera recalcular el evaluador. No se vuelve a ejecutar ninguna optimización.

| Modalidad / panel | Datos inspeccionados y alcance |
|---|---|
| Simulación / Resultados | Ciclos ideal y no ideal del caso actual; Segunda Ley si se proporcionó. |
| Optimización | Estudios A/B ideal y no ideal, naturaleza del resultado, candidatos guardados y contraste analítico/numérico sólo si consta. El supremo reversible no recibe un ciclo ficticio. |
| Sensibilidad | Todos los registros R/A/B del barrido y la referencia local existente; no se limita a los índices que tenían contraste independiente. La ausencia de ese contraste se indica como no evaluable. |
| Mapa de diseño | Todas las celdas guardadas de la malla, óptimos A/B por T3 y cortes adicionales cuya T3 no coincide con una fila de la malla. Una fila compartida no se cuenta dos veces. |
| Segunda Ley | Estados y análisis guardados de ambos modelos. Este estudio no conserva trabajos/calores: sus controles energéticos permanecen no evaluables, aunque haya temperaturas. |

En OFAT y mapa se evalúan todos los registros disponibles y después se agrupa por `(grupo, id)`. Los contadores superiores suman **controles individuales**, no filas HTML ni sólo muestras viables. Una fila agrupada conserva `conteos` por estado, `muestras` y los valores de **un ejemplo localizado**; prioriza Atención, después No evaluable y, en igualdades del mismo estado, el mayor `abs(residuo)/tolerancia`. Las desigualdades no se ordenan como si su margen fuese un error de igualdad. La tolerancia expuesta pertenece a ese ejemplo, no a todas las muestras de la fila. Las muestras excluidas no se eliminan para mejorar artificialmente el resumen.

#### Registro, residuos y criterio de tolerancia

**PYTHON.** Cada control es un `dict`: `id`, `nombre`, `grupo`, `relacion`, `valor`, `referencia`, `residuo`, `residuo_relativo`, `tolerancia`, `unidad`, `estado`, `explicacion`, `motivo`, `criterio`, `naturaleza` y `comparacion`. El orquestador puede añadir `contexto`, `conteos` y `muestras`. `None` expresa ausencia, nunca un cero. Los estados internos son `cumple`, `atencion` y `no_evaluable`; el presentador los traduce. `naturaleza` distingue identidad, contraste de rutas del mismo modelo y restricción; `comparacion` identifica igualdad, desigualdad o clasificación para interpretarlas correctamente al agrupar.

Para una igualdad se guarda el residuo **absoluto** `abs(valor−referencia)` y, si la escala es positiva, el relativo `residuo/escala`. Se acepta

\[
 |v-v_{ref}|\leq\max(\mathrm{atol},\mathrm{rtol}\,S).
\]

`S` tiene la misma unidad que la magnitud; `rtol` no tiene dimensión. Sin escala explícita se usa `max(abs(v),abs(vref))`. El piso absoluto permite contrastar números próximos a cero sin dividir por un valor minúsculo. La escala térmica `SE=(cp/1000)·max(T1,T2,T3,T4)` evita que una cancelación en trabajo neto establezca una tolerancia físicamente desproporcionada respecto a las energías restadas. No es una estimación de incertidumbre de un motor real.

Las desigualdades conservan el valor del margen, la frontera de referencia y su banda. No se interpreta el tamaño del margen como error de igualdad: para `valor>limite` el déficit es `max(0,limite−valor)`; para no negatividad se muestra `max(0,−valor)` y se compara `valor>=−limite`. En igualdad exacta con una frontera estricta puede haber déficit cero y aun así Atención, pues la desigualdad es abierta. Las condiciones estrictas excluyen frontera y banda; la no negatividad de Segunda Ley admite exclusivamente el pequeño negativo de redondeo justificado por su escala.

| Comprobación y ecuación | Unidad / tolerancia | Significado y limitación |
|---|---|---|
| Cuatro T y cuatro p positivas y finitas | K / kPa; positividad estricta | Un dato negativo no se acepta por tolerancia. |
| `wc=cp(T2−T1)/1000`, `wt=cp(T3−T4)/1000`, `qin=cp(T3−T2)/1000` | kJ/kg; `max(1e−10,1e−9·SE)` | Coherencia de estados, signos y conversión J→kJ; comparte las ecuaciones de construcción. |
| `wn=wt−wc`; `wn=qin−qout`, `qout=cp(T4−T1)/1000` | kJ/kg; `max(1e−10,1e−9·SE)` | Identidades energéticas internas; no son dos pruebas físicas independientes. `qout` se reconstruye expresamente de los estados. |
| `η=wn/qin`; `BWR=wc/wt` | Adimensional; `max(1e−12,1e−9·S)` | Sólo con interior motor y denominador positivo. Rango `(0,1)` estricto y signo `qout>0` por separado. |
| `T1/T3` contra entradas; `p=(p1,p1·rp,p1·rp·(1−δ),p1)` | K / kPa; `max(1e−10,1e−9·S)` | Contraste de datos transmitidos; el ideal usa `δ=0`. Órdenes de T de los cuatro procesos se comprueban con margen estrictamente positivo. |
| `T2s=T1(p2/p1)^a`, `T4s=T3(p4/p3)^a`; `a=(γ−1)/γ` | K; `max(1e−10,1e−9·S)` | Se usan logaritmos y exponenciales para reducir desbordamientos de cocientes intermedios. Sólo el ideal exige que T2/T4 reales sean isentrópicas. |
| `ηc·(T2−T1)=T2s−T1`, `T3−T4=ηt·(T3−T4s)` | K; `max(1e−10,1e−9·max(T))` | Forma multiplicada de las eficiencias para no dividir por saltos casi nulos. La referencia se reconstruye desde presiones; sin saltos positivos, no evaluable. Ideal: ambas eficiencias igual a 1. |
| Ideal: `η=1−rp^(−a)` | Adimensional; `max(1e−12,1e−9·S)` | Otra ruta de implementación del mismo modelo; sólo en motor. |
| Motor: `rp−1`, `p3−p4`, `qin`, `wn` mayores que sus bandas | Adimensional, kPa, kJ/kg; bandas originales `1e−10·escala` | Reutiliza `evaluar_punto`; un residuo energético pequeño no demuestra viabilidad. Si el ciclo conserva `viable`, sólo se compara cuando es `bool`: `None` → No evaluable; texto o número → Atención, sin coerción a verdadero/falso. |
| `si−s1=(cp/1000)[ln(Ti/T1)−a·ln(pi/p1)]` | kJ/(kg·K); `max(1e−12,1e−9·max(abs(si),cp/1000))` | Contraste de las cuatro entropías relativas guardadas. La elección `s1=0` no es entropía absoluta ni generación. |
| Equipo adiabático: `sgen,bruta=(cp/1000)[ln(Tj/Ti)−a·ln(pj/pi)]` | kJ/(kg·K); `max(1e−12,1e−9·Ss)` | Contrasta generación bruta guardada con estados; `Ss=max(abs(si),abs(sj),cp/1000)`. |
| `sgen,bruta≥−1e−10·Ss`; `sgen=max(0,sgen,bruta)` sólo dentro de banda | kJ/(kg·K); banda de generación y tolerancia de igualdad anteriores | La corrección de redondeo no oculta un negativo significativo. Se mantienen valor bruto y cuantificado. |
| `eD=T0·sgen`; `eD≥−T0·banda_s` | kJ/kg; igualdad `max(1e−10,1e−9·abs(T0)·Ss)` | Gouy–Stodola es identidad de construcción; requiere T0 positiva. |
| `Δψ=cp·ΔT/1000−T0·Δs`; `eD,c=wc−(ψ2−ψ1)`, `eD,t=(ψ3−ψ4)−wt` | kJ/kg; `max(1e−10,1e−9·max(abs(w),abs(Δψ),abs(T0·sgen)))` | Balance alternativo de equipos adiabáticos, sin energía cinética/potencial; necesita el trabajo guardado. Comparte el modelo físico; no es referencia experimental independiente. |
| `eD,parcial=eD,c+eD,t` | kJ/kg; `max(1e−10,1e−9·S)` | Suma parcial; no es destrucción global ni `W_ideal−W_noideal`. Cámara/balance global quedan no evaluables. |
| Óptimo: rp dentro del intervalo abierto y ciclo motor; analítico frente a numérico | rp y η adimensionales; W en kJ/kg; tolerancias guardadas por el coordinador | Admisión no prueba optimalidad. El contraste sólo se declara si están sus dos resultados y tolerancia; no se inventa una búsqueda ausente. |
| Supremo reversible: `sup η=1−T1/T3`, no alcanzado | Adimensional; `max(1e−12,1e−9·S)` | Frontera excluida, sin candidato ni máximo numérico motor ficticio. |

Las tolerancias son de diagnóstico con `float`, adaptadas por magnitud. Una alerta señala una discrepancia para investigar; no corrige los datos ni cambia su valor. Si faltan trabajos en un informe de Segunda Ley, las filas de balance no se convierten en positivas por reconstruir las energías en silencio. La advertencia V.5 sobre JSON semánticamente manipulado de §4.55 permanece vigente.

#### Contratos completos del motor — `diagnostico.py`

Entradas físicas comunes: `parametros: dict` con las nueve claves de §5; `ciclo: dict | None` con resultados existentes; T [K], p [kPa], cp [J/(kg·K)], energías [kJ/kg], entropía [kJ/(kg·K)] y cocientes sin dimensión. Los números son escalares reales. Los prefijos `_` indican funciones de apoyo internas, no una sintaxis que las haga inaccesibles. Las funciones no escriben archivos y no modifican resultados recibidos; errores de contrato inesperados se propagan. Los nombres de funciones en la columna de relaciones son llamadas, no copias del cálculo.

| Firma completa | Argumentos, retorno, validaciones y relaciones; ejemplo |
|---|---|
| `_finito(valor)` | `valor: object` → `bool`: acepta `int`/`float` finitos, excluye `bool`, `None` y otros tipos. Sin unidades ni cálculo físico; usa `isinstance` y `math.isfinite`, sin llamadas propias. Lo llaman comparadores y diagnosticadores. Ejemplo: `_finito(None)` → `False`. |
| `_registro(identificador, nombre, grupo, relacion, unidad, explicacion, naturaleza="identidad", **datos)` | Siete textos más campos por nombre → `dict` uniforme inicialmente no evaluable; `**datos` reemplaza los valores predeterminados. Los escalares no finitos recibidos se convierten a texto para preservar una alerta serializable en JSON; no se convierten en éxito. Unidad descrita por `unidad`, sin conversión. Lo llaman `_comparar`, `_margen`, `diagnosticar_ciclo`, `_diagnosticar_segunda_ley` y `diagnosticar_optimizacion`; no llama funciones propias. Contratos de texto se presuponen. Ejemplo: `_registro('x','Balance','Caso','wn=wt−wc','kJ/kg','Consistencia')`. |
| `_comparar(identificador, nombre, grupo, relacion, valor, referencia, unidad, explicacion, *, atol=1e-12, rtol=1e-9, escala=None, naturaleza="identidad")` | Textos, `valor/referencia: float | None`, tolerancia absoluta en la unidad, relativa adimensional y escala opcional en esa unidad → un registro. Llama `_registro`/`_finito`; lo llaman los diagnosticadores. Calcula residuos y umbral de la tabla; ausencia → no evaluable, no finito o escala inválida → atención. `*` obliga a nombrar las opciones. Ejemplo: `_comparar('x','Balance','Caso','x=ref',2.,2.,'kJ/kg','Identidad',atol=1e-10)`. |
| `_margen(identificador, nombre, grupo, relacion, valor, limite, unidad, explicacion, *, estricto=True)` | Textos, `valor/limite: float | None` en la misma unidad, `estricto: bool` → registro de restricción. Llama `_registro`/`_finito`; lo llaman ciclo y Segunda Ley. Ausencia → no evaluable; margen/banda no representables o banda negativa → atención. Comprueba `valor>limite` o `valor>=−limite`. Ejemplo: `_margen('m','Calor','Caso','qin>banda',10.,1e-7,'kJ/kg','Interior motor')`. |
| `diagnosticar_ciclo(parametros, ciclo, modelo="noideal", contexto="Caso actual", segunda_ley=None, T0=None)` | Parámetros/ciclo anteriores, `modelo/contexto: str`, `segunda_ley: dict | None` **de un solo modelo** y `T0: float | None` [K] → `list[dict]` de controles. Llama helpers, `evaluar_punto` para bandas y `_diagnosticar_segunda_ley`. Lo llaman los coordinadores de `diagnostico_informe` y pruebas. `modelo` ajeno a ideal/noideal → `ValueError`; estados ausentes → controles no evaluables; `viable` sólo se compara como booleano auténtico, sin aceptar textos ni 0/1 como clasificación; límites físicos/numericos previstos al recuperar bandas se registran, errores inesperados propagan. Ejemplo: `diagnosticar_ciclo(PARAMETROS_PREDETERMINADOS, ciclo, modelo='ideal')`. |
| `_diagnosticar_segunda_ley(grupo, estudio, T0, cp, gamma, ciclo)` | `grupo: str`, `estudio: dict | None` de un modelo, `T0: float | None` [K], cp/gamma anteriores y `ciclo: dict` con trabajos si existen → `list[dict]` de entropías relativas, generación, signos, Gouy–Stodola, balance alternativo, suma parcial y límites globales. Llama `_registro`, `_comparar`, `_margen`, `_finito` y `math.log`; sólo lo llama `diagnosticar_ciclo`. Datos insuficientes → no evaluable; estado de límite/inconsistencia disponible → alerta; contrato estructural incorrecto propaga. Ejemplo interno: `_diagnosticar_segunda_ley('Ideal',estudio['modelos']['ideal'],288.15,1005.,1.4,ciclo_ideal)`. |
| `diagnosticar_optimizacion(parametros, estudio, modelo="noideal", objetivo="trabajo", contexto="")` | `parametros: dict`, `estudio: dict | None`, tres textos → `list[dict]` con clasificación y concordancia de resultados existentes. rp/η sin dimensión y W en kJ/kg. Llama `_registro`, `_comparar`, `_finito`; lo llaman `diagnostico_optimos` y `_items_muestra`. Modelo/objetivo desconocido → `ValueError`; datos de búsqueda ausentes → no evaluable, frontera/candidato inadmisible → atención. No llama optimizadores. Ejemplo: `diagnosticar_optimizacion(p, optimizaciones['noideal'],objetivo='trabajo')`. |

#### Contratos del alcance y agrupación — `diagnostico_informe.py`

Estas funciones conocen diccionarios y secuencias ya descritos en §§4.35–4.44, sin introducir ecuaciones ni cambiar sus unidades. Los errores de claves/tipos incorrectos se propagan; no se convierten en inviabilidad termodinámica. Las entradas se recorren o se copian; no se completan con datos de otra simulación.

| Firma completa | Argumentos, salida, llamadas, errores y ejemplo |
|---|---|
| `resumir_diagnosticos(items, alcance, agrupar=False)` | `items: iterable[dict]`, `alcance: str`, `agrupar: bool` → `dict` con `items: list`, `resumen: dict` de los tres estados y `alcance: str`. Sin unidades propias; conserva las de cada control. Copia registros, cuenta estados y agrupa por tupla `(grupo,id)`; usa `isfinite`, sin funciones propias. Lo llaman los cuatro coordinadores. Estado desconocido → `KeyError`; contratos numéricos de agrupación se presuponen. Ejemplo: `resumir_diagnosticos([], 'Sin datos')` devuelve tres contadores cero. |
| `diagnostico_simulacion(parametros, ideal, noideal, segunda_ley=None)` | Tres diccionarios y Segunda Ley opcional → resumen de los dos ciclos actuales. Extrae el bloque de cada modelo y T0; llama dos veces `diagnosticar_ciclo` y luego `resumir_diagnosticos`. Lo llama `crear_informe_html`. Ejemplo: `diagnostico_simulacion(p,ideal,noideal,estudio_sl)`. |
| `diagnostico_optimos(parametros, optimizaciones=None, estudio_rendimiento=None)` | Parámetros y dos estudios opcionales, todos `dict` → resumen de óptimos ideal/no ideal A/B y ciclos analíticos guardados. Llama `diagnosticar_optimizacion`, `diagnosticar_ciclo` si hay candidato y `resumir_diagnosticos`; lo llama `crear_informe_html`. Copia parámetros para usar la rp del candidato. Ejemplo: `diagnostico_optimos(p, optimizaciones, rendimientos)`. |
| `diagnostico_segunda_ley(parametros, estudio)` | Dos `dict`; estudio con T0/modelos → resumen de ambos modelos. Llama `diagnosticar_ciclo` sobre estados guardados y `resumir_diagnosticos`; lo llaman creadores normal y de Segunda Ley. Un trabajo ausente sigue ausente. Ejemplo: `diagnostico_segunda_ley(p,estudio_sl)`. |
| `_items_muestra(muestra, escenarios, ubicacion)` | `muestra: dict`, `escenarios: iterable[str]` R/A/B y `ubicacion: str` → **generador** que produce registros uno a uno, no lista. Llama diagnosticadores de ciclo/óptimo; lo llama `recorrer`. Mantiene parámetros/rp propios y contexto; R sin ciclo registra disponibilidad/motivos, sin inventar energías. Escenario/clave inválidos → `KeyError`. Ejemplo interno: `list(_items_muestra(muestra,'AB','T3=1600 K'))`. |
| `diagnostico_estudio(estudio, tipo)` | `estudio: dict`, `tipo: str` sensibilidad/mapa → resumen agrupado de todos los datos indicados en la tabla de modalidades. Llama el generador local `recorrer()` y `resumir_diagnosticos(...,agrupar=True)`; lo llaman los creadores OFAT/mapa. Otro tipo → `ValueError`. Ejemplo: `diagnostico_estudio(estudio_ofat,'sensibilidad')`. |
| `recorrer()` — local a `diagnostico_estudio` | Sin argumentos; captura `estudio`/`tipo` de su función contenedora → generador de registros. Recorre muestras o filas, evita repetir cortes con la misma T3 y usa `yield from _items_muestra(...)` / `diagnosticar_ciclo`. Sólo lo invoca el resumen al consumir su iterable; errores del estudio se propagan durante ese consumo. Ejemplo real de uso: `resumir_diagnosticos(recorrer(),alcance,agrupar=True)`. |

**PYTHON: `yield` y tuplas de agrupación.** Una función con `yield` produce un generador: entrega un elemento y conserva el punto del bucle para continuar cuando se pide otro. `yield from` entrega sucesivamente los elementos de otro generador. Así no hace falta acumular primero todos los controles del mapa para resumirlos. La tupla `(grupo,id)` es una clave de diccionario: agrupa la misma relación y contexto, sin confundir modelos. `{**parametros,'relacion_presiones':rp}` crea una copia con una clave sustituida; no cambia las entradas originales.

#### Presentación y funciones existentes que cambian

`renderizar_diagnostico(diagnostico, clave="actual")` recibe el `dict` agregado anterior y una `clave: str`; devuelve HTML `str` con resumen, grupos, tabla de cinco columnas y explicaciones nativas. No calcula física ni modifica el diccionario. Lo llaman los creadores de `reporting`; usa los helpers locales siguientes y `urllib.parse.quote` para prefijar identificadores únicos. Contratos de tipos mal formados propagan sus errores. Ejemplo mínimo:

```python
from diagnostico_html import renderizar_diagnostico
html = renderizar_diagnostico({
    'items': [],
    'resumen': {'cumple': 0, 'atencion': 0, 'no_evaluable': 0},
    'alcance': 'No hay resultados guardados en este contexto.'
})
```

Los tres helpers son funciones **locales** a ese renderizador y sólo están disponibles durante su ejecución: `texto(valor)` recibe cualquier valor representable y devuelve `html.escape(str(valor),quote=True)`; lo llaman el renderizador, `numero` y `magnitud`. `numero(valor)` recibe escalar/texto/`None` y devuelve `str` escapado; `None` se muestra como «No disponible», real no finito como «No disponible (no finito)» y real finito con `.6g`; llama `texto` e `isfinite`. `magnitud(valor, unidad)` recibe valor y unidad `str`, llama `numero`/`texto` y devuelve texto con unidad entre corchetes. No convierten unidades, no validan física ni tienen retorno numérico. Ejemplos internos: `texto('<T>')` → `&lt;T&gt;`, `numero(None)` → `No disponible`, `magnitud(1.5,'kJ/kg')` incorpora `1.5` y esa unidad. Una conversión `str` inválida o un contrato ajeno se propaga; el formato no redondea los datos empleados por el motor.

Los creadores `crear_informe_html`, `crear_informe_sensibilidad_html`, `crear_informe_mapa_html` y `crear_informe_segunda_ley_html` mantienen sus firmas públicas. Antes reunían los datos técnicos; ahora además llaman los coordinadores adecuados y el renderizador. La lista `comprobaciones` conserva los mensajes de controles previos de `main`: no se usa como fuente de residuos inventados ni como representación de V.1–V.5. Las tablas científicas nuevas provienen de los registros del motor.

`terminar_informe` añade el argumento de sólo nombre `diagnosticos=None`, un `dict` de panel→diagnóstico. Su firma completa actual figura en §4.41. Antes organizaba contenidos/KPI; ahora también conserva la información del panel en el HTML y metadata. `separar_presentacion` recupera esos bloques igual que los demás contenidos, sin ejecutar el motor al consultar el historial. El camino de descarga sigue devolviendo los bytes guardados. No se atribuyen controles nuevos a un informe antiguo sin ese bloque. La autonomía utiliza el CSS ya incrustado por `renderizar_dashboard`, sin recursos de red ni dependencia nueva.

Las filas tienen texto de estado además de color; los encabezados de tabla usan `scope="col"`. Todos los grupos y explicaciones comienzan plegados. El resumen visible de cada grupo muestra número de relaciones y los tres recuentos individuales; cuando las filas están agrupadas suma sus `conteos`, no confunde filas con muestras. Cada explicación muestra ecuación, interpretación, naturaleza, criterio, motivo, alcance y localización del ejemplo. Por debajo de 760 px la tabla se presenta como tarjetas con etiquetas por celda y el encabezado permanece en el DOM. `details`/`summary` funcionan sin JavaScript adicional; las gráficas y sus controles conservan su flujo.

#### Verificación y ejemplos reproducibles

Las comprobaciones ejecutadas para esta funcionalidad y sus límites se registran en el [milestone 18](docs/milestones/18_diagnostico_fisico.md) y en [§12 de la guía de aprendizaje activa](docs/milestones/11_verificacion_numerica_APRENDIZAJE.md). El **23/10/2026**, tras importar la copia ZIP sobre el commit remoto verificado en un directorio Linux independiente, el caso de integración antes pendiente pasó. El cierre focalizado obtuvo **20/20 pruebas físicas, 11/11 de integración, 101/101 regresiones relacionadas y 12/12 pruebas de contratos V.5**: **144 métodos distintos correctos**. Se corrigió exclusivamente la coerción de clasificaciones `viable` ausentes o de tipo incorrecto en el diagnóstico. El análisis estructural de HTML comprobó etiquetas `details`, identificadores/referencias accesibles y CSS móvil integrado; **no equivale a una inspección visual de escritorio o teléfono**. No se ha ejecutado la suite completa ni se ha podido acceder al directorio Windows. Los recuentos de V.1–V.5 anteriores mantienen su fecha/entorno y no se suman como si se hubieran vuelto a ejecutar en cada informe. El panel por sí solo no corrige la limitación V.5 sobre JSON manipulado (abordada posteriormente en §4.44); tampoco estima incertidumbre experimental ni introduce modelos de combustión o destrucción global de exergía.

### 4.57. Propiedades caloríficas variables del aire — `propiedades_aire.py` (Fase 2A)

**Alcance exacto.** Es un módulo autónomo sin importaciones desde `main.py`, `viabilidad.py`, `segunda_ley.py`, Flask o el dashboard; desde Fase 2B lo importa **únicamente** el nuevo `ciclo_cp_variable.py` y las pruebas. No reemplaza el modelo de `cp=1005 J/(kg·K)` y `gamma=1.4` del flujo histórico. Las pruebas tampoco validan un motor real. El [milestone técnico 19](docs/milestones/19_cp_variable_aire.md) y la [guía de aprendizaje independiente](docs/milestones/19_cp_variable_aire_APRENDIZAJE.md) desarrollan las hipótesis y los casos de prueba.

**INTERPRETACIÓN FÍSICA.** Aire seco de composición molar constante `0.78 N₂ + 0.21 O₂ + 0.01 Ar`, sin disociación ni cambio de especies; masa molar de mezcla `M=0.02896968 kg/mol`, constante específica `R_u/M≈287.005677 J/(kg·K)` y presión de referencia `p_ref=100 kPa=1 bar`. N₂ y O₂ emplean los coeficientes Shomate de NIST WebBook (N₂: 200–500 y 500–2000 K; O₂: 200–700 y 700–2000 K); argón monoatómico usa `cp,m=5 R_u/2`. NIST tabula `t=T/1000`, `cp,m=A+Bt+Ct²+Dt³+E/t²`, la primitiva de entalpía en kJ/mol y la de entropía en J/(mol·K). Las fracciones son **molares**, no másicas: primero se suma `Σ y_i propiedad_molar_i` y después se divide por `M` (y por `1000` si el retorno está en kJ/kg).

La referencia **relativa** es `h(298.15 K)=0` y `s0(298.15 K)=0`, en lugar de entalpía o entropía absolutas; el término constante de mezcla ideal desaparece al restar la referencia para una composición fija. Con p en kPa:

```text
cp(T)         = Σ y_i cp,m,i(T) / M                       [J/(kg K)]
h(T)          = [Σ y_i ∫(Tref→T) cp,m,i(u) du] / (1000 M) [kJ/kg]
s0(T)         = [Σ y_i ∫(Tref→T) cp,m,i(u)/u du] / (1000 M)
s(T,p)        = s0(T) − (R_u/(1000 M)) ln(p/100)          [kJ/(kg K)]
gamma(T)      = cp(T) / [cp(T) − R_u/M]                   [−]
T_desde_h(h)  = solución monótona de h(T) = h_objetivo   [K]
```

Las dos primitivas de NIST, ajustadas por separado a cada intervalo, pueden diferir ligeramente en el empalme. `_incremento_molar` integra desde `T_REF` hasta el límite con el primer polinomio y desde éste hasta T con el segundo, conservando **continuidad exacta de h y s0**. No obliga a que cp sea continua: los ajustes NIST pueden tener una discontinuidad pequeña en 500/700 K. No se extrapola fuera del intervalo cerrado 200–2000 K. `T_desde_h` usa bisección porque `dh/dT=cp/1000>0`; no requiere SciPy, derivadas numéricas ni una estimación inicial arbitraria.

**PYTHON: contratos públicos.** Todas reciben reales finitos (se rechazan `bool`, `None`, complejos, cadenas, NaN e infinitos) y plantean `ValueError` si el valor no pertenece al dominio. Las temperaturas se dan en K:

| Firma completa | Retorno y contrato | Llamadas y ejemplo |
|---|---|---|
| `cp(T)` | `float`, J/(kg·K), `200<=T<=2000` | `_temperatura`, `_coeficientes`, `_cp_shomate`; invocada desde `gamma`, las pruebas y usuarios de la API. `cp(300)` ≈ `1004.414` |
| `h(T)` | `float`, kJ/kg relativa a Tref; mismo intervalo | `_temperatura`, `_incremento_molar`, `_h_shomate`; invocada por `T_desde_h`. `h(1000)` ≈ `747.4853` |
| `s0(T)` | `float`, kJ/(kg·K) relativa a Tref a 1 bar | `_temperatura`, `_incremento_molar`, `_s_shomate`; invocada por `s`. `s0(1000)` ≈ `1.271674` |
| `s(T, p)` | `float`, kJ/(kg·K); `p` real finita y positiva en kPa | `_temperatura`, `_real_finito`, `s0`, `math.log`. `s(298.15, 100)==0`; p inválida → `ValueError` |
| `gamma(T)` | `float` adimensional, `cp/(cp−R_AIRE)` | `cp`; `gamma(300)` ≈ `1.400059`, no es `gamma` del ciclo actual |
| `T_desde_h(entalpia)` | `float` en K; entrada `h` en kJ/kg dentro de `[h(200),h(2000)]` | `_real_finito`, `h`, 80 iteraciones como máximo, parada por anchura `1e−10 K`; `T_desde_h(h(1000))` ≈ `1000` |

**PYTHON: auxiliares privados** (el guion bajo inicial comunica que no son API pública). ` _real_finito(valor)` recibe un objeto y devuelve `bool`, usa `numbers.Real` y `math.isfinite` con captura de excepciones numéricas para rechazar incluso enteros inmensos; lo llaman `_temperatura`, `s` y `T_desde_h`. `_temperatura(T)` devuelve `float` en K tras validar límites y llama `_real_finito`; lo llaman `cp`, `h`, `s0`, `s`. `_coeficientes(nombre, T)` recibe nombre `str` (`'N2'`/`'O2'`) y T en K, devuelve una tupla de ocho coeficientes y se usa en `cp` (un nombre no registrado produce `KeyError`). `_cp_shomate(T, c)` devuelve J/(mol·K), `_h_shomate(T, c)` devuelve J/mol y `_s_shomate(T, c)` devuelve J/(mol·K); todas reciben T en K y tupla Shomate, son fórmulas internas utilizadas desde `cp` o `_incremento_molar`. `_incremento_molar(nombre, T, primitiva)` recibe nombre y T válidos más una **función** de primitiva (h o s) y devuelve su diferencia molar desde Tref en las unidades de esa función; lo llaman `h` y `s0`. Estos auxiliares presuponen argumentos ya validados por la API pública y no aceptan nombres arbitrarios.

`_SHOMATE` es un diccionario de dos especies cuyos valores son tuplas `(límite, coeficientes_inferiores, coeficientes_superiores)`; `_ESPECIES` es una tupla de ternas `(nombre, fracción_molar, masa_molar)`. El `for nombre, y, _ in _ESPECIES[:2]` desempaqueta las ternas y descarta sólo la masa molar individual porque la conversión se realiza con `MASA_MOLAR` al final. `for _ in range(80)` denota una variable de bucle cuyo índice no se necesita. En `T_desde_h`, cada comparación conserva una de las dos mitades de `[inferior,superior]`; sus cotas finales garantizan error de temperatura pequeño, no exactitud experimental.

Ejemplo aislado, desde la raíz del proyecto, sin generar informes ni modificar ningún estado del ciclo:

```python
from propiedades_aire import cp, h, s0, s, gamma, T_desde_h
print(cp(300), gamma(300))        # aprox. 1004.414 J/(kg K), 1.400059
print(h(1000), s0(1000))          # aprox. 747.4853 kJ/kg, 1.271674 kJ/(kg K)
print(s(1000, 200))               # incluye el término de presión respecto a 100 kPa
print(T_desde_h(h(1000)))         # vuelve a 1000 K
```

**Verificación frente a validación.** `tests/test_propiedades_aire.py` contrasta cp en temperaturas representativas con valores fijados a partir de NIST, deriva numéricamente h y s0, integra por cuadratura independiente, inspecciona ambos empalmes, extremos, inversión y rechazo de errores. Son pruebas de fórmulas y consistencia del **modelo elegido**, no datos de rendimiento de un motor. La función `s0` no incluye una entropía absoluta de mezcla: sólo diferencias respecto al estado de referencia. Los estados y balances ya se calculan mediante un **solucionador independiente** (§4.58); su integración con optimizadores, sensibilidad, segunda ley histórica y HTML continúa pendiente.

### 4.58. Solucionador Brayton con cp(T) — `ciclo_cp_variable.py` (Fase 2B)

**Alcance y punto de entrada.** El nuevo `resolver_ciclo(T1, T3, rp, p1, eta_c=1.0, eta_t=1.0, delta=0.0, tolerancia=1e-10)` recibe dos temperaturas en K, relación de presión adimensional `rp=p2/p1`, presión en kPa, eficiencias `0<eta<=1`, pérdida fraccional `0<=delta<1` y tolerancia relativa. Devuelve un **diccionario** de números/tuplas y diagnósticos: no genera imágenes, no publica informes, no modifica `main.py` y actualmente lo invoca la capa web a través de `preparar_resultados`. Los parámetros históricos `cp` y `gamma` no aparecen en su firma ni en sus ecuaciones. Véanse [milestone técnico 20](docs/milestones/20_ciclo_cp_variable.md) y [aprendizaje 2B](docs/milestones/20_ciclo_cp_variable_APRENDIZAJE.md).

**INTERPRETACIÓN FÍSICA.** Aire seco ideal de composición molar **fija** según §4.57. Se ignoran cambios cinéticos/potenciales; compresor y turbina son adiabáticos; el «combustor» es sólo un aporte externo de calor al mismo aire. Para `R_kJ=R_AIRE/1000`, las presiones son `p2=rp·p1`, `p3=p2·(1-delta)`, `p4=p1`. En cada equipo se invierte una **diferencia de entropía térmica** para hallar la referencia isentrópica:

```text
s0(T2s) = s0(T1) + R_kJ · ln(rp)
s0(T4s) = s0(T3) + R_kJ · [ln(p4) − ln(p3)]
h2 = h1 + [h(T2s) − h1]/eta_c
h4 = h3 − eta_t · [h3 − h(T4s)]
T2 = T_desde_h(h2) ; T4 = T_desde_h(h4)
wc=h2−h1 ; wt=h3−h4 ; wn=wt−wc
qin=h3−h2 ; qout=h4−h1 ; residuo=wn−(qin−qout)
eta_th=wn/qin  (sólo motor válido)
```

Las diferencias de h están en kJ/kg; las de s en kJ/(kg·K). Las eficiencias usan **saltos de entalpía**, no cocientes de saltos de temperatura. Como `cp(T)` varía, la igualdad con `T2s=T1·rp^((gamma−1)/gamma)` o su equivalente para turbina **ya no es exacta**, y evaluar `gamma(T)` en una temperatura elegida no la arregla. El software reevalúa `h` en las temperaturas recuperadas para permitir inspeccionar residuos de inversión. `residuo_isentropico_compresor`, `residuo_isentropico_turbina` y `residuo_primera_ley` permiten verificar cada ecuación sin limitarse a mostrar trabajo neto.

**Segunda ley y no motores.** `entropias` es `(s1,s2,s3,s4)` calculado con cada `(Ti,pi)`. Para equipos adiabáticos `generacion_entropia_compresor=s2−s1` y `generacion_entropia_turbina=s4−s3`; en compresión/expansión normales deben ser no negativas (con tolerancia numérica). **No** son la generación total de la instalación ni un balance del aporte de calor. `viable=True` sólo si hay compresión (`rp>1`), expansión (`p3>p4`), `qin>0`, `wn>0` y ningún resultado de generación significativamente negativo; los umbrales usan `tolerancia` para presión/energía y un suelo `1e−11 kJ/(kg·K)` para redondeos entrópicos. La lista `motivos` identifica las restricciones incumplidas; `rendimiento` y `back_work_ratio` son `None` fuera del régimen motor. **No** se recortan valores calculados ni se convierte un trabajo negativo en cero. Con relaciones de presión opuestas a la dirección nominal, las fórmulas de eficiencia pueden incluso dar entropía generada negativa: se registra `segunda_ley_compresor`/`segunda_ley_turbina` como motivo y **no** se presenta ese ciclo como físicamente válido.

**Distinguir errores.** Las entradas no finitas, booleanas, no reales, relaciones/presiones no positivas, eficiencias o pérdidas fuera de límites, temperaturas de entrada fuera de `[200,2000]` y tolerancias inválidas producen `ValueError` **antes de calcular**. `EstadoFueraDeRango(ValueError)` señala que **las entradas son admisibles pero** algún estado isentrópico o real exigiría una temperatura fuera de 200–2000 K; no se extrapola Shomate. `ErrorNumericoCiclo(ArithmeticError)` indica presiones/entalpías intermedias no representables o ausencia de convergencia, sin etiquetar el caso de «no motor». Un ciclo que puede calcularse pero no entrega trabajo motor devuelve normalmente su diccionario con `viable=False` y sus motivos, no una excepción.

**PYTHON — funciones reales y llamadas.** Las dos clases de excepción nuevas no cambian las del motor histórico. La API del módulo tiene cinco funciones:

| Firma completa | Entrada, retorno y papel | Llamadas, límites y errores |
|---|---|---|
| `_numero_finito(valor)` | Objeto → `bool`; filtro sin unidades | `numbers.Real`, `math.isfinite`; rechaza `bool` y `OverflowError`; llamada por `_validar_entradas`. Ej.: `_numero_finito(True)==False`. |
| `_validar_entradas(T1, T3, rp, p1, eta_c, eta_t, delta, tolerancia)` | Escalares reales en K, kPa y adimensionales → `None` | Llama a `_numero_finito`; `ValueError` si falla cualquier dominio. Invocada por `resolver_ciclo`. Ej.: `_validar_entradas(300,1600,10,100,.85,.9,.05,1e-10)` no devuelve datos. |
| `_temperatura_desde_s0(objetivo)` | Entropía térmica relativa en kJ/(kg·K) → temperatura `float` en K | `s0(200)`, `s0(2000)`, `s0(medio)`; bisección acotada (máx. 80, anchura `1e−10 K`). `EstadoFueraDeRango` sin raíz, `ErrorNumericoCiclo` al no converger. La llama `resolver_ciclo`. Ej.: `_temperatura_desde_s0(s0(500))≈500`. |
| `_temperatura_desde_h_acotada(entalpia)` | Entalpía relativa kJ/kg → temperatura `float` K | `h(200)`, `h(2000)`, `T_desde_h`; convierte una meta fuera de rango en `EstadoFueraDeRango`. La llama `resolver_ciclo`. Ej.: `_temperatura_desde_h_acotada(h(1000))≈1000`. |
| `resolver_ciclo(T1, T3, rp, p1, eta_c=1.0, eta_t=1.0, delta=0.0, tolerancia=1e-10)` | K, K, –, kPa, –, –, –, – → `dict` con cuatro estados, referencias isentrópicas, h, s, trabajos, calores, residuos, viabilidad y motivos | Llama a todos los validadores/inversores y a `h`, `s0`, `s`, `T_desde_h` de Fase 2A, `math.log`; la invocan las pruebas o el usuario en Python. No recibe cp/gamma. Puede devolver `viable=False` o elevar los errores diferenciados anteriores. |

El `dict` contiene las tuplas `temperaturas=(T1,T2,T3,T4)` K, `presiones=(p1,p2,p3,p4)` kPa, `entalpias=(h1,h2,h3,h4)` kJ/kg, `entalpias_isentropicas=(h2s,h4s)` kJ/kg, `entropias=(s1,s2,s3,s4)` kJ/(kg·K), `T2s`/`T4s` K; seis magnitudes energéticas (`trabajo_compresor`, `trabajo_turbina`, `trabajo_neto`, `calor_aportado`, `calor_rechazado`, `residuo_primera_ley`); `rendimiento` y `back_work_ratio` como fracciones adimensionales o `None`; generación/residuos entrópicos en kJ/(kg·K); `motivos` como tupla de códigos; `margenes` y `tolerancias` como diccionarios para auditar la clasificación.

El código `for _ in range(80)` representa un bucle de búsqueda donde el índice no importa. `raise EstadoFueraDeRango(...)` distingue la imposibilidad de permanecer en el dominio NIST de una inviabilidad motora. `tuple(clave for clave, margen in margenes.items() if ...)` es una **expresión generadora** consumida por `tuple`, que recoge todos los motivos simultáneos sin ocultar sus valores. La condición `wnet/qin if viable else None` evita dividir en un punto no motor. Las presiones se logaritman como diferencias `log(p4)-log(p3)` sin dividir presiones extremas, y las temperaturas se devuelven como `float`, no listas de NumPy.

Ejemplo directo, desde la raíz del repositorio:

```python
from ciclo_cp_variable import resolver_ciclo
punto = resolver_ciclo(288.15, 1600, 10, 100, .85, .9, .05)
print(punto["temperaturas"])  # 288.15, 597.692837, 1600, 993.581041 K
print(punto["trabajo_neto"])  # 402.070798 kJ/kg
print(punto["rendimiento"])    # 0.348934281, NO porcentaje
```

**Comparación de referencia a `rp=10`.** Con `eta_c=.85`, `eta_t=.9`, `delta=.05`, el modelo variable entrega `wn≈402.070798 kJ/kg` y `eta≈34.893428 %`; el modelo histórico con `cp=1005`, `gamma=1.4` entrega `wn≈369.476301 kJ/kg` y `eta≈36.898732 %`. En condiciones reversibles sin pérdida (`eta_c=eta_t=1`, `delta=0`), los valores respectivos son `542.818426 kJ/kg; 45.245515 %` y `505.619018 kJ/kg; 48.205253 %`. Estas diferencias se deben a **modelos térmicos distintos**, no a un cambio de los resultados HTML.

**Verificación.** `tests/test_ciclo_cp_variable.py` comprueba isentrópicas también con cuadratura independiente de `cp(T)/T` y bisección propia del test (sin llamar a `s0`), reproduce saltos de h por integración independiente de `cp`, revisa eficiencias, balances, entropías, reversibilidad, viabilidad y límites. No compara prestaciones con mediciones de turbinas reales. El registro de ejecución y las limitaciones del entorno quedan en los documentos de milestone y aprendizaje de Fase 2B.

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
| `from math import isfinite, log`, `from numbers import Real` — `propiedades_aire.py` | Estándar | Shomate, integración analítica, logaritmos estables, control estricto de tipos y bisección |
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

`sensibilidad.py` reutiliza NumPy/Matplotlib y añade `perf_counter` (biblioteca estándar) para medir cálculo, sin dibujo. Importa dominios, evaluador y candidatos de las fases previas. Los imports de `reporting` dentro de `ejecutar_sensibilidad` se resuelven al llamar, sin ejecutar informes al importar. No se añade ninguna dependencia.

### Imports de Flask

`from flask import Flask, Response, abort, request, url_for, render_template` incorpora aplicación, respuesta HTTP, errores, petición, URL y renderización directa de la plantilla específica del turborreactor. El dashboard histórico/cp(T) sigue renderizándose en `dashboard.renderizar_dashboard` sin cambiar su contrato.

`web_app.py` importa los presentadores de `cp_variable_web`, el nuevo adaptador `turborreactor_web` y las excepciones del solucionador cp(T). Los módulos históricos se usan en otras rutas de terminal y reporting; Flask no ejecuta cálculos antiguos desde `/`. La ruta `/turborreactor` sí invoca el módulo científico M37 **por medio** de `turborreactor_web` después de POST válido, sin duplicar sus ecuaciones. Nunca recalcula un informe histórico con el turborreactor.

### Imports de las pruebas

`unittest` aporta pruebas y aserciones; `unittest.mock.patch` sustituye temporalmente operaciones para simular fallos; `tempfile` aísla archivos; `redirect_stdout` y `StringIO` capturan terminal; `HTMLParser` inspecciona etiquetas; `b64decode` comprueba la codificación; `sha256` compara los PNG históricos; `matplotlib.image` decodifica imágenes. También se importan fechas, zona UTC, rutas y bytes en memoria, y los módulos propios `main` y `reporting`.

Las pruebas de raíces incorporan `sqrt` de `math` para la fórmula cuadrática, y reutilizan `unittest` y `subTest`; no requieren bibliotecas adicionales. `test_comparacion_scipy.py` añade `exp`, `log`, `isfinite`, `sqrt` y `SimpleNamespace` de la biblioteca estándar, y sólo intenta importar `scipy.optimize` dentro de un `try/except ImportError` opcional; `unittest.skipIf` registra las seis comparaciones omitidas cuando falta SciPy. Estas herramientas verifican implementación, almacenamiento y rutas HTTP, no datos experimentales del modelo.

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
GET / → valores_formulario (7 valores) → renderizar_dashboard(modo_cp=True)
POST / → request.form → leer_entradas → preparar_resultados
                                      ├─ resolver_ciclo (Fase 2B)
                                      ├─ estudiar_cp_variable (Fase 2C)
                                      ├─ propiedades_estados y SVG
                                      ├─ error esperado → formulario + 400
                                      └─ éxito → HTML con Resultados y Optimización + 200
POST / con acción antigua → aviso no adaptada + 400, sin cálculo
GET /informes/nombre → consulta de HTML histórico de gas perfecto, solo lectura
```

`float(texto)` convierte un número escrito; `.strip()` quita espacios y `isfinite` rechaza NaN/infinitos. En el formulario actual, la pérdida `delta=0.05` significa 5 %: **no se introduce 5**. Las eficiencias también se introducen como fracciones. Este contrato es distinto del antiguo formulario de nueve campos.

El POST actual devuelve directamente 200 y muestra los resultados de cp(T); **no genera ni redirige a un nuevo informe**. Las rutas `/informes/<nombre>` siguen aceptando únicamente nombres con el patrón y las marcas del sistema histórico para su consulta y descarga. Si no existe, devuelven 404. Recargar un POST puede solicitar su reenvío al navegador, pero no provoca escrituras al historial.

Los archivos históricos conservan los enlaces de consulta/descarga y siguen funcionando sin conexión. En el formulario actual, «Restablecer valores» es un enlace GET que carga los siete predeterminados. No hay botón para guardar informes nuevos desde cp(T).

El servidor se enlaza exclusivamente a `127.0.0.1`. Con `debug=False` no se ofrece depurador interactivo; `use_reloader=False` evita procesos de recarga y `threaded=False` procesa una petición cada vez. Durante una simulación otras peticiones esperan. No es una cola de trabajos ni un servidor de producción. Una ejecución de terminal en otro proceso aún puede coincidir con Flask: no se añade bloqueo entre procesos en esta tarea.

### Plantilla Jinja, campos HTML y CSS

`templates/index.html` es la plantilla compartida por el dashboard Flask y los informes autónomos. La renderiza Jinja tanto desde Flask como desde la presentación sin servidor. Flask/Jinja sustituye `{{ valores.get(nombre, '') }}` por texto escapado; `{% for ... %}`, `{% if ... %}` y `{% set ... %}` controlan repetición, condiciones y asignación en la plantilla. Estas expresiones no se ejecutan en el navegador: Python renderiza el resultado antes de enviarlo. No deben confundirse con las llaves de las f-strings ni de CSS.

`<form method="post" action="...">` define destino y método; el atributo `name` de cada `<input>` será la clave de `request.form`. `label for` y `id` enlazan etiqueta y campo. `type="number"`, `step="any"`, `required`, `min` y `max` ayudan en el navegador, pero no sustituyen el servidor; límites estrictos como mayor que cero o pérdida menor que 100 se comprueban en Python. Los mensajes muestran además el valor recibido para conservar información incluso si un control numérico no puede representar texto inválido.

`fieldset` y `legend` agrupan Condiciones de entrada (T1/T3/p1), Propiedades del fluido (cp/gamma) y Configuración y pérdidas (rp/eta_c/eta_t/delta). El control OFAT está en la sección Sensibilidad del mismo formulario, sin duplicar las nueve entradas físicas. `aria-describedby`, `aria-invalid` y `role="alert"` relacionan ayudas y errores para accesibilidad. El CSS local usa una cuadrícula de dos columnas, que pasa a una en pantallas estrechas. `url_for('static', filename='style.css')` construye la URL del CSS; este recurso sirve solo al formulario. El informe no depende de él.

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

1. Se crea `app` de Flask con las rutas `/`, `/informes/<nombre>` y `/documentacion/<nombre>`; sin Blueprint alternativo.
2. `iniciar_servidor()` escucha en 127.0.0.1:5000, con depurador y recarga desactivados.
3. GET `/` obtiene las siete entradas de `DEFAULTS`. Jinja renderiza `templates/index.html`, adaptada a cp(T).
4. POST con acción `normal` o `optimizar` llama al lector finito y después al solucionador 2B y optimizador 2C. Se muestran balances, propiedades, SVG y óptimos dentro de Resultados y Optimización. La acción solo determina el panel inicial.
5. Sensibilidad, mapa y segunda ley muestran una explicación de próxima adaptación y no invocan los módulos antiguos. No se generan archivos ni una redirección 303.
6. GET `/informes/<nombre>` solo consulta informes históricos. Los errores físicos esperados devuelven 400 y los inesperados 500; el servidor sigue activo.

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

El código usa el vértice `centro=(1+h)/2` como punto interior negativo y las cotas Q(0)=Q(1+h)=hk>0 para acotar ambas raíces mediante bisección. El vértice sólo acota raíces de Q; no se usa como óptimo de trabajo no ideal. La fórmula de x_± permite un contraste analítico independiente, ejecutado para casos moderados en `tests/test_verificacion_raices.py` (§4.46). El criterio de parada es relativo en x (1e−12) y tiene 100 iteraciones como máximo. Las fronteras de rp se obtienen elevando x a 1/a. Si las escalas dejan de ser representables, se informa de límite numérico y no de ausencia física de motor.

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

Los módulos independientes de propiedades variables (Fase 2A, §4.57) y solucionador de cuatro estados (Fase 2B, §4.58) ya existen; **integrarlos en los optimizadores, análisis, informes y ejecución histórica** es trabajo posterior. Esta sección describe únicamente mejoras todavía pendientes.

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
8. **Revisar unidades y energía.** Calcula en una función nueva de práctica el calor rechazado `cp*(T4−T1)/1000`, como magnitud positiva. Contrasta `qin−qout` con el trabajo neto del balance utilizando tolerancias. Las funciones de ciclo no devuelven una clave `qout`; el diagnóstico ya lo reconstruye expresamente de las temperaturas para su fila de Primera Ley (§4.56).
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

### 4.59. Fase 2C — Viabilidad y optimización independiente con cp(T)

**PYTHON:** `optimizacion_cp_variable.py` importa `resolver_ciclo` de 2B y `h`, `s0`, `T_desde_h` de 2A. Actualmente lo llama `preparar_resultados` desde el dashboard Flask; los módulos `main.py`, sensibilidad, mapa y los informes históricos no lo llaman. La entrada pública `estudiar_cp_variable(T1,T3,p1=100.,eta_c=.85,eta_t=.9,delta=.05,*,tolerancia=1e-9,muestras=160)` recibe K, kPa, fracciones e integer para el tamaño de muestra, y devuelve `dict` con `dominio_motor=(rp_min,rp_max)` abierto, `A` y `B`, o campos `None` y `tipo='sin_motor'`. La búsqueda de A y B utiliza raíces de derivadas y `_raiz_monotona` (bisección), tras comprobar los signos en fronteras. `_maximo_acotado` queda sólo como auxiliar disponible para pruebas comparativas. Si una derivada no cambia de signo y el mejor valor corresponde a una frontera abierta, se informa de `supremo_frontera` y se deja `rp=None`. Ambos auxiliares reciben una función Python como argumento y cota inferior/superior reales; fallan con `ValueError` cuando no existe bracket y `ArithmeticError` por falta de convergencia. El auxiliar `_real_positivo(x)` comprueba reales finitos, sin permitir booleanos; es auxiliar de apoyo.

**INTERPRETACIÓN FÍSICA:** la viabilidad exige compresión, expansión efectiva, temperaturas 200–2000 K, `q_in>0`, `q_out>0`, trabajo neto positivo y coherencia de Segunda Ley en compresor/turbina. La cota inferior está en `rp>1/(1-delta)`. Las cotas superiores se obtienen de temperaturas por entropía y entalpía, no de fórmulas de gamma constante. `w_neto` es cóncavo respecto a `x=ln rp`, pues `dw/dx=R_kJ*(eta_t*T4s-T2s/eta_c)` es estrictamente decreciente. Para el rendimiento, el signo de `d eta/dx` coincide con `F=b*q_in-a*q_out`, con `a=R_kJ*T2s/eta_c`, `b=R_kJ*eta_t*T4s`; `F' < 0` mientras `q_in,q_out>0`. Por tanto hay a lo sumo un máximo interior alcanzado; si no, se informa de supremo en frontera excluida.

Ejemplo: `estudiar_cp_variable(288.15,1600)` retorna dominio aproximado `(1.069645,229.221073)`, `rp_A≈15.87795`, `w_A≈414.08583 kJ/kg`, `rp_B≈46.81910` y `eta_B≈0.43745`. Véanse el [milestone 21](docs/milestones/21_optimizacion_cp_variable.md) y [aprendizaje 21](docs/milestones/21_optimizacion_cp_variable_APRENDIZAJE.md). Las 13/13 pruebas específicas se ejecutaron con los archivos auténticos de 2A/2B, acreditados por sus hashes Git. La suite web histórica no se ha ejecutado. Ninguna comparación constituye validación experimental.

### 4.60. Primera interfaz cp(T) — Fase 2D (referencia histórica)

La Fase 2D introdujo temporalmente una ruta y plantilla independiente para cp(T), ver [milestone 22](docs/milestones/22_integracion_web_cp_variable.md). En esa versión se verificaron 32 pruebas web mediante Actions. **La ruta /modelo-cp-variable, su Blueprint y la plantilla secundaria fueron retirados en el milestone 23**. Los algoritmos y presentadores físicos de aquella fase sí se conservan; el resultado histórico de sus pruebas no se presenta como una prueba del código actual.

### 4.61. Unificación del dashboard principal con cp(T) — milestone 23

**PYTHON — flujo.** `web_app.index()` sigue registrado en GET/POST `/`. GET llama a `valores_formulario()` y devuelve siete valores desde `cp_variable_web.DEFAULTS`. POST recibe exactamente `T1, T3, rp, p1, eta_c, eta_t, delta`: las temperaturas se introducen en K, p1 en kPa, rp sin dimensión, eficiencias y delta en fracciones. `leer_entradas(form)` convierte cadenas a números finitos; luego `preparar_resultados(entradas)` reutiliza 2B/2C. Las acciones `normal` y `optimizar` muestran el resultado en su sección correspondiente; Sensibilidad, Mapa y Segunda ley se activaron progresivamente en §4.62–§4.64, siempre sin ejecutar modelos antiguos. Los errores físicos y numéricos se muestran diferenciados. El servidor conserva `127.0.0.1:5000` y el mismo lanzador.

**Firmas y contrato de las funciones modificadas:**

- `valores_formulario() -> dict`: sin argumentos, entrega copia de siete valores (K, kPa, fracciones). La usan index y el manejador HTTP 500. No contiene cp ni gamma constantes. Ejemplo: `valores_formulario()['delta'] == 0.05`.
- `leer_entradas(form) -> dict[str,float]`: objeto formulario con siete campos, devuelve escalares reales finitos; `ValueError` para ausencias, no numéricos, NaN o infinitos. La llama `index`. Ejemplo: `leer_entradas({'T1':'288.15','T3':'1600','rp':'10','p1':'100','eta_c':'.85','eta_t':'.9','delta':'.05'})`.
- `preparar_resultados(entradas) -> dict`: recibe esos siete `float` y devuelve `ciclo` (2B), `estados` (cuatro propiedades T, p, cp, gamma, h, s), `graficas_resultados` (seis tuplas de título/SVG o None/explicación), `diagnostico_comparacion` (texto), `optimizacion` (2C) y `graficas_optimizacion` (tres tuplas, o vacío sin dominio motor). Resuelve una vez el caso, una vez el estudio A/B y el barrido de 90 relaciones de compresión; la presentación de Resultados resuelve además un caso ideal de componentes con el **mismo** cp(T) y las mismas T1, T3, rp y p1, sin alterar las bibliotecas científicas. Propaga los errores del caso principal, pero una comparación ideal fuera de rango se transforma en diagnóstico local. Ejemplo: `preparar_resultados({'T1':288.15,'T3':1600.,'rp':10.,'p1':100.,'eta_c':.85,'eta_t':.9,'delta':.05})['ciclo']['trabajo_neto'] ≈ 402.071`.
- `index()` recibe `flask.request` implícitamente, devuelve HTML y código 200/400. `@app.route` es un decorador que registra esta función; el código se ejecuta al recibir una petición y no genera un informe HTML guardado.
- `dashboard.renderizar_dashboard(valores, *, contenidos=None, metadata=None, informes=(), errores=None, modo_local=True, informe_actual='', seccion_inicial='simulacion', modo_cp=False, cp_datos=None, campos_cp=()) -> str`: nueva bandera `modo_cp`, diccionario `cp_datos` y tupla `campos_cp`. Con `modo_cp=True` renderiza la interfaz activa. Por defecto conserva el contenido de informes históricos con propiedades constantes. Jinja evalúa `{% if modo_cp %}` en Python antes de transmitir HTML; el JavaScript sigue ocupándose solo de navegación, pestañas y ampliación de imágenes. Lo llaman `index`, `error_interno` y los presentadores de informes.
- Los presentadores `propiedades_estados(p)`, `_escala(valor, low, high, inicio, ancho)` y `curvas_optimizacion(entradas, estudio, muestras=90)` siguen en `cp_variable_web.py` con sus firmas del hito 22. `svg_ts` se trasladó a `graficas_cp_variable.py` y ahora presenta ejes numéricos; la antigua gráfica única `svg_optimizacion` se sustituyó por tres SVG separados. Véase §4.67 para sus firmas y límites. La plantilla no calcula ninguna propiedad.

**INTERPRETACIÓN FÍSICA.** El panel Simulación utiliza siete parámetros; Resultados contiene T1–T4 y T2s/T4s [K], p1–p4 [kPa], trabajo de compresor y turbina, trabajo neto, calor entrante/saliente [kJ/kg], rendimiento [%] únicamente si el ciclo es motor, cp(T) [J/(kg K)], gamma(T), h [kJ/kg] y s [kJ/(kg K)]. El T–s representa estados calculados y segmentos esquemáticos. Optimización entrega máximos independientes A/B y distingue punto interior alcanzable de supremo en frontera excluida. Ejemplo: para T1=288.15 K, T3=1600 K, rp=10, p1=100 kPa, eta_c=.85, eta_t=.9, delta=.05, wneto≈402.071 kJ/kg y rendimiento≈34.893 %. A tiene rp≈15.878 y trabajo máximo≈414.086 kJ/kg; B, rp≈46.819 y rendimiento máximo≈43.745 %. No son resultados experimentales.

**Compatibilidad y estado de aquel hito.** `templates/index.html` mantuvo la disposición y navegación original de ocho secciones y la presentación IBM Plex. `templates/cp_variable.html` fue eliminada después de verificar la nueva interfaz; no hay selector ni ruta alternativa. En el hito 23, Sensibilidad, Mapa de diseño y Segunda ley permanecían pendientes; se recuperaron en §4.62, §4.63 y §4.64 respectivamente. El panel Informes identifica los HTML anteriores como **gas perfecto histórico** y los deja consultar o descargar sin recalcular; no los atribuye a cp(T). `main.py` todavía permite ejecutar el simulador antiguo directamente en Python, pero no desde el formulario de Flask. Solo hay una página HTML de cálculo activa.

**Pruebas.** Se usan `tests/test_cp_variable_web.py`, `tests/test_web_app.py` y `tests/test_dashboard.py` en GitHub Actions. Comprueban integración científica, gráficos, entradas y fallos, rutas, archivo histórico y navegación. Véanse [milestone técnico 23](docs/milestones/23_unificacion_dashboard_cp_variable.md) y [guía 23](docs/milestones/23_unificacion_dashboard_cp_variable_APRENDIZAJE.md) para resultados efectivos y limitaciones.

### 4.62. Sensibilidad OFAT cp(T) — milestone 24 (Fase 2E)

**Ingeniería.** Un estudio *one factor at a time* conserva seis de las siete entradas (`T1`, `T3`, `rp`, `p1`, `eta_c`, `eta_t`, `delta`) y varía la séptima sobre una malla lineal. En cada muestra se llama a **exactamente el mismo** `resolver_ciclo(**entradas)` de 2B: no se ha creado una ecuación paralela para cp(T), h o s. Trabajo del compresor/turbina, trabajo neto, calor entrante, rendimiento, T2 y T4 proceden de ese retorno. El residuo de primera ley se conserva para comprobar la identidad \(w_t-w_c=q_{in}-q_{out}\). Estado calculable no motor no implica prestación válida, aunque el balance siga teniendo sentido.

**Cálculo `sensibilidad_cp_variable.py`.**

- `PARAMETROS_CP` es un diccionario que asocia siete claves a etiquetas, unidades y **rangos iniciales sugeridos**. Los límites editables no garantizan viabilidad.
- `_evaluar(entradas) -> dict`: retorna `estado` (`motor`, `no_motor`, `fuera_rango`, `entrada_invalida` o `error_numerico`), `motivo` y `ciclo` si el cálculo es representable. Captura `EstadoFueraDeRango` **antes** que `ValueError`, por ser su subclase. No confunde dominio no motor con fallo numérico.
- `barrido_cp_variable(entradas, parametro, minimo, maximo, muestras=41) -> dict`: siete valores físicos, parámetro elegido, dos números finitos ordenados y entero de 3 a 201. La malla incluye ambos extremos. La lista `filas` mantiene los huecos, incluso si ninguna prestación es representable; `magnitudes` conserva diagnósticos calculables y `operativas` solo se rellena cuando el ciclo es motor. También devuelve `conteos`, referencia y sensibilidades locales. `ValueError` ante configuración inválida. Ejemplo: `barrido_cp_variable(DEFAULTS,'p1',80,120,9)` produce nueve ciclos motores con el mismo trabajo y rendimiento dentro de la precisión numérica, aunque cambian las presiones absolutas y las entropías con referencia a presión.
- `sensibilidad_local(entradas, parametro, paso_relativo=1e-3) -> dict`: calcula \(S_x^Y=(x/Y)\,dY/dx\) para `trabajo_neto` y `rendimiento`. Diferencia central si ambos vecinos son motores; unilateral si un vecino no pertenece al dominio. Compara las estimaciones con paso `h` y `h/2` (tolerancia 5 % relativa y 1e-4 absoluta para la elasticidad). Si x=0, Y≈0, el base no es motor, faltan vecinos o los pasos no son coherentes, declara la estimación no disponible/inestable en lugar de publicar un número. Es una **aproximación numérica local**, no una derivada analítica ni una validación experimental.

**Presentación y Flask.** `preparar_sensibilidad(entradas,parametro,minimo,maximo,muestras)` añade al barrido tres SVG mediante `svg_sensibilidad(barrido,claves,etiqueta,unidad_y)`: trabajo neto [kJ/kg], rendimiento [%], trabajo del compresor/turbina [kJ/kg]. El trazador cierra cada tramo al encontrar una fila no motora o sin resultado; una línea vertical discontinua indica el valor de referencia cuando está dentro del intervalo. El controlador `web_app.index()` acepta `accion='sensibilidad'`, lee siete números desde el formulario habitual y cuatro campos `sens_cp_*`; muestra errores con HTTP 400 y retorna a la sección Sensibilidad. No llama al optimizador 2C en este análisis; **rp permanece fija** salvo si el usuario la escoge como factor. `dashboard.renderizar_dashboard(...,sens_datos=None,sens_config=None,sens_parametros=None)` inyecta esos datos a la rama `modo_cp` existente de `templates/index.html`. El JS únicamente actualiza el rango sugerido al seleccionar otro factor; no ejecuta termodinámica. El mapa de diseño y la Segunda ley se incorporan en §4.63 y §4.64.

**Ejemplo reproducible.** Con `cp_variable_web.DEFAULTS` (288.15 K, 1600 K, rp=10, p1=100 kPa, ηc=.85, ηt=.9, δ=.05), el base proporciona 402.070798 kJ/kg y η=34.893428 %. Para un barrido T3=1200–1750 K con 41 muestras, las 41 son motoras: `sensibilidad_local(DEFAULTS,'T3')` da aproximadamente `S_T3^w=1.848248` y `S_T3^η=0.154523`, usando diferencias centrales con paso reducido. Estos valores son **elasticidades**: aproximadamente +1 % en T3 predice +1.85 % en trabajo específico cerca de este caso; no significa +1.85 puntos porcentuales de rendimiento. Para `p1`, ambas elasticidades son ≈0: el aire ideal no introduce una dependencia de entalpías con la presión absoluta, a T y relaciones de presiones fijas. Un barrido de rp distingue aumento inicial de trabajo, máximo cercano a 15.878, y máximo de rendimiento cercano a 46.819 (calculados en 2C, no optimizados por la malla OFAT).

**Aprendizaje y pruebas.** Leer [milestone técnico 24](docs/milestones/24_sensibilidad_cp_variable.md) y [aprendizaje 24](docs/milestones/24_sensibilidad_cp_variable_APRENDIZAJE.md). Los tests `test_sensibilidad_cp_variable.py` (10 métodos) y `test_sensibilidad_cp_web.py` (6) contrastan directamente 2B, clasificación, tolerancias, fronteras, estados no motores, gráficos y errores Flask. El workflow existente incorpora estos métodos sin ejecutar de nuevo toda la verificación científica de 2A/2B/2C. La cobertura y resultado definitivos de CI se confirman por separado, sin atribuirlos a este texto.

#### Ampliación visual de Sensibilidad (milestone 31)

**PYTHON.** \`preparar_sensibilidad(entradas, parametro, minimo, maximo, muestras)\` sigue ejecutando una sola vez \`barrido_cp_variable\` y agrega cinco gráficos en \`graficas\`. El módulo \`graficas_sensibilidad_cp.py\` reutiliza los registros \`filas\` y el \`referencia.ciclo\`: \`svg_variaciones_relativas(estudio)\` devuelve \`(svg, diagnóstico)\` y \`svg_temperaturas_caracteristicas(estudio)\` devuelve SVG o \`None\`. El auxiliar \`_svg_dos_series(filas, etiqueta_x, unidad_x, claves, etiqueta_y, unidad_y, x_ref=None)\` transforma parejas físicas en puntos SVG sin resolver ciclos; \`None\` corta las polilíneas. Los círculos contienen \`data-x\` y \`data-valor\` para pruebas. El HTML muestra un diagnóstico cuando la comparación relativa es singular.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Las variaciones finitas \`100(x−x0)/x0\`, \`100(W−W0)/W0\` y \`100(η−η0)/η0\` no son la sensibilidad local \`S=(x/Y)dY/dx\`. Si \`x0=0\`, el caso base no es motor o las prestaciones base son nulas, no se normaliza ni se inventan porcentajes. El gráfico adicional de temperaturas T2/T4 [K] muestra solo muestras motoras calculadas por 2B; un hueco no representa una temperatura de cero. Ver [milestone técnico 31](docs/milestones/31_graficas_sensibilidad_cp.md) y [aprendizaje](docs/milestones/31_graficas_sensibilidad_cp_APRENDIZAJE.md).


### 4.63. Mapas de diseño rp–T3 con cp(T) — milestone 25 (Fase 2F)

**INGENIERÍA — dos entradas que cambian a la vez.** En una malla bidimensional, cada pareja \((r_p,T_3)\) representa un ciclo independiente. Mantenemos fijas `T1` [K], `p1` [kPa], `eta_c`, `eta_t` y `delta` [fracciones]. Las otras dos entradas del formulario son `rp` [−] y `T3` [K], pero su valor de referencia no limita el barrido; la T3 del formulario sirve también para comparar una única condición con 2C. En todas las celdas se llama a `resolver_ciclo(**entradas)` de 2B, que aplica los mismos balances: \(w_\mathrm{neto}=w_t-w_c=q_\mathrm{in}-q_\mathrm{out}\), con entalpías \(h(T)\) y ecuaciones de entropía ya verificadas. El rendimiento \(\eta=w_\mathrm{neto}/q_\mathrm{in}\) se representa como prestación **solo** cuando `viable=True`.

**PYTHON — funciones de `mapa_diseno_cp_variable.py`:**

- `DEFAULT_MAPA: dict` reúne rangos sugeridos `rp_min=1.1`, `rp_max=80`, `T3_min=1200`, `T3_max=1800`, `n_rp=n_T3=31`. `MAX_PUNTOS_EJE=51` limita a 2601 las celdas; es un límite de interfaz y coste, no una ley física.
- `_configuracion_valida(entradas: dict, rp_min: float, rp_max: float, T3_min: float, T3_max: float, n_rp: int, n_T3: int) -> None`: comprueba claves, números finitos, límites estrictamente crecientes, `0 < rp_max ≤ 1000`, `0 < T3_max ≤ 3000 K`, y 5–51 nodos por eje. Llama a `resolver_ciclo` para validar entradas fijas; no reimplementa comprobaciones físicas. `ValueError` indica configuración incorrecta. Una referencia cuyos estados exceden el rango de 2B no impide calcular otros puntos.
- `_evaluar_punto(entradas: dict, rp: float, T3: float) -> dict`: construye `**{**entradas, 'rp': rp, 'T3': T3}`; copia siete entradas y sustituye solo las dos variables. Llama a `resolver_ciclo`. Retorna `estado` (`motor`, `no_motor`, `fuera_rango`, `entrada_invalida`, `error_numerico`), `motivo`, `datos` calculados (trabajos y calores [kJ/kg], rendimiento fraccional, T1–T4 [K], residuo [kJ/kg]) o `None`, y `operativas` únicamente para motor. Captura `EstadoFueraDeRango` antes que `ValueError`; errores de convergencia no se confunden con inviabilidad física. La usa `calcular_mapa_cp_variable`.
- `calcular_mapa_cp_variable(entradas: dict, rp_min: float=1.1, rp_max: float=80, T3_min: float=1200, T3_max: float=1800, n_rp: int=31, n_T3: int=31) -> dict`: valida con la función anterior, construye `rps` geométricos (espaciado uniforme en ln rp) y `T3s` lineales, ambos extremos incluidos. Una comprensión de listas anidada crea `filas[j][i]`, **j es T3 ascendente** e **i es rp ascendente**. `Counter` resume estados. Los diccionarios `mejores_malla['trabajo_neto']` y `['rendimiento']` usan `max` **solo** sobre puntos motores y devuelven `None` si no existe ninguno. Contiene `fijos` y `referencia_T3`. No llama a 2C: son únicamente mejores muestras discretas. Ejemplo: `calcular_mapa_cp_variable(DEFAULTS, 10, 20, 1500, 1700, 5, 5)['filas'][2][0]` corresponde a rp=10, T3=1600 K, \(w_\mathrm{neto}\approx402.071\) kJ/kg y \(\eta\approx34.893\%\). Lo llaman `preparar_mapa` y las pruebas.

**PYTHON — presentación en `cp_variable_web.py`:**

- `_color_mapa(fraccion: float, rendimiento: bool=False) -> str` interpola dos colores RGB y devuelve un código hexadecimal SVG. No modifica resultados de ingeniería.
- `svg_mapa_cp_variable(estudio: dict, magnitud: str, opt: dict|None=None) -> str|None` acepta `trabajo_neto` [kJ/kg] o `rendimiento` [fracción convertida a % en rótulos], genera rectángulos SVG con `<title>` consultable al pasar el cursor, ejes físicos, barra de color y una leyenda de estados. **Los puntos inválidos no se convierten en 0 ni se interpolan**: reciben un color distinto para no motor, estado fuera de 200–2000 K, entrada inadmisible o error numérico. Si no hay motores devuelve `None`. Marca A/B solo si 2C devuelve `maximo_interior`, la rp calculada está en el rango horizontal y la T3 coincide con la referencia; un supremo no es un punto marcado. `ValueError` para otra magnitud. La llama `preparar_mapa`.
- `preparar_mapa(entradas: dict, rp_min: float, rp_max: float, T3_min: float, T3_max: float, n_rp: int, n_T3: int) -> dict`: llama una vez a `calcular_mapa_cp_variable`, y opcionalmente **una sola** a `estudiar_cp_variable` de 2C si existen puntos motores y T3 de referencia está en el dominio y 200–2000 K. Devuelve el estudio más `optimos_referencia`, `svg_trabajo` y `svg_rendimiento` (SVG o `None`). Nunca reoptimiza cada fila, no ejecuta el modelo antiguo. La llama `web_app.index()`.

**PYTHON/FLASK — ejecución.** El mismo GET `/` solo renderiza el formulario; ninguna malla se calcula por navegación. POST `/` con `accion='mapa'` lee las siete entradas con `leer_entradas`, convierte los seis campos `mapa_cp_*` (`float` para límites e `int` para cantidades), llama a `preparar_mapa`, y envía `mapa_datos` y `mapa_config` al único `templates/index.html`. Si la configuración está mal, retorna HTTP 400 y conserva la sección. `dashboard.renderizar_dashboard(..., mapa_datos=None, mapa_config=None)` añade datos opcionales a la firma existente; los informes históricos mantienen sus parámetros por defecto y nunca calculan cp(T). SVG se genera en Python; JavaScript sigue ocupándose solo de la navegación/pestañas. El CSS nuevo aumenta discretamente la altura máxima de los SVG del mapa, sin rediseñar los paneles.

**Interpretación.** A T1, p1 y pérdidas fijas, una mayor T3 suele permitir más trabajo; elevar rp no mejora indefinidamente wnet porque aumenta el consumo del compresor. B maximiza otra razón, \(\eta=w_\mathrm{neto}/q_\mathrm{in}\), y puede estar lejos de A. En el caso base con T3=1600 K, 2C calcula por separado A en rp≈15.877934 y B en rp≈46.819105; ninguno se deduce de la malla. Cambiar ventana o número de muestras modifica el mejor nodo discreto, no el resultado matemático de 2C. Sin motores, ambos SVG se omiten con aviso específico. Un mapa termodinámico simplificado no es un mapa operativo real de turbomáquina.

**Verificación y aprendizaje.** 10 tests nuevos de cálculo en `test_mapa_diseno_cp_variable.py` y 6 de presentación/Flask en `test_mapa_cp_web.py`. Se conservan y adaptan 48 regresiones web previas: total previsto 64. Workflow `.github/workflows/verificacion_web_cp_variable.yml` en rama temporal de validación. Los resultados efectivos de CI se documentan después de ejecutarlos; ni esas pruebas ni el SVG constituyen validación experimental o inspección visual completa. Véanse [milestone técnico 25](docs/milestones/25_mapa_diseno_cp_variable.md) y [aprendizaje 25](docs/milestones/25_mapa_diseno_cp_variable_APRENDIZAJE.md).

#### Ampliación del mapa de diseño (milestone 32)

**PYTHON.** \`preparar_mapa(entradas, rp_min, rp_max, T3_min, T3_max, n_rp, n_T3)\` sigue invocando solo una vez \`calcular_mapa_cp_variable\`. Además de los mapas de prestaciones, usa \`graficas_mapa_cp.svg_mapa_viabilidad(estudio)\` (SVG con una celda por muestra y las cinco categorías, sin solver) y \`graficas_mapa_cp.svg_cortes_mapa(estudio,magnitud)\` (SVG o None para trabajo_neto [kJ/kg] o rendimiento [%]). Esta última elige tres índices de fila reales, traza rp con posición logarítmica y cierra la polilínea si operativas es None. \`data-rp\`, \`data-T3\`, \`data-valor\` permiten comparar exactamente números de prueba, sin inspección de píxeles.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** El mapa categórico no asigna rendimiento cero a un punto no motor. Las regiones visibles dependen de la resolución de la malla; los tres cortes no son curvas interpoladas ni máximos A/B. Solo se etiquetan temperaturas T3 presentes en la malla. Los nuevos gráficos se dibujan en la misma galería ampliable y no provocan evaluaciones termodinámicas adicionales. Véanse [milestone 32](docs/milestones/32_graficas_mapa_cp.md) y [aprendizaje](docs/milestones/32_graficas_mapa_cp_APRENDIZAJE.md).


### 4.64. Segunda ley y exergía física con cp(T) — milestone 26 (Fase 2G)

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** El panel Segunda ley se encuentra **activo** en el único dashboard cp(T). `segunda_ley_cp_variable.py` no resuelve otro ciclo: recibe la salida de `ciclo_cp_variable.resolver_ciclo` con cuatro temperaturas [K], presiones [kPa], entalpías [kJ/kg], entropías [kJ/(kg·K)] y trabajos [kJ/kg]. Usa `propiedades_aire.h(T0)` y `s(T0,p0)` para definir el estado ambiente de referencia con **T0 independiente de T1** y **p0 independiente de p1**. Ambas referencias se validan: 200≤T0≤2000 K, p0>0, reales finitos; por defecto 288,15 K y 100 kPa. Para cada estado calcula \(e_i=[h_i-h(T0)]-T0[s_i-s(T0,p0)]\). Las entropías son relativas a 298,15 K y 100 kPa como en 2A, sin inventar un valor absoluto de entropía.

En compresor adiabático \(s_{gen,c}=s_2-s_1\) y \(e_{D,c}=T0(s_2-s_1)\); en turbina adiabática \(s_{gen,t}=s_4-s_3\) y \(e_{D,t}=T0(s_4-s_3)\). Trabajos absorbidos/entregados se consideran positivos respectivamente. Para contrastar el teorema de Gouy–Stodola mediante la **otra expresión independiente del balance**, se evalúan \(w_c-(e_2-e_1)\) y \((e_3-e_4)-w_t\). Se conservan ambos resultados y sus residuos [kJ/kg]. Un pequeño negativo de generación entre `-1e-10` y 0 kJ/(kg·K) se normaliza a cero solo en el valor publicado, conservándose el **bruto**. Un negativo de mayor magnitud permanece con diagnóstico de inconsistencia, nunca se oculta con `max(0,x)`. La banda del balance es `1e-8 * max(1,abs(wc),abs(wt),abs(e_i))` [kJ/kg]: margen numérico, **no** incertidumbre experimental.

Los rendimientos \(\eta_{ex,c}=(e_2-e_1)/w_c\) y \(\eta_{ex,t}=w_t/(e_3-e_4)\) [fracción] se publican solo con ciclo motor, balances coherentes y numerador/denominador positivos no degenerados; en otro caso son `None` y la web los muestra como no definidos. La suma `eD_c+eD_t` **solo** cubre las turbomáquinas, no toda la instalación. Sin fuentes térmicas externas y sin combustión química modelada, ni `s3−s2` ni `s1−s4` se pueden identificar con generación de entropía en los procesos de calor. La caída de presión entre 2 y 3 se refleja en estados, pero no permite atribuir una destrucción aislada sin volumen de control definido. No se calcula rendimiento exergético global ni se confunde con el rendimiento térmico `wneto/qin`.

**PYTHON — nuevas funciones y contratos de `segunda_ley_cp_variable.py`:**

- `_ambiente_valido(T0: Real, p0: Real) -> None`: T0 [K], p0 [kPa]; valida rango, presión estrictamente positiva, finitud y exclusión de `bool`. Lanza `ValueError` para ambiente inválido, sin resolver estados. La llama `analizar_segunda_ley_cp_variable`; no invoca funciones científicas. Ejemplo: `_ambiente_valido(288.15,100)` termina sin retorno útil. El auxiliar controla una precondición matemática; `isfinite` se protege contra enteros enormes que producirían `OverflowError`.
- `analizar_segunda_ley_cp_variable(ciclo: dict, T0: Real=288.15, p0: Real=100.0) -> dict`: recibe salida 2B con cuatro estados, entalpías, entropías y trabajos ya calculados. Devuelve referencias `T0,p0,h0,s0`, `entropias`, `exergias` [kJ/kg], `generacion_bruta` y `generacion` [kJ/(kg·K)], `destruccion` [kJ/kg], `suma_turbomaquinas` [kJ/kg], `aportaciones_porcentaje` [0–100 % o `None`], `balances_exergia`, `residuos_balances` [kJ/kg], bandas numéricas, `eta_ex_compresor`, `eta_ex_turbina` [fracción o `None`], `estado` (`motor`, `no_motor`, `inconsistente`) y `diagnosticos` (tupla de textos). Llama a `_ambiente_valido`, `h` y `s` de 2A; **no** cambia 2B. `ValueError` para estructura/ambiente inválidos, sin convertir inconsistencia física en rendimiento. La llaman `preparar_segunda_ley` y las pruebas. Ejemplo: `analizar_segunda_ley_cp_variable(resolver_ciclo(288.15,1600,10,100,.85,.9,.05))['destruccion']` ≈ `(23.78256,24.00679)` kJ/kg.

**PYTHON — funciones de presentación en `cp_variable_web.py`:**

- `_ciclo_para_segunda_ley(T1: float, T3: float, rp: float, p1: float, eta_c: float, eta_t: float, delta: float) -> dict`: exactamente siete argumentos con K, kPa y fracciones; llama `resolver_ciclo` de 2B y propaga sus errores. `@lru_cache(maxsize=16)` memoriza los 16 últimos conjuntos de estados **solo lectura**. La llama `preparar_segunda_ley`; modificar T0/p0 no altera la clave y no reejecuta 2B. Ejemplo: `_ciclo_para_segunda_ley(288.15,1600,10,100,.85,.9,.05)`. La caché vive solo durante el proceso Flask y no modifica informes.
- `svg_exergia_destruida(estudio: dict) -> str | None`: acepta el retorno del análisis y genera SVG con dos barras realmente proporcionales a `destruccion` [kJ/kg], etiquetas, unidades y tooltip; si alguna destrucción es negativa retorna `None` y deja visible el diagnóstico numérico. La llama `preparar_segunda_ley` y no llama física. Ejemplo: `svg_exergia_destruida(estudio)` contiene dos `<rect>` para valores no negativos; la interpolación se limita a longitudes en píxeles.
- `preparar_segunda_ley(entradas: dict, T0: float=288.15, p0: float=100.0) -> dict`: dict de siete parámetros + referencias ambientales; retorna `{'ciclo': dict, 'estudio': dict, 'svg_destruccion': str|None}`. Llama una vez a `_ciclo_para_segunda_ley`, después a `analizar_segunda_ley_cp_variable` y `svg_exergia_destruida`, sin optimizar ni guardar archivos. Propaga `ValueError`, `EstadoFueraDeRango` y errores del solucionador. La llama la acción Flask `segunda_ley`. Ejemplo: `preparar_segunda_ley(DEFAULTS,300,120)['estudio']['T0'] == 300`.

**FLASK / JINJA.** `web_app.index()` conserva GET sin resolución de ciclos y añade POST `accion='segunda_ley'`: usa `leer_entradas` para los siete valores ya existentes, lee `T0`/`p0` como `float` e invoca `preparar_segunda_ley`. HTTP 400 conserva las entradas y selección de la sección si hay ambiente inválido, y no publica datos exergéticos falsos. `dashboard.renderizar_dashboard(...,segunda_datos=None,segunda_config=None)` acepta dos nuevos argumentos opcionales: resultados y valores ambientales del formulario. La rama `modo_cp=True` de `templates/index.html` contiene cinco bloques de datos/interpretación, barras SVG y los residuos de ambos balances; la rama `modo_cp=False` y los módulos antiguos conservan **informes de gas perfecto históricos**. No hay segunda plantilla, selector de modelos, combustible ni nueva URL. El icono/diagrama T-s antiguo no se copia como si fuera una trayectoria del proceso real.

**Ejemplo, residuos y efecto del ambiente.** Con T1=288.15 K, T3=1600 K, rp=10, p1=100 kPa, ηc=.85, ηt=.9, δ=.05, T0=288.15 K y p0=100 kPa: `s=(−0.034254422,0.048280925,1.181022688,1.264336212)` kJ/(kg·K), `e=(0,292.452989,1118.335756,376.022617)` kJ/kg, `sgen=(0.082535347,0.083313524)`, `eD=(23.782560,24.006792)` kJ/kg y total **47.789352 kJ/kg**, no total del ciclo. Comprobación alternativa: `eD_compresor` 23.782560 y `eD_turbina` 24.006792 kJ/kg, con residuos ≈2.49e−14 y 1.88e−13 kJ/kg. ηex,c≈92.479479 % y ηex,t≈96.765948 %. Cambiar p0 a 120 kPa desplaza los cuatro e_i por igual (las diferencias y destrucciones se cancelan); cambiar T0 a 300 K escala eD a temperatura de referencia nueva sin modificar los cuatro estados de flujo. Se distingue verificación de identidades, pruebas numéricas y validación científica experimental.

**Pruebas y límites:** 14 métodos científicos `tests/test_segunda_ley_cp_variable.py` y 7 de Flask `tests/test_segunda_ley_cp_web.py`; se conservan los 64 métodos de regresión de Fase 2F. GitHub Actions se amplía con un paso específico y rama temporal, sin reejecutar suites científicas históricas completas. Véanse [milestone técnico 26](docs/milestones/26_segunda_ley_cp_variable.md) y [guía educativa 26](docs/milestones/26_segunda_ley_cp_variable_APRENDIZAJE.md). Revisión visual real de Windows pendiente; no equivale a test Flask.

#### Ampliación gráfica de Segunda ley (milestone 33)

**PYTHON.** \`preparar_segunda_ley(entradas, T0=288.15, p0=100.0)\` conserva la reutilización de estados cacheados de 2B y una sola llamada a \`analizar_segunda_ley_cp_variable\`, añadiendo tres resultados SVG al diccionario para el dashboard. El módulo nuevo \`graficas_segunda_ley_cp.py\` incorpora \`svg_exergias_estados(estudio)\`, \`svg_generacion_entropia(estudio)\` y \`svg_balances_exergia(ciclo, estudio)\`, que devuelven cadenas SVG o \`None\`. El auxiliar \`_svg_barras_signo(datos, titulo, unidad, nota)\` transforma listas de etiquetas, valores firmados y colores en barras con origen cero, sin calcular de nuevo propiedades. Las pruebas XML leen \`data-rol\`, \`data-valor\` y \`data-residuo-c/t\` para comparar números. El HTML conserva una sola galería con visor ampliable y no publica nuevas barras ante \`estado='inconsistente'\`.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Exergía física e_i=(h_i−h0)−T0(s_i−s0) [kJ/kg] de los estados 1–4 con ambiente T0/p0. Generación de entropía en las máquinas adiabáticas s2−s1 y s4−s3 [kJ/(kg·K)]. Balance de compresor wc=(e2−e1)+T0*s_gen,c y de turbina (e3−e4)=wt+T0*s_gen,t, con signos y residuos conservados. **No** representan la destrucción total del ciclo, exergía química ni un rendimiento exergético global. Ver [milestone 33](docs/milestones/33_graficas_segunda_ley_cp.md) y [aprendizaje](docs/milestones/33_graficas_segunda_ley_cp_APRENDIZAJE.md).


### 4.65. Revisión educativa y visual del dashboard cp(T) — milestone 27, iteración 1

**Qué cambió entonces y qué no.** En aquella primera iteración había ocho gráficas SVG: un T–s en Resultados, una gráfica dual A/B en Optimización, tres curvas OFAT, dos mapas y una distribución de exergía destruida. Posteriormente **Resultados pasó a seis y Optimización a tres** mediante el milestone 29 (§4.67); la cifra anterior es histórica, no el inventario actual. Las ocho secciones, el único `templates/index.html` y los solucionadores 2A–2G permanecen intactos.

**Python — `educacion_cp_variable.py`.** Es un módulo **exclusivamente editorial**, importado por `dashboard.py`:

- `AYUDAS_CP: dict[str,str]` explica función física, unidades y cotas de las siete entradas del ciclo. `AYUDAS_MAPA: dict[str,str]` hace lo propio con los seis campos de la malla. Se muestran en etiquetas de ayuda vinculadas mediante `aria-describedby`; el solucionador sigue siendo el único responsable de verificar las restricciones.
- `CONTENIDOS: dict` almacena ocho parejas (`uso`, `fundamentos`). Cada sección científica tiene un resumen de uso breve más **ocho bloques teóricos desarrollados**; Informes y Ayuda mantienen cinco bloques conceptuales más breves. No recibe parámetros de usuario ni calcula estados.
- `_tarjeta(titulo: str, cuerpo: str) -> str` convierte el contenido de autoría propia en una tarjeta HTML. Escapa el título con `html.escape`; el cuerpo contiene marcado HTML propio y controlado para listas y subíndices, y **no debe incorporar texto externo sin escaparlo**.
- `construir_educacion_cp() -> dict` prepara el HTML común y lo pasa a Jinja a través de `dashboard.renderizar_dashboard` como `educacion_cp`, junto con los diccionarios de ayuda. En modo informe histórico (`modo_cp=False`) las tres variables se vacían y los paneles siguen el flujo original.

**HTML — ocho apartados, dos vistas.** En `templates/index.html` cada apartado cp(T) posee `data-edu-tabs`, una pestaña de configuración y otra de fundamentos. Informes y Ayuda reciben ahora esta estructura, conservando lectura histórica y enlaces. En seis apartados con cálculo, se añaden explicaciones de variables y conclusiones condicionadas a datos realmente presentes: por ejemplo, `c.viable` evita atribuir rendimiento a un ciclo no motor; `e.A.tipo` distingue máximo de supremo; `sens_datos.conteos` y `mapa_datos.conteos` identifican muestras motoras y descartadas; `ex.suma_turbomaquinas` se presenta explícitamente como **suma parcial**. En Simulación, Informes y Ayuda las conclusiones son orientativas, porque no se calculan prestaciones específicas en esas vistas.

**Gráficas — macro y modal.** La macro de Jinja `grafica_cp(titulo, svg, explicacion)` genera una tarjeta `<figure class="cp-figure">` con `<figcaption>`, SVG original de Python y nota de interpretación. Las tarjetas están agrupadas por secciones en `data-plot-viewer` y `.plot-grid`, con dos columnas en escritorio y una en pantallas de hasta 760 px. Los SVG se limitan en altura **solo en la tarjeta**, no se alteran sus valores ni su `viewBox`; el botón «Ampliar» utiliza el `<dialog>` histórico. `static/dashboard.js::enlarge(figure,button)` distingue `<img>` (histórico) y `<svg>` (modelo cp(T)), clona el SVG en `.chart-vector` y abre con `showModal()`. El cierre manual y Escape del diálogo nativo activan el evento `close`, limpian el visor y devuelven el foco al botón que abrió la gráfica. El script no pide recursos externos ni recalcula datos.

**Pruebas.** `tests/test_revision_educativa_cp.py` comprueba ocho secciones, extensión y estructura del texto, campos de ayuda, resultados idénticos a 2B, galería por acción, clasificaciones no motoras, historial inequívoco, semántica de modal y CSS responsive. El workflow `.github/workflows/verificacion_web_cp_variable.yml` conserva las regresiones web y ejecuta los tests editoriales. El commit previo 9dc0b8fe superó 97 tests y GitHub Actions; la segunda revisión añade cobertura educativa focalizada. La revisión visual manual a tamaño de pantalla real sigue siendo distinta de un test Flask.

**Para aprender:** identifica por qué el módulo editorial no importa ningún solucionador termodinámico; busca en Jinja `{{ educacion_cp.resultados.fundamentos|safe }}` y localiza su origen en `construir_educacion_cp`; después inspecciona la macro de SVG y el cambio de soporte de `<img>` a `<svg>` en `enlarge`. Véanse [milestone técnico 27](docs/milestones/27_revision_educativa_visual_cp.md) y [guía educativa 27](docs/milestones/27_revision_educativa_visual_cp_APRENDIZAJE.md).

### 4.66. Fundamentos extensos en ocho apartados — milestone 28, iteración educativa 2

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** La vista «Uso y configuración» conserva instrucciones breves: qué entrada modificar, qué acción ejecutar y qué resultado esperar. La vista «Fundamentos y procedimiento» es ahora una secuencia de lectura universitaria, no cinco tarjetas con dos frases. Las seis secciones científicas tienen **ocho temas progresivos y desarrollados** (contexto, fenómenos, magnitudes/ecuaciones, procedimiento real, lectura de resultados, ejemplo y límites). Informes y Ayuda tienen cinco temas cada una, adaptados a trazabilidad y glosario. Los cálculos y sus unidades son los de 2A–2G; el contenido es didáctico, no una nueva función científica.

Las explicaciones siguen **los algoritmos que realmente se ejecutan**: Simulación usa bisección de entropía para T2s/T4s e inversión de entalpía h(T) para T2/T4, con eficiencias de componentes; Resultados emplea diferencias h2−h1, h3−h4, h3−h2, h4−h1 y el residuo de la primera ley; Optimización busca A y B mediante cambios de signo y bisección en `x=ln(rp)`, usando respectivamente `R(eta_t*T4s−T2s/eta_c)` y el numerador de la derivada del rendimiento. No se afirma que A/B provengan de escoger el mejor punto de la gráfica. Sensibilidad evalúa OFAT lineal y sensibilidad central/unilateral, contrasta paso y medio paso; Mapa calcula celdas `T3 × rp` con rp logarítmica, clasifica no motor y distingue mejores nodos de la referencia continua 2C. Segunda ley combina la generación de entropía de cada turbomáquina adiabática, `e=(h−h0)−T0(s−s0)`, `eD=T0*sgen` y balances exergéticos alternativos. La destrucción mostrada sigue siendo **suma parcial**, no total del ciclo.

Los ejemplos introducidos son explícitamente **ilustrativos**: presiones p1/rp/δ, un balance aritmético de entalpías, un esquema de mapa 5×5, un cambio porcentual relativo y Gouy–Stodola con T0 fijada. No usan variables del caso actual ni pretenden sustituir las cifras calculadas en los paneles. Se enseñan además distinciones entre gas ideal y cp constante, máximo y supremo, prestación no motora y cero, residuo numérico y validación experimental.

**PYTHON, HTML Y CSS.** `educacion_cp_variable.CONTENIDOS` mantiene exactamente el mismo tipo `dict[str, {'uso': str, 'fundamentos': tuple[tuple[str,str],...]}]`. Los textos son literales HTML escritos y controlados por el proyecto: fragmentos `<p>`, `<ol>`, `<ul>`, expresiones con `<sub>` y superíndices, ejemplos y recuadros `<aside class="edu-insight">`. No se incorpora entrada editable ni interpolación desde el formulario. `_tarjeta(titulo, cuerpo)` y `construir_educacion_cp()` conservan firmas, argumentos, retornos, escapado de títulos y conexión con `dashboard.renderizar_dashboard`. **No** se altera `templates/index.html`: la plantilla sigue renderizando expresiones como `{{ educacion_cp.simulacion.fundamentos|safe }}` mediante claves estáticas de sección. Solo `static/style.css` cambia la distribución de `.edu-deep-grid` de dos columnas a **una columna de lectura**, con ancho máximo, tipografía/espaciado y formatos para `.edu-equation` y `.edu-insight`. Las gráficas y su visor permanecen idénticos.

**Cómo seguir el flujo real.** GET `/` llama a la preparación del dashboard y lee una vez las cadenas estáticas; Jinja inserta cada sección en su panel `fundamentos`. Al alternar pestañas, el JavaScript del dashboard muestra u oculta el contenido sin pedir otro cálculo. Las ecuaciones educativas **no se evalúan** en el navegador. La lógica para validar entradas, clasificar motores y producir SVG sigue exclusivamente en los módulos científicos y sus presentadores de etapas anteriores.

**Verificación.** `tests/test_revision_educativa_cp.py` comprueba cantidad/extensión de bloques, separación de la vista de uso, fórmulas y ejemplos presentes en HTML, CSS de lectura en columna, siete entradas e integración Flask; las demás pruebas siguen contrastando las prestaciones científicas. No se han incorporado bibliotecas ni recursos externos. La calidad de la exposición se revisa razonadamente contra las funciones citadas; la inspección de legibilidad y desplazamiento en Windows sigue como comprobación manual. Véanse [milestone técnico 28](docs/milestones/28_fundamentos_extensos_cp.md) y [aprendizaje 28](docs/milestones/28_fundamentos_extensos_cp_APRENDIZAJE.md).

### 4.67. Nueve representaciones científicas cp(T) — milestone 29, iteración visual 3

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Resultados pasa de **una a seis** representaciones: (1) T–s, (2) P–v específico, (3) cp(T), (4) γ(T), (5) trabajos y calores específicos, y (6) comparación de componentes ideales con el caso configurado. Optimización pasa de **una gráfica de escalas simultáneas a tres**: trabajo neto frente a rp, rendimiento frente a rp y compromiso entre ambos. Las secciones restantes conservan sus seis SVG anteriores: tres de Sensibilidad, dos de Mapa y uno de Segunda ley. Por tanto, con un caso motor y dominio A/B representable el dashboard activo reúne **quince SVG** en total, de los cuales nueve aparecen tras pulsar Simulación normal/Optimizar; otros seis se obtienen en sus acciones específicas. No se incorporan PNG ni recursos de red.

**Fuente científica de cada imagen.**

1. **T–s:** los cuatro pares exactos de `entropias` [kJ/(kg·K)] y `temperaturas` [K] los entrega `resolver_ciclo`. Se muestran ejes y marcas numéricas; solo sus uniones discontinuas son guías **esquemáticas**.
2. **P–v:** cada presión absoluta `p` [kPa] y temperatura `T` [K] del mismo ciclo determina `v=R_AIRE·T/(1000·p)` [m³/kg], porque `R_AIRE` tiene unidades J/(kg·K) y p está en kPa. No es volumen geométrico ni trayectoria politrópica.
3. **cp y γ:** dos curvas separadas, evaluadas con `propiedades_aire.cp(T)` y `gamma(T)` en 73 temperaturas equidistantes del intervalo cerrado 200–2000 K. Los cuatro estados se marcan a sus temperaturas calculadas. No hay extrapolación y γ(T) no se usa como constante para resolver las transformaciones.
4. **Balance:** barras con `trabajo_compresor`, `trabajo_turbina`, `trabajo_neto`, `calor_aportado` y `calor_rechazado`, todas en kJ/kg y con los signos que entrega 2B. Compresor se etiqueta como trabajo **consumido**, turbina como **producido**; se conserva la identidad `wnet=wt−wc=qin−qout`. Se omite la barra de prestaciones si `viable=False`.
5. **Ideal frente a configurado:** una segunda resolución de `resolver_ciclo(T1,T3,rp,p1,1,1,0)` mantiene T1, T3, rp y p1, además del **mismo aire cp(T)**. El SVG compara `wc`, `wt` y `wnet` en un panel [kJ/kg] y `η` en otro [%], con ejes independientes. No se representan barras operativas si cualquiera de los dos casos es no motor o no calculable: solo un mensaje diagnóstico.
6. **Optimización:** `estudiar_cp_variable` (2C) devuelve dominio motor abierto y resultados A/B. `curvas_optimizacion` resuelve **una sola malla** interior de 90 rp en escala logarítmica y conserva los valores `None`; las tres gráficas reutilizan sus muestras. El eje horizontal de las dos primeras muestra **valores reales de rp**, no `ln(rp)`, aunque la distancia entre marcas sea logarítmica. Un marcador A o B solo se dibuja si el optimizador lo clasifica como `maximo_interior`; un `supremo_frontera` **nunca** se convierte en punto del gráfico. El compromiso dibuja W [kJ/kg] frente a η [%], sin atribuir condición de frontera de Pareto a toda la curva.

**PYTHON — módulo nuevo `graficas_cp_variable.py`.** Separa estrictamente *datos científicos* y *coordenadas SVG*. Las funciones no cambian estados ni optimizan nada: transforman magnitudes ya resueltas en elementos `<svg>` accesibles. El único cálculo termodinámico adicional es el caso ideal del punto 5, mediante una llamada al **mismo** `resolver_ciclo`. Las firmas actuales son:

| Firma real | Argumentos, salida, unidades y conexión |
|---|---|
| `_numero(valor) -> str` | Recibe un número finito; formatea cuatro cifras significativas para las marcas, sin redondear el dato usado en la física. La llaman los trazadores de ejes y barras; ejemplo: `_numero(123.456) == "123.5"`. |
| `_margen(valores) -> tuple[float,float]` | Recibe muestras verticales del **mismo** indicador, retorna límites de presentación con 9 % de margen; no extrapola propiedades ni crea ciclos. La llaman los gráficos de líneas. Requiere una secuencia no vacía. |
| `_marco(nombre,x_etiqueta,y_etiqueta,x_lim,y_lim,*,log_x=False) -> tuple[str,callable]` | Recibe leyendas y límites de ejes en sus unidades físicas; produce cabecera SVG con seis marcas por eje y una **función interna** `posicion(x,y)` que convierte datos en píxeles. `log_x=True` requiere rp positivas y etiquetas de rp reales; límites no finitos producen `ValueError`. La llaman T–s, P–v, propiedades y optimización. |
| `_tramos(muestras,posicion,*,color=AZUL) -> str` | Recibe pares reales (x,y) o `None`; emite una polilínea por tramo contiguo, o un círculo para tramo aislado. **Cada None corta el dibujo.** La llaman propiedades y optimización; no interpola huecos. |
| `_estado(numero,x,y,posicion,*,color=AZUL,etiqueta=None) -> str` | Inserta círculo SVG con `data-estado` y coordenadas físicas `data-x/y`, texto y ayuda `<title>`. `numero` es 1–4 o las letras A/B; las llamadas provienen de estados, cp/γ y extremos interiores. |
| `svg_ts(ciclo) -> str` | Recibe el diccionario de 2B; dibuja estados T,s y guía discontinua 1→2→3→4→1. Lo llama `graficas_resultados`; no calcula nuevas trayectorias. |
| `svg_pv(ciclo) -> str` | Recibe el diccionario de 2B, usa `R_AIRE`, T [K] y p [kPa] y devuelve P–v [m³/kg,kPa]. Lo llama `graficas_resultados`; las guías son esquemáticas. |
| `svg_propiedades(estados) -> tuple[str,str]` | Recibe cuatro diccionarios `{'numero','T',...}`, llama cp/γ de 2A solo en 200–2000 K y devuelve dos SVG separados. Lo llama `graficas_resultados`. |
| `svg_balances(ciclo) -> str|None` | Cinco energías kJ/kg tomadas de 2B; devuelve `None` si el ciclo es no motor, sin fabricar rendimiento. Lo llama `graficas_resultados`. |
| `svg_comparacion(ideal,configurado) -> str|None` | Dos diccionarios 2B resueltos con cp(T); compara tres trabajos kJ/kg y rendimiento %, cada uno con su eje. Devuelve `None` si algún `viable` es falso. Lo llama `graficas_resultados`. |
| `graficas_resultados(ciclo,estados,entradas) -> tuple[list, str]` | Entradas: dict 2B, cuatro filas de estados, siete `float` de formulario; retorna seis tuplas `(titulo,svg|None,explicacion)` y texto diagnóstico. Llama todos los presentadores anteriores y, una vez, al solucionador 2B para el ideal. Captura `ValueError`, `EstadoFueraDeRango` y `ErrorNumericoCiclo` **solo de esa comparación**. La llama `cp_variable_web.preparar_resultados`. |
| `graficas_optimizacion(curva,estudio) -> tuple` | Recibe una lista de hasta 90 dict `{'rp','trabajo','rendimiento'}` o `None` y el dict 2C; devuelve tres tuplas `(titulo,svg,explicacion)` si hay al menos dos muestras motoras y dominio abierto, o `()`. Llama a `_marco`, `_tramos` y `_estado`. La llama `cp_variable_web.preparar_resultados`; **no** invoca de nuevo 2B/2C. |

**Entrada, control de flujo, vista HTML y ejemplo.** `web_app.index()` sigue recibiendo siete parámetros y dos acciones `normal/optimizar`; no cambia el servidor, la navegación ni las otras secciones. `cp_variable_web.preparar_resultados` ejecuta 2B una vez, 2C una vez, calcula las cuatro propiedades y llama a `graficas_resultados`; después pasa el único barrido `curvas_optimizacion(entradas,estudio)` a `graficas_optimizacion`. Ya no genera el SVG dual obsoleto `svg_optimizacion` ni claves `ts/grafica`. Jinja hace un `for titulo,svg,explicacion in ...` para cada galería y reutiliza la macro `grafica_cp`, la cuadrícula responsive y el botón «Ampliar»; los SVG no contienen JavaScript. Ejemplo: `datos=preparar_resultados(DEFAULTS)`, `len(datos['graficas_resultados']) == 6` y `len(datos['graficas_optimizacion']) == 3` para el caso base. Sus nueve imágenes se conservan en memoria; no se crean PNG ni archivos de informe.

**Verificación y límites.** `tests/test_graficas_cp_variable.py` compara los valores de los SVG (atributos `data-x`/`data-y`/`data-valor`) contra las salidas de 2A–2C; comprueba conversión de Pa/kPa, ideal versus configurado, máscaras por `None`, máximos interiores versus supremos y funcionamiento Flask/visor. La suite web vigente de esta iteración sumó **110/110 pruebas correctas**, incluyendo doce nuevas. En aquel momento el descubrimiento histórico de 439 métodos producía 18 fallos y 62 errores **anteriores** por contratos Flask sustituidos. El milestone 30 separa los contratos antiguos y explica cómo se mantiene la suite completa actual (§4.68). Esta verificación comprueba coherencia **interna**, no validación experimental. Se inspeccionaron seis SVG rasterizados, pero la legibilidad real en diferentes navegadores/tamaños debe revisarse en Windows. Véanse [milestone técnico 29](docs/milestones/29_graficas_resultados_optimizacion_cp.md) y [aprendizaje 29](docs/milestones/29_graficas_resultados_optimizacion_cp_APRENDIZAJE.md).

### 4.68. Suite vigente y pruebas históricas — milestone 30

**PYTHON — qué hace `unittest`.** `python -m unittest discover -s tests -q`
importa los módulos `test_*.py`, descubre las clases derivadas de
`unittest.TestCase` y ejecuta sus métodos `test_*`. Cada comprobación usa
aserciones: `FAIL` significa aserción falsa; `ERROR`, excepción inesperada;
`skipped`, omisión explícita, como las comparaciones opcionales con SciPy.
El método `subTest` repite casos dentro de una misma prueba, por lo que un
solo método puede generar varias incidencias. Una **regresión** sería perder
un requisito todavía vigente, no dejar de ejecutar una ruta Flask eliminada
intencionadamente en favor de cp(T).

**Estado y organización.** Antes de esta intervención se descubrieron 439
métodos: 394 correctos, 37 métodos afectados por 18 fallos y 62 errores,
y ocho omisiones justificadas por SciPy opcional. Los once archivos de pruebas
que mezclaban física todavía válida con contratos de la web antigua se
conservan completos en `legacy_tests/`. Su contenido coincide con el
repositorio congelado `Brayton_simutalor-gas_perfecto`; allí son válidos los
303 de redirección, los nueve parámetros y la creación de HTML. En la
aplicación cp(T), los 37 métodos Flask incompatibles se enumeran por nombre
en `tests/test_compatibilidad_historica.py`, mientras **los otros 127 métodos
de estos archivos siguen ejecutándose** en el perfil vigente. No se
introducen `skip` ni tolerancias mayores para ocultar problemas.

**Firmas y flujo del módulo de compatibilidad:**

- `_casos(suite)`: recibe `unittest.TestSuite`, produce con `yield` instancias
  `TestCase` de sus suites anidadas; devuelve un generador, sin unidades
  físicas. Su recursión con `yield from` simplifica el filtrado; no evalúa
  un ciclo. Un `suite` no iterable produciría `TypeError`. La llama
  `load_tests`; no la invoca el simulador.
- `load_tests(loader, tests, pattern)`: función de protocolo reconocida por
  `unittest` al descubrir el módulo; recibe un `TestLoader`, una `TestSuite`
  preexistente y un patrón de descubrimiento (`str | None`), y devuelve una
  `TestSuite` de los 127 tests históricos aún vigentes. `importlib.util`
  carga cada archivo de `legacy_tests` mediante su ruta `Path`, sin alterar
  imports de producción. `loader.loadTestsFromModule` enumera los métodos y
  `_casos` los aplana. Si falta alguno de los 37 nombres del manifiesto o
  cambia su total, lanza `AssertionError` durante el descubrimiento. No hay
  parámetros termodinámicos ni unidades: es infraestructura de calidad.

**Conservación de JSON heredado.** Los ocho métodos de
`tests/test_integridad_historica_actual.py` son pruebas de la **aplicación
actual**, no de las antiguas redirecciones. Parten de un estudio legítimo de
gas perfecto, lo serializan en `TemporaryDirectory`, alteran de forma
controlada estructuras, tipos, temperaturas, presiones, entropías y exergía,
y usan `segunda_ley.validar_estudio_reutilizable(estudio,parametros)` para
rechazar incoherencias. También prueban HTTP 422 ante metadatos ilegibles,
aviso ante Segunda Ley no verificable, descarga idéntica a los bytes
originales y ausencia de reutilización de un informe histórico como si fuera
un cálculo cp(T). Estas pruebas **no** vuelven a introducir las ecuaciones
antiguas en el nuevo solucionador.

**Ingeniería y criterio de calidad.** Las verificaciones científicas activas
de 2A–2G siguen comprobando conservación energética, dominios físicos,
entropía/exergía y máximos interiores frente a supremos. Las pruebas del gas
perfecto verifican su modelo **histórico**; la integridad de un informe no
demuestra su autoría, y todas estas comprobaciones son **verificación interna
del software**, nunca validación experimental de un motor real. El workflow
`.github/workflows/verificacion_web_cp_variable.yml` mantiene las 110 pruebas
web focalizadas y añade el descubrimiento completo actual para que un fallo
vigente haga fallar GitHub Actions.

**Uso reproducible** (desde la raíz, tras instalar `requirements.txt`):

```bash
python -m unittest discover -s tests -q
python -m unittest discover -s tests -p 'test_integridad_historica_actual.py' -v
```

**Resultado local comprobado:** 410 métodos descubiertos, 402 correctos,
cero fallos, cero errores y ocho omisiones opcionales de SciPy en 46.623 s,
Linux/Python 3.12 con dependencias declaradas. Las ocho pruebas nuevas
también pasaron por separado. Queda comprobar el commit de validación en
GitHub Actions antes de publicarlo en la rama de desarrollo.

En Windows, usar `.venv\Scripts\python.exe` si no existe el alias global
`python`. Las pruebas no se ejecutan al arrancar Flask. El histórico completo
se ejecuta en el repositorio separado de gas perfecto, sin modificarlo.
Véanse [milestone técnico 30](docs/milestones/30_saneamiento_suite_historica.md)
y [aprendizaje 30](docs/milestones/30_saneamiento_suite_historica_APRENDIZAJE.md).

### 4.69. Núcleo monoeje estático cp(T) — milestone 34

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** El ciclo Brayton de `ciclo_cp_variable.py` mantiene `p4=p1` y calcula trabajo neto; el nuevo `acoplamiento_turbomaquinaria_cp.py` resuelve otra pregunta: qué presión queda después de extraer de la turbina el trabajo necesario para alimentar el compresor a través de un eje de eficiencia `eta_m`. La condición es `eta_m*wt=wc`, con `wc=h2-h1` y `wt=h3-h4`, en kJ/kg. El modelo prescribe `T3` y la pérdida de cámara; `q_in=h3-h2` no equivale a modelar combustible. Primero se invierte la entalpía de salida real `h4=h3-wc/eta_m`; posteriormente `h4s=h3-wt/eta_t`. La presión desconocida satisface `ln(p4)=ln(p3)+(s0(T4s)-s0(T3))/(R_AIRE/1000)`; así se conserva la entropía en el estado isentrópico ficticio sin imponer `p4=p_amb`. El margen de tobera solo compara `p4` con `p_amb`, sin inferir empuje.

**PYTHON.** `resolver_acoplamiento(T_amb,p_amb,rp,eta_c,T3,delta,eta_t,eta_m)` recibe ocho reales (K, kPa y factores adimensionales) y retorna un `dict`: tuplas `temperaturas`, `presiones`, `entalpias`, `entropias` (orden 1–4), `T2s`, `T4s` [K], `h2s`, `h4s`, `trabajo_compresor`, `trabajo_turbina`, `calor_aportado`, `residuo_eje` [kJ/kg], `rendimiento_mecanico`, `rendimiento_turbina`, `residuo_isentropico_turbina` [kJ/(kg·K)], `relacion_salida_ambiente` [-], `margen_presion_kpa` [kPa] y `diagnostico_tobera` (`con_margen`, `limite`, `sin_margen`). Llama a `h`, `s`, `s0`, `T_desde_h` y a `_temperatura_desde_s0` de la Fase 2B; no llama a `resolver_ciclo`, no modifica el dashboard y no comparte presiones impuestas con el Brayton anterior. `_real(valor)` devuelve un booleano que rechaza `bool`, no reales y no finitos; es auxiliar puro del solucionador. `_invertir_h(valor,descripcion)` valida una entalpía finita [kJ/kg], lanza `EstadoFueraDeRango` ante valores fuera del dominio entálpico, `ErrorNumericoCiclo` ante no representabilidad, o devuelve temperatura [K] por bisección ya implementada. Rechaza relaciones `rp<=1`, eficiencias fuera de `(0,1]`, `delta` fuera de `[0,1)`, `q_in<=0` y presiones incompatibles. Ejemplo: `r=resolver_acoplamiento(288.15,100,10,.85,1600,.04,.9,.98)`; `r['presiones'][3]` recupera `p4` en kPa. Reproducibilidad, límites y pruebas en [milestone 34](docs/milestones/34_acoplamiento_turbomaquinaria_cp.md) y [aprendizaje 34](docs/milestones/34_acoplamiento_turbomaquinaria_cp_APRENDIZAJE.md).

### 4.70. Tobera convergente y empuje específico cp(T) — milestone 35

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** La salida del núcleo monoeje de §4.69 se interpreta como el estado de **remanso** `Tt,pt` de una tobera convergente; esto exige despreciar la energía cinética del plano 4 y las pérdidas de conexión, hipótesis adicionales al balance previo. En la salida, `Te,pe` son magnitudes estáticas. Para una `pe` de prueba, `s(Tes,pe)=s(Tt,pt)` y `he=ht-eta_n*(ht-h(Tes))` describen expansión y eficiencia entálpica. La energía cinética es `Ve=sqrt(2000*(ht-he))` [m/s]. El criterio sónico se evalúa **sobre el estado real**: `Mach=Ve/sqrt(gamma(Te)*R_AIRE*Te)`; el programa halla `Mach=1` mediante bisección acotada, sin usar como exacta la relación analítica de gamma constante. Si la presión ambiente permite expansión subsónica, `pe=p_amb`; si la tobera está bloqueada, `pe=pcrit>p_amb` y Mach ≈ 1. La continuidad proporciona `Ae/mdot=1/(rho_e Ve)` [m²/(kg/s)] y el empuje específico estático (caudal de aire igual antes/después) es `Fs=Ve+1000*(pe-p_amb)/(rho_e Ve)` [N/(kg/s)], suma de término de momento y presión. El factor 1000 convierte presiones de kPa a Pa. Es una aproximación de núcleo más tobera, NO empuje absoluto de motor real.

**PYTHON.** El módulo nuevo `tobera_cp_variable.py` no modifica `ciclo_cp_variable.py` ni el panel web. `_validar_real(x)` recibe cualquier objeto y devuelve booleano, rechazando booleanos numéricos y no finitos; se llama desde `resolver_tobera_convergente`. `_estado_desde_isentropica(Tt,ht,Tes,eta_n)` recibe K, kJ/kg, K y eficiencia [-], valida dominio y devuelve tupla `(Te [K], Ve [m/s], Mach [-])`, usando `h`, `T_desde_h` y `gamma`; `eta_n=1` reaprovecha `Tes` exactamente. `_estado_critico(Tt,ht,eta_n)` recibe K, kJ/kg y eficiencia; busca por bisección la `Tes` que da Mach 1 y devuelve K o `None` cuando el dominio 200–2000 K termina antes; llama al auxiliar de estado. `resolver_tobera_convergente(Tt,pt,p_amb,eta_n=1.0)` recibe temperatura de remanso K, presiones kPa y eficiencia [-]. Valida `pt>p_amb>0`, `0<eta_n<=1`; calcula presión crítica, clasifica `regimen`, recupera temperatura isentrópica de salida si procede y devuelve un diccionario con `temperatura_remanso`, `presion_remanso`, `temperatura_isentropica_salida`, `temperatura_salida`, `presion_salida`, `presion_ambiente`, `presion_critica`, `temperatura_isentropica_critica`, `entalpia_remanso`, `entalpia_salida`, `velocidad_salida`, `velocidad_sonido`, `mach_salida`, `densidad_salida`, `area_por_caudal`, `empuje_especifico_momento`, `empuje_especifico_presion`, `empuje_especifico_total`, `rendimiento_tobera`, `residuo_energia` y `residuo_isentropico`; los valores numéricos llevan las unidades indicadas por las fórmulas y documentos 35. `resolver_nucleo_con_tobera(T_amb,p_amb,rp,eta_c,T3,delta,eta_t,eta_m,eta_n=1.0)` llama a `resolver_acoplamiento` una sola vez y luego a la tobera, devolviendo `{'nucleo':dict,'tobera':dict}`. Ejemplo: `resultado=resolver_nucleo_con_tobera(288.15,100,10,.85,1600,.04,.9,.98,.95)`; `resultado['tobera']['mach_salida']` consulta Mach. Las tres excepciones posibles son `ValueError`, `EstadoFueraDeRango` y `ErrorNumericoCiclo`; no se simula resultado si la tobera carece de margen de presión o se exige extrapolación. Más desarrollo educativo en [milestone técnico 35](docs/milestones/35_tobera_cp_variable.md) y [aprendizaje 35](docs/milestones/35_tobera_cp_variable_APRENDIZAJE.md).

### 4.71. Condiciones de vuelo subsónico, difusor y empuje neto cp(T) — milestone 36

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** `vuelo_cp_variable.py` añade una atmósfera de referencia (troposfera 0–11 km e isotérmica 11–20 km geopotenciales), o ambiente estático introducido por el usuario. ISA se calcula con `T0=288.15 K`, `p0=101.325 kPa`, `g0=9.80665 m/s²`, `L=-0.0065 K/m`, `R_ISA=287.05287 J/(kg K)`; usa `p=p0(T/T0)^(-g0/(L R_ISA))` en troposfera y `p=p11 exp[-g0(z-11000)/(R_ISA T11)]` encima. Esta referencia hidrostática usa `R_ISA`, ligeramente distinto del `R_AIRE` del aire de composición fija que simula el motor. No predice meteorología. A `0<=Mach<1`, la velocidad `V∞=M∞sqrt(gamma(T∞)*R_AIRE*T∞)` y la temperatura de remanso satisfacen `h(Tt0)=h(T∞)+V∞²/2000`. La presión total ideal surge de la igualdad `s(Tt0,pt0)=s(T∞,p∞)`, sin asumir gamma constante. El difusor prescribe `pt2=pi_d pt0` con `0<pi_d<=1` y conserva `Tt2=Tt0`. El núcleo monoeje toma **pt2** como presión de entrada al compresor; la tobera descarga contra la presión **estática exterior p∞**. Se reevalúa el diagnóstico de margen del núcleo frente a `p∞`, no frente a `pt2`. El empuje específico neto `Fs=Ve-V∞+1000(pe-p∞)/(rho_e Ve)` [N/(kg/s)] desglosa momento saliente, resistencia de entrada y presión. Si es negativo se informa sin truncarlo; si no existe presión de expansión, no se inventa empuje.

**PYTHON.** `_finito(valor)` recibe un objeto y devuelve booleano: acepta reales finitos, pero no `bool`. `atmosfera_estandar(altitud_geopotencial)` recibe metros geopotenciales y devuelve dict con `altitud_geopotencial` [m], `temperatura` [K], `presion` [kPa], `densidad` [kg/m³] y `capa`; lanza `ValueError` fuera de 0–20000 m. `calcular_remanso(T_estatica,p_estatica,mach)` recibe K, kPa y Mach [-], devuelve dict con estados estáticos, `velocidad_sonido`, `velocidad_vuelo` [m/s], `temperatura_remanso`, `presion_remanso`, `residuo_energia` [kJ/kg] y `residuo_entropia` [kJ/(kg K)], usando `gamma`, `h`, `T_desde_h`, `s0`, `s`. Propaga `EstadoFueraDeRango` fuera de 200–2000 K y `ErrorNumericoCiclo` si una presión no es representable. `aplicar_difusor(remanso,pi_d)` recibe dict de remanso y factor [-], devuelve `temperatura_remanso` [K], `presion_remanso`, `presion_remanso_ideal` [kPa] y `recuperacion_presion` [-], o errores por valores inválidos. `resolver_turborreactor_vuelo(mach,rp,eta_c,T3,delta,eta_t,eta_m,eta_n=1.0,pi_d=1.0,*,T_amb=None,p_amb=None,altitud_geopotencial=None)` permite *únicamente una* fuente ambiental, pareja K/kPa o ISA con altitud [m], y devuelve dict anidado `ambiente`, `remanso`, `difusor`, `nucleo`, `tobera` (dict o `None`), `diagnostico`, `empuje_especifico_momento`, `resistencia_entrada`, `empuje_especifico_presion`, `empuje_especifico_neto` [m/s o `None`], `empuje_neto_positivo` [booleano o `None`] y `origen_ambiente`. El `*` fuerza argumentos ambientales nombrados. Invoca una sola vez a `resolver_acoplamiento` con `pt2`, realiza una copia de `nucleo` para sobrescribir únicamente sus diagnósticos relativos a la presión exterior y llama a `resolver_tobera_convergente` cuando `p4>p∞`. Ejemplo: `r=resolver_turborreactor_vuelo(.7,10,.85,1600,.04,.9,.98,.95,.97,T_amb=288.15,p_amb=100)`; `r['empuje_especifico_neto']` devuelve N/(kg/s). Sin tobera disponible el empuje es `None`, no cero. Los contratos públicos 34 y 35 y el dashboard permanecen intactos. Véanse [milestone técnico 36](docs/milestones/36_condiciones_vuelo_cp.md) y [aprendizaje](docs/milestones/36_condiciones_vuelo_cp_APRENDIZAJE.md).

### 4.72. Turborreactor con combustible energético y TSFC — milestone 37

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** El nuevo módulo `combustible_cp_variable.py` amplía el *modelo científico separado* del turborreactor de §§4.69–4.71 y no altera `ciclo_cp_variable.py`. Las estaciones del compresor y de entrada a turbina representan condiciones **totales**; se reutilizan ISA, remanso y difusor del milestone 36. La temperatura prescrita `T3` fija la energía demandada al combustible: `h2 + f*eta_b*PCI = (1+f)*h3`, o `f=(h3-h2)/(eta_b*PCI-h3)` [kg combustible/kg aire]. `h(T)` del aire está referida a cero en 298.15 K; la hipótesis específica de esta ecuación es **entalpía sensible de combustible despreciada en esa misma referencia**. El PCI es energía química por kg de combustible y el combustible se usa con un gas equivalente de composición fija; no se resuelve una reacción real ni gases quemados. El caudal de turbina es `1+f` veces el de aire y su balance de eje correcto es `eta_m*(1+f)*(h3-h4)=h2-h1`, por kg de aire. `h4s=h3-(h3-h4)/eta_t` permite obtener `T4s` y la presión `p4` de `s(T4s,p4)=s(T3,p3)`. La tobera existente calcula condiciones estáticas; el empuje específico neto en vuelo es `(1+f)*Ve - V_inf + (1+f)*1000*(pe-p_inf)/(rho_e*Ve)` [N/(kg/s aire)], con presión en kPa. La resistencia asociada al aire entrante resta y el factor másico multiplica ambos términos de salida. El **TSFC** es `f/Fs` [kg/(N·s)] o `3600*f/Fs` [kg/(N·h)]; queda indefinido si el empuje neto es no positivo o no hay expansión. No se especifica caudal másico absoluto.

**PYTHON.** `resolver_turborreactor_con_combustible(mach,rp,eta_c,T3,delta,eta_t,eta_m,eta_n=1.0,pi_d=1.0,eta_b=0.99,PCI=43000.0,*,T_amb=None,p_amb=None,altitud_geopotencial=None)` recibe Mach, relaciones, pérdidas y eficiencias [-], temperaturas K, presiones kPa, altitud m, PCI kJ/kg combustible; retorna un diccionario con `origen_ambiente`, `ambiente`, `remanso`, `difusor`, `compresor`, `combustor`, `turbina`, `tobera` (diccionario o `None`), `prestaciones` (empuje bruto, salida, entrada, presión, neto, TSFC en dos unidades) y `diagnosticos` (margen, régimen, funcionamiento y aproximación). La llaman sus pruebas o código externo; internamente llama a `atmosfera_estandar` o recibe ambiente directo, `calcular_remanso`, `aplicar_difusor`, `_compresor`, `_combustor`, `_turbina`, `resolver_tobera_convergente`. `_validar_entradas(rp,eta_c,T3,delta,eta_t,eta_m,eta_n,eta_b,PCI)` es auxiliar sin retorno que valida reales finitos, eficiencia `(0,1]`, `rp>1`, `delta` `[0,1)`, `PCI>0` y `T3` 200–2000 K; produce `ValueError` si falla. `_compresor(T1,p1,rp,eta_c)` invierte entropía a `T2s` y entalpía a `T2`, devuelve `dict` de estados [K,kPa,kJ/kg], trabajo y residuo; usa `s0`, `_temperatura_desde_s0`, `_invertir_h`, `h` y `s`. `_combustor(h2,T3,p2,delta,eta_b,PCI)` devuelve `dict` con `f`, `factor_masico`, `h2`, `h3`, `p3`, parámetros y residuo energético; rechaza aporte no positivo o denominador no positivo. `_turbina(T3,p3,h3,wc,f,eta_m,eta_t)` devuelve `dict` con `T4/T4s` [K], `h4/h4s` [kJ/kg], `p4` [kPa], trabajos referidos a gas y a aire, rendimiento y residuos; usa `_invertir_h`, `h`, `s0`, `s`, `log`, `exp`. Sus auxiliares solo los llama la función pública; los dominios se defienden con `ValueError`, `EstadoFueraDeRango` y `ErrorNumericoCiclo`. Los diccionarios anidados permiten `r['combustor']['f']` y `r['prestaciones']['TSFC_kg_N_h']`; `None` expresa ausencia física de valor, no un cero. Ejemplo: `r=resolver_turborreactor_con_combustible(0,10,.85,1600,.04,.9,.98,.95,1,.99,43000,T_amb=288.15,p_amb=100)` devuelve `f≈0.02802821` y `TSFC≈0.10529688 kg/(N·h)`. En un límite **matemático** `PCI→infinito`, `f→0` y se recupera el modelo de los milestones 34–36, sin atribuir valor físico a ese PCI. Las pruebas y limitaciones están en [milestone 37](docs/milestones/37_combustible_tsfc_cp.md) y [aprendizaje 37](docs/milestones/37_combustible_tsfc_cp_APRENDIZAJE.md).

### 4.73. Mapas paramétricos de turborreactor cp(T) y Pareto — milestone 38

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** `mapas_prestaciones_turborreactor_cp.py` agrega evaluaciones discretas del solucionador de combustible de §4.72 sin cambiar una sola ecuación termodinámica del motor. El mapa `rp–T3` compara diseños con ambiente y Mach idénticos: devuelve empuje específico `Fs` [N/(kg/s aire)], TSFC [kg/(N·h)], dosado `f` [-], `wc` [kJ/kg aire], salida de turbina `T4` [K], `p4` [kPa], régimen de tobera y motivos de inviabilidad. Mayor `rp` suele requerir mayor `wc` y extracción de trabajo de turbina; variar `T3` afecta al dosado, la energía y la expansión: ni Fs ni TSFC obedecen tendencias universales. Se identifican puntos de máximo Fs y mínimo TSFC únicamente entre casos con empuje neto positivo y tobera disponible. Un punto A domina B si `Fs_A>=Fs_B`, `TSFC_A<=TSFC_B` y alguna desigualdad es estricta. El conjunto no dominado representa compromisos **en la malla**, no óptimos continuos ni puntos operables por un mismo motor. La detección `en_frontera_malla` advierte que el extremo puede cambiar al ampliar un eje. Un segundo mapa `Mach–altitud ISA` compara resultados *descriptivamente*; no se define Pareto global entre ambientes y Mach distintos. Sin mapas de compresor/turbina, geometría, giro y gasto másico, no son mapas reales fuera de diseño ni permiten inferir empuje absoluto en altitud.

**PYTHON.** Tres funciones públicas independientes: `barrer_rp_t3(valores_rp,valores_T3,*,mach=0,pi_d=1,T_amb=None,p_amb=None,altitud_geopotencial=None,eta_c=.85,delta=.04,eta_t=.9,eta_m=.98,eta_n=.95,eta_b=.99,PCI=43000,restricciones=None)` recibe vectores crecientes de rp [-] y T3 [K], condiciones de ambiente directo por defecto 288.15 K/100 kPa o altitud ISA [m], y controles de diseño; devuelve dict de `nombre`, nombres y vectores de ejes, `fijos`, `restricciones`, matriz de `puntos` organizada `[fila T3][columna rp]`, matriz `estados`, `unidades`, contadores, extremos y lista `pareto`. `barrer_mach_altitud(valores_mach,valores_altitud,*,rp=10,T3=1600,pi_d=.98,eta_c=.85,delta=.04,eta_t=.9,eta_m=.98,eta_n=.95,eta_b=.99,PCI=43000,restricciones=None)` recibe Mach en `[0,1)` y altitud geopotencial ISA 0–20000 m; usa la misma estructura con `pareto=None` y extremos solo descriptivos. `frente_pareto(puntos)` recibe lista de dicts con claves `estado`, `Fs` y `TSFC_kg_N_h`, devuelve una lista de los dicts válidos no dominados, por comparaciones anidadas O(n²); si un punto marcado válido tiene objetivos inválidos, lanza `ValueError`. Las funciones públicas llaman a `_eje` (validación de secuencia ordenada de números finitos; tupla de unidades del eje), `_barrer` (doble bucle y construcción de matriz), y mediante este a `_restricciones(configuracion)` (normaliza dict de T3_max [K], rp, Mach, altitud y booleanos; `ValueError` por límites incoherentes), `_punto(entradas,indices,config)` (dict con entradas, índices, estado, motivo, métricas y resultado completo o `None`) y `_resumen(puntos,nx,ny,comparar)` (cuenta estados con `Counter`, `max/min`, borde, y llama a `frente_pareto` solo si los ambientes son comparables). `_incumplimiento(entradas,config)` retorna etiqueta de restricción o `None`; la llama `_punto` antes de invocar `resolver_turborreactor_con_combustible(**entradas)`. Excepciones físicas previstas `ValueError`/`EstadoFueraDeRango` producen `inadmisible`; `ErrorNumericoCiclo` produce `fallo_numerico`, con campos indefinidos `None`, pero errores de programación como `TypeError` se propagan y **no se ocultan**. `_eje(valores,nombre,minimo,maximo,incluir_maximo=True)` comprueba secuencia no vacía, estrictamente creciente, real y finita o lanza `ValueError`. `_barrer(nombre,eje_x,eje_y,fijo,nombre_x,nombre_y,restricciones,comparar)` recibe ejes (rp/T3, Mach/ISA), constantes y indicador de comparabilidad, y devuelve toda la estructura científica. `enumerate` evita índices manuales; copias `dict(fijo)` evitan sobrescribir controles entre puntos; las comprensiones montan filas. Ejemplo: `m=barrer_rp_t3([5,10,15],[1400,1600]); m['maximo_Fs']['valor']` consulta el mayor Fs de la malla. Véanse [milestone 38](docs/milestones/38_mapas_prestaciones_turborreactor_cp.md) y [aprendizaje 38](docs/milestones/38_mapas_prestaciones_turborreactor_cp_APRENDIZAJE.md).

**CORRECCIÓN VERIFICADA EN M39 (estado actual del mapa).** `_punto` registra ahora por separado `cumple_restricciones` (`bool`) y su `estado` físico; `_resumen` añade el entero `cumplen_restricciones`. `exigir_empuje_positivo` y `exigir_margen_tobera` actúan realmente sobre el filtro sin cambiar los resultados: un punto `empuje_no_positivo` solo cumple un filtro que relaja el primer requisito; uno `sin_expansion` necesita que se relajen ambos para poder cumplirlo, porque el empuje no está definido. Aunque cumplan un filtro relajado, ninguno se convierte en `valido` ni participa en óptimos/Pareto de empuje positivo y TSFC. La clasificación real y los contratos públicos anteriores permanecen. Ejemplo: `m=barrer_rp_t3([3],[500,600],mach=.9,pi_d=.7,restricciones={'exigir_empuje_positivo':False,'exigir_margen_tobera':False}); m['cumplen_restricciones']` devuelve 2, mientras `m['validos']` devuelve 0. Más detalle en [auditoría 39](docs/milestones/39_verificacion_independiente_turborreactor_cp.md).

### 4.74. Verificación científica independiente de turborreactor — milestone 39

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Esta etapa no añade componentes físicos. Audita matemáticamente el compresor, combustible, eje, turbina, tobera, remanso, difusor, empuje, TSFC y mapas de §§4.69–4.73. La referencia analítica usa gas caloríficamente perfecto `cp=1.08 kJ/(kg K)`, `R=R_AIRE J/(kg K)` y `gamma=cp/(cp-R/1000)`; la entalpía relativa es `cp*(T-298.15)` [kJ/kg], la entropía se expresa en función de `ln(T/Tref)` y `ln(p/pref)`, y las transformaciones isentrópicas tienen potencias explícitas de `rp`. La función de referencia calcula por separado Tt0/pt0, T2, f, trabajo y presión de turbina, condición crítica de tobera, empuje y TSFC. No llama a propiedades variables ni a solucionadores de producción para construir sus resultados. Comparar magnitudes en unidades iguales mediante `error_absoluto=abs(x_cp-x_ref)` y `error_relativo=error_absoluto/abs(x_ref)` permite detectar diferencias; **no** se exige igualdad exacta de dos hipótesis caloríficas distintas. Por ejemplo, los errores relativos de Fs para los tres casos de §4.72 frente a la referencia constante son ~1.36 %, ~1.42 % y ~1.21 %, mientras los balances energéticos internos cierran hasta precisión numérica. El test de presión crítica cruza `pcrit` con un factor `1±1e-6` y exige continuidad de Mach/velocidad; no valida experimentalmente una tobera real. Los casos sin expansión y con empuje negativo conservan diagnósticos verdaderos. Cantera, cuando existe, puede contrastar cp y **diferencias** de h/s de aire 78 % N2, 21 % O2 y 1 % Ar, previa conversión de unidades y referencias; no es una dependencia de producción.

**PYTHON.** `tests/test_verificacion_independiente_turborreactor_39.py` define `referencia_perfecta(*,mach,rp,eta_c,T3,delta,eta_t,eta_m,eta_n,eta_b,PCI,pi_d,T_amb,p_amb)`: recibe reales con Mach/eficiencias/relaciones [-], T3/T_amb [K], p_amb [kPa], PCI [kJ/kg combustible]; devuelve dict con `Tt0`, `pt0`, `p1`, `T2`, `p2`, `wc`, `f`, `T4`, `T4s`, `p4`, `pcrit`, `Te`, `pe`, `Ve`, `Me`, `rho`, `regimen`, `bruto`, `Fs`, `TSFC`, con K/kPa/kJ/kg/m/s/kg/(N h) según cada clave, y lanza `ValueError` si no existe expansión. Es llamada por `test_referencia_analitica_estatica_y_vuelo` y por el análisis de comparación; no llama a los modelos de producción. `comparar(valor_cp,referencia)` recibe valores finitos de la misma unidad y devuelve tupla `(error_absoluto, error_relativo)` [unidad original, adimensional], lanza `ValueError` si hay no finitos, protege la división por cero mediante `max(abs(referencia),1e-15)` y se llama en tests para comparar ambas formulaciones. `@unittest.skipUnless(importlib.util.find_spec('cantera'),...)` omite el contraste de propiedades cuando no se dispone de la librería; una omisión no cuenta como prueba superada. `unittest.mock.patch` sustituye temporalmente resultados de un solucionador para verificar reglas del filtro, sin contaminar producción. Las pruebas del grupo 39 contrastan balances, unidades, casos ideales, límites de f y tobera, exclusión de puntos y Pareto sintético. Véanse [milestone técnico 39](docs/milestones/39_verificacion_independiente_turborreactor_cp.md) y [aprendizaje 39](docs/milestones/39_verificacion_independiente_turborreactor_cp_APRENDIZAJE.md).

### 4.75. Primera interfaz web del turborreactor — milestone 40

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** La página `/turborreactor` presenta el solucionador con combustible de §4.72 como sistema propulsivo **distinto** del Brayton convencional: el trabajo de turbina se destina al compresor, y la tobera transforma entalpía total en velocidad de escape. El ambiente se prescribe mediante T/p estáticas directas o atmósfera ISA en altitud geopotencial (nunca simultáneamente); el vuelo subsónico produce presión/temperatura de remanso y pérdidas del difusor. Las estaciones de entrada exterior y escape se etiquetan **estáticas**; las de difusor, compresor, cámara y turbina son **de remanso**. La pérdida de cámara del formulario está en **porcentaje** y se divide por 100 para obtener la fracción de pérdida de presión total. Las tarjetas separan `(1+f)*Ve` y el empuje por presión, `V_inf` como resistencia entrante y `Fs` neto [N/(kg/s aire)]; `TSFC=3600*f/Fs` [kg/(N·h)] se deja indefinido si no hay empuje neto positivo. Sin gasto másico absoluto no existe empuje total en N. El dibujo de componentes muestra el eje compresor-turbina; las dos gráficas dinámicas muestran **sólo cuatro estados de remanso** de T [K] y p [kPa], sin mezclar los extremos estáticos. Los resultados, incluido el bloqueo sónico, siguen las hipótesis y límites del solucionador M37, no constituyen validación experimental.

**PYTHON — nuevas funciones y contratos.** `turborreactor_web.py` separa presentación de la ciencia y `web_app.py` incorpora una segunda ruta del **mismo** servidor Flask. Resumen de todas las firmas y su finalidad:

| Firma | Argumentos y tipos → retorno y unidades; errores; llamadas |
| --- | --- |
| `valores_turborreactor(formulario=None)` | `None` o mapping de entradas de usuario `str` → `dict[str,str]` sin unidades convertidas. La llama `web_app.turborreactor`; copia constantes o preserva entradas; sin cálculos físicos. Ej.: `valores_turborreactor()['mach']=='0'`. |
| `leer_turborreactor(valores)` | `dict[str,str]` → `dict` de números finitos con `mach,rp,eta_c,T3,delta,eta_t,eta_m,eta_n,pi_d,eta_b,PCI` y ambiente directo (`T_amb,p_amb`) o ISA (`altitud_geopotencial`); K, kPa, m, kJ/kg y fracciones. Lanza `ValueError` por combinación de modos, texto, no finitos, `%` fuera de `[0,100)` o `rp<=1` con mensaje específico **antes** de invocar M37; las demás restricciones se contrastan en el motor. La llama `simular_turborreactor`. Ej.: `leer_turborreactor(valores_turborreactor())['delta']==0.04`; con `rp='0'` lanza `ValueError('La relación de compresión rp debe ser mayor que 1.')`. |
| `simular_turborreactor(valores)` | Dict de cadenas → dict científico de M37 con ambiente, difusor, compresor, cámara, turbina, tobera, prestaciones y diagnósticos [K, kPa, kJ/kg, m/s, kg/(N·h)]. Llama al lector y **una sola vez** a `resolver_turborreactor_con_combustible(**argumentos)`; los errores físicos y numéricos se propagan a la ruta. Desde M45, si `gasto_masico_aire` contiene un número positivo [kg/s], añade `prestaciones_absolutas` y `dimensionamiento_tobera` sin recalcular el motor; con el campo vacío conserva las salidas específicas originales. Desde M46.1, valida `angulo_semidivergencia` [°] y, con caudal, añade `geometria_conica` (disponible sólo para C-D). Ej.: `simular_turborreactor(valores_turborreactor())['combustor']['f']≈0.028028`. |
| `estaciones_turborreactor(resultado)` | Resultado M37 → lista de seis `dict` (siete si existe estado de garganta C-D) con `nombre,tipo,T,p,h` (K, kPa, kJ/kg), `None` para salida de tobera inexistente. Usa `h` de `propiedades_aire` sólo para registrar estaciones ya resueltas. La llama `preparar_vista_turborreactor`. Ej.: `estaciones_turborreactor(r)[0]['tipo']=='Estático'`. |
| `svg_componentes(tipo_tobera="convergente")` | Tipo de tobera `str` → `str` SVG con cinco componentes y eje mecánico, sin datos termodinámicos ni errores habituales. La llama el preparador de vista. Ej.: `'Difusor' in svg_componentes()`. |
| `svg_evolucion(estaciones,clave,etiqueta,unidad)` | Lista de estaciones y tres `str` (clave `T`/`p`, nombre, unidad) → SVG `str` con eje y cuatro valores de remanso, no modelos termodinámicos. Se llama dos veces desde preparador; requiere estaciones físicas correctas. Ej.: `svg_evolucion(estaciones_turborreactor(r),'T','Temperatura total','K')`. |
| `preparar_vista_turborreactor(resultado)` | Dict M37 → dict con `estaciones`, `adaptacion_cd`, `datos_tobera_graficas` y los diez SVG previos (`svg_componentes`, `svg_temperaturas`, `svg_presiones`, `svg_empuje`, `svg_ts`, `svg_mach_tobera`, `svg_presion_tobera`, `svg_balance_energetico`, `svg_mach_perfil_tobera`, `svg_presion_perfil_tobera`), además de `balance_energetico` y `perfil_tobera`, que pueden ser `None` según disponibilidad. Desde M45 incorpora `svg_empuje_absoluto` [N]; M46.1 añade `svg_geometria_conica` [m] o `None`; M46.2 añade `perfil_axial_tobera`, `svg_mach_axial` y `svg_presion_axial` o `None`, sin recalcular el flujo. Llama a las funciones de estaciones, adaptación y dibujo; lo utiliza Flask sólo tras cálculo. Véanse §§4.81–4.87. Ej.: `preparar_vista_turborreactor(r)['estaciones']`. |
| `turborreactor()` | Controlador `@app.route('/turborreactor', methods=['GET','POST'])` sin argumentos Python (utiliza `request`); retorna `(HTML, 200/400)` generado por `render_template('turborreactor.html',...)`. GET no llama al motor; POST diferencia `accion='simular'`, `'sensibilidad'` y `'mapa'`, calcula el punto individual y, en las dos últimas, invoca `preparar_estudio` del M41; captura errores de rango, cálculo, dominio y aritmética sin mostrar trazas. El resultado de estudio y su error se guardan separados de los del cálculo individual. Prueba de uso: `app.test_client().get('/turborreactor').status_code == 200`. |

**PYTHON — interfaz y flujo.** El archivo `templates/turborreactor.html` ofrece el formulario original HTTP POST, Jinja de resultados y **seis paneles**: Configuración, Resultados, Estaciones, Visualizaciones, Sensibilidad y Mapas de prestaciones; los dos estudios nuevos se explican en §4.76. Cada panel alberga dos pestañas (uso y fundamentos): la teoría se distribuye mediante macros Jinja, sin formularios anidados. `static/turborreactor.css` reutiliza fuentes y variables de `static/style.css`, y `static/turborreactor.js` introduce mejora progresiva: cuando hay JavaScript, desactiva y vacía el otro modo de ambiente y carga tres ejemplos sin calcular. También **muestra exactamente un panel por vez** con `hidden`, y resalta sólo su enlace lateral con `aria-current='page'`. `location.hash` permite enlaces directos a `#configuracion`, `#resultados`, `#estaciones`, `#graficas`, `#sensibilidad`, `#mapa`; `history.pushState` registra cada navegación, mientras `popstate`/`hashchange` restauran la sección elegida con atrás/adelante del navegador. El identificador del panel inicial lo aporta Jinja mediante `data-initial-panel`: Configuración en GET/error de simulación, Resultados después de POST individual correcto, o Sensibilidad/Mapas después de solicitar el estudio (incluso con error propio de estudio). Los paneles ocultos permanecen en el mismo DOM y conservan campos y resultados; al cambiar por menú, se mueve el foco al encabezado visible para teclado. La rueda sólo desplaza el **contenido del panel activo**, no pasa a otro apartado. Sin JavaScript los seis paneles y ambas vistas de cada uno permanecen **apilados verticalmente** y los tres formularios HTTP POST siguen siendo utilizables (las entradas del motor para estudios son las ya reflejadas por el servidor). `request.form` es un mapping de cadenas; `float` convierte magnitudes e `isfinite` rechaza NaN/inf; `**argumentos` expande un dict a argumentos nombrados del motor. Jinja escapa las entradas por defecto. Sólo los SVG creados en servidor con números y etiquetas conocidas usan `|safe`. El enlace `/turborreactor` en `templates/index.html` está condicionado a **`modo_cp and modo_local`**, por lo que los informes históricos renderizados con `modo_cp=False` no lo incorporan ni cambian de formato. Las rutas `/`, `/informes/<nombre>` y descarga permanecen; la navegación del turborreactor se reduce a seis secciones, sin perder teoría.

**PYTHON — JavaScript y CSS accesibles.** En `static/turborreactor.js`, `elegir(id, moverFoco=false)` recibe un identificador de sección `string` y un indicador `boolean`, no devuelve un cálculo: para cada panel ejecuta `p.hidden=p.id!==id`, actualiza el único `aria-current` e, si el usuario inició el cambio, desplaza la vista al inicio y centra el foco en el título sin provocarle un nuevo salto de scroll. La función auxiliar `porUrl()` no recibe argumentos y retorna el identificador `string` extraído de `location.hash`. `sincronizarHistoria()` tampoco recibe argumentos ni retorna valores; se conecta a los eventos `popstate`/`hashchange` y llama a `elegir`. El callback `(evento)=>{...}` en cada enlace recibe un evento de clic: `preventDefault()` evita el salto nativo a un elemento oculto; `history.pushState` guarda un fragmento y `elegir` cambia pantalla. `document.body.dataset.initialPanel` permite inicializar correctamente GET, POST y errores, sin sesiones de servidor ni almacenamiento persistente. Las seis parejas de pestañas con `role='tab'` alternan dos paneles con `hidden`, `aria-selected`, `tabIndex` y navegación por flechas/Home/End, sin volver a calcular el motor; sin JS se ven ambas vistas. Los bloques explicativos `<details><summary>` se despliegan con ratón o teclado. Las regiones gráficas tienen `tabindex='0'`, `role='region'` y nombre accesible, y CSS `overflow-x:auto` más `min-width:660px` preservan texto legible en ventanas estrechas **dentro** del gráfico; los tres SVG mantienen sus mismas magnitudes y resultados. Los tres términos del empuje muestran ahora la unidad completa `N/(kg/s de aire)`. Los presets fijan `pi_d=1` (difusor ideal); referencias anteriores del M36/M37 con `pi_d=.97`/`.98` no corresponden exactamente a esos casos de interfaz.

**Comprobaciones y ejercicios.** Los ejemplos reproducibles con el formulario inicial dan Fs neto ≈958.257683 N/(kg/s) estático, ≈758.381570 a Mach 0.7 y ≈898.674568 a 10 km/Mach 0.5, con TSFC ≈0.105297, 0.126252 y 0.123240 kg/(N·h), respectivamente. En los tres casos la tobera convergente queda bloqueada; los valores proceden del solucionador original, no de la plantilla. La batería `tests/test_turborreactor_web_40.py` cubre POST/GET, modos incompatibles, salida indefinida, escape HTML, unidades, SVG, navegación por paneles, estados de GET/POST, educación y preservación del dashboard. Su inspección de estructuras HTML/JS no equivale a una revisión visual de un navegador real; esa comprobación deberá hacerse en Windows después de sincronizar. La prueba `test_revision_educativa_cp.test_una_sola_plantilla_principal` exige la presencia de `index.html`, `turborreactor.html` y `turborreactor_teoria_43.html`, sin excluir otras plantillas legítimas; conserva la comprobación de la galería cp(T) (detalle en §4.80). Experimenta con el porcentaje de presión de cámara y compara bruto/neto: no deduzcas empuje absoluto ni comportamiento real fuera de diseño. Detalles completos en [milestone 40](docs/milestones/40_integracion_web_turborreactor_cp.md) y [aprendizaje 40](docs/milestones/40_integracion_web_turborreactor_cp_APRENDIZAJE.md).

### 4.76. Sensibilidad y mapas de prestaciones web del turborreactor — milestone 41

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** La interfaz añade dos herramientas de exploración al solucionador científico de §§4.72–4.74, **sin cambiar ninguna ecuación del motor**. En Sensibilidad, OFAT (*One Factor At a Time*) cambia una sola variable y mantiene fijos los demás valores del formulario del turborreactor; se pueden variar `rp`, `T3`, Mach, `eta_c`, `eta_t`, `pi_d` y la pérdida de cámara `delta_pct` en porcentaje. Cada punto resuelve de nuevo compresor, combustible, acoplamiento de turbina y tobera. Se grafican `Fs` [N/(kg/s de aire)] y `TSFC=3600*f/Fs` [kg/(N·h)] cuando están definidos; además la tabla indica `f` [kg combustible/kg aire], `T4` de remanso [K] y `p4` total [kPa]. OFAT muestra dependencias parciales: no descubre por sí solo interacciones entre parámetros.

El mapa A barre `rp` y `T3` en un mismo ambiente y Mach y compara dos objetivos: **maximizar el empuje específico neto y minimizar el TSFC**. `frente_pareto()` del milestone 38 identifica puntos no dominados entre los estados físicamente `valido`; un punto A domina a B si `Fs_A>=Fs_B` y `TSFC_A<=TSFC_B`, con al menos una desigualdad estricta. El mapa B barre Mach y altitud ISA, modificando presión/temperatura exteriores, por lo que comunica extremos descriptivos pero **no** calcula Pareto global entre ambientes distintos. Ningún extremo discreto puede llamarse sin más óptimo continuo o global: puede quedar en frontera de la malla. Los estudios conservan `valido`, `empuje_no_positivo`, `sin_expansion`, `inadmisible` y `fallo_numerico` según M38/M39. Un `None` se representa por **—** o ×, no por cero; un Fs negativo calculado puede mostrarse en tabla, pero no se incorpora a los candidatos de Pareto. Estas son **mallas paramétricas** y no mapas reales de funcionamiento fuera de diseño de un motor.

**PYTHON — archivos y secuencia de ejecución.** `prestaciones_turborreactor_web.py` es un adaptador de controles y visualización, no un módulo científico. Se importa en `web_app.py` y se llama desde `turborreactor()` cuando `request.form['accion']` es `'sensibilidad'` o `'mapa'`. Primero `leer_turborreactor(valores_motor)` proporciona números finitos con ambiente mutuamente excluyente y convierte `%` de cámara a fracción. El adaptador valida selector/intervalos/tamaño **antes** de invocar el módulo M38; OFAT aprovecha una malla 1×1 de `barrer_rp_t3([rp],[T3],**fijos)` por cada muestra, reusando clasificación y métricas; el mapa A llama directamente a `barrer_rp_t3(xs,ys,...)` y B a `barrer_mach_altitud(xs,ys,...)`. M38 llama internamente al solucionador con combustible M37 y a `frente_pareto` solo cuando el ambiente es comparable. Las muestras OFAT admiten 2–31 (11 por defecto); las mallas 2–15 por eje (5×5 por defecto, máximo 225), con límites web rp 1.01–40, T3 200–2000 K, Mach 0–0.95, eficiencias ηc/ηt 0.2–1, πd 0.5–1 y δ 0–30 %. Son **límites de interacción educativos**, no límites certificados de una turbina. El estudio B siempre usa ISA 0–20 km; el mapa A conserva el modo de ambiente configurado. Un error de formulario produce HTTP 400 y conserva valores introducidos.

**PYTHON — funciones nuevas y contratos completos** (los auxiliares `_...` solo son usados dentro del adaptador, salvo en pruebas). Los parámetros `str` proceden de HTML; las unidades indicadas pertenecen a los reales **después** de su conversión.

| Firma | Entrada / retorno / unidades; validaciones, llamadas y uso |
| --- | --- |
| `valores_estudios(formulario=None)` | `None` o mapping `str→str` → dict de cadenas de configuración OFAT/mapa, con valores por defecto y texto original aunque sea erróneo; llamada por Flask y `preparar_estudio`. Ej.: `valores_estudios()['sens_n']=='11'`. No calcula magnitudes físicas. |
| `_real(valores, clave, minimo, maximo)` | Dict de cadenas, clave y límites float de la misma unidad → float finito; llama a `float` e `isfinite`, levanta `ValueError` por texto, infinito o rango. Llamada por `_eje`; ej.: `_real({'x':'0.9'},'x',0,1)==.9`. |
| `_entero(valores, clave, minimo, maximo)` | Dict de cadenas, nombre y límites enteros → int; `ValueError` si `int(...)` falla, se indica `3.5` o se excede límite. Lo llama `preparar_estudio`; ej.: `_entero({'n':'5'},'n',2,15)==5`. |
| `_eje(valores, clave_min, clave_max, limite_min, limite_max, n)` | Diccionario de texto, nombres de extremos, límites float, número entero `n>=2` → lista creciente `list[float]` en la unidad del parámetro; prohíbe min≥max o fuera de límites; llama a `_real` y lo invoca `preparar_estudio`. Ej.: `_eje({'a':'1','b':'3'},'a','b',0,5,3)==[1,2,3]`. |
| `_argumentos_comunes(datos)` | Dict numérico M40 → nuevo dict con `eta_c,eta_t,eta_m,eta_n,eta_b,PCI,pi_d,delta` ([-], PCI en kJ/kg); selecciona claves, no modifica el origen; lo llama `preparar_estudio`. Ej.: `_argumentos_comunes(datos)['PCI']==43000`. |
| `_ambiente_mapa(datos)` | Dict numérico con ambiente directo K/kPa o ISA en m → dict con **solo** `T_amb,p_amb` o `altitud_geopotencial`; lo llama `preparar_estudio`. Ej.: `{'T_amb':288.15,'p_amb':100}` cuando esos campos están en `datos`. |
| `_base_svg(ancho, alto, cuerpo, descripcion)` | Dos dimensiones enteras SVG, lista `str` de elementos, texto descriptivo → `str` SVG con atributos de anchura, altura, `viewBox` y `aria-label` escapada con `html.escape`; lo llaman los generadores de gráfica; ej.: `'<svg' in _base_svg(100,80,[],'gráfica')`. |
| `_svg_curva(puntos,parametro,unidad_x,clave,titulo,unidad_y)` | Lista de puntos `{valor_parametro:float,punto:dict M38}`, cinco strings de clave/etiquetas/unidades → SVG `str` con ejes, círculos y polilíneas **interrumpidas** ante estados no válidos; muestra ×, no utiliza `None` como 0. Lo llama `preparar_estudio`; ej.: `_svg_curva(r['puntos'],'rp','–','Fs','Empuje','N/(kg/s)')`. |
| `_color(valor,minimo,maximo,clave)` | Tres floats finitos de una magnitud homogénea y `clave` de resultado → cadena CSS `hsl(...)`, mayor valor más intenso (escala normalizada con protección de valores iguales), sin cálculo físico; lo llama `_svg_mapa`. Ej.: `_color(5,0,10,'Fs')`. |
| `_svg_mapa(mapa,clave,titulo)` | Dict completo M38, `clave='Fs'` o `'TSFC_kg_N_h'`, etiqueta → SVG `str` con ejes, cifras, leyenda, títulos emergentes de celdas y × para ausencias; llama a `_color`, `_base_svg`, lo invoca `preparar_estudio`. Ej.: `'<rect' in _svg_mapa(mapa,'Fs','Empuje')`. |
| `_svg_pareto(mapa)` | Dict M38 de rp–T3 comparable → `str` SVG de dispersión sobre TSFC [kg/(N·h)] y Fs [N/(kg/s aire)], anillos sobre puntos no dominados; si no hay válidos devuelve mensaje SVG. Lee `mapa['pareto']` (no recalcula dominancia), llama `_base_svg`, se usa **solo** desde mapa A. Ej.: `_svg_pareto(mapa)`. |
| `preparar_estudio(accion, formulario, valores_motor)` | Acción `str` `'sensibilidad'`/`'mapa'`, mapping de texto con rangos y dict de texto M40 → dict de presentación. OFAT: `{tipo,parametro,etiqueta,unidad,puntos,grafico_Fs,grafico_TSFC,cuenta_validos,total}`; mapa: `{tipo,nombre,datos,grafico_Fs,grafico_TSFC,grafico_pareto,filas}`. Reutiliza `leer_turborreactor`, `_entero`, `_eje`, los filtradores, barridos M38 y los tres SVG; `ValueError` por datos o acciones inválidas; la llama `web_app.turborreactor`. Ej.: `preparar_estudio('sensibilidad',{'sens_n':'3','sens_min':'5','sens_max':'15','sens_parametro':'rp'},valores_turborreactor())['total']==3`. |

**PYTHON — estructura de formulario y conceptos.** `templates/turborreactor.html` incluye **tres formularios hermanos** (simulación, OFAT, mapa) para evitar HTML anidado; los dos estudios envían su `accion` y los valores del motor como `input type='hidden'`. El callback de `submit` en `static/turborreactor.js` utiliza `querySelectorAll('input[data-motor-field]')` y `forEach` para copiar los valores editados *antes* de enviarlos. Sin JS se envían los últimos valores del servidor (primero ejecutar «Simular» si se editaron campos nuevos). Otro callback de `change` ofrece intervalos sugeridos para el parámetro OFAT y la función local `mostrarMapa()` (sin argumentos ni retorno) oculta el fieldset no elegido; Python valida sólo los controles activos. `data-initial-panel` elige la pantalla del estudio tras POST conservando su error/resultado. El estado del formulario individual también se vuelve a calcular para mantener visibles Resultados/Estaciones. El CSS conserva desplazamiento horizontal **dentro de SVG enfocados por teclado** y el documento no se ensancha. `tests/test_prestaciones_turborreactor_web_41.py` contrasta integración, referencias M38, estados físicos, límites, acceso al dashboard Brayton e inmutabilidad del historial; GitHub Actions añade la ejecución individual antes de la suite completa.

**Ejercicio y verificación realizada.** Con los valores por defecto `eta_c=.85,delta=.04,eta_t=.9,eta_m=.98,eta_n=.95,eta_b=.99,PCI=43000`, realiza A: rp=[5,7.5,10,12.5,15] y T3=[1400,1500,1600,1700,1800] K con T∞=288.15 K, p∞=100 kPa, Mach=0, πd=1. Se obtiene Fs máximo ≈1077.684377 y TSFC mínimo ≈0.086202290 con **7 no dominados**. Para B, con Mach=[0,.2,.4,.6,.8], altitud ISA=[0,5000,10000,15000,20000] m, rp=10, T3=1600 K y **πd=.98** (distinto del preset M40 πd=1), Fs máximo ≈1030.247814 y TSFC mínimo ≈0.105830471, sin Pareto global. C, OFAT rp=[4,6,8,10,12,14,16,18,20] con T3=1600 K y mismo ambiente A, tiene Fs máximo en rp=14, TSFC mínimo en rp=20 y cuatro puntos no dominados si se evaluase Pareto sobre esos puntos. Las **25 pruebas M41** y **27 pruebas M40** se ejecutaron individualmente; la suite global de **557 pruebas** finalizó en Linux/Python 3.12 con **548 correctas, nueve omitidas y cero fallos**. Son contrastes reproducibles de implementación, **no validación experimental**. Faltan geometría, caudal másico absoluto, química y composición real, mapas de componentes, régimen fuera de diseño y ensayos de motor. Véanse [milestone 41](docs/milestones/41_prestaciones_web_turborreactor_cp.md) y [aprendizaje 41](docs/milestones/41_prestaciones_web_turborreactor_cp_APRENDIZAJE.md).

### 4.77. Tobera convergente-divergente ideal con cp(T) — milestone 42.A

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** El nuevo módulo `tobera_convergente_divergente_cp.py` es **independiente**: ni la web ni los motores de §§4.69–4.76 lo importan todavía. Tampoco reemplaza la tobera exclusivamente convergente de §4.70. Para remanso `Tt,pt`, contrapresión `p_amb` [kPa] y geometría `epsilon=Ae/Ag>=1`, aplica `h(Tt)=h(T)+V²/2000` con h [kJ/kg] y `s(T,p)=s(Tt,pt)` con s [kJ/(kg K)]; obtiene `V=sqrt(2000*(h(Tt)-h(T)))` [m/s], `a=sqrt(gamma(T)*R_AIRE*T)` y `G=rho*V` [kg/(m² s)] con `rho=1000*p/(R_AIRE*T)` [kg/m³]. En la garganta bloqueada `Mg=1`, `Gg=G*` y `Ag=A*`, por lo que `epsilon=G*/Ge`. En flujo no bloqueado `Mg<1` y **Ag no es A\***. La ecuación `dA/A=(M²-1)dV/V` explica que el divergente acelera cuando `M>1`. Para una misma relación de áreas existen una raíz subsónica y otra supersónica: elegir una sin contrapresión ni régimen físico induce errores.

**INTERPRETACIÓN FÍSICA / INGENIERÍA — diagnósticos.** La salida ideal adaptada cumple `pe=p_amb`, la subexpandida `pe>p_amb`, la sobreexpandida `pe<p_amb`. El empuje específico de **tobera aislada** es `Fs=Ve+1000*(pe-p_amb)/(rho_e*Ve)` [N/(kg/s)=m/s]; no presupone caudal absoluto, no resta velocidad del avión y no equivale al empuje neto del turborreactor web. Una garganta bloqueada **no garantiza** una salida supersónica: el modelo 42.C calcula choques normales internos o de salida con conservación y aumento de entropía. El umbral `umbral_choque_salida_aproximado` conserva su nombre histórico pero ahora se calcula con el solucionador cp(T) y no con gamma local congelada. Debajo de ese umbral se mantiene la **rama supersónica ideal**, sin modelar choques exteriores, separación ni fricción. El aire de composición fija y las correlaciones `200–2000 K` excluyen extrapolar gases de combustión reales. La verificación numérica/analítica no es validación experimental.

**PYTHON — funciones, entrada y ejecución.** No hay nuevo consumidor en producción: las dos funciones públicas las invocan directamente las pruebas y las puede utilizar código Python futuro. `resolver_tobera_convergente_divergente(Tt, pt, p_amb, epsilon)` recibe cuatro reales finitos no booleanos (K, kPa, kPa, ratio [-]), valida `200<Tt<=2000`, `pt>p_amb>0`, `epsilon>=1`, y devuelve `dict` con `regimen: str`, `resuelto: bool`, `diagnostico: str|None`, entradas, temperaturas y presiones de garganta/salida [K,kPa], Mach [-], densidades [kg/m³], velocidades [m/s], flujos por área [kg/(m² s)], `area_salida_por_caudal` [m²/(kg/s)], presiones crítica y diferencia [kPa], `adaptacion: str|None`, empuje de momento, presión y total [N/(kg/s)] y residuos de energía [kJ/kg], entropía [kJ/(kg K)] y masa [kg/(m² s)]. En ramas no resueltas los campos de salida, empuje y residuos son `None`, no ceros. `relacion_areas_adaptada(Tt, pt, p_amb)` recibe K,kPa,kPa y devuelve `float epsilon>1` para `Me>1` y `pe=p_amb` con cp(T). `ValueError` señala entradas o pretensión subsónica de adaptación supersónica; `EstadoFueraDeRango` señala temperatura requerida fuera de 200–2000 K; `ErrorNumericoCiclo` señala una raíz fuera de la rama o falta de convergencia. Ejemplo: `epsilon=relacion_areas_adaptada(1200,500,70)` da ≈1.652764798; `resolver_tobera_convergente_divergente(1200,500,70,epsilon)['mach_salida']` da ≈1.939449112. Para `p_amb=400`, el mismo caso devuelve `resuelto=False` y `empuje_especifico_total=None`, sin estado inventado.

**PYTHON — auxiliares y conceptos.** `_validar(Tt,pt,p_amb,epsilon)` devuelve `None` o lanza `ValueError` al comprobar con `isinstance(Real)`, `isfinite` y un control específico de `bool`; lo llaman las dos públicas. `_estado(T,Tt,pt)` convierte K,K,kPa en un `dict` estático (`T,p,V,a,M,rho,G`) usando `h,s0,gamma` existentes; lo usan `_sonico`, `_salida_area` y las funciones públicas. `_sonico(Tt,pt)` devuelve ese dict para M=1 o `None` si no existe antes de 200 K; `_temperatura_para_presion(Tt,pt,p)` devuelve T [K] o `EstadoFueraDeRango`, invirtiendo s0 a presión fija. Ambos usan `_biseccion(funcion,inferior,superior,*,iteraciones=110)`, que recibe un callback real→real, un intervalo numérico y un máximo entero como **argumento solo de palabra clave** después de `*`; devuelve `float` y lanza `ErrorNumericoCiclo` sin cambio de signo. `_salida_area(Tt,pt,critico,epsilon,*,supersonica)` escoge expresamente la raíz de `G(T)=G*/epsilon` por su intervalo térmico y devuelve dict de estado, o excepción de dominio/raíz; recibe K,kPa,dict,ratio y booleano de rama, y lo llama el solucionador principal. `_resultado(Tt,pt,p_amb,epsilon,critico,garganta,salida,regimen,*,motivo=None,umbral_choque=None)` arma el dict homogéneo desde reales, estados dict/None, cadena y diagnósticos; lo llama el solucionador principal. La bisección monótona sin derivadas evita saltar fuera del dominio; `None` preserva la diferencia entre **física no resuelta** y valor cero. Los métodos de `tests/test_tobera_convergente_divergente_42a.py` verifican continuidad de masa, energía, entropía y rama, frontera de bloqueo, rechazo de extrapolación, comparación de gas perfecto con fórmula área–Mach independiente y compatibilidad M35. **19 tests específicos correctos tras revisión (16 iniciales + 3 nuevos). La suite final tiene 576 pruebas, 575 correctas, una omitida (Cantera opcional) y ninguna fallida; los 573 casos anteriores correspondían a la versión previa.** Más detalles y experimentos en [técnico 42.A](docs/milestones/42a_tobera_convergente_divergente_cp.md) y [aprendizaje 42.A](docs/milestones/42a_tobera_convergente_divergente_cp_APRENDIZAJE.md).

**PYTHON — revisión de entradas extremas.** `_validar` captura `OverflowError`, `TypeError` y `ValueError` de `isfinite(x)` mediante `try/except`: un entero arbitrariamente grande como `10**10000` no se puede convertir implícitamente a float, y ahora genera el `ValueError` contractual; `bool`, texto, NaN e infinito siguen rechazados. Los tests ejercitan las cuatro posiciones de entrada y las tres de la función inversa.

**INTERPRETACIÓN FÍSICA / INGENIERÍA — choque y estado parcial.** En la rama `choque_interno_o_salida_no_resuelto`, el estado de garganta **sí** se conoce por bloqueo: se pasa `critico` como `garganta` a `_resultado` y se conservan `Tg,pg,rhog,Vg,Mg=1`. Solo `salida` continúa `None`; los residuos que dependen de ella y el empuje también permanecen indefinidos. El umbral `p_choque_salida_aproximado` congela gamma local en la fórmula de choque perfecto: los tests próximos al umbral verifican la clasificación **programada**, no una frontera exacta para cp(T). La referencia de gas perfecto invierte ahora **independientemente** la fórmula `A/A*(M)` por bisección dentro del test para comparar Mach supersónico a 600 K; la tolerancia relativa del 3 % reconoce modelos caloríficos distintos, sin implicar validación experimental.

### 4.78 — Integración web de tobera C-D (milestone 42.B)

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** La convergente conserva el modelo
histórico con ηn. La convergente-divergente C-D impone `epsilon=Ae/Ag≥1` y
expansión isentrópica ideal `cp(T)`: el parámetro `eta_n` **se valida** como
fracción física `0<eta_n≤1` por compatibilidad de la API, pero **no interviene**
en las ecuaciones C-D, cuya eficiencia ideal efectiva es 1. La garganta
puede estar bloqueada (M=1) mientras un choque normal interno ya resuelto
reduce el Mach de salida y la presión total (véase §4.79). Cuando el dominio
no permite resolverlo, `Fs` y `TSFC` quedan en `None`, no en cero. En mapas,
esos casos conservan el estado separado `tobera_no_resuelta`; `sin_expansion` se reserva
para falta de margen total de presión. El empuje conocido se calcula como
`(1+f)*(Ve+1000*(pe-p_amb)/Ge)-Vinf` en N/(kg/s de aire), con `Ge=ρe Ve`;
`TSFC=3600*f/Fs` sólo para Fs positivo.

**PYTHON: firmas y flujo de llamada.** `resolver_turborreactor_con_combustible(
mach,rp,eta_c,T3,delta,eta_t,eta_m,eta_n=1,pi_d=1,eta_b=.99,PCI=43000,*,
T_amb=None,p_amb=None,altitud_geopotencial=None,tipo_tobera="convergente",
epsilon=1.5)` recibe magnitudes adimensionales salvo K, kPa y PCI [kJ/kg].
Valida `eta_n` en ambos modos, `epsilon≥1` en C-D y todos los dominios ya
existentes; puede lanzar `ValueError`, `EstadoFueraDeRango` o
`ErrorNumericoCiclo`. Mantiene su diccionario previo de componentes, empuje
y diagnóstico; para una C-D no resuelta conserva `tobera` con garganta
calculada y deja prestaciones no calculables en `None`.
`leer_turborreactor(valores: dict[str,str]) -> dict` transforma textos del
formulario en parámetros físicos, exige `eta_n` numérico y finito en ambos
modos y delega al solucionador con
`simular_turborreactor(valores)`. El servidor muestra `ValueError` en pantalla;
el navegador mantiene visible y editable `eta_n` también en C-D y sólo oculta
el campo geométrico `epsilon` cuando corresponde, sin alterar las ecuaciones.

**PYTHON: `_presion_adaptacion_cd(Tt, pt, epsilon) -> float`** devuelve la
contrapresión ideal de adaptación [kPa] a partir de remanso [K, kPa] y
relación de áreas adimensional. Usa `_sonico()` de 42.A para conocer `p*`,
y `relacion_areas_adaptada()` para evaluar la relación física, sin duplicar
la relación área–Mach. Para `epsilon=1`, devuelve `p*` directamente. Para
`epsilon>1`, el extremo inferior del intervalo es la menor presión admisible
en 200 K (con un pequeño margen) y su área debe ser **mayor o igual** al
objetivo; el extremo superior es `p*`, cuyo área límite es 1, inferior al
objetivo. La función es monótona decreciente en la rama supersónica. La
bisección conserva la solución entre ambos extremos y verifica el residuo
`abs(Ae/Ag calculada - epsilon)` antes de retornar. El algoritmo previo
partía de la *primera presión válida* de la rama supersónica, que podía
tener un área mayor que el objetivo, sin demostrar que encerrase la raíz:
devolvía presiones equivocadas cerca de `epsilon=1`. Para `Tt=1200 K`,
`pt=500 kPa` y `epsilon=1.001`, la presión correcta es `259.119611 kPa`,
con área reconstruida `1.0010000001`. `ValueError` cubre entradas no reales,
no finitas, relación inválida, límite inferior del aire y falta de
convergencia; pueden propagarse excepciones físicas de 42.A.

**PYTHON: `_adaptacion_cd(resultado: dict) -> dict|None`** la llama
`preparar_vista_turborreactor(resultado)` desde la ruta Flask. Devuelve
`presion_adaptada`, `epsilon_adaptada` y dos campos de error textual, o
`None` si no existe tobera C-D. Evalúa la relación inversa pública de 42.A
para el ambiente actual; controla fallos físicos sin inventar presiones.
`mapas_prestaciones_turborreactor_cp._punto(...)` usa el estado
`tobera_no_resuelta` y sus entradas/resultado conservan la garganta; no
participa en óptimos, Pareto ni TSFC. `prestaciones_turborreactor_web`
agrega su etiqueta a `ESTADOS_WEB` para tablas, máscaras y estadísticas.
Por ejemplo, `_presion_adaptacion_cd(1200,500,1.001)` produce aproximadamente
`259.119611`; `_presion_adaptacion_cd(1200,500,1e8)` lanza `ValueError`
porque la geometría excede el dominio del aire.

Verificación del software: inversiones directas/inversas, límites, legado,
API y regresión de mapas; no se ha efectuado validación contra ensayos de
toberas o turborreactores. Véanse el [documento técnico 42.B](docs/milestones/42b_integracion_web_tobera_cd_cp.md)
y su [aprendizaje](docs/milestones/42b_integracion_web_tobera_cd_cp_APRENDIZAJE.md).

### 4.79 — Choque normal y flujo posterior en la tobera C-D (milestone 42.C)

**Correcciones finales tras revisión independiente:** dos textos de
interfaz ahora reconocen la resolución de choques normales; los choques
oblicuos y las pérdidas viscosas siguen excluidos. En un choque interno,
`choque_normal.generacion_entropia` [kJ/(kg·K)] representa el incremento
físico positivo, mientras que `residuo_entropia_salida` compara la salida
con `s(Tt, pt2)` (presión total aguas abajo), por lo que debe ser cercano
a cero. Las fronteras cercanas a `Ae/Ag=1` emplean tolerancias acotadas
por la anchura del intervalo físico de contrapresiones. Las nuevas pruebas
ejercitan esa región y verifican en Flask las magnitudes y unidades del
bloque visual de choque.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** El choque normal es una discontinuidad
adiabática cuasiunidimensional: `rho1*V1=rho2*V2` [kg/(m²·s)],
`p1+rho1*V1²/1000=p2+rho2*V2²/1000` [kPa] y
`h(T1)+V1²/2000=h(T2)+V2²/2000` [kJ/kg]. La entalpía total se conserva;
la entropía aumenta y la presión total posterior disminuye. Se calcula
`Achoque/Ag`, nunca una posición axial [m] sin geometría `A(x)`.
La corriente se expande supersónicamente hasta el choque, experimenta el
salto y continúa en la rama subsónica isentrópica hasta la salida. Para
`Tt=1200 K`, `pt=500 kPa`, `Ae/Ag=1.5`, `pamb=350 kPa` se obtiene
`Achoque/Ag≈1.36206`, `pe≈350 kPa`, `Me≈0.54316` y empuje específico
de tobera ≈`358.658 N/(kg/s)`; son resultados del modelo, no ensayos.
No se calculan choques oblicuos, separación de capa límite ni fricción.

**PYTHON — nuevo solucionador.** `choque_normal_cp.resolver_choque_normal(T1,
p1,V1,*,tolerancia=1e-9) -> dict` recibe temperatura estática [K], presión
estática [kPa], velocidad [m/s] y tolerancia numérica relativa [-]. Comprueba
reales finitos, dominio del aire y `M1>1`. Encuentra `Tt` con `T_desde_h`,
construye `p2(T2)` de la ecuación de cantidad de movimiento, y mediante
bisección en la rama subsónica impone continuidad de masa y ecuación de
estado. Devuelve `T1,p1,V1,M1,rho1,T2,p2,V2,M2,rho2,Tt,pt1,pt2`, pérdida
de presión total [kPa], entropía generada [kJ/(kg·K)], flujo superficial
[kg/(m²·s)] y diccionario `residuos` (masa, momento, energía).
Lanza `ValueError` para entradas inválidas, `EstadoFueraDeRango` para
temperaturas imposibles y `ErrorNumericoCiclo` si no queda una solución física
con residuos pequeños. Ejemplo: `resolver_choque_normal(763.6539,84.12215,
995.2389)['M2']` es aproximadamente `0.60473`. Importa `h`, `s`, `s0`,
`gamma`, `R_AIRE` y `T_desde_h` de los módulos existentes; lo llama
`_salida_tras_choque` y también los tests de 42.C.

**PYTHON — área y contrapresión.** `_salida_tras_choque(Tt,pt,critico,
epsilon,area_choque) -> (dict,dict)` recibe K, kPa, estado crítico, Ae/Ag
y Achoque/Ag [-]; invoca `_salida_area` supersónica, el solucionador de
choque y una nueva inversión isentrópica de flujo a la salida con `pt2`.
`_choque_en_divergente(Tt,pt,p_amb,epsilon,critico) -> (dict,dict)` busca por
bisección la relación `Achoque/Ag` entre 1 y `epsilon`, comparando las
contrapresiones de los extremos antes de iterar; lanza `ValueError` cuando
la contrapresión queda fuera de esta rama. Ambas funciones son auxiliares
llamadas por `resolver_tobera_convergente_divergente`. Su resultado público
incluye `choque_normal` (dict o `None`) y `relacion_areas_choque` [-]. Para
estado no resuelto preserva la garganta y no inventa empuje.

**PYTHON — integración.** `combustible_cp_variable.py` utiliza la salida
resuelta sin nuevas eficiencias; `mapas_prestaciones_turborreactor_cp._punto`
marca `motivo='choque_normal_resuelto'` para conservar `estado='valido'` en
optimizaciones. Los SVG de `prestaciones_turborreactor_web.py` destacan
visualmente esos puntos y `templates/turborreactor.html` muestra ambas
caras del choque, pérdida de presión total y entropía generada. La
calculadora 42.B sigue siendo *isentrópica ideal*. Las pruebas específicas
comparan conservación, gas perfecto independiente, fronteras y regresión;
no constituyen validación experimental. Véanse [documento técnico](docs/milestones/42c_choque_normal_tobera_cd_cp.md)
y [aprendizaje](docs/milestones/42c_choque_normal_tobera_cd_cp_APRENDIZAJE.md).

### 4.80 — Milestone 43: interfaz educativa del turborreactor por apartado

**PYTHON / JINJA — estructura sin duplicar cálculos.**
`templates/turborreactor.html` mantiene **seis secciones funcionales**:
configuración, resultados, estaciones, gráficas, sensibilidad y mapa. Cada
una contiene `div[data-edu-tabs]`, dos botones `role="tab"` y dos paneles
`role="tabpanel"` con `aria-controls` / `aria-labelledby` y `id` únicos.
La teoría ya no es un séptimo destino de navegación: se encuentra junto a
la función que explica. El HTML conserva los tres formularios POST
separados (sin formularios anidados). Sus valores y datos del motor proceden
de las mismas funciones de siempre; ninguna fórmula física se calcula en
la plantilla. La única acción principal del formulario individual es
«Simular turborreactor»; la misma respuesta incluye automáticamente la
calculadora de adaptación C-D mediante `_adaptacion_cd(resultado)` cuando
corresponde. La antigua acción HTTP `adaptacion` sigue admitida para
compatibilidad, aunque ya no tiene botón propio.

**JINJA — macros de contenido.** `templates/turborreactor_teoria_43.html`
define `configuracion()`, `resultados()`, `estaciones()`, `graficas()`,
`sensibilidad()` y `mapa()`: las seis macros no tienen argumentos, devuelven
fragmentos HTML seguros redactados por el proyecto y no tienen unidades de
salida ni validación de entradas porque son exclusivamente *presentación*.
La sentencia `{% import 'turborreactor_teoria_43.html' as teoria %}` importa
sus nombres en un espacio separado. Por ejemplo, `{{ teoria.resultados() }}`
inserta las explicaciones de Fs, TSFC, dosado, escape y tobera junto a los
indicadores calculados en el panel vecino. Las macros no llaman al motor
ni conocen `resultado`: física y representación permanecen separadas.

**JAVASCRIPT — pestañas accesibles.** Al cargar, el manejador existente de
`DOMContentLoaded` recorre los seis grupos con `querySelectorAll` y crea
las funciones locales `activar(index,enfocar=false)` (índice `number`,
bandera `boolean`, sin valor de retorno). Lee los botones `role="tab"`,
localiza sus paneles por `aria-controls` y alterna `hidden`, `aria-selected`
y `tabIndex`; `click`, flechas izquierda/derecha, `Home` y `End` manejan
el cambio y el foco. Es una acción de DOM, no una llamada Flask. Con JS
ausente las dos vistas están presentes una tras otra; con JS, la clase
`.js` activa los estilos de pestañas de `static/style.css`. El estado de
sección sigue en `location.hash` y el estado de pestaña es local al DOM:
los POST recargan la vista «Uso» del apartado solicitado, preservando los
resultados en el HTML. Ejemplo: tras simular, abre `#resultados` y pulsa
«Fundamentos teóricos y procesos» para leer la explicación del empuje,
sin recalcular nada.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Resultados distingue empuje bruto,
neto y resistencia de entrada, (f) [kg/kg], TSFC [kg/(N·h)] y velocidad
de escape; la zona de tobera interpreta garganta sónica, choque, presión
de adaptación y límites de Ae/Ag. Estaciones diferencia propiedades
estáticas/totales a través de difusor, compresor, cámara, turbina y
tobera. Los gráficos comparan estaciones discretas, OFAT modifica un
parámetro y mapas dos; ni las curvas ni los mapas sustituyen ensayos.
No se ha incorporado caudal másico ni empuje absoluto, y las ecuaciones
de `cp(T)` y la resolución de choque siguen intactas. Las pruebas HTML
del milestone verifican estructuras y resultados; una prueba automatizada
de estructura no sustituye revisión visual real de escritorio/móvil.
**Precisión física de la presentación.** El selector usa «Convergente-divergente (C-D)», sin atribuir reversibilidad a todo el flujo. Las regiones continuas son ideales e isentrópicas; los choques normales internos o en la salida conservan masa, cantidad de movimiento y energía, pero generan entropía y reducen presión total. El modelo puede dar salida subsónica o supersónica y mantiene sus límites físicos/numéricos. `eta_n` se valida por compatibilidad, pero no interviene en C-D. Una prestación `None` significa no disponible, no cero ni necesariamente un choque sin resolver; se conserva el diagnóstico específico de la tobera.

**PYTHON — contrato flexible de plantillas.** El método existente `test_una_sola_plantilla_principal(self)` no recibe entradas externas ni devuelve magnitudes (retorno `None`, sin unidades); lo invoca `unittest` por descubrimiento. `necesarias` y `disponibles` son conjuntos de nombres únicos obtenidos con `Path.glob`. `necesarias.issubset(disponibles)` comprueba inclusión: `{'index.html'}.issubset({'index.html','otra.html'})` es verdadero. Si falta una requerida, `assertTrue` falla y `sorted(necesarias - disponibles)` muestra los nombres ausentes. Se mantiene `assertIn` para la galería Brayton; permitir otra plantilla no relaja esa integridad.

**CSS — navegación estrecha del turborreactor.** M43 activa la clase `js` para sus pestañas. A ≤760 px, una regla específica en `static/turborreactor.css` mantiene `.section-nav` visible con `display:flex`, porque esta página no usa el botón de menú plegable de Brayton. La regla no cambia el dashboard ni el modelo físico.

**PYTHON — recuperación y portabilidad final.** El método histórico `test_rutas_malformadas_symlink_e_informe_incompleto` conserva las verificaciones de rutas e informes aunque Windows no pueda crear el alias (error 1314); solo los dos subcasos que dependen realmente del enlace simbólico se marcan como omitidos mediante `subTest`/`skipTest`. El método `test_recuperacion_cuatro_informes_descarga_identica_sin_recalculo` conserva un `bytes` leído antes de la petición de descarga y comprueba `descarga.data == bytes_guardados` y que `ruta.read_bytes()` no cambie. Evita confundir igualdad textual con conservación byte a byte cuando hay saltos CRLF. Estas pruebas no alteran los informes ni los modelos físicos. Su regresión final está pendiente porque el entorno actual no dispone de Flask/Jinja2 y, por instrucción, no se instalaron dependencias.

Documentos: [técnico 43](docs/milestones/43_interfaz_educativa_turborreactor.md)
y [aprendizaje 43](docs/milestones/43_interfaz_educativa_turborreactor_APRENDIZAJE.md).

### 4.81 — Milestone 44.1: dos gráficos educativos del turborreactor

**FÍSICA — misma solución, otras representaciones.** El empuje específico
neto [N/(kg/s de aire)] es la suma del momento de escape `(1+f)Ve`, la
contribución de presión de tobera —ambas ya normalizadas por el solucionador—
y la entrada negativa `−V0`. El combustible está incluido una sola vez. Si
falta el estado de salida, no se puede dibujar un valor de cero ficticio.
El T–s usa `propiedades_aire.s(T,p)` [kJ/(kg·K)], con `cp(T)` variable y
presión en kPa, para estados de remanso 1–4. Solo cuando existe solución de
tobera se añade el estado de escape **estático** `E`. Las líneas discontinuas
son conexiones esquemáticas de estados; no describen trayectorias, geometría
axial ni una entropía química rigurosa de combustión.

**PYTHON — contratos y errores.** En `turborreactor_web.py`,
`datos_empuje_grafica(resultado)` recibe el `dict` del solucionador y retorna
`(salida, -entrada, presion, neto)` con cuatro `float` en
N/(kg/s de aire), o `None` si alguna magnitud falta, no es real o no es finita. Comprueba el cierre de
la suma con escala relativa `1e-8` y lanza `ValueError` si el resultado es
incoherente. `svg_descomposicion_empuje(resultado, *, absoluto=False)` recibe el mismo diccionario
y retorna una cadena SVG o `None`. `datos_ts_turborreactor(estaciones)`
recibe la lista de dicts con `nombre`, `tipo`, `T` [K] y `p` [kPa], y retorna
tuplas `(nombre, entropia, T, tipo)` para los cuatro estados de remanso y
opcionalmente la salida estática. Lanza `ValueError` si faltan las cuatro
estaciones requeridas. `svg_ts_turborreactor(estaciones)` convierte esos
puntos discretos en un SVG textual. `svg_descomposicion_empuje` llama a
`datos_empuje_grafica`; `svg_ts_turborreactor` llama a `datos_ts_turborreactor`,
y esta última a `s(T,p)`. `preparar_vista_turborreactor` llama a ambas funciones
SVG y añade `svg_empuje` y `svg_ts` al contexto existente; las plantillas solo
los muestran con descripciones y etiquetas accesibles. Ninguna nueva función
modifica los estados físicos o resuelve ecuaciones nuevas.

**PYTHON — lectura del código y uso.** `valores = [p.get(clave) for clave in
claves]` es una comprensión: crea una lista en el orden de las claves. `any`
permite retornar `None` antes de dibujar datos incompletos. `zip` recorre en
paralelo nombres, números y colores; `enumerate` aporta el índice para situar
cada barra. Las cadenas `f"{valor:+.2f}"` muestran signo y dos decimales,
sin redondear los resultados del solucionador. Los retornos SVG no tienen
unidades físicas propias: las unidades pertenecen a los datos rotulados.
Por ejemplo:

```python
r = simular_turborreactor(DEFAULTS_TURBO)
terminos = datos_empuje_grafica(r)       # tupla de cuatro números
svg = svg_descomposicion_empuje(r)       # str o None; usa los términos
estaciones = estaciones_turborreactor(r)
puntos = datos_ts_turborreactor(estaciones)  # cinco tuplas en el caso base
svg_ts = svg_ts_turborreactor(estaciones)    # str; usa esos puntos
```

Se exige la estructura del resultado científico: las claves obligatorias
inexistentes producen `KeyError`. Los errores de dominio de `s(T,p)` se
propagan; el dibujante T–s no inventa una entropía para eludirlos. En el SVG,
`escalar = lambda p: (...)` es una función corta que transforma un punto en
coordenadas de dibujo, sin modificar T ni s. El rótulo E se coloca debajo
del punto y los textos tienen contorno blanco (`paint-order="stroke"`) para
que las conexiones discontinuas no crucen las letras. La altura máxima del
T–s es 420 px; las regiones conservan desplazamiento horizontal y foco.

**COMPROBACIÓN EN WINDOWS.** El 27/10/2026 pasan las 42 pruebas específicas
de 44.1–44.4 (7 + 9 + 10 + 16), las 74 de integración web M40/M41/M42.B/M43
y la regresión vigente: 651 pruebas, 641 correctas, cero fallos/errores y diez
omisiones justificadas. Flask/Jinja2 están disponibles en `.venv`; no se instala
ninguna dependencia. Se revisan ocho configuraciones que cubren los nueve casos
solicitados (el estático inicial es también convergente bloqueado), sus POST,
SVG, balances y vistas reales en tamaños grande y estrecho. El recuento de
accesibilidad del caso base es ocho SVG; con perfil C-D disponible son diez.
Los comandos, limitaciones e incidencias se registran en el técnico 44.4.
Véanse [documento técnico 44.1](docs/milestones/44_1_graficas_empuje_ts_turborreactor.md)
y [aprendizaje 44.1](docs/milestones/44_1_graficas_empuje_ts_turborreactor_APRENDIZAJE.md).

### 4.82 — Milestone 44.2: estados discretos de Mach y presión de tobera

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** La serie de Mach [-] y la de
presión **estática** [kPa] comparten el orden de los estados que realmente
resuelve la tobera: garganta C-D, estados antes/después de choque normal y
salida; la convergente solo aporta su salida, que coincide con la garganta
si se bloquea. La línea de referencia en cada SVG es `Mach=1` o la presión
ambiente `p∞`. Un choque normal eleva presión estática y reduce Mach de
supersónico a subsónico; al mismo tiempo pierde **presión total**, que no se
mezcla en el gráfico de presión estática. El eje horizontal es **categórico**:
no se conoce un perfil espacial continuo ni una distancia de choque.
Los puntos se toman del solver con cp(T) variable, sin modificar sus ecuaciones.

**PYTHON.** `datos_tobera_graficas(resultado)` recibe un `dict` con
`resultado['tobera']`, `['ambiente']` y `['diagnosticos']` y retorna otro
`dict` con `estados: tuple[dict]`, `ambiente: float` [kPa], `regimen: str` y
`tipo: str`, o `None` si falta la salida. Cada estado define `nombre: str`,
`mach: float` [-], `presion: float` [kPa] y `papel: str`. Reutiliza las claves
existentes `mach_garganta`, `presion_garganta`, `mach_salida`, `presion_salida`
y, si existe, `choque_normal` con `M1,p1,M2,p2`. La función local
`punto(nombre,mach,presion,papel)` convierte tipos y rechaza presión no
positiva, Mach negativo y valores no finitos con `ValueError`. Por ejemplo,
`datos_tobera_graficas(simular_turborreactor(DEFAULTS_TURBO))['estados']`
contiene solo el punto de salida bloqueada. No calcula nuevas condiciones
interiores.

`svg_estados_tobera(datos,magnitud)` recibe el dict anterior y un `str`:
`'mach'` o `'presion'`, y devuelve un `str` SVG o `None` si `datos` es `None`.
Con una magnitud no reconocida lanza `ValueError`. Construye `xs` por índice
de estado (categorías, sin unidades) y la escala vertical para representación;
el texto de cada punto conserva los resultados originales. Sus dos variantes
se invocan desde `preparar_vista_turborreactor(resultado)`, cuyo diccionario
ahora incorpora `datos_tobera_graficas`, `svg_mach_tobera` y
`svg_presion_tobera`, además de los SVG existentes de 44.1. La plantilla Jinja
los coloca bajo «Visualizaciones y transformaciones» con explicación del
régimen y un aviso cuando faltan estados. No cambia JS ni formularios.

**PYTHON — ejemplo y función local.** `punto(nombre, mach, presion, papel)`
recibe dos `str` y dos números reales (Mach sin unidades, presión en kPa),
retorna un diccionario con esas cuatro claves y números convertidos a `float`
y solo la llama `datos_tobera_graficas`. Usa `isinstance`, `isfinite` y `all`
para rechazar booleanos, valores no reales/no finitos y estados fuera de
signo; la presión ambiente también debe ser real, finita y positiva.
Las claves requeridas ausentes provocan `KeyError`. Las funciones SVG no
resuelven la tobera: consumen estos datos y forman cadenas de texto.

```python
r = simular_turborreactor({**DEFAULTS_TURBO,
                         'tipo_tobera': 'convergente_divergente', 'epsilon': '6'})
datos = datos_tobera_graficas(r)
svg_mach = svg_estados_tobera(datos, 'mach')
svg_presion = svg_estados_tobera(datos, 'presion')
```

`**DEFAULTS_TURBO` copia pares clave/valor; las claves posteriores reemplazan
solo los ajustes elegidos. `preparar_vista_turborreactor`, llamado por
`web_app.turborreactor()` tras POST, obtiene `datos` una vez y llama al dibujante
para cada magnitud; este usa `escape` para los rótulos. La plantilla muestra
ambos SVG con las mismas estaciones, sin interpolación física ni distancia.

**VERIFICACIÓN ACTUAL EN WINDOWS.** Se aplican los resultados acumulados
indicados en §4.81. En el motor inicial con C-D y Ae/Ag=6 se obtiene choque
interno: M1≈3.141495, M2≈0.456981, p1≈8.407155 kPa y p2≈96.905779 kPa,
con salida a 100.000000 kPa y Mach≈0.399778. El ejemplo directo de tobera
Tt=1200 K, pt=500 kPa, p∞=350 kPa y Ae/Ag=1,5 es otro caso distinto,
conservado en las pruebas de 44.2. Los dos gráficos muestran estados a ambos
lados del choque como puntos separados. En el navegador se verifica también
la supresión de gráficos ante salida ausente, sin conservar valores anteriores.
Estas pruebas verifican presentación y coherencia interna, no validación
experimental. Véanse [técnico 44.2](docs/milestones/44_2_mach_presion_tobera.md)
y [aprendizaje 44.2](docs/milestones/44_2_mach_presion_tobera_APRENDIZAJE.md).

### 4.83 — Milestone 44.3: balance energético del turborreactor

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** La figura compara cuatro
transferencias energéticas: trabajo absorbido por el compresor, aporte
químico efectivo en la cámara de combustión, trabajo extraído por la
turbina y energía cinética de escape. Son magnitudes de etapas sucesivas,
**no sumandos de una misma igualdad**. Todas se expresan en kJ por kg de
aire entrante; en las etapas posteriores a la inyección de combustible se
usa el factor másico `1+f`. El trabajo del eje útil y cinco residuos de
cierre aparecen como comprobaciones adicionales. `h(T)` procede del
modelo existente con `cp(T)` variable y referencia `h(298,15 K)=0`;
no se añade entalpía sensible del combustible al modelo. El balance de
tobera distingue entalpía estática de salida y energía cinética.

**PYTHON.** `datos_balance_energetico(resultado)` recibe el `dict` devuelto
por `simular_turborreactor` y retorna otro diccionario: `compresor`,
`combustor`, `turbina`, `eje_util`, `tobera_cinetica` (valores en kJ/kg
de aire entrante, este último `None` si no se dispone de escape),
`f` [kg combustible/kg aire], `factor_masico=1+f` y `residuos`
(diccionario con las claves `compresor`, `combustor`, `turbina`, `eje`,
`tobera`; la última es `None` si falta la salida). Reutiliza las
entalpías y los trabajos ya calculados por los módulos físicos;
verifica finitud y consistencia de cierres con una escala relativa,
lanzando `ValueError` ante datos incoherentes. No resuelve estados ni
altera ecuaciones, tolerancias del solver o modelos de tobera.

`svg_balance_energetico(datos)` recibe ese diccionario y devuelve una
cadena SVG accesible con cuatro barras independientes, sus valores y
unidades. `preparar_vista_turborreactor(resultado)` llama ambas funciones
y añade `balance_energetico` y `svg_balance_energetico` al contexto
empleado por `templates/turborreactor.html`; la plantilla muestra además
la tabla con los cinco residuos, o el estado «No disponible» para la
tobera si no existe un escape calculado. Las gráficas 44.1 y 44.2 y sus
contratos permanecen intactos.

**PYTHON — uso y validaciones.** `datos_balance_energetico(resultado)` llama
a `h(T_salida)` cuando existe salida. Exige trabajos, aporte químico y dosado
positivos; factor másico >1 y coherente con `1+f` dentro de `1e-10 × factor`.
Los cinco residuos, si están disponibles, deben ser finitos y cumplir
`abs(residuo) <= 1e-8 × escala`, donde la escala es el máximo de 1 y las
magnitudes energéticas de referencia. Una inconsistencia produce `ValueError`;
las claves obligatorias ausentes producen `KeyError`. Si no hay tobera o su
velocidad de salida es `None`, el término cinético y su residuo son `None`.
Una velocidad presente con temperatura ausente es un error, no una energía cero.
`svg_balance_energetico(datos)` espera el dict ya comprobado, llama a `escape`
para rótulos y retorna `str` sin unidades propias; no valida de nuevo el modelo.
Ambas funciones se llaman desde el preparador de vista usado por la ruta Flask.

```python
r = simular_turborreactor(DEFAULTS_TURBO)
balance = datos_balance_energetico(r)
svg = svg_balance_energetico(balance)
# balance['compresor'] ≈ 316.235549 kJ/kg aire
# balance['residuos']['eje'] ≈ -1.22e-11 kJ/kg aire
```

`any(condicion for valor in magnitudes)` recorre un generador y detecta si
algún dato incumple las reglas. `valor is None` distingue ausencia de un
cero calculado. El formato `f"{valor:.2f}"` redondea solo la etiqueta; los
balances conservan los números del solucionador. El bucle Jinja recorre las
cinco claves de residuos; no resuelve física en la plantilla.

**VERIFICACIÓN.** Los diez métodos de
`tests/test_balance_energetico_turborreactor_44_3.py` contrastan cinco identidades,
normalización, salidas ausentes, parámetros, errores, SVG y preservación de
44.1–44.2. La batería acumulada actual y la regresión Windows se resumen en
§4.84. Se revisan barras y tabla en navegador, incluyendo ausencia de escape.
Es verificación de conservación interna, **no validación experimental**.
Véanse el [técnico 44.3](docs/milestones/44_3_balance_energetico_turborreactor.md)
y el [aprendizaje 44.3](docs/milestones/44_3_balance_energetico_turborreactor_APRENDIZAJE.md).

### 4.84 — Milestone 44.4: perfiles físicos C-D con cp(T) variable

**FÍSICA / INGENIERÍA.** El solucionador C-D ya determina el régimen,
los estados de garganta y salida y, si existe, el salto de choque normal.
El milestone 44.4 calcula condiciones **intermedias** a lo largo del área
geométrica relativa `A/Ag`, sin introducir distancias axiales. En cada
región suave se conservan `h(Tt)=h(T)+V²/2000`, `ρVA=constante` y
`s(T,p)=s(Tt,pt)`. Después de choque cambia la presión total a `pt2`,
con un área crítica posterior distinta: `A/A*2` **no** es el mismo eje
que `A/Ag`. Un choque aparece como dos estados distintos en la misma
relación geométrica de área; no se inventan interpolaciones a través de
él, choques exteriores ni una longitud física.

**PYTHON.** Nuevo módulo `perfil_tobera_cp_variable.py`:
`perfil_tobera_cp_variable(resultado, *, puntos_por_region=41)` recibe
un `dict` científico del turborreactor y número entero de puntos por
región (3–121); devuelve un `dict` con `disponible: bool`, `motivo`,
`regimen`, `segmentos: tuple[tuple[dict]]`, `choque: tuple[dict,dict]|None`,
`p_ambiente` [kPa], `relacion_areas` [-],
`flujo_masico_por_garganta` [kg/(m²·s)] y `area_critica`.
Cuando falta geometría convergente o salida C-D físicamente resuelta,
retorna `disponible=False` con motivo explícito y segmentos vacíos;
los controles incorrectos (`puntos_por_region`) lanzan `ValueError`.

Cada estado tiene `area_relativa` [-], `temperatura` [K], `presion` [kPa],
`densidad` [kg/m³], `velocidad` [m/s], `mach` [-], `entalpia` [kJ/kg],
`entropia` [kJ/(kg·K)], `flujo_masico_por_area` [kg/(m²·s)],
`flujo_masico_por_garganta`, `residuo_energia` [kJ/kg],
`residuo_entropia` [kJ/(kg·K)], `area_sobre_critica` [-],
`presion_remanso_region` [kPa], `rama` y `papel`.
La función reutiliza `_estado`, `_sonico`, `_salida_area` y `_biseccion`
de `tobera_convergente_divergente_cp.py`. Los auxiliares nuevos
`_malla`, `_punto`, `_subsonico`, `_desde_choque` y `_validar_perfil`
discretizan, resuelven la raíz subsónica en el intervalo físico,
preservan los estados exactos del choque y verifican invariantes.
El adaptador no altera los solucionadores científicos existentes.

`svg_perfil_tobera(datos, magnitud)` en `turborreactor_web.py` recibe
el diccionario anterior y `'mach'` o `'presion'`, y devuelve un SVG `str`
o `None` para un perfil no disponible; otras magnitudes producen
`ValueError`. Dibuja una polilínea **por región isentrópica**, una marca
de salto para choque y los mismos valores `A/Ag` para las dos gráficas.
`preparar_vista_turborreactor` añade `perfil_tobera`,
`svg_mach_perfil_tobera` y `svg_presion_perfil_tobera` a su diccionario;
`templates/turborreactor.html` muestra las curvas y explicaciones en
«Visualizaciones y transformaciones» cuando hay perfil, o el motivo
cuando no lo hay. Las gráficas discretas 44.2 siguen siendo visibles.

**Ejemplo reproducible.** C-D con `Tt=1200 K`, `pt=500 kPa`,
`p∞=350 kPa`, `Ae/Ag=1,5`: choque interno a `As/Ag≈1,36206`, con
`M1≈1,7019`, `M2≈0,63448`, `p1≈102,015 kPa`, `p2≈327,088 kPa`,
salida `M≈0,54316` y `p≈350 kPa`. `Ag/A*1=1` y
`Ag/A*2≈0,847456` por pérdida de presión total.

**PYTHON — contratos auxiliares.** Las funciones con `_` inicial son
convencionalmente internas al módulo; no son funciones anidadas salvo
`ausente`. Sus argumentos físicos proceden del solucionador ya verificado;
no repiten todas sus validaciones. Las claves ausentes producen `KeyError` y
los errores numéricos/de dominio de las rutinas reutilizadas se propagan.

| Firma completa | Entrada → retorno; unidades; llamadas |
|---|---|
| `_malla(inicio, fin, puntos)` | Dos reales A/Ag [-] y entero ≥3 → tupla de reales con ambos extremos. La llama `perfil_tobera_cp_variable`; usa `range` y no realiza física ni validación independiente. |
| `_punto(area, estado, Tt, pt, g_star, rama, papel="intermedio")` | Área relativa real [-], dict `_estado`, Tt [K], pt [kPa], G* real o `None` [kg/(m²·s)] y dos `str` → dict de estado y residuos enumerados arriba. Llama `h` y `s`; la llaman el perfil y `_desde_choque`. |
| `_desde_choque(area, choque, lado, Tt, g_star)` | A/Ag [-], dict del choque, `lado` interno `'antes'`/`'despues'`, Tt [K], G* [kg/(m²·s)] → dict de `_punto`. Reutiliza T,p,V,rho,M,pt del lado elegido; la llama el perfil. |
| `_subsonico(Tt, pt, temperatura_sonica, flujo_objetivo)` | Reales: K, kPa, K, kg/(m²·s) → dict de `_estado`; llama `_biseccion` y `_estado` para resolver G(T) en la rama subsónica. La llama el perfil; propaga `ErrorNumericoCiclo`. |
| `_validar_perfil(segmentos, flujo_garganta, *, salto=None)` | Tuplas de estados, Gg [kg/(m²·s)] y par de estados o `None` → `None`. La llama el perfil; usa `isfinite`, comprueba invariantes y lanza `ErrorNumericoCiclo` si no cierran. |
| `ausente(motivo)` | Función anidada: `str` → dict de cinco claves `disponible=False`, `motivo`, `segmentos=()`, `choque=None`, `regimen`. La llama solo el perfil; describe indisponibilidad, sin cálculo físico. |

`_validar_perfil` comprueba caudal con `2e-6 × max(1,abs(Gg))`, energía con
`1e-7 kJ/kg`, entropía regional con `1e-8 kJ/(kg·K)` y, en choque, coincidencia
de área a `1e-12`, M1>1>M2, p2>p1, s2>s1 y pt2<pt1. El perfil comprueba además
la coincidencia de salida con el solucionador (Mach absoluto `1e-5`, presión
`1e-5 × max(1,abs(pe))`). Esas tolerancias verifican esta representación;
no alteran los algoritmos existentes. El dict completo descrito arriba se
retorna solo con `disponible=True`; la forma de indisponibilidad es la de
`ausente`. `svg_perfil_tobera` espera esos datos, llama a `escape` para texto,
propaga errores de estructura y valida la magnitud antes de aceptar `None`.
Su salida textual no tiene unidades propias; los ejes son A/Ag, Mach y kPa.

```python
r = simular_turborreactor({**DEFAULTS_TURBO,
                         'tipo_tobera': 'convergente_divergente', 'epsilon': '6'})
perfil = perfil_tobera_cp_variable(r, puntos_por_region=11)
svg = svg_perfil_tobera(perfil, 'mach')
# 11 estados antes y 11 después del choque, con dos estados en la misma área.
```

El `*` de la firma pública obliga a escribir `puntos_por_region=11` por nombre.
Una comprensión crea cada malla; `tuple` conserva el orden de estados. La
función `lambda T: ...` es el residuo que la bisección debe hacer cero; no
interpola Mach. En el SVG, `' '.join(...)` reúne coordenadas y cada región
produce una polilínea distinta. `_desde_choque` reutiliza la solución exacta
del salto: no se añade una fila física ficticia entre ambos lados.
El flujo es `web_app.turborreactor` → `simular_turborreactor` →
`preparar_vista_turborreactor` → perfil y dos SVG → plantilla Jinja.

**VERIFICACIÓN ACTUAL.** Windows 11 (10.0.26300), Python 3.13.0 de `.venv`:
42/42 pruebas específicas, 74/74 web y regresión vigente de 651 pruebas:
641 correctas, 0 fallos, 0 errores y 10 omisiones (8 por SciPy opcional,
1 por Cantera opcional y 1 subcaso de enlace simbólico sin privilegio).
Los nueve casos pedidos se reproducen en ocho configuraciones científicas,
HTTP y de navegador, incluyendo convergente bloqueada/no bloqueada, C-D
subsónica/supersónica, choque interno y en salida y ausencia de expansión.
La convergente no genera perfiles; las C-D usan 41 puntos por región, y el
choque de salida no prolonga una rama exterior. La navegación por seis
secciones, teoría, OFAT de 2 puntos y mapa 2×2 funciona. Se revisan tamaño
normal, grande y estrecho, foco y desplazamiento local sin desbordar la página.
No se modifican los solucionadores, ecuaciones o dependencias. La coincidencia
con invariantes y con el solver es verificación interna, no validación experimental.
Comandos, parámetros, integración compatible e incidencias: [técnico 44.4](docs/milestones/44_4_perfiles_cuasidimensionales_tobera.md)
y [aprendizaje 44.4](docs/milestones/44_4_perfiles_cuasidimensionales_tobera_APRENDIZAJE.md).

### 4.85 — Milestone 45: caudal másico, empuje absoluto y dimensionamiento de toberas

La organización de la entrega es:

- **45.1:** gasto másico de aire, combustible y gases; consumo horario.
- **45.2:** empuje absoluto en N/kN y sus contribuciones firmadas.
- **45.3:** áreas de garganta/salida y diámetros circulares equivalentes.

La integración web, las pruebas y la documentación son actividades transversales
del milestone completo, no una entrega 45.3 diferente.

**PYTHON — Datos y contratos.** El archivo nuevo
`dimensionamiento_turborreactor.py` es una capa algebraica sobre la solución
científica del milestone 37; no resuelve de nuevo el motor. El formulario de
`/turborreactor` incorpora el campo **opcional** `gasto_masico_aire` [kg/s].
Su cadena vacía (incluso con espacios) deja los resultados específicos tal
como estaban. Una cifra debe ser real, finita y estrictamente positiva:
`validar_gasto_masico_aire(gasto_masico_aire)` devuelve `float` o lanza `ValueError`.
No se interpreta como caudal de combustible ni de gases de escape.

`calcular_prestaciones_absolutas(resultado, gasto_masico_aire)` recibe el
diccionario ya resuelto y devuelve otro con caudales [kg/s], términos
firmados de empuje [N], empuje neto [N y kN], consumo horario [kg/h], TSFC
[kg/(N·h)] y residuos de cierre. La entrada de aire, la masa de combustible
y el escape satisfacen `ṁf = f ṁa` y `ṁe = (1 + f) ṁa`.
Los términos de empuje absoluto multiplican por `ṁa` los correspondientes
términos *específicos* del solucionador; su suma ha de reproducir
`ṁa F_específico`. El consumo específico absoluto sólo se muestra cuando
el empuje neto es positivo y está disponible.

`dimensionar_tobera(resultado, gasto_masico_aire, *, absolutos=None)` usa
los estados estáticos reales de salida `ρe` [kg/m³] y `Ve` [m/s] para
calcular `Ae = ṁe/(ρe Ve)` [m²]. Para tobera convergente, garganta y
salida coinciden en área incluso sin bloqueo. Para convergente-divergente,
la garganta emplea el flujo másico superficial real `Gg` [kg/(m²·s)]
del solver (crítico solo si está bloqueada): `Ag = ṁe/Gg`. Las áreas sólo se publican cuando existe una
solución física suficiente. Ambos diámetros son **circulares equivalentes**
`D = √(4A/π)` [m], no una geometría axial ni una longitud de tobera.
Un choque normal no se interpola: se utilizan las propiedades de salida
resueltas por el modelo, ya aguas abajo del choque cuando corresponde.

`simular_turborreactor` llama una vez al solver M37 y sólo entonces
incorpora `resultado['prestaciones_absolutas']` y
`resultado['dimensionamiento_tobera']` si se indica un caudal válido. El
adaptador `preparar_vista_turborreactor` genera un SVG adicional con
`svg_descomposicion_empuje(resultado, absoluto=True)`; la llamada original
sin ese argumento continúa dibujando el empuje específico [N/(kg/s)].
Jinja muestra los caudales, la identidad de empuje, el consumo horario,
áreas y diámetros disponibles. No hay cambios en JavaScript, CSS o
algoritmos termodinámicos.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** El empuje específico permite
comparar motores sin fijar su tamaño; el empuje absoluto responde a
cuántos newtons desarrolla el motor al procesar un caudal concreto. Para
un punto operativo fijo, duplicar `ṁa` duplica empuje, combustible y
secciones, pero **no** duplica los diámetros (crecen con la raíz cuadrada
del área). El término de presión puede ser negativo cuando `pe < p∞`:
no se ha de eliminar su signo para obtener un resultado estético. Tampoco
debe calcularse TSFC físico si el empuje no es positivo. La garganta
crítica de una C-D y la salida no son intercambiables; la relación de
áreas procede del régimen realmente resuelto. El dimensionamiento es
continuidad cuasi-1D de un punto, no un diseño mecánico detallado ni
validación de motor real.

```python
from dimensionamiento_turborreactor import (
    calcular_prestaciones_absolutas, dimensionar_tobera
)
from turborreactor_web import simular_turborreactor, valores_turborreactor

valores = valores_turborreactor()
valores['gasto_masico_aire'] = '20'  # kg/s; ejemplo docente, no dato de diseño
resultado = simular_turborreactor(valores)
F = resultado['prestaciones_absolutas']['empuje_neto']  # N
Ae = resultado['dimensionamiento_tobera']['area_salida']  # m²
```

**PYTHON — llamadas y presentación.** La validación recibe un real (`int`
o `float`, sin `bool`) y devuelve `float` [kg/s]; la llaman el adaptador web,
el escalado y el dimensionamiento. `_finito(valor)` recibe un objeto y devuelve
`bool`: por ejemplo, `_finito(20.0)` es `True` y `_finito(True)` es `False`.
La usan `calcular_prestaciones_absolutas` y `dimensionar_tobera` para comprobar
números del resultado. La primera llama al validador; la segunda llama al
validador y, si no recibe `absolutos`, al escalado. Ambas se llaman desde
`simular_turborreactor`; el argumento `absolutos=a` permite reutilizar el dict.
Sus claves, unidades y errores se detallan en el técnico 45. Las claves
científicas obligatorias ausentes pueden producir `KeyError`; las entradas o
cierres incoherentes producen `ValueError`. No se alteran estados del solver.

`svg_descomposicion_empuje(resultado, *, absoluto=False)` retorna `str` SVG
o `None` si no hay fuerza disponible. La llama el preparador de vista dos
veces: modo específico original y modo absoluto; reutiliza los datos ya
calculados. Un cero con signo se muestra como cero en tabla/SVG (`valor or 0.0`),
sin alterar el dict numérico: `or` conserva cualquier número no nulo, también
negativo. El argumento después de `*` se pasa por nombre. Las unidades están
en las etiquetas; la cadena SVG no añade un cálculo físico.

**VERIFICACIÓN WINDOWS — 28/10/2026.** 19/19 pruebas específicas y 74/74 web
M40/M41/M42.B/M43 correctas. Tras normalizar el cero se repiten juntas las
93, sin fallos, errores ni omisiones. No se ejecuta la regresión científica
histórica. Se comprueban GET/POST y el campo vacío, 20/40 kg/s y entradas
inválidas. Las extensivas se duplican y los diámetros crecen por √2, conservando
las magnitudes específicas. Se revisan escritorio y pantalla estrecha.
Es verificación interna y de integración, no validación experimental.
Véanse el [técnico 45](docs/milestones/45_gasto_masico_dimensionamiento_turborreactor.md)
y el [aprendizaje 45](docs/milestones/45_gasto_masico_dimensionamiento_turborreactor_APRENDIZAJE.md)
para resultados, ejemplos y límites; las baterías previas de desarrollo no se
presentan como pruebas repetidas en esta revisión.

### 4.86 — Milestone 46.1: geometría del divergente cónico

**PYTHON.** `geometria_tobera_conica.py` contiene tres funciones nuevas y no
importa módulos de termodinámica:

- `validar_semidivergencia(angulo_grados)` recibe un `Real` numérico, no
  booleano, y devuelve `float` [°]. Rechaza con `ValueError` valores no
  finitos y ángulos fuera de `(0,90)`; lo invocan el formulario y la función
  geométrica.
- `calcular_geometria_conica(dimensionamiento, angulo_grados)` recibe el
  `dict` del M45 y ángulo [°] y devuelve `dict` con `disponible`, `motivo`,
  `radio_garganta`, `radio_salida`, `diametro_garganta`, `diametro_salida`,
  `longitud_divergente` [m], ambas áreas [m²], relación y residuos [m²].
  Llama al validador y a `sqrt`, `tan`, `radians`; para C-D no dimensionada
  o convergente conserva los resultados como `None` y explica el motivo;
  rechaza áreas finitas no positivas o `Ae<Ag` mediante `ValueError`.
  El caso límite `Ae=Ag` no genera longitud y devuelve indisponibilidad:
  el solver puede admitirlo sin que exista un divergente geométrico.
- `svg_geometria_conica(geometria)` recibe el dict anterior y devuelve SVG
  en texto o `None`. Lo llama `preparar_vista_turborreactor`; las líneas y
  el polígono se trazan con **la misma escala en x e y**. No interpola
  estados físicos. Las cotas textuales expresan las dimensiones calculadas.

El `DEFAULTS_TURBO` añade `angulo_semidivergencia='15'`, ángulo que no es
un óptimo. `valores_turborreactor` conserva este valor predeterminado al
recibir un POST antiguo sin ese campo; `simular_turborreactor` convierte el
texto a `float` y comprueba el dominio **sólo con caudal y tobera C-D**:
una entrada de ángulo inválida no bloquea simulaciones sin esa geometría.
Llama **una sola vez** al solucionador y añade `geometria_conica` tras
`dimensionamiento_tobera` si hay caudal y C-D. La plantilla muestra el esquema en los resultados existentes;
el resto de secciones no cambia. El uso de `dict.get`, `None` y una bandera
de disponibilidad evita inventar longitud cuando no hay datos.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** La geometría es una hipótesis
axisimétrica construida sobre los **diámetros circulares equivalentes**
del M45. En el divergente recto, `rg = √(Ag/π)`, `re = √(Ae/π)` y
`Ld = (re−rg)/tan(α)` [m], siendo `α` la semidivergencia desde el eje,
no el ángulo total entre paredes. Con áreas fijas reducir `α` alarga el
divergente; con `ṁaire` cuatro veces mayor y termodinámica fija, áreas ×4,
radios ×2 y longitud ×2. No se especifica entrada del convergente, por
lo que **no existe longitud total calculada de la tobera**. Tampoco se
calcula efecto de α sobre Mach, presión, separación, rozamiento ni empuje;
esto requeriría un modelo aerodinámico adicional y validación separada.

```python
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor
v = {**DEFAULTS_TURBO, 'tipo_tobera':'convergente_divergente',
     'gasto_masico_aire':'20', 'angulo_semidivergencia':'15'}
r = simular_turborreactor(v)
Ld = r['geometria_conica']['longitud_divergente']  # m
```

**VERIFICACIÓN.** `tests/test_geometria_tobera_conica_46_1.py` comprueba
longitud analítica, conservación de áreas, radios y relación de áreas,
escalado, monotonicidad, ángulos inválidos, disponibilidad, SVG XML y
conservación de resultados termodinámicos. Ver [técnico 46.1](docs/milestones/46_1_geometria_conica_tobera.md)
y [aprendizaje 46.1](docs/milestones/46_1_geometria_conica_tobera_APRENDIZAJE.md)
para la verificación realmente ejecutada y las limitaciones.

### 4.87 — Milestone 46.2: proyección axial de perfiles cuasi-1D

**PYTHON.** El módulo nuevo `perfil_axial_tobera_conica.py` no llama
al solucionador termodinámico. Contiene tres funciones:

- `posicion_axial_por_area(area_relativa, geometria)` recibe `a=A/Ag`
  adimensional y el `dict` de geometría M46.1. Comprueba finitud y el
  intervalo `[1,Ae/Ag]` con tolerancia relativa compartida `2e-6`;
  retorna `x` [m] y lanza `ValueError` con diferencias fuera de rango.
  Para los extremos y sus redondeos aceptados retorna `0.0` o `Ld`.
  La llaman las comprensiones del proyector y la localización del choque.
- `proyectar_perfil_axial(perfil, geometria)` recibe el `dict` científico
  del M44.4 y el del M46.1. Comprueba compatibilidad de área con la misma
  tolerancia de la conversión, y retorna un
  `dict` con `disponible`, `motivo`, `segmentos` (tuplas de estados),
  `choque` (dos estados o `None`), `x_choque` [m],
  `longitud_divergente` [m], `regimen` y `p_ambiente` [kPa]. Cada estado se
  copia como `{**estado, 'x': posicion_axial_por_area(...)}`: se añade
  distancia sin alterar Mach, presión ni el objeto M44.4 original. Se llama
  desde `preparar_vista_turborreactor` después de `perfil_tobera_cp_variable`.
  Cuando no hay perfil o geometría, devuelve indisponibilidad explícita.
- `svg_perfil_axial(datos, magnitud)` acepta `'mach'` o `'presion'` y
  devuelve SVG o `None`; lo llama el adaptador web dos veces. Cada segmento
  físico tiene su propia `<polyline>`. El choque tiene **dos puntos a la
  misma abscisa** y una marca vertical, sin unirlos como una trayectoria
  continua de estados imposibles. Los ejes tienen marcas numéricas y
  referencias `M=1` o presión ambiente [kPa]. No interpola valores en Python.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Para cono axisimétrico,
`r(x)=rg+x tan α` y `A(x)=πr(x)²`, por lo que
`x=(√(Ag·(A/Ag)/π)−rg)/tan α`. La garganta es `x=0` y la salida `x=Ld`.
Como los estados del M44.4 ya son discretos en `A/Ag`, asignamos una
coordenada `x` a **cada estado calculado**. No inferimos nuevas
propiedades físicas. Con choque normal interior o en salida, la misma
área física y la misma `x` corresponden a valores diferentes antes y
después del salto; no se representa una rampa de presión ficticia.
Modificar caudal o α cambia longitudes y abscisas, pero no la
distribución física frente a relación de áreas si los demás parámetros
del motor permanecen fijos. Sin caudal, C-D resuelta o divergente positivo,
no hay coordenadas longitudinales para estas curvas. Los gráficos antiguos
frente a `A/Ag` se mantienen para distinguir solución de hipótesis.

```python
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor, preparar_vista_turborreactor
v = {**DEFAULTS_TURBO, 'tipo_tobera':'convergente_divergente',
     'gasto_masico_aire':'20', 'angulo_semidivergencia':'15'}
vista = preparar_vista_turborreactor(simular_turborreactor(v))
xs = [p['x'] for p in vista['perfil_axial_tobera']['segmentos'][0]]  # m
```

**VERIFICACIÓN.** `tests/test_perfiles_axiales_tobera_46_2.py` verifica
conversión e inversa analítica, extremos, monotonía, conservación exacta
de Mach y presión, choque en misma x con SVG por ramas, rangos inválidos,
sensibilidad geométrica y compatibilidad con 46.1. Las pruebas de 46.1
también cubren la validación condicional de α y el caso `Ae/Ag=1`.
Ver [técnico 46.2](docs/milestones/46_2_perfiles_axiales_tobera.md)
y [aprendizaje 46.2](docs/milestones/46_2_perfiles_axiales_tobera_APRENDIZAJE.md).
Estas pruebas son verificación interna, no validación experimental.

### 4.88 — Milestone 46.3: sensibilidad geométrica de la longitud

**PYTHON.** `estudio_geometrico_tobera.py` contiene tres funciones nuevas,
sin llamadas al solucionador termodinámico:

- `estudiar_angulos_geometria(geometria, *, angulos=ANGULOS_EDUCATIVOS)`
  recibe el `dict` de geometría M46.1 y una secuencia de ángulos [°]
  (por defecto, 5°, 10°, 15°, 20°, 25°). Devuelve otro `dict` con
  `disponible`, `motivo`, `filas` (tupla de dicts), `seleccionado` [°]
  y `comparacion` (tres geometrías con α=10°, 15° y 20°). Cada fila incluye
  `angulo_grados` [°], `longitud_divergente` [m], radios y diámetros [m],
  `relacion_areas` adimensional y `seleccionado` booleano. Llama a
  `calcular_geometria_conica` repetidamente **manteniendo constantes las
  dos áreas**, no al motor científico. Si falta geometría devuelve
  indisponibilidad con filas vacías; `*` obliga a escribir `angulos=` por
  nombre. `set` quita duplicados y `sorted` ordena los ángulos, incluyendo
  siempre el valor elegido en el formulario. Lo llama el preparador web.
- `svg_longitud_angulo(estudio)` recibe el estudio anterior y devuelve
  una cadena SVG graduada o `None`. Los valores horizontales son grados,
  los verticales metros, y se marca en rojo el ángulo del formulario.
- `svg_comparacion_conos(estudio)` recibe el mismo estudio y devuelve SVG
  o `None`; usa una sola escala px/m en x e y para tres conos (10°,15°,20°),
  con radios idénticos y distintas longitudes. Ambas funciones SVG son
  invocadas desde `preparar_vista_turborreactor` y no modifican los datos.

`preparar_vista_turborreactor` añade `estudio_geometrico`,
`svg_longitud_angulo`, `svg_comparacion_conos` a su diccionario de vista.
El bloque de Visualizaciones usa esas claves y muestra una tabla con las
áreas equivalentes, diámetros y ángulo elegido; si falta geometría,
explica la indisponibilidad en lugar de inventar una longitud.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Con `Ag`, `Ae` y, por tanto,
`rg`, `re` constantes, `Ld(α)=(re−rg)/tan(α)` decrece al aumentar α.
Los diámetros, la relación `Ae/Ag` y los estados físicos del motor
permanecen iguales. Minimizar Ld en un intervalo docente cerrado
como `[5°,25°]` elegiría el límite superior, **solamente como mínimo
geométrico condicionado**. No implica un ángulo óptimo de empuje:
faltan pérdidas por divergencia, fricción, separación, aerodinámica
externa y penalizaciones de estructura y masa.

```python
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor, preparar_vista_turborreactor
v = {**DEFAULTS_TURBO, 'tipo_tobera':'convergente_divergente',
     'gasto_masico_aire':'20', 'angulo_semidivergencia':'15'}
vista = preparar_vista_turborreactor(simular_turborreactor(v))
filas = vista['estudio_geometrico']['filas']
```

**VERIFICACIÓN.** `tests/test_estudio_geometrico_tobera_46_3.py` verifica
longitudes analíticas, monotonía, conservación de diámetros y estados
físicos, selección, dibujo a escala común e indisponibilidad. Dos
pruebas de `tests/test_perfiles_axiales_tobera_46_2.py` cubren las
tolerancias compatibles y graduaciones. Véanse [técnico 46.3](docs/milestones/46_3_estudio_angulo_longitud.md),
[aprendizaje 46.3](docs/milestones/46_3_estudio_angulo_longitud_APRENDIZAJE.md)
y [cierre M46](docs/milestones/46_cierre_geometria_tobera.md).

### 4.89 — Milestone 47.1: inversión del problema de caudal de tobera

**INGENIERÍA.** En el milestone 45 conocíamos el gasto de aire y se
dimensionaban las secciones. Ahora, con garganta `Ag` y salida `Ae`
prescritas, el gasto compatible con las condiciones de remanso se
obtiene de `ṁg = (ρV)g Ag`. La C-D utiliza el flujo superficial de
garganta **ya resuelto** en M42–M44.4: puede ser subsónico y depender
de contrapresión, o sónico si se bloquea. La convergente utiliza su
sección de salida, coincidente con garganta. Se coteja continuidad
`(ρV)g Ag ≈ (ρV)e Ae` y se distingue el gas del aire y combustible:
`ṁa = ṁg/(1+f)`; `ṁf = f ṁa`.

**PYTHON.** `caudal_tobera_geometria_fija.py` añade una función pública
de resolución directa y otra que adapta el resultado de un solucionador
existente sin volver a ejecutar el núcleo. `simular_turborreactor`
interpreta `modo_caudal=impuesto|fijo`, valida las áreas, deduce
`epsilon=Ae/Ag` antes del cálculo C-D y convierte el caudal de gases en
aire para reutilizar los escalados absolutos M45. El formulario oculta
y deshabilita los campos incompatibles; mantiene el modo histórico y
las seis secciones de la página. Los estados no resueltos se muestran
como indisponibles (`None`), nunca como caudal cero.

**VERIFICACIÓN Y LÍMITES.** Nueve métodos nuevos prueban regímenes
bloqueado, subsónico, choque, continuidad, escalado, combustible,
áreas, referencia aproximada de gas perfecto y regresión web. Se
requiere un remanso suministrado externamente: todavía no hay solución
acoplada con mapas de compresor y turbina, ni validación experimental.
Documentos: [técnico 47.1](docs/milestones/47_1_caudal_geometria_fija.md)
y [aprendizaje 47.1](docs/milestones/47_1_caudal_geometria_fija_APRENDIZAJE.md).

### 4.90 — Milestone 47.2: continuidad de admisión condicionada

**INGENIERÍA.** El flujo de corriente libre `ρ∞V∞A_cap` permite relacionar
caudal conocido con área de captación en vuelo; no predice la aspiración
en estático, donde `V∞=0`. Una sección interna `A2` del compresor, junto
con Mach local prescrito, sí permite calcular `ρ2V2A2` desde el remanso
posterior al difusor (`pt2=πd·pt∞`). Esto es una condición local y no
un punto operativo cerrado. Si coexiste un caudal de tobera, se informa
del residuo de continuidad sin alterar ningún dato.

**PYTHON.** `admision_caudal_cp.py` utiliza `h(T)`, `s0(T)` y `gamma(T)`;
resuelve `h(Tt2)=h(T2)+M2²gamma(T2)RT2/2000` mediante bisección,
deduce presión y densidad estáticas, y devuelve disponibilidad y
diagnósticos estructurados. Tres campos opcionales del formulario web
activan la comparación, con conservación de resultados previos cuando
están vacíos. [Técnico 47.2](docs/milestones/47_2_admision_y_caudal.md)
y [guía educativa 47.2](docs/milestones/47_2_admision_y_caudal_APRENDIZAJE.md).

### 4.91 — Milestone 47.3: mapas públicos de turbomáquinas escalados

**INGENIERÍA.** Dos mapas tabulados de NASA T-MATS (`HPC.map` y `HPT.map`)
se emplean como **formas educativas**, no como arquitectura JT9D. El
turborreactor sigue siendo monoeje: comparte `N` mecánico, mientras cada
`Ncorr=N/sqrt(Tt/Tref)` utiliza su propia temperatura de entrada. El
caudal corregido es `ṁcorr=ṁsqrt(Tt/Tref)/(pt/pref)`. Cuatro factores
por componente escalan nudo interior de cada mapa a un diseño
verificable del motor existente (20 kg/s de aire, rp=10, T3=1600 K,
ηc=.85, ηt=.90, N=20 000 rpm de referencia educativa).

**PYTHON.** Un script transforma mecánicamente tablas NASA originales
en JSON trazable. `interpolar_bilineal` rechaza extrapolación;
`calibrar_mapas` conserva ecuaciones del núcleo y calcula escalas;
`consultar_compresor` y `consultar_turbina` usan un único N real con
conversiones de referencia distintas. Verificación contra nudos y
punto de diseño en `tests/test_mapas_turbomaquinaria_47_3.py`.
[Técnico 47.3](docs/milestones/47_3_mapas_turbomaquinaria.md) y
[aprendizaje 47.3](docs/milestones/47_3_mapas_turbomaquinaria_APRENDIZAJE.md).

### 4.92 — Milestone 47.4: un punto estacionario con un solo eje

**INGENIERÍA.** El punto de diseño de 47.3 calibra dos mapas independientes,
pero ambos reciben la misma velocidad mecánica `N`. El compresor aporta
`mdot_a`, `PRc` y `ηc`, la cámara calcula el combustible `f` a `Tt3`
prescrita y la turbina entrega la potencia requerida con `ηm`. Tres
incógnitas `N`, `Rline` y `PRt` se cierran mediante tres residuos:
coincidencia entre expansión exigida por el eje y mapa; continuidad
`mdot_a(1+f)=mdot_g,mapa`; y gasto del gas igual al de la garganta
`Gg·Ag`. Se prohíbe imponer simultáneamente el gasto o la compresión.

**PYTHON.** `acoplamiento_motor_mapa_47.py` contiene `punto_diseno_47`,
`_resultado_punto` (estado y tres residuos), `_resolver_3x3` (Gauss con
pivotado) y `resolver_motor_acoplado` (Newton amortiguado con prueba de
descenso, chequeo de residuos y dominio de mapa). En fallo retorna
`disponible=False` y explica la causa; **no** rellena prestaciones.
`turborreactor_web.py` incorpora el modo C sin reescribir los modos A/B,
ni los solucionadores térmicos. El formulario oculta parámetros derivados
y solo muestra resultados con cierres verificados. La admisión con Mach y
área local opcionales debe transportar el mismo caudal.

La calibración educativa reproduce 20 kg/s, 20 000 rpm, compresión 10 y
garganta fija de 0,0473481164 m² en estático. Esta igualdad de diseño
es verificación, **no** validación experimental.
[Técnico 47.4](docs/milestones/47_4_acoplamiento_motor.md) y
[aprendizaje 47.4](docs/milestones/47_4_acoplamiento_motor_APRENDIZAJE.md).

### 4.93 — Milestone 47.5: verificación y cierre acumulado

**INGENIERÍA.** Diferenciamos los tres problemas: A dimensiona tobera a
caudal prescrito, B calcula caudal compatible con tobera de geometría fija
y remanso dado, C busca equilibrio estacionario de mapas/eslabones.
El balance del eje, continuidad en turbina/tobera, límites de los mapas,
regímenes de tobera y cambios de vuelo se prueban sin presentar el
motor educativo como un motor real validado.

**PYTHON.** `unittest` verifica nuevas ramas y regresiones relacionadas,
incluidos rechazos físicos; `compileall` y el analizador de JavaScript
separan fallos de sintaxis de defectos científicos. La suite histórica
completa y la inspección HTTP/visual quedan para la integración en Windows.
[Cierre 47.5](docs/milestones/47_5_verificacion_cierre.md) y
[aprendizaje 47.5](docs/milestones/47_5_verificacion_cierre_APRENDIZAJE.md).

### 4.94 — Milestone 48.1: navegación principal y API HTTP del turborreactor

**PYTHON / FLASK.** En `web_app.py`, `portada()` (`GET /`) utiliza
`redirect(url_for('turborreactor'))` para seleccionar el turborreactor
como portada. `index()` conserva su contrato `GET/POST` y todo el ciclo
Brayton en `/brayton`; las rutas de informes y descargas siguen
independientes. Los enlaces del simulador apuntan ahora a esas rutas.

`_render_turborreactor(valores, resultado=None, vista=None, *, error=None,
estudio=None, error_estudio=None, controles=None, accion=None)` recibe
los valores del formulario (cadenas), el resultado físico y presentación
o `None`, y los diagnósticos/estudios opcionales. Devuelve HTML como
`str` mediante la plantilla existente y lo utilizan tanto el endpoint
tradicional como la API. `*` significa que los argumentos siguientes
deben indicarse por nombre; evita confundir un error con un estudio.

`api_turborreactor_simular()` (`POST /api/turborreactor/simular`) recibe
un objeto JSON plano o un formulario `FormData`; devuelve JSON con
`ok`, `modo`, `magnitudes`, `estaciones`, `diagnosticos`, `svg` y
`html_documento`. Este último conserva el HTML de los paneles actuales
para que JavaScript pueda extraer las secciones `#resultados`,
`#estaciones` y `#graficas` sin reescribir las tarjetas; no desencadena
estudios OFAT ni mapas. Los errores devuelven `ok:false` y
`error:{tipo,mensaje}` sin inventar prestaciones: 400 para formato, 415
para tipo de contenido no admitido y 422 para entradas o soluciones no
admisibles. `_respuesta_json_api(datos, estado=200)` serializa con
`json.dumps(...,allow_nan=False)` para no publicar NaN ni infinitos.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Esta etapa no añade ecuaciones.
Ambas vías (`POST /turborreactor` y API) llaman una sola vez a
`simular_turborreactor` (A: caudal impuesto; B: geometría fija; C: motor
monoeje acoplado) y después a `preparar_vista_turborreactor`. Los
resultados y SVG pertenecen al mismo cálculo. Las restricciones y
unidades físicas permanecen en Python. No hay todavía listeners
automáticos ni sliders: corresponden a 48.2.

Ejemplo: `client.post('/api/turborreactor/simular', data=DEFAULTS_TURBO)`.
Los tests antiguos que pedían Brayton en `/` pasan ahora a `/brayton`
sin cambiar sus referencias científicas. [Técnico 48.1](docs/milestones/48_1_navegacion_y_api_interactiva.md)
y [aprendizaje 48.1](docs/milestones/48_1_navegacion_y_api_interactiva_APRENDIZAJE.md).

### 4.95 — Milestone 48.2: control deslizante y simulación automática

**PYTHON / INGENIERÍA.** No cambian los solucionadores. Mach (`0≤M<1`) y
T3 (`200–2000 K`, además del margen frente al compresor) son entradas
en A, B y C. Se añadió `regimen_tobera` a `magnitudes` de la API 48.1
para representar el régimen sin deducirlo en el navegador. Los caudales,
temperaturas, empujes y gráficos siguen siendo resultados coherentes de
una sola llamada a `simular_turborreactor` y su presentador Python.

**JAVASCRIPT.** `static/turborreactor_interactivo.js` introduce tres
funciones: `acoplarControl48({numero,deslizador,lectura,unidad,onCambio})`
conecta los eventos `input` de campo exacto y rango, y devuelve tres
funciones auxiliares para actualización; `crearControlador48({solicitar,
onEstado,onRespuesta,onError,demora=350,setTimer,clearTimer,Abort})`
devuelve `cambiar`, `invalidar`, `cancelar` y `version`, usa `setTimeout`
para esperar 350 ms sin bloquear la página, `AbortController` y un
identificador de versión que impide respuestas obsoletas; por último
`inicializar48(documento,fetcher)` prepara el formulario, indicadores,
regiones de HTML y las tres previsualizaciones SVG, o devuelve `null` si
no existe la interfaz. Las entradas `documento` y `fetcher` son objetos
del navegador (o dobles de prueba); no contienen unidades físicas.

`FormData` transmite los campos activos a la API existente. `DOMParser`
lee el HTML generado por Jinja y solo se reemplaza el contenido de uso
en `#resultados`, `#estaciones` y `#graficas`, manteniendo las pestañas
y los estudios independientes. El resumen junto a los deslizadores
enseña N, N/(kg/s), kg/s, kg/(N·h), rpm y régimen cuando proceden; para
`null` muestra «No aplicable» y en error borra resultados antiguos.
La variable de Mach exacto puede superar 0,999 del deslizador, pero sigue
sujeta al límite estricto `M<1` del solver.

**VERIFICACIÓN.** `tests/js/test_interaccion_48_2.cjs` ejercita seis
casos de sincronización, temporización, orden de respuestas y reintentos
con `node:test`, sin instalar dependencias. La prueba HTTP de los modos
A/B/C y el render final Jinja requieren el entorno Flask. Esta etapa
no implementa nuevos mapas ni pérdidas físicas, ni el milestone 48.3.
[Técnico 48.2](docs/milestones/48_2_actualizacion_automatica.md) y
[aprendizaje 48.2](docs/milestones/48_2_actualizacion_automatica_APRENDIZAJE.md).

### 4.96 — Milestone 48.3: cierre de la interacción inicial

**PYTHON / INGENIERÍA.** El recorrido de Mach y T3 desde los campos HTML
hasta `POST /api/turborreactor/simular` sigue utilizando los mismos nombres,
unidades y restricciones del cálculo tradicional. La API realiza **una sola**
simulación `simular_turborreactor(valores)` y presenta ese mismo `resultado`
mediante `preparar_vista_turborreactor(resultado)`; los indicadores estructurados,
SVG y paneles Jinja corresponden a la misma ejecución. A (caudal prescrito),
B (garganta prescrita) y C (mapas de motor monoeje) siguen siendo modelos
diferentes. Ningún cálculo aerotermodinámico se mueve al navegador.

**JAVASCRIPT.** `crearControlador48` expone `cancelar()` sin argumentos ni
retorno. Desde este cierre, el método incrementa la versión **además** de
cancelar temporizador y `AbortController`: el `submit` manual lo invoca y
deja definitivamente obsoleta cualquier respuesta automática pendiente. Esto
complementa `invalidar()` para editar campos no automáticos y `cambiar()`
para los deslizadores (350 ms); todos conservan un orden único de peticiones.
Ejemplo: si `cambiar()` inició una petición y acto seguido el usuario pulsa
«Simular», `cancelar()` invalida el identificador; ni una respuesta que
ignore el aborto ni un error tardío volverán a modificar esa página.

**Integridad de interfaz.** Solo se sustituyen los hijos de los tres paneles
«Uso» de resultados, estaciones y gráficas: no sus elementos contenedores,
las pestañas, controles, enlaces o formularios de sensibilidad y mapas. Las
previsualizaciones SVG y cifras usan un mismo JSON; se borran los resultados
obsoletos durante la espera o un error. El texto de los ejemplos distingue
ahora el cálculo automático con JavaScript del POST manual sin JavaScript.

**Verificación y límites.** Las ocho pruebas sin dependencias de
`tests/js/test_interaccion_48_2.cjs` cubren sincronización, espera,
reordenación, errores, invalidación de otros campos y envío manual. Las
pruebas HTTP 48.1 y la inspección visual están preparadas, pero no se
ejecutan en este entorno sin Flask/Jinja2; no equivalen a validación de
un motor real. [Técnico 48.3](docs/milestones/48_3_cierre_primera_etapa_interactiva.md)
y [aprendizaje 48.3](docs/milestones/48_3_cierre_primera_etapa_interactiva_APRENDIZAJE.md).

**Correcciones finales del milestone 48.** Los POST del Brayton original
en `tests/test_graficas_cp_variable.py` y la navegación histórica en
`tests/test_dashboard.py` usan `/brayton`; el `GET /` permanece como
redirección. En la plantilla del turborreactor, el atributo
`data-simulacion-inicial` del `<body>` indica `pendiente`, `resuelta` o
`error`: `inicializar48(documento,fetcher)` llama a `controlador.cambiar()`
una sola vez al abrir un GET pendiente (espera habitual de 350 ms), sin
duplicar el cálculo cuando ya hubo un POST manual resuelto o fallido.
La función local `estudioDesactualizado()` no recibe argumentos ni devuelve
un valor; muestra los avisos `.turbo-study-stale` existentes al modificar
entradas del motor. Los estudios previos **no se recalculan**. Tras una
respuesta automática correcta, se elimina únicamente el error del formulario
principal (`#turbo-configuracion-vista-uso > .error-summary`), sin alterar
diagnósticos de estudios independientes. Estas operaciones son de interfaz:
no se cambian propiedades del gas ni balances físicos.

### 4.97 — Milestone 49.1: separación de vistas y navegación del simulador

**PYTHON.** `portada()` sigue sin argumentos y devuelve una redirección
HTTP, ahora a `url_for('turborreactor_interactivo')`. En un mismo servidor,
`/turborreactor/interactivo` y `/turborreactor` están registrados sobre
`turborreactor(interfaz="clasico")`: su argumento `interfaz` es una cadena
con valores `"interactivo"` o `"clasico"` y no tiene unidades. La función
acepta GET o POST, lee `request.form`, ejecuta los mismos solucionadores y
devuelve `(html, codigo_http)` como antes; no hay nuevo motor. La función
`_render_turborreactor(valores, resultado=None, vista=None, *, error=None,
estudio=None, error_estudio=None, controles=None, accion=None,
interfaz="clasico")` recibe también la modalidad visual, la pasa a Jinja y
devuelve HTML. Los demás argumentos y sus unidades **no cambian**; las
entradas científicas conservan sus nombres (`mach`, `T3`, `modo_caudal`, etc.).
La ruta `/api/turborreactor/simular` sigue ejecutando una única simulación
para las modalidades físicas A/B/C, independientemente de la vista.

**JINJA/HTML.** Una única `templates/turborreactor.html` genera ambas
interfaces usando la variable `interfaz`: cambia título, menú activo y
destino del POST tradicional. El banco conserva en el DOM los paneles
clásicos que reutiliza `DOMParser`, pero CSS solo presenta `#configuracion`
con los controles y el panel-resumen interactivo; las otras cinco secciones
continúan íntegras y visibles desde `/turborreactor`. Esto permite a 49.2
rediseñar el banco sin romper los identificadores de la API. El ciclo Brayton
usa la misma `templates/index.html` de siempre, ahora con tres enlaces y
acción del formulario local `/brayton` (los informes offline conservan `#`).

**INGENIERÍA.** «Interfaz» no es «modalidad física». En cualquier vista del
turborreactor, A prescribe caudal y dimensiona, B prescribe geometría y
obtiene caudal compatible, C acopla mapas monoeje y balances. Mach es
adimensional y T3 está en K. Ninguna ecuación, propiedad variable ni
rendimiento se ha cambiado; navegación y diseño no validan el motor real.

**VERIFICACIÓN.** `tests/test_navegacion_49_1.py` contiene pruebas Flask
focalizadas de rutas, menú, controles, clásico y modos A/B/C, pendientes de
ejecutar aquí por ausencia de Flask/Jinja2. Se actualizaron las expectativas
de redirección del 48.1. Los ocho tests JS de 48.2 siguen correctos.
[Técnico 49.1](docs/milestones/49_1_separacion_interfaces.md) y
[aprendizaje 49.1](docs/milestones/49_1_separacion_interfaces_APRENDIZAJE.md).

### 4.98 — Milestone 49.2: distribución del banco de ensayos

**PYTHON / HTML.** La vista `interfaz="interactivo"` continúa utilizando una
única plantilla (`templates/turborreactor.html`), un solo formulario
`#turbo-form` y un panel de respuestas `#turbo-live`. La variable Jinja
`interfaz` añade la explicación compacta y clases de presentación
`turbo-bank-active-fields`, `turbo-bank-extra-fields`,
`turbo-bank-slider-field` y `turbo-bank-other-field`. No crea otra instancia
de `mach`, `T3`, sus deslizadores ni `modo_caudal`: los campos adicionales
siguen dentro del formulario y se envían a Flask, aunque el banco inicial
con JavaScript sólo muestre las dos entradas interactivas de 48.2.
`url_for('turborreactor_interactivo')` permite restablecer los valores con un
GET, que inicia de nuevo la simulación automática. En `/turborreactor` se
conserva el formulario íntegro, sus seis secciones y los estudios independientes.

**CSS / JAVASCRIPT.** En `static/turborreactor.css`, los selectores bajo
`.js .turbo-page[data-interfaz="interactivo"]` sitúan el formulario a la
izquierda y el panel de indicadores/SVG a la derecha mediante CSS Grid.
La columna de controles usa `position: sticky` en ordenador y vuelve a
`position: static` en pantallas de 900 px o menos; el diseño se apila
verticalmente. Se ocultan visualmente las entradas no habilitadas para esta
primera etapa, pero no se eliminan del DOM ni del POST. El controlador
`inicializar48(documento, fetcher)` sigue conectando `input` de Mach/T3,
sincronizando valores, esperando 350 ms y descartando respuestas antiguas.
`onRespuesta` sustituye las regiones de resultados y actualiza a la vez
las tarjetas y los tres SVG. El CSS no añade solicitudes HTTP ni fórmulas.
La API añade el campo `magnitudes.velocidad_salida_m_s` [m/s] leyendo
`tobera['velocidad_salida']` de **la misma ejecución**; JavaScript lo
representa en una tarjeta sin calcularlo de nuevo.

**INGENIERÍA.** Mach es adimensional, no un porcentaje. T3 [K] representa
la temperatura **total de entrada a turbina** tras la cámara, no la salida
de turbina. El selector conserva A (caudal impuesto), B (área fija de tobera)
y C (mapas de turbomáquinas acoplados); el caudal y el régimen mostrados
proceden de la API y pueden no estar disponibles. Los gráficos representan
únicamente los SVG generados por Python. La maquetación no altera los balances
ni equivale a validar prestaciones de un motor real.

**VERIFICACIÓN.** Se añadieron comprobaciones estáticas específicas
`tests/test_diseno_banco_49_2.py`; las pruebas de interacción 48.2 siguen
siendo la referencia del controlador JS. Sin Flask/Jinja2 no se atribuye
ninguna prueba HTTP ni inspección visual a este entorno. Véanse el
[documento técnico](docs/milestones/49_2_rediseño_banco_interactivo.md)
y el [aprendizaje](docs/milestones/49_2_rediseño_banco_interactivo_APRENDIZAJE.md).

## Evolution of the project

- **Milestone 49.2: banco interactivo en dos zonas (pendiente de commit).** CSS Grid reúne los controles Mach/T3 y modalidad junto a tarjetas y SVG reactivos; diseño adaptable sin nuevas entradas físicas ni duplicar la API. [Técnico](docs/milestones/49_2_rediseño_banco_interactivo.md) y [aprendizaje](docs/milestones/49_2_rediseño_banco_interactivo_APRENDIZAJE.md).
- **Milestone 49.1: tres interfaces y navegación compartida.** El banco interactivo es la portada, el clásico conserva todas sus secciones y Brayton mantiene su formulario en `/brayton`. Las dos vistas de turborreactor comparten un único controlador Flask, plantilla, lógica JS y solucionadores. [Técnico](docs/milestones/49_1_separacion_interfaces.md) y [aprendizaje](docs/milestones/49_1_separacion_interfaces_APRENDIZAJE.md).
- **Milestone 48.3: cierre focalizado de la etapa interactiva (pendiente de commit).** Protección del POST manual frente a peticiones tardías, pruebas de cancelación e invalidación y comprobación del flujo físico único; pendiente de pruebas HTTP/visuales en Windows. [Técnico](docs/milestones/48_3_cierre_primera_etapa_interactiva.md) y [aprendizaje](docs/milestones/48_3_cierre_primera_etapa_interactiva_APRENDIZAJE.md).
- **Milestone 48.2: primera simulación interactiva (pendiente de commit).** Controles Mach/T3, espera de 350 ms, cancelación y orden de respuestas, KPIs y SVG sincronizados con una ejecución Python; no modifica los solucionadores ni recalcula estudios independientes. [Técnico](docs/milestones/48_2_actualizacion_automatica.md) y [aprendizaje](docs/milestones/48_2_actualizacion_automatica_APRENDIZAJE.md).

- **Milestone 48.1: portada del turborreactor y API HTTP (pendiente de commit).** Flask separa `/`, `/turborreactor`, `/brayton` y JSON; reutiliza los cálculos físicos y la plantilla actual, preparando datos y HTML para el navegador sin recálculo automático ni cambios de ecuaciones. [Técnico](docs/milestones/48_1_navegacion_y_api_interactiva.md) y [aprendizaje](docs/milestones/48_1_navegacion_y_api_interactiva_APRENDIZAJE.md).

- **Milestones 47.4–47.5: solución estacionaria monoeje y cierre (sin commit).** Tres ecuaciones y tres incógnitas de mapa/eje/tobera resueltas con Newton amortiguado y límites físicos; conservación de las tres modalidades, regresión dirigida y registro de límites de verificación. [Técnico 47.4](docs/milestones/47_4_acoplamiento_motor.md), [aprendizaje 47.4](docs/milestones/47_4_acoplamiento_motor_APRENDIZAJE.md) y [cierre 47.5](docs/milestones/47_5_verificacion_cierre.md).

- **Milestone 47.3: mapas NASA T-MATS escalados al monoeje (sin commit).** Datos HPC/HPT públicos atribuidos, interpolación bilineal acotada y reproducción exacta de un punto de diseño didáctico, sin copiar la arquitectura original JT9D. [Técnico](docs/milestones/47_3_mapas_turbomaquinaria.md) y [aprendizaje](docs/milestones/47_3_mapas_turbomaquinaria_APRENDIZAJE.md).

- **Milestone 47.2: admisión y caudal condicionado (sin commit).** Captación exterior en vuelo y sección local de compresor a Mach prescrito; recuperación de presión total y diagnóstico de continuidad, sin fabricar aspiración en estático. [Técnico](docs/milestones/47_2_admision_y_caudal.md) y [aprendizaje](docs/milestones/47_2_admision_y_caudal_APRENDIZAJE.md).

- **Milestone 47.1: caudal de gases con geometría de tobera fija (sin commit).** Nueva alternativa al caudal impuesto; continuidad en garganta/salida cp(T), dosado aire/gas y régimen subsónico/bloqueado/choque sin reescribir solucionadores. [Técnico](docs/milestones/47_1_caudal_geometria_fija.md) y [aprendizaje](docs/milestones/47_1_caudal_geometria_fija_APRENDIZAJE.md).

- **Sensibilidad geométrica de la semidivergencia (milestone 46.3, sin commit).** Gráfica y tabla de longitud frente a α manteniendo áreas fijas, tres conos a escala común, selección explícita y ejes/tolerancias axiales corregidos; ninguna afirmación de óptimo aerodinámico. [Técnico](docs/milestones/46_3_estudio_angulo_longitud.md) y [aprendizaje](docs/milestones/46_3_estudio_angulo_longitud_APRENDIZAJE.md).

- **Perfiles axiales de Mach y presión (milestone 46.2, sin commit).** Transformación geométrica de A/Ag a x [m] para los estados físicos del M44.4 mediante el cono 46.1; discontinuidades de choque conservadas y gráficos coordinados sin modificar el solver. [Técnico](docs/milestones/46_2_perfiles_axiales_tobera.md) y [aprendizaje](docs/milestones/46_2_perfiles_axiales_tobera_APRENDIZAJE.md).

- **Geometría cónica axisimétrica del divergente (milestone 46.1, sin commit).** Conversión educativa de áreas físicas del M45 en radios y longitud del tramo divergente a partir de semidivergencia validada, dibujo proporcional y resultados no disponibles explícitos; sin alterar el flujo ni optimizar rendimiento. [Técnico](docs/milestones/46_1_geometria_conica_tobera.md) y [aprendizaje](docs/milestones/46_1_geometria_conica_tobera_APRENDIZAJE.md).

- **Caudal, empuje absoluto y dimensionamiento mínimo (milestone 45, preparado para revisión, sin commit).** Extensión algebraica opcional que escala el motor existente con un caudal de aire, cierra fuerzas y continuidad y dimensiona áreas y diámetros equivalentes de garganta y salida para toberas convergentes y C-D; la interfaz conserva el funcionamiento específico previo. [Técnico](docs/milestones/45_gasto_masico_dimensionamiento_turborreactor.md) y [aprendizaje](docs/milestones/45_gasto_masico_dimensionamiento_turborreactor_APRENDIZAJE.md).

- **Perfiles cuasi-1D de Mach y presión en tobera C-D (milestone 44.4, sin commit).** Cálculo de estados intermedios con cp(T) variable frente a `A/Ag`, selección de rama física, conservación regional y choque normal discontinuo con crítica posterior propia. Sin geometría axial inventada; gráfico discreto conservado. [Técnico](docs/milestones/44_4_perfiles_cuasidimensionales_tobera.md) y [aprendizaje](docs/milestones/44_4_perfiles_cuasidimensionales_tobera_APRENDIZAJE.md).

- **Balance energético por etapas del turborreactor (milestone 44.3, sin commit).** Cuatro transferencias no aditivas normalizadas por kg de aire, cierre separado de compresor, cámara, turbina, eje y tobera, indisponibilidad explícita cuando falta salida y pruebas de coherencia; sin alterar el solver. [Técnico](docs/milestones/44_3_balance_energetico_turborreactor.md) y [aprendizaje](docs/milestones/44_3_balance_energetico_turborreactor_APRENDIZAJE.md).

Estos hitos resumen capacidades ya implementadas en la versión analizada, sin atribuirles fechas ni reconstruir un historial de commits. Los detalles del funcionamiento actual se explican en las secciones anteriores.

- **Estados discretos de Mach y presión estática en tobera (milestone 44.2, sin commit).** Series coordinadas de garganta, choque y salida con referencias a M=1 y p∞; abscisa categórica sin geometría ficticia, lectura y pruebas sobre datos existentes. [Técnico](docs/milestones/44_2_mach_presion_tobera.md) y [aprendizaje](docs/milestones/44_2_mach_presion_tobera_APRENDIZAJE.md).

- **Gráficas de empuje y T–s (milestone 44.1, sin commit).** Descomposición firmada del empuje específico con identidad de cierre, estados discretos de remanso y escape estático opcional con `cp(T)`, SVG accesibles y limitaciones físicas explícitas. [Técnico](docs/milestones/44_1_graficas_empuje_ts_turborreactor.md) y [aprendizaje](docs/milestones/44_1_graficas_empuje_ts_turborreactor_APRENDIZAJE.md).

- **Interfaz educativa del turborreactor (milestone 43, commit `d61ef3795ae58027927adc5077409bb3dfe6b018`).** Ingeniería: interpretación conjunta de empuje, consumo, estaciones, expansión, OFAT y mapas, con límites explícitos. Jinja/JS: seis secciones con dos pestañas accesibles, macros educativas y único botón de simulación sin cambiar el modelo físico. [Técnico](docs/milestones/43_interfaz_educativa_turborreactor.md) y [aprendizaje](docs/milestones/43_interfaz_educativa_turborreactor_APRENDIZAJE.md).

- **Choques normales cuasi-1D con cp(T) variable (milestone 42.C).** Ingeniería: conservación y segunda ley, presión total decreciente, choque localizado por relación de áreas y salida subsónica. Python: raíces físicas acotadas, nuevos estados de salida y diagnóstico web/estudios. [Técnico](docs/milestones/42c_choque_normal_tobera_cd_cp.md) y [aprendizaje](docs/milestones/42c_choque_normal_tobera_cd_cp_APRENDIZAJE.md).

- **Tobera C-D ideal cp(T) independiente (milestone 42.A; revisión local).** Ingeniería: garganta crítica, ramas de área, contrapresión, adaptación, régimen de choque no resuelto y empuje específico de tobera; Python: bisección de flujos por área, diagnósticos explícitos y verificación de compatibilidad convergente. Sin conexión con Flask ni con el motor. [Técnico](docs/milestones/42a_tobera_convergente_divergente_cp.md) y [aprendizaje](docs/milestones/42a_tobera_convergente_divergente_cp_APRENDIZAJE.md).

- **Sensibilidad y mapas paramétricos web del turborreactor (milestone 41).** Ingeniería: OFAT de un parámetro, mapas rp–T3 y Mach–altitud, estados inadmisibles, extremos discretos y Pareto solo bajo ambientes comparables; Python: adaptador de controles y SVG, tres formularios sin anidar, límites de malla, reutilización de barridos M38 y pruebas integradas en Actions. Véanse [milestone 41](docs/milestones/41_prestaciones_web_turborreactor_cp.md) y [aprendizaje](docs/milestones/41_prestaciones_web_turborreactor_cp_APRENDIZAJE.md).

- **Primera pantalla web para el turborreactor (milestone 40).** Ingeniería: estaciones de remanso/estáticas, entrada ISA o directa, empuje bruto/neto, consumo específico y diagnósticos de tobera; Python: ruta Flask aislada, validación estricta, plantilla Jinja2, CSS propio y tres SVG sin modificar el motor científico. Véanse [milestone 40](docs/milestones/40_integracion_web_turborreactor_cp.md) y [aprendizaje](docs/milestones/40_integracion_web_turborreactor_cp_APRENDIZAJE.md).

- **Mantenimiento de la suite histórica tras la migración cp(T).** Ingeniería:
  se conservan los contrastes físicos del gas perfecto sin confundirlos con
  las comprobaciones del aire de propiedades variables; la integridad de
  metadatos heredados se verifica en lectura, sin recalcular un ciclo
  distinto. Python: `unittest.load_tests`, `TestSuite`, manifiesto explícito
  de contratos obsoletos, importación dinámica y GitHub Actions sobre el
  perfil vigente completo. Véanse [milestone 30](docs/milestones/30_saneamiento_suite_historica.md)
  y [guía educativa 30](docs/milestones/30_saneamiento_suite_historica_APRENDIZAJE.md).

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

- **Fase 4: sensibilidad paramétrica OFAT.** Ingeniería: comparación de rp fija y objetivos reajustados, derivadas absolutas/elasticidades y límites de disponibilidad. Python: copias por muestra, arrays con NaN, callback con caché local, contraste de pasos y rutas de acción independientes; informes comparten publicación/retención. Véase [milestone](docs/milestones/06_sensibilidad_parametrica.md) y [aprendizaje](docs/milestones/06_sensibilidad_parametrica_APRENDIZAJE.md).

- **Rediseño del dashboard, independiente de fases físicas.** Ingeniería: presentación de KPI, comparación de objetivos y trazabilidad sin modificar el modelo. Python/web: plantilla compartida, mejora progresiva, navegación por fragmentos, visores sin duplicar PNG, fuentes locales y metadatos JSON. Véase [milestone](docs/milestones/07_rediseno_dashboard.md) y [aprendizaje](docs/milestones/07_rediseno_dashboard_APRENDIZAJE.md).

- **Fase 5: mapa de diseño rp–T3.** Ingeniería: región motora bidimensional, fronteras, trayectorias A/B y cortes a siete parámetros fijos. Python: matrices orientadas por temperatura, máscaras, datos reutilizados, color discreto y controles de cálculo acotados. Véanse [milestone 08](docs/milestones/08_mapa_diseno_rp_t3.md) y [guía educativa](docs/milestones/08_mapa_diseno_rp_t3_APRENDIZAJE.md).

- **Fase 6: segunda ley y exergía de equipos adiabáticos.** Ingeniería: entropía relativa, generación y Gouy–Stodola, suma parcial compresor+turbina, sin atribuir generación a la cámara. Python: análisis de estados existentes, copias profundas para T0 y dos SVG autónomos; [milestone 09](docs/milestones/09_segunda_ley_exergia.md) y [aprendizaje](docs/milestones/09_segunda_ley_exergia_APRENDIZAJE.md).

- **Milestone 34: acoplamiento monoeje cp(T).** Ingeniería: balance de potencia de eje, eficiencia mecánica y determinación de presión de turbina por estado isentrópico, distinguiendo margen de expansión de empuje. Python: solucionador independiente, reutilización de inversores monótonos y clasificación de presión sin interfaz; [documento técnico](docs/milestones/34_acoplamiento_turbomaquinaria_cp.md) y [aprendizaje](docs/milestones/34_acoplamiento_turbomaquinaria_cp_APRENDIZAJE.md).

- **Milestone 35: tobera convergente cp(T).** Ingeniería: remanso frente a estático, expansión con eficiencia, Mach crítico por propiedades variables, cantidad de movimiento y empuje por presión. Python: bisección sónica independiente, estados y diagnósticos estructurados, composición del núcleo sin cambiar contratos; [documento técnico](docs/milestones/35_tobera_cp_variable.md) y [aprendizaje](docs/milestones/35_tobera_cp_variable_APRENDIZAJE.md).

- **Milestone 36: vuelo subsónico y difusor cp(T).** Ingeniería: perfil ISA por capas, recuperación de entalpía de remanso, pérdida de presión total, distinción pt2/p∞ y resta del momento entrante. Python: composición de modelos con referencias correctas, ambiente mutuamente excluyente, diagnóstico de empuje negativo o indefinido, sin cambios en ciclos previos; [técnico 36](docs/milestones/36_condiciones_vuelo_cp.md) y [aprendizaje](docs/milestones/36_condiciones_vuelo_cp_APRENDIZAJE.md).

- **Nuevo Plan de Mejoras, Fase 1: verificaciones y sensibilidad numérica (Tareas 1.1–1.5, cierre técnico publicado).** Ingeniería: referencias analíticas, raíces y dominios abiertos, contraste con SciPy, control de mallas y tolerancias, balances e invariantes del modelo ideal/no ideal; sin validación experimental ni cambio de ecuaciones. Python: `unittest.subTest`, errores y residuos, importación opcional de SciPy, `skipIf`, pruebas parametrizadas y reproducción con entorno virtual. Se ejecutó una única suite completa de 215 métodos en Linux. Véanse [aprendizaje de la nueva fase](docs/milestones/11_verificacion_numerica_APRENDIZAJE.md) y [cierre técnico publicado](docs/milestones/12_cierre_verificacion_numerica.md), commit `cd3349c`; no se confunde con la antigua Fase 1 de dominio viable.

- **Verificación V.1 de Sensibilidad OFAT (publicada, `8d767b6`).** Ingeniería: ecuaciones reconstruidas para R, derivadas de sus cinco entradas, regla del cociente, elasticidades, envolvente del óptimo A y contraste independiente de B con SciPy; sin nuevos modelos ni algoritmos de producción. Python: helpers de referencia aislados en tests, pruebas parametrizadas, omisión explícita de dependencia opcional y comprobaciones de ausencia de resultados motores. Ocho pruebas nuevas y 29 regresiones relacionadas correctas en Linux; véase [milestone técnico 13](docs/milestones/13_verificacion_sensibilidad.md).

- **Verificación V.2 del Mapa de Diseño (publicada, `d6f9dc9`).** Ingeniería: reconstrucción independiente de estados, energía, discriminante y fronteras abiertas del plano rp–T3; máximos continuos A/B, bandas numéricas, primeras leyes y errores de discretización. Python: testigos por celda, mallas anidadas, máscaras `np.ma`, inspección focalizada de datos entregados a Matplotlib y SciPy opcional. Nueve pruebas nuevas y 21 regresiones del mapa correctas en Linux; véase [milestone técnico 14](docs/milestones/14_verificacion_mapa_diseno.md).

- **Verificación V.3 de Segunda Ley y Exergía (pendiente de revisión).** Ingeniería: referencias decimales de entropía, balances exergéticos alternativos de compresor/turbina, cámara sin atribución de generación, invariantes y límites de representabilidad. Python: `Decimal.ln`, `subTest`, aserciones con errores absolutos e intercepción temporal de trazas Matplotlib. Nueve pruebas nuevas y 22 regresiones pertinentes correctas en Linux; véase [documento técnico 15](docs/milestones/15_verificacion_segunda_ley.md).

- **Diagnóstico y coherencia física en cada informe (revisión focalizada completada; sin commit).** Ingeniería: residuos y tolerancias por magnitud, distinción entre identidades, contrastes del mismo modelo y restricciones, disponibilidad de Segunda Ley y naturaleza de los óptimos. Python: registros homogéneos, generadores y agregación de estudios completos, separación entre motor/orquestación/HTML y persistencia del panel. Pertenece a la fase vigente de verificación, sin cambiar el modelo ni ejecutar V.1–V.5 por informe; queda pendiente la inspección visual real y cotejar la copia con Windows. Véanse [milestone 18](docs/milestones/18_diagnostico_fisico.md) y [aprendizaje §12](docs/milestones/11_verificacion_numerica_APRENDIZAJE.md).

- **Fase 2A del nuevo plan: propiedades caloríficas variables del aire.** Ingeniería: mezcla molar ideal N₂/O₂/Ar, correlaciones Shomate contrastadas con NIST, h y s0 continuas por integración y referencia a 298,15 K/1 bar, cp y gamma dependientes de T; el ciclo histórico sigue intacto. Python: módulo independiente sin dependencias externas, tablas de coeficientes, funciones internas, validación estricta y bisección monótona de entalpía. Véanse [milestone técnico 19](docs/milestones/19_cp_variable_aire.md) y [guía de aprendizaje de Fase 2A](docs/milestones/19_cp_variable_aire_APRENDIZAJE.md).

- **Fase 2B del nuevo plan: solucionador independiente con cp(T).** Ingeniería: estados por raíces de entropía isentrópica, eficiencias por saltos de entalpía, balances de primera ley y generación de entropía adiabática, clasificación de puntos no motores y límite térmico 200–2000 K. Python: retorno estructurado, bisección acotada, excepciones específicas y pruebas con cuadratura independiente; originalmente no estaba integrado en Flask, aunque ahora sí se reutiliza mediante la capa web. Véanse [milestone 20](docs/milestones/20_ciclo_cp_variable.md) y [aprendizaje](docs/milestones/20_ciclo_cp_variable_APRENDIZAJE.md).

- **Fases 2C–2D del nuevo plan: optimización e integración cp(T).** Ingeniería: dominio motor abierto y objetivos A/B independientes; propiedades y balances variables en el navegador. Python: búsqueda numérica por derivadas, presentadores SVG y pruebas Flask mediante Actions. La primera integración de 2D usaba una página secundaria que ya no forma parte del código actual. Véanse [milestone 21](docs/milestones/21_optimizacion_cp_variable.md), [milestone 22](docs/milestones/22_integracion_web_cp_variable.md) y §4.61.

- **Milestone 23: interfaz única con cp(T).** Ingeniería: un solo modelo activo, parámetros variables, estados y optimización A/B; se evitan prestaciones engañosas de apartados aún no adaptados. Python: reutilización de presentadores en un controlador Flask, condicionales Jinja para separar la lectura histórica de la simulación actual, regresiones HTTP y eliminación de ruta/plantilla redundantes. Véanse [milestone técnico 23](docs/milestones/23_unificacion_dashboard_cp_variable.md) y [aprendizaje 23](docs/milestones/23_unificacion_dashboard_cp_variable_APRENDIZAJE.md).

- **Fase 2E, milestone 24: sensibilidad OFAT cp(T).** Ingeniería: variar exactamente un parámetro, conservar balance de energía, distinguir estados no motores y huecos del dominio, elasticidades locales de diferencias finitas y estabilidad por refinamiento. Python: módulo independiente que reutiliza 2B, separación cálculos/SVG/Flask, validación del formulario y tests HTTP focalizados. Véanse [milestone técnico 24](docs/milestones/24_sensibilidad_cp_variable.md) y [aprendizaje 24](docs/milestones/24_sensibilidad_cp_variable_APRENDIZAJE.md).

- **Fase 2F, milestone 25: mapas rp–T3 con cp(T).** Ingeniería: exploración de dos factores y región motora en 2D; prestaciones enmascaradas fuera del dominio; máximo discreto frente a óptimos A/B de 2C a una T3 de referencia. Python: matrices de diccionarios, doble bucle de solución reutilizable, `Counter`, máscara por `None`, SVG interactivo mediante `<title>`, formulario Flask de cálculo explícito y cota de tamaño. Véanse [milestone técnico 25](docs/milestones/25_mapa_diseno_cp_variable.md) y [aprendizaje 25](docs/milestones/25_mapa_diseno_cp_variable_APRENDIZAJE.md).

- **Fase 2G, milestone 26: Segunda ley y exergía de las turbomáquinas cp(T).** Ingeniería: entropía de estados, Gouy–Stodola, balance exergético independiente, referencia ambiental T0/p0 y límite de la suma parcial; rendimientos de componentes con aplicabilidad física. Python: análisis postprocesado de estados 2B, caché acotada por parámetros físicos, datos y diagnósticos estructurados, SVG basado en destrucciones calculadas, acción Flask específica y pruebas de regresión. Véanse [milestone técnico 26](docs/milestones/26_segunda_ley_cp_variable.md) y [aprendizaje 26](docs/milestones/26_segunda_ley_cp_variable_APRENDIZAJE.md).

- **Iteración 1 de revisión educativa y visual, milestone 27.** Ingeniería: objetivos, hipótesis, procedimientos, interpretación y límites explicados en las ocho secciones; comentarios sobre prestaciones vinculados al estado motor y al criterio de disponibilidad. Python/HTML/JS/CSS: nuevo módulo de contenidos estáticos y ayudas, estructura de pestañas uniforme, macro Jinja para ocho gráficas SVG compactas con visor modal ampliado y responsive; sin tocar 2A–2G. Véanse [milestone técnico 27](docs/milestones/27_revision_educativa_visual_cp.md) y [aprendizaje 27](docs/milestones/27_revision_educativa_visual_cp_APRENDIZAJE.md).

- **Iteración 2 de fundamentos teóricos, milestone 28.** Ingeniería: notas progresivas de Brayton cp(T) con ecuaciones, algoritmos reales, ejemplos explícitos, interpretaciones y límites en seis secciones científicas; glosario e informes de trazabilidad en otras dos. Python/web: el mismo diccionario editorial entrega contenido HTML controlado; CSS organiza la teoría en una sola columna con ecuaciones y recuadros, sin alterar cálculo ni visor SVG. Véanse [milestone 28](docs/milestones/28_fundamentos_extensos_cp.md) y [aprendizaje 28](docs/milestones/28_fundamentos_extensos_cp_APRENDIZAJE.md).

- **Iteración 3 de gráficas científicas cp(T), milestone 29.** Ingeniería: P–v por gas ideal con R en J/(kg·K), variación cp/γ, balances energéticos, ideal de componentes frente a configuración real y dos objetivos de optimización con compromiso W–η. Python/SVG: módulo de representación separado, transformaciones de coordenadas y ticks, enmascaramiento por None, reutilización de 90 muestras, marcadores de extremos interiores y pruebas de datos incrustados. Véanse [milestone 29](docs/milestones/29_graficas_resultados_optimizacion_cp.md) y [aprendizaje 29](docs/milestones/29_graficas_resultados_optimizacion_cp_APRENDIZAJE.md).

- **Milestone 37: combustible energético y TSFC de turborreactor cp(T).** Ingeniería: dosado combustible/aire, balance de cámara en referencia sensible única, aumento del caudal de turbina, nuevo cierre del eje y empuje con ambos términos de salida multiplicados por `1+f`; TSFC solo con empuje neto positivo, sin química real. Python: módulo científico independiente, funciones auxiliares pequeñas, dicts de componentes y valores indefinidos `None`, tests de referencia, límite matemático sin combustible. Véanse [milestone técnico 37](docs/milestones/37_combustible_tsfc_cp.md) y [aprendizaje 37](docs/milestones/37_combustible_tsfc_cp_APRENDIZAJE.md).

- **Milestone 38: mapas paramétricos y compromisos de turborreactor cp(T).** Ingeniería: cambios prescritos de rp/T3 y Mach/altitud, empuje por unidad de caudal, consumo, viabilidad y frontera Pareto **solo en ambientes comparables**, sin mapa real fuera de diseño. Python: doble barrido ordenado, puntos y máscaras anidadas, `Counter`, extremos discretos, clasificación de errores y dominancia cuadrática verificable. Véanse [milestone 38](docs/milestones/38_mapas_prestaciones_turborreactor_cp.md) y [aprendizaje 38](docs/milestones/38_mapas_prestaciones_turborreactor_cp_APRENDIZAJE.md).

- **Milestone 39: verificación científica independiente del turborreactor.** Ingeniería: ecuaciones revisadas por gas caloríficamente perfecto separado, errores absolutos/relativos y continuidad de bloqueo, distinción entre variación de hipótesis, defecto de software y validación experimental pendiente. Python: tests con referencia independiente, Cantera opcional y corrección puntual de los filtros `exigir_*` de mapas sin modificar estados físicos ni optimizadores. Véanse [milestone 39](docs/milestones/39_verificacion_independiente_turborreactor_cp.md) y [aprendizaje 39](docs/milestones/39_verificacion_independiente_turborreactor_cp_APRENDIZAJE.md).

