# Milestone 50.0 — Sincronización del motor y las estaciones calculadas

## Alcance

Se conecta la selección del SVG longitudinal de M49.7 a los **puntos ya calculados** de los SVG de M49.6. No se cambian ecuaciones, mapas, tolerancias, flujo de datos de la API ni control Mach/T3. Tampoco se sustituye el visor con zoom y exportación de M49.4 ni los estudios M49.5.

## Correspondencias

| Pieza | Entrada | Salida | Otras marcas |
| --- | --- | --- | --- |
| Difusor | Ambiente exterior, **estático** (solo en el resumen) | `pt2`, remanso | Sin nuevo trabajo |
| Compresor | `pt2` | `pt3` | Barras de trabajo absorbido y balance |
| Cámara | `pt3` | `pt4` | Barra de energía del combustible |
| Turbina | `pt4` | `pt5` | Barras de trabajo entregado y balance |
| Eje | — | — | Solo trabajo mecánico del eje |
| Tobera | `pt5`, remanso | `salida`, estático; `garganta`, estática **solo si está calculada** | Barra de energía cinética |

Las etiquetas `pt2`–`pt5` representan, respectivamente, los estados internos **T1–T4** (aproximadamente Tt2–Tt5 en una notación de motor habitual). No se modifica el significado ni el nombre de `T3` en Python. La entrada del difusor no se superpone a una curva de remanso porque el ambiente de la API es estático. El eje no es un volumen de gas atravesado por estaciones termodinámicas.

## Implementación

- `turborreactor_web.py`: añade `id` a los diccionarios de estaciones; atribuye `data-engine-station` a los círculos reales de las cuatro estaciones, T–s y garganta/salida discretas cuando existan. Atribuye `data-engine-work`/`data-engine-energy` a barras existentes. No modifica posiciones ni valores.
- `static/turborreactor_interactivo.js`: controlador visual `iniciarSincronizacion50_0`, con tabla declarativa de asociaciones y callback opcional de M49.7. La selección usa datos de la respuesta ya recibida; nunca solicita una nueva simulación. Tras cada sustitución SVG reexplora los marcadores en el documento.
- `templates/turborreactor.html`: resumen contextual accesible que identifica estaciones, tipo total/estático, temperatura y presión calculadas.
- `static/turborreactor.css`: estilo de marcas y atenuación reversible, además de `prefers-reduced-motion`.

En estados `pendiente`, `actualizando` y `error`, el controlador retira los resaltados numéricos, mientras mantiene la pieza elegida. En `actualizado`, usa exclusivamente `datos.estaciones` de esa respuesta. Cuando una magnitud o un estado no existe, no fabrica un cero ni una garganta ficticia.

## Verificación y límites

Pruebas `tests/test_sincronizacion_motor_50_0.py` y `tests/js/test_sincronizacion_motor_50_0.cjs`: cuatro estaciones, salida T–s, ausencia de garganta ficticia, barra de eje, selección sin peticiones y limpieza tras invalidación. Ejecutar también las pruebas existentes y una regresión general. La revisión visual y accesibilidad con navegador real en Windows queda pendiente.

Los gráficos de tobera que usan abscisas ordinales **no son** perfiles axiales; las curvas internas de todos los componentes del núcleo **no se resuelven**. M50.1 y M50.2 permanecen pendientes.
