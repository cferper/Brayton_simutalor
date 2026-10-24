# Milestone 27 · Revisión educativa y visual cp(T), iteración 1

**Fecha:** 24/10/2026  
**Repositorio:** `cferper/Brayton_simutalor`  
**Rama de destino:** `mejoras/cp-variable`  
**Base verificada:** `daa3787ccbbb3aebb40598125f33bce43f730b78` (Fase 2G)  
**Naturaleza:** presentación y aprendizaje; sin modificación del modelo físico.

## 1. Objetivo y criterios

Hacer comprensible la interfaz a una persona que conoce los fundamentos de Termodinámica, pero todavía no domina los detalles del Brayton con propiedades variables. Reducir el tamaño visible de las ocho gráficas **ya existentes** y permitir ampliarlas bajo demanda, sin introducir nuevos tipos de gráfica en esta iteración.

El simulador de gas perfecto se conserva en otro repositorio y los informes históricos siguen etiquetados correctamente. Esta revisión afecta únicamente al simulador cp(T) en la rama indicada; no modifica `main`, el repositorio de conservación, el equipo Windows ni el plan histórico de mejoras.

## 2. Organización de la información

Cada uno de los ocho apartados dispone de dos vistas:

1. **Uso y configuración:** presentación «Qué vamos a hacer», descripciones de parámetros y unidades, resultados actuales y su interpretación cuando existen.
2. **Fundamentos y procedimiento:** cinco tarjetas propias: objetivo, hipótesis, pasos, interpretación y límites. En Informes y Ayuda los títulos se adaptan al propósito documental.

| Apartado | Contenido enseñado y resultado interpretado |
| --- | --- |
| Simulación | Estados 1–4, siete parámetros, pérdidas, hipótesis de aire ideal cp(T) y validación motora posterior. |
| Resultados | Tabla T/p/cp/γ/h/s, primera ley, trabajos, calores, rendimiento si es motor, carácter esquemático del T–s. |
| Optimización | Objetivos A y B, dominio motor abierto, máximos interiores frente a supremos. |
| Sensibilidad | Barrido OFAT, elasticidad local, recuentos motores, discontinuidades sin interpolación. |
| Mapa | Malla rp–T3, regiones inválidas, mejores nodos discretos frente a óptimos continuos. |
| Segunda ley | Entropía, exergía de flujo y destrucción parcial de compresor/turbina, referencia T0/p0. |
| Informes | Naturaleza histórica de los HTML con cp y γ constantes, sin nuevo exportador cp(T). |
| Ayuda | Unidades, ruta de aprendizaje y limitaciones frente a un motor real. |

La tabla de resultados no es sustituida por contenido divulgativo: la explicación se añade al cálculo. No se publica una prestación de motor si solo existe un estado calculable no motor.

## 3. Galería y ampliación de los SVG

Se reutilizan los ocho SVG generados previamente:

- 1 diagrama T–s;
- 1 gráfica combinada de A/B;
- 3 gráficas OFAT;
- 2 mapas rp–T3;
- 1 gráfica de destrucción de exergía de turbomáquinas.

La macro `grafica_cp(titulo, svg, explicacion)` dibuja una tarjeta con figura, nombre y nota legible. `.cp-gallery .plot-grid` utiliza dos columnas a tamaño de escritorio y una en móvil. La propiedad `max-height` solo limita la vista preliminar; **los SVG calculados permanecen íntegros**. `static/dashboard.js` amplía SVG mediante `cloneNode(true)` en el diálogo existente y conserva ampliación de imágenes PNG históricas. La gestión nativa del diálogo mantiene cierre con Escape y retorno del foco.

No se representa ninguna gráfica adicional. Tampoco se generan imágenes de captura ni se afirma haber comprobado el diseño en un navegador real; la revisión visual de Windows permanece como siguiente paso manual.

## 4. Implementación y límites

| Archivo | Cambio |
| --- | --- |
| `educacion_cp_variable.py` | Nuevo. Textos controlados de ocho apartados, ayudas de siete parámetros físicos y seis del mapa. |
| `dashboard.py` | Inyección de contenidos educativos a Jinja solo en `modo_cp`. |
| `templates/index.html` | Estructura pedagógica, ayudas, conclusiones condicionadas, galería, modal SVG; sin segunda plantilla. |
| `static/dashboard.js` | Reutilización del visor con soporte para SVG además de `<img>`. |
| `static/style.css` | Diseño compacto de figuras y tarjetas educativas, responsive y modal. |
| `tests/test_revision_educativa_cp.py` | Doce pruebas focalizadas de estructura, integración y garantías. |
| `.github/workflows/verificacion_web_cp_variable.yml` | Incorporación de rama temporal y test de iteración 1 al conjunto anterior. |
| `CODE_WALKTHROUGH.md` | Nueva sección 4.65, funciones, contratos, interacción y límites. |
| `docs/milestones/27_*` | Documento técnico y guía de aprendizaje. |

Se mantienen sin cambios `propiedades_aire.py`, `ciclo_cp_variable.py`, `optimizacion_cp_variable.py`, `sensibilidad_cp_variable.py`, `mapa_diseno_cp_variable.py`, `segunda_ley_cp_variable.py`, módulos históricos, informes antiguos y `docs/PLAN_MEJORAS_BRAYTON_SIMULATOR.md`.

## 5. Verificación y pruebas

**Comprobación local de la iteración:** 97 pruebas correctas: 85 de regresión y 12 nuevas; sintaxis de `static/dashboard.js` validada con `node --check`.

Las nuevas pruebas incluyen: ocho conjuntos de pestañas, cinco tarjetas educativas por apartado, siete ayudas físicas y seis del mapa, igualdad de cifras de 2B, diferenciación de máximos de 2C, tres curvas OFAT, dos mapas y su malla, suma de exergía parcial, conservación del archivo histórico, soporte de modal para SVG e imágenes y reglas responsive.

**GitHub Actions:** el workflow ejecuta las mismas baterías focalizadas en rama temporal de validación, antes de incorporar el commit a desarrollo. Su estado debe comprobarse en la ejecución remota (no se confunde un test local con un resultado de Actions).

### Pendiente para la revisión visual de Windows

Revisar manualmente, en tamaños de pantalla real, el número de tarjetas visibles, la legibilidad de ejes y leyendas, la ampliación con ratón/teclado, el desplazamiento del modal, estados vacíos/no motores y la carga visual de los fundamentos. Ninguna prueba HTML puede certificar por sí sola esa experiencia. La siguiente iteración podrá añadir más gráficos una vez acordada su utilidad y corrección termodinámica.

