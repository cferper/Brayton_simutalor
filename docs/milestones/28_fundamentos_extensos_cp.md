# Milestone 28 — Segunda iteración educativa: fundamentos extensos cp(T)

**Fecha de trabajo:** 24/10/2026  
**Repositorio:** `cferper/Brayton_simutalor`  
**Rama de destino:** `mejoras/cp-variable`  
**Commit de partida verificado:** `9dc0b8fe70c6667d2f3df9c30b2535379598c3c3`  
**Commit asociado a esta iteración:** pendiente de publicación; el commit base no contiene el cambio.

## Estado anterior

La primera iteración (milestone 27) reunía el simulador en una sola plantilla, aportaba dos vistas educativas en las ocho secciones y un visor ampliado de las ocho gráficas cp(T). Las explicaciones teóricas seguían siendo demasiado breves (cinco tarjetas de unas frases); «Uso y configuración» y «Fundamentos y procedimiento» tenían profundidades parecidas.

## Qué se ha añadido

- Las seis secciones científicas contienen ocho bloques teóricos cada una (aproximadamente 700–800 palabras), secuenciados desde el contexto hasta las limitaciones.
- Informes y Ayuda tienen cinco bloques más desarrollados, sin repetir toda la teoría de las otras secciones.
- «Uso y configuración» permanece breve; se conservan los formularios, sus ayudas individuales y los resultados.
- La teoría presenta ecuaciones con unidades, pasos numerados, ejemplos explícitamente ilustrativos y recuadros de interpretación.
- Una sola columna de lectura sustituye las tarjetas teóricas compactas en dos columnas; el diseño base, colores, menú y las galerías de gráficos permanecen.

No se han incorporado módulos científicos, parámetros físicos, rutas ni gráficos nuevos.

## Nuevos conceptos de ingeniería que se enseñan

| Sección | Aspectos desarrollados y contrastados con el código |
| --- | --- |
| Simulación | Brayton abierto/idealizado, cuatro estados y procesos; ley de gas ideal frente a cp(T); referencia isentrópica y eficiencia real; inversión por bisección de s° y h; restricciones. |
| Resultados | Primera ley de volumen de control, entalpía de flujo y signos de trabajo; qin/qout; cierre del balance, tabla de propiedades, T–s esquemático y diferencias entre kJ/kg y kW. |
| Optimización | Objetivos A/B independientes, dominio motor abierto, x=ln(rp), derivadas realmente implementadas, bisección, máximo interior frente a supremo y escala dual de curvas. |
| Sensibilidad | OFAT de siete variables, muestras lineales, clasificación, diferencia central o unilateral, sensibilidad normalizada, paso y medio paso, estabilidad y límites de OFAT. |
| Mapa | Malla T3 lineal y rp logarítmica, color por magnitud y máscara, mejores nodos discretos y referencia de óptimos continuos de una sola T3, diferencia frente a mapa operativo de turbomáquinas. |
| Segunda ley | Entropía y generación en volúmenes adiabáticos; exergía física relativa a T0/p0; Gouy–Stodola; balances alternativos, residuos, eficiencia exergética de equipos; destrucción **parcial**, nunca total. |
| Informes | Trazabilidad, modelos/entradas/versiones, verificación frente a validación; archivo histórico de gas perfecto sin nuevos informes cp(T). |
| Ayuda | Glosario de variables/unidades, itinerario pedagógico, estados no motores/errores/supremos, hipótesis y alcance aeroespacial. |

Los ejemplos de presiones, balance aritmético de entalpías, sensibilidad porcentual, construcción de malla y destrucción de exergía **no se presentan como resultados del caso activo**. La revisión de rigor usa los módulos `propiedades_aire.py`, `ciclo_cp_variable.py`, `optimizacion_cp_variable.py`, `sensibilidad_cp_variable.py`, `mapa_diseno_cp_variable.py` y `segunda_ley_cp_variable.py` en su versión del commit base, sin alterarlos.

## Nuevos conceptos de Python, HTML y CSS

- **Contenidos declarativos:** `CONTENIDOS` mantiene por sección `uso` (cadena) y `fundamentos` (tupla de pares título/cuerpo). Las seis secciones científicas pasan de cinco a ocho pares; los consumidores no cambian.
- **Concatenación de literales Python:** los fragmentos de varias líneas forman una sola cadena sin necesidad de añadir saltos ni concatenar variables del usuario.
- **HTML semántico de autoría controlada:** párrafos, listas ordenadas, subíndices y recuadros; `safe` se utiliza sobre esos textos estáticos, nunca con datos arbitrarios de formularios.
- **CSS de lectura:** `.edu-deep-grid` emplea una columna, ancho máximo, mayor interlineado, estilos `.edu-equation` para fórmulas y `.edu-insight` para advertencias y ejemplos. Adaptación a móvil sin bibliotecas nuevas.

Las funciones `_tarjeta(titulo,cuerpo)` y `construir_educacion_cp()` no cambian de firma. `dashboard.py`, el HTML y el JavaScript no se modifican. Los cálculos siguen produciéndose solo al ejecutar sus acciones Flask originales.

## Qué hemos aprendido

Una interfaz educativa necesita distintos niveles de explicación: la acción inmediata debe ser fácil de encontrar, mientras que la teoría debe desarrollar el razonamiento físico completo. Se puede mejorar sustancialmente la utilidad didáctica mediante contenido estático y maquetación sin tocar un solucionador numérico verificado.

## Comprobaciones

- Pruebas focalizadas de contenido, estructura y representación Flask, más regresiones de las funciones web existentes.
- Comprobación de que el módulo educativo no atribuye al algoritmo fórmulas de γ constante, optimizadores de malla inexistentes o destrucción total de exergía.
- Sintaxis de Python y JavaScript cuando corresponde; revisión manual de contenido contra las funciones.
- GitHub Actions sobre rama temporal antes de avance rápido de `mejoras/cp-variable`.

Los resultados efectivos se comunicarán y enlazarán tras ejecutarse; no se presuponen aquí.

## Limitaciones que siguen existiendo

El aire sigue siendo ideal de composición fija; no hay combustión química ni empuje, potencia sin caudal, mapa real de compresor/turbina ni validación experimental. El apartado Informes no exporta nuevos HTML cp(T). Una inspección visual en Windows deberá valorar longitud de lectura, legibilidad de fórmulas y navegación móvil; la prueba HTML no la sustituye.

