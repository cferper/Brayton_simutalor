# Milestone 46.2 — Mach y presión frente a la coordenada axial

**28/10/2026.** Rama `mejoras/cp-variable`. Base publicada comprobada: `b9bc18f61dc601241edaa1c9c9d6bf6ef8d04b19`. Entregas 46.1–46.2 todavía sin commit ni push.

## Estado anterior

El milestone 44.4 calculaba estados físicos en secciones `A/Ag`, incluidas dos ramas separadas por choque normal. La entrega 46.1 construía longitud y dibujo de un divergente cónico, pero sin convertir los estados a posiciones `x`.

## Corrección de compatibilidad 46.1

El campo de ángulo se valida **sólo** si existe gasto de aire y se selecciona una C-D: ni la convergente ni el modo específico sin caudal deben bloquearse por una entrada geométrica irrelevante. En el estado límite `Ae/Ag=1`, admitido por el solucionador, el dimensionamiento M45 sigue disponible pero la geometría devuelve `disponible=False` con motivo explícito: no hay tramo divergente de longitud positiva. Se añadieron pruebas a `tests/test_geometria_tobera_conica_46_1.py`. No se modificó el solucionador.

## Qué se ha añadido

Módulo `perfil_axial_tobera_conica.py`:

- `posicion_axial_por_area(area_relativa, geometria)`: convierte una relación `A/Ag` resuelta en posición longitudinal `x` [m].
- `proyectar_perfil_axial(perfil, geometria)`: copia los segmentos calculados por M44.4, añadiendo `x` a cada estado. Conserva los valores de `mach`, `presion`, entropía y restantes propiedades sin ajuste ni nueva solución física.
- `svg_perfil_axial(datos, magnitud)`: dos SVG separados, Mach frente a `x` y presión estática frente a `x` [kPa]. Los segmentos físicos son polilíneas **independientes**; para un choque se marca la posición común y se evita unir las dos ramas con una curva espuria.

Se llama a la proyección en `preparar_vista_turborreactor` después de obtener el perfil M44.4. Dos nuevos gráficos aparecen en el apartado de visualizaciones, vinculados a la longitud y la hipótesis geométrica de 46.1. Las gráficas anteriores frente a `A/Ag` permanecen intactas.

## Ecuaciones y conservación

Para radio de garganta `rg`, semidivergencia `α`, área de garganta `Ag` y área local `A`:

\[
r(x)=r_g+x\tan\alpha,\quad A(x)=\pi r(x)^2,
\quad x(A)=\frac{\sqrt{A/\pi}-r_g}{\tan\alpha}.
\]

En un estado de M44.4 con `a=A/Ag`, la función utiliza `A=Ag·a`. La garganta da `x=0` y la salida `x=Ld`. Un choque interno en `Achoque/Ag` se sitúa en `xchoque=x(Achoque/Ag)`; las dos ramas tienen ese mismo `x` y valores distintos de `Mach` y `p`, como exige la discontinuidad. Para choque de salida `xchoque=Ld` y no existe segmento exterior adicional.

## Verificación y limitaciones

**Corrección puntual durante 46.3 (28/10/2026):** ambos filtros de área emplean ahora la misma tolerancia relativa `2e-6`; las pequeñas diferencias de redondeo aceptadas se sitúan en el extremo geométrico correspondiente sin modificar estados físicos. Los SVG axiales añaden graduaciones numéricas y rótulos de `M=1` o `p∞` ambiente. Se agregaron dos pruebas a esta batería; el recuento vigente es **10 pruebas**. Véanse [46.3](46_3_estudio_angulo_longitud.md) y [cierre 46](46_cierre_geometria_tobera.md).

Pruebas de `tests/test_perfiles_axiales_tobera_46_2.py`: conversión analítica/inversa, extremos, monotonicidad, identidad de Mach y presión, régimen subsónico, supersónico y choque interno/salida, segmentos independientes del SVG, efectos de α y caudal, casos sin geometría y compatibilidad web. Ejecutadas **8/8 correctas**, sin fallos ni errores. Junto con 46.1 corregida, **20/20**.

Regresión científica relacionada realmente ejecutada (M46.1, M46.2, M45, M44.1–44.4, M37 y M42.A/C):

```bash
python3 -m unittest -q tests.test_geometria_tobera_conica_46_1 \
  tests.test_perfiles_axiales_tobera_46_2 \
  tests.test_gasto_masico_dimensionamiento_45 \
  tests.test_perfiles_tobera_44_4 \
  tests.test_balance_energetico_turborreactor_44_3 \
  tests.test_graficas_tobera_44_2 \
  tests.test_graficas_turborreactor_44_1 \
  tests.test_combustible_cp_variable_37 \
  tests.test_tobera_convergente_divergente_42a \
  tests.test_choque_normal_42c
```

**126 pruebas, 126 correctas, 0 fallos, 0 errores, 0 omisiones.**

No se calcula el flujo de nuevo ni se interpola para generar puntos; la secuencia gráfica une visualmente estados **ya calculados** en una misma rama. Esta comprobación es verificación de la transformación geométrica, no validación aerodinámica de un contorno real. El modelo no incorpora pérdidas por cono, rozamiento, separación o choques oblicuos. La sensibilidad del ángulo es la futura 46.3.

**Pruebas históricas completas e inspección web en Windows:** pendientes para la integración final. Las dependencias Flask/Jinja2 no están disponibles en el entorno de desarrollo.

## Commit asociado

Pendiente de autorización. `main` y los documentos personales no se modificaron.
