# Aprendizaje 43 — Por qué cada resultado del turborreactor necesita una explicación

**Base:** `a44f6fc74aaa9f71096aa11c827d5796fab88873`, rama
`mejoras/cp-variable`. **Estado:** cambios locales sin commit ni push.

## 1. El problema de diseño

Antes había que saltar entre Resultados y un séptimo apartado de
Fundamentos para relacionar una cifra con su ecuación. Ahora cada uno
de los seis apartados conserva la acción práctica y ofrece una pestaña
para analizar qué significa físicamente. No se ha simplificado el modelo:
se ha cambiado cómo se estudian sus salidas.

## 2. Qué aprender en cada apartado

1. **Configuración.** T∞/p∞ estáticas, Mach, remanso ideal y pérdidas
   prescritas. La presión total puede aumentar por compresión y bajar por
   pérdidas; no confundas presión total con estática. El selector ISA
   describe una atmósfera de referencia, no el tiempo del día.
2. **Resultados.** La cantidad de movimiento del escape y su fuerza de
   presión componen el empuje bruto; restar V∞ da el específico neto Fs.
   El consumo TSFC=3600f/Fs sólo está definido cuando Fs>0 y existe
   salida resuelta. La cifra de Fs aún necesita ṁaire para dar newtons.
3. **Estaciones.** Del estado estático exterior al remanso del difusor;
   después, compresor (trabajo recibido), cámara (calor químico
   equivalente), turbina (trabajo cedido) y tobera (aceleración). La
   salida de tobera vuelve a ser estática.
4. **Gráficas.** Tₜ y pₜ cambian entre cuatro estados discretos: los
   trazos no son perfiles espaciales reales ni muestran geometría.
5. **Sensibilidad.** OFAT cambia una sola entrada. Las curvas describen
   tendencias de la malla elegida; un hueco significa valor indefinido,
   no cero, y una pendiente local no es ley universal.
6. **Mapas.** Dos entradas varían simultáneamente: Fs máximo y TSFC
   mínimo pueden corresponder a configuraciones diferentes. El Pareto
   rp–T3 se interpreta a ambiente fijo; Mach–altitud compara escenarios
   de vuelo distintos. No son mapas experimentales de turbomáquinas.

## 3. Un ejemplo físico

Si un estudiante observa Fs alto pero TSFC también alto, debe preguntar
si f ha aumentado proporcionalmente más que el empuje neto. La pestaña
de resultados ofrece ambas ecuaciones. Si cambia rp en Sensibilidad,
el compresor exigirá otro trabajo, la turbina consumirá diferente salto
de entalpía y la tobera tendrá otro margen de expansión: por eso la
respuesta puede cambiar de signo. No se inventan magnitudes absolutas.

## 4. Qué conceptos Python/Jinja/JS aprendemos

**PYTHON / JINJA:** un archivo de macros no resuelve un motor. En
`templates/turborreactor_teoria_43.html` existen seis macros sin
argumentos, cada una devuelve HTML editorial: `configuracion()`,
`resultados()`, `estaciones()`, `graficas()`, `sensibilidad()`, `mapa()`.
No tienen unidades de retorno porque son presentación, no física; no
validan datos ni producen excepciones físicas. El motor sigue siendo
llamado por la ruta Flask al enviar formularios. La importación
`{% raw %}{% import 'turborreactor_teoria_43.html' as teoria %}{% endraw %}`
permite insertar, por ejemplo, la macro de resultados sin copiar textos.

**JAVASCRIPT:** el controlador ya existente de `DOMContentLoaded`
recorre `data-edu-tabs`, obtiene botones y paneles, y define la función
local `activar(index, enfocar=false)`. `index` es un número entero que
selecciona vista; `enfocar` es un booleano; no retorna datos ni hace
peticiones de red. Sólo cambia los atributos `hidden`, `aria-selected`
y `tabIndex`. Los eventos `click` y `keydown` permiten ratón, flechas,
Home y End. Sin JavaScript ambas vistas siguen en el documento.

**CSS:** reutilizamos `.edu-tabbar`, `.edu-tab`, `.edu-tab-pane` y
`.edu-theory` del dashboard Brayton; no se duplicó un sistema de estilos.

## 5. Pruebas, verificación y límites

Las pruebas de HTML verifican identificadores únicos, relación entre
pestañas y paneles, formulario de simulación único, adaptación tras POST,
conservación de controles OFAT/mapas y choque normal visible. Son
**verificación de software**. La validación del motor frente a medidas
experimentales queda fuera del milestone, igual que geometría real,
rozamiento y mapas de compresor/turbina. La inspección visual real en
móvil y la interacción manual con lector de pantalla no quedan probadas
por un parser HTML.

**Resultado anterior documentado en el archivo recibido:** 609 métodos en suite general (607 correctos,
uno omitido y uno fallido por expectativa de número de plantillas),
seguido de la corrección de esa expectativa y 75/75 pruebas web y
regresión asociada correctas. No se volvió a ejecutar la suite general.

## 6. Práctica propuesta

1. Simula el motor predeterminado; alterna resultados y fundamentos.
2. Contrasta empuje bruto, neto, V∞, f y TSFC.
3. Cambia a C-D, observa Mach en garganta y escape y calcula adaptación.
4. Barre rp mediante OFAT; compara con el mapa rp–T3 y explica por qué
   un extremo de la malla no es un máximo continuo garantizado.

