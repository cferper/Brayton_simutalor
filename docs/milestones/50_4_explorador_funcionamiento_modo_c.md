# Milestone 50.4 — Explorador avanzado del funcionamiento del motor acoplado

## Estado anterior y base

- Rama remota: `mejoras/cp-variable`.
- HEAD comprobado mediante GitHub el **12 de noviembre de 2026**: `460749bc92de7b7cfb660dbcf0f6606a7c521855` (M50.3 publicado).
- Base aportada: `Brayton_milestone_50_3(1).zip`, **ZIP incremental de 11 archivos**, íntegro. Sus archivos de código cotejados coinciden con los blobs del commit remoto. El documento técnico M50.3 del ZIP difiere del remoto (este último incluye una actualización sobre la integración en Windows); no se modifica ese documento como parte del 50.4.
- Restricción del entorno actual: no se dispone de la copia completa del repositorio ni de Flask. Los módulos M49.5 se han consultado en el commit remoto y preparado como archivos completos para el paquete incremental.
- No se ha modificado GitHub, creado commit, realizado push ni cambiado `main`.

## Estado anterior — M49.5 y M50.1–50.3

El estudio existente realiza barridos independientes Mach, T3 y mapas Mach–T3, con límites A/B de 21 puntos por curva y 11×11, y C de 9 por curva y 6×6. Ya proporciona empujes, TSFC, régimen de tobera, SVG discretos, superposición de curvas, CSV/PNG/SVG, cancelación de espera y advertencias de datos desactualizados. Su endpoint sigue siendo `POST /api/turborreactor/estudio`.

M50.1 conserva la referencia de comparación independientemente del punto actual; M50.2 calcula magnitudes corregidas y el mapa HPC; M50.3 proporciona configuraciones completas y diagnóstico basado en evidencias de error. **Nada de ello se sustituye ni se duplica.**

## Qué se ha añadido

1. **Resultados C completos por celda:** `caudal_aire`, `caudal_corregido`, `rpm`, `rpm_corregidas`, `relacion_compresion`, `rendimiento_compresor`, `rline`, `iteraciones` y `norma_residual`, además de empujes y TSFC ya disponibles. Se extraen del resultado M47 y de `diagnosticar_motor_50_2`, sin otro cálculo termodinámico. Las entradas completas, incluida la geometría, se guardan en `punto.entradas` únicamente en C.
2. **Clasificación conservadora:** el estado heredado (`valido`, `fuera_dominio`, `fallo_numerico`, `sin_solucion`) se conserva. C añade `clasificacion` con `convergencia_verificada`, `entrada_fuera_dominio`, `fuera_mapa`, `sin_convergencia_numerica`, `modelo_no_resuelto` o `causa_indeterminada`. `diagnostico` explica evidencia y limitación; `resumen.por_clasificacion` cuenta cada causa. La clasificación reutiliza `diagnosticar_fallo_50_3`, no infiere estabilidad física.
3. **Extensión del mismo visor M49.5:** selector de magnitudes (incluidas corregidas y residuo), mapa de categorías o valores numéricos, celdas discretas sin interpolación, consulta por ratón/teclado y panel de detalle que muestra constantes, datos disponibles, causas y entradas del estudio. CSV incluye campos M50.4 en C.
4. **Configuración inicial conocida:** el selector de base del estudio utiliza inicialmente la configuración de diseño C de M50.3, independiente del modo que esté actualmente en el banco. Puede elegirse «Controles actuales» para conservar los estudios A/B o explorar otro punto C. El cálculo sigue siendo manual, no se lanza al cambiar la visualización.
5. **Carga de punto válido C:** `brayton:aplicar-estudio-50-4` transfiere las entradas completas a `aplicarEjemplo50_3`, que sincroniza ambiente, tobera y controles Mach/T3 sin eventos propagados. También sincroniza el modo de formulario A/B→C mediante un evento local `change` no propagado. El controlador M48 se solicita **una sola vez**; conserva la referencia guardada por M50.1 y actualiza gráficos y mapa M50.2 tras recibir la nueva simulación. Si falla la simulación, el controlador original invalida los datos obsoletos.

## Modelo físico y ecuaciones

El punto C continúa siendo el equilibrio estacionario del modelo monoeje M47 con mapas escalados NASA T-MATS. La aceptación física y numérica es la del solucionador: continuidad del caudal de gases en turbina y tobera, cierre de potencia de eje, límites de propiedades y mapas, y norma residual normalizada de Newton. En M47, el criterio nominal es norma residual no superior a `2·10⁻⁷` y la aceptación también verifica cierres dimensionales. **M50.4 no modifica esa tolerancia ni recalcula los residuos**. Los valores de iteraciones y norma provienen del estado resuelto. La magnitud de flujo corregido usa los totales a la entrada del compresor y las referencias de M50.2; el giro corregido está disponible únicamente si M47 ha resuelto rpm.

No se deben interpretar la malla, Rline, el borde tabulado ni las celdas no convergidas como línea de surge, frontera de estabilidad o límite físico certificado. La falta de convergencia puede ser numérica o de alcance del modelo. Los casos A/B mantienen sus contratos y prestaciones anteriores.

