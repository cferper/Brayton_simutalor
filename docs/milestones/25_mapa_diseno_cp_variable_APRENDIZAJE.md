# Milestone 25 — Aprendizaje: mapas de diseño Brayton con cp(T)

## 1. Qué sabíamos y qué cambiamos (24/10/2026)

La base verificada de la Fase 2F es `cee7753eab68eafcb1616a3edd63e9a111248dcd`. El solucionador `resolver_ciclo` de 2B ya devolvía estados, energías y viabilidad con propiedades del aire variables. Optimización 2C encontraba A/B para **una temperatura T3 fija**. Sensibilidad 2E barría **un solo factor**. El panel «Mapa de diseño» no calculaba cp(T) y estaba desactivado.

Ahora ese panel presenta simultáneamente los efectos de la compresión `rp` y de la temperatura máxima `T3`, sin escribir otra versión de las ecuaciones físicas.

## 2. Física — de una curva a un mapa de diseño

Imagina que para un ciclo Brayton escoges `rp=10` y `T3=1600 K`. El compresor consume trabajo \(w_c\), la turbina entrega \(w_t\), y la diferencia \(w_{neto}=w_t-w_c\) es el trabajo específico neto. El calor aportado es \(q_{in}\); el rendimiento es \(\eta=w_{neto}/q_{in}\) **solo si hay ciclo motor viable**. Todos esos valores se obtienen de diferencias de entalpía variable h(T), no de un cp constante.

En un barrido OFAT eliges solo un parámetro, por ejemplo T3, y dejas `rp=10` en todas las pruebas. En una **malla bidimensional** eliges varios niveles de rp y T3. Cada pareja `(rp,T3)` corresponde a un ciclo distinto. Las otras cinco entradas se mantienen fijas: T1 [K], p1 [kPa], eficiencia del compresor, eficiencia de la turbina y pérdida de presión del combustor (las tres últimas como fracciones).

Los mapas colorean únicamente celdas **motoras**: el de trabajo [kJ/kg] y el de rendimiento [%]. Los estados «no motor», «fuera de 200–2000 K», «entrada inadmisible» y «error numérico» tienen colores de diagnóstico aparte. No los pintamos como trabajo=0 o rendimiento=0, porque eso introduciría falsos mínimos y falsas continuidades de la prestación.

## 3. PYTHON — cómo se organiza una matriz

`calcular_mapa_cp_variable(entradas, rp_min=1.1, rp_max=80, T3_min=1200, T3_max=1800, n_rp=31, n_T3=31)` construye dos listas de coordenadas: `rps` y `T3s`. `rps` se reparte **uniformemente en log(rp)**; la progresión es multiplicativa y representa mejor ratios pequeñas y grandes. `T3s` se reparte linealmente: entre 1200 y 1800 K hay saltos iguales.

Después forma `filas[j][i]`: `j` selecciona el nivel de T3; `i` la columna de rp. Cada celda tiene la forma:

```python
{
    'rp': 10.0,
    'T3': 1600.0,
    'estado': 'motor',
    'motivo': '',
    'datos': {...},
    'operativas': {...}
}
```

Los puntos no calculables retornan `datos=None`; los calculables no motores retienen sus datos para diagnóstico, pero siempre `operativas=None`. Esto es una **máscara de viabilidad**. El `Counter` cuenta cuántas celdas hay de cada tipo. En el caso base, 31×31 son 961 evaluaciones, con 959 motoras y 2 no motoras.

### Funciones y responsabilidades

- `DEFAULT_MAPA: dict`, `MAX_PUNTOS_EJE=51`: configuración inicial y tope de 2601 celdas. Permite explorar sin bloquear el servidor Flask por mallas enormes.
- `_configuracion_valida(entradas,rp_min,rp_max,T3_min,T3_max,n_rp,n_T3) -> None`: valida la forma y los intervalos introducidos; pide al solucionador 2B la comprobación de entradas físicas, no duplica sus reglas. `ValueError` si la ventana o el número de puntos no son correctos; el intervalo solicitado queda limitado a rp positiva y no mayor de 1000 y T3 positiva no mayor de 3000 K. **Estas cotas de interfaz no amplían** los 200–2000 K de las correlaciones.
- `_evaluar_punto(entradas,rp,T3) -> dict`: recibe siete parámetros, sustituye `rp` y `T3` en una copia y llama a `resolver_ciclo(**{**entradas,'rp':rp,'T3':T3})`. La sintaxis `**` pasa las claves de un diccionario como argumentos con nombre. Captura las excepciones para distinguir estados. No hace conversiones de propiedades en paralelo.
- `calcular_mapa_cp_variable(...) -> dict`: usa `filas=[[... for rp in rps] for T3 in temperaturas]`, una comprensión de listas anidada. Selecciona `mejores_malla` con `max(...,key=...)`, **solo entre celdas motoras**. Si no hay ninguna, devuelve `None` para ambos mejores puntos y cuenta las causas.
- `_color_mapa(fraccion,rendimiento=False) -> str`: transforma un número entre 0 y 1 en un color hexadecimal de SVG por interpolación RGB. La magnitud física **no cambia**; solo cambia cómo la vemos.
- `svg_mapa_cp_variable(estudio,magnitud,opt=None) -> str|None`: dibuja un `<rect>` por celda; cada rectángulo incluye un `<title>` con rp, T3 y diagnóstico o trabajo. Dibuja ejes, barra de color y leyenda. Cuando recibe A/B de 2C, coloca marcadores solo si son máximos interiores para la T3 de referencia y están dentro de la ventana. Sin motores devuelve `None`, no una gráfica inventada.
- `preparar_mapa(entradas,rp_min,rp_max,T3_min,T3_max,n_rp,n_T3) -> dict`: coordina los cálculos y la presentación. Llama a `calcular_mapa_cp_variable`, opcionalmente una vez a `estudiar_cp_variable` de 2C para la T3 de referencia, y genera ambos SVG. Devuelve todos los datos para Flask.

