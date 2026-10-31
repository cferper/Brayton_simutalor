# Milestone 49.2 — Rediseño del banco interactivo

## Estado anterior

El 49.1 separó las rutas `/turborreactor/interactivo`, `/turborreactor`
y `/brayton`, pero la primera compartía visualmente la configuración extensa
del simulador clásico. La API y los deslizadores de Mach/T3 ya funcionaban.

## Cambios

- Dos columnas de escritorio: controles visibles a la izquierda y resultados
  en directo con tres gráficos SVG a la derecha.
- Controles compactos para modalidad A/B/C, Mach [–] y T3 [K]. Se indica
  que T3 es temperatura total de entrada a turbina después de combustión.
- El formulario original sigue conteniendo los demás parámetros para que
  la API reciba exactamente el mismo estado y las reglas físicas originales.
  Esos campos se ocultan **solo en el banco con JavaScript activo**;
  siguen editables en `/turborreactor`.
- La columna de controles puede permanecer visible mediante `position:sticky`;
  a anchuras ≤900 px se apilan las columnas sin posición fija.
- Botón «Simular» intacto y enlace de restablecimiento a la ruta interactiva,
  donde se carga el estado predeterminado y se calcula automáticamente.
- Tarjetas con valores disponibles/indisponibles y SVG procedentes de la
  respuesta coherente de `/api/turborreactor/simular`.
- Una tarjeta adicional muestra la velocidad de salida [m/s] ya calculada
  por Python (`tobera.velocidad_salida`); la API solo expone ese valor.

## Arquitectura y conservación

La plantilla `templates/turborreactor.html` sigue siendo compartida entre
ambas vistas. No se duplican formularios ni controladores ni se modifican
el controlador de `static/turborreactor_interactivo.js`, ni los solucionadores
físicos. Solo se amplía una clave de la respuesta API y su presentación JS.
Los selectores CSS están limitados a `data-interfaz="interactivo"` y al
modo JavaScript; no alteran el clásico ni Brayton. Sensibilidad y mapas
siguen siendo operaciones independientes disponibles en el clásico.

## Verificación y límites

Se requieren los tests JS existentes del 48.2, las comprobaciones estáticas
`tests/test_diseno_banco_49_2.py`, sintaxis y revisión de formato. Las
pruebas HTTP de Flask y la inspección visual responsive se realizarán en
Windows cuando esté disponible el entorno. Los valores ocultos conservan
los predeterminados previamente definidos; el 49.3 podrá exponer más
parámetros, pero no se ha implementado en esta entrega.

## Commit asociado

Pendiente. Rama `mejoras/cp-variable`; la copia de trabajo conserva
modificaciones sin staging ni publicación.
