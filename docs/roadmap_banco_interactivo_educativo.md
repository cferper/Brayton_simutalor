# Roadmap — Banco interactivo educativo (propuesta 49.7–50.2)

> **Estado:** planificación aprobada como orientación de trabajo; **ninguna de las funciones futuras descritas aquí se considera implementada** por aparecer en este documento. Los números 49.7–50.2 son propuestas de secuencia; cada milestone se documentará como realizado solo cuando exista código y verificación.
>
> **Rama de desarrollo:** `mejoras/cp-variable`. Punto de partida funcional: milestone 49.6, con estudios paramétricos 49.5, cuatro familias de vistas, modos A/B/C y restablecimiento explícito de geometría de diseño C. `main` queda fuera de este plan salvo autorización posterior.

## 1. Objetivo docente

Convertir el banco actual en un entorno donde se pueda **modificar el punto de funcionamiento**, **seleccionar las partes del turborreactor** y **comprender las magnitudes, ecuaciones y limitaciones** que justifican sus resultados. Conservar el simulador físico, el rigor de la verificación y las funciones gráficas ya construidas.

El esquema será didáctico, **no una geometría a escala calculada**, ni un simulador tridimensional, ni una predicción certificable de un motor real.

## 2. Requisitos transversales no negociables

1. **Mantener el cálculo interactivo actual:** controles permanentes de Mach exterior y temperatura total de entrada a turbina (variable interna vigente `T3`), sus sliders/entradas, recálculo automático debounced y señalización de carga/error. Conservar todos los parámetros avanzados y modos **A (caudal impuesto), B (geometría fija) y C (motor acoplado)**.
2. **Conservar las gráficas 49.6 y estudios 49.5:** ciclo, tobera, prestaciones, estudios paramétricos, zoom, consultas, exportación y estados de indisponibilidad.
3. **Una sola fuente física:** el backend y la API existentes proporcionan resultados. Seleccionar una pieza, una estación o una pestaña solo cambia la presentación; **no recalcula** el motor. Cambiar una entrada sí solicita el cálculo habitual, sin duplicar las peticiones ni presentar resultados anteriores como nuevos.
4. **Conservar los límites del modelo:** aire con propiedades variables cuando corresponda; combustión energética equivalente sin química detallada; un solo eje en C; tobera convergente o C-D según modelo. Sin magnitudes estimadas arbitrariamente ni perfiles espaciales ficticios dentro de los componentes.
5. **Nomenclatura:** el software llama `T3` a la entrada de turbina. La convención de estaciones habituales sitúa esa condición en `Tt4`. Crear una tabla de correspondencias verificadas antes de cambiar etiquetas; **no renombrar variables internas/API por estética**.
6. **Valores no disponibles:** distinguir claramente «no calculado», «no aplicable», «fuera de dominio» y «no convergencia verificada». Un fallo numérico de C no demuestra imposibilidad física. La geometría de referencia M47 es convergente, con Ag=Ae; no presentarla como óptima C-D.
7. **Accesibilidad y claridad:** teclado y lectores de pantalla para componentes seleccionables, contraste, foco visible, etiquetas y unidades SI; esquema responsive; evitar información que dependa solo del color.
8. **Disciplina de proyecto:** leer `AGENTS.md`, `CODE_WALKTHROUGH.md` relevante y documentación del milestone previo. Actualizar manual vigente y documentos técnico/educativo por cada implementación. Pruebas focalizadas durante el trabajo; regresión completa una vez al cierre importante; inspección visual en Windows; sin commits ni cambios en `main` salvo autorización.

## 3. Organización objetivo de la pantalla

- **Zona izquierda — Control del motor:** Mach, temperatura de entrada a turbina, selector A/B/C, geometría y configuración avanzada. **No ocultar esos dos controles principales al explorar el esquema.**
- **Zona central — Esquema SVG longitudinal:** entrada/difusor, compresor, cámara, turbina, eje y tobera; regiones seleccionables. El chorro puede representarse de forma esquemática sin simular su campo externo.
- **Zona derecha — Ficha contextual:** nombre, propósito y estado seleccionado; después se ampliará con estados de entrada/salida, ecuaciones, pérdidas y disponibilidad.
- **Zona inferior — Gráficas y estudios:** conservar las herramientas 49.4–49.6 y sus paneles.
- En pantallas pequeñas, apilar regiones con navegación que mantenga fácil el acceso al control del motor.

## 4. Secuencia de milestones (propuestos)

### 49.7 — Esquema interactivo del turborreactor

**Alcance:** implementar un SVG vectorial de corte longitudinal didáctico con al menos seis zonas seleccionables: difusor, compresor, cámara de combustión, turbina, eje y tobera. Cada selección resalta la pieza y muestra título y descripción funcional breve en un panel contextual. La selección funciona con ratón y teclado. Integración visual dentro de `/turborreactor/interactivo`, sin modificar el motor físico ni la API de cálculo salvo justificación explícita.

