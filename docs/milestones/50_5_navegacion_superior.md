# Milestone 50.5 — Navegación horizontal y espacios de trabajo

## Estado anterior

Base: rama `mejoras/cp-variable`, commit publicado `c5884067eb034507fb7e5c1460173039bdb969ab` (M50.4), comprobado en GitHub el 12-11-2026. El banco utilizaba seis secciones HTML y una selección adicional entre punto motor y estudio M49.5. Las herramientas actualizadas por JavaScript coexistían en la configuración, provocando mucho desplazamiento vertical. Los modelos A/B/C, el explorador M50.4 y el laboratorio M50.1 ya existían.

## Qué se ha añadido

- Encabezado `BRAYTON SIMULATOR` con exactamente siete enlaces de navegación: **Simulación, Motor, Termodinámica, Tobera, Turbomáquinas, Estudios y Comparador**. La barra es horizontal, `sticky` y desplazable lateralmente en móvil; el encabezado incluye una franja de contexto para modalidad, Mach, T3 y estado.
- Módulo `static/navegacion_superior_50_5.js`: crea siete regiones en el mismo `<main>`, oculta las inactivas y utiliza `history.pushState`, `popstate`, `hashchange`, `aria-current` y teclas de navegación. Enlaces directos `#espacio-motor`, `#espacio-estudios`, etc.
- Contenidos **existentes**, movidos con `appendChild` sin duplicarlos: formulario/indicadores en Simulación; esquema y caracterización en Motor; visor SVG compartido en Termodinámica/Tobera; diagnóstico M50.2 en Turbomáquinas; explorador M50.4 y formularios de estudios históricos en Estudios; laboratorio M50.1 en Comparador.
- El elemento `#turbo-live` completo se desplaza entre Simulación, Termodinámica y Tobera según la vista. Así `turborreactor_interactivo.js` conserva sus consultas internas `panel.querySelector(...)` y los gráficos, y no se reconstruye ningún controlador. El selector de grupo cambia `ciclo`/`tobera` como acción exclusivamente visual.
- Los apartados históricos de resultados, estaciones, otras gráficas, sensibilidad y mapas se mantienen dentro de `<details>` provisionales, inicialmente plegados para reducir el desplazamiento vertical. Su redistribución definitiva queda para M50.6–M50.8.
- Se interceptan en fase de captura los botones históricos `data-study49-view`, evitando que dos sistemas cambien simultáneamente la visibilidad. El explorador mantiene su propia lógica de malla, exportación y aplicación de puntos.

## Integración y estado

Se preservan `#turbo-form`, `#turbo-live`, `#estudio49`, los módulos 49.5–50.4 y las API. La navegación no cambia los parámetros, no hace `fetch` ni ejecuta una simulación. El controlador M48 continúa siendo el único propietario del cálculo. La franja lee **directamente** el mismo formulario; un `MutationObserver` sigue `data-estado` de `#turbo-live` para Pendiente/Calculando/Resuelto/Error. No se guarda otra solución en el navegador. Cambiar de sección no elimina la referencia privada de M50.1.

**Mejora progresiva:** la cabecera nueva está oculta por defecto. Solo se activa tras inicialización de su módulo; si falta JavaScript, permanecen el HTML y el formulario originales. `static/turborreactor.js` mantiene la navegación histórica para la ruta clásica `/turborreactor`; en la interactiva, el nuevo controlador restaura los atributos `hidden` que su listener histórico pudiera alterar tras atrás/adelante.

## Ingeniería y nuevas técnicas de programación

No existe física nueva. Que el estado sea «Resuelto» significa únicamente que el solucionador aceptó el cálculo del modelo didáctico. El mapa HPC no representa un compresor certificado y los modos A/B no aportan régimen mecánico calculado.

Se emplean movimientos de nodos DOM (`appendChild`), delegación de eventos en captura, observación de mutaciones, historial de URL, acceso por teclado con foco visible, estilos CSS acotados a `data-interfaz="interactivo"` y diseño responsive con overflow horizontal.

## Pruebas efectuadas

En el paquete incremental, antes de integrarlo en Windows:

- `tests/test_navegacion_superior_50_5.py`: **7 pruebas correctas** (sintaxis Jinja, siete nombres, un único formulario, compatibilidad de identificadores, aislamiento, estado, CSS).
- `tests/js/test_navegacion_superior_50_5.cjs`: **29 comprobaciones correctas** (navegación, visibilidad única, mover y devolver visor, conservar referencia/entradas, estados, historial, puente M50.4 y teclado) con DOM simulado.
- `node --check`: sintaxis correcta del módulo nuevo; no hay comprobación termodinámica ejecutada.

En la integración de Windows del 12-11-2026 se reprodujeron las 7 pruebas Python focalizadas y las 29 comprobaciones JavaScript con DOM simulado. También pasaron las 9 pruebas JavaScript de M50.3/M50.4 y las comprobaciones de sintaxis Jinja y JavaScript. La regresión Python terminó con 829 pruebas (819 correctas, 10 omitidas y 0 fallidas). El servidor local en 5002 respondió HTTP 200 en el banco interactivo, en el recurso JavaScript y en las rutas clásica y Brayton. Los siete enlaces se sirven únicamente en el banco interactivo.

## Limitaciones y pendientes

El usuario revisó y aprobó visualmente la nueva distribución. Las pruebas automatizadas de navegación y persistencia de la referencia M50.1 se realizaron con DOM simulado. Los ajustes estéticos se reservan para después del milestone 50.9.

## Commit asociado

SHA de este milestone pendiente de registrar. Base publicada: `c5884067eb034507fb7e5c1460173039bdb969ab`.
