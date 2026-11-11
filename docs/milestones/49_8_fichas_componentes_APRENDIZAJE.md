# Aprendizaje 49.8 — Cómo llevar los resultados del motor a cada pieza

## Base y pregunta de ingeniería (10-11-2026)

Partimos del milestone 49.7 publicado en
`55f49ccf1b3c82d0f29eb59c383cfe21b50df4d7`, rama
`mejoras/cp-variable`. Su esquema era seleccionable, pero las fichas
no contenían magnitudes. Queremos saber **qué está pasando realmente**
en compresor, cámara, turbina, eje y tobera sin inventar datos.

## Cómo circulan los datos

1. El formulario conserva Mach, T3 y demás entradas.
2. `api_turborreactor_simular` llama una vez a
   `simular_turborreactor(valores)` y después a
   `preparar_vista_turborreactor(resultado)`.
3. El adaptador llama `fichas_componentes_49_8(resultado)`, que lee
   **los diccionarios del resultado ya resuelto**.
4. Flask entrega `componentes` junto a las magnitudes y SVG anteriores.
5. JavaScript conserva `seleccionActual` y actualiza solo la ficha
   visible; ninguna selección llama a la API.

## Función Python nueva

`fichas_componentes_49_8(resultado)`:

- **Entrada:** `resultado: dict`, salida de un cálculo válido del
  turborreactor; contiene `ambiente`, `remanso`, `difusor`, `compresor`,
  `combustor`, `turbina`, `tobera`, `diagnosticos` y, según modalidad,
  `prestaciones_absolutas`, `dimensionamiento_tobera` o `motor_acoplado`.
- **Salida:** `dict[str, list[dict]]`, seis claves con filas de cinco
  campos: `etiqueta`, `valor` (float/str/None), `unidad`, `clase` y `origen`.
- **Unidades:** K, kPa, m/s, kg/s, m², rpm, kJ/kg aire, kW o
  magnitudes adimensionales, siempre indicadas en cada fila.
- **Validación:** reutiliza un resultado que ya ha superado las
  validaciones del solucionador; los datos opcionales ausentes son
  `None`. No crea estados de flujo ni ignora errores del backend.
- **Llamada:** `preparar_vista_turborreactor(resultado)`; la API toma
  directamente el bloque de la vista. No realiza llamadas salientes.
- **Ejemplo:** `fichas_componentes_49_8(resultado)['compresor']`
  contiene la temperatura total de entrada `compresor.T1` y la de salida
  `compresor.T2`, junto con presión y trabajo específico.

Los pequeños auxiliares `fila`, `tot`, `est`, `op` declarados dentro de
la función evitan repetir la creación de diccionarios: es un ejemplo
de *funciones locales* en Python. Una comprensión de diccionario no es
necesaria; se usan filas explícitas para verificar su procedencia.

## JavaScript y estado de la interfaz

`iniciarEsquemaEducativo49_7(documento)` mantiene su nombre y firma.
Devuelve un objeto ampliado con métodos:

- `seleccionar(clave: string): boolean`: cambia la pieza visible.
- `cambiarApartado(clave: string): boolean`: cambia entre
  funcionamiento, resultados y ecuaciones sin red.
- `actualizar(datos: object): void`: recibe la respuesta JSON con
  `datos.componentes`, construye filas DOM con `createElement` y
  `textContent`, manteniendo pieza y apartado.
- `pendiente(mensaje: string): void`: borra inmediatamente cifras
  del caso anterior y anuncia la indisponibilidad temporal.

No hay unidades en el estado visual; las unidades viven en las filas
calculadas. Los eventos de teclado/clic seleccionan componentes y
apartados, no desencadenan el solucionador. El controlador M48
actualiza al variar entradas y llama `actualizar` solo ante resultados
válidos. Si Flask renderizó el cálculo mediante POST completo, un
`<script type="application/json">` permite leer esos mismos datos
sin una segunda petición.

## Interpretación física y estaciones

| Interna | Interpretación | Convención aproximada |
| --- | --- | --- |
| T1/p1 | Entrada de compresor, tras difusor | Tt2/pt2 |
| T2/p2 | Salida de compresor, entrada de cámara | Tt3/pt3 |
| T3/p3 | Salida de cámara, entrada de turbina | Tt4/pt4 |
| T4/p4 | Salida de turbina, entrada de tobera | Tt5/pt5 |

Estas correspondencias dependen de la convención adoptada y **no
renombran** las variables internas. En el núcleo, T y p son **totales**.
No podemos calcular la temperatura **estática** de una etapa interna a
partir de la total sin velocidad/entalpía cinética local; por eso no se
inventa. Los estados de garganta y salida de tobera, cuando existen,
sí son estáticos.

### Ecuaciones esenciales utilizadas

- **Compresor:** `wc = h(T2) − h(T1)` [kJ/kg aire]; la entalpía h(T)
  procede de cp(T), no de multiplicar por un cp constante.
- **Cámara:** `h2 + ηb·f·PCI = (1+f)·h3`; el combustible es un
  aporte energético equivalente y la base es kg de aire.
- **Turbina:** `wt = (1+f)(h3−h4)` [kJ/kg aire].
- **Eje:** `ηm·wt = wc`; al conocer caudal de aire,
  `P = ṁaire·ηm·wt` [kW]. Sin caudal no existe P calculada.
- **Tobera:** `ht,e = he + Ve²/2000` [kJ/kg gas]; los valores estáticos
  de salida corresponden al modelo de tobera resuelto.

El esquema no modifica ninguna de estas relaciones físicas. La tabla
de procedencia más detallada está en el documento técnico 49.8.

## Experimentos educativos

1. Elige compresor, consulta temperaturas **totales** y modifica Mach.
   Mantén la selección: la ficha queda pendiente y luego muestra el
   nuevo resultado calculado.
2. Elige eje en A sin caudal absoluto: no hay potencia ni rpm ficticias.
   En C, el régimen procede del acoplamiento de mapas.
3. Compara las magnitudes totales de entrada a tobera con su salida
   **estática**; son estados diferentes, no valores intercambiables.

## Pruebas y estado de entrega

`tests/test_fichas_componentes_49_8.py` contrasta resultados y unidades
de A/B/C y tobera C-D. `tests/js/test_fichas_componentes_49_8.cjs`
verifica la permanencia de selección, el cambio de apartados y la
eliminación de datos obsoletos. Las pruebas constituyen verificación
del software, no validación física experimental.

En Windows, 11-11-2026, pasaron las 6 pruebas focalizadas y los 11 tests
JavaScript; `node --check` también pasó. La regresión completa ejecutó 788
pruebas: 778 correctas, 10 omitidas y 0 fallidas. El informe del ZIP reporta
787/1, con el mismo total. En este `.venv` faltan SciPy y Cantera, por lo que
se omiten ocho comprobaciones opcionales de SciPy y una de Cantera; además,
Windows omite una prueba de permisos para symlinks. No cambió el descubrimiento
ni se eliminaron pruebas. Flask queda disponible en
`http://127.0.0.1:5002/turborreactor/interactivo`; la inspección visual manual
queda pendiente del usuario. No se afirma validación experimental.

La fase queda **sin staging, commit ni push**. No se implementan los
milestones 49.9–50.2.
