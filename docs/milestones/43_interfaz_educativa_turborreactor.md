# Milestone 43 — Interfaz educativa del turborreactor

**Estado:** implementado en el árbol de trabajo; commit y push pendientes de revisión.
**Rama:** `mejoras/cp-variable`.
**Base verificada:** `a44f6fc74aaa9f71096aa11c827d5796fab88873` (42.C).

## Objetivo y punto de partida

El turborreactor tenía siete apartados, incluida una sección general de
fundamentos, y dos botones que ejecutaban el mismo cálculo de simulación.
La información física se encontraba lejos de sus resultados. Se adopta el
patrón del dashboard Brayton: dos vistas en cada uno de los seis apartados
funcionales, una para operar y otra para comprender la física.

## Organización final

| Apartado | Resultados / uso | Fundamentos teóricos y procesos |
| --- | --- | --- |
| Configuración | Ambiente directo/ISA, Mach, parámetros y único botón Simular | Remanso/estático, función de componentes, relaciones de presión y eficiencias |
| Resultados | Fs bruto/neto, TSFC, f, velocidades, diagnósticos y adaptación C-D | Momento + presión − entrada, dosado energético, interpretación y límites de tobera |
| Estaciones | Tabla T/p/h de estados reales y tipo estático/total | Recorrido ambiente→difusor→compresor→cámara→turbina→tobera |
| Visualizaciones | Esquema de eje y SVG de Tₜ y pₜ con unidades | Lectura de estaciones discretas y transferencia de energía |
| Sensibilidad | Formulario OFAT, curvas, tabla y validez | Parámetro variable, constantes, tendencias locales y límites |
| Mapas | Formulario bidimensional, mapas, extremos y Pareto | Dos variables, regiones, compromisos y no equivalencia a mapas experimentales |

La calculadora C-D sigue mostrándose automáticamente en resultados tras
«Simular turborreactor», cuando existe estado calculado apropiado. Se
eliminó sólo el botón «Calcular geometría adaptada»; la ruta Flask todavía
admite la antigua acción `adaptacion` por compatibilidad. No se recalcula
ninguna propiedad física al cambiar pestaña.

## Archivos y decisiones técnicas

- `templates/turborreactor.html`: seis secciones, dos paneles por sección,
  12 pestañas con identificadores únicos y referencias accesibles; salida
  de la antigua sección general «Fundamentos».
- `templates/turborreactor_teoria_43.html`: seis macros editoriales Jinja,
  sin cálculos ni acceso al resultado de simulación.
- `static/turborreactor.js`: conmutación por clic/teclado, roles/atributos
  ARIA, foco y `hidden`; la navegación lateral sigue usando hashes.
- `tests/test_turborreactor_web_43.py`: pruebas GET/POST, unicidad de IDs,
  referencias de pestañas, botón, adaptación y estudios.
- `CODE_WALKTHROUGH.md`: funcionamiento y justificación física/educativa.
- Este documento y `43_interfaz_educativa_turborreactor_APRENDIZAJE.md`.

El contenido de la sección anterior de teoría se distribuye y amplía
contextualmente: empuje y consumo en Resultados, procesos en Estaciones,
condiciones de entrada en Configuración, lectura de gráficas en
Visualizaciones y metodología paramétrica en Sensibilidad/Mapas.

## Accesibilidad y degradación progresiva

Con JavaScript, cada grupo presenta una sola vista; botones `role=tab`,
`aria-selected`, `aria-controls`, `tabIndex` y las teclas izquierda,
derecha, Inicio y Fin permiten operar con teclado. Cada panel se asocia
con su pestaña por `aria-labelledby`. Sin JavaScript, ambas vistas están
en el HTML en orden natural y los tres formularios POST siguen utilizables.
El CSS responsive existente del dashboard controla el ancho de botones
y tarjetas, y los SVG conservan scroll horizontal interno.

## Verificación

