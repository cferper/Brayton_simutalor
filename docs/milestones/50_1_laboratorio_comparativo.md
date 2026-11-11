# Milestone 50.1 — Laboratorio comparativo de puntos de funcionamiento

## Estado anterior

Rama `mejoras/cp-variable`, base verificada `2ec7b68e4a3b86719a81fb8ad65afd8f15ef2325`, publicación del 50.0. El banco mostraba un solo punto y sincronizaba sus estaciones gráficas con el componente seleccionado.

## Qué se ha añadido

- Panel **Punto 1 — Referencia / Punto 2 — Actual**; guardar, sustituir, eliminar y revisar todas las entradas en un `details`.
- Copia profunda en memoria de condiciones, modo A/B/C, identificación de modelo, `caracterizacion`, estaciones, prestaciones y diagnósticos. Nunca se ejecuta una petición al guardar.
- Tabla de condiciones, empujes, consumos, dosado, trabajos y velocidades con diferencias absolutas y relativas válidas. Ausencias se muestran como `No disponible` / `—`.
- Cuatro gráficos comparativos: T–s con puntos discretos (incluyendo salida estática cuando existe), temperaturas totales, presiones totales y pares de barras de prestaciones. Cada gráfico utiliza una escala común para las dos soluciones; las barras emplean una escala por magnitud, porque sus unidades son distintas. Consulta por ratón/teclado, zoom local y exportación SVG.
- Advertencias al cambiar el modo, geometría, contorno y otros parámetros avanzados; descripción de variaciones numéricas sin atribuir causalidad automática a Mach/T3.
- Al invalidar o fallar el cálculo actual, se elimina la comparación anterior y se conserva la referencia.

## Nuevos conceptos de ingeniería

`ΔX=X_actual−X_referencia`; `ΔX_rel=100ΔX/X_referencia` si y solo si la referencia es distinta de cero. Para una magnitud expresada en `%`, el salto absoluto se expresa en **puntos porcentuales**, mientras que la variación relativa sigue siendo %. La comparación entre modalidades A/B/C no autoriza restar directamente prestaciones de bases másicas o restricciones diferentes; se mantienen visibles las condiciones y magnitudes, pero se retiran esas diferencias. Una variación conjunta de Mach, TIT o geometría no permite identificar una causa única.

El diagrama T–s sigue representando puntos resueltos enlazados esquemáticamente: **no** es una trayectoria de proceso ni un perfil axial interno. La entropía se evalúa en Python con `propiedades_aire.s`, sobre cada estado T,p ya existente; no se introducen ecuaciones termodinámicas en el navegador.

## Nuevos conceptos de Python y JavaScript

`estaciones_turborreactor` añade `s` a cada dict sin alterar su lista de estaciones. JavaScript almacena una instantánea independiente mediante `JSON.parse(JSON.stringify(...))`. El nuevo módulo separa extracción de datos, comparación numérica, compatibilidad y generación SVG. Se integra a través de los callbacks existentes del controlador M48; no cambia la API, no crea otro solucionador y no modifica el sistema de gráficas 49.4/50.0.

## Qué hemos aprendido

Una referencia debe permanecer inmutable durante cambios de controles. Las diferencias requieren igual magnitud, unidad y base física. Un valor ausente no es cero; un fallo numérico no demuestra inviabilidad física. La presentación comparativa y su descripción no equivalen a una validación experimental.

## Limitaciones que siguen existiendo

La referencia reside solo en la pestaña actual, sin base de datos. No hay optimización de casos ni mapas nuevos. Las escalas individuales de las barras de prestaciones impiden comparar entre magnitudes distintas por su longitud. No se incorporan caudales corregidos, márgenes de surge ni los diagnósticos avanzados del 50.2. Inspección visual y usabilidad en Windows pendientes.

## Verificación

Pruebas focalizadas Python/JavaScript nuevas para contrato de estados, autenticidad de la API, diferencias, cero, ausencia de valores y modalidades; regresión general al concluir (resultado registrado en la entrega). Esta es **verificación de software**, no validación física externa.

## Commit asociado

**Pendiente**. Implementado en una copia de trabajo sobre el HEAD 50.0 indicado, sin commit ni push.
