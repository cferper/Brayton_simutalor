# Aprendizaje — Milestone 50.4: exploración del motor acoplado

## 1. Qué teníamos y qué queríamos aprender

El M49.5 ya permitía recorrer una malla de Mach y T3, dibujar celdas y calcular empuje/TSFC. El M47 resolvía un motor monoeje mediante mapas escalados, M50.2 añadía magnitudes corregidas, M50.3 proporcionaba puntos comprobados y M50.1 guardaba una referencia para comparar. **La novedad no es un solucionador físico**: es hacer consultables las magnitudes de cada punto del estudio existente y reutilizar ese punto como entrada del banco.

Estamos trabajando en `mejoras/cp-variable`, sobre el commit publicado `460749bc92de7b7cfb660dbcf0f6606a7c521855` (12-11-2026). El ZIP inicial era incremental; no se han tocado referencias Git.

## 2. INTERPRETACIÓN FÍSICA / INGENIERÍA

### 2.1. Qué significa que el punto sea válido

En el modo C, las incógnitas principales son el giro del eje, la coordenada Rline del mapa de compresor y la expansión de turbina. Su equilibrio exige continuidad en los componentes y compatibilidad de potencia. El solucionador M47 calcula un vector de **residuos normalizados** y su norma final. La condición de aceptación está implementada en M47 (`disponible=True`), que verifica también cierres dimensionales; el estudio **consulta esa aceptación**, no introduce otras ecuaciones o tolerancias.

La expresión `norma_residual = 0` del punto de diseño calibrado es posible porque se parte de una referencia construida para satisfacer el modelo. En otros puntos pueden hacer falta varias iteraciones; una norma pequeña es un control interno del modelo, no un contraste experimental. Una iteración de Newton es un paso de ajuste del sistema acoplado, no un segundo tiempo físico real.

### 2.2. Caudales y velocidades corregidos

Para comparar puntos del compresor, el M50.2 utiliza las propiedades **totales** a la entrada del compresor, no las condiciones estáticas del ambiente, y unas magnitudes normalizadas a las referencias del mapa:

\[
\dot m_{\mathrm{corr}}=\dot m_a\,\frac{\sqrt{T_{t1}/T_{\mathrm{ref}}}}{p_{t1}/p_{\mathrm{ref}}},\qquad
N_{\mathrm{corr}}=\frac{N}{\sqrt{T_{t1}/T_{\mathrm{ref}}}}.
\]

El factor exacto y las referencias que utiliza el código permanecen en `mapas_turbomaquinaria_47.py`. El estudio llama a `diagnosticar_motor_50_2(resultado)`, no vuelve a escribir estas expresiones. En A/B se puede conocer un caudal corregido, pero **no** unas rpm determinadas por mapas: el presente milestone agrega las variables nuevas de compresor únicamente para C, conservando el resultado anterior de A/B.

### 2.3. Interpretar los estados con prudencia

| `clasificacion` | Evidencia y alcance |
|---|---|
| `convergencia_verificada` | El solucionador M47 aceptó el punto según sus comprobaciones |
| `entrada_fuera_dominio` | Datos o propiedades fuera de restricciones explícitas |
| `fuera_mapa` | Consulta fuera del intervalo tabulado reconocido |
| `sin_convergencia_numerica` | El algoritmo no confirmó la solución; **no implica que no exista** |
| `modelo_no_resuelto` | Algún régimen o componente no dispone de salida implementada |
| `causa_indeterminada` | No hay evidencias suficientes para atribuir causa concreta |

**Rline no es un margen de surge**: es una coordenada que parametriza un mapa educativo escalado. No debe trazarse una frontera física entre celdas verdes y grises. El mapa puede fallar por limitación del método, de dominio o por regímenes no implementados.

## 3. PYTHON — estructuras, tipos y flujo

### 3.1. `configurar_estudio_49_5(configuracion, modo)`

**Argumentos:** `configuracion: dict` con `tipo` y los intervalos/puntos, `modo: str` entre `impuesto`, `fijo`, `acoplado`. **Resultado:** `dict` con listas `x`/`y`, sus nombres y `tipo`. Mach se mide adimensionalmente, T3 en kelvin. El modo C conserva 9 puntos por curva y hasta 6×6 por mapa. **Errores:** `ValueError` si intervalos, número entero de puntos, límites o tipo no son válidos. **Llamada por:** `calcular_estudio_49_5`. **Llama a:** la función local `eje(nombre)` para cada eje.