## Archivos afectados

| Ruta | Cambio |
|---|---|
| `estudios_parametricos_49_5.py` | Añade extracción de magnitudes, diagnósticos, entradas completas y recuentos C |
| `static/estudios_parametricos_49_5.js` | Amplía el mismo visor y CSV; selecciona celdas y solicita cargar C |
| `templates/turborreactor.html` | Base inicial, nuevas métricas y panel detallado del estudio |
| `static/turborreactor.css` | Estilos del panel y control de carga |
| `static/configuraciones_modo_c_50_3.js` | Expone el cargador completo ya implementado |
| `static/turborreactor_interactivo.js` | Un solo paso de aplicación y una simulación del controlador original |
| `tests/test_explorador_funcionamiento_50_4.py` | Pruebas reales de mallas, estado, consistencia, modos A/B y HTTP |
| `tests/js/test_explorador_funcionamiento_50_4.cjs` | Pruebas unitarias JS de CSV, clasificación, aplicación única y compatibilidad |
| `CODE_WALKTHROUGH.md` | Actualiza contrato actual del estudio y describe la ampliación |
| `docs/milestones/50_4_explorador_funcionamiento_modo_c_APRENDIZAJE.md` | Guía educativa independiente |

## Pruebas ejecutadas y alcance

**Ejecutadas en el entorno de entrega (12-11-2026):**

- Integridad de ZIP M50.3 aportado: correcta (11 entradas, sin corrupción).
- Comprobación de identidad de archivos críticos contra GitHub: positiva; el documento técnico M50.3 difiere del remoto y no se ha sobrescrito.
- Cinco controles locales de Python **con dependencias simuladas** sobre el módulo de orquestación: correctos. Verifican estructura, malla, constantes, fallos, nulos, A/B y rechazo de C no verificado. **No validan ecuaciones ni magnitudes con el solucionador real.**
- Nueve pruebas JavaScript (`node --test tests/js/*.cjs`): **9 correctas**, combinando cuatro regresiones del M50.3 y cinco nuevas del M50.4. Una expresión esperada de la prueba nueva se corrigió antes de la ejecución final. Incluyen extracción CSV, descripción, contrato del controlador y solicitud única de simulación.
- Comprobaciones de sintaxis Python (`py_compile`) y JavaScript (`node --check`): correctas para archivos de implementación.

**Pendiente durante el análisis del ZIP parcial:** mallas con solver real, comparación cuantitativa de empuje/rpm/TSFC, test HTTP Flask, regresión general y revisión visual. El intento de `unittest discover -s tests -q` sobre esa copia parcial no pudo importar dos módulos por ausencia de `acoplamiento_motor_mapa_47`; eso no fue un fallo físico ni una regresión del repositorio completo. Estas comprobaciones se completaron después sobre la integración completa en Windows; sus resultados constan en «Verificación local en Windows» más abajo.

## Limitaciones y tareas pendientes

- Un mapa de hasta 6×6 celdas conserva el coste M49.5. No se ha medido el tiempo real del nuevo barrido con el solver en Windows, por lo que no se aumenta el límite.
- La clasificación deriva de la evidencia textual reconocida por M50.3. Errores no identificables se marcan indeterminados, no como imposibilidad física.
- El gráfico de mapa de estados representa categorías discretas. Una celda con resultado convergido pero una magnitud individual ausente permanece disponible para consulta; no recibe valores inventados.
- El usuario aprobó la revisión visual de la integración en Windows. La verificación funcional y la regresión automatizada se resumen en «Verificación local en Windows»; la malla discreta no constituye validación experimental ni una envolvente continua.
- No existen nuevos commits del milestone 50.4; rama remota intacta al finalizar esta entrega.

## Verificación local en Windows (12-11-2026)

Sobre la integración completa, las 7 pruebas focalizadas Python pasaron y la
suite JavaScript completa quedó en 28/28. La regresión Python ejecutó 822
pruebas, con 812 correctas, 10 omitidas y ningún fallo. Las omisiones
corresponden a SciPy (8), Cantera (1) y permiso de symlinks (1). El cambio
pequeño de compatibilidad en `estudios_parametricos_49_5.js` evita acceder a
`options` en el DOM mínimo de pruebas; la inspección mostró que este mock no
definía esa propiedad. Se volvió a ejecutar toda la suite JavaScript y pasó.

Una malla Mach 0–0,4 por T3 1550–1650 K de 5×5 ejecutó 25 soluciones reales
en 8,246 s. Las 25 tuvieron `convergencia_verificada`, sin puntos fuera del
mapa ni fallos numéricos. Los índices 0, 12 y 24 coincidieron en rpm, caudal
y empuje con simulaciones individuales del mismo vector de entradas. Esta
malla discreta no establece una envolvente continua.

La prueba HTTP focalizada se ejecutó con Flask. El usuario completó y aprobó
la revisión visual de la interfaz.

## Commit asociado

Pendiente; el desarrollo se entrega sin commit ni push por solicitud expresa.
