# Aprendizaje 49.1 — Separar una interfaz sin duplicar la física

## Problema y punto de partida

El milestone 48 incorporó la interacción en una página clásica llena de secciones. Queremos tres puertas de entrada, no tres implementaciones de las ecuaciones. Trabajamos sobre la misma copia de 48.1–48.3, en la rama `mejoras/cp-variable`, base `a6cb03f843a2d3d6718155324ec198e55349d212`; los cambios siguen pendientes de publicación.

## PYTHON: dos URL, una función

La función `turborreactor(interfaz="clasico")` recibe una cadena de texto opcional; Flask le pasa `"interactivo"` al visitar `/turborreactor/interactivo`. Recibe entradas de `request.form` en POST, usa `simular_turborreactor(valores)` y `preparar_vista_turborreactor(resultado)` igual que antes, y devuelve HTML más estado HTTP. Este parámetro selecciona la presentación, no un régimen de flujo.

`_render_turborreactor(..., interfaz="clasico")` pasa el indicador a `render_template` para que Jinja escoja título, formulario y menú; mantiene todos sus argumentos científicos y resultados anteriores. `portada()` no recibe entradas y devuelve `redirect(url_for("turborreactor_interactivo"))`. Con `url_for` el enlace depende del nombre de ruta Flask en vez de repetir cadenas literales.

## Jinja: condicionales y reutilización

Una plantilla HTML puede utilizar:

```jinja2
{{ 'Banco de ensayos interactivo' if interfaz=='interactivo' else 'Turborreactor clásico' }}
```

Los dos caminos mantienen los mismos IDs que el JavaScript del 48 utiliza para actualizar datos. En la vista interactiva, CSS deja visible la sección de configuración con el panel vivo; los paneles técnicos restantes siguen en el DOM, pues reciben las respuestas de la API. Al visitar el clásico, esas secciones continúan visibles y utilizables, incluidos los estudios. No copiamos una plantilla gigantesca ni hacemos un nuevo solucionador.

En el ciclo Brayton, el formulario local usa `/brayton` en vez de `/`, que ahora es una redirección. Los informes sin servidor conservan su acción local. El menú usa `aria-current="page"`, una señal accesible que permite identificar la interfaz abierta.

## INGENIERÍA: tres vistas frente a tres modalidades

La elección de página no altera la física: A dimensiona una tobera con caudal prescrito; B obtiene el caudal compatible con áreas fijas; C resuelve un equilibrio monoeje con mapas escalados. El Mach de vuelo es adimensional y T3 es la temperatura total de entrada a turbina en kelvin. Una simulación inicial automática sigue calculándose con Python mediante `POST /api/turborreactor/simular`; JavaScript solo transmite parámetros y representa resultados SVG y magnitudes.

Separar presentación y ecuaciones permite rediseñar el banco en 49.2 sin afectar los balances de energía, continuidad ni potencia, y añadir controles en 49.3 sin cambiar las modalidades físicas.

## Ejercicios y pruebas

1. Abrir `/`: verificar que redirige al banco.
2. Cambiar Mach y T3: comprobar que la API responde sin navegar.
3. Alternar A/B/C y verificar que cada modalidad mantiene sus reglas.
4. Visitar el clásico: comprobar las seis secciones, incluidos sensibilidad y mapas.
5. Volver a `/brayton` y enviar el formulario histórico.

Las pruebas HTTP están escritas en `tests/test_navegacion_49_1.py`, pero Flask/Jinja2 no están disponibles en este entorno y se ejecutarán en Windows. Las ocho pruebas JavaScript heredadas pasaron. Esto es **verificación de software**, no validación experimental.
