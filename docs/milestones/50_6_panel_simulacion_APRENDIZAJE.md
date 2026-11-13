# Aprendizaje — Milestone 50.6: Simulación eficiente y un solo estado

**Fecha de trabajo:** 12-11-2026. **Base:** `dd31bad020427d58c26ac0d1683ece5bbb05f3c5`, rama `mejoras/cp-variable`, M50.5 publicado. **Estado:** desarrollo sin commit; pruebas integrales en Windows pendientes.

## 1. Qué problema estamos resolviendo

M50.5 divide el banco en siete espacios. En el de Simulación, M48 seguía mostrando un formulario largo que tenía un scroll propio. Se cambiaban Mach y T3, pero había que recorrer grupos grandes para ver el caudal, los resultados y la gráfica; el visor SVG incluso estaba oculto en este espacio. Nuestro objetivo no es reducir física ni documentación, sino **separar lo que se usa en cada operación de lo que se consulta ocasionalmente**, manteniendo exactamente los mismos controles y valores.

## 2. Correspondencia entre interfaz y modelo

- **Modo A (caudal impuesto):** el usuario prescribe el gasto de aire `gasto_masico_aire`; cuando no lo aporta, la fuerza absoluta no puede determinarse. El empuje específico puede existir, pero no se inventa un caudal para rellenar la tarjeta.
- **Modo B (geometría fija):** se prescribe una garganta y el modelo calcula el caudal compatible con el remanso y la tobera cuando existe solución.
- **Modo C (motor acoplado):** el mapa de turbomáquinas y los balances proporcionan caudal, rpm y relación de compresión. Mantiene las seis configuraciones comprobadas y el restablecimiento global del diseño; no hay aceleración por cerrar/abrir el panel avanzado.

**Mach** es adimensional y **T3** es la temperatura **total a la entrada de turbina**, en kelvin. El cambio de esas entradas obliga al cálculo existente; mirar otra gráfica no. Las cifras en tarjetas pertenecen a `datos.magnitudes` devuelto por Python; `null` no significa cero. Los valores marcados pendientes/error no deben tratarse como una solución vigente. Nada en M50.6 constituye validación experimental.

## 3. HTML: un solo formulario y un solo visor

La plantilla `templates/turborreactor.html` ya contiene `#turbo-form` y `#turbo-live`; estos IDs no cambian. Se añade solo un `<script defer>` específico de la vista interactiva. Como `defer` respeta el orden de los scripts, el módulo 50.6 se inicializa después de los controladores antiguos y mueve **los mismos nodos DOM**. No se reconstruye el formulario y no se crean duplicados ocultos con distintos valores.

Los campos `mach`, `T3`, `gasto_masico_aire`, `tipo_tobera`, `area_garganta_fija` y `area_salida_fija` conservan su `name`, `id`, atributos `data-*` y escuchas de eventos. El campo de ambiente directo/ISA y los parámetros de componentes permanecen dentro del formulario, en el grupo avanzado. El selector A/B/C y los botones C permanecen en la zona principal.

## 4. JavaScript: qué hace y por qué

### `iniciarPanelSimulacion50_6(documento)`

- **Argumento:** `documento`, objeto `Document` que contiene los elementos HTML del banco interactivo.
- **Retorno:** `null` cuando se usa la ruta clásica, faltan los elementos requeridos o ya se inicializó; en caso contrario `{formulario, visor, principales, porModo}`, con cuatro referencias a elementos del DOM, sin unidades físicas.
- **Función:** busca nodos, los mueve al nuevo contenedor, oculta la guía histórica detrás de un `<details>` reutilizando su contenido, incorpora títulos y activa una clase CSS. **No llama al servidor, no calcula el motor y no modifica campos de entrada.**
- **Dependencias:** usa `documento.getElementById`, `querySelector`, `closest`, `documento.createElement`, `append`, `insertAdjacentElement`, `classList.add` y `dataset`. Es invocada automáticamente desde `DOMContentLoaded`. Los módulos M48 y M50.5 continúan siendo quienes utilizan `formulario` y `visor` para cálculo y navegación.
- **Errores:** si faltan controles esenciales, se devuelve `null` antes de mover cualquier campo; no se lanza una excepción por un DOM incompleto. Las validaciones físicas de números y límites siguen siendo responsabilidad de los módulos existentes y de Python.

**Fragmento real:**

```javascript
const ejes=documento.createElement('div');
ejes.className='turbo-sim-axes56';
ejes.append(mach,T3);
```

`append` **traslada** un elemento que ya tiene padre, no lo copia. Por tanto, el mismo `input` y el mismo `input[type=range]` mantienen sus valores y las funciones registradas con `addEventListener`. Este principio es distinto de `cloneNode`, que generaría otros controles e introduciría dos fuentes de verdad. Después de mover los nodos, el formulario sigue enviando los valores por `FormData(formulario)`.

