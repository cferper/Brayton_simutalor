# Aprendizaje — Milestone 45: del empuje específico al tamaño físico

## 1. Por qué introducimos el caudal

En el milestone 44 conocíamos la velocidad de salida, el dosado de combustible y el **empuje específico** por kilogramo de aire que entra cada segundo. Eso permite comparar configuraciones sin elegir tamaño. Para convertirlo en fuerza necesitamos **cuánto aire pasa por el motor cada segundo**.

- **Masa** [kg]: cantidad de materia.
- **Gasto másico** `ṁ` [kg/s]: masa que atraviesa una sección durante un segundo.
- **Empuje específico** `Fs` [N/(kg/s)]: fuerza que obtendría el motor por unidad de gasto de aire.
- **Empuje absoluto** `F` [N]: fuerza para un caudal de aire elegido.

Se deja el campo `gasto_masico_aire` **vacío por defecto**. Así los resultados antiguos siguen describiendo un punto de funcionamiento sin asignar un tamaño arbitrario. El valor **20 kg/s** solo es un ejemplo educativo; no implica que el motor modelado pueda admitir realmente ese caudal.

## 2. 45.1 — Aire, combustible y gases no son el mismo caudal

El solucionador ya conoce `f=ṁf/ṁa`. Si entran 20 kg/s de aire y `f≈0,0280282`, se consumen `f·20≈0,56056 kg/s` de combustible y salen `(1+f)·20≈20,56056 kg/s` de gases equivalentes. En una hora se consumen `3600·0,56056≈2018,03 kg`.

No se ha cambiado el modelo de combustión: sigue siendo un aporte energético equivalente con propiedades de aire `cp(T)` y no una simulación de especies químicas.

## 3. 45.2 — De velocidad a newtons

La primera identidad es **F=ṁa·Fs**. Como contraste se calcula:

\[
F=\underbrace{\dot m_eV_e}_{\text{momento de salida}}
 -\underbrace{\dot m_aV_0}_{\text{entrada}}
 +\underbrace{(p_e-p_\infty)A_e}_{\text{presión}}.
\]

Recuerda que una presión en kPa multiplicada por m² da **kN**, no N: la implementación multiplica la diferencia de presiones por 1000. El término de presión puede ser negativo en una salida sobreexpandida. El neto también puede ser negativo; truncarlo a cero alteraría la física y ocultaría el caso desfavorable.

Para `F>0`, `TSFC=3600ṁf/F` [kg/(N·h)] reproduce el valor específico `3600f/Fs`. Si la fuerza es nula o negativa, el TSFC convencional deja de ser útil y no se presenta.

## 4. 45.3 — Cómo se obtiene el área de una sección

Con densidad estática `ρ` [kg/m³] y velocidad `V` [m/s], el caudal que pasa por una sección de área `A` [m²] es `ṁ=ρVA`. Luego `A=ṁ/(ρV)`. Para la salida se utiliza el gasto **de gases**, no el de aire.

En C-D, el solucionador físico proporciona `Gg=ρgVg` para la garganta. Así se calcula `Ag=ṁe/Gg`. Si la garganta está bloqueada, Mach es aproximadamente 1; si no lo está, se conserva **su verdadero Mach subsónico**. En una tobera convergente, la garganta geométrica es la sección final incluso cuando no está bloqueada.

En choque normal interno o de salida, se emplean las **condiciones de salida correctas del solver**. No se utiliza por error el estado anterior al choque en el plano de salida. Los cierres de masa y `Ae/Ag=ε` comprueban la coherencia.

Un diámetro `D=√(4A/π)` describe un **círculo con esa área**, no una sección transversal real obligatoriamente circular. Y conocer Ag y Ae no nos dice la longitud ni el ángulo de divergencia.

## 5. Programación transversal: separar ciencia, escalado y presentación

El código nuevo está en `dimensionamiento_turborreactor.py`. Así los módulos de física M35–44 no necesitan conocer un gasto absoluto.

### Función de validación

`validar_gasto_masico_aire(gasto_masico_aire)` recibe un número real, devuelve `float` [kg/s] y lanza `ValueError` ante cero, negativo, no finito, texto o booleano. Comprueba `isfinite`; en Python `bool` hereda de `int`, por eso debe rechazarse explícitamente.

### Escalado de magnitudes

`calcular_prestaciones_absolutas(resultado, gasto_masico_aire)` recibe el dict científico que ya ha resuelto combustión y tobera; accede con `resultado['combustor']['f']` y `resultado['prestaciones']`, multiplica por el caudal y devuelve otro **dict** de consumos, fuerzas firmadas, TSFC y residuos. No modifica ni vuelve a ejecutar `resultado`. Los campos de empuje son `None` si falta expansión física.

### Dimensionamiento

`dimensionar_tobera(resultado, gasto_masico_aire, *, absolutos=None)` calcula áreas, diámetros y residuos. El argumento opcional después de `*` debe pasarse **por nombre**: `dimensionar_tobera(r,20,absolutos=a)`. Es útil para reutilizar `a` y evitar trabajo repetido. Retorna `disponible=False` con motivo claro cuando no puede calcular dimensiones; no convierte `None` en cero.

