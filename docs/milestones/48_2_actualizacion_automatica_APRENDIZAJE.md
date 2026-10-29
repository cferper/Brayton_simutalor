# Aprendizaje 48.2 — Cómo responde un simulador sin recargar la página

## Una misma física, dos formas de interactuar

En el formulario tradicional, pulsar «Simular» envía los datos a Flask y se vuelve a dibujar la página. En modo interactivo, JavaScript envía los mismos campos a una API con `fetch`, recibe JSON y reemplaza únicamente los indicadores y gráficos necesarios. **Las ecuaciones siguen en Python**: el usuario no obtiene una segunda aproximación calculada por JavaScript.

## Eventos y sincronización

En HTML, `type="range"` es un deslizador, mientras `type="number"` permite escribir un número exacto. Los dos están asociados al mismo parámetro físico, por ejemplo Mach:

```javascript
deslizador.addEventListener('input', () => {
  numero.value = deslizador.value;
  lectura.textContent = numero.value + ' –';
});
```

La implementación real está en `acoplarControl48({numero,deslizador,lectura,unidad,onCambio})`, que sincroniza **en ambos sentidos**. Cuando un número se sale del muestreo del deslizador, no se cambia la cifra que ha escrito el usuario: solo se aproxima la posición visual del rango. El servidor mantiene la última palabra sobre su validez.

## Debounce y orden de respuestas

Si arrastramos Mach, el navegador podría generar decenas de eventos por segundo. `crearControlador48({solicitar,onEstado,onRespuesta,onError,demora=350,setTimer,clearTimer,Abort})` espera 350 ms desde el último movimiento. Si llega otro cambio, cancela el temporizador anterior. Si una petición ya está en vuelo, `AbortController` solicita cancelarla. Además compara el número de versión de la solicitud: aunque llegue una respuesta antigua tarde, **no puede sobrescribir** resultados nuevos.

Se distinguen claramente:

1. **Respuesta visual inmediata:** el texto del control enseña el Mach o T3 escrito.
2. **Estado actualizando:** se retiran los resultados anteriores y se espera al cálculo de Python.
3. **Respuesta física:** si Flask confirma la solución, se presentan conjuntamente nuevos números y SVG; si no, aparece un diagnóstico sin datos ficticios.

## JavaScript y Flask: funciones con papeles distintos

`inicializar48(documento, fetcher)` prepara los nodos de la página y conecta todo al formulario existente. La expresión `new FormData(formulario)` captura las entradas activas; `fetcher('/api/turborreactor/simular', {method:'POST',body:...,signal:...})` las transmite. La respuesta incluye `magnitudes`, `diagnosticos`, `svg` y `html_documento`. `DOMParser` transforma ese HTML de Jinja en nodos y el navegador copia los paneles sin producir datos físicos por su cuenta.

El servidor preserva los significados: A dimensiona a caudal impuesto, B calcula caudal de garganta fija y C busca equilibrio monoeje con mapas. Un `null` significa que no existe un valor disponible, no cero. Las temperaturas se muestran en K; los caudales en kg/s, el empuje en N, el empuje específico en N/(kg/s) y las revoluciones en rpm.

## Ejercicios y verificación

1. En modo A, escribe un Mach exacto, después cambia el deslizador. Comprueba que ambos controles muestran el mismo número cuando es representable.
2. Arrastra T3 rápidamente: la espera evita enviar todos los valores intermedios.
3. En C, prueba un punto fuera de los mapas. Debe aparecer un error, no un empuje ficticio ni resultados antiguos.
4. Utiliza el botón manual: debe seguir funcionando incluso con JavaScript desactivado.

Seis pruebas Node comprueban la lógica de eventos y orden de solicitudes. La ejecución HTTP y la inspección real de interfaz necesitan Flask y un navegador; si no se dispone de ellos aquí, quedan pendientes para la integración en Windows. **Verificar la interacción no equivale a validar experimentalmente el modelo del motor.**
