# Aprendizaje — Milestone 50.8: Estudios y Comparador sin duplicar estado

**Rama:** `mejoras/cp-variable` · **Base verificada:**
`d819e506a68203b597c1e80c962381feb0668321` · **Fecha:** 14/11/2026.

## 1. Problema que resuelve la fase

M49.5/M50.4 ya calculaban barridos y mapas Mach–T3. M50.1 ya comparaba dos
puntos de funcionamiento. El 50.8 **no incorpora un nuevo modelo**: organiza
herramientas grandes en paneles consultables y conecta su uso con la
navegación M50.5, evitando que las vistas borren referencias o provoquen
una petición física accidental.

## 2. INTERPRETACIÓN FÍSICA / INGENIERÍA

En un barrido frente a Mach o T3 se modifica una condición por muestra y se
mantienen las otras entradas. En un mapa se resuelve un conjunto discreto
de pares (Mach, T3). La ausencia de equilibrio C en una celda no implica que
ese punto sea físicamente imposible: puede ser un límite tabulado o un fallo
numérico, como documenta M50.4. La norma residual comprueba balances
internos; **Rline no equivale a margen de surge**. T3 es la temperatura
total a la entrada de turbina [K].

El comparador conserva `Punto 1` como referencia y utiliza el último punto
motor válido como `Punto 2`. Para una magnitud común X:

\[
\Delta X = X_2-X_1,\qquad
\Delta X_{\mathrm{rel}}=100\frac{X_2-X_1}{X_1}\;[\%]
\]

La diferencia relativa **no está definida si X1 = 0**, ni si la magnitud
falta. No se deben comparar como equivalentes diferentes modos con bases de
caudal y restricciones distintas. M50.1 ya hace estas comprobaciones;
M50.8 solo mueve las vistas de resultados.

## 3. Arquitectura y ciclo de vida

- `#turbo-form`: formulario motor único; M48 gestiona recálculo, debounce y
  solicitudes obsoletas.
- `#estudio49` y `#turbo-study49-form`: un explorador único. Cambiar la
  subvista Barridos/Mapa mueve este nodo, sin copiar sus campos ni SVG.
- `.turbo-lab50`: una instancia única. M50.1 mantiene `referencia` y `actual`
  en variables privadas de su clausura JavaScript.
- `controladorNavegacion50_5`: único sistema de navegación principal; M50.8
  no escucha `popstate` ni crea otro historial.

Mover con `appendChild` conserva **identidad del objeto DOM**, eventos y
referencias capturadas en clausuras. Si se clonase el laboratorio, las
consultas de M50.1 podrían apuntar al nodo antiguo y los botones nuevos
no actualizarían la referencia verdadera.

## 4. Función pública y auxiliares

### `iniciarAnalisis50_8(documento, ventana=raiz)`

**Parámetros:** `documento` es un objeto `Document`; `ventana` es `Window`
(opcional, por defecto el contexto global donde se cargó el módulo).
**Unidades:** ninguna: organiza solo interfaz. **Retorno:** `null` si no
es interactivo, falta la navegación o ya estaba inicializado; en otro caso,
`{estudios,comparador,aviso,referencia,estudio}`. `estudios` expone
`seleccionar(clave,opciones)`, `actual()`, `paneles`, `botones`; `comparador`
añade `seleccionarGrafica(tipo)`. Llama a los auxiliares descritos abajo,
y es llamada desde `DOMContentLoaded` después de M50.5–50.7. No lanza
excepciones por entradas físicas ni hace `fetch`; presupone los nodos de
la plantilla M50.7. Ejemplo:

```javascript
const ui = iniciarAnalisis50_8(document, window);
ui?.estudios.seleccionar('clasicos');  // No recalcula el motor.
ui?.comparador.seleccionarGrafica('ts');
```

No hay una función Python de producción nueva en este milestone.

### Funciones locales de presentación

- `crear(tag,clase='',contenido='')`: recibe tres cadenas y devuelve
  `HTMLElement` nuevo con clase y texto, sin HTML inyectado ni magnitudes.
  Se llama para construir botones, paneles y avisos. Usa `textContent`,
  no evalúa texto del usuario.
