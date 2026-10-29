# Milestone 48.1 — Navegación principal y API de simulación

## Estado anterior

En el commit publicado **`a6cb03f843a2d3d6718155324ec198e55349d212`**, la portada `/` mostraba el ciclo Brayton y el turborreactor estaba en `/turborreactor`. Las modalidades A (caudal impuesto), B (geometría fija) y C (motor acoplado) se resolvían con un formulario HTML y recarga de página. Existían seis secciones de turborreactor, estudios independientes de sensibilidad y mapas, informes históricos, descargas y gráficos SVG.

## Implementación

| Ruta | Métodos | Comportamiento |
| --- | --- | --- |
| `/` | GET | HTTP 302 con `redirect(url_for('turborreactor'))` |
| `/turborreactor` | GET/POST | Formulario histórico y sus estudios sin modificar los solucionadores |
| `/brayton` | GET/POST | Dashboard histórico de Brayton, incluidos los formularios de estudio |
| `/api/turborreactor/simular` | POST | Una simulación principal A/B/C sin cálculo automático de OFAT/mapa |

`web_app.py` reutiliza `simular_turborreactor(valores)` y `preparar_vista_turborreactor(resultado)`, con idénticos modelos `cp(T)` y límites del milestone 47. `_render_turborreactor` centraliza el contexto de la misma plantilla Jinja para el POST tradicional y la API, evitando duplicar los cálculos o mantener componentes visuales distintos. La API acepta `application/json` (objeto plano con campos del formulario) o `application/x-www-form-urlencoded`/`multipart/form-data`. El cuerpo de respuesta se genera con `json.dumps(..., allow_nan=False)` para impedir NaN e infinitos no estándar.

## Contrato de respuesta de la API

Éxito (HTTP 200):

```json
{
  "ok": true,
  "modo": "impuesto",
  "magnitudes": {
    "empuje_especifico_neto": 0,
    "empuje_especifico_bruto": 0,
    "TSFC_kg_N_h": null,
    "empuje_absoluto_N": null,
    "gasto_masico_aire_kg_s": null,
    "gasto_masico_combustible_kg_s": null,
    "gasto_masico_gases_kg_s": null,
    "rpm_eje": null,
    "regimen_tobera": null
  },
  "estaciones": [],
  "diagnosticos": {},
  "svg": {},
  "html_documento": "..."
}
```

**Este bloque ilustra la estructura, no resultados termodinámicos calculados.** Las magnitudes reales se asignan desde el resultado físico de cada petición. Los campos no disponibles son JSON `null`, no cero; los empujes se expresan en N o N/(kg/s) según el nombre, los caudales en kg/s y el giro en rpm. `estaciones` contiene estado, tipo, T en K, p en kPa y h en kJ/kg. `svg` agrupa todas las cadenas SVG ya obtenidas por el presentador; `html_documento` es la página renderizada con la plantilla actual, de la cual el navegador podrá extraer las secciones principales. La API no devuelve gráficos de un barrido de sensibilidad o mapas nuevos: estos siguen siendo acciones POST tradicionales explícitas.

La entrega 48.2 añadió la clave `regimen_tobera` a las magnitudes para mostrar sin deducciones JavaScript el diagnóstico generado por Python. El resto del contrato de 48.1 permanece igual.

Error: `{"ok":false,"error":{"tipo":"formato|simulacion","mensaje":"..."},"modo":"..."}`; `modo` solo aparece cuando se ha podido interpretar la petición. HTTP **400**: JSON no objeto, campos desconocidos, valores estructurados o acción de estudio; **415**: tipo de contenido no permitido; **422**: validación numérica, régimen físico fuera de dominio o falta de convergencia. Nunca se fabrican resultados por sustitución silenciosa de una entrada. El adaptador `valores_turborreactor` sigue la misma semántica de campos faltantes que el POST tradicional.

## Límites y próximas tareas

- No se modifican ecuaciones de compresión, combustión, tobera, mapas o caudal, ni cambia el significado de A/B/C.
- El navegador **todavía no llama** a la API; el botón Simular, estudios y seis secciones permanecen operativos. La conexión con listeners, cancelación de solicitudes anteriores y actualizaciones parciales queda para **48.2**.
- `html_documento` prioriza reutilización sin refactorizar masivamente Jinja, a costa de transportar también HTML de navegación y contenidos educativos; una etapa posterior podrá optimizar el tamaño si existe motivo medido.
- Las pruebas HTTP requieren Flask/Jinja2; si no están instalados en el intérprete de desarrollo, la ejecución queda pendiente de Windows. Sin validación experimental del motor real.

## Commit asociado

Base comprobada: `a6cb03f843a2d3d6718155324ec198e55349d212` en `mejoras/cp-variable`. **Entrega 48.1 sin commit ni push.**
