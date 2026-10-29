# Milestone 49.1 — Tres accesos, un único simulador científico

## Punto de partida

Rama `mejoras/cp-variable`, copia acumulada de 48.1–48.3 verificada por presencia de API, controles, gestor de peticiones, pruebas y documentación. Base Git local `a6cb03f843a2d3d6718155324ec198e55349d212`; los desarrollos 48 y 49.1 permanecen sin commit en esta copia. No se ha clonado otra vez.

## Rutas

| Ruta | Vista | Comportamiento |
| --- | --- | --- |
| `/` | Portada | Redirige a `/turborreactor/interactivo` |
| `/turborreactor/interactivo` | Banco de ensayos | GET de configuración y simulación inicial automática con la API; POST manual disponible |
| `/turborreactor` | Clásico | Formulario completo, resultados, estaciones, gráficas, sensibilidad, mapas, ayuda y POST tradicional |
| `/brayton` | Ciclo Brayton | Simulador histórico original y sus POST |
| `/api/turborreactor/simular` | API compartida | JSON de una única simulación de A, B o C |

Las tres vistas muestran enlaces cruzados, con la página activa identificada mediante `aria-current="page"`. Solo las rutas del turborreactor comparten plantilla; el ciclo Brayton conserva la suya.

## Implementación

- `web_app.py`: dos reglas Flask con distinta ruta visual llaman a una misma función `turborreactor(interfaz="clasico")`; el argumento se transmite a `_render_turborreactor`. La ruta API no cambia.
- `templates/turborreactor.html`: decide encabezado, enlaces y destino del POST manual según `interfaz`. Mantiene todos los nodos `id="turbo-*"` para no romper los eventos del milestone 48.
- `static/turborreactor.css`: en la ruta interactiva muestra Configuración y el panel interactivo; conserva el resto del DOM como fuente de las sustituciones de resultados. En clásico no oculta nada nuevo.
- `templates/index.html`: añade los accesos cruzados en modo local y usa `/brayton` para el POST. El informe HTML autónomo no añade enlaces a rutas Flask inexistentes.
- `static/style.css`: estilos mínimos y accesibles del menú común.
- `tests/test_navegacion_49_1.py`: pruebas dirigidas de navegación, controles y API A/B/C.
- `tests/test_navegacion_api_48_1.py`: actualiza solo la redirección esperada.

## Hipótesis científicas y validación

No hay nuevas ecuaciones. Las modalidades A (caudal impuesto), B (geometría fija) y C (motor monoeje acoplado) siguen sus restricciones previas. Se conservan `mach` [–], `T3` [K] y el resto de parámetros del modelo, incluso cuando en la vista interactiva una parte del formulario sigue siendo tradicional. Las gráficas SVG y los indicadores los devuelve Python. Esta fase reorganiza presentación; no valida experimentalmente ningún motor.

## Verificación y limitaciones

- Se comprobó por inspección la continuidad de los ID y rutas de la API 48.
- Ocho pruebas Node de sincronización, temporización y cancelación: correctas.
- Sintaxis Python y diferencias de Git: sin errores.
- No se han ejecutado pruebas HTTP ni inspección visual: el intérprete disponible no tiene Flask ni Jinja2. Las pruebas nuevas quedan para Windows.

## Pendiente para el 49.2

La interfaz interactiva aún reutiliza íntegro el formulario de parámetros y los componentes existentes; solo se distingue su vista y navegación. El rediseño del banco, la disposición prioritaria de indicadores y los nuevos deslizadores se abordarán respectivamente en 49.2 y 49.3, no en este milestone.
