# Aprendizaje del milestone 49.3 — Interfaz del banco de ensayos

## Qué problema resolvemos

El motor termodinámico funciona, pero su uso educativo se dificulta cuando
el alumno debe buscar la modalidad en un desplegable, desplazarse para ver
T–s y distinguir muchas tarjetas vacías. Reorganizar la información no cambia
el resultado científico.

## PYTHON / HTML — Una entrada física, tres botones visibles

El formulario clásico tiene un campo `modo_caudal` con tres valores:
`impuesto`, `fijo` y `acoplado`. En el banco los botones tienen el atributo
`data-bank-mode` con esos mismos valores. Una pulsación hace:

```javascript
selectorModo.value=b.dataset.bankMode;
selectorModo.dispatchEvent(new Event('change',{bubbles:true}));
```

`dataset` lee un atributo HTML `data-*`; `dispatchEvent` notifica el cambio
a los demás controladores. Así el código anterior de `turborreactor.js`
continúa habilitando/deshabilitando campos incompatibles. `aria-pressed`
indica cuál de los tres botones está seleccionado para lectores de pantalla.
No se crean dos estados de modalidad independientes.

## CSS — Mostrar campos relacionados

El valor del selector se refleja también en `formulario.dataset.bankMode`.
Los selectores CSS específicos muestran la entrada de caudal en A y la
configuración de geometría de tobera en B/C, conservando `mach`, `T3` y
sus deslizadores. «Configuración avanzada» alterna una clase en el formulario
para exponer campos originales del ambiente, núcleo y componentes. La
maquetación es específica de `data-interfaz="interactivo"`; el clásico
mantiene su diseño y sus formularios.

Un campo oculto no significa físicamente igual a cero. Cuando el modo lo
prohíbe, la lógica anterior lo deshabilita, y `FormData` no lo envía.
Cuando está permitido, conserva el valor real introducido, también si está
vacío y el backend lo admite. La última palabra sobre validez la tiene Python.

## JavaScript — Pestañas sin más simulaciones

`activarGrafica(clave)` cambia `aria-selected` y la propiedad `hidden`
de las figuras. No llama al servidor. `dibujar(clave,svg)` actualiza el SVG
de esa pestaña tras una respuesta de Python. El visor comienza con `ts`;
si una figura no existe para el punto, se oculta la pestaña y se selecciona
otra disponible. Esto permite añadir pestañas en fases posteriores sin
repetir ecuaciones termodinámicas en JavaScript.

## Estados del cálculo y disponibilidad

La interacción conserva `crearControlador48`: un cambio muestra «Actualizando»,
espera 350 ms y envía `FormData` mediante `fetch`. El identificador secuencial
y `AbortController` impiden que una respuesta antigua sustituya otra más
reciente. La API devuelve magnitudes y SVG coherentes, o un error 422 con
motivo cuando no existe solución.

No son equivalentes estas situaciones:

1. **Calculado:** se muestra el valor con unidades, incluido el cero cuando
   sea realmente resultado del solucionador.
2. **Faltan entradas:** en A, sin caudal de aire conocido, el empuje absoluto
   [N] no se puede obtener aunque el específico sí esté definido.
3. **No aplicable:** fuera de C no se determina el régimen de giro mediante
   mapas; se oculta esa tarjeta y se explica en resultados adicionales.
4. **Error físico:** el motor no ha convergido o los parámetros incumplen el
   dominio. Se limpian los resultados antiguos y se muestra el diagnóstico.

## INGENIERÍA — Interpretación de modalidades

- A: prescribe gasto másico de aire y dimensiona tobera.
- B: prescribe geometría fija y calcula caudal compatible con el estado.
- C: resuelve el punto estacionario acoplando mapas y balances monoeje.

El diagrama T–s representa estados calculados con el modelo educativo cp(T).
Mach es adimensional, T3 [K] es temperatura total anterior a turbina. Ni un
gráfico visible ni una prueba informática validan los resultados frente a un
motor experimental real.

## Prácticas de comprobación

Alternar A/B/C, elegir un campo avanzado, variar Mach/T3 rápidamente y
comprobar que solo aparece el último resultado. Cambiar de gráfica no debe
crear una solicitud de red. Comparar el panel con el clásico, revisar errores
422 y repetir en pantalla estrecha. Las pruebas HTTP y la inspección visual
se documentan únicamente si se realizan de verdad.

## Iteración de integración en Windows (2026-10-31)

La integración ejecutó la regresión completa una vez: 752 pruebas, con una
fallida y 10 omitidas. La comprobación histórica del milestone 43 esperaba
12 pestañas en total; el visor nuevo añade cuatro pestañas con nombres
accesibles (`ts`, `mach`, `presion` y `geometria`). Se conservó el recuento
de las 12 pestañas educativas y todas las demás aserciones, y se añadió una
comprobación explícita de las cuatro del visor. La ejecución selectiva de
`test_turborreactor_web_43.py` pasó sus 5 pruebas. No se repitió la regresión.

**Estado:** base GitHub `b1d8f0e` verificada, cambios 49.3 sin commit.
