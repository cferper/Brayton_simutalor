# Aprendizaje — Milestone 49.2: banco de ensayos en dos zonas

## 1. Antes y después

La simulación automática de 48 y las tres rutas de 49.1 ya estaban
implementadas. El problema era de **presentación**: controlar Mach en un
formulario largo y localizar abajo las prestaciones obligaba a desplazarse.
Ahora, la vista interactiva muestra controles a la izquierda y tarjetas y
gráficas a la derecha. El motor científico no ha cambiado.

## 2. HTML y Jinja: una sola fuente de entradas

En `templates/turborreactor.html` el formulario `#turbo-form` contiene
una única entrada numérica `#mach`, una `#T3`, sus deslizadores y el selector
`#modo_caudal`. Jinja comprueba `interfaz=='interactivo'` para añadir
descripciones y clases. Las demás entradas no se eliminan del formulario:
permanecen disponibles para el motor aunque esta vista todavía no permita
editarlas. Esto evita dos estados distintos del mismo motor.

`url_for('turborreactor_interactivo')` genera el destino del enlace
«Restablecer valores». Al abrir de nuevo la ruta mediante GET, Flask entrega
los parámetros de partida y JavaScript inicia el cálculo; no hace falta
inventar una segunda lista de valores por defecto en el navegador.

## 3. CSS Grid y diseño adaptable

`#turbo-configuracion-vista-uso` usa `display:grid` con dos columnas
`minmax(...)`. `minmax(0,...)` permite que los SVG y valores largos no
fuercen un ancho mayor que el contenedor. Las reglas solo se aplican a
`.js .turbo-page[data-interfaz="interactivo"]`:

- `.js` indica que el navegador ejecuta JavaScript.
- `data-interfaz` distingue la vista interactiva de la clásica.
- `position:sticky` mantiene los controles visibles dentro de su espacio
  durante el desplazamiento; `max-height` y `overflow-y:auto` permiten
  recorrerlos en ventanas bajas.
- `@media(max-width:900px)` cambia a una columna y desactiva el sticky.

La operación de ocultar mediante `display:none` es visual: el campo sigue
existiendo dentro del formulario. Los campos avanzados se editan en la
interfaz clásica hasta que una fase posterior diseñe sus propios controles.

## 4. JavaScript y Flask: física única

`inicializar48(documento, fetcher)` en
`static/turborreactor_interactivo.js` reutiliza la misma cadena:

1. Un evento `input` actualiza al instante el número junto al deslizador.
2. El controlador espera 350 ms desde el último cambio.
3. `fetch` envía un `FormData` a `POST /api/turborreactor/simular`.
4. Python obtiene las prestaciones mediante los solucionadores anteriores.
5. La respuesta incluye magnitudes y SVG del mismo caso; JavaScript los
   inserta en `#turbo-live` y en las regiones históricas sin recálculo.

Como ejemplo de ampliación sin nueva física, `web_app.py` añade al JSON
`magnitudes.velocidad_salida_m_s`, leyendo el resultado existente
`tobera['velocidad_salida']` [m/s]. La plantilla crea su tarjeta y
`onRespuesta` la actualiza con la misma ejecución que genera los SVG.

El controlador conserva su identificador de versión y `AbortController`:
una respuesta antigua no puede sobrescribir otra más reciente. La maquetación
no crea nuevos eventos ni otra API. «Simular» continúa disponible como POST
manual tradicional.

## 5. Interpretación de ingeniería

- **A:** se prescribe el gasto másico de aire y se dimensiona la tobera.
- **B:** se prescriben áreas de la tobera y se obtiene el caudal compatible.
- **C:** mapas educativos de compresor y turbina y equilibrio del eje
  determinan un punto de funcionamiento, cuando existe solución.

Mach es adimensional (velocidad / velocidad local del sonido). T3, en kelvin,
es la **temperatura total de entrada a turbina** tras la cámara de combustión;
no es la temperatura de salida de turbina. Las tarjetas de empuje o consumo
no reciben ceros ficticios cuando un dato es inaplicable. Los tres gráficos
son SVG generados por Python; no representan un motor experimental validado.

## 6. Prácticas, pruebas y límites

Para inspección en Windows: abrir el banco, cambiar A/B/C, mover Mach y T3,
comprobar indicadores, errores y SVG, redimensionar la ventana a menos de
900 px y volver al clásico y Brayton. Las pruebas estáticas revisan que
no se duplicaron controles ni fuentes de respuesta. Las ocho pruebas JS de
48.2 verifican sincronización, debounce y protección contra respuestas
tardías. La comprobación HTTP necesita Flask/Jinja2, ausentes en este entorno.

**Estado Git:** rama `mejoras/cp-variable`, trabajo no preparado para commit.
Milestone 49.2 pendiente de integración y revisión en Windows.
