# Milestone 47.2 — Aprendizaje: el área de admisión no basta para conocer el caudal

## El error que debemos evitar

Un motor en tierra tiene `V∞ = 0`, pero **puede aspirar aire**. La expresión `mdot = rho∞ V∞ A` describe la masa de la corriente libre que cruza una superficie perpendicular al movimiento; no determina el campo de velocidades inducido por el compresor cuando el avión está parado.

Por eso distinguimos tres cosas:

- **Captación exterior**, condicionada a una corriente libre en vuelo.
- **Sección de entrada al compresor**, donde hay un campo de velocidad local distinto de la corriente libre.
- **Caudal real del conjunto**, que debe ser simultáneamente compatible con compresor, turbina, eje y tobera.

## ¿Cómo calculamos la velocidad local con cp(T)?

Si conocemos un Mach local `M2`, podemos hallar la temperatura estática a partir de la entalpía de remanso `h(Tt2) = h(T2) + V2²/2000`, con `V2=M2·a(T2)` y `a(T2)=sqrt(gamma(T2) R T2)`. La temperatura aparece a ambos lados porque la velocidad del sonido depende de T. El código utiliza **bisección**, no una expresión con gamma constante.

Una vez conocidas T2 y la presión estática obtenida desde la entropía ideal, `rho2=1000p2/(RT2)` y `mdot2=rho2 V2 A2`.

La recuperación del difusor `pi_d` se aplica a la presión **total** antes de calcular la sección. No es lo mismo que multiplicar directamente la densidad ambiente por `pi_d`.

## Ejercicios guiados

1. **Motor parado en tierra:** deja Mach de vuelo cero, indica solo área de captación. El resultado es *aspiración no determinada*, nunca un caudal real cero.
2. **Aspiración condicionada:** añade área interna y un Mach local mayor que cero; el modelo ya puede calcular un gasto compatible con esa sección.
3. **Avión en vuelo:** fija Mach 0,5 y un caudal conocido; el programa puede calcular el área exterior requerida. Si no conocemos el caudal, el área exterior por sí sola no cierra el problema del motor.
4. **Dos caudales que no coinciden:** introduce a la vez el caudal del motor y área+Mach local incompatibles. Obtendrás un diagnóstico de continuidad, no una corrección ficticia.

## Python, hipótesis y futuro

`estado_seccion_compresor` calcula el estado estático condicionado a Mach local. `evaluar_admision` compara los flujos en áreas distintas y devuelve un diccionario con valores `None` cuando faltan condiciones. El formulario solo ejecuta este estudio si se han rellenado sus campos opcionales, de modo que las simulaciones históricas no cambian.

**Esto no valida una admisión real.** No hay geometría de conducto ni mapa de compresor ni modelo de captura o derrame; las áreas y Mach locales son entradas educativas. Para predecir un punto operativo se deberán vincular con mapas y balances del resto del motor.