Ejemplo: `configurar_estudio_49_5({'tipo':'mapa','mach_inicio':0,'mach_fin':0.4,'mach_puntos':2,'T3_inicio':1550,'T3_fin':1650,'T3_puntos':3}, 'acoplado')` devuelve una malla de 2×3 puntos. Una malla 7×6 en C produce un error, sin comenzar cálculos.

### 3.2. `calcular_estudio_49_5(valores, configuracion)`

**Argumentos:** `valores: dict[str,str]` con entradas completas de formulario, incluidas áreas si corresponde; `configuracion: dict` validado internamente. **Resultado:** objeto JSON con `ejes`, `constantes`, `modo`, `tipo`, `unidades`, `puntos` y `resumen`. Su entrada es `POST /api/turborreactor/estudio` a través de `web_app.api_estudio_parametrico_49_5()`; llama una vez por celda a `simular_turborreactor`.

El patrón:

```python
parametros = dict(valores)                  # Copia independiente por celda
parametros['mach'] = format(x, '.12g')       # Variable que se barre
resultado = simular_turborreactor(parametros) # Único cálculo físico
```

`dict(valores)` crea una copia superficial suficiente porque el diccionario de entrada contiene cadenas inmutables, no listas u objetos anidados. Las condiciones no barridas se conservan en `constantes`. En C, `punto['entradas']` guarda las cadenas completas de esa celda, para trasladarlas después al banco. Si el cálculo falla, los números ausentes siguen siendo `None`; `json` los transforma en `null`, **no en 0**.

### 3.3. `_magnitudes_c_50_4(resultado)`

**Argumento:** `resultado: dict` procedente de `simular_turborreactor` de C. **Devuelve:** `dict[str, float|int|None]` con caudal [kg/s], corregido [kg/s ref.], rpm, rpm corregidas, relación de presión, rendimiento, Rline, iteraciones y norma residual, estos últimos adimensionales. **Validación:** exige `motor_acoplado.disponible is True` y norma residual finita; si no, `ValueError`. **Llama a:** `diagnosticar_motor_50_2`, que reutiliza los estados del cálculo. **Llamada por:** `calcular_estudio_49_5` solamente después de que la tobera disponga de salida.

Ejemplo: para un resultado C del diseño M50.3, los campos `'rpm'` y `'iteraciones'` proceden de `resultado['motor_acoplado']`, mientras `'caudal_corregido'` se extrae de `diagnosticar_motor_50_2`. Es importante no recalcular una velocidad mecánica a partir de un gráfico de presentación.

### 3.4. `_diagnostico_fallo_c_50_4(mensaje, *, excepcion=None)`

**Argumentos:** `mensaje: str`, `excepcion: type|None` opcional y solo por palabra clave (`*`). **Retorno:** tupla `(estado_heredado: str, diagnostico: dict)`; el dict incluye `codigo`, `evidencia`, `resumen`, `recomendacion`. **Llama a:** `diagnosticar_fallo_50_3`; lo llama `calcular_estudio_49_5` al capturar excepciones. **Errores:** el llamador captura los tipos de error del modelo; esta función no provoca un nuevo cálculo físico.

El modificador `*, excepcion=None` evita pasar accidentalmente una segunda cadena como si fuese una clase. El mapa de clases `CLASES_C` es un diccionario donde cada evidencia reconocida produce una clasificación nueva y su `estado` antiguo. Así el cliente M49.5 previo puede seguir consultando `estado`.

## 4. JAVASCRIPT — visualización y aplicación sin duplicación

### 4.1. El visor existente

`iniciar49(doc, fetcher)` recibe el documento DOM y la función `fetch` (o sustituto de prueba), y devuelve un controlador de exportación para el panel existente. Gestiona `datos`, índice de selección, guardados y versión de petición; el navegador no ejecuta el solver. `svgMapa()` y `svgLineas()` siguen creando nodos SVG con `createElementNS`. `svgMapa` colorea categorías o valores numéricos discretos; no interpola entre muestras. `csv49(datos)` devuelve una cadena CSV con cabeceras, unidades, constantes y valores ausentes como celdas vacías. `colorMapa49(valor,min,max)` devuelve únicamente un color HSL visual, no una magnitud científica.

La instrucción:

```javascript
const p = datos.puntos[index];
```

usa `index` para consultar un cálculo ya existente. El evento de `keydown` admite `Enter` y espacio, por lo que no depende exclusivamente del ratón. El selector de magnitud ejecuta `pintar()`, nunca `fetcher()`.

### 4.2. `aplicarPunto50_4({formulario,entradas,aplicarEntradas,preparar,solicitar})`

