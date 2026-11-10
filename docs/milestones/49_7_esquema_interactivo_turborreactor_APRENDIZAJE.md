# Aprendizaje del milestone 49.7 — Esquema educativo del turborreactor

## Punto de partida y objetivo (10-11-2026)

Partimos del HEAD remoto `0ef12ef8b4fa08440d53836c01e729b5be3f6dfe`
en `mejoras/cp-variable`, con milestone funcional 49.6. Ya existían los
controles Mach y T3, modos A/B/C, actualización diferida de resultados,
geometría C y todas las gráficas y estudios paramétricos.

La dificultad consistía en añadir una representación visual seleccionable
sin confundir **seleccionar una parte para aprender** con **modificar las
condiciones del motor para volver a calcular**.

## Implementación: HTML, SVG, CSS y JavaScript

1. En `templates/turborreactor.html`, la plantilla inserta la sección
   `.turbo-engine-educational` solo para `interfaz == 'interactivo'`.
   Consta de un `<svg viewBox="0 0 660 280">` y una ficha lateral.
   Los grupos del SVG identifican cada componente mediante `data-engine-part`.
2. En `static/turborreactor.css`, un **CSS Grid** organiza esquema y ficha;
   mediante media queries se apilan si no hay anchura suficiente. Se destaca
   tanto la selección como el foco, con especial atención al teclado.
3. En `static/turborreactor_interactivo.js`, `iniciarEsquemaEducativo49_7(documento)`
   conecta los eventos visuales una sola vez en la inicialización del banco.
   Devuelve `{seleccionar}` o `null` cuando no existe el esquema.

### Función nueva: `iniciarEsquemaEducativo49_7(documento)`

- **Parámetro:** `documento`, instancia del DOM `Document` con los métodos
  `querySelector` y `querySelectorAll` sobre la sección, o doble de pruebas.
- **Retorno:** `{seleccionar: Function}` cuando existe el panel; `null` si
  la plantilla no lo incluye (caso clásico). No hay unidades físicas.
- **Función interna:** `seleccionar(clave)` recibe `clave: string`, devuelve
  `boolean`: `true` para una clave válida y `false` para otra desconocida.
  Sus entradas permitidas son `difusor`, `compresor`, `camara`, `turbina`,
  `eje`, `tobera`.
- **Validación y errores:** claves desconocidas no modifican la selección;
  no se consultan datos numéricos ni se lanzan errores físicos. La función
  presupone los dos elementos textuales presentes cuando existe la sección,
  coherente con la plantilla actual.
- **Llamadas:** `inicializar48(documento, fetcher)` la invoca al iniciar el
  banco; la función interna `seleccionar` se llama tras clic, Intro o Espacio.
  No llama a ninguna función del backend, API o simulador.
- **Ejemplo:** tras cargar la vista, pulsar Tab hasta compresor y después
  Intro equivale a `seleccionar('compresor')`: su grupo adquiere la clase
  `is-selected` y la ficha explica la compresión.

### Conceptos básicos de programación

- **`const fichas = { ... }`:** objeto JavaScript que relaciona cada clave
  con una pareja `[título, explicación]`, sin consultar al servidor.
- **`dataset.enginePart`:** lee `data-engine-part` desde un elemento SVG.
- **`addEventListener`:** escucha `click` o `keydown` sin alterar el
  procesamiento del formulario.
- **`classList.toggle('is-selected', activa)`:** añade o retira una clase
  según un booleano; `aria-pressed` refleja también el estado para apoyos
  de accesibilidad.
- **`textContent`:** actualiza únicamente texto y evita interpretar la
  explicación como HTML ejecutable.

## Diferencia física: esquema frente a motor resuelto

Entrada/difusor, compresor, cámara, turbina, eje y tobera reflejan las
funciones de un turborreactor monoeje, **no** longitudes, diámetros ni
campos internos deducidos del ciclo. El modelo trata la combustión como
aporte energético equivalente. La imagen no pretende representar la
distribución real de temperatura, presión o Mach dentro del compresor.

Cuando se mueve Mach o T3, el controlador anterior realiza el recálculo;
si espera resultados o existe error, las tarjetas de prestaciones conservan
sus diagnósticos. Las fichas 49.7 siempre son descriptivas, por lo que
ninguna muestra valores anteriores como si fueran los actuales.

## Ejercicios de observación

1. Selecciona compresor, turbina y eje: identifica qué componente requiere
   trabajo y cuál lo proporciona.
2. Con la ficha de turbina abierta, modifica T3: la explicación seguirá
   siendo correcta y las magnitudes del cálculo cambiarán según el backend.
3. Cambia a modo C y utiliza «Restablecer geometría de diseño»: esa
   acción sí modifica parámetros y solicita simulación, a diferencia del clic
   en un componente del SVG.

## Pruebas, límites y estado

Los archivos `tests/test_esquema_educativo_49_7.py` y
`tests/js/test_esquema_educativo_49_7.cjs` prueban la presencia HTML,
selección, teclado y separación respecto a la API. Las pruebas demuestran
coherencia del software, **no validación experimental**. No se implementan
fichas numéricas, nuevos indicadores ni capacidades del 49.8–50.2.

En la integración Windows del 10-11-2026 pasaron las 3 pruebas focalizadas
49.7, `node --check` y los 10 tests JavaScript. La única regresión Python,
`python -m unittest discover -s tests -p 'test*.py'`, ejecutó 782 pruebas:
772 correctas, 10 omitidas y 0 fallidas. El entorno `.venv` no tiene SciPy ni
Cantera: ocho pruebas condicionales de SciPy y una de Cantera se omiten; también
se omite la comprobación de enlaces simbólicos porque Windows no concede ese
privilegio. El resultado 782/781/1 incluido en el ZIP refleja un entorno donde
esas nueve pruebas opcionales sí se ejecutaron. No hay cambio en el método de
descubrimiento: el total coincide y se añaden exactamente tres pruebas Python.

El test client de Flask y una petición directa con `curl` respondieron HTTP 200
en `/turborreactor/interactivo`. El HTML incluye el SVG con seis componentes,
la ficha, los modos A/B/C y el restablecimiento C. La aplicación queda activa
en `http://127.0.0.1:5002`. La revisión visual manual fue realizada y aprobada por el usuario el
10-11-2026. El informe registra verificación de software, no validación
experimental.
