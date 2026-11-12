# Aprendizaje del milestone 50.3 — Configuraciones reproducibles de un motor monoeje

## 1. Problema docente

En el modo C ya no se impone libremente el caudal o la relación de compresión: las incógnitas independientes del equilibrio son el régimen mecánico N, la coordenada de carga del compresor `Rline` y la relación de expansión de turbina. Las entradas externas como Mach, TIT (interna `T3`) y área de garganta desplazan el punto operativo. Puede dejar de existir una **solución encontrada numéricamente**, sin que eso pruebe que un motor real sea imposible.

Esta fase **no cambia el solucionador M47**. Enseña a partir de configuraciones reproducidas y diagnostica de forma honesta por qué una tentativa puede fracasar.

## 2. Modelo físico respetado

En régimen estacionario monoeje, el compresor y la turbina comparten la misma velocidad física N, pero sus velocidades corregidas usan las temperaturas totales de entrada respectivas. Los mapas NASA T-MATS de HPC y HPT están escalados a un turborreactor educativo; no son ensayos de un motor real. El solucionador exige simultáneamente:

\[
R_1=\frac{PR_{t,\mathrm{map}}-p_{t3}/p_{t4,\mathrm{eje}}}{PR_{t,d}},\qquad
R_2=\frac{\dot m_a(1+f)-\dot m_{g,\mathrm{map}}}{\dot m_{g,d}},\qquad
R_3=\frac{\dot m_a(1+f)-G_g A_g}{\dot m_{g,d}}.
\]

Cada residuo debe aproximarse a cero, y luego se comprueban balances dimensionales. Aquí `f` es el dosado del combustible equivalente, `Gg` es el flujo másico por área de garganta, y el subíndice `d` corresponde al diseño. Para el trabajo de eje se conserva además el balance energético original con `ηm` y propiedades cp(T). Una solución numérica con residuo pequeño no es validación experimental.

## 3. Ejemplos y límites

Se han reproducido seis casos completos con la implementación actual: diseño (Mach 0, T3 1600 K), Mach 0,4, T3 1550 y 1650 K, presión ambiente 95 kPa y C-D con Ae/Ag=1,2. Todos usan Ag=0,04734811643457149 m² y los demás parámetros de diseño descritos en [el documento técnico](50_3_configuraciones_modo_c.md). Los resultados numéricos completos están allí. No se garantizan valores intermedios ni extrapolación fuera de los mapas.

Ejemplo: el diseño da N=20000 rpm, caudal 20 kg/s y compresión 10; el caso Mach 0,4, con las demás entradas iguales, da aproximadamente N=20139,26 rpm, caudal 21,2896 kg/s y compresión 9,5339. El cambio es una **predicción del modelo acoplado**, no una regla monótona ni una medición.

La prueba con área 1,1 Ag,d termina sin descenso del residuo tras 11 iteraciones. Esto permite afirmar *«no se ha encontrado equilibrio con el método y criterio actuales»*, nunca *«es físicamente imposible»* ni *«hay surge»*.

## 4. Programación: datos completos y copia de formulario

**PYTHON.** `configuraciones_verificadas_50_3(*, referencia=None)` recibe opcionalmente el diccionario del diseño M47 y devuelve una lista de diccionarios con campos `id`, `nombre`, `descripcion` y `entradas`. `entradas` contiene todas las claves de `DEFAULTS_TURBO` y sus valores como cadenas, por ejemplo `{'mach':'0.4','T3':'1600', ...}`. El operador `**` de los diccionarios crea una copia con algunas claves reemplazadas:

```python
entradas = {**base, **{'mach': '0.4'}}
```

No altera `base`. Una caché `@lru_cache(maxsize=1)` evita repetir el cálculo de la calibración M47 cuando Flask necesita presentar la misma selección. No se consulta de nuevo el solucionador al seleccionar un caso en la página. La función llama a la referencia M47 solo si no se proporciona una de forma explícita.

