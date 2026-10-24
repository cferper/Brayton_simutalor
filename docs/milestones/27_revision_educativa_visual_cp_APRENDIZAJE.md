# Aprendizaje · Milestone 27, interfaz educativa cp(T)

Dirigido a un estudiante de 4.º de Ingeniería Aeroespacial con Python básico. La tarea cambia **cómo se explica y visualiza** un resultado, no cómo se calcula.

## 1. Separar tres responsabilidades

1. **Modelo:** `ciclo_cp_variable.py` evalúa estados, trabajo y calor mediante h(T) y s(T,p). `optimizacion_cp_variable.py` busca los óptimos A y B. Otros módulos resuelven OFAT, mapa y exergía.
2. **Presentación:** `educacion_cp_variable.py` contiene explicaciones de física y de uso. `dashboard.py` reúne contenido y resultados y lo pasa a la plantilla.
3. **Interacción:** `templates/index.html` muestra valores, unidades y diagramas; `static/dashboard.js` cambia pestañas y amplía gráficos sin ejecutar las ecuaciones.

Este reparto evita que una mejora educativa rompa una función de cálculo verificada y permite comprobar cada capa por separado.

## 2. Cómo llega una explicación a la pantalla

`CONTENIDOS['resultados']['fundamentos']` contiene cinco pares `(título, texto)`. `construir_educacion_cp()` recorre el diccionario con una comprensión:

```python
return {seccion: {
    'uso': _tarjeta('Qué vamos a hacer', item['uso']),
    'fundamentos': '<div class="edu-deep-grid">' + ... + '</div>',
} for seccion, item in CONTENIDOS.items()}
```

`dashboard.py` recibe ese diccionario y Jinja usa:

```jinja
{{ educacion_cp.resultados.fundamentos | safe }}
```

`safe` evita que Jinja escriba los signos de HTML como caracteres literales. Se utiliza **solo porque el contenido ha sido escrito dentro del código y no incluye texto del usuario**. Si se incorporara una nota editable en un futuro, debería escaparse antes de representarla; de otro modo habría riesgo de inyección HTML.

**Ejercicio:** añade mentalmente una novena sección al diccionario. ¿En qué tres lugares necesitarías conectarla (contenido, plantilla, navegación)? ¿Por qué el diccionario no basta para crear una ruta nueva automáticamente?

## 3. Fundamentos físicos que enseñamos

- **Simulación:** con ηc y ηt definidos respecto a compresión/expansión isentrópicas, no basta usar potencias de presión con un γ fijo; hay que resolver las ecuaciones de entropía y entalpía.
- **Resultados:** (w_c=h_2-h_1), (w_t=h_3-h_4), (w_{net}=w_t-w_c=q_{in}-q_{out}). La tabla permite relacionar propiedades con estados.
- **Optimización:** máximo de (w_{net}) y máximo de (eta=w_{net}/q_{in}) no son necesariamente la misma rp. La frontera abierta del dominio motor puede tener supremo, pero no máximo alcanzado.
- **Sensibilidad:** OFAT cambia solo un factor. La elasticidad (S=(x/Y)(dY/dx)) es local y adimensional; no es una variación en puntos porcentuales.
- **Mapa:** cada pareja (rp,T3) se resuelve como un ciclo. El mejor nodo de una malla finita no es necesariamente el óptimo continuo.
- **Segunda ley:** (e=(h-h_0)-T_0(s-s_0)) y (e_D=T_0 s_{gen}) miden potencial de trabajo destruido. La suma de compresor y turbina no es la exergía destruida total del sistema.

La sección Informes recuerda por qué comparar archivos históricos de gas perfecto con una ejecución cp(T) exige identificar los supuestos; Ayuda enseña unidades y limitaciones del modelo.

## 4. Una figura SVG sin crear otra gráfica

La función de trazado Python ya entrega un texto que empieza por `<svg ...>`. La macro de Jinja:

```jinja
{% macro grafica_cp(titulo, svg, explicacion) %}
  <figure class="cp-figure">
    <figcaption>{{ titulo }}</figcaption>
    <div class="cp-plot">{{ svg | safe }}</div>
    <p class="plot-help">{{ explicacion }}</p>
  </figure>
{% endmacro %}
```

No calcula datos. El CSS reduce la altura visible hasta 260 px; su `viewBox` original no cambia. En móvil una tarjeta ocupa toda la columna. La descripción de la figura explica aspectos que pueden malinterpretarse (segmentos esquemáticos, distintas escalas, celdas inválidas, sumas parciales).

El JavaScript identifica el elemento `img` o `svg` del `<figure>`. Para un SVG ejecuta `cloneNode(true)` y coloca el duplicado en un `<dialog>`. Al cerrar se elimina la copia; el gráfico de origen se conserva siempre. También se devuelve el foco al botón «Ampliar». **No requiere un segundo servidor, librería gráfica o cálculo Flask.**

## 5. Qué verifican los nuevos tests

Las pruebas inspeccionan HTML real renderizado por Flask en `app.test_client()`, no solo que exista texto fuente. Por ejemplo, un POST con parámetros conocidos debe seguir mostrando el mismo trabajo neto que `resolver_ciclo` y conservar un gráfico T–s ampliable. Otras pruebas hacen POST para OFAT, mapa y segunda ley y comprueban las tarjetas creadas. Tests de estructura verifican CSS de dos columnas y cambio a una, y las funciones JavaScript relacionadas con el modal.

**Límite de la verificación:** encontrar clases CSS, botones y SVG en el HTML no demuestra que la tipografía sea legible en un portátil de 13 pulgadas. Por eso se propone una revisión manual posterior en Windows.

## 6. Preguntas para afianzar

1. ¿Por qué no es correcto etiquetar una curva con `rendimiento=0` cuando el ciclo no es motor?
2. ¿Por qué añadir una gráfica de OFAT con parámetros fijos no prueba que hayas encontrado un óptimo continuo?
3. ¿Qué propiedad del SVG permite ampliarlo sin perder resolución como una imagen raster pequeña?
4. ¿Qué se podría romper si `safe` recibiera texto arbitrario de una entrada del usuario?
5. ¿Por qué cambia una destrucción (e_D) al cambiar T0 aunque no cambien las temperaturas 1–4?

**Resultado de la iteración:** se ha añadido una capa didáctica común a los ocho apartados y un visor para SVG, reutilizando todas las funciones científicas de las fases 2A–2G. El valor científico depende de los modelos, hipótesis y verificaciones originales; la interfaz ahora ayuda a leerlos sin sobreinterpretarlos.