La línea `if(form.dataset.simPanel56)return null;` evita repetir la preparación dos veces. `dataset` da acceso a los atributos `data-*`; un guard permite tener la misma página sin múltiples reorganizaciones. La condición `documento.body?.dataset.interfaz!=='interactivo'` utiliza encadenamiento opcional `?.` para no lanzar un error si falta el cuerpo del documento.

## 5. Configuración avanzada, CSS y responsive

Se reutiliza `#turbo-bank-advanced-toggle`: M48 ya añade o retira la clase `turbo-bank-show-advanced` y actualiza `aria-expanded`. El nuevo CSS oculta el contenedor `#turbo-bank-advanced-fields` cuando no está abierto y lo revela con esa clase. Como no se eliminan ni reinician inputs, el contenido se conserva. La selección del modo A/B/C continúa ocultando y deshabilitando los campos que no correspondan, mediante los eventos ya instalados.

El layout emplea CSS Grid con dos columnas, una para los controles y otra para los resultados y su gráfica. Por debajo de **1100 px** pasa a una columna, y a **600 px** se simplifican las cuadrículas de controles y tarjetas. Para móviles cercanos a **390 px** las tarjetas y los modos se adaptan a la anchura disponible. Se elimina el scroll vertical interno del formulario para permitir desplazamiento natural de la página. Estos son puntos de ruptura de CSS, **no** anchuras verificadas visualmente.

La galería original `.turbo-live-plot-viewer` pasa a mostrarse también en Simulación; el módulo no crea SVG, no sustituye `data-plot-panel`, ni intercepta los botones de zoom/exportación. M50.5 sigue moviendo el mismo `#turbo-live` a Termodinámica/Tobera y devolviéndolo al espacio Simulación cuando se regresa. Las gráficas permanecen sincronizadas con el resultado físico compartido.

## 6. Ejemplo de recorrido de ejecución

1. Se carga la vista interactiva; M48 prepara el estado y M50.5 monta la navegación superior.
2. M50.6 mueve Mach/T3 a la zona principal y deja el resto detrás del desplegable.
3. El usuario selecciona C y carga un caso verificado. M50.3 rellena **el formulario original**, sin crear otro.
4. M48 utiliza el endpoint `/api/turborreactor/simular`, recibe magnitudes y SVG, y actualiza las tarjetas y el gráfico activo.
5. El usuario abre parámetros avanzados para consultar la presión ambiente: no se ejecuta una petición nueva.
6. El usuario navega a Comparador y vuelve: el laboratorio conserva su referencia. Cambiar la pestaña de la gráfica tampoco ejecuta una petición.

En el caso A sin gasto másico, no debe aparecer un empuje absoluto ficticio. En caso de error numérico del modo C, la norma residual o un mensaje de fallo tampoco se convierten en prestaciones. El cálculo M47 sigue siendo el único que decide la convergencia.

## 7. Comprobaciones, ejercicios y límites

### Integración en Windows · 12-11-2026

Pasaron 7 pruebas Python del 50.6 y 7 del 50.5. Node registró 30 pruebas correctas, incluidas 25 comprobaciones internas del 50.6 y 29 del 50.5. La regresión Python del repositorio completo ejecutó 836 pruebas, con 826 correctas, 10 omitidas y 0 fallos.

Con Flask y Chrome automatizado se comprobaron los modos A/B/C, los casos `diseno` y `vuelo04`, la recuperación tras HTTP 422 y la conservación de una referencia al navegar y recalcular. La galería permitió consultar un punto, cambiar de gráfica, ampliar, restaurar el zoom y generar SVG y PNG.

El formulario seguía heredando un límite de altura en escritorio. El selector CSS ahora incluye `data-active-workspace="simulacion"`, lo que aumenta su especificidad dentro de ese espacio y deja el desplazamiento vertical a la página. Se repitieron las 14 pruebas focalizadas y la comprobación de navegador a 1920, 1366, 768 y 390 px. La revisión visual queda a cargo del usuario.

**Ejercicios recomendados en Windows:** abrir 1366×768, alternar A/B/C, ocultar/mostrar el avanzado y verificar que `gasto_masico_aire`, áreas y ambiente conservan sus valores; cambiar T3 y leer el nuevo empuje; provocar un error de entrada y comprobar que se retiran datos desactualizados; visitar Termodinámica, volver a Simulación y cambiar de gráfico sin otra petición; guardar una referencia y comparar después con otro punto. Verificar también tablet/móvil y zoom 125 %.

**Limitaciones:** no se han cambiado las secciones del 50.7 ni la organización de Estudios/Comparador del 50.8. La reducción exacta del scroll y el comportamiento visual en dispositivos reales requieren validación visual. Este desarrollo verifica interfaces, no el comportamiento físico mediante datos de ensayo.