**JS.** `aplicarEjemplo50_3(formulario, entradas)` valida que el caso es C y que están presentes los controles. Escribe sus valores sin emitir eventos `input` a nivel de formulario, sincroniza la visibilidad mediante eventos no propagados y coloca Mach/T3 en sus sliders y textos. Devuelve el mismo diccionario usado. `iniciarConfiguraciones50_3(documento, formulario, onAplicar)` devuelve `{cargar, diagnosticar, exito, pendiente, modificada}` o `null` si falta el panel. El callback `onAplicar()` se invoca una sola vez después de copiar los campos; reutiliza `controlador.cambiar()` y su mecanismo debounced/abortable. No hay un segundo `fetch`.

```javascript
const caso = porClave.get(clave);
aplicarEjemplo50_3(formulario, caso.entradas);
onAplicar(); // programa un solo recálculo del mismo motor
```

La etiqueta `<script type="application/json">` permite que Jinja entregue datos estructurados al navegador de forma escapada (`tojson`), sin código JavaScript generado dinámicamente. Al navegar entre A/B/C, únicamente se muestra la ayuda en C; los ejemplos no reescriben los valores de A/B mientras están seleccionados.

## 5. Programación: mensajes con incertidumbre

**PYTHON.** `diagnosticar_fallo_50_3(mensaje)` recibe un `str` o algo convertible a texto y devuelve `{'codigo','resumen','recomendacion'}`. Comprueba términos específicos en el mensaje del solver; prioriza fallos numéricos cuando aparecen síntomas de Jacobiano o falta de descenso. Si no hay una evidencia clara usa `indeterminado`. No lanza simulaciones ni devuelve resultados físicos. Flask incorpora el objeto únicamente en `error.diagnostico_50_3` para 422 de modo C.

**JS.** El controlador retira estados y gráficas anteriores al actualizar o fallar. `diagnosticar(error)` muestra el mensaje específico, si existe, y si no una recomendación general. La referencia del laboratorio comparativo permanece guardada en su memoria independiente.

## 6. Qué comprobar en Windows

Selecciona el diseño C desde otra configuración avanzada, comprueba que Mach/T3 y todas las áreas vuelven a los valores de referencia y que el mapa HPC sitúa el punto. Luego prueba el caso Mach 0,4 y el caso C-D. Cambia únicamente Ag a 1,1 Ag,d: debe advertir el fallo sin mostrar el antiguo punto de operación ni empuje viejo; prueba «Restablecer punto de diseño C». Alterna A y B y confirma que sus controles siguen funcionando. Ejecuta los tests Python/Node y la regresión general con Flask instalado. Esta revisión del navegador es **pendiente**, no realizada aquí.

## 7. Verificación y estado

Se han ejecutado 7 pruebas Python focalizadas correctas (una prueba HTTP omitida porque falta Flask) y 23 pruebas JavaScript correctas. La regresión Python general ejecutó 498 pruebas con 24 errores de importación por ausencia de Flask y 4 omisiones; no queda aprobada. Se comprobaron sintaxis y plantilla Jinja. Se verificaron reproducción de los casos, residuos, ausencia de empujes inventados y selección sin peticiones extra. Este cambio aún **no tiene commit ni push**; su base confirmada es `39a303545be4d5578c0780d303d583378b9376ea` del 50.2. No constituye validación experimental.
# Verificación local en Windows — 12-11-2026

En la integración Windows pasaron las ocho pruebas Python focalizadas,
incluida la prueba HTTP con Flask, y las 23 pruebas JavaScript. La regresión
completa ejecutó 815 pruebas: 805 correctas, 10 omitidas y ningún fallo.
Las omisiones se deben a SciPy (8), Cantera (1) y permisos de symlinks (1).
Los seis casos del selector reprodujeron los resultados del solucionador
documentados en el milestone técnico. Estos ensayos verifican el código y no
constituyen validación experimental. La inspección visual final queda a cargo
del usuario.