La cadena completa es: formulario del usuario → `web_app.index()` → `leer_entradas()` → `preparar_mapa()` → `calcular_mapa_cp_variable()` → muchas llamadas a `resolver_ciclo()` → SVG → `dashboard.renderizar_dashboard()` → `templates/index.html`.

## 4. Por qué distinguir exploración de optimización

Imagina 31 valores de rp y 31 de T3. Obtenemos **961 celdas**: el mayor número dentro de esas celdas es el *mejor valor muestreado*. Si repetimos con 51×51, podemos encontrar otro mayor porque hemos explorado más puntos. El máximo puede estar incluso fuera de la ventana que dibujamos.

En cambio, `estudiar_cp_variable` (Fase 2C) busca máximos continuos a **T3 fija**. Para el caso base T3=1600 K:

- A: rp≈15,877934, trabajo neto máximo≈414,086 kJ/kg.
- B: rp≈46,819105, rendimiento máximo≈43,745 %.

El mapa predeterminado llega hasta 1800 K, por lo que el mayor trabajo de **toda la malla** (≈524,635 kJ/kg) no coincide con el valor A obtenido **solo** a 1600 K. Compararlos como si fueran la misma búsqueda sería incorrecto. También es posible que una frontera abierta tenga un *supremo no alcanzado*: el mapa no debe marcarlo como punto real.

## 5. Conexión Python–Flask–HTML y coste

El navegador muestra una sola plantilla: `templates/index.html`. En ella el formulario de Simulación tiene los siete parámetros originales y el panel Mapa añade seis controles para rangos y tamaño de malla. Las entradas permanecen sincronizadas porque están dentro del mismo formulario HTML.

No se recalcula nada al escribir ni al abrir la sección. Solo `POST /` con `accion='mapa'` activa el cálculo. Si el usuario escribe muestras fuera de 5–51, extremos invertidos, `NaN` o presiones inválidas, la respuesta 400 conserva el valor introducido y explica el error. El JavaScript de la interfaz cambia pestañas, pero no realiza ecuaciones; toda la física procede de Python. Si un navegador permite pasar el cursor sobre el SVG, el `<title>` ofrece el detalle de una celda sin una biblioteca nueva. En pantallas táctiles esa interacción puede variar.

La resolución inicial **31×31=961** evalúa centenares de ciclos. El límite **51×51=2601** impide peticiones desmesuradas. El coste es proporcional al número de celdas, aproximadamente \(O(n_{rp}\,n_{T3})\), aparte de la búsqueda de A/B una sola vez. No instalamos SciPy ni librerías de gráficos nuevas.

## 6. Ejercicios para estudiar

1. Calcula un mapa 5×5 de rp=10–20 y T3=1500–1700 K. Localiza la celda rp=10, T3=1600: ¿por qué entrega ≈402,071 kJ/kg y ≈34,893 %?
2. Amplía rp hacia 1. ¿Por qué algunos puntos pueden ser calculables, pero no motores? ¿Qué significa una celda gris?
3. Amplía T3 hasta 2300 K. ¿Por qué aparecen entradas inadmisibles a pesar de que la ventana gráfica acepta 2300 K?
4. Compara el mayor trabajo de una malla 5×5 y una 31×31 con los mismos extremos. ¿Por qué no puedes llamar «óptimo continuo» al mejor nodo?
5. Cambia ηc de 0,85 a 0,75. Describe cómo esperarías que cambien las regiones motoras y el trabajo neto, **sin** asumir que ocurre lo mismo en todos los regímenes.
6. En la función `_evaluar_punto`, explica por qué se captura `EstadoFueraDeRango` **antes** que `ValueError` y por qué `operativas` es `None` cuando `viable=False`.

## 7. Pruebas y límites

Se añaden 10 pruebas científicas y 6 de Flask/visualización. Las 48 pruebas focalizadas anteriores deben seguir superándose; el total previsto es **64**. GitHub Actions ejecuta el árbol exacto en una rama temporal, antes de publicar en desarrollo. Estas comprobaciones verifican la implementación y la coherencia interna con 2B/2C: no validan datos experimentales.

Segunda ley y exergía siguen desactivadas. No se modifican algoritmos 2A, 2B, 2C, informes de gas perfecto ni el repositorio de conservación. No se ha iniciado la Fase 2G. Cualquier comprobación visual real con navegador debe documentarse por separado de `Flask.test_client()`.

## 8. Estado Git

Base publicada verificada: `cee7753eab68eafcb1616a3edd63e9a111248dcd`. La Fase 2F se desarrolla en `validacion/fase-2f-cp`, con un único commit definitivo autorizado previsto en `mejoras/cp-variable` tras CI satisfactoria; no se modifican `main` ni el repositorio `Brayton_simutalor-gas_perfecto`.
