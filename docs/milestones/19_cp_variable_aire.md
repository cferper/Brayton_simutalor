# Fase 2A — Propiedades del aire ideal con calor específico variable

## Estado anterior

Base remota verificada el **23/10/2026**: `96449ca4960778ec7de6b910330b148dc5ece4d3`, rama `mejoras/verificacion-numerica` del repositorio `cferper/Brayton_simutalor`. No existía un módulo específico de propiedades termodinámicas variables. El solucionador Brayton y sus estudios usan `cp` y `gamma` constantes. El repositorio de conservación `Brayton_simutalor-gas_perfecto` no participa en esta fase.

## Qué se ha añadido

- `propiedades_aire.py`: API independiente `cp(T)`, `h(T)`, `s0(T)`, `s(T,p)`, `gamma(T)` y `T_desde_h(h)`; sin dependencias externas.
- `tests/test_propiedades_aire.py`: referencias numéricas, derivadas, cuadraturas, monotonía, empalmes Shomate, inversión, presión y validación de tipos/límites.
- Documentación científica y didáctica: este milestone, [aprendizaje independiente](19_cp_variable_aire_APRENDIZAJE.md) y [§4.57 del manual](../../CODE_WALKTHROUGH.md).

**Delimitación:** `main.py`, `viabilidad.py`, `segunda_ley.py`, optimizadores, sensibilidad, mapa, Flask, HTML y CSS no importan ni utilizan este módulo. No se crean informes ni se modifican las nueve entradas actuales. La integración física pertenece a **Fase 2B**, no implementada aquí.

## Nuevos conceptos de ingeniería

Se modela aire seco como mezcla ideal **de composición molar fija**: 78 % N₂, 21 % O₂ y 1 % Ar. La masa molar media resultante es `0,02896968 kg/mol` y `R=287,005677 J/(kg·K)`. Rango cerrado 200–2000 K; referencia `Tref=298,15 K` y `pref=100 kPa=1 bar`.

N₂ y O₂ usan las correlaciones Shomate del NIST Chemistry WebBook: N₂ cambia de coeficientes a **500 K**, O₂ a **700 K**. Se han transcrito los ocho coeficientes de ambos tramos (A–H) a `propiedades_aire.py`. Para Ar se utiliza el valor ideal monoatómico `cp,molar=(5/2)Ru≈20,78616 J/(mol·K)`, cuya extrapolación a 200 K responde al modelo ideal elegido, no a un ajuste experimental en ese extremo. Las fuentes primarias son:

- [NIST: N₂, 100–500 y 500–2000 K](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Mask=1).
- [NIST: O₂, 100–700 y 700–2000 K](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7782447&Mask=1).
- [NIST: Ar, masa molar y contraste del cp monoatómico](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7440371&Mask=1).

Para `t=T/1000` la expresión de NIST es:

```text
cp,m(T) = A + B·t + C·t² + D·t³ + E/t²       [J/(mol K)]
```

Las primitivas analíticas Shomate permiten evaluar `h(T)` y `s0(T)` como diferencias desde `Tref`. Para evitar los minúsculos saltos originados por dos ajustes independientes, a cada temperatura superior a un cambio de tramo se suma la integral del tramo bajo hasta la frontera y la del tramo alto desde la frontera. **La entalpía y la entropía térmica son continuas**; el `cp(T)` puede presentar una pequeña diferencia lateral al cambiar coeficientes. La construcción respeta `dh/dT=cp/1000`, `ds0/dT=cp/(1000 T)` fuera de las fronteras y `s(T,p)=s0(T)−(R/1000)ln(p/pref)`.

Las salidas másicas usan `cp` en J/(kg·K), `h` en kJ/kg, `s0` y `s` en kJ/(kg·K), `gamma` adimensional. Son **magnitudes relativas**: `h(Tref)=0`, `s0(Tref)=0`; no se publican entalpías de formación ni entropías absolutas de mezcla.

## Nuevos conceptos de Python