La función auxiliar `_finito(valor)` comprueba la calidad de los valores que vienen del solucionador. Un guion bajo inicial indica que es de uso interno del módulo.

### La web

`simular_turborreactor(valores)` llama una sola vez al solucionador. Si `valores['gasto_masico_aire']` está vacío, **no añade campos nuevos** al resultado: compatibilidad total con el uso previo. Si hay un número válido, añade `prestaciones_absolutas` y `dimensionamiento_tobera`. `svg_descomposicion_empuje(resultado, absoluto=True)` usa las mismas barras del 44.1 pero cambia valores y unidades a newtons; `False` conserva el gráfico original. El formulario muestra las áreas y consumos en «Resultados», sin cambiar los seis apartados ni los estudios de sensibilidad y mapas.

## 6. Experimentos que puedes realizar

1. Deja vacío el caudal y comprueba que el simulador funciona como antes.
2. Escribe **20 kg/s** en el caso estático: el empuje C-D del ejemplo es aproximadamente **19,60 kN** (con `Ae/Ag=1,5`).
3. Cambia a **40 kg/s** sin modificar la termodinámica: duplicas empuje, consumo y áreas; los diámetros solo se multiplican por `√2`.
4. Compara convergente bloqueada con no bloqueada: en ambas la garganta física es la salida, pero Mach cambia.
5. Prueba una configuración con empuje específico negativo: seguirá mostrando empuje absoluto negativo y no mostrará un TSFC convencional.
6. Prueba `0`, `-5`, `NaN` y un campo vacío: los primeros son inválidos y el último es el modo específico original.

## 7. Verificación y límites

Las **19 pruebas del milestone 45** cubren consumo, fuerza, cierres dimensionales, regímenes de tobera, choque interno/salida, escalado, entradas inválidas, compatibilidad con resultados específicos, SVG y casos sin expansión. La regresión científica de 45 y 44 junto a hitos anteriores termina con **159 correctas de 160**, una omisión opcional de Cantera, ningún fallo ni error.

En ese entorno de desarrollo quedaba pendiente la integración Flask/Jinja. La revisión Windows descrita a continuación sí utiliza las dependencias existentes; no repite aquella batería científica. **Verificar igualdades internas no equivale a validar el motor con ensayos experimentales.**

## 8. Lo que no sabemos todavía

Las condiciones termodinámicas actuales **no fijan el caudal real que puede tragar un compresor** sin mapas y restricciones adicionales. El código dimensiona el motor que correspondería a un caudal impuesto. Tampoco calcula área de captación del aire a partir de la velocidad de vuelo: eso fallaría en estático. El perfil geométrico completo, longitud y ángulos quedan fuera de este milestone.


## 9. Revisión Windows y numeración unificada — 28/10/2026

45.1 corresponde a **caudales**, 45.2 a **empuje absoluto** y 45.3 a **áreas y
diámetros**. Interfaz, pruebas y documentación acompañan a las tres entregas;
no constituyen una 45.3 separada. Se conservan las explicaciones y ejemplos.

La base local comprobada es `52331435f1b55f01b64153517048c60809de5865`, rama
`mejoras/cp-variable`, sin cambios versionados y con dos archivos personales
que se preservan. Se integra el ZIP de siete archivos. El T–s de M44 y los
solucionadores físicos anteriores permanecen iguales; no se crea commit.

**PYTHON.** En la tabla y el SVG se usa `valor or 0.0` para representar un cero
firmado como cero. `or` elige el segundo operando cuando el primero es cero;
un valor negativo no nulo se conserva. Es formato, no una alteración de las
fuerzas ni de las ecuaciones. `_finito(valor)` devuelve `bool`; por ejemplo,
`_finito(20.0)` es verdadero y `_finito(True)` es falso. La usan el escalado
y el dimensionamiento. Las llamadas y errores completos están en el manual §4.85.

**INGENIERÍA / PRÁCTICA.** El campo vacío conserva el funcionamiento específico.
Con 20 y 40 kg/s se comprueba que caudales, fuerzas y áreas duplican su valor,
pero D40/D20=√2 porque el diámetro procede de la raíz del área. Los estados
T,p, Mach, dosado y TSFC se conservan. La C-D del ejemplo anterior es distinta
de la convergente por defecto: no mezclar sus valores de fuerza o áreas.

19/19 pruebas específicas y 74/74 web correctas; después de corregir el formato
se repiten juntas: 93/93, sin fallos, errores ni omisiones. Se comprueban campo
vacío, 20/40 y entradas inválidas en navegador, tarjetas y unidades en escritorio
y pantalla estrecha. No se ejecuta toda la regresión científica ni se instalan
paquetes. Los resultados previos de 160 métodos siguen siendo antecedentes,
no pruebas ejecutadas otra vez aquí. La verificación interna no sustituye una
validación experimental ni predice el caudal real admitido por un compresor.
