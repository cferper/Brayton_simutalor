# Aprendizaje del milestone 50.5 — Navegación superior

**Fecha:** 12 de noviembre de 2026. **Rama:** `mejoras/cp-variable`. **Base verificada:** `c5884067eb034507fb7e5c1460173039bdb969ab` (M50.4). **Publicación del 50.5:** pendiente, sin commit/push.

## 1. Problema y solución elegida

El banco interactivo reunía formulario, panel didáctico, diagnóstico y laboratorio bajo «Configuración», además de secciones de resultados y estudios con un selector independiente. No faltaban modelos físicos: faltaba **una jerarquía visual que conservase una única simulación**. En el 50.5 se establece la navegación por siete espacios y no se reescriben las herramientas.

La vista activa cambia sin recargar la página. Una aplicación termodinámica no debe recalcular un motor solo porque el usuario pase de ver el compresor a consultar la tobera: no han cambiado ni el estado ambiente, ni el caudal, ni la geometría, ni la temperatura de entrada a turbina. El control del cálculo sigue perteneciendo al módulo M48.

## 2. ¿Por qué mover nodos en vez de copiarlos?

En el navegador, cada elemento HTML es un **nodo DOM**. Al ejecutar `destino.appendChild(nodo)`, el mismo nodo cambia de padre. No se genera otra copia del formulario, ni se crea otro gráfico, ni se pierden los controladores asociados al nodo:

```javascript
paneles.termodinamica.appendChild(live);  // un solo #turbo-live
```

El controlador `turborreactor_interactivo.js` continúa buscando las gráficas dentro de `#turbo-live` mediante `panel.querySelector(...)`. Por eso se mueve el panel **completo** entre Simulación, Termodinámica y Tobera, no sus gráficos por separado. Al volver a Simulación, se devuelve al padre original.

También se conservan por identidad los nodos del esquema del motor, la caracterización, el diagnóstico y el laboratorio. Mover el nodo del laboratorio no borra su variable privada `referencia` (M50.1).

## 3. Contrato de las funciones nuevas

El módulo nuevo es `static/navegacion_superior_50_5.js`. No se han añadido funciones Python ni cálculos de propiedades físicas.

### `fragmento50_5(hash)`

- **Parámetro:** `hash` (`string`), por ejemplo `'#espacio-tobera'`.
- **Resultado:** identificador `string` válido, como `'tobera'`; si no coincide, `'simulacion'`.
- **Papel:** interpretar el fragmento de URL sin consultar el servidor. No tiene unidades, errores físicos ni efectos secundarios.
- **Consumidores:** `iniciarNavegacion50_5` y `volverPorHistoria`.

### `estadoFranja50_5(modo, mach, T3, estado, estadoInicial='pendiente')`

- **Parámetros:** modalidad `string` (`impuesto|fijo|acoplado`), Mach adimensional y T3 [K] (`string|number` procedentes del formulario), estado del controlador `string` y estado inicial opcional `string`.
- **Resultado:** objeto `{modo,mach,T3,estado,clase}` con etiquetas para el encabezado. «A/B/C» y «Pendiente/Calculando/Resuelto/Error» son textos de presentación; las entradas ausentes se muestran como `—`, no como 0.
- **Llamadas:** `actualizarContexto()` invoca esta función. No invoca propiedades termodinámicas ni calcula empuje.
- **Ejemplo:** `estadoFranja50_5('acoplado','0.4','1600','actualizado').estado` produce `'Resuelto'`.

### `iniciarNavegacion50_5(documento, ventana)`

- **Parámetros:** `Document` y `Window`; ejecución al evento `DOMContentLoaded` de la ruta interactiva.
- **Resultado:** `null` si faltan los siete enlaces, formulario o panel; de otro modo objeto `{activar,navegar,actualizarContexto,activo}`.
- **Función:** crea siete regiones visuales, mueve los nodos preexistentes, instala los controladores de navegación, histórico y franja de contexto. **No ejecuta `fetch` ni llama al solucionador.**
- **Errores/validación:** comprueba el modo interactivo y la existencia de nodos esenciales; `activar` y `navegar` devuelven `false` si el identificador no pertenece a los siete espacios.
- **Llamadas:** `activar(espacio,{foco=false})` selecciona un único panel y, en Termodinámica/Tobera, cambia visualmente el grupo de gráficos existente; `navegar(espacio,{foco=true})` además modifica `history` sin recargar. El callback `volverPorHistoria()` recupera la vista tras `popstate` o `hashchange`.
- **Ejemplo:** `const nav = iniciarNavegacion50_5(document,window); nav.navegar('motor')` presenta el mismo esquema SVG sin recalcular el punto.

