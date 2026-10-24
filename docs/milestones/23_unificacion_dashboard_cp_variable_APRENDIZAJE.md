# Milestone 23 — Aprendizaje: de dos páginas a un único dashboard cp(T)

## 1. Punto de partida y objetivo (24/10/2026)

Partimos del commit `64b4568a98f36779e305fe80d7c36c9e9498bd1d` en `mejoras/cp-variable`. La web de Fase 2D calculaba cp(T) en una plantilla nueva, mientras que la pantalla principal ejecutaba el modelo de gas perfecto. Queríamos conservar el diseño original, no seleccionar modelos, y evitar resultados de gas constante rotulados erróneamente como cp(T).

Los siete parámetros son T1 y T3 [K], rp [−], p1 [kPa], eta_c y eta_t [fracción] y delta [fracción]. El aire tiene cp(T), gamma(T), entalpía y entropía variables dentro de 200–2000 K.

## 2. Nuevos pasos del flujo

1. GET `/` crea una copia de las entradas por defecto y muestra `index.html` con `modo_cp=True`.
2. El usuario envía POST `/` con acción `normal` o `optimizar`. `leer_entradas` convierte cadenas a números finitos.
3. `preparar_resultados` pide `resolver_ciclo` y `estudiar_cp_variable`; monta la tabla de estados y dos SVG.
4. `renderizar_dashboard` pone los resultados en las secciones originales. No se publica informe HTML.
5. Las acciones de OFAT, mapa y segunda ley se rechazan. Los informes históricos se consultan o descargan por rutas de solo lectura; no se calculan de nuevo.

## 3. Funciones Python: firmas y contratos

- `valores_formulario() -> dict`: sin argumentos; retorna los siete valores de `DEFAULTS` en sus unidades físicas originales; devuelve una copia para evitar mutaciones globales. La llaman `index` y `error_interno`. Ejemplo: `valores_formulario()['rp'] == 10.0`.
- `leer_entradas(form) -> dict[str,float]`: toma el formulario con siete claves, usa `float`, `isfinite` y `strip`; devuelve números finitos, sin convertir delta a porcentaje. Llama desde `index`; `ValueError` para ausencias/no finitos. Ejemplo: `leer_entradas({'T1':'288.15','T3':'1600','rp':'10','p1':'100','eta_c':'.85','eta_t':'.9','delta':'.05'})`.
- `preparar_resultados(entradas) -> dict`: recibe el diccionario de siete valores; devuelve `ciclo` (trabajos/calores en kJ/kg, viabilidad), `estados` (lista de cuatro dict con T [K], p [kPa], cp [J/(kg K)], gamma [−], h [kJ/kg], s [kJ/(kg K)]), `ts` y `grafica` (SVG), `optimizacion` (A/B y dominio motor). Llama a `resolver_ciclo`, `estudiar_cp_variable` y presentadores. Propaga errores de entrada/rango y numéricos. Ejemplo: `preparar_resultados({'T1':288.15,'T3':1600.,'rp':10.,'p1':100.,'eta_c':.85,'eta_t':.9,'delta':.05})['ciclo']['trabajo_neto']` ≈ 402.071.
- `index()`: función de ruta Flask sin argumentos explícitos, porque `request` conserva los datos de la petición actual. Entrega HTML y código 200 (éxito) o 400 (rechazo). Valida primero la acción para no ejecutar funciones antiguas. Llama al lector, al preparador, a `listar_informes` y a `renderizar_dashboard`.
- `renderizar_dashboard(valores, *, contenidos=None, metadata=None, informes=(), errores=None, modo_local=True, informe_actual='', seccion_inicial='simulacion', modo_cp=False, cp_datos=None, campos_cp=()) -> str`: todos los valores se pasan a Jinja. El signo `*` obliga a nombrar los argumentos posteriores: evita confundir `modo_cp` con `seccion_inicial`. En modo cp se muestra el calculador actual; en modo histórico se conserva el HTML de archivos anteriores. El código HTML no resuelve ecuaciones.

