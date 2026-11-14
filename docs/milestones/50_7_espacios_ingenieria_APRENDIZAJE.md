# Milestone 50.7 — Aprendizaje: reutilización de vistas de ingeniería

**Fecha de implementación documental:** 13 de noviembre de 2026. **Rama:** `mejoras/cp-variable`. **Base remota comprobada:** `4cbd77769e4e8d0f2888685c3ba4ab31aef8e141` (M50.6). **Estado de publicación del 50.7:** pendiente, sin commit.

## 1. Qué teníamos y qué problema resolvemos

En M50.5 se crearon siete espacios. El controlador colocaba Motor, diagnóstico HPC, estudios y comparador en cada espacio y trasladaba el único visor gráfico completo `#turbo-live` entre Simulación y las vistas de Termodinámica y Tobera. M50.6 reorganizó los campos, las tarjetas y la galería de Simulación. Las herramientas de ingeniería todavía acumulaban contenidos y no contaban con navegación interna coherente.

M50.7 **no añade ningún modelo de motor**. Añade una capa de presentación para localizar una herramienta de cada familia y visualizarla sin recorrer todas las gráficas en vertical.

## 2. Reparto sin duplicados

| Espacio | Vista principal | Otras vistas | Fuente original |
|---|---|---|---|
| Motor | SVG de difusor, compresor, cámara, turbina, eje y tobera, con ficha | Estaciones y propiedades | M49.7/M49.8, M50.0 y `#estaciones` |
| Termodinámica | T–s, T/p total, trabajos, balance (una seleccionada) | Informe y teoría | M48 `data-plot-tab` y `#graficas` |
| Tobera | Mach, presión estática, temperatura, velocidad y geometría | Funcionamiento y enlace a su ficha | M48 `data-plot-tab`; tarjetas originales de régimen y velocidad |
| Turbomáquinas | Diagnóstico corregido y mapa HPC | Indicadores existentes de turbina/eje y límites | M50.2 y M49.9 |

La ficha de cada componente sigue siendo única en Motor; la caracterización numérica M49.9 cambia de ubicación a Turbomáquinas. Un valor no calculable permanece ausente. Los gráficos no se reconstruyen para cada apartado.

## 3. ¿Por qué mover un elemento DOM y no copiarlo?

**JavaScript.** `appendChild` elimina el nodo de su padre anterior y lo inserta en el nuevo, conservando objetos, eventos, datos de formularios y controladores asociados. En cambio, clonar elementos con `cloneNode` generaría IDs duplicados, controladores que seguirían actualizando el original y posibles indicadores contradictorios.

```javascript
const destino = ventana.destinoVisor50_7?.(espacio) || paneles[espacio];
destino.appendChild(live);
```

Este fragmento permanece en `static/navegacion_superior_50_5.js`: **solo el módulo de navegación principal mueve `#turbo-live`**. El módulo M50.7 proporciona las ubicaciones y selecciona la vista adecuada mediante acciones de M48.

**Ingeniería.** La misma respuesta del solucionador alimenta todos los espacios. Cambiar la vista no representa un nuevo punto de operación, por lo que no se justifica recalcular el equilibrio del motor.

## 4. Funciones y flujo JavaScript

### `iniciarEspaciosIngenieria50_7(documento, ventana=raiz)`

- **Entradas:** `documento`, objeto `Document`; `ventana`, objeto `Window` opcional (por defecto el objeto raíz usado al cargar el script). No recibe magnitudes termodinámicas ni tolerancias.
- **Retorno:** `null` si se usa una ruta distinta de la interactiva, si faltan los paneles necesarios o si ya está inicializado; en caso contrario, objeto `{vistas, hosts, seleccionar}`. `vistas` contiene cuatro controladores internos, `hosts` dos destinos de visualización y `seleccionar(id,v)` cambia una subvista devolviendo `boolean`.
- **Unidades:** no aplica; maneja únicamente identificadores y referencias DOM.
- **Validación/errores:** comprueba `dataset.interfaz`, marca `turbo-50-7-ready` y exige `#turbo-live`, los cuatro espacios y los botones del visor anterior. No captura errores de programación ajenos.
- **Llamadores:** se llama desde `DOMContentLoaded` después de M50.5/M50.6; también se exporta para tests Node.
- **Funciones que usa:** auxiliares locales `crear`, `preparar` y `crearHost`; controladores previos de M48 mediante clic en sus botones, `ventana.controladorNavegacion50_5` y `destinoVisor50_7`.
- **Ejemplo:** `const c = iniciarEspaciosIngenieria50_7(document, window); c.seleccionar('motor','estaciones')` muestra las estaciones si los elementos existen.

