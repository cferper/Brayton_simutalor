# Milestone 44.2 — Aprendizaje: Mach, presión y ondas de choque en la tobera

## 1. ¿Por qué dos gráficos?

El **número de Mach** es la relación entre velocidad del gas y velocidad local del sonido: M=V/a. Es adimensional. La **presión estática** p [kPa] describe la presión termodinámica local del gas, distinta de la **presión total** pt que se asociaría a detener isentrópicamente el flujo. En expansión sin choque, el chorro tiende a acelerar y disminuir presión estática. Un choque normal desacelera el gas desde supersónico a subsónico **aumentando** p estática, generando entropía y perdiendo presión **total**.

En el código no hay posiciones x [m] ni distribuciones continuas de velocidad/presión. Por eso ambas gráficas muestran puntos de **estaciones identificadas**: garganta, antes y después del choque, y salida. Las posiciones horizontales son ordinales para facilitar la lectura; **no son una escala de distancias**.

## 2. Garganta y salida no significan siempre lo mismo

- **Tobera convergente bloqueada:** garganta = salida; M≈1. No se agrega un punto de garganta distinto del de salida.
- **Convergente no bloqueada:** solo se representa la salida, con M<1, porque la rutina no entrega otro plano interior independiente.
- **Convergente-divergente no bloqueada:** garganta y salida son subsónicas.
- **C-D bloqueada supersónica:** la garganta es sónica y la salida puede ser supersónica.
- **C-D con choque normal:** el solver conoce dos estados estáticos en el choque, antes `(M1,p1)` y después `(M2,p2)`. No hay transición suave entre ellos. El archivo `choque_normal_cp.py` calcula ese salto por masa, momento, energía y segunda ley utilizando cp(T); la gráfica solo consulta resultados ya calculados.

Si el choque es interno, el solucionador identifica su relación geométrica `Achoque/Ag`, pero no una distancia en metros. Si la contrapresión está fuera de un dominio resoluble, una `None` no debe mostrarse como cero.

## 3. Qué significa p∞

La línea horizontal de referencia en la gráfica de presión es la **presión ambiente** p∞. Si en la salida `pe>p∞`, el chorro permanece subexpandido; si `pe<p∞`, sobreexpandido. Que las dos no coincidan no es automáticamente un error: depende del estado de salida y de la relación de presiones de la tobera. Ni el gráfico ni el modelo predicen una pluma real, separación o choques externos.

## 4. Cómo se traduce a Python

1. `datos_tobera_graficas(resultado)` recibe el resultado del motor (`dict`), inspecciona si `resultado['tobera']` existe y reúne los puntos calculados en una tupla de pequeños diccionarios. El acceso `n.get('choque_normal')` devuelve el choque o `None`, de manera que los dos puntos de choque **solo aparecen si existen**.
2. La función interior `punto(nombre,mach,presion,papel)` verifica que los números sean reales finitos y que presión sea positiva. No es otro solucionador de flujo; es una comprobación defensiva antes de dibujar.
3. `svg_estados_tobera(datos,magnitud)` dibuja un SVG usando `'mach'` o `'presion'`; la lista de abscisas `xs` se calcula a partir del **número de estados**, igual en ambos gráficos. La referencia es 1 para Mach y `datos['ambiente']` para presión. Las ordenadas solo cambian la escala visual; las etiquetas muestran los valores originales.
4. `preparar_vista_turborreactor(resultado)` llama estas funciones una sola vez después de simular y entrega ambas cadenas HTML/SVG a Jinja; JavaScript no recalcula datos.

**Ejercicio:** toma el caso de choque interno de Tt=1200 K, pt=500 kPa, Ae/Ag=1,5 y p∞=350 kPa. Comprueba que `M1>M2` y `p2>p1`. Después cambia solo p∞ y observa el desplazamiento de choque o el cambio de régimen. No interpretes el desplazamiento entre marcas en la figura como una distancia real.

