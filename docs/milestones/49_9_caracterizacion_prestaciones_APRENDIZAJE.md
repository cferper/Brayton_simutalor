# Aprendizaje 49.9 — Indicadores habituales y límites de un turborreactor educativo

## Punto de partida y pregunta de ingeniería — 11/11/2026

Partimos de `mejoras/cp-variable`, commit `ca128874527b0b2a2712ef642b68a3c91bd64d13` (49.8 publicado), sin cambios locales previos en esta nueva copia. Ya existían fichas por pieza, API y prestaciones. El problema nuevo: **organizar indicadores de motor sin confundir una relación calculable con una medida instrumental o una eficiencia físicamente definida**.

## Solución elegida

Se agrega un módulo puro y breve, `caracterizacion_motor_49_9.py`, con la función:

```python
def caracterizar_motor_49_9(resultado):
    ...
```

- **Entrada:** `resultado: dict`, resultado ya calculado de `simular_turborreactor`; las subestructuras esperadas son `ambiente`, `remanso`, `difusor`, `compresor`, `combustor`, `turbina`, `prestaciones`, y opcionalmente `tobera`, `prestaciones_absolutas` y `motor_acoplado`.
- **Salida:** tres listas bajo `funcionamiento`, `consumo`, `rendimientos`; cada elemento es un diccionario con `id`, `nombre`, `simbolo`, `valor`, `unidad`, `estado`, `formula`, `fuente`, `nota`.
- **Unidades:** K, kPa, rpm, kg/s, N, N/(kg/s), kg/kg, kg/(N·h), m/s, %, kJ/kg aire y kW, o adimensional (–).
- **Validación:** un cociente requiere denominador finito y positivo; no se serializan infinitos, se entrega `None` si falta el dato. La función no valida entradas del motor: eso pertenece al solucionador existente. No lanza solicitudes HTTP ni usa archivos.
- **Llamadas:** la función es invocada por `preparar_vista_turborreactor`, que ya es usado por Flask para HTML y para API; reutiliza `ratio(...)` e `item(...)`, funciones locales, sin llamar a ningún solver.
- **Ejemplo:** `caracterizar_motor_49_9(resultado)['funcionamiento'][0]['valor']` proporciona TIT [K] desde `combustor.T3`.

## Python: conceptos aplicados

Una **función local** se define dentro de otra y solo sirve allí. `ratio(num, den)` controla el dominio de una división; `item(...)` construye una estructura repetible de datos para el frontend. Los argumentos por palabra clave `derivado=False`, `nota=''`, `pendiente=False` hacen legible por qué una fila está disponible o no. Un `None` es ausencia, a diferencia de `0`, que puede ser un resultado físico legítimo (por ejemplo resistencia de captación en estático).

En `turborreactor_web.py` se incorpora el valor al diccionario `vista`; en `web_app.py`, la API expone la misma `vista['caracterizacion']` sin alterar sus claves anteriores. Los caudales absolutos se consultan con `.get(...)` porque en A el usuario puede dejarlos vacíos. No se recalculan las propiedades del aire ni se cambia el motor C.

## Interpretación física: qué significa cada relación