## 7. Revisión local y portabilidad — 26/10/2026

El punto de partida real en Windows fue el commit base indicado arriba,
sin modificaciones versionadas; el código M43 preparado se recibió en un
ZIP de diez archivos. Se preservó ese trabajo y se corrigieron únicamente
los textos, la prueba de plantillas y los ajustes adicionales autorizados.

**Ingeniería.** «C-D» describe la geometría, no reversibilidad global:
regiones continuas ideales/isentrópicas y choques normales irreversibles,
con entropía creciente y presión total decreciente. El modelo puede
resolver salida subsónica o supersónica y mantiene configuraciones sin
solución disponible. `eta_n` no interviene en C-D y `None` no significa
cero ni diagnostica automáticamente un choque sin resolver.

**Python: conjuntos e inclusión (concepto desarrollado en la prueba).**
`necesarias.issubset(disponibles)` pregunta si todos los nombres necesarios
están presentes, sin prohibir otros. Los conjuntos eliminan duplicados y
no imponen orden. `sorted(necesarias - disponibles)` produce una lista
ordenada de nombres ausentes para el mensaje de `assertTrue`. El método
`test_una_sola_plantilla_principal(self)` retorna `None`, no calcula física
ni tiene unidades; lo ejecuta el descubrimiento de `unittest` y sigue
llamando a `assertIn` para verificar la galería del dashboard.

**Python: bytes y texto (precisión nueva para Windows).**
`ver_informe(nombre)` mantiene su firma: `nombre` es `str`, devuelve una
`Response` HTTP y llama a los mismos lectores/presentadores de informes.
Ahora usa `contenido_bytes = ruta.read_bytes()` y
`contenido = contenido_bytes.decode("utf-8")`: el primer objeto preserva
el archivo y el segundo permite validar marcas y presentar HTML. Descargar
retorna los bytes originales; no normaliza CRLF a LF ni escribe el archivo.
Las validaciones de ruta, UTF-8 y marcas siguen devolviendo 404 cuando
corresponde. Véase §4.29 del manual para el contrato completo y ejemplos.
No cambia ninguna ecuación termodinámica.

**Python: subcasos y capacidades del sistema (conceptos reutilizados).**
El método histórico de listado utiliza `with self.subTest(...)` para aislar
la comprobación de enlaces simbólicos. Si `symlink_to` lanza `OSError` con
`winerror == 1314`, `skipTest` omite sólo ese subcaso y continúa con el
listado y sus metadatos. Otros errores vuelven a lanzarse con `raise`.
La omisión declara una cobertura no disponible; no demuestra el rechazo
de enlaces en ese Windows ni modifica sus permisos de seguridad.

**CSS: alcance de una regla.** Activar `js` para las pestañas también activó
la regla de menú móvil de Brayton. Como el turborreactor no tiene ese botón,
se añadió una regla propia a ≤760 px que mantiene `.section-nav` visible.
La especificidad del selector limita el arreglo al turborreactor y no
cambia la navegación del dashboard.

**Verificación actual.** Las 87 pruebas web iniciales fueron correctas
fuera del sandbox. La revisión ampliada de portabilidad pasó 222 pruebas
sin fallos/errores, con un subcaso de enlace omitido, y después pasaron las
15 del dashboard. Las dos regresiones completas intermedias expusieron
primero los fallos CRLF y el privilegio de enlaces, y después una expectativa
textual del dashboard incompatible con la descarga exacta de bytes; se
corrigió comparando con el archivo guardado y comprobando que no se muta.
Se conservan arriba las cifras históricas comunicadas en el ZIP.

<!-- RESULTADO_FINAL_M43 -->

La inspección visual actual sí se realizó en navegador integrado a 1219 y
441 px: seis apartados/dos pestañas, teclado, choque con `epsilon=6`,
adaptación automática, OFAT de tres puntos y mapa 2×2 con conservación al
navegar. Las tres plantillas Jinja y la sintaxis JS se comprobaron. Un
render controlado validó el mensaje para `None` y el diagnóstico específico;
los cuatro informes históricos se descargaron con sus bytes intactos.
Verificación no equivale a validación física experimental.

## Commit asociado

Pendiente de autorización posterior; la base 42.C no incorpora este hito.

## Nota de recuperación — 26/10/2026

La comparación con el ZIP posterior permitió incorporar las correcciones
de accesibilidad móvil, terminología, descarga binaria y portabilidad de
enlaces simbólicos sin rehacer el milestone. En el segundo caso de
enlace simbólico, se registra como omitido **solo el subcaso dependiente**
cuando Windows devuelve el error 1314; una ruta malformada o un informe
incompleto deben seguir rechazándose siempre. La descarga de informes se
compara con la secuencia de bytes previa a la petición, porque la
normalización de saltos de línea al tratar texto no forma parte del
contrato de conservación de informes.

En este cierre no se pudo ejecutar la suite: el entorno anterior había
desaparecido y faltan Flask/Jinja2. Sin instalar dependencias nuevas, se
comprobó únicamente sintaxis Python y diferencias del árbol. Por tanto,
la verificación final completa **sigue pendiente** y no deben confundirse
los resultados históricos con una nueva ejecución satisfactoria.
