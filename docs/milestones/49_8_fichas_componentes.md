# Milestone 49.8 — Fichas con magnitudes y ecuaciones por componente

## Estado anterior

La rama `mejoras/cp-variable` parte del HEAD verificado
`55f49ccf1b3c82d0f29eb59c383cfe21b50df4d7` (49.7 publicado).
El SVG educativo seleccionaba seis componentes, pero únicamente enseñaba
sus nombres y funciones. La API ya devolvía estaciones y prestaciones,
no una agrupación de datos por componente.

## Qué se ha añadido

- En el panel contextual de cada componente aparecen tres apartados:
  **Funcionamiento**, **Resultados** y **Ecuaciones**.
- La nueva estructura JSON `componentes` reúne valores de resultados
  existentes, su unidad, tipo (`total`, `estatica`, `operacion`) y procedencia.
- El componente seleccionado se conserva al cambiar Mach, T3 o modalidad.
  La respuesta válida actualiza sus cifras sin otra petición HTTP.
- Antes de calcular y ante errores, las cifras se retiran y aparece un
  estado de indisponibilidad: no se reutiliza un punto antiguo.
- Una simulación manual cargada desde Flask puede mostrar su ficha inicial
  desde JSON incrustado en HTML, sin volver a ejecutar el solucionador.
- El panel incluye una correspondencia orientativa de estaciones internas
  T1–T4 frente a convenciones habituales Tt2–Tt5.

## Procedencia física de los datos

| Pieza | Datos | Origen del resultado |
| --- | --- | --- |
| Difusor | Exterior estático, vuelo, remanso antes/después, πd | `ambiente`, `remanso`, `difusor` |
| Compresor | T/p totales 1–2, rp, ηc, trabajo específico | `compresor`; relaciones de entalpías ya usadas en cp(T) |
| Cámara | T/p totales, δ, dosado f, combustible y aporte energético | `compresor`, `combustor`, `prestaciones_absolutas` |
| Turbina | T/p totales 3–4, ηt y trabajo específico | `combustor`, `turbina`, `compresor` |
| Eje | Trabajo específico turbina/transmisión/pérdidas, ηm, potencia, rpm C | `turbina`, `compresor`, `prestaciones_absolutas`, `motor_acoplado` |
| Tobera | Remanso de entrada, estáticos de garganta/salida, Mach, velocidad, áreas, régimen y presión de empuje | `tobera`, `dimensionamiento_tobera`, `diagnosticos`, `prestaciones` |

Se conserva `None` para caudales, potencia, rpm, áreas o valores de
garganta que el modelo no ha proporcionado. En los componentes del núcleo
no se calculan magnitudes estáticas sin conocer la velocidad local.

## Nuevos conceptos de ingeniería

Los resultados distinguen **magnitudes totales** (remanso) de
**estáticas** (flujo local). T3 interna corresponde a la temperatura
total de entrada a turbina (aproximadamente Tt4 convencional).
El trabajo específico [kJ/kg aire] no es potencia [kW]; únicamente se
puede multiplicar por el caudal [kg/s] cuando está disponible. La cámara
representa combustible equivalente sin química detallada.

Las ecuaciones seleccionadas son balances ya implementados: entalpía
cp(T), rendimientos isentrópicos, recuperación de presión, aporte
equivalente de combustible, balance monoeje y energía de tobera.

## Nuevos conceptos de programación

`fichas_componentes_49_8(resultado)` agrupa resultados del backend sin
resolver un nuevo punto motor. `preparar_vista_turborreactor` reutiliza
el mismo dict para la plantilla y la API. JavaScript actualiza únicamente
texto y nodos de la ficha, sin cálculos termodinámicos. Tres botones
`aria-pressed` controlan los apartados de cada ficha.

## Qué hemos aprendido

Una representación educativa debe mostrar **de dónde procede cada
número** y retirar datos cuando cambia el punto motor. El estado
visual (componente/apartado seleccionado) se mantiene aunque el resultado
numérico esté temporalmente pendiente.

## Limitaciones que siguen existiendo

- No hay perfiles estáticos interiores del compresor, cámara o turbina.
- No se han añadido indicadores del 49.9 ni modificado mapas o solucionadores.
- Las ecuaciones son explicaciones breves de relaciones ya implementadas;
  los detalles completos están en `CODE_WALKTHROUGH.md`.
- Las pruebas verifican coherencia de software; no validación experimental.
- Falta la inspección visual definitiva en el equipo Windows.

## Verificación en Windows (11-11-2026)

Pasaron las 6 pruebas focalizadas del 49.8 y los 11 tests JavaScript; `node --check` también pasó. La regresión única ejecutó 788 pruebas: **778 correctas, 10 omitidas, 0 fallidas**. El informe del ZIP indica 787 correctas y 1 omitida, también 788 en total. La diferencia son opciones del entorno: el `.venv` actual no contiene SciPy ni Cantera (8 pruebas de SciPy y 1 de Cantera) y Windows omite una prueba que requiere permiso para crear symlinks. No se modificaron ni retiraron pruebas previas. Esta comprobación verifica coherencia del software, no datos experimentales.

La revisión visual queda para el usuario; Flask se deja disponible en `http://127.0.0.1:5002/turborreactor/interactivo`.

## Commit asociado

**Pendiente.** Entrega en ZIP, sin staging, commit ni push.
