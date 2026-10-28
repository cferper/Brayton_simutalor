# Cierre técnico provisional — Milestone 46: geometría de la tobera

**Fecha:** 28/10/2026. **Rama:** `mejoras/cp-variable`. **HEAD de partida publicado:** `b9bc18f61dc601241edaa1c9c9d6bf6ef8d04b19`. **Sin commit ni push** de las entregas 46.1–46.3. Se presenta para integración posterior en Windows, todavía no como cierre integral de aplicación.

## 1. Tres entregas y relación con módulos anteriores

| Entrega | Capacidad nueva | Datos físicos reutilizados |
|---|---|---|
| 46.1 | Divergente cónico: ángulo, radios, longitud y esquema longitudinal | Áreas/diámetros equivalentes del M45 |
| 46.2 | Mach y presión frente a `x` [m], garganta/salida y posición de choque | Estados cuasi-1D `cp(T)` del M44.4 |
| 46.3 | Tabla y gráfica `Ld(α)` y tres conos a escala común | Geometría de 46.1 con áreas constantes |

Se corrigió el uso condicional del ángulo (no bloquea convergente ni modo sin caudal), el límite `Ae/Ag=1` (sin divergente, sin fallo del motor), las graduaciones axiales y la tolerancia compartida de áreas. Todos los solucionadores termodinámicos permanecen intactos.

## 2. Ecuaciones e hipótesis

Se supone **cono axisimétrico del tramo divergente**, con secciones circulares equivalentes:

\[
r_g=\sqrt{A_g/\pi},\quad r_e=\sqrt{A_e/\pi},\quad
L_d=\frac{r_e-r_g}{\tan\alpha}.
\]

La geometría asigna a cualquier estado M44.4 conocido en `a=A/Ag`:

\[
x(a)=\frac{\sqrt{A_g a/\pi}-r_g}{\tan\alpha},\quad x(1)=0,\ x(A_e/A_g)=L_d.
\]

El choque normal, si existe, tiene **dos estados distintos con una única posición** calculada por su relación `Achoque/Ag`, nunca interpolados entre sí. Para áreas constantes, `Ld(α)` es estrictamente decreciente; cambiar únicamente α no cambia empuje, Mach ni presión del modelo termodinámico actual.

## 3. Caso numérico reproducible

Parámetros del ejemplo M45: ambiente directo `288,15 K`, `100 kPa`, vuelo estático `M0=0`, compresor `rp=10`, `ηc=0,85`, `T3=1600 K`, pérdida cámara `4 %`, `ηt=0,90`, `ηm=0,98`, `ηn=0,95`, combustión equivalente `ηb=0,99`, `PCI=43000 kJ/kg`, C-D `Ae/Ag=1,5`, gasto de aire **supuesto** `20 kg/s`.

Se obtienen `Ag=0,0457171753 m²`, `Ae=0,0685757629 m²`, `rg=0,1206326194 m`, `re=0,1477441819 m`.

| α [°] | Ld [m] | Dg [m] | De [m] | Ae/Ag |
|---:|---:|---:|---:|---:|
| 5 | 0,30988658 | 0,24126524 | 0,29548836 | 1,5 |
| 10 | 0,15375731 | 0,24126524 | 0,29548836 | 1,5 |
| **15 (seleccionado)** | **0,10118173** | 0,24126524 | 0,29548836 | 1,5 |
| 20 | 0,07448841 | 0,24126524 | 0,29548836 | 1,5 |
| 25 | 0,05814093 | 0,24126524 | 0,29548836 | 1,5 |

Comando reproducible desde la raíz:

```python
from turborreactor_web import DEFAULTS_TURBO, simular_turborreactor, preparar_vista_turborreactor
v = {**DEFAULTS_TURBO, 'tipo_tobera':'convergente_divergente',
     'gasto_masico_aire':'20', 'angulo_semidivergencia':'15'}
r = simular_turborreactor(v)
print([(f['angulo_grados'], f['longitud_divergente'])
       for f in preparar_vista_turborreactor(r)['estudio_geometrico']['filas']])
```

## 4. Pruebas realmente ejecutadas en el entorno de desarrollo

**28/10/2026:**

- 46.1: **12 pruebas** (10 iniciales y 2 adicionales de compatibilidad).
- 46.2: **10 pruebas** (8 iniciales y 2 adicionales de tolerancias y ejes).
- 46.3: **8 pruebas** nuevas.
- Regresión científica relacionada M37/M42/M44/M45/M46, una ejecución de cierre: **136 métodos, 136 correctos, 0 fallos, 0 errores, 0 omisiones**.

```bash
python3 -m unittest -q tests.test_geometria_tobera_conica_46_1 \
  tests.test_perfiles_axiales_tobera_46_2 \
  tests.test_estudio_geometrico_tobera_46_3 \
  tests.test_gasto_masico_dimensionamiento_45 \
  tests.test_perfiles_tobera_44_4 \
  tests.test_balance_energetico_turborreactor_44_3 \
  tests.test_graficas_tobera_44_2 \
  tests.test_graficas_turborreactor_44_1 \
  tests.test_combustible_cp_variable_37 \
  tests.test_tobera_convergente_divergente_42a \
  tests.test_choque_normal_42c
```

Compilación Python con `python3 -m compileall -q` sobre los cuatro archivos Python de producción/interfaz afectados y los tres archivos nuevos de pruebas: **correcta**. `node --check static/turborreactor.js`: **correcto** (sin cambio JS). `git diff --check`: **sin incidencias**. **No se ha realizado regresión histórica completa ni inspección visual web** en este entorno, que carece de Flask/Jinja2. Son tareas pendientes de Windows; no se inventan resultados.

## 5. Límites físicos y próximos trabajos

- Sólo se dimensiona el **divergente**: faltan condiciones geométricas de entrada para el convergente, espesor, refrigeración, masa y resistencia estructural.
- No se han introducido modelos de pérdidas por divergencia angular, fricción, separación, choques oblicuos ni estela externa.
- La simulación de flujo es cuasiunidimensional y no determina de forma autónoma el caudal admitido por un motor real.
- **Optimización geométrica condicionada:** en un intervalo angular fijado a priori, el ángulo máximo da la longitud mínima. Sin restricciones aerodinámicas/estructurales y sin verificación con datos independientes, **no** hay un ángulo óptimo de empuje ni una validación experimental.
- Integrar el ZIP acumulado en Windows, instalar sólo las dependencias ya previstas del proyecto cuando corresponda, ejecutar regresión completa e inspección visual de los nuevos paneles en pantalla normal y estrecha. Las mejoras de presentación general pertenecen al milestone 47 y no se han iniciado.

## 6. Archivos nuevos y modificados

**Modificados:** `turborreactor_web.py`, `templates/turborreactor.html`, `CODE_WALKTHROUGH.md`.

**Creados:** `geometria_tobera_conica.py`, `perfil_axial_tobera_conica.py`, `estudio_geometrico_tobera.py`, tres archivos `tests/test_*_46_*.py`, seis documentos técnico/educativos de las entregas, y este documento de cierre.

No se han alterado `main`, los solucionadores termodinámicos ni `docs/PLAN_MEJORAS_BRAYTON_SIMULATOR.md`. No hay commit ni push.
