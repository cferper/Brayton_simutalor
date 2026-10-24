# Fase 2D — Interfaz Flask del modelo cp(T)

## Base y alcance

Rama `mejoras/cp-variable`, punto de partida remoto confirmado `b72453f356a0cb73ec1f15a3e9ac19df1ca127d7` (24-10-2026). La aplicación histórica sigue resolviendo aire con cp/gamma constantes y mantiene su historial de informes. La nueva sección es independiente y no cambia `propiedades_aire.py`, `ciclo_cp_variable.py` ni `optimizacion_cp_variable.py`.

## Arquitectura preparada

`cp_variable_web.py` define el `Blueprint('cp_variable', __name__)`, ruta GET/POST `/modelo-cp-variable`. `web_app.py` debe registrar el blueprint, y la navegación debe enlazar la ruta sin eliminar la antigua. Plantilla `templates/cp_variable.html`: formulario, estados, prestaciones, explicación de cp(T), T–s y objetivos A/B. Datos y HTML permanecen separados de las ecuaciones del ciclo. El campo `delta` está expresado **en fracción**, al contrario que el campo de porcentaje del dashboard clásico, y se etiqueta explícitamente.

- Simulación `resolver_ciclo` con siete parámetros físicos; muestra cuatro estados (T,p,h,s,cp,gamma), T2s/T4s y energías en kJ/kg.
- Optimizaciones `estudiar_cp_variable` con distinción entre máximo interior alcanzado y supremo en frontera abierta. El barrido gráfico muestrea únicamente puntos físicos calculados en el dominio motor y deja huecos si no son evaluables.
- Diagrama T–s: coordenadas **exactas del modelo en los cuatro estados**; uniones por líneas discontinuas explícitamente **esquemáticas**. No se modelan trayectorias de máquinas reales ni la variación detallada de presión dentro de la cámara.
- Errores: entradas inválidas, estados fuera de los límites Shomate, ausencia de motor y error numérico, con mensajes sin trazas en página.

## Verificación y limitaciones de cierre

En esta sesión se han ejecutado las **13 pruebas de optimización 2C**, correctas (0 fallos); no se ha revalidado el conjunto 2A/2B ni el dashboard antiguo. No se han podido ejecutar las pruebas de integración `tests/test_cp_variable_web.py`, porque el intérprete actual carece de Flask/Jinja2 y la red impide instalar Flask temporalmente. Por ello **no se autoriza publicación de esta versión preparada** ni se afirma que la interfaz web sea operativa. Debe ensayarse con `Flask.test_client()` sobre un repositorio completo, incluida la regresión de la ruta `/` y la generación de resultados.

No existe validación experimental ni verificación visual en navegador. El estilo de la plantilla reutiliza el CSS del proyecto y ajustes de presentación acotados a la nueva página. La integración del registro del Blueprint y enlace de navegación continúa pendiente de aplicar al archivo `web_app.py` exacto antes de publicación.
