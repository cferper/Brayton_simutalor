# Aprendizaje — Milestone 42.B

## Qué cambia para el estudiante

Una tobera convergente alcanza Mach 1 en la salida cuando se bloquea. Una
convergente-divergente dispone además de garganta y sección divergente. Si se
bloquea en garganta, **no significa** que la salida sea siempre supersónica:
pueden aparecer un tramo subsónico, una expansión supersónica sin choque o un
choque que el modelo actual todavía no sabe situar.

## Pasos para aprender con la web

1. Simula el caso estándar con tobera convergente y registra empuje neto y TSFC.
2. Cambia a C-D, fija `Ae/Ag = 1.5` y observa garganta, escape y presión.
3. Compara la presión exterior con la presión de adaptación de esa geometría.
4. Compara `Ae/Ag = 1.5` con el área que adaptaría la presión exterior actual.
5. Prueba una geometría más abierta. Si el programa anuncia choque no resuelto,
   comprueba que conserva Mach de garganta pero **no inventa** empuje ni TSFC.
6. Ejecuta un barrido OFAT o mapa: el área permanece fija y los casos sin
   salida conocida se marcan como no disponibles, no como cero.

## Interpretación rigurosa

El parámetro `eta_n` anterior sólo aplica a toberas convergentes. La C-D de
42.A es adiabática e isentrópica con `cp(T)` variable. Por coherencia de la API,
el dato `eta_n` sigue siendo obligatorio y se valida en `(0,1]`, pero
**no se usa para la tobera C-D**; su eficiencia efectiva ideal es uno. Esto
permite conservar los barridos antiguos con `eta_n=.95` sin hacer creer que
se ha implementado una tobera C-D con pérdidas. El modelo no supone eficiencia
real de tobera, pérdidas viscosas o resolución de choques internos. En el
formulario HTML el campo sigue **visible y editable** en C-D: ocultarlo sería
confuso, porque el servidor rechaza valores inválidos incluso en ese modo.
Cambiar el selector no modifica el valor que introdujo el usuario. Las
ecuaciones se **verifican** frente a balances y límites, pero no se han
**validado** prestaciones frente a datos experimentales.

## Cinco conceptos físicos distintos

1. **Bloqueo sónico en garganta:** en la sección mínima C-D, `Mg=1`. Limita
   el gasto por unidad de área crítica, pero no determina el Mach de escape.
2. **Expansión supersónica:** con la contrapresión adecuada, el flujo se
   acelera en el divergente y alcanza `Me>1`. El cociente `Ae/Ag` fija el
   estado de salida isentrópico para unas condiciones totales conocidas.
3. **Adaptación:** `pe=p∞`; desaparece el término de empuje de presión,
   aunque continúa existiendo el término de momento. La presión que adapta
   una geometría no tiene por qué ser la presión exterior real.
4. **Choque no resuelto:** una geometría con garganta bloqueada puede exigir
   una onda de choque en el divergente. Saber `Mg=1` no proporciona `Me`,
   `pe`, el empuje ni el TSFC. En mapas se muestra `tobera_no_resuelta`,
   **distinto de** `sin_expansion`.
5. **Dominio de propiedades:** la correlación de aire equivalente sólo cubre
   temperaturas entre 200 y 2000 K. Una expansión que requiera menos de
   200 K no es calculable por este software, aunque pueda ser físicamente
   posible en condiciones reales.

## Por qué importa encerrar una raíz antes de bisecar

Queremos resolver la ecuación `F(p)=Ae/Ag(p)-epsilon=0`. En la rama
supersónica, `F` disminuye cuando aumenta `p`: una presión suficientemente
baja ofrece `F>=0` y cerca de la presión crítica sónica tenemos `F<0`
si `epsilon>1`. Una bisección correcta debe **comprobar ambos lados** antes
de reducir el intervalo. Cada iteración conserva la raíz dentro: el punto
medio sustituye sólo al extremo que comparte el mismo signo.

La versión inicial de 42.B tomaba el primer estado supersónico válido como
extremo superior sin demostrar que `F<0`. Para `Tt=1200 K`, `pt=500 kPa`
y `epsilon=1.001`, entregaba aproximadamente `250.35 kPa` en vez de
`259.119611 kPa`. Ahora, al reintroducir `259.119611 kPa` en la función
independiente de áreas de 42.A, se recupera aproximadamente `1.0010000001`.
El caso `epsilon=1` representa la salida sónica límite y se trata
directamente mediante el estado crítico; valores excesivamente grandes
dan un error controlado por límite del aire.

**PYTHON.** `_presion_adaptacion_cd(Tt,pt,epsilon)` comprueba tipos, finitud
y límites, obtiene la presión crítica mediante `_sonico()` y delega la
relación de áreas a `relacion_areas_adaptada()`. Un bucle `for` conserva
un intervalo de raíz y `try/except ValueError` evita aceptar un valor
no supersónico como salida. Devuelve `float` [kPa] o lanza un error físico
controlado. La función `_adaptacion_cd(resultado)` la llama para preparar
la visualización Flask y muestra el motivo cuando no existe solución.

Este contraste de ida y vuelta es **verificación numérica del código**.
**Validación científica** requeriría medir o contrastar la tobera frente a
datos experimentales de ensayos o referencias independientes de fidelidad
adecuada: todavía no se ha realizado.

## Comprobaciones del cierre de esta corrección

La inversión de área se contrastó con casos `Ae/Ag=1`, `1.0001`,
`1.001`, `1.01`, `1.5` y otros mayores, junto con el solucionador de 42.A,
sin modificarlo. En este entorno la suite final ejecutó **592 pruebas**:
**591 correctas, 1 omisión opcional y 0 fallidas**. Los **16 tests** de 42.B
incluyen dos comprobaciones del campo `eta_n` visible y del mensaje de error
corregible tras enviar un valor inválido. Estos resultados prueban
consistencia del programa y preservación de regresiones; no son evidencia
experimental de prestaciones del motor.
