# Milestone 49.7 — Esquema interactivo educativo del turborreactor

## Estado anterior

La rama `mejoras/cp-variable`, HEAD de partida verificado
`0ef12ef8b4fa08440d53836c01e729b5be3f6dfe` (roadmap), contiene el
milestone funcional 49.6: modos A/B/C, entradas Mach y T3 con actualización,
geometría de referencia C, gráficas y estudios 49.5. No había selección
didáctica de piezas del motor.

## Qué se ha añadido

- SVG longitudinal esquemático de turborreactor monoeje con seis selecciones:
  entrada/difusor, compresor, cámara, turbina, eje mecánico y tobera.
- Etiquetas accesibles, navegación con Tab, activación con Intro/Espacio,
  foco visible, color y contorno de selección; contexto textual independiente.
- Ficha de nombre y función breve; la pieza elegida permanece resaltada.
- Diseño adaptable dentro del panel de resultados del banco: el control
  preexistente permanece a la izquierda y el esquema/ficha comparten el espacio
  derecho sobre resultados y gráficas. En pantalla pequeña se apilan.
- JS de selección puramente local; sin nueva petición ni cálculo.

## Nuevos conceptos de ingeniería

Orden de componentes en un turborreactor, sentido del flujo,
acoplamiento mecánico monoeje y distinción entre función física y
representación esquemática. La ilustración no indica cotas reales ni
distribuciones espaciales resueltas. Las explicaciones no enseñan magnitudes
calculadas y no pueden quedar desactualizadas por un cambio de punto motor.

## Nuevos conceptos de Python y programación web

No hay nuevas funciones Python ni nuevas ecuaciones. HTML/SVG usa grupos
`<g>` con `role="button"` y `tabindex="0"` y atributos `data-engine-part`;
CSS aplica estilo a la clase `is-selected`; JavaScript crea escuchas de
`click` y `keydown`, actualiza `aria-pressed` y escribe la ficha con
`textContent`. La inicialización se produce desde `inicializar48`, sin pasar
el cliente de API ni el controlador al gestor del esquema.

## Qué hemos aprendido

La interactividad educativa puede mantener su propio estado de presentación
sin duplicar el estado ni el solucionador físico. El cambio de Mach/T3 continúa
requiriendo simulación; seleccionar una pieza solo cambia la explicación.

## Comprobaciones

Los tests focalizados verifican las seis piezas, su accesibilidad, el
comportamiento de selección, ausencia de segunda solicitud física y
conservación de controles, modos, gráficas y navegación. La revisión visual
final del navegador en Windows queda a cargo de la integración del usuario.

Integración Windows (10-11-2026): las 3 pruebas focalizadas 49.7 pasaron;
`node --check` y los 10 tests JavaScript también. La regresión única con
`python -m unittest discover -s tests -p 'test*.py'` ejecutó 782 pruebas:
772 correctas, 10 omitidas y 0 fallidas. En el `.venv` usado no están
instalados SciPy ni Cantera; ocho comprobaciones opcionales requieren SciPy,
una requiere Cantera y una comprueba permisos para enlaces simbólicos en
Windows. El informe del paquete (782/781/1) corresponde a un entorno con esas
nueve opciones disponibles; el total idéntico y los tres métodos Python
nuevos confirman que no cambió el descubrimiento ni se quitaron pruebas.
El test client de Flask y una petición HTTP directa con `curl` entregan 200
para `/turborreactor/interactivo`; el HTML servido contiene el SVG, las seis
partes, modos A/B/C, ficha y botón de geometría C. La revisión visual manual fue realizada y aprobada por el usuario el
10-11-2026; no se automatizó desde esta tarea.

## Limitaciones que siguen existiendo

No hay valores numéricos ni ecuaciones particulares de cada pieza en la ficha;
eso corresponde al futuro 49.8. No hay geometría interna calculada, turbofán,
posquemador, 3D ni cambio en los límites o convergencia de los solucionadores.
La selección no resuelve ni valida físicamente el motor.

## Commit asociado

**Pendiente de registrar el SHA del commit de implementación**, que se crea
con esta publicación. Rama `mejoras/cp-variable`; base `0ef12ef` verificada.
