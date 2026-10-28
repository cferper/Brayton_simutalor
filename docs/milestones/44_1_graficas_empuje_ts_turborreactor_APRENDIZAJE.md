# Milestone 44.1 — Aprendizaje: ¿de dónde sale el empuje y qué enseña T–s?

## 1. Cómo leer las barras de empuje

Imagina que por la entrada entra 1 kg/s de aire: el motor proporciona un empuje específico, medido en **N/(kg/s de aire)**. La salida incluye aire y combustible, por eso el modelo considera `(1+f)` kg/s al calcular las contribuciones del chorro. La entrada de aire avanzando con el avión resta empuje. La diferencia entre presión de escape y ambiente puede empujar o frenar.

Las cuatro barras son: (1) momento de salida, (2) resistencia por velocidad de entrada —negativa—, (3) empuje de presión —firmado— y (4) suma neta. La barra neta **no es una cuarta contribución**, sino el resultado de las otras tres.

Ejemplo calculado para el formulario inicial (Mach 0):

| Término | N/(kg/s de aire) |
|---|---:|
| Salida | +681.304221 |
| Entrada | 0 |
| Presión | +276.953463 |
| **Neto** | **+958.257683** |

Prueba a aumentar Mach: aumenta el término de entrada negativo y también cambian otros estados. No esperes que el neto se obtenga restando solo la nueva velocidad al caso anterior: el motor completo se vuelve a resolver.

Si la tobera no tiene estado de salida resuelto, el gráfico **no dibuja ceros**; una magnitud desconocida no es una magnitud nula. Tampoco convierte el empuje específico en newtons absolutos: para eso faltaría indicar el caudal real de aire.

## 2. Entropía con calor específico variable

El eje horizontal de T–s es `s` [kJ/(kg·K)], y el vertical `T` [K]. La rutina `propiedades_aire.s(T,p)` evalúa la entropía del modelo de aire equivalente con `cp(T)` variable:

\[s(T,p)=s_0(T)-R\ln(p/P_{ref}).\]

La función `s0(T)` ya incluye la dependencia térmica de `cp(T)`; no reemplazarla por `cp_constante × ln(T/T_ref)`.

Se marcan **1–4 de remanso**: 1 después del difusor, 2 salida de compresor, 3 salida de cámara y 4 salida de turbina. Si existe salida válida de tobera, se agrega **E estático**. El diagrama identifica este cambio de tipo: temperatura total y temperatura estática no significan lo mismo.

Las líneas discontinuas sirven para reconocer qué componentes conectan cada par de estados; **no** significan que el solver conozca todas las condiciones intermedias. Tampoco se debe leer su pendiente como una ley del proceso. En compresor y turbina, las irreversibilidades desplazan los estados respecto a los ideales isentrópicos. La cámara aporta combustible, pero el modelo conserva una composición de aire equivalente: por eso la diferencia de `s` entre 2 y 3 no se anuncia como entropía rigurosa de combustión.

## 3. Qué funciones nuevas leer primero

1. `datos_empuje_grafica(resultado)` obtiene las cuatro contribuciones de la solución numérica y verifica la igualdad de la suma; da `None` cuando faltan datos.
2. `svg_descomposicion_empuje(resultado)` convierte esas magnitudes en barras accesibles sin modificar ningún cálculo.
3. `datos_ts_turborreactor(estaciones)` toma las temperaturas y presiones de la tabla, llama a `s(T,p)` y identifica remanso frente a estático.
4. `svg_ts_turborreactor(estaciones)` coloca los puntos en los ejes y añade conexiones **esquemáticas**.
5. `preparar_vista_turborreactor(resultado)` recoge los nuevos SVG para la plantilla Jinja.

El test `tests/test_graficas_turborreactor_44_1.py` comprueba su coherencia mediante **siete métodos**. La revisión Windows del 27/10/2026 incorpora también integración Flask/Jinja y navegador real; las pruebas numéricas no sustituyen la revisión de legibilidad.


## 4. Integración y aprendizaje de la revisión Windows — 27/10/2026

**Punto de partida verificado.** Windows estaba en `mejoras/cp-variable`,
commit base `d61ef3795ae58027927adc5077409bb3dfe6b018` (M43), con los archivos
versionados limpios y dos archivos personales no versionados que se conservan.
Se integra el ZIP acumulado de 44.1/44.2; esta fecha documenta la revisión,
no inventa la fecha de desarrollo de cada función. La fase sigue sin commit propio.

**PYTHON / PRESENTACIÓN.** Una prueba antigua contaba tres regiones SVG.
Ahora hay siete: la comparación se actualiza, pero se conserva que **cada una**
tenga nombre accesible, `role="region"` y `tabindex="0"`. Así se verifica el
contrato de teclado sin confundir ampliación de pantalla con fallo del modelo.
En `svg_ts_turborreactor(estaciones)` la condición
`texto_y = y + 20 if label == 'E' else y - 9` es una expresión condicional:
solo escoge dónde escribir el texto. E se rotula debajo para separarlo de 4.
`paint-order="stroke"` dibuja primero un contorno blanco en las letras y
protege su lectura frente a las líneas. El máximo de 420 px mejora el tamaño
legible; las coordenadas físicas de los puntos no cambian. Es una corrección
de presentación, sin nueva función ni modificación de la firma.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Con choque, T estática de E puede
quedar cercana a T total de 4, aunque sus entropías sean distintas. Esa
proximidad explica el solapamiento visual, pero no autoriza a desplazar los
puntos físicos. Se desplazan los rótulos. Al cambiar Mach de vuelo, el motor
completo se vuelve a resolver; un Mach de salida todavía igual a 1 puede
ser correcto si la convergente sigue bloqueada.

**Ejercicio reproducible.** Simular Motor estático; en Resultados comprobar
681.304221 + 0 + 276.953463 ≈ 958.257683 N/(kg/s de aire). Cargar Mach 0,7
y simular de nuevo: la entrada es −238.218634 y el neto 758.381570. En
Visualizaciones distinguir los cuatro puntos totales de E estático. Después
seleccionar C-D y Ae/Ag=6: el nuevo T–s permite leer 4 y E por separado.
En pantalla estrecha, enfocar el gráfico y usar flechas para ver sus extremos.

**Comprobación real.** 16/16 específicas acumuladas, 74/74 web y regresión
vigente de 625 (615 correctas, diez omisiones justificadas, cero fallos/errores).
Tras corregir el rótulo: 90/90 específicas/web. También se comprueban cinco
POST y cinco casos en navegador. El intento inicial con temporales bloqueados
se conserva separado de estos resultados en el [técnico 44.2](44_2_mach_presion_tobera.md).
No hay validación experimental ni cambios de ecuaciones. Firmas, tipos,
retornos, unidades, errores y llamadas de las funciones: [manual §4.81](../../CODE_WALKTHROUGH.md).