- `navegacion(id)`: recibe clave `string` de los siete espacios y devuelve
  el `boolean` que obtiene del `controladorNavegacion50_5.navegar(id)`.
  La utilizan los atajos `atajo(destino,texto)`, que construyen un botón
  HTML y lo devuelven; ningún atajo llama a M48 directamente.
- `pestañas(padre,config,clase='turbo-ana58',solicitar=null)`:
  recibe un `HTMLElement` contenedor, una lista de parejas `[clave,nombre]`,
  un nombre CSS y, opcionalmente, un callback que gestiona selección.
  Devuelve `{seleccionar,actual,paneles,botones}` con sendos `Map`.
  `seleccionar(clave,{foco=false}={})` devuelve `true` si la clave existe,
  `false` en otro caso; actualiza `hidden`, `aria-selected`, `tabIndex` y
  foco. Los eventos `click`, flechas y Home/End llaman a ese método o al
  callback suministrado.
- `elegirEstudios(clave,{foco=false,actualizarTipo=true}={})`:
  cambia entre `'barridos'`, `'mapa'` y `'clasicos'`. Si es necesario,
  modifica el selector **existente** `#study49-tipo` y despacha su evento
  `change`, reutilizando el código M49.5. Devuelve `boolean`; si había un
  gráfico, solicita confirmación antes de descartarlo, y `false` si se
  cancela. Cambiar a Clásicos, a otra ventana o regresar sin cambiar tipo
  **no provoca** ese `change`.
- `invalidar(mensaje)`: recibe una cadena y no devuelve valor. Si hay un SVG
  previo, muestra aviso de desactualización y deshabilita aplicar celda.
  Conserva los valores numéricos anteriores: el aviso deja claro que son
  históricos. Los listeners se activan con cambios en rangos o en el
  formulario motor cuando la fuente es «banco».
- `asignar(padre,selector)`: recibe un contenedor y selector CSS, localiza
  **un nodo existente** dentro del laboratorio y lo mueve; no retorna
  magnitudes. La llaman las tres subpestañas del comparador.
- `elegirGrafica(tipo)`: recibe `'ts'`, `'T'`, `'p'` o `'prestaciones'` y
  devuelve `boolean`. Muestra la figura existente y oculta las demás.
  Envía un evento `click` sin petición al contenedor original para que
  la lógica M50.1 de zoom y exportación identifique la gráfica visible.

Los parámetros `foco` y `actualizarTipo` usan la sintaxis de
**desestructuración con valores por defecto**. `Map` guarda asociaciones
clave → nodo, no datos termodinámicos; el operador `?.` permite consultar
módulos opcionales sin romper otras rutas.

## 5. Aplicar un punto C sin doble simulación

1. El explorador M49.5 llama al endpoint de estudio para producir una malla.
2. El usuario selecciona una celda; **no se ejecuta otro cálculo**.
3. M50.4 envía el evento `brayton:aplicar-estudio-50-4` con las entradas
   completas de la celda convergida.
4. El controlador M48 reutiliza `aplicarPunto50_4` y el cargador M50.3;
   llama **una vez** a `controlador.cambiar()`.
5. El puente de clic de M50.5 navega a Simulación. M50.8 no crea un
   segundo mecanismo de aplicación o navegación.
6. M50.1 conserva la copia de la referencia y actualiza o invalida el punto
   actual según el resultado nuevo, sin presentar datos antiguos como válidos.

## 6. ¿Qué es un estudio desactualizado?

Si el usuario cambia los límites de Mach, T3 o el tamaño de malla, la
figura antigua conserva los puntos calculados **antes** del cambio. M50.8
muestra un aviso y bloquea la aplicación de la celda para que esos datos
no parezcan corresponder a la nueva configuración. Si se cambian entradas
físicas del banco, M49.5 conserva su mecanismo de invalidación y M50.8
refuerza el aviso visual. Si la fuente es el diseño C verificado, modificar
el banco no afecta por sí solo a las condiciones fijas de esa malla.

