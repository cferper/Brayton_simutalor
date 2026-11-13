# Milestone 50.6 — Panel de Simulación compacto

## Estado anterior

- Rama `mejoras/cp-variable`; base publicada **`dd31bad020427d58c26ac0d1683ece5bbb05f3c5`**, identificada directamente en GitHub el **12-11-2026** (M50.5).
- M50.5 ya separa siete espacios mediante navegación horizontal. En Simulación, el formulario M48 todavía ocupaba una columna larga y con scroll interno, mientras la galería de `#turbo-live` estaba oculta. Mach/T3 se encontraban en grupos de parámetros originales; el visor conservaba ocho indicadores calculados.
- El ZIP de trabajo usa archivos completos del paquete de entrega 50.5 contrastados mediante *git blob SHA* con el HEAD 50.5 para HTML, CSS y navegación. El repositorio Windows puede tener cambios locales no consultables desde aquí. No se cambió GitHub.

## Qué se ha añadido

1. `static/panel_simulacion_50_6.js`: adaptación progresiva del DOM de **Simulación**. Coloca los mismos elementos `#mach`, `#T3` y sus deslizadores en una zona principal y traslada el campo de caudal A y el bloque de tobera/geometría a un área asociada al modo activo. No crea inputs, no altera `name`, `id`, valores ni listeners. Mantiene el selector C, sus seis ejemplos y el restablecimiento del diseño. La ayuda y los tres casos tradicionales se conservan en un `<details>`.
2. `static/turborreactor.css`: distribución en dos columnas equilibradas (A: formulario, B: resultados/galería) en escritorio; una columna para ≤1100 px. El scroll del formulario es natural y no está anidado. Los parámetros ambientales y el resto de componentes quedan cerrados hasta pulsar el **botón avanzado existente**, con sus valores retenidos. El CSS del modo respeta `hidden` y los controles deshabilitados por el código histórico.
3. Se hace visible en Simulación la **galería única ya existente** en `#turbo-live`, con selección por grupos y pestañas, consulta, zoom y descarga SVG/PNG administrados por M48. Una figura SVG sigue siendo la activa; no se duplican datos ni peticiones. El título y las tarjetas son compactos. Los estados pendientes impiden leer como actuales las cifras de una solución previa.
4. `templates/turborreactor.html`: agrega únicamente la carga condicional del nuevo JS, **después** de M50.5 y solo para la ruta interactiva. La ruta clásica mantiene el mismo HTML funcional al no inicializarse el módulo 50.6.

## Arquitectura y compatibilidad

El nuevo módulo se inicializa en `DOMContentLoaded`, después de `turborreactor_interactivo.js` y `navegacion_superior_50_5.js`. Los controladores 50.3, 50.4, 50.1 y 50.2 continúan gestionando estado, selección y cálculo como antes. M50.6 no modifica esos archivos. La navegación M50.5 puede **seguir moviendo `#turbo-live` entero** a Termodinámica o Tobera y devolverlo a su contenedor original: el 50.6 nunca lo cambia de padre. La galería solo se muestra en Simulación mediante estilos condicionados a `data-active-workspace="simulacion"`.

| Zona | Elementos reutilizados | Disponibilidad |
|---|---|---|
| A. Controles | `#turbo-form`, `data-bank-mode`, Mach/T3, `#turbo-c-example`, `#turbo-bank-advanced-fields`, campos caudal/áreas | Entradas originales A/B/C; geometría depende del modo y del tipo de tobera |
| B. Resultados | `#turbo-live-status`, ocho `data-live-card`, aviso de disponibilidad | Valores de `datos.magnitudes` según el solucionador; datos ausentes no se rellenan |
| C. Visualización | `.turbo-live-plot-viewer`, `data-plot-tab`, `data-live-plot`, herramientas `data-plot-action` | La figura activa procede de M48, sin cálculos por seleccionar pestaña |

**Sin cambio de física:** no se modificaron modelos, balances, mapas HPC/HPT, ecuaciones, tolerancias, endpoints ni estructura de la respuesta HTTP. En A el empuje absoluto puede no estar disponible si no hay caudal; solo C resuelve rpm. La UI conserva la diferencia entre punto resuelto, sin datos y cálculo fallido.

## Pruebas y verificación

- `tests/test_panel_simulacion_50_6.py`: siete pruebas de plantilla, identificadores, controles A/B/C, coexistencia M50.5, herramientas de gráfica y CSS responsive; Jinja analizado con `Environment.parse`.
- `tests/js/test_panel_simulacion_50_6.cjs`: DOM artificial con comprobación de conservación de los nodos y valores, del único formulario y visor, de listeners, referencia del comparador simulada y ausencia de llamadas al cálculo durante la redistribución.
- **Integración en Windows, 12-11-2026.** 7/7 pruebas Python de M50.6 y 7/7 de M50.5. Node registró 30 pruebas correctas, incluidas las 25 comprobaciones internas de M50.6, las 29 de M50.5, las 5 pruebas de M50.4 y las 4 de M50.3. Sintaxis Jinja y JavaScript correcta. La regresión Python del repositorio completo ejecutó 836 pruebas, con 826 correctas, 10 omitidas y 0 fallos.
- **Flask y Chrome automatizado.** A, B y los casos C `diseno` y `vuelo04` devolvieron HTTP 200. En A/B se ocultó la tarjeta de rpm y en C se mostraron valores calculados. Una T3 de 100 K produjo HTTP 422, retiró la gráfica anterior y permitió recuperar el diseño C. Se verificaron la sincronización de Mach/T3, la configuración avanzada, la navegación sin recálculo, la referencia del comparador, la consulta de puntos, el zoom y la generación de SVG y PNG.
- **Ajuste CSS.** Se incluyó el espacio activo en el selector del formulario para que prevalezca sobre la regla de scroll interno anterior. Tras el ajuste volvieron a pasar las 14 pruebas Python focalizadas y la comprobación con Chrome. A 1920 y 1366 px el panel presentó dos columnas, y a 768 y 390 px una. Las cuatro anchuras se midieron con el avanzado abierto y cerrado, con el formulario sin scroll interno y la página sin desbordamiento horizontal.

## Limitaciones y continuidad

La reorganización se aplica al banco interactivo y al espacio Simulación. La comprobación con Chrome midió la distribución e interactuó con los controles sin inspección visual. Queda pendiente la revisión personal del aspecto y la legibilidad. El recorrido automatizado incluyó dos de los seis ejemplos C.

## Commit asociado

**Pendiente**: el paquete M50.6 no crea commits ni modifica `main` o `mejoras/cp-variable` en GitHub. La base M50.5 está publicada en `dd31bad020427d58c26ac0d1683ece5bbb05f3c5`.
