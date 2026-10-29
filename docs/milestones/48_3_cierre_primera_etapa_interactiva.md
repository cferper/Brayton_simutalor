# Milestone 48.3 — Cierre de la primera etapa interactiva

## Base y alcance

- Rama: `mejoras/cp-variable`.
- Base publicada: `a6cb03f843a2d3d6718155324ec198e55349d212`.
- Entregas 48.1, 48.2 y 48.3 acumuladas **sin staging, commit ni push**.
- No se han modificado los solucionadores de aire, combustión, turbomáquinas ni toberas.

## Recorrido de datos verificado por inspección de código

1. Los campos `mach` (adimensional) y `T3` (K) mantienen el número exacto y sincronizan el deslizador.
2. `crearControlador48` agrupa eventos durante 350 ms y cancela peticiones anteriores.
3. `new FormData(formulario)` envía los campos activos a `/api/turborreactor/simular`.
4. Flask valida parámetros, llama una vez a `simular_turborreactor` y prepara una sola presentación de ese resultado.
5. Un mismo JSON suministra magnitudes (N, N/(kg/s), kg/s, kg/(N·h), rpm), diagnósticos, SVG y HTML Jinja.
6. El navegador cambia solo el contenido «Uso» de resultados, estaciones y gráficas, además del panel-resumen; conserva nodos de navegación, teoría y estudios independientes.

La API no interpreta los valores inexistentes como cero ni convierte una configuración no resuelta en resultado válido. La modalidad A dimensiona para caudal de aire prescrito; B calcula caudal de tobera de geometría fija; C intenta el equilibrio con mapas monoeje escalados. En C no se vuelven entradas independientes el giro y la relación de compresión.

## Defecto encontrado y corrección

`cancelar()` abortaba la petición automática al enviar el formulario manual pero no invalidaba su identificador. Si el servidor completaba una respuesta pese al aborto, el cliente podía aceptarla. Ahora `cancelar()` incrementa la versión antes de abortar. Pruebas específicas comprueban tanto este supuesto como la invalidación al cambiar otros campos. Se ha corregido también la ayuda de ejemplos para reconocer el cálculo automático cuando hay JavaScript.

La actualización del HTML usa `DOMParser`, prepara los tres conjuntos de nodos y después los sustituye, sin reinstalar eventos de navegación ni tocar los controles. Los SVG provienen del mismo resultado del servidor. No se ejecutan automáticamente las operaciones independientes de sensibilidad y mapas de diseño.

## Pruebas de esta entrega

| Comprobación | Resultado |
| --- | --- |
| Ocho pruebas `node:test` de controles, carrera entre peticiones, fallo y cancelación manual | 8 correctas |
| Regresiones relacionadas `tests.test_acoplamiento_motor_47_4` y `tests.test_caudal_geometria_fija_47_1` | 19 correctas |
| `node --check` en los dos JS, `python -m compileall` de API y prueba 48.1, `git diff --check` | Correctos |
| HTTP 48.1 (`tests/test_navegacion_api_48_1.py`) | Pendiente: Flask/Jinja2 no están instalados en este entorno |
| Navegación, descarga, diseño estrecho y eventos en navegador real | Pendiente de integración en Windows |

Las pruebas de los módulos científicos son **verificación interna**, no validación experimental de un motor. Las pruebas Node ejercitan la lógica, no el DOM ni la conectividad HTTP real.

## Pendientes exactos para Windows

1. Ejecutar las ocho pruebas HTTP de 48.1 y las específicas de JS.
2. Abrir `/`, `/turborreactor` y `/brayton`; comprobar redirección y ambos formularios tradicionales.
3. Para A, B y C: probar Mach y T3 válidos e inválidos, y error de dominio de mapas en C; comprobar punto de diseño C (20 kg/s, 20 000 rpm) y vuelo Mach 0,4 frente al solucionador, no frente a constantes aproximadas.
4. Inspeccionar sustitución conjunta de números, SVG, mensajes, descargas, seis secciones y diseño estrecho; observar arrastres rápidos y envío manual.
5. Ejecutar una sola regresión histórica completa durante la integración final.

No se inicia una etapa de rediseño ni se incorpora física nueva.

## Correcciones posteriores a la revisión en Windows (29-10-2026)

La revisión externa comunicó tres fallos entre 740 pruebas, debidos a rutas
históricas sin actualizar; ese total es **un resultado aportado por el usuario**,
no una ejecución de esta copia. Se sustituyó `/#sección` por
`/brayton#sección` en `test_acciones_no_se_ejecutan_al_navegar`, y los dos
POST de `test_integracion_flask_usa_galeria_y_ampliacion_existentes` ahora
utilizan `/brayton`. No se suprimieron las aserciones.

La página añade `data-simulacion-inicial`: `pendiente` inicia una única
solicitud automática al abrir el GET, tras 350 ms; `resuelta` conserva el
resultado obtenido en el POST manual sin repetir el cálculo; `error` evita
repetir automáticamente una configuración ya rechazada. Al obtener éxito se
quita el banner de error antiguo de **Configuración**. Si cambian entradas
principales se muestra un aviso en sensibilidad o mapas previamente
calculados, sin alterarlos ni recalcularlos. También se detecta el cambio de
modo de ambiente, que usa eventos `change`.

En esta corrección se ejecutaron las ocho pruebas Node (8 correctas),
`node --check` y compilación de sintaxis Python. Las dos pruebas históricas
afectadas no pueden ejecutarse en este entorno porque **Flask y Jinja2 no
están instalados**; queda pendiente repetirlas en Windows. No se repitió la
regresión de 740 pruebas.
