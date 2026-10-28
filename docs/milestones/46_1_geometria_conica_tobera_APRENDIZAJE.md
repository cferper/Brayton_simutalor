# Aprendizaje — Milestone 46.1: geometría de un divergente cónico

**28 de octubre de 2026.** Punto de partida verificado: `b9bc18f61dc601241edaa1c9c9d6bf6ef8d04b19`, rama `mejoras/cp-variable`. Sin commit nuevo.

## 1. ¿Qué sabíamos y qué faltaba?

El milestone 45 calculaba áreas y diámetros equivalentes de las secciones de garganta y salida, pero **un área no determina una forma**. Existen muchas toberas con idénticas áreas extremas y distintos contornos. Ahora elegimos conscientemente la familia más sencilla: el **cono de revolución** para el tramo divergente.

## 2. Física y dibujo

Al suponer secciones circulares, `A = πr²`; por tanto, `r = √(A/π)`. La pared es una recta que forma el ángulo de semidivergencia `α` respecto al eje:

`tan(α) = (re-rg)/Ld` y `Ld = (re-rg)/tan(α)`.

Medimos **α desde el eje**, no el ángulo total entre paredes (que sería `2α`). Con `α=0°` aparecería una división por cero; con `α=90°` la tangente es singular. Para un tramo verdaderamente divergente, exigimos `Ae>Ag>0`. El caso `Ae=Ag`, que admite el solucionador, no tiene tramo divergente: se muestra como geometría no disponible en vez de fallar toda la simulación.

Si mantenemos las áreas y reducimos α, la longitud crece. Si cuadruplicamos el caudal de aire sin cambiar el punto termodinámico, las áreas se cuadruplican, cada radio se duplica y **Ld también se duplica** al mantener α fijo. Nada de esto implica que el empuje o el rendimiento mejoren por elegir otro ángulo.

## 3. Python — las funciones

### `validar_semidivergencia(angulo_grados)`

- Entrada: número `Real` finito en grados, diferente de `bool`.
- Salida: `float` [°].
- Errores: `ValueError` si no es real, no es finito o está fuera de `(0,90)`.
- Llaman a ella el adaptador del formulario `simular_turborreactor` y la función geométrica siguiente. No llama al solucionador físico.

### `calcular_geometria_conica(dimensionamiento, angulo_grados)`

- Entradas: diccionario de M45 (`disponible`, `tipo_tobera`, `area_garganta`, `area_salida` [m²]) y ángulo [°].
- Salida: diccionario con bandera de disponibilidad, motivo, radios [m], diámetros [m], áreas [m²], `longitud_divergente` [m], relación de áreas y residuos [m²].
- Llama a `validar_semidivergencia`, `sqrt`, `tan` y `radians`; no calcula presiones ni velocidades. La llama `simular_turborreactor` después de `dimensionar_tobera` sólo cuando existe caudal con tobera C-D. Ángulos erróneos no bloquean la simulación específica o convergente.
- Si no hay dimensiones o la tobera es sólo convergente, devuelve `disponible=False` y magnitudes geométricas `None`; con áreas incompatibles lanza `ValueError`.

### `svg_geometria_conica(geometria)`

- Entrada: diccionario anterior; salida: cadena SVG o `None` si no hay geometría.
- Calcula **una única escala** `px/m` para el eje y la dirección radial, y crea `<polygon>`, `<line>` y `<text>`; así el dibujo representa el ángulo geométrico real.
- La llama `preparar_vista_turborreactor`, después de simular. No se dibujan estados de flujo ni se interpolan resultados.

## 4. ¿Cómo probarlo?

1. Selecciona **tobera convergente-divergente**, introduce un gasto de aire (por ejemplo 20 kg/s), deja semidivergencia en 15° y pulsa Simular.
2. Anota `Ag`, `Ae`, radios y longitud; verifica que `πr²` reproduce las áreas.
3. Cambia sólo α a 10°: la longitud debe crecer; los estados termodinámicos no deben variar.
4. Cambia sólo el caudal de 20 a 80 kg/s: áreas ×4, radios y longitud ×2.
5. Prueba el formulario sin caudal y con tobera convergente: no debe aparecer una longitud cónica ficticia.

## 5. Verificación frente a validación

Diez pruebas nuevas contrastan ecuación analítica, radios/áreas, escalado, monotonicidad, conservación del resultado termodinámico, ausencia de estados y SVG XML. **10/10 superadas** el 28/10/2026. Esta es **verificación de software** y de una hipótesis geométrica elemental, no **validación experimental** de una tobera con pérdidas.

Los perfiles `Mach(A/Ag)` y `p(A/Ag)` ya existen en M44.4, pero su proyección a la coordenada axial se deja para 46.2; el barrido de ángulos queda para 46.3. No hemos optimizado la longitud ni el empuje.

Documento técnico relacionado: [46.1](46_1_geometria_conica_tobera.md).
