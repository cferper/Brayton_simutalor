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

**24/10/2026, GitHub Actions, Python 3.11:** dependencias de `requirements.txt` instaladas; 6/6 pruebas `tests/test_cp_variable_web.py`, 11/11 regresiones `tests/test_web_app.py` y 15/15 `tests/test_dashboard.py`: **32/32 correctas**, sin fallos. Se ejecutaron sobre la rama `validacion/fase-2d-web-cp` y el árbol definitivo de Fase 2D. El caso base y ambos óptimos se contrastan con los módulos de cálculo en las pruebas web. Se registró `cp_variable_bp` en `web_app.py` y se añadió acceso por formulario GET en la página histórica; se preserva el carácter autocontenido de los informes anteriores. Los algoritmos 2A/2B/2C no se modificaron.

No existe validación experimental ni comprobación visual exhaustiva en navegador. Las pruebas comprueban integración HTTP, no la fidelidad de un motor real ni la estética en un navegador concreto.
