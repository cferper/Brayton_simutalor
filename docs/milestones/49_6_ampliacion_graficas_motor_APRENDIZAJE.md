# Milestone 49.6 — Aprender a leer las gráficas del motor

## De controles a representaciones

Los controles del banco (modalidad A/B/C, Mach, T3 y parámetros avanzados) producen una petición a la API ya existente. Flask invoca el solucionador, prepara los estados y devuelve las representaciones SVG. JavaScript coloca esas figuras en el visor. Cambiar de familia o de gráfica **no** llama al solucionador: solo cambia cuál se ve.

## Ciclo termodinámico

**Diagrama T–s:** cada marcador representa un estado termodinámico calculado. Las líneas son orientativas; no implican que se hayan resuelto todos los estados intermedios.

**Temperatura total (K):** se muestran cuatro estados de remanso (tras difusor, compresor, cámara de combustión y turbina). La compresión eleva generalmente Tt; la combustión eleva Tt hasta T3; la turbina reduce Tt al extraer trabajo. T3 es la temperatura total **de entrada a turbina**, no la de salida.

**Presión total (kPa):** el compresor aumenta pt, la cámara puede perder una fracción de pt y la turbina reduce pt durante la expansión. La presión estática exterior o de salida de tobera no se debe conectar como si fuera presión total.

**Trabajos (kJ/kg de aire entrante):** trabajo absorbido por el compresor, trabajo entregado por la turbina y trabajo transmitido por el eje. Es importante distinguirlos del empuje. El eje incorpora el rendimiento mecánico; no se interpreta `Wt − Wc` como trabajo útil de un turborreactor.

**Energías por componente:** barras de magnitudes tomadas de balances ya calculados. Compresor, aporte químico, turbina y energía cinética **no se suman entre sí**: describen intercambios en distintos componentes. Las magnitudes están normalizadas con la masa de aire entrante, teniendo en cuenta el combustible cuando corresponde.

## Tobera

El Mach, la presión **estática**, la temperatura **estática** y la velocidad local son propiedades del flujo. Se representan frente a distancia axial *solo* si el solucionador dispone de estados de un divergente C-D y la geometría permite asignar posiciones a las secciones calculadas.

En un choque normal, las propiedades pueden cambiar bruscamente. Se muestran dos ramas independientes, con los estados «antes» y «después» en la misma posición; conectar esos estados como una evolución suave sería físicamente engañoso.

**Presión total axial:** el perfil vigente no la proporciona punto por punto, aunque conozcamos la presión estática. Por ello **no** se presenta esa curva. Si más adelante el solucionador publica explícitamente pt en sus estados axiales, se podrá añadir sin inventar relaciones nuevas.

## Prestaciones

La descomposición del empuje distingue la contribución positiva del chorro, la resistencia de la corriente de entrada, el empuje de presión y la suma neta. Las barras usan signo: no hay que sumar sus valores absolutos. El empuje absoluto, expresado en N, solo puede verse si el modelo conoce un caudal válido; el específico usa N/(kg/s de aire).

La comparación de velocidades muestra V₀ (vuelo) y Vₑ (salida), ambas en m/s. Son dos estados conocidos; las barras no describen cómo acelera el flujo entre el difusor y la salida. La representación local del divergente C-D se consulta por separado en la familia Tobera.

## Uso y ampliación

1. Selecciona una familia (Ciclo, Tobera, Prestaciones). La familia Estudios paramétricos abre el banco independiente heredado del 49.5.
2. Elige una gráfica disponible; las no aplicables a la configuración actual no se ofrecen como si fueran válidas.
3. Modifica Mach, T3 o modo. El controlador M48 cancela peticiones antiguas y actualiza el conjunto completo de resultados.
4. Selecciona un punto para leer su magnitud, usa zoom y exporta SVG o PNG cuando lo permita el navegador.

Para añadir otra gráfica, primero identifica el campo físico y las unidades en el solucionador. Después crea la visualización en Python, publícala como `svg_*` en `preparar_vista_turborreactor`, añade un panel y pestaña en la plantilla, conéctala mediante `dibujar(...)` al JS y prepara pruebas que verifiquen datos, disponibilidad y estados discontinuos. El HTML clásico debe continuar separado de las opciones nuevas del banco.

## Iteración del 10-11-2026: geometría de referencia del modo C

El motor C combina mapas calibrados de compresor y turbina con las condiciones de tobera. La geometría **no** es solo un dibujo: el área de garganta afecta al caudal que puede admitir la tobera, por lo que modifica los residuos de masa y el equilibrio del eje. Una mala elección puede impedir que el algoritmo alcance sus tolerancias, sin que ello demuestre que exista una imposibilidad física.

La función `punto_diseno_47()` genera una **referencia matemática de calibración** con condiciones fijas del modelo, no con el Mach y la T3 que se están explorando. Utiliza `dimensionar_tobera()` y devuelve dos áreas: `area_garganta_diseno` y `area_salida_diseno`. En esta versión ambas valen aproximadamente 0,0473481164 m²: el punto se calibró con una **tobera convergente**. Por tanto, Ae/Ag = 1 es la referencia calculada, **no** un diseño C-D óptimo. Si se desea estudiar una convergente-divergente, se modifica Ae después de aplicar la referencia.

