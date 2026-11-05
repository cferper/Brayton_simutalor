# Milestone 49.4 — Aprendizaje: explorar las gráficas sin alterar el motor

## 1. Ingeniería: ¿qué representa cada figura?

**T–s.** Cada marcador corresponde a una estación física resuelta. La
temperatura se expresa en kelvin y la entropía específica en kJ/(kg·K).
Los segmentos discontinuos **solo ayudan a leer el orden de estaciones**:
no son curvas de compresión, combustión, expansión ni tobera calculadas punto a
punto. El estado `E`, cuando aparece, es estático; los numerados son de remanso.

**Mach axial.** El eje horizontal es posición desde la garganta en metros,
siempre que exista geometría para asignar posiciones. El Mach es adimensional.
Un choque normal se identifica por dos estados distintos (antes y después) en
la **misma posición**. No es correcto unirlos con una curva suave.

**Presión axial.** La presión trazada es **estática** [kPa]. Un salto en choque
normal indica aumento de presión estática aunque disminuya la presión total.
La línea de referencia representa la presión ambiente.

**Geometría de la tobera.** Se representa el divergente cónico y se mantienen
las mismas escalas horizontal y vertical. El radio es la distancia desde el
eje hasta la pared, y el diámetro es el doble. No aparecen aquí geometrías
supuestas de la parte convergente.

La disponibilidad depende de las magnitudes realmente calculadas en A, B o C.
Cuando no existe un SVG válido, el visor no crea valores artificiales.

## 2. Programación: tres responsabilidades separadas

1. **Python** resuelve los estados y genera SVG. Los módulos de dibujo han
   recibido atributos `data-plot-info` con sus números reales. El modelo físico
   y el sistema de ecuaciones permanecen iguales.
2. **Flask** conserva `POST /api/turborreactor/simular` y devuelve la respuesta
   con SVG y prestaciones. No se añade otro endpoint.
3. **JavaScript** (`iniciarExplorador49`) recibe el SVG ya dibujado y gestiona
   eventos visuales. Un botón de zoom modifica el ancho uniforme del SVG; un
   marcador muestra su descripción; una descarga serializa el dibujo.

El mismo controlador `crearControlador48` sigue agrupando peticiones y
descartando respuestas antiguas. Cuando llegan nuevos resultados, el explorador
restablece las cuatro escalas para asociar una vista limpia a la simulación.

### Funciones JavaScript incorporadas

- `escalaGrafica49(valor, factor)`: recibe y devuelve números sin unidades.
  Redondea a centésimas y limita la escala entre 1 y 4; no transforma
  magnitudes físicas. La llama `ampliar(factor)`. Ejemplo:
  `escalaGrafica49(2, 1.25)` devuelve `2.5`.
- `iniciarExplorador49(documento, panel)`: recibe el `Document` y el elemento
  HTML del banco; devuelve `null` si faltan controles, o el objeto
  `{aplicar, restaurar}`. La llama `inicializar48(documento, fetcher)`. Instala
  manejadores de eventos locales; no solicita cálculos ni llama la API.
- Cierres locales de `iniciarExplorador49`: `claveActiva()` obtiene la clave
  de pestaña; `contenedor(clave)` el elemento de su figura; `grafica()` su SVG;
  `informar(texto)` actualiza el lector accesible; `aplicar()` aplica el zoom
  y disponibilidad de controles; `restaurar()` reinicia escala, scroll y
  mensaje; `ampliar(factor)` actualiza la escala activa mediante
  `escalaGrafica49`; `descargar(nombre, blob)` crea el enlace local de descarga;
  `exportar(tipo)` devuelve una promesa, serializa SVG o rasteriza PNG; y
  `punto(evento)` localiza el marcador consultado. Sus entradas son claves y
  datos DOM (`Event`, texto, `Blob` y factor numérico), no valores físicos.
  `aplicar`, `restaurar` y `ampliar` no devuelven resultados físicos. Las
  validaciones omiten acciones cuando no hay SVG y muestran un mensaje si falla
  el canvas PNG; la opción SVG permanece disponible.
- Ejemplo de conexión: `const visor=iniciarExplorador49(documento,panel);`
  seguido, tras seleccionar una pestaña, de `visor?.aplicar()`. El zoom solo
  cambia el ancho visual; las ecuaciones y sus funciones llamadoras del motor
  siguen en Python.

## 3. Modificar la interfaz en el futuro

- Añade un marcador **solo** si tienes un dato numérico trazable a un estado o
  punto calculado. Evita leer píxeles para inventar su magnitud.
- Si creas otra pestaña, añade `data-plot-tab`, `data-plot-panel` y
  `data-live-plot`, y entrega un SVG real desde el backend.
- Mantén la representación axial separada en dos series ante un choque y
  diferencia siempre magnitudes estáticas y de remanso.
- Para una exportación CSV futura, ofrece un esquema explícito con puntos
  calculados y unidades desde Python; no interpretes los trazos del SVG.
- Verifica siempre por separado la **corrección del programa** (pruebas de
  sincronización y dibujo) y la **validación científica** del modelo (datos
  experimentales independientes, fuera del alcance de este milestone).

## 4. Actividad guiada

Abre el banco, cambia Mach, observa cómo se regeneran los SVG y consulta
los estados disponibles. Amplía sin cambiar Mach ni T3 y comprueba que el
estado de la simulación sigue siendo el mismo. Exporta SVG y verifica sus
rótulos. Si hay choque, compara la presión antes y después **sin interpolar**.

## Integración y comprobaciones en Windows (2026-10-31)

El ZIP se incorporó desde la base `ca8d0554935607bf7cc68e051aec9b617c9ef40e`
en `mejoras/cp-variable`. La regresión completa pasó 757 pruebas con 10
omisiones. Las cinco pruebas nuevas de 49.4, las cinco pruebas del banco 49.3
y los ocho tests JavaScript pasaron. La primera ejecución de la prueba nueva
detectó que buscaba Node con `which`, comando Unix; se cambió únicamente esa
detección a `shutil.which`, que conserva la prueba y funciona en Windows.

El cliente de pruebas Flask confirmó las tres vistas (200; la portada redirige
al banco) y la API respondió en A, B y C. Para el mismo caso de 20 kg/s, el empuje continuó en
19 165,15366881058 N; C mantuvo 20 000 rpm. Coincide con la base 49.3. La
inspección visual y las descargas desde navegador no se pudieron completar en
esta sesión; por ello siguen pendientes la comprobación manual de zoom,
consulta de puntos, exportación PNG/SVG y presentación visual.
