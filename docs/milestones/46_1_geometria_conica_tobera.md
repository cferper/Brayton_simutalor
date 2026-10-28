# Milestone 46.1 — Geometría cónica axisimétrica del divergente

**Fecha de verificación:** 28/10/2026. **Rama:** `mejoras/cp-variable`.
**Commit publicado de partida:** `b9bc18f61dc601241edaa1c9c9d6bf6ef8d04b19` (milestone 45 integrado). Cambios de esta entrega todavía **sin commit ni push**.

## Estado anterior

M45 proporcionaba los caudales, el empuje absoluto y las áreas y diámetros circulares equivalentes de garganta y salida; no definía un contorno ni una longitud. Los perfiles del M44.4 están expresados frente a relación de áreas, sin coordenada axial.

## Qué se ha añadido

- Campo de formulario `angulo_semidivergencia` [°], por defecto **15°** (hipótesis educativa, **no óptimo**), válido en `(0°, 90°)` sólo si se requiere geometría C-D con caudal.
- Módulo `geometria_tobera_conica.py` con `validar_semidivergencia`, `calcular_geometria_conica` y `svg_geometria_conica`.
- Para **tobera convergente-divergente** con dimensiones M45, radios, longitud del tramo divergente y esquema SVG longitudinal de escala uniforme; cotas, garganta, salida, eje y ángulo.
- Recalcula únicamente la geometría después de cada simulación; no modifica el solucionador ni altera prestaciones.
- Convergente, dimensión no disponible, campo de caudal vacío o `Ae = Ag`: sin dibujo/longitud inventados; el último es un caso límite admisible del solver sin divergente. `Ae < Ag` sí es incompatible y se rechaza.

## Nuevos conceptos de ingeniería

La geometría es una **hipótesis de cono axisimétrico** aplicada a las áreas equivalentes del M45:

\[
r_g=\sqrt{A_g/\pi},\qquad r_e=\sqrt{A_e/\pi},\qquad
L_d=\frac{r_e-r_g}{\tan(\alpha)}.
\]

La ecuación sólo proporciona **longitud del divergente**: no existe radio de entrada ni ángulo del convergente definidos para calcular su longitud. Para áreas fijas, un ángulo menor implica longitud mayor; no se atribuye mejora termodinámica al cambio de ángulo. El dibujo usa una sola escala para distancias longitudinales y radiales; puede resultar muy fino para conos extremadamente esbeltos, y las cotas siguen indicando los valores físicos.

## Nuevos conceptos de Python

Validación centralizada del ángulo; retornos `dict` con `disponible`, `motivo`, radios y longitudes [m], áreas [m²], semidivergencia [°] y residuos [m²]; `None` para magnitudes inexistentes. El SVG es texto generado a partir de los mismos radios y longitud, sin librerías adicionales ni imagen precalculada. La integración consume `resultado['dimensionamiento_tobera']` y genera `resultado['geometria_conica']` y `vista['svg_geometria_conica']` sólo si se ha introducido un caudal.

## Ejemplo reproducible

Motor C-D base `ε=1,5`, `ṁaire=20 kg/s`, `α=15°`; resultados realmente calculados: `Ag=0,0457171753 m²`, `Ae=0,0685757629 m²`, `rg=0,1206326194 m`, `re=0,1477441819 m`, **`Ld=0,1011817288 m`**. Son dimensiones condicionales al caudal supuesto, no medidas de un motor real. Para repetirlo en Python:

```python
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor
valores = {**DEFAULTS_TURBO, 'tipo_tobera':'convergente_divergente',
           'gasto_masico_aire':'20', 'angulo_semidivergencia':'15'}
r = simular_turborreactor(valores)
print(r['geometria_conica'])
```

## Verificación y limitaciones

`python3 -m unittest -q tests.test_geometria_tobera_conica_46_1` — **10/10 correctas, 0 fallos, 0 errores, 0 omisiones** (28/10/2026, entrega inicial). En el ajuste previo a 46.2 se añadieron dos pruebas y se adaptaron las expectativas de una prueba anterior; véase [46.2](46_2_perfiles_axiales_tobera.md).

Regresión científica relacionada, ejecutada desde la raíz: `python3 -m unittest -q tests.test_geometria_tobera_conica_46_1 tests.test_gasto_masico_dimensionamiento_45 tests.test_perfiles_tobera_44_4 tests.test_balance_energetico_turborreactor_44_3 tests.test_graficas_tobera_44_2 tests.test_graficas_turborreactor_44_1 tests.test_combustible_cp_variable_37 tests.test_tobera_convergente_divergente_42a tests.test_choque_normal_42c`: **116/116 correctas, 0 fallos, 0 errores, 0 omisiones**.

Compilación Python (`python3 -m compileall -q geometria_tobera_conica.py turborreactor_web.py tests/test_geometria_tobera_conica_46_1.py`), sintaxis JS existente (`node --check static/turborreactor.js`) y `git diff --check`: sin errores. **Flask y Jinja2 no están disponibles en este entorno y no se instalaron**: compilación de plantilla y verificación visual en navegador pendientes para integración en Windows. No se ejecutó la suite histórica completa.

Esto verifica ecuaciones geométricas y coherencia de la implementación, **no valida una tobera real**: no hay diseño del convergente, espesor, refrigeración, rozamiento, separación, pérdidas de divergencia ni interacción del contorno con el flujo. No se genera todavía Mach(x), p(x) ni estudio de sensibilidad: pertenecen a 46.2 y 46.3.

## Commit asociado

Pendiente de autorización. No se modifican `main`, modelos físicos ni documentos personales.