### Auxiliares internas

- `crear(tag,clase,texto)`: recibe tres cadenas, crea y devuelve un `HTMLElement` sin resultados físicos; no consulta otros elementos. Se usa desde la inicialización para títulos, navegación, contenedores, ayuda y enlaces.
- `preparar(id,opciones)`: recibe el nombre de un espacio `string` y pares `[clave, título]`; construye los botones y devuelve un controlador `{seleccionar, actual, contenido, panel, botones, contenedores}`. El consumidor es la función principal.
- `seleccionar(clave,{foco=false}={})`: función interna del controlador; recibe clave `string` y configuración de foco opcional, devuelve `boolean`. Conmuta `hidden`/`aria-pressed`. En Termodinámica/Tobera delega en botones M48 originales; no calcula ni solicita datos. Devuelve `false` para claves inexistentes.
- `contenido(clave,elemento)`: registra una referencia original `HTMLElement` como contenido de la subvista; no devuelve resultados ni aplica transformaciones físicas.
- `crearHost(id)`: recibe el identificador de Termodinámica o Tobera, crea un contenedor del visor y devuelve un `HTMLElement`; **no mueve** `#turbo-live`.
- `ventana.activarEspacioIngenieria50_7(espacio)` restaura la subvista elegida cuando M50.5 activa un espacio. `ventana.destinoVisor50_7(espacio)` entrega el host o `null`, sin mover el visor.

**Conceptos:** `Map` asocia claves con elementos; `dataset.ing57Vista` guarda selección **de interfaz**, no resultados; `?.` evita errores si un controlador previo no existe; `hidden` retira contenido inactivo de la navegación por teclado; `aria-pressed` permite saber qué acción está activa. Las flechas/Home/End cambian selección y foco dentro de cada barra secundaria.

## 5. Ciclo de vida y coherencia con los controladores anteriores

1. El navegador carga los scripts con `defer`. M48 registra sus listeners originales de los diagramas y del esquema; M50.5 prepara los siete espacios; M50.6 organiza el formulario.
2. M50.7 crea cuatro barras secundarias y desplaza **una sola vez** los elementos no gráficos a sus destinos finales.
3. Cuando se pulsa «Tobera», M50.5 mueve el único visor al host indicado por M50.7; M50.7 selecciona, por ejemplo, Mach mediante el botón antiguo `data-plot-tab="mach"`.
4. Al cambiar a «Geometría», se muestra el gráfico **que ya había calculado** el servidor. Cambian estilos y visibilidad, pero no los parámetros ni el estado físico.
5. Si cambian Mach/T3 en Simulación, el controlador M48 actualiza o invalida los datos. Las demás vistas muestran ese mismo último resultado o el mensaje pendiente/error.
6. Al regresar a una pestaña, se restaura su selección local. El historial principal sigue usando fragmentos `#espacio-*`.

Las vistas «Estaciones» y «Informe» reutilizan el HTML histórico dentro de su nuevo contenedor, sin dejar restos activos dentro de envoltorios `<details>` vacíos. Estudios y Comparador no se reorganizan en esta tarea.

## 6. Física que debe acompañar a la interfaz

