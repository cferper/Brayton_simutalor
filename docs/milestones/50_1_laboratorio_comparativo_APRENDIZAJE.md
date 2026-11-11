# Milestone 50.1 — Aprendizaje: comparar dos puntos sin recalcular

## Situación de partida y objetivo

El 50.0 sincronizaba un esquema de motor con las estaciones y gráficos de **un** punto calculado. El laboratorio añade un segundo conjunto de resultados conservado como referencia en la memoria del navegador. Partida: `mejoras/cp-variable`, commit `2ec7b68e4a3b86719a81fb8ad65afd8f15ef2325`, limpio. No se modifica `main`.

## Modelo físico y magnitudes

El solucionador continúa siendo el modelo educativo monoeje cp(T) con combustión equivalente. El punto de referencia y el actual contienen condiciones de vuelo, TIT (`T3` interna), modalidad A/B/C, entradas avanzadas, estados y métricas del mismo motor. El servidor calcula entalpía y entropía y entrega estaciones:

| ID | Estación | Tipo |
|---|---|---|
| `pt2` | Tras difusor, entrada compresor | Total/remanso |
| `pt3` | Salida compresor | Total/remanso |
| `pt4` | Salida cámara, entrada turbina (`T3`) | Total/remanso |
| `pt5` | Salida turbina | Total/remanso |
| `salida` | Escape de tobera si está resuelto | Estática |

Para ambas series, T–s usa pares `(s,T)` en kJ/(kg·K) y K. Los cuatro puntos totales se comparan con la misma escala, y la salida estática se distingue por su identificador y la lectura. Una unión discontinua entre estaciones no representa un proceso continuo resuelto.

## Diferencias y comparación válida

`ΔX = X₂−X₁`; `ΔX_rel = 100(X₂−X₁)/X₁`. Si X₁=0, la variación relativa no existe. Un cambio de eficiencia de 80 % a 85 % implica **+5 puntos porcentuales** y **+6,25 % relativo**. La diferencia conserva signo incluso cuando la magnitud disminuye.

No se pueden comparar como equivalentes prestaciones absolutas basadas en un caudal prescrito con otras obtenidas por geometría o mapas sin revisar las restricciones. Por eso cambiar A/B/C bloquea esas diferencias, y variar otra entrada distinta de Mach/T3 genera una advertencia. Una correlación entre dos ensayos no prueba causalidad: si Mach y TIT cambian, no sabemos qué proporción de la variación corresponde a cada uno.

## Programación: estado separado del cálculo

El módulo `static/laboratorio_comparativo_50_1.js` utiliza:

- `extraer50_1(datos, entradas)`: toma una respuesta JSON válida y construye una instantánea con `modelo`, `modo`, `entradas`, `estaciones`, `caracterizacion`, `magnitudes` y `diagnosticos`. Devuelve `null` si faltan datos. No realiza cálculos físicos.
- `iniciarLaboratorio50_1(documento, formulario)`: registra los botones y devuelve métodos `actualizado`, `pendiente`, `guardar`, `borrar`, `referencia` y `actual`. Retiene dos variables distintas en el cierre de JavaScript (*closure*).
- `diferencia50_1(ref,actual,unidad)`: opera sobre números finitos; retorna `{absoluta,relativa,unidadAbsoluta}` con `null` en diferencias no definidas.
- `compatibilidad50_1(ref,actual)`: compara las claves de entrada y el modo; devuelve `{compatible,homogenea,cambios,mensaje}`. La lista de cambios se obtiene del conjunto unión de nombres de las entradas.
- `valor50_1(p,id)`: localiza la magnitud `id` en los indicadores calculados por Python; devuelve número o `null`.
- `dibujarEstados50_1(ref,actual,tipo)`: produce un SVG con dos series T–s, T o p. Recibe `tipo='ts'|'T'|'p'`; no interpola estados internos. Devuelve una cadena o `''`.
- `dibujarPrestaciones50_1(ref,actual,compatible)`: produce barras SVG para magnitudes existentes si las modalidades son compatibles. Devuelve cadena o `''`.

El guardado ejecuta una **copia profunda** `JSON.parse(JSON.stringify(actual))`: modificar más tarde los campos del punto actual no modifica la referencia. Al cambiar Mach/T3, el controlador físico existente invalida el punto actual, llama a `pendiente()` y obtiene un nuevo resultado mediante su único `fetch`. Guardar, borrar, ver condiciones, consultar marcadores, ampliar y descargar SVG no lanzan simulaciones.

## Ejemplo de ensayo

1. Calcula un punto A con Mach 0,3 y TIT 1500 K; guarda la referencia.
2. Cambia solo Mach a 0,5 y espera la nueva respuesta. Observa ΔFs, ΔTSFC y los cambios de los cuatro estados totales sin presuponer el sentido de la variación.
3. Cambia también T3. El panel advierte que ya no puedes atribuir las diferencias a una sola variable.
4. Cambia a C. La referencia A sigue guardada; las diferencias incompatibles se omiten.
5. Provoca una entrada inválida: la referencia persiste y el punto actual se retira. Recupera un punto válido y sustituye la referencia si lo deseas.

## Pruebas y limitaciones

La batería nueva comprueba diferencias firmadas, caso cero, estados ausentes, cambio de modalidad/geometría, independencia de instantáneas y SVG con puntos discretos; la regresión y sus resultados aparecen en la entrega. No se ha realizado validación experimental. La revisión de diseño, accesibilidad y exportación en navegador Windows queda pendiente. No incluye funciones del 50.2.

## Estado de Git

Base `2ec7b68e`; cambios sin commit ni push. Los archivos deben integrarse localmente y revisarse visualmente antes de su publicación.