Se comprueban renderización sin resultado, simulación con tobera C-D,
choque resuelto, adaptación implícita, estructuras HTML y estudios OFAT y
mapa. Los tests verifican implementación, no comportamiento en vuelo ni
validación experimental. Un repaso visual real a distintos anchos y la
interacción manual por teclado siguen siendo recomendables antes de
publicar una versión final.

**Resultados anteriores comunicados con el archivo recibido (no ejecutados en esta revisión):** la regresión completa ejecutó **609 pruebas**
(**607 correctas, 1 fallo, 1 omitida**). El único fallo correspondió a
una expectativa antigua que enumeraba exactamente dos plantillas HTML;
se actualizó para admitir el fragmento de macros educativas del hito 43.
Después se ejecutaron **75 pruebas relevantes**, incluida la comprobación
corregida y la regresión web del turborreactor: **75/75 correctas**.
La suite completa no se repitió después de ajustar esa expectativa.
`node --check` validó la sintaxis JS; una inspección HTML confirmó seis
secciones, 12 pestañas, tres formularios sin anidar y destinos de pestaña
existentes. No se pudo realizar inspección visual en un navegador real.

## Revisión final local — 26/10/2026

La revisión de Windows partió de `a44f6fc74aaa9f71096aa11c827d5796fab88873`,
en `mejoras/cp-variable`, sin cambios versionados. Los diez archivos del
milestone 43 estaban en el ZIP entregado y se incorporaron sin rehacer su
implementación. Los cambios siguen sin commit ni push.

- Se corrigieron los dos textos obsoletos de choques y la denominación
  C-D en cabecera, selector, ayuda de `eta_n` y fundamentos. Las zonas
  continuas son isentrópicas; los choques normales son irreversibles,
  generan entropía y reducen presión total. No se cambió ningún algoritmo.
- La prestación no disponible se presenta como tal, conservando el
  diagnóstico particular; `None` no se convierte en cero.
- `test_una_sola_plantilla_principal(self)` comprueba inclusión de las tres
  plantillas requeridas mediante conjuntos e `issubset`, conservando la
  comprobación de la galería Brayton y admitiendo otras plantillas legítimas.
- Se detectó y corrigió, con autorización, la ocultación del menú móvil
  causada por activar la clase global `js`: una regla específica del
  turborreactor mantiene sus enlaces visibles a ≤760 px.
- También se autorizaron dos correcciones de portabilidad detectadas en
  la regresión: `ver_informe(nombre)` lee bytes, los decodifica una vez
  para validar/presentar y descarga los bytes originales, conservando CRLF.
  El test del dashboard compara con los bytes del archivo y comprueba que
  no se muta. La prueba histórica de listado sólo omite el subcaso de
  enlace simbólico si Windows devuelve error 1314; las comprobaciones de
  metadatos/listado restantes continúan. No se cambian permisos del sistema.

**Comprobaciones actuales, distintas de las anteriores del ZIP.**
Las pruebas web iniciales fueron 87/87 correctas fuera del aislamiento;
una pasada anterior tuvo un error de limpieza de temporales del sandbox.
Tras las correcciones de portabilidad se ejecutaron 222 pruebas sin fallos
ni errores y un subcaso omitido por el privilegio de enlaces simbólicos.
Las 15 pruebas del dashboard también pasaron tras ajustar su expectativa.
La primera regresión general local dio 609 ejecutadas, 596 correctas,
3 fallos de CRLF, 1 error de enlace simbólico y 9 omisiones opcionales.
La segunda dio 609, 598 correctas, 1 fallo de expectativa del dashboard,
0 errores y 10 omisiones. Se repitió la general por esas causas concretas.

### Verificación de recuperación y cierre — 26/10/2026

**Estado: pendiente de cierre técnico.** Se recuperaron y compararon los
15 archivos del ZIP de estado más reciente con el árbol de trabajo en
`mejoras/cp-variable`, HEAD
`a44f6fc74aaa9f71096aa11c827d5796fab88873`. Cuatro coincidían en
contenido y once incorporaban cambios posteriores compatibles; se
recuperaron sin cambiar `main`, sin commit ni push.

