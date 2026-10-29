# Aprendizaje 47.5 — Qué hemos comprobado y qué no

## Tres preguntas diferentes

1. **¿Qué tobera necesita este caudal?** El modo A recibe `ṁa` y calcula el área.
2. **¿Qué caudal permite esta garganta?** El modo B recibe `Ag`, una presión y temperatura de remanso prescritas y una contrapresión. Hay que distinguir el flujo bloqueado del subsónico.
3. **¿A qué caudal trabajaría el motor completo según nuestros mapas?** El modo C busca simultáneamente el giro y los estados compatibles con la admisión, compresor, cámara, turbina y garganta. No se impone `ṁ` como dato: es un resultado.

## Lectura de los residuos

La relación `ṁg=ṁa+ṁf` comprueba continuidad. El balance mecánico exige que la potencia de turbina, tras las pérdidas del eje, cubra la del compresor. Las relaciones de presión y gasto de los mapas deben coincidir con las que exige la solución termodinámica y la geometría. Por eso no basta que un programa numérico escriba «terminado»: se inspeccionan **residuos numéricos** y se descartan puntos fuera de las tablas de los mapas.

En Python, un test de verificación compara funciones con identidades o referencias independientes. Un `ValueError` por mapa extrapolado es frecuentemente el comportamiento **correcto**. La regresión verifica que los modos anteriores siguen funcionando. El test no convierte el modelo en una predicción validada del motor real.

## Ejemplo para experimentar

```python
from acoplamiento_motor_mapa_47 import resolver_motor_acoplado
for mach in (0., 0.1, 0.4):
    r = resolver_motor_acoplado(mach=mach)
    print(mach, r['caudal_aire'] if r['disponible'] else r['motivo'])
```

Las diferencias no provienen de una regla universal «más Mach = más empuje». Son consecuencia del difusor, los mapas escalados, el balance del eje y el área fija escogida. La ausencia de una solución no autoriza a interpolar un supuesto resultado por conveniencia.

## Verificación frente a validación

- **Verificar:** demostrar que se implementaron bien las ecuaciones declaradas, la interpolación y el balance entre componentes.
- **Validar:** comparar con datos independientes de rendimiento y límites de **un motor real**. Esa tarea no se ha realizado.

En esta entrega se cerraron las pruebas científicas focalizadas, pero la regresión histórica completa y la inspección visual de Flask esperan al entorno Windows, como se acordó. [Informe técnico de cierre](47_5_verificacion_cierre.md).