1. **NPR:** `pt,entrada tobera / p∞`, presión total frente a estática ambiental. No usar presión total exterior en el denominador.
2. **EPR teórico:** `pt,salida turbina / pt,entrada compresor`, dos presiones totales, por convención de descarga de turbina y cara de compresor. No es una lectura de sonda de un motor certificado. Véase [FAA](https://www.faa.gov/sites/faa.gov/files/09_phak_ch7.pdf) y la [definición NASA de EPR entre estaciones](https://www.grc.nasa.gov/www/k-12/airplane/epr.html).
3. **πt:** entrada de turbina dividida por salida, por tanto >1 en expansión válida; la convención inversa debe llamarse de otro modo.
4. **TSFC:** `3600f/Fs` en kg/(N·h); el factor 3600 convierte segundos a horas. Si Fs≤0 no se publica valor.
5. **Potencia de eje:** `ṁa ηm wt` en kW, ya que kg/s × kJ/kg = kJ/s. El trabajo específico de turbina utiliza la base de kg de aire e incluye `(1+f)`.
6. **Bruto y captación:** `Fbruto = Fmomento,salida + Fpresión` y `Fneto = Fbruto − Dentrada`. En el backend `resistencia_entrada` absoluta lleva signo negativo, por lo que el panel cambia el signo para enseñar una resistencia positiva.

Las equivalencias orientativas siguen siendo T1→Tt2, T2→Tt3, T3→Tt4, T4→Tt5. En el núcleo son estados **totales**. En motores reales los puntos de toma y numeraciones pueden cambiar. El panel no crea una EGT instrumental ni estado estático de turbina.

## Por qué se aplazan ηth, ηp y ηo

El Brayton productor de eje usa trabajo neto dividido por calor aportado. Nuestro turborreactor emplea el trabajo de la turbina para mover el compresor; su producto útil es empuje. Para definir eficiencia propulsiva hace falta relacionar potencia útil `F V∞` con la energía del chorro, tratando correctamente empuje de presión y flujo entrante. En un ensayo estático `F V∞=0`, aunque el motor produzca empuje. Por eso no se debe reutilizar la fórmula de rendimiento de ciclo de eje como si describiera la propulsión. Estos tres indicadores se muestran como no disponibles.

## JavaScript: estado sin simulaciones extra

`iniciarCaracterizacion49_9(documento)` recibe `Document`, devuelve `{actualizar, pendiente, seleccionarGrupo}` o `null` si el panel no existe. `seleccionarGrupo(clave)` devuelve boolean y cambia una variable privada `grupo`; `actualizar(respuesta)` lee `respuesta.caracterizacion`; `pendiente(texto)` borra los valores actuales. El objeto no tiene `fetcher`: por diseño no puede lanzar otra simulación. Usa `createElement` y `textContent` para construir tarjetas legibles y `details/summary` para explicación accesible.

`inicializar48` invoca ambos controladores visuales (fichas 49.8 y panel 49.9) en `onEstado`, `onRespuesta` y `onError`. Mantiene el grupo elegido mientras los números se eliminan durante el cálculo. Un POST manual ya resuelto ofrece JSON inicial incrustado por Jinja, sin segunda petición.

## Ejercicios de interpretación (sin cambios de código)

- Poner Mach 0 y después 0,7: comparar NPR y EPR; pueden coincidir accidentalmente en estático con πd=1, pero **no comparten definición**.
- Dejar vacío el caudal en A: los resultados específicos permanecen, pero Fneto [N] y Peje [kW] no aparecen como cero.
- Probar un punto con Fs≤0: TSFC no se presenta como consumo útil.
- Cambiar a C: N [rpm] solo aparece si converge el equilibrio de mapas; su ausencia no significa N=0.

## Pruebas, preservación y límites

La prueba Python nueva contrasta presiones, unidades, A/B/C, balances de empuje y consumo, ausencia de TSFC para Fs≤0 y contrato de error HTTP. La prueba JS nueva comprueba pestañas, indisponibilidad y limpieza al modificar entradas. Las regresiones existentes verifican que el motor, esquema, fichas y estudios siguen disponibles. Estas comprobaciones son **verificación de software, no validación experimental**.

No se añaden ecuaciones termodinámicas al frontend, no se modifica la tobera ni se generan nuevos rendimientos. EGT, bypass, N1/N2, peso, ruido, emisiones y surge quedan excluidos. Revisión visual pendiente en Windows; publicación y commit pendientes por decisión del usuario.

Para la auditoría completa de símbolos, fuentes, unidades y disponibilidad, consultar el [documento técnico](49_9_caracterizacion_prestaciones.md).