## 5. Comprobación

Las 9 pruebas propias de 44.2 cubren convergente bloqueada, C-D subsónica y supersónica, choque interno y en salida, estados ausentes, lectura de etiquetas y actualización. Junto a las 7 pruebas vigentes de 44.1, la primera ejecución acumulada dio **16/16 correctas** el 27/10/2026. Sigue siendo una prueba interna del software, no un ensayo de prestaciones reales.


## 6. Revisión conjunta en Windows — 27/10/2026

**Base y alcance.** Se comprueba `mejoras/cp-variable` en
`d61ef3795ae58027927adc5077409bb3dfe6b018` (M43), sin cambios versionados
iniciales. Se incorpora el ZIP acumulado, conservando dos archivos personales
no versionados. No se inicia 44.3 ni se crea commit; el hash base no contiene
44.1/44.2. La revisión local añade evidencia de ejecución y de legibilidad.

**PYTHON — comprobar capas distintas.** Los datos científicos son diccionarios;
el presentador los transforma en texto SVG y Jinja inserta ese texto en HTML.
Se comprueba, para cinco POST, que los SVG recibidos son exactamente los
producidos por `preparar_vista_turborreactor(resultado)`. La prueba en navegador
comprueba otra cosa: lectura, foco, desplazamiento y actualización de la página.
Las firmas completas y ejemplos de `datos_tobera_graficas(resultado)`, su
función local `punto(nombre, mach, presion, papel)` y
`svg_estados_tobera(datos, magnitud)` están en [manual §4.82](../../CODE_WALKTHROUGH.md).
`None` se propaga hasta el aviso HTML; no se sustituye por un punto en cero.

**INTERPRETACIÓN FÍSICA / INGENIERÍA.** Para el motor inicial con C-D y
Ae/Ag=6, M1≈3.141495 cae a M2≈0.456981 mientras p estática sube de
8.407155 a 96.905779 kPa. La salida llega a Mach≈0.399778 y p≈100 kPa.
Es otro caso distinto del ejemplo de tobera aislada Tt=1200 K/pt=500 kPa
usado antes: no mezclar sus números. La abscisa solo ordena estaciones;
la separación de puntos no representa grosor del choque ni distancia.

**Experimento y límites.** Desde el formulario inicial, seleccionar C-D,
Ae/Ag=1,5 y simular: salida supersónica (Me≈1.821278). Cambiar a Ae/Ag=6
y simular: aparecen ambos lados del choque, sin curva suave. Después cargar
Motor estático, fijar Mach=0,9, rp=3, πd=0,7 y T3=500 K: no hay expansión
porque pt4≈84.839 kPa es menor que p∞=100 kPa. Las gráficas de salida deben
desaparecer; T–s mantiene solo los cuatro estados totales. Esto comprueba
que no permanecen datos antiguos. En pantalla estrecha se apilan Mach y
presión y se desplaza cada SVG horizontalmente, también con teclado.

**Resultados actuales.** Python 3.13.0, Windows 11; 16/16 específicas,
74/74 web y 625 en la regresión vigente: 615 correctas, ocho omisiones por
SciPy, una por Cantera y un subcaso por privilegio de enlaces simbólicos,
sin fallos ni errores. Tras el ajuste visual del T–s se repiten las 90
específicas/web, todas correctas. El primer intento falló por temporales de
la sandbox y por contar tres SVG en una prueba de M40; se corrigen entorno
y expectativa, sin alterar física ni rebajar controles de accesibilidad.
Los comandos y resultados iniciales/finales están en [técnico 44.2](44_2_mach_presion_tobera.md).
La suite usa su selección histórica existente; no se descubre toda
`legacy_tests`. No se instalan paquetes ni se generan salidas permanentes
ajenas. Esta verificación interna y visual no constituye validación con un
motor experimental ni cubre todos los navegadores o regímenes posibles.