**Conceptos clave:** `const` declara una referencia; `dataset` lee atributos `data-*`; el operador `?.` evita fallos cuando falta un control opcional; `aria-current="page"` indica al lector de pantalla el espacio elegido. La navegación con flechas cambia el **foco** entre enlaces; Intro activa el enlace. Las secciones no activas reciben `hidden`, de modo que desaparecen del flujo visual y accesible.

## 4. Observación de estado sin una segunda simulación

```javascript
const observador = new ventana.MutationObserver(actualizarContexto);
observador.observe(live,{attributes:true,attributeFilter:['data-estado']});
```

`#turbo-live` ya recibe `data-estado` del controlador M48 cuando se modifican entradas, se calcula, se recibe una respuesta o falla el punto. El observador se limita a releer esos atributos. Mach, T3 y modalidad se leen del **mismo** formulario `#turbo-form`; no hay una configuración paralela. «Resuelto» indica convergencia aceptada del software, **no** validación experimental ni estabilidad garantizada.

## 5. Compatibilidad y prevención de dobles mecanismos

M49.5 tiene botones antiguos `data-study49-view` que directamente ocultaban o mostraban `#estudio49` y `#configuracion`. Si se mantuvieran ambos mecanismos se producirían paneles contradictorios. Un listener en captura identifica esos botones antes de que se ejecute su listener histórico; llama al nuevo `navegar('estudios'|'simulacion')` y detiene el clic original. Las acciones de M50.4 que usan `.click()` sobre esos botones siguen funcionando, pero el movimiento entre espacios lo gestiona un único responsable.

El módulo histórico `turborreactor.js` mantiene su papel sobre el formulario y la ruta clásica. Como también escucha atrás/adelante, `activar` restablece `hidden=false` en las secciones históricas trasladadas antes de ocultar las seis regiones inactivas mediante el controlador nuevo.

## 6. Experimentos, pruebas y límites

- **Prueba de estado:** A/B/C debe mostrar la modalidad correspondiente; Mach o T3 vacío debe mostrar `—`, no cero.
- **Prueba de navegación:** tras guardar una referencia en M50.1, navegar a Estudios, usar una celda C válida y regresar no debe borrar aquella referencia. El cálculo solo ocurre cuando se aplican **entradas nuevas** al motor.
- **Prueba de historia:** abrir `#espacio-turbomaquinas` y usar atrás/adelante debe cambiar la región visible sin modificar el formulario.

### Integración en Windows · 12-11-2026

Pasaron 7 pruebas Python focalizadas, 29 comprobaciones JavaScript sobre DOM simulado y 9 pruebas JavaScript de M50.3/M50.4. La sintaxis Jinja y JavaScript fue correcta. La regresión Python ejecutó 829 pruebas, con 819 correctas, 10 omitidas y 0 fallidas. Flask respondió HTTP 200 y sirvió los siete enlaces y el módulo nuevo en la ruta interactiva. Las rutas clásica y Brayton respondieron HTTP 200 con su navegación habitual.

El DOM simulado comprueba que la navegación conserva la referencia al mover el nodo del comparador. El usuario aprobó visualmente la nueva distribución. El recorrido completo del comparador con un punto C real y un cambio de Mach o T3 sigue disponible como ejercicio de comprobación en el navegador.

## 7. Qué se conserva y qué queda para después

No cambian `web_app.py`, las API, el núcleo termodinámico, los mapas HPC/HPT, Newton, tolerancias, casos M50.3, estudio M50.4 o laboratorio M50.1. Los resultados históricos, tablas de estaciones, gráficos clásicos, OFAT y mapas permanecen en paneles plegables provisionales; los próximos milestones reorganizarán su disposición y definirán mejor el tratamiento responsive.