**Correcciones finales de Windows:**

- `test_rutas_malformadas_symlink_e_informe_incompleto`: el segundo
  enlace simbólico se intenta explícitamente. Solo cuando Windows
  devuelve `winerror=1314` se omiten los subcasos dependientes de ese
  enlace; los casos de rutas malformadas, documento no autorizado e
  informe incompleto se siguen comprobando.
- `test_recuperacion_cuatro_informes_descarga_identica_sin_recalculo`:
  se compara la respuesta de descarga con los bytes leídos **antes**
  de solicitarla y se verifica que el archivo sigue intacto. Se retira
  la comparación textual sensible a CRLF; permanecen los controles de
  metadatos y las protecciones contra recálculo.

**Entorno actual:** Linux, Python del runtime de Codex; Flask/Jinja2 no
están disponibles y el entorno virtual utilizado en la revisión anterior
ya no existe. La instrucción de no instalar dependencias impidió ejecutar
las pruebas web y la regresión completa en esta sesión.

**Comandos intentados:**

```bash
MPLCONFIGDIR=/tmp/brayton42c_mpl /tmp/brayton_42c_venv/bin/python \
  -m unittest legacy_tests.test_verificacion_integracion_web tests.test_dashboard -q
```

El intérprete indicado no existe en esta sesión (`No such file or directory`).
El Python disponible tampoco permite importar `flask`. No se obtuvieron
resultados de pruebas unitarias ejecutadas en este cierre: totales 0,
correctas 0, fallos 0, errores 0 y omisiones 0 **por falta de ejecución**,
no por una regresión aprobada. Las cifras anteriores de 609 pruebas,
incluidas las omisiones opcionales y la incidencia de Windows 1314,
pertenecen a la revisión previa registrada arriba; no se presentan como
resultado final de este cierre. Su justificación requiere verificación
en un entorno con las dependencias ya configuradas.

**Comprobaciones disponibles:** compilación sintáctica Python de los
archivos afectados y revisión de diferencias. La compilación Jinja y el
HTTP 200 no se pueden volver a verificar sin Flask/Jinja2. El resultado
final de regresión y el criterio de cero fallos y cero errores quedan
pendientes; **no se declara cerrado el milestone 43**.

Se comprobaron `node --check static/turborreactor.js`, el parseo y compilación
de las tres plantillas Jinja y HTTP 200. Un render controlado con prestación
`None` verificó el mensaje general y la conservación del diagnóstico
específico. Las descargas de los cuatro informes reales coincidieron byte
a byte con los archivos guardados, sin regenerarlos.

**Inspección visual realizada:** navegador integrado real, escritorio
(1219 px) y vista estrecha (441 px), en una instancia temporal de revisión
del puerto 5003. Se revisaron los seis apartados y sus dos pestañas,
Home/End/flechas, botón único, choque normal interno resuelto con
`epsilon=6`, adaptación automática y conservación de controles/resultados
OFAT (3 puntos) y mapa rp–T3 (2×2) al alternar pestañas y navegar. No hubo
errores de consola ni desbordamiento horizontal global. Se guardaron
capturas fuera del repositorio. Esto verifica presentación e implementación;
no es validación experimental del motor.

## Limitaciones

No cambian ecuaciones, tolerancias ni propiedades `cp(T)`. No se añade
caudal másico, geometría dimensional, empuje absoluto ni mapas reales
de componentes. El modelo sigue siendo educativo, de composición
equivalente y con pérdidas prescritas.

## Trabajo pendiente

Revisión visual final por el usuario, decisión de publicación y, en
milestone posterior autorizado, dimensionamiento absoluto si procede.

## Commit asociado

Pendiente; no se ha creado commit de este milestone.