En la interfaz, el botón «Restablecer geometría de diseño» únicamente se muestra en modo C. Al pulsarlo, JavaScript consulta `GET /api/turborreactor/geometria-diseno`. Flask llama al diseño existente y devuelve áreas en m². La función JS `aplicarGeometriaDiseno49(garganta, salida, datos)` valida que ambas sean finitas, positivas y Ae ≥ Ag; escribe solo esos dos controles y devuelve `{ag, ae}`. Si no llegan datos válidos, lanza un error sin modificar los campos. La función es puramente de interfaz: **no resuelve el motor**.

El controlador principal `inicializar48(documento, fetcher)` comprueba antes de aplicar que seguimos en C y que nadie ha editado las áreas mientras se consultaba la referencia. Emite los eventos `input` habituales para marcar resultados y estudios antiguos como obsoletos y llama una sola vez a `controlador.cambiar()`. Se mantiene la sincronización del formulario enviado al backend y la prevención de respuestas atrasadas. Cambiar entre A/B/C **no** restaura dimensiones automáticamente.

Ejemplo: con Mach 0,838 y T3 1704 K, Ag = 0,5 m² y Ae = 3,5 m² puede no producir equilibrio numérico verificado. Restablecer recupera la referencia del modelo. El usuario puede volver a fijar Ae = 1,5 Ag para estudiar una tobera C-D; ese 1,5 fue ensayado en pruebas, pero **no** es la relación de diseño calibrada por M47.


La verificación efectuada en esta integración pasó 5 pruebas focalizadas, 21 pruebas HTTP/API, estudios 49.5 y gráficas, y 9 pruebas JavaScript. La regresión Python completa ejecutó 779 pruebas: 769 correctas, 10 omitidas y 0 fallidas. Es verificación de código e integración, no validación con datos experimentales. La revisión visual manual en navegador fue aprobada por el usuario el 10-11-2026. El milestone se publica en un único commit de `mejoras/cp-variable`; `main` no se modifica.

## Verificación en Windows (2026-11-09)

La integración parte del commit 49.5 `c731375046aff4a52fe6ac1e56659f22d1c4a297`.
La suite completa pasó 770 métodos, con 10 omitidos; los 8 tests JavaScript y
la sintaxis del controlador también pasaron. El archivo de prueba 49.6 reporta
4 métodos `unittest` en esta copia del ZIP (aunque las instrucciones de
entrega mencionan 17); los cuatro fueron correctos.

Flask test client confirmó las rutas, A/B/C y la serie de estudios 49.5. Con
tobera C-D y geometría válida, las tres modalidades devolvieron gráficos de
temperatura y velocidad axial, trabajos y velocidades de extremos; con tobera
convergente, las series axiales no aplicables quedaron ausentes. Las respuestas
JSON se serializaron con `allow_nan=False`. No se cambió ningún solucionador.
La inspección visual y las descargas mediante navegador quedan para el usuario.

## Corrección de incidencias (2026-11-09)

El panel 49.5 existía y su controlador retiraba `hidden`, pero la regla CSS
heredada `.turbo-section:not(#configuracion)` lo mantenía en `display:none`
con `!important`. Se excluye también `#estudio49`; los controles y sus
exportaciones conservan el mismo código. Una prueba ejecuta el controlador
JavaScript real con elementos DOM simulados, alterna repetidamente entre
Punto motor y Estudios y comprueba el contrato CSS. No equivale a revisión visual.

Para C se comparó el adaptador actual con el de la base 49.5 sin sobrescribir
archivos: diseño (20 kg/s, 20 000 rpm), Mach 0,4, T3=1550 K y C-D Ae/Ag=1,2
conservan exactamente resultados. Mach 0,838/T3=1704 K converge con garganta
de diseño para Ae/Ag=1,2; 1,5 y 2. Con garganta aumentada un 10 % y Ae/Ag=1,5
se reproduce en ambas versiones la falta de descenso (13 iteraciones,
residuo normalizado aproximado 0,02369, superior a 2e-7). No es evidencia
suficiente para declarar ausencia física de solución ni un defecto del solver.
El usuario confirmó después Ag=0,5 m² y Ae=3,5 m² (Ae/Ag=7), sin otros cambios.
Con Mach=0,838 y T3=1704 K, tanto la base 49.5 como la versión actual terminan
por falta de descenso tras 13 iteraciones; el residuo normalizado queda en
8,201032, frente a la tolerancia 2e-7. La garganta es 10,5601 veces la de
diseño (0,04734811643457149 m²). Se confirma el mismo fallo numérico previo,
sin prueba de inexistencia de una solución física global.

`_simular_motor_acoplado_web(valores)` solo cambia su diagnóstico textual de
no convergencia: explica que no se obtuvo equilibrio verificado y conserva el
detalle numérico. La API responde 422 sin inventar resultados. Pruebas con
`patch(..., wraps=resolver_motor_acoplado)` verifican que Mach, T3 y áreas
llegan al solucionador; se comprueban además los cierres históricos de masa y
potencia. No se alteran mapas, inicialización, tolerancias o solucionadores.

Tras las correcciones, la regresión completa se ejecutó una vez: 774 métodos
en 127,944 s, con 764 correctos, 10 omitidos y cero fallos/errores. Pasaron las
4 pruebas Python nuevas, las 10 históricas del acoplamiento y los 9 tests JS.