**Argumento:** objeto con formulario DOM, copia completa de entradas C y tres callbacks de aplicación, preparación de interfaz y solicitud. **Retorna:** `true` si organiza correctamente la operación o lanza `Error` por modo distinto de C o ausencia del cargador. **Llamada por:** el evento `brayton:aplicar-estudio-50-4` gestionado dentro de `inicializar48`. **Llama a:** `aplicarEjemplo50_3`, callbacks visuales y una única invocación de `controlador.cambiar()`.

```javascript
aplicarEntradas(formulario,entradas);  // Copia completa, sin eventos propagados
preparar();                          // Sincroniza pestañas y etiquetas
solicitar();                         // Una sola orden al controlador M48
```

`aplicarEjemplo50_3` ya sincroniza los deslizadores y la presentación de ambiente/tobera. Después, M48 retira resultados obsoletos, solicita `POST /api/turborreactor/simular` y actualiza el mapa HPC M50.2. El laboratorio M50.1 conserva su objeto `referencia`, aunque la comparación actual se invalide hasta recibir el punto nuevo.

### 4.3. Datos obsoletos y coste

Un estudio responde a una instantánea de sus parámetros fijos. Si se usa el banco como base y se modifican sus entradas, el explorador avisa y oculta el botón de aplicar. Si se usa el diseño C verificado, los parámetros del estudio están fijados independientemente del banco. Cambiar solo el color o la magnitud seleccionada no solicita otro cálculo. La cancelación de `fetch` descarta respuestas antiguas; no cancela necesariamente el trabajo de CPU que ya empezó en Flask.

## 5. Recorrido práctico

1. En Estudios paramétricos, seleccionar el diseño C verificado como base (opción inicial).
2. Definir por ejemplo Mach 0–0,4 (2 muestras) y T3 1600–1650 K (2 muestras); pulsar «Calcular estudio» una vez.
3. Leer `resumen.por_clasificacion`, seleccionar rpm o estado y consultar una celda. Si falta un dato, aparece «No disponible», no cero.
4. Si la celda fue aceptada por M47, «Utilizar este punto en el modo C» restaura sus entradas. Solo se inicia una simulación del banco.
5. Guardar antes una referencia en el laboratorio M50.1 permite comparar el nuevo punto cuando se resuelva; diferencias de geometría y parámetros avanzados permanecen visibles.

**Importante:** los pasos son el flujo diseñado; no equivalen a una prueba visual ejecutada en Windows.

## 6. Verificación y límites

El 12-11-2026 se comprobó el ZIP M50.3 recibido y la identidad del código crítico en GitHub. Se ejecutaron **9 pruebas JavaScript correctas** (4 regresiones M50.3 + 5 nuevas M50.4) y **5 controles aislados Python con sustitutos de dependencias correctos**. Se comprobó sintaxis Python/JavaScript. Estos controles verifican los contratos de interfaz, estado y orquestación; no el equilibrio termodinámico M47, porque el ZIP aportado contiene solo 11 archivos y no el núcleo completo ni Flask.

El intento de `unittest discover -s tests -q` en la copia incremental no pudo importar dos módulos de pruebas por ausencia de `acoplamiento_motor_mapa_47`; ese intento no fue una regresión del repositorio completo. Tras integrar el ZIP en Windows, las pruebas reales se ejecutaron sobre el repositorio completo: las 7 pruebas Python focalizadas, 28 pruebas JavaScript y la regresión Python de 822 pruebas terminaron sin fallos (812 correctas, 10 omitidas). También se compararon tres celdas de una malla 5×5 con simulaciones individuales. El usuario revisó y aprobó visualmente la interfaz. Las omisiones corresponden a dependencias opcionales y permisos del entorno; la malla no valida experimentalmente el modelo ni establece una frontera continua. El código científico, el Jacobiano de Newton, los mapas y las tolerancias se mantienen como estaban.

El milestone 50.4 está integrado localmente y aprobado visualmente; su publicación queda pendiente del commit autorizado. La documentación técnica en `50_4_explorador_funcionamiento_modo_c.md` resume contratos y comprobaciones; esta guía explica el aprendizaje sin sustituir el manual vigente `CODE_WALKTHROUGH.md`.
# Registro de integración en Windows — 12-11-2026

Las 7 pruebas Python focalizadas pasaron. La regresión ejecutó 822 pruebas,
con 812 correctas, 10 omitidas y ningún fallo. Las 28 pruebas JavaScript
pasaron después de ajustar la lectura de opciones para el DOM mínimo usado
por la prueba del panel. Una malla 5×5 real calculó 25 puntos convergentes en
8,246 s. Tres puntos se compararon con ejecuciones individuales y coincidieron
en rpm, caudal y empuje. Esto verifica consistencia del programa, no valida el
modelo con datos experimentales. El usuario aprobó la revisión visual.
