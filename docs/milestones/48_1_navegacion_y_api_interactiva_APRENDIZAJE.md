# Aprendizaje 48.1 — De una página recargada a una API reutilizable

## ¿Qué había y qué cambia?

Hasta el milestone 47, al pulsar «Simular» el navegador enviaba el formulario y Flask devolvía una página HTML completa. Esa vía sigue funcionando. Ahora `/` conduce a `/turborreactor`, mientras `/brayton` conserva el ciclo original. Hemos añadido un *segundo modo de comunicación*, una API HTTP capaz de devolver datos sin exigir recargar el navegador. **No hemos conectado todavía escuchadores de cambios: eso es trabajo de 48.2.**

## Conceptos de Python y Flask

Una **ruta** asocia una dirección con una función. `@app.route('/brayton', methods=['GET','POST'])` permite que `index()` responda tanto al formulario inicial como a sus resultados. Para la portada usamos:

```python
@app.route('/')
def portada():
    return redirect(url_for('turborreactor'))
```

`url_for` pide a Flask la dirección actual de la función; es más resistente que repetir enlaces codificados. El navegador recibe un 302 y solicita `/turborreactor`.

La función `api_turborreactor_simular()` no recibe argumentos posicionales: Flask la llama en cada POST y lee `request`. Cuando el cuerpo es JSON, debe ser un **diccionario plano**; para un formulario se convierte `request.form` en un diccionario. La API solo acepta campos del simulador principal y permite `accion=simular`, pero nunca lanza sensibilidad ni mapa.

El flujo interno es:

1. `valores_turborreactor` conserva la semántica del formulario anterior.
2. `simular_turborreactor` calcula **una vez** el modo A, B o C.
3. `preparar_vista_turborreactor` obtiene estaciones y gráficos de ese mismo estado.
4. `_render_turborreactor` aplica la plantilla Jinja que ya se usaba con el botón tradicional.
5. `_respuesta_json_api` devuelve un objeto con números, diagnósticos, SVG y el HTML renderizado.

`_render_turborreactor(valores, resultado=None, vista=None, *, error=None, estudio=None, error_estudio=None, controles=None, accion=None)` devuelve una cadena HTML. Sus argumentos opcionales son contextos de presentación; no realiza ecuaciones de flujo. La marca `*` impide pasar inadvertidamente un error en la posición de un estudio.

`_respuesta_json_api(datos, estado=200)` devuelve un objeto `Response` con estado HTTP y MIME `application/json`. Utiliza `json.dumps(...,allow_nan=False)`: JSON estándar no admite `NaN` o infinitos de Python. Cuando falta una magnitud física, se entrega `null`.

## Ingeniería: por qué conservar el solucionador en Python

JavaScript será el medio de **presentar** resultados, no un segundo motor termodinámico. Las ecuaciones `cp(T)`, el balance del eje, las condiciones de bloqueo y los mapas de compresor/turbina permanecen en Python. Así un POST tradicional y la API no pueden divergir por aplicar modelos diferentes. Una solución física imposible devuelve un error explicativo y ninguna magnitud inventada. La verificación compara valores de la API con el simulador Python para el mismo conjunto de entradas; **no es validación experimental**.

## Ejemplo para experimentar cuando Flask esté disponible

```python
from web_app import app
from turborreactor_web import DEFAULTS_TURBO
cliente = app.test_client()
respuesta = cliente.post('/api/turborreactor/simular', data=DEFAULTS_TURBO)
datos = respuesta.get_json()
print(respuesta.status_code, datos['ok'])
print(datos['magnitudes']['empuje_especifico_neto'])
```

En modo A sin gasto impuesto, `empuje_absoluto_N` será `null`; esto no equivale a empuje nulo. En B se calcula el gasto compatible con el remanso y la garganta. En C se verifica el estado monoeje y se obtiene `rpm_eje` o un error de dominio.

## Verificación y límites

`tests/test_navegacion_api_48_1.py` incluye ocho métodos para navegación, Brayton original, A/B/C, vuelo, falta de convergencia/dominio y errores de formato. Las pruebas web históricas que dependían de la antigua portada se dirigen ahora a `/brayton`, sin alterar sus referencias físicas. La simulación automática en el navegador aún no existe; los campos dinámicos y los sliders esperan al milestone 48.2. Las limitaciones de entorno y resultados ejecutados se registran en el informe técnico.
