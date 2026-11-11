# Milestone 50.0 — Aprendizaje: estados, procesos y resaltado visual

## 1. Qué relaciona el nuevo comportamiento

Una pieza del esquema es un **componente físico**. Un punto de una gráfica es un **estado termodinámico** en una frontera de ese componente. Una barra es un **intercambio de energía o trabajo**. No son lo mismo: por ejemplo, el eje puede transmitir trabajo sin tener ni temperatura ni presión de fluido propias.

## 2. Tipos de magnitudes

- **De remanso o totales:** `pt2` tras el difusor; `pt3` tras el compresor; `pt4` tras la cámara; `pt5` tras la turbina. Son las cuatro estaciones internas T1, T2, T3 y T4, respectivamente, sin renombrarlas.
- **Estáticas:** ambiente, garganta y salida de la tobera. La garganta aparece separada solo cuando el modelo proporciona ese estado. Una tobera convergente no tiene por qué aportar un estado adicional de garganta distinto de la salida.

Una conexión gráfica **no** permite deducir dónde se sitúa cada estado dentro de un motor real. Los segmentos de T–s son uniones ilustrativas entre valores resueltos, no trayectorias integradas de un proceso irreversible. La gráfica de estados discretos de tobera tampoco utiliza distancia axial.

## 3. Cómo se relaciona SVG con JavaScript

El servidor ya conoce las temperaturas y presiones. Al crear el SVG, escribe `data-engine-station="pt3"` en el círculo de la salida de compresor, por ejemplo. El navegador no calcula `pt3`: busca los elementos con ese atributo y añade una clase de estilo cuando el usuario selecciona «Compresor». También puede resaltar las barras de trabajo asociadas con `data-engine-work`.

La selección cambia únicamente el estado **visual**. No ejecuta la API porque el dato físico no ha cambiado. En cambio, modificar Mach o T3 invalida las cifras anteriores y provoca el cálculo ya existente; el resaltado desaparece hasta recibir una nueva solución válida. Después se vuelve a aplicar a los puntos recién dibujados sin perder la selección del usuario.

## 4. Por qué no inventamos un perfil axial

Disponer de temperaturas y presiones en las fronteras no determina las distribuciones internas de cada componente. Para obtenerlas sería preciso añadir modelos de geometría, etapas, pérdidas y evolución del fluido que no forman parte de este milestone. El esquema, por tanto, es una herramienta de **lectura de resultados discretos**, no una predicción espacial de toda la máquina.

## 5. Cómo comprobarlo

Selecciona Compresor: deben marcarse los estados de entrada y salida en T–s y en los gráficos totales, además de su trabajo. Selecciona Eje: debe quedar solo una barra mecánica, sin puntos de temperatura. Al cambiar Mach o T3, deben retirarse las marcas hasta que lleguen los nuevos datos. Comprueba también los tres modos A/B/C, los zoom de gráficas y los estudios paramétricos.