El selector M49.5 descarta resultados al cambiar de tipo/fuente. Para
no hacerlo inadvertidamente, M50.8 instala un listener en fase de captura
que solicita confirmación **antes** del controlador heredado. Si se cancela,
restaura el selector anterior y detiene ese evento; si se confirma, el
estudio previo se sustituye explícitamente. Los `input` y `change` que
provocan un estudio desactualizado **no** son equivalentes a navegar.

Un selector del navegador emite primero `input` y después `change`. Si
el primer evento del selector de fuente se tratara como un cambio de rango,
el botón quedaría deshabilitado aunque el usuario cancelara el segundo
evento. El controlador excluye ambos selectores de ese listener y deja
que la confirmación gobierne el cambio. El aviso por cambios físicos sí
escucha ambos eventos del formulario motor para la fuente «banco».

## 7. Experimentos y pruebas

- Realizar un barrido Mach en la fuente «banco». Cambiar un límite;
  comprobar el aviso y el botón de aplicación deshabilitado. Recalcular.
- Obtener un mapa C. Seleccionar una celda convergida y aplicar. Verificar
  que el modo es C y que se han conservado todas las áreas/condiciones.
- Guardar una referencia C, aplicar un punto nuevo, abrir Comparador.
  Verificar que los dos puntos son distintos y las diferencias están
  definidas solo donde corresponde.
- Elegir otra gráfica comparativa y exportar: se descarga la seleccionada,
  sin volver a consultar el servidor.
- Forzar un fallo HTTP 422 y comprobar que solo se invalida el punto actual.
- Abrir y cerrar Sensibilidad/Mapas clásicos: no recalcula al abrir. Si se
  envía uno de sus formularios HTTP históricos, esa operación sí puede
  recargar la ruta clásica; se conserva el contrato previo.

**Verificación realizada en la entrega:** 8 pruebas Python M50.8, 23 de
M50.5–50.7 (31/31), 70 comprobaciones DOM JS M50.8 y regresiones JS
locales M50.3–50.7. Sintaxis Jinja y Node correcta. La suite completa Python,
Flask, el recorrido 422 y la comprobación visual real requieren el
repositorio íntegro en Windows; no se han ejecutado aquí.

### Integración en Windows · 14-11-2026

Se comprobó el flujo con el motor real en Chrome y Flask. La referencia
fue Mach 0 / T3 1600 K, y la celda aplicada Mach 0,82 / T3 1690 K. El
empuje específico pasó de 958,258 a 778,186 N/(kg/s), un descenso del
18,792 %. El punto nuevo necesitó una sola petición de simulación. Tras
forzar un HTTP 422, desaparecieron las diferencias y se conservó la
referencia. Una celda fuera de dominio tampoco se pudo aplicar.

La regla CSS general del banco ocultaba OFAT y mapas incluso dentro de
un panel abierto. Se añadió una regla específica para esas dos secciones
en Estudios, vinculada a `<details open>`. Ambos formularios produjeron
gráficas. Se verificaron zoom y exportaciones, y seis vistas a cuatro
anchuras, sin desplazamiento horizontal de página. Pasaron 31 pruebas
focalizadas Python y 32 pruebas de Node, con 71 comprobaciones del 50.8.
La regresión Python final ejecutó 853 pruebas, con 843 correctas,
10 omitidas y ningún fallo.

## 8. Alcance, archivos y continuidad

Nuevos: módulo JS y dos suites de prueba; modificados: plantilla, CSS y
`CODE_WALKTHROUGH.md`. Se crean los documentos técnico y educativo M50.8.
No hay cambios físicos, nuevos endpoints, copias del laboratorio, ni
actualizaciones de `main`. Base SHA real del M50.7 indicada arriba; **commit
M50.8 pendiente**. La validación visual y responsive final corresponde al
milestone 50.9, aún no iniciado.

Lecturas: [técnico 50.8](50_8_estudios_comparador.md),
[walkthrough](../../CODE_WALKTHROUGH.md) §4.112,
[explorador M50.4](50_4_explorador_funcionamiento_modo_c.md),
[laboratorio M50.1](50_1_laboratorio_comparativo.md).
