# Aprendizaje 46.3 — Estudiar longitud sin confundirla con eficiencia

**28/10/2026.** Base comprobada: `b9bc18f61dc601241edaa1c9c9d6bf6ef8d04b19`; trabajo pendiente de commit.

## 1. ¿Qué significa variar un ángulo?

Tenemos `Ag` y `Ae` calculadas por el mismo motor y el mismo caudal de aire. En un cono de revolución eso fija `rg` y `re`. Si la pared se abre más deprisa (α mayor), alcanza el radio de salida en menos distancia:

`Ld = (re−rg)/tan(α)`.

Como `tan(α)` crece de 0° a 90°, `Ld` decrece. Es una conclusión **geométrica**. El modelo actual no contiene un término de pérdidas por ángulo ni por longitud, por lo que no permite concluir que el cono corto tenga mejor empuje real.

## 2. Python — las funciones nuevas

### `estudiar_angulos_geometria(geometria, *, angulos=ANGULOS_EDUCATIVOS)`

- Entradas: dict geométrico M46.1 y secuencia de ángulos (por defecto tupla `(5.,10.,15.,20.,25.)`).
- Salida: dict con `disponible`, `motivo`, `filas`, `seleccionado` y `comparacion`. Cada fila incluye ángulo [°], longitud [m], diámetros [m], radios [m], relación adimensional y bandera `seleccionado`.
- Llama a `calcular_geometria_conica` con **las mismas áreas originales** para cada α. No llama al solucionador M37 ni al perfil M44.4. Si no hay geometría, devuelve filas vacías y motivo.
- El argumento `*` obliga a pasar `angulos=` por nombre. `set` elimina duplicados si el ángulo seleccionado coincide con uno de los ejemplos; `sorted` ordena de menor a mayor. Lo llama el adaptador de presentación.

### `svg_longitud_angulo(estudio)`

Entrada: dict de estudio; salida: cadena SVG o `None`. El eje horizontal usa α [°] y el vertical `Ld` [m]. Marca el ángulo seleccionado en rojo. La polilínea une sólo las **longitudes analíticas calculadas**; no representa un ajuste experimental ni una función de rendimiento. Llama a ella `preparar_vista_turborreactor`.

### `svg_comparacion_conos(estudio)`

Entrada: dict de estudio; salida: SVG o `None`. Dibuja tres perfiles (10°,15°,20°), cada uno con las **mismas áreas**. Calcula una sola escala `px/m`, compartida entre x e y y entre los tres dibujos, para no falsificar la comparación. La llama también el preparador de vista.

## 3. Ajustes puntuales heredados de 46.2

La constante `TOLERANCIA_RELATIVA_AREAS=2e-6` se usa tanto al comprobar que el perfil y la geometría corresponden a las mismas áreas como al convertir cada `A/Ag` a `x`. Si un redondeo mínimo sitúa la salida justo fuera del intervalo aceptado, se coloca en `x=Ld` sin cambiar su Mach ni presión. Una discrepancia que supera la tolerancia se rechaza. Los SVG axiales muestran graduaciones numéricas y las referencias físicas **M=1** y **presión ambiente**; no unen las ramas a través de un choque.

## 4. Experimentos y aprendizaje

1. Selecciona C-D y un caudal de aire (por ejemplo 20 kg/s).
2. Compara 5°, 10°, 15°, 20° y 25° en la tabla. Verifica que sólo cambia la longitud.
3. Introduce un ángulo diferente, por ejemplo 12°: aparece en la tabla y queda marcado en la gráfica.
4. Compara los tres contornos con una escala común: 10° es más largo que 15°, y 15° más largo que 20°.
5. Cambia sólo el ángulo y comprueba que la solución termodinámica y el empuje específico no cambian.

## 5. Optimización geométrica condicionada

Si fijamos por ejercicio `5°≤α≤25°`, la **menor longitud dentro de ese intervalo** se obtiene al alcanzar el límite superior `α=25°`. Esto no permite afirmar que el cono sea óptimo: hemos omitido el rozamiento, la separación, el empuje divergente, la masa y las condiciones externas. En un diseño real habría que evaluar y validar modelos adicionales antes de optimizar.

## 6. Verificación frente a validación

Ocho pruebas 46.3 y dos nuevas pruebas 46.2 verifican sensibilidad, escala de dibujos, invariantes y tolerancias. No constituyen validación de una tobera real ni autorizan un modelo empírico de pérdidas. Los resultados agregados del milestone se encuentran en [cierre 46](46_cierre_geometria_tobera.md).

Documento técnico: [46.3](46_3_estudio_angulo_longitud.md).