**Criterios de aceptación:** 
- Mach y T3 siguen siempre editables; al cambiarlos se actualizan resultados y gráficas como en 49.6.
- La selección de una pieza no origina llamadas de simulación.
- Los modos A/B/C, restablecimiento de geometría C, estudios 49.5 y gráficas 49.6 permanecen funcionales.
- Diseño entendible a escala de escritorio y móvil; teclado, foco y descripciones accesibles.
- En ausencia de datos o ante error 422 no se atribuyen números ni estados antiguos a la pieza.
- Documento técnico y aprendizaje 49.7, `CODE_WALKTHROUGH.md` sincronizado y pruebas de interfaz pertinentes.

**Fuera de alcance:** fichas numéricas exhaustivas (49.8), nuevos parámetros (49.9), vinculaciones finas con gráficos (50.0), 3D, nuevas ecuaciones, refactorización general.

### 49.8 — Fichas educativas por componente y estaciones

Para cada pieza: qué hace, qué entra/sale, temperaturas y presiones totales disponibles, caudales y trabajos donde procedan, pérdidas, fórmula fundamental, base másica y limitaciones. Usar solo valores existentes en API o transformaciones justificadas. Introducir una correspondencia explícita de estaciones entre convención actual y convencional; distinguir estados totales de estados estáticos. El SVG y el panel muestran la misma selección y se actualizan después de cada simulación válida.

**Aceptación:** datos verificados contra API y estados físicos; magnitudes no aplicables ocultas o rotuladas; ningún perfil continuo inventado.

### 49.9 — Panel de caracterización habitual del motor

Organizar en «Funcionamiento», «Consumo y prestaciones» y «Rendimientos y pérdidas». Priorizar:
- Ya existentes: empuje neto/específico/absoluto condicionado a caudal, consumo, TSFC, velocidades, `rp`, TIT, balance de eje, régimen C.
- Deducibles si existen estados y convenciones compatibles: relación combustible/aire `f=ṁ_f/ṁ_a`; EPR (definición por estaciones explícita); NPR (presión total a entrada de tobera frente a presión ambiente estática); relaciones de presión de compresor/turbina; indicadores de caída de presión.
- Requieren definición y verificación independientes: rendimiento térmico, propulsivo, global, caudal y velocidad corregidos (con referencias y estaciones verificadas).

Cada magnitud contendrá símbolo, unidad, definición, fórmula/procedencia, condiciones de validez y estado «calculada / derivada / no disponible». **No extrapolar a motores con fan ni inferir masa del motor, empuje/peso, emisiones, ruido o margen de surge sin información adicional.**

### 50.0 — Sincronización entre motor, estaciones y gráficas

Al seleccionar componente/estación, resaltar de forma coherente sus **puntos calculados discretos** en T–s, temperatura/presión total y balances; mantener las herramientas de gráfica. No fingir distribución espacial axial en compresor/cámara/turbina. Seleccionar no recalcula.

### 50.1 — Laboratorio comparativo de puntos de funcionamiento

Permitir conservar el estado A de referencia y comparar con un estado B del **mismo modelo y condiciones identificadas**: entradas modificadas, incrementos absolutos/relativos de magnitudes disponibles, puntos en gráficas y diagnóstico de diferencias. Especial énfasis en ensayos Mach y temperatura de entrada a turbina. Evitar atribuir causalidad a un único parámetro si varios cambiaron o si varían las restricciones entre A/B/C. No comparar cifras ausentes.

### 50.2 — Diagnóstico avanzado condicionado por física

Solo tras analizar necesidad y disponibilidad de datos: caudal/velocidad corregidos según las convenciones del mapa; mapas de turbomaquinaria con punto de operación; márgenes operativos **solo si existen líneas límite verificadas**; resultados frente a Mach/altitud o regímenes cuando estén soportados. Requiere diseño físico, pruebas numéricas y documentación antes de enseñar indicadores.

## 5. Regla de publicación por etapas

Cada milestone se implementa y revisa **por separado**. Tras integrar en Windows: pruebas focalizadas, regresión pertinente, inspección visual, aprobación del usuario y solo después commit/push en rama autorizada. No comenzar el siguiente milestone automáticamente. Si la versión local tiene cambios sin publicar, coordinar primero con Git para no perderlos ni sobrescribirlos.

## 6. Referencias metodológicas

- NASA Glenn, [EngineSim](https://www.grc.nasa.gov/www/k-12/BGP/ngnsim.html): precedente educativo de selección de componentes, cambios en entradas y múltiples vistas.
- NASA Glenn, [estaciones y esquema de turbina de gas](https://www.grc.nasa.gov/www/k-12/airplane/turbdraw.html): nomenclatura habitual de estaciones (no necesariamente igual a nombres internos del proyecto).
- NASA Glenn, [caudal corregido](https://www.grc.nasa.gov/www/k-12/BGP/wcora.html): importancia de condiciones de referencia y flujo compresible.

Estas referencias orientan los objetivos didácticos; **no validan experimentalmente** nuestros cálculos ni autorizan copiar código o recursos protegidos.

## 7. Primera acción acordada

Preparar exclusivamente el **milestone 49.7** sobre la versión real actualizada de `mejoras/cp-variable`. Mantener la simulación Mach/T3 en tiempo real y no modificar solucionadores. Entregar para integración y verificación visual en Windows antes de su publicación.
