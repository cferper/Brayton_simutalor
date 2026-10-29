# Aprendizaje 47.4 — ¿Cómo encuentra el motor su caudal?

## Ingeniería: tres piezas que deben encajar

En el modo A de caudal impuesto damos los kg/s y calculamos áreas. En B damos una garganta y un remanso **ya conocido** y deducimos los kg/s que atravesarían esa tobera. En C ya no se permite elegir a voluntad el gasto, la relación de compresión ni la velocidad del rotor: compresor, cámara, turbina y tobera deben ponerse de acuerdo.

Para concretarlo, imagina girar un mando de velocidad `N`, ajustar un punto de trabajo del compresor (`Rline`) y elegir el salto de presión de la turbina. Solo son válidas las combinaciones en que simultáneamente:

1. La turbina proporciona al eje la potencia que absorbe el compresor (teniendo en cuenta `ηm`).
2. El gasto de gases del mapa de turbina coincide con aire más combustible: `ṁg=ṁa(1+f)`.
3. La garganta de área fija puede transportar exactamente ese gasto en las condiciones de remanso calculadas.

El programa emplea **un mismo giro mecánico** `N` para ambas turbomáquinas. No obstante, su *giro corregido* no coincide: `Ncorr=N/√(Tt/Tref)`, y las temperaturas de entrada de compresor y turbina son distintas. También `ṁcorr=ṁ·√(Tt/Tref)/(pt/pref)`.

## Python: resolver tres incógnitas sin inventar respuestas

La función `resolver_motor_acoplado` evalúa primero un candidato con `_resultado_punto` y devuelve tres residuos. Newton utiliza pequeñas perturbaciones de cada incógnita para aproximar una matriz de derivadas; resuelve un sistema lineal 3×3 y acorta el paso si no reduce la norma. No se limita a comprobar que se agotaron las iteraciones: exige residuos pequeños **y** verifica las unidades físicas de las masas y la potencia. Si el mapa no contiene la consulta, no extrapola: devuelve una causa de indisponibilidad.

Las tres modalidades comparten modelos termodinámicos, pero no confunden sus entradas. La interfaz oculta parámetros derivados en C y muestra las RPM, la línea de mapa y los cierres físicos. Las pruebas también ejercitan el modo A y el B para detectar regresiones.

## Ejemplo que puedes repetir

```python
from acoplamiento_motor_mapa_47 import punto_diseno_47, resolver_motor_acoplado
ref = punto_diseno_47()
r = resolver_motor_acoplado(referencia=ref, mach=0.4)
assert r['disponible']
print(r['caudal_aire'], r['rpm'], r['norma_residual'])
```

La referencia parte de 20 kg/s, compresión 10, Tt3=1600 K y tobera convergente bloqueada. En vuelo Mach 0,4, el resultado cambia porque el difusor cambia las condiciones de entrada y el motor debe reencontrar el equilibrio. El número producido no describe automáticamente ningún turborreactor real: hemos **verificado las ecuaciones y la implementación**, no validado un motor mediante ensayos.