- La temperatura T3 introducida es **temperatura total de entrada de turbina**; en bibliografía de aerorreactores puede llamarse Tt4. Las estaciones no son posiciones axiales continuas.
- Un diagrama T–s de estados discretos no demuestra que se haya integrado el proceso dentro de cada componente.
- Mach/presión/perfiles de tobera muestran únicamente los puntos y regímenes que implementa el modelo existente; no se inventan ondas de choque adicionales.
- El modo C resuelve el giro con equilibrio monoeje y mapas escalados; A/B no tienen rpm determinadas por esos mismos datos. Las mediciones corregidas emplean los estados totales y las referencias del mapa, **no caudales estáticos equivalentes**.
- Rline es coordenada de mapa; no es una distancia a una línea experimental de surge. No hay mapa HPT gráfico ni validación experimental.

## 7. Prácticas para aprender

1. Abre Simulación, guarda un punto en el comparador y navega a Turbomáquinas. Comprueba que los valores son los del mismo caso y que la referencia sigue disponible.
2. En Motor, selecciona «Eje», consulta sus resultados y abre «Estaciones». Regresa sin modificar parámetros: el esquema y la ficha deben conservar el componente activo.
3. En Termodinámica alterna T–s, T/p total y balance; comprueba que el contador de peticiones HTTP no aumenta.
4. En Tobera alterna Mach y presión; cambia a Geometría en modo A/B/C y verifica que el gráfico indique «no disponible» si el modelo no puede calcularlo.
5. En modo A o B, consulta Turbomáquinas: las rpm y el punto HPC acoplado no deben aparecer como si fueran resultados C.

## 8. Pruebas y límites de esta entrega

La suite focalizada nueva contiene **9 tests Python** de contratos HTML/CSS/Jinja y **48 comprobaciones JavaScript** con DOM simulado, todos correctos. Las pruebas disponibles del M50.5/M50.6 sumaron 14 Python y 54 comprobaciones JS adicionales; las pruebas M50.3/M50.4 (4+5 casos JS) también pasaron. Este segundo confirma identidad de nodos, subpestañas, foco, historial, selección de M48 y ausencia de reconstrucción de la referencia. **No es una prueba visual real de navegador ni verifica las ecuaciones del solucionador.** Los números finales de tests se registran también en el documento técnico y la respuesta de entrega.

La regresión completa del repositorio y los ensayos integrados con Flask requieren el código y las dependencias completas. La inspección visual Windows deberá cubrir cuatro resoluciones, zoom/exportación, mapas HPC en C, los placeholders en A/B y el tránsito con parámetros cambiados y errores HTTP 422. El milestone 50.8 continuará con Estudios y Comparador; el 50.9 resolverá el cierre responsive/accesibilidad.

### Integración en Windows · 13-11-2026

El grupo SVG de la tobera recibe un evento `click` para activar el listener original del esquema. Las reglas de visibilidad distinguen las secciones de estaciones e informe activas de las ocultas. Un observador de `data-estado` vuelve a seleccionar la subvista técnica después de la actualización de M48. Por ejemplo, la selección «Geometría» se conserva aunque el nuevo punto no disponga de esa figura.

Pasaron 23 pruebas Python focalizadas, 31 pruebas de Node y la regresión general (835 correctas, 10 omitidas, 0 fallos). Después de los ajustes pasaron las 9 pruebas Python y las 49 comprobaciones JavaScript del 50.7. Chrome y Flask verificaron transiciones sin recálculo, los SVG que corresponden a cada geometría, el mapa HPC en C, la recuperación tras HTTP 422 y la referencia del comparador. Las mediciones a 1920, 1366, 768 y 390 px no detectaron desbordamiento de página. La inspección visual personal queda pendiente.

## 9. Archivos, compatibilidad y Git

Archivos de interfaz: `static/espacios_ingenieria_50_7.js` nuevo, `static/navegacion_superior_50_5.js`, `static/turborreactor.css` y `templates/turborreactor.html` actualizados. Se agregan `tests/test_espacios_ingenieria_50_7.py`, `tests/js/test_espacios_ingenieria_50_7.cjs`, documentos técnico y educativo, y se actualiza `CODE_WALKTHROUGH.md`.

El cambio **no** modifica el modelo físico, la API, la ruta clásica ni `/brayton`. No hay commit ni push del 50.7. El commit inicial publicado del 50.6 permanece como referencia histórica, **no** como commit del nuevo milestone.