- Diccionario de coeficientes por especie/tramo y tuplas de fracción y masa molar; suma de magnitudes molares antes de convertir a másicas.
- Funciones auxiliares privadas (`_coeficientes`, `_incremento_molar`, `_cp_shomate`, `_h_shomate`, `_s_shomate`) para separar datos, polinomios e integración.
- `numbers.Real` con exclusión explícita de `bool` y `math.isfinite`: no aceptar `True` como `1 K`, `NaN`, infinitos ni datos textuales.
- Bisección de una función monótona con intervalo **acotado** por 200 y 2000 K; criterio de anchura `1e−10 K`, máximo 80 iteraciones, rechazo explícito de entalpías fuera del rango.
- Para presiones positivas extremas, `log(p)−log(pref)` evita el subdesbordamiento que puede causar `log(p/pref)`.
- `unittest` con `subTest`, diferencias centradas, cuadratura trapezoidal y valores de referencia independientes del módulo.

## Qué hemos aprendido

1. Un modelo de **gas ideal** puede tener calor específico dependiente de temperatura; `cp` constante es una hipótesis adicional, no la definición de gas ideal.
2. Para mezclar en base molar hay que ponderar primero propiedades molares y dividir después por la masa molar media.
3. Las integrales deben compartir la referencia y continuidad aunque las correlaciones publicadas cambien de tramo.
4. Si `cp(T)>0`, `h(T)` es estrictamente creciente y se puede invertir sin un algoritmo general de raíces ni SciPy.
5. Coincidencia con fórmulas NIST y pruebas matemáticas **no** constituye validación experimental de prestaciones de un motor.

**Resultados numéricos representativos:** a 298,15 K, `cp≈1004,318 J/(kg·K)` y `gamma≈1,400113`; a 1000 K, `cp≈1140,117 J/(kg·K)`, `h≈747,485 kJ/kg`, `s0≈1,271674 kJ/(kg·K)` y `gamma≈1,336422`. Estos valores pertenecen sólo al módulo nuevo y no cambian los resultados Brayton previos.

### Verificación ejecutada — 23/10/2026

Los **17 métodos específicos de `tests/test_propiedades_aire.py` han resultado correctos**, incluida la comparación exacta de A–H con las tablas originales NIST. Una comprobación directa adicional de `viabilidad.evaluar_punto` conservó `w_n,ideal=505,619018249` y `w_n,noideal=369,476301045 kJ/kg` para la referencia conocida, sin importar el nuevo módulo. Se intentó una única ejecución de `unittest discover` de toda la suite: **no fue evaluable** en este entorno, que dispone de NumPy y Matplotlib pero no de `Flask`/`jinja2`. El descubrimiento contabilizó 88 métodos y **19 errores de importación de módulos históricos**, bloqueados por la dependencia de presentación ausente; no se registraron fallos de aserción. Conforme a las restricciones, no se instalaron dependencias. No se declara superada esa regresión ni se suman recuentos históricos de V.1–V.5.

## Limitaciones que siguen existiendo

- Composición fija sin humedad, combustible, disociación, ionización ni variaciones de mezcla; gas ideal con presión sólo en el término entrópico.
- Las correlaciones ajustadas de N₂/O₂ no dan `cp` rigurosamente continua entre tramos; el módulo garantiza continuidad de **h** y **s0**, no suavidad de sus derivadas.
- No se extrapola a temperaturas menores de 200 K ni mayores de 2000 K.
- No se validan datos de motores, eficiencias de componentes, combustión ni variaciones reales de composición. La posible incertidumbre de correlaciones no se cuantifica.
- La Fase 2B deberá usar diferencias de `h` en trabajos y calor y resolver isentrópicas mediante `s(T,p)`; no basta sustituir la constante `cp` en las fórmulas existentes. No se ha iniciado esa integración.

## Commit asociado

**Pendiente de publicación** al preparar este documento. Base verificada `96449ca4960778ec7de6b910330b148dc5ece4d3`; rama de la fase `mejoras/cp-variable`. El hash de su propio commit no puede incorporarse en el mismo commit antes de generarlo.