Los presentadores reutilizados (`propiedades_estados`, `svg_ts`, `_escala`, `curvas_optimizacion`, `svg_optimizacion`) mantienen firmas y limitaciones del aprendizaje de Fase 2D. El Blueprint `modelo_cp_variable` y el registro `cp_variable_bp` se retiraron; no se creó otro.

## 4. PYTHON — conceptos que conviene comprender

**Una sola fuente de verdad.** El valor de rendimiento viene de `resolver_ciclo`; no se reimplementa la ecuación en Jinja o JavaScript. Si cambiara el motor científico en el futuro, solo el presentador consumiría su nuevo contrato.

**Datos y presentación.** En `return {'ciclo': ciclo, 'estados': ..., 'ts': ...}`, un diccionario reúne distintos tipos de resultado y permite a la plantilla acceder a `cp_datos.ciclo`. Esa notación de Jinja consulta la clave del diccionario; no ejecuta un método físico.

**Condicionales en Jinja.** `{% if modo_cp %}` decide qué contenido renderiza el servidor. El navegador recibe solo una versión del contenido de cada panel. Un informe histórico generado por Python conserva la rama anterior porque `modo_cp=False` es el valor por defecto. No hay selector visible.

**Control de errores.** `except EstadoFueraDeRango` se comprueba antes de `except ValueError` porque es una subclase de este último; de otro modo se perdería el diagnóstico térmico. El error numérico tampoco significa necesariamente que no exista ciclo motor.

**Pruebas con cliente Flask.** `app.test_client()` llama GET/POST sin abrir sockets. Se comparan números de la web con `resolver_ciclo` y `estudiar_cp_variable`, y se comprueba que las antiguas acciones no llaman al preparador. No se confunde la regresión histórica de documentos con ejecutar el modelo viejo.

## 5. INTERPRETACIÓN FÍSICA y ejemplos

En rp=10, T1=288.15 K, T3=1600 K, p1=100 kPa, eta_c=0.85, eta_t=0.90 y delta=0.05:

- Trabajo neto ≈ 402.071 kJ/kg.
- Rendimiento ≈ 34.893 %.
- Máximo A ≈ 414.086 kJ/kg en rp≈15.878.
- Máximo B ≈ 43.745 % en rp≈46.819.

Los dos criterios no coinciden porque incrementar rp puede mejorar la proporción de energía aprovechada mientras crece el trabajo que consume el compresor. Un máximo interior es un punto operativo matemáticamente admisible; una frontera abierta solo puede definir un supremo. Se rechazan estados fuera del dominio 200–2000 K y no se atribuye rendimiento motor a ciclos no motores. Un SVG T–s con líneas discontinuas no reconstruye los procesos reales.

## 6. Ejercicios para aprender

1. Cambia solo rp de 10 a 12. Comprueba el efecto en estados, trabajo y rendimiento sin cambiar T1/T3.
2. Introduce una eficiencia 0 y explica por qué se devuelve 400 sin intentar optimizar.
3. Identifica en `index.html` las tres secciones desactivadas y explica por qué no basta ocultar solo sus botones.
4. Lee `modo_cp=False` en `renderizar_dashboard`: ¿por qué permite consultar un archivo antiguo sin anunciarlo como resultado del modelo cp(T)?
5. Comprueba que el punto B tiene mayor eficiencia pero no necesariamente más trabajo que A.

## 7. Verificación y límites

Pruebas afectadas: 10 de integración cp(T), 7 de HTTP/rutas/historial, 15 de presentación. Los resultados finales de GitHub Actions se comunicarán tras ejecutarse. Las suites históricas cuyos tests suponían POST de nueve parámetros/creación de informes no equivalen al contrato actual: deben adaptarse antes de volver a exigirse como regresiones de la web. El mantenimiento de los algoritmos físicos se acredita con la comparación de hashes Git. No se ha comprobado una turbina real ni inspeccionado todos los navegadores.

## 8. Estado Git

Base: `64b4568a98f36779e305fe80d7c36c9e9498bd1d`. Desarrollo en rama de validación autorizada antes de actualización por fast-forward de `mejoras/cp-variable`. Commit definitivo pendiente de confirmación; no se toca `main` ni el repositorio de conservación.
