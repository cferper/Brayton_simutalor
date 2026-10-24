# Milestone 23 — Unificación del dashboard con cp(T)

## Estado anterior

Base verificada: rama `mejoras/cp-variable`, commit `64b4568a98f36779e305fe80d7c36c9e9498bd1d`. La Fase 2D ofrecía una segunda página en `templates/cp_variable.html` y un Blueprint (`/modelo-cp-variable`) para el modelo variable. El formulario original `index.html` todavía ejecutaba el gas de propiedades constantes. Los módulos científicos de las Fases 2A–2C ya estaban implementados.

## Qué se ha añadido

- La única interfaz de cálculo es GET/POST `/` con `templates/index.html`, conservando navegación de ocho secciones, estilos, componentes, fuentes y distribución.
- Simulación recibe siete entradas (T1, T3, rp, p1, eta_c, eta_t, delta); Resultados muestra cuatro estados, presiones, temperaturas isentrópicas, cp(T), gamma(T), h, s, balances, rendimiento físico y SVG T–s esquemático.
- Optimización calcula A (máximo trabajo neto) y B (máximo rendimiento) por separado con `estudiar_cp_variable` y gráfica de muestras reales. Se distingue máximo interior de supremo de frontera abierta.
- Sensibilidad, Mapa de diseño y Segunda ley están desactivados en la interfaz con avisos explícitos; sus implementaciones Python/documentación no se tocan.
- Los informes antiguos permanecen consultables/descargables, identificados como gas perfecto histórico. No se producen informes nuevos con cp(T).
- Se retira la ruta Blueprint y se elimina `templates/cp_variable.html`, después de trasladar sus capacidades. `cp_variable_web.py` conserva los presentadores y añade un orquestador reutilizable.
- El workflow CI verifica el contrato nuevo de Flask y la presentación de los documentos históricos.

## Nuevos conceptos de ingeniería

Las propiedades dependientes de T no son un modo seleccionable del gas perfecto, sino el único modelo activo en este repositorio. En ambas turbomáquinas los saltos energéticos se calculan con h(T), y el rendimiento únicamente se muestra en el dominio motor. A y B tienen relaciones óptimas diferentes; el caso base ofrece aproximadamente 402.071 kJ/kg y 34.893 % a rp=10, máximo A 414.086 kJ/kg en rp≈15.878 y máximo B 43.745 % en rp≈46.819.

## Nuevos conceptos de Python

Separa la conversión de un formulario, el cálculo reutilizable y la presentación. El parámetro Jinja `modo_cp` permite mantener una sola plantilla con la vista variable activa y lectura fiel de informes históricos, sin ejecutar ecuaciones en JavaScript. La lista `campos_cp` alimenta un bucle de inputs. La ruta POST rechaza acciones que aún apuntarían a los algoritmos de propiedades constantes, manteniendo los componentes físicos independientes de Flask.

## Qué hemos aprendido

Una interfaz puede conservar la apariencia aunque se sustituya su proveedor científico. La compatibilidad de lectura de informes históricos no exige mantener habilitados sus cálculos. Las antiguas regresiones HTTP sobre creación de informes ya no representan el contrato del dashboard; las pruebas de la nueva ruta deben contrastar los módulos científicos y la no ejecución de rutas obsoletas.

## Limitaciones que siguen existiendo

No se han adaptado sensibilidad OFAT, mapa rp–T3, exergía ni exportación de nuevos informes con cp(T). Los archivos de informes antiguos pertenecen al gas perfecto. El diagrama T–s tiene trayectorias esquemáticas. Las pruebas HTTP no sustituyen una inspección completa del navegador ni validación experimental. Algunos tests históricos de rutas de escritura de informes del modelo antiguo requieren ser archivados o adaptados al nuevo contrato; no se les atribuye éxito sin ejecutarlos.

## Verificación

Pruebas locales previstas/ejecutadas: `test_cp_variable_web.py` (10), `test_web_app.py` (7) y `test_dashboard.py` (15); CI definitivo debe confirmar el mismo conjunto. La ejecución temporal del workflow se registrará mediante su enlace después de comprobarla. La integridad de los módulos científicos anteriores se compara por hash de blob antes de publicar.

## Commit asociado

Pendiente hasta que GitHub confirme la publicación. Mensaje previsto: `refactor: unify variable-cp simulator into main dashboard`.
