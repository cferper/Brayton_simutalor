# Milestone 46.3 — Sensibilidad geométrica al ángulo del divergente

**28/10/2026.** Rama `mejoras/cp-variable`; commit base publicado del M45: `b9bc18f61dc601241edaa1c9c9d6bf6ef8d04b19`. Entregas 46.1–46.3 sin commit ni push.

## Estado anterior

46.1 calculaba la longitud del divergente cónico con áreas M45 y un ángulo escogido. 46.2 proyectaba estados físicos M44.4 sobre `x` [m]. Aún no existía un estudio de diferentes ángulos a áreas constantes; los SVG axiales carecían de graduaciones numéricas explícitas, y las tolerancias de los dos filtros de relaciones de áreas no coincidían.

## Qué se ha añadido y corregido

- `estudio_geometrico_tobera.py`: barrido didáctico fijo de **5°, 10°, 15°, 20°, 25°** y ángulo elegido en formulario si es diferente. Tabla con `α`, `Ld`, ambos diámetros y `Ae/Ag`; las áreas se mantienen **fijas**.
- Gráfica SVG graduada de **longitud frente a α** con ángulo seleccionado marcado en rojo, y comparación de **10°, 15° y 20°** en una escala longitudinal/radial común.
- En los perfiles axiales 46.2, marcas numéricas legibles de ambos ejes, referencia `M=1` o `p∞` [kPa], garganta, salida, unidades y choque normal. Se conservan polilíneas separadas para las ramas de choque.
- `TOLERANCIA_RELATIVA_AREAS = 2e-6` compartida por la comprobación global de perfil/geometría y la conversión puntual. Una diferencia de redondeo ya aceptada por el filtro global puede asignarse al extremo de salida sin recalcular `Mach` ni `p`. Una diferencia física mayor sigue dando `ValueError`.
- Misma estructura de seis apartados: la nueva comparación se inserta en Visualizaciones, sin rediseñar la página ni ampliar el modelo termodinámico.

## Ecuaciones y resultados

Con radios calculados en 46.1, `Δr=re−rg>0` fijo:

\[
L_d(\alpha)=\frac{\Delta r}{\tan\alpha},\qquad
\frac{dL_d}{d\alpha}=-\frac{\Delta r}{\sin^2\alpha}<0
\quad (\alpha\ \text{en radianes}).
\]

Con áreas constantes, diámetros y `Ae/Ag` no cambian con α. **No** se deduce cambio de empuje ni eficiencia del motor por variar el ángulo: el solucionador base recibe los mismos parámetros termodinámicos.

### Ejemplo reproducible

Punto base C-D `Ae/Ag=1,5`, gasto de aire supuesto `20 kg/s`: `rg≈0,1206326194 m`, `re≈0,1477441819 m` y `Δr≈0,0271115625 m`.

```python
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor, preparar_vista_turborreactor
v = {**DEFAULTS_TURBO, 'tipo_tobera':'convergente_divergente',
     'gasto_masico_aire':'20', 'angulo_semidivergencia':'15'}
vista = preparar_vista_turborreactor(simular_turborreactor(v))
for fila in vista['estudio_geometrico']['filas']:
    print(fila['angulo_grados'], fila['longitud_divergente'])
```

## Optimización y limitaciones

Se puede minimizar `Ld` **sólo bajo restricciones geométricas explícitas**, como `α∈[5°,25°]` para un ejemplo de clase: la mínima longitud en ese intervalo corresponde a **25°**, simplemente porque la función decrece. Esto no convierte 25° en un ángulo recomendado, óptimo aerodinámico ni óptimo estructural.

No se han introducido modelos empíricos de pérdidas por divergencia, rozamiento, separación, comportamiento externo, masa o cargas térmicas. Tampoco se define el convergente. Para optimizar empuje real o peso, harían falta otros modelos, contraste con datos independientes y restricciones de diseño justificadas.

## Verificación

Pruebas específicas `tests/test_estudio_geometrico_tobera_46_3.py`: longitudes analíticas, monotonicidad, áreas/diámetros constantes, gráfico y selección, tres conos, indisponibilidad, invariancia de resultados termodinámicos y compatibilidad 46.1/46.2. **8/8 correctas**.

Pruebas añadidas en `tests/test_perfiles_axiales_tobera_46_2.py`: discrepancia redondeada tolerada y ejes graduados/referencias. **10/10** en esa batería. La regresión científica relacionada se registra en el documento de cierre M46, separada de la regresión completa Windows.

## Commit asociado

Pendiente de autorización. Sin modificaciones en `main`, solucionadores termodinámicos ni documentos personales.
