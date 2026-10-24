# Aprendizaje de la Fase 2D — Del modelo físico a una página Flask

**Estado:** implementación web preparada, pendiente de integración en `web_app.py` y verificación con Flask. Base remota: `b72453f356a0cb73ec1f15a3e9ac19df1ca127d7`. Fecha de documentación: 24-10-2026.

## Interpretación física

El cálculo del ciclo no cambia: `resolver_ciclo` obtiene estados mediante `s0(T)` y diferencias de entalpía `h(T)` y clasifica el punto. `estudiar_cp_variable` halla el dominio motor y, por separado, el máximo de trabajo A y rendimiento B. La página **solo presenta** sus resultados; no sustituye el modelo por aproximaciones de gamma constante. Entalpías y trabajos se expresan en kJ/kg, entropías en kJ/(kg·K), cp en J/(kg·K), temperaturas K y presiones kPa.

El diagrama T–s identifica los estados reales 1–4 calculados. No es legítimo inferir una curva termodinámica exacta entre estados reales con solo una eficiencia isentrópica: harían falta hipótesis sobre disipación y presión en el interior del equipo. Por ello la línea de unión se rotula como **esquemática**. La cámara 2→3 sufre pérdida de presión si `delta>0`: no se debe calificar estrictamente de isobárica.

## Python y Flask

- **`Blueprint`**: encapsula rutas de una sección independiente para registrarlas con `app.register_blueprint(...)` en la aplicación existente.
- **`@cp_variable_bp.route('/modelo-cp-variable', methods=['GET','POST'])`**: en GET presenta valores de ejemplo; en POST `request.form` contiene cadenas que `leer_entradas` transforma a números finitos.
- **`render_template` + Jinja2**: pasa a HTML un diccionario de resultados reales, sin calcular termodinámica en JavaScript. Jinja escapa los valores del formulario por defecto; solo el SVG construido por funciones internas se presenta como contenido seguro.
- **Errores explícitos**: `ValueError` distingue entrada inválida, `EstadoFueraDeRango` indica imposibilidad de resolver en 200–2000 K, y `ErrorNumericoCiclo` avisa de fallos de convergencia/representación. `viable=False` es un **resultado**, no una excepción.
- **SVG generado desde Python**: una función convierte `(s,T)` de los cuatro estados a posiciones del dibujo. Las coordenadas geométricas no alteran la magnitud termodinámica. Los segmentos discontinuos representan únicamente la conectividad del ciclo.

## Funciones nuevas y contratos

`leer_entradas(form)` recibe un mapping de cadenas, devuelve un dict de siete `float` con unidades K/kPa/fracciones; `ValueError` por campo ausente, no numérico o no finito. Lo invoca la ruta.

`propiedades_estados(p)` recibe el diccionario de `resolver_ciclo`, devuelve cuatro diccionarios de estado con `cp`, `gamma`, `h`, `s`, `T`, `presion` y `numero`. Llama a `cp(T)` y `gamma(T)` de 2A. No cambia el ciclo.

`_escala(valor, low, high, inicio, ancho)` transforma linealmente una coordenada física numérica al sistema de coordenadas SVG. Solo la usan funciones gráficas; `max(high-low,1e-12)` evita división por cero en la presentación.

`svg_ts(p)` recibe el diccionario 2B, devuelve SVG `str` con cuatro estados y líneas esquemáticas; lo invoca la ruta.

`curvas_optimizacion(entradas, estudio, muestras=90)` recibe entradas validadas, dict 2C y número de puntos de muestreo; devuelve una lista de diccionarios `{'rp','trabajo','rendimiento'}` o `None` para puntos no evaluables. Llama a `resolver_ciclo` únicamente dentro del dominio motor. Los óptimos no dependen de esta malla.

`svg_optimizacion(curva, estudio)` devuelve SVG o `None`; traza tramos solo si existen datos físicos, dos escalas verticales normalizadas independientes y la abscisa log(rp). No infiere óptimos.

`modelo_cp_variable()` es la ruta GET/POST; no recibe argumentos explícitos y devuelve una respuesta Flask con HTTP 200 o 400. Llama a validación, solución 2B, optimización 2C, funciones de presentación y Jinja. Se registra bajo el Blueprint y se invoca desde navegador.

Ejemplo de llamada al motor físico que no depende de Flask:

```python
from ciclo_cp_variable import resolver_ciclo
p = resolver_ciclo(288.15, 1600, 10, 100, 0.85, 0.9, 0.05)
print(p['trabajo_neto'], p['rendimiento'])
```

## Prácticas de verificación

`tests/test_cp_variable_web.py` prepara solicitudes con `Flask.test_client()` sin iniciar servidor. Comprueba rutas, comparación de salidas con el motor, óptimos, límites, errores y regresión de `/`. Son pruebas **preparadas, no ejecutadas** porque falta Flask/Jinja2 en este entorno. Las 13 pruebas 2C sí se ejecutaron sin fallos. Una prueba web no demuestra validación experimental: verifica el paso de datos desde Python hasta la respuesta HTML.
