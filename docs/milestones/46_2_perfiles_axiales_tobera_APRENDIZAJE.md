# Aprendizaje 46.2 — De la relación de áreas a una distancia física

**28 de octubre de 2026.** Continuación de 46.1 sobre base publicada `b9bc18f61dc601241edaa1c9c9d6bf6ef8d04b19`, sin commit nuevo.

## 1. ¿Por qué ahora sí podemos usar metros?

En M44.4 conocíamos Mach y presión como funciones de `A/Ag`. Eso **no basta** para asignar distancias: infinitas toberas comparten las áreas pero tienen longitudes diferentes. En 46.1 elegimos una forma cónica; conocemos radio de garganta y ángulo, de modo que cada sección se asocia a una posición única del tramo divergente.

La ley geométrica del cono es `r(x)=rg+x·tan(α)`; al sustituir `A=πr²` obtenemos:

`x = (√(Ag·a/π)−rg)/tan(α)`, donde `a=A/Ag`.

Comprueba que para `a=1`, `x=0`, y para `a=Ae/Ag`, `x=Ld`. Cambiar α o el caudal de aire cambia la posición en metros, **pero no cambia por sí solo los estados termodinámicos**.

## 2. Python — funciones nuevas

### `posicion_axial_por_area(area_relativa, geometria)`

Recibe una relación `a` adimensional numérica finita y un diccionario de geometría 46.1 disponible; devuelve `x` [m]. Usa `sqrt`, `pi`, `tan`, `radians` y los radios originales; lanza `ValueError` si falta geometría, `a` es inválida o está fuera de `[1,Ae/Ag]`. Devuelve los extremos exactamente como `0.0` y `Ld` para evitar ruido de redondeo. La llama la proyección que sigue.

### `proyectar_perfil_axial(perfil, geometria)`

Recibe el diccionario de M44.4 (`segmentos`, `choque`, `relacion_areas`, `p_ambiente`) y el de 46.1; devuelve un dict con `disponible`, `motivo`, `segmentos` de estados con `x`, `choque`, `x_choque`, `longitud_divergente`, `regimen`, `p_ambiente`.

Utiliza comprensión de tuplas y expansión de diccionarios `{**estado, 'x': posicion...}`: se crea **una copia**, preservando el dict original y las magnitudes físicas. La función **no llama** al solucionador físico. Si falta un perfil o geometría, devuelve indisponibilidad explicada en vez de una curva artificial. La invoca `preparar_vista_turborreactor`.

### `svg_perfil_axial(datos, magnitud)`

Recibe la salida de la proyección y `'mach'` o `'presion'`; devuelve texto SVG o `None`. Las posiciones se dibujan con una escala longitudinal común y los valores verticales se toman literalmente de los estados.

Para un choque usa **dos `<polyline>`**, una por cada región física, y una línea vertical discontinua en la posición del choque. No conecta el punto anterior con el posterior como si atravesase estados intermedios. Esta función sólo dibuja: no interpola Mach ni presión.

## 3. Casos que debes reconocer

| Régimen | Perfil axial correcto |
|---|---|
| C-D supersónica ideal | Rama de Mach creciente; presión decreciente |
| C-D subsónica | Mach decreciente y presión creciente en el divergente |
| Choque interno | Dos ramas y dos valores en la misma `xchoque` |
| Choque en salida | El salto ocurre en `x=Ld`; sin prolongación exterior |
| C-D sin solución o `Ae/Ag=1` | Sin curva axial; diagnóstico explícito |
| Tobera convergente o sin caudal | No se inventa un divergente cónico |

## 4. Corrección 46.1 y aprendizaje de diseño de interfaces

El campo α no debe validar una simulación si **no se usa**: antes, un texto inválido podía impedir incluso una simulación sin caudal. Ahora la validación condicional depende de que haya caudal y se haya seleccionado una C-D. También `Ae/Ag=1` puede ser válido para el solucionador aunque no corresponda a un divergente de longitud positiva. Se evita que una hipótesis gráfica bloquee la física.

## 5. Verificación ≠ validación

**Ajuste de 46.3 (28/10/2026).** La posición de una sección con redondeo tolerado no puede fallar después de superar la comparación de áreas. Ambos puntos de control usan `2e-6` relativo y los valores físicos `Mach`/`p` se preservan. Los gráficos incorporan números en ambos ejes y referencias `M=1`/`p∞`; dos pruebas adicionales cubren ambos detalles. La suite de 46.2 pasa a **10 métodos**.

Las pruebas nuevas comprueban la ecuación inversa de área, extremos, monotonicidad, conservación *exacta* de estados, posición común de choque, independencias de las polilíneas, sensibilidad geométrica y estados no disponibles. **8/8 pruebas nuevas y 20/20 combinadas con 46.1**, sin fallos ni errores. Eso verifica el software y la geometría elegida, **no valida** predicciones de pérdidas de una tobera real.

La entrega 46.3 estudiará ángulo y longitud para áreas fijas. No se ha comenzado ni se deducirá un ángulo óptimo de rendimiento sin otro modelo físico.

[Documento técnico de 46.2](46_2_perfiles_axiales_tobera.md).
