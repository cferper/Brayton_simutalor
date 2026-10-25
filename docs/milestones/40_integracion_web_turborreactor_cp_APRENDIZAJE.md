# Milestone 40 — Aprendizaje: la primera web del turborreactor

**Fase iniciada y documentada el 25/10/2026.** Base remota original `mejoras/cp-variable` en `c0bce440882e31f10c1ad7dd95bfbc81825e142e`, primera publicación M40 `96f75e683d888e76815d3c82ae97b2b8824dc9e0`. Los modelos 34–39 ya existían. Este milestone presenta sus cálculos sin modificarlos. La revisión posterior se realiza sobre dicho commit inicial de la interfaz.

## 1. Qué existía y qué problema resuelve la interfaz

El núcleo compresor-turbina, la tobera, el difusor de vuelo y el combustible eran módulos Python independientes. Había que conocer sus funciones para estudiarlos. Ahora una página separada `/turborreactor` permite experimentar con un motor hipotético, visualizar estados y explicar sus límites. Se conserva el dashboard Brayton de **ocho apartados**, que representa un problema termodinámico diferente: su turbina no está acoplada con la condición de potencia de un turborreactor.

## 2. El recorrido de una petición HTTP

1. `GET /turborreactor`: `web_app.turborreactor()` prepara las cadenas por defecto, no llama al motor ni genera prestaciones.
2. El usuario selecciona ambiente y modifica los campos. El navegador envía `POST` mediante un formulario HTML normal.
3. `valores_turborreactor(request.form)` conserva todas las cadenas, incluso si hay errores.
4. `leer_turborreactor(valores)` convierte sólo campos del modo activo y adapta `delta_pct/100`. Rechaza mezclas de ambiente, entradas vacías/no numéricas, NaN/infinito y porcentaje fuera de dominio.
5. `simular_turborreactor(valores)` llama **una sola vez** a `resolver_turborreactor_con_combustible(**argumentos)`; las ecuaciones siguen en `combustible_cp_variable.py`.
6. `preparar_vista_turborreactor(resultado)` ensambla seis estaciones y tres SVG. Finalmente `render_template` construye HTML escapando los valores del usuario.

La técnica se llama separación de responsabilidades: el motor responde qué ocurre físicamente; el adaptador presenta magnitudes; Flask traduce peticiones y respuestas; Jinja construye el HTML. Cambiar estilo no modifica la física.

## 3. ¿Por qué dos ambientes excluyentes?

El aire exterior puede definirse mediante dos números medidos (`T_amb` en K y `p_amb` en kPa) o por una altitud ISA [m] que aproxima ambos. Si se mezclan, una función podría ignorar silenciosamente datos contradictorios. Por eso el servidor comprueba que el modo `directo` exige T/p y altitud vacía; modo `ISA` exige altitud y T/p vacías. Con JavaScript se vacían/desactivan automáticamente los campos inactivos; sin él, pueden vaciarse manualmente. No se realizan cálculos al seleccionar ejemplos.

El Mach es adimensional: `V_inf=M_inf sqrt(gamma(T_inf)*R*T_inf)`. La energía cinética se convierte en entalpía total mediante `h(Tt0)=h(T_inf)+V_inf²/2000` porque h está en kJ/kg y la velocidad en m/s. El difusor mantiene Tt pero pierde presión total: `pt2=pi_d*pt0`.

## 4. Compresor, cámara y turbina

El compresor necesita trabajo `wc=h2-h1` [kJ/kg aire]. El combustible equivalente aporta `f*eta_b*PCI` [kJ/kg aire]. La masa después de la cámara es `(1+f)` kg de gas equivalente por cada kg de aire captado, de modo que:

`h2+f*eta_b*PCI=(1+f)*h3` y `f=(h3-h2)/(eta_b*PCI-h3)`.

La turbina acciona el compresor mediante un eje que pierde una pequeña parte de potencia: `eta_m*(1+f)*(h3-h4)=wc`. El núcleo ofrece una temperatura y presión **totales** de entrada a tobera; no es correcto identificarlas con la presión estática exterior ni con la presión **estática** de escape. A la salida de tobera `Ve²=2000*(ht-he)`, con `Te,pe` estáticos. La salida de una convergente está bloqueada cuando su Mach llega a uno; la presión de escape puede ser mayor que la exterior y aportar fuerza por presión.

## 5. De los flujos al empuje neto y al TSFC

El empuje bruto por caudal de aire incluye término de momento `(1+f)*Ve` y término por presión `(1+f)*1000*(pe-p_inf)/(rho_e*Ve)`, ambos en N/(kg/s). La resistencia del aire que entra es `V_inf`; por tanto `Fs=empuje_bruto−V_inf`. No se fuerza a ser positivo. Si no existe expansión, las velocidades y el empuje se dejan indefinidos; si el empuje neto es cero o negativo, `TSFC` se deja en `None`.

Con empuje positivo, `TSFC=3600*f/Fs` [kg/(N·h)]. El factor 3600 transforma segundos en horas. Una fuerza absoluta necesitaría el caudal másico de aire en kg/s, que este modelo no conoce.

## 6. Sintaxis Python: funciones y retornos

Todas las funciones nuevas están en `turborreactor_web.py`, salvo el controlador Flask en `web_app.py`:

| Función y firma completa | Argumentos → retorno / uso, errores y llamadas |
| --- | --- |
| `valores_turborreactor(formulario=None)` | `formulario`: `MultiDict` o mapping de cadenas, opcional; retorna `dict[str,str]` de valores preservados. La llama `web_app.turborreactor`; no calcula física ni emite errores propios. Ejemplo `valores_turborreactor()` devuelve Mach `"0"`. |
| `leer_turborreactor(valores)` | `dict[str,str]` → `dict` de reales en K, kPa, m, kJ/kg y eficiencias; conversión `delta_pct → delta` adimensional. La llama `simular_turborreactor`; lanza `ValueError` ante campos incompatibles, incompletos o no finitos. Ejemplo `leer_turborreactor(valores_turborreactor())['delta']==.04`. |
| `simular_turborreactor(valores)` | Dict de cadenas → dict científico completo con `ambiente`, `remanso`, `difusor`, `compresor`, `combustor`, `turbina`, `tobera`, `prestaciones`, `diagnosticos`. La llama la ruta; llama a `leer_turborreactor` y al motor M37, propagando validaciones físicas y numéricas. Ejemplo `simular_turborreactor(valores_turborreactor())['combustor']['f']≈.028028`. |
| `estaciones_turborreactor(resultado)` | Dict científico → lista de 6 dicts `{nombre,tipo,T,p,h}`, con K, kPa, kJ/kg. La llama `preparar_vista_turborreactor`, obtiene h desde `propiedades_aire.h` sin resolver nuevos estados; si no hay tobera marca su estación `None`. Requiere dict de salida válida del motor. |
| `svg_componentes()` | Sin argumentos → SVG `str` fijo con cinco componentes y eje. La llama `preparar_vista_turborreactor`; no tiene resultados físicos ni errores especiales. |
| `svg_evolucion(estaciones,clave,etiqueta,unidad)` | Lista de estaciones, clave `"T"`/`"p"`, texto de título y unidad → SVG `str` que grafica cuatro estados **totales**. La llama `preparar_vista_turborreactor`; requiere estaciones científicas válidas. Ejemplo `svg_evolucion(estaciones_turborreactor(r),'T','Temperatura total','K')`. |
| `preparar_vista_turborreactor(resultado)` | Dict científico → dict con `estaciones`, `svg_componentes`, `svg_temperaturas`, `svg_presiones`. La llama la ruta tras POST válido, y llama a las tres funciones anteriores. |
| `turborreactor()` | Ruta decorada `@app.route('/turborreactor', methods=['GET','POST'])`: sin argumentos explícitos, lee `flask.request`, devuelve HTML con código HTTP 200/400; llama a presentadores y `render_template`. Captura `ValueError`, `EstadoFueraDeRango`, `ErrorNumericoCiclo` y `ArithmeticError`; no expone traceback. |

La instrucción `**argumentos` expande un diccionario como argumentos **por nombre** de una función, por ejemplo `f(**{'mach':0})` equivale a `f(mach=0)`. `dict(DEFAULTS_TURBO)` crea una copia para que editar una respuesta no altere los predeterminados de la siguiente petición. `zip(nombres,etiquetas)` recorre listas a la vez y `enumerate` aporta el índice para situar componentes. En Jinja, `|safe` se limita a SVG creado internamente con números; para valores recibidos se mantiene el escape HTML automático.

## 7. Caso práctico y experimentos

Configura el caso estático, ejecuta y luego selecciona «Mach 0,7». Manteniendo la misma temperatura y presión exterior, compara empuje **bruto** y **neto**; este último resta V∞. Prueba `delta_pct=4` y `delta_pct=8` para observar que mayores pérdidas de presión pueden reducir el margen disponible de tobera. Cambia el modo a ISA, deja la altitud 10000 m y Mach 0,5; no confundas un empuje específico alto en aire tenue con empuje absoluto alto, ya que falta caudal másico.

Resultados calculados con parámetros comunes `rp=10, eta_c=.85, T3=1600, delta_pct=4, eta_t=.90, eta_m=.98, eta_n=.95, pi_d=1, eta_b=.99, PCI=43000`:

| Modo | Mach | Bruto | Neto | TSFC |
| --- | ---: | ---: | ---: | ---: |
| Directo, 288.15 K y 100 kPa | 0 | 958.257683 | 958.257683 | 0.105297 |
| Directo, 288.15 K y 100 kPa | 0.7 | 996.600204 | 758.381570 | 0.126252 |
| ISA, 10000 m | 0.5 | 1048.467227 | 898.674568 | 0.123240 |

Bruto/neto en N/(kg/s), TSFC en kg/(N·h). En los tres casos la tobera está bloqueada. Los números son verificación de software del modelo especificado, no validación experimental.

## 8. Comprobaciones y límites

Ejecutar `python -m unittest discover -s tests -p 'test_turborreactor_web_40.py' -q` y `python -m unittest discover -s tests -q` tras instalar `requirements.txt`. Las pruebas verifican ruta, unidades, modos incompatibles, escape HTML, estados estáticos/totales, resultados indefinidos, compatibilidad del dashboard y ausencia de cálculos GET. Los resultados finales constan en la entrega. No se instala dependencia nueva.

Se conservan los límites de M37: no hay geometría, caudal másico absoluto, combustión química, composición real de productos, mapas off-design ni entrada supersónica. Los SVG sólo representan tendencias de los estados calculados y no son diagramas de geometría real ni validación experimental. El ordenador Windows, `main` y el repositorio histórico permanecen fuera del alcance.

## 9. Iteración de revisión visual y educativa — 25/10/2026

**Motivo.** Tras sincronizar el primer milestone 40 en Windows se comprobó que las cinco secciones se encontraban apiladas. La rueda permitía recorrerlas sin utilizar el menú, mientras éste mantenía «Configuración» como selección estática. También se observaron SVG con texto demasiado pequeño en ventanas estrechas, explicaciones contextuales cortas, omisión de unidades en el desglose de empuje y mensajes genéricos para `rp=0`.

**Navegación actual.** La función local de JavaScript `elegir(id, moverFoco=false)` recibe un identificador de sección `str` y un booleano que indica si el cambio lo ha solicitado el usuario. No devuelve un valor: cambia el DOM. Si el `id` no está entre los cinco permitidos, selecciona Configuración. Su fragmento central es:

```javascript
paneles.forEach(p=>{p.hidden=p.id!==id;});
enlaces.forEach(a=>{
  if(a.getAttribute('href')==='#'+id)a.setAttribute('aria-current','page');
  else a.removeAttribute('aria-current');
});
```

La propiedad `hidden` retira los otros paneles del flujo visual y de la navegación por teclado; CSS refuerza su ocultación (`display:none!important`). Un `aria-current="page"` identifica para lectores de pantalla y visualmente la única selección activa. `querySelectorAll` devuelve listas de elementos; `forEach` aplica la operación a cada uno. La función `porUrl()` no recibe argumentos y devuelve la parte `str` después de `#` en `location.hash`. `sincronizarHistoria()` tampoco recibe argumentos ni retorna datos; lee el fragmento y llama a `elegir(..., true)`, y está conectada a `popstate` y `hashchange`. El manejador local de clic `(evento)=>{...}` recibe el evento del enlace, hace `preventDefault()`, registra `history.pushState` y selecciona el panel sin saltar a un elemento oculto. `focus({preventScroll:true})` coloca el foco en el encabezado, evitando un segundo salto vertical del navegador. Sólo se llama a `window.scrollTo({top:0,behavior:'auto'})` durante una navegación voluntaria, para empezar el panel por arriba.

**Cómo se elige la vista inicial.** El servidor sigue teniendo una sola ruta `turborreactor()` (contrato sin cambios). En la respuesta Jinja escribe `data-initial-panel="resultados"` si hubo POST exitoso, o `"configuracion"` en GET/error. Al cargar, el script prefiere un fragmento `#id` válido, o utiliza esta señal inicial. No hay almacenamiento persistente, sesiones ni peticiones AJAX. Al navegar dentro del HTML calculado se mantienen todos los números y las cadenas introducidas porque los otros paneles sólo están ocultos. Si JavaScript está deshabilitado **el formulario sigue funcionando y las cinco secciones quedan apiladas** como respaldo; en ese caso no existe navegación exclusiva, limitación intencionada de mejora progresiva.

**Legibilidad y teclado.** Antes, un SVG se reducía por completo al ancho de la tarjeta. Ahora la caja `.turbo-svg` admite `overflow-x:auto`, se puede enfocar (`tabindex="0"`, `role="region"`, `aria-label`) y el SVG conserva `min-width:660px`; en móvil se desplaza **sólo el gráfico**. La navegación entre paneles usa enlaces `<a href="#...">` activables con Enter, funciona en pantallas estrechas y actualiza su resalte. No se han cambiado las funciones físicas ni los puntos de los gráficos.

**Educación aplicada.** Los grupos de Configuración incorporan `<details><summary>...</summary>...</details>`: las descripciones de ambiente/Mach, compresor/cámara, eje/turbina/tobera y combustible aparecen bajo demanda sin alargar el formulario. Resultados explica `Fs=Fbruto/ṁaire−V∞` en N/(kg/s de aire), `TSFC=3600*f/Fs` sólo con Fs positivo, el significado de f, y por qué falta gasto másico para fuerza absoluta. Estaciones guía las seis transformaciones distinguiendo estados estáticos y totales. Visualizaciones explica qué representan las curvas de pₜ/Tₜ y el eje compresor-turbina. Fundamentos diferencia propiedades ideales y pérdidas no ideales prescritas, aire equivalente y gases reales, estudio de parámetros y un motor real fuera de diseño, y verificación numérica frente a validación experimental.

**Validación del formulario en Python.** Cambia el cuerpo de `leer_turborreactor(valores)`, pero no su firma ni retorno: tras convertir todos los campos finitos y **antes** de llamar a `resolver_turborreactor_con_combustible`, ahora ejecuta:

```python
if datos["rp"] <= 1:
    raise ValueError("La relación de compresión rp debe ser mayor que 1.")
```

Esta excepción es capturada por la ruta y aparece en Configuración, con estado HTTP 400 y las entradas originales intactas. El motor M37 conserva su propia validación científica. Ejemplo: un POST con `rp="0"` muestra ese mensaje y no llama al solucionador.

**Ejemplos y unidades.** Los presets conservan `pi_d=1` (difusor sin pérdida total idealizada); algunas referencias numéricas anteriores fijaban `pi_d=.97` en Mach .7 o `.98` a 10 km/Mach .5. No son contradicciones: se están comparando **configuraciones diferentes**. El desglose de cantidad de movimiento, sobrepresión y resistencia de entrada ahora indica explícitamente `N/(kg/s de aire)` en los tres sumandos.

**Pruebas.** `tests/test_turborreactor_web_40.py` amplía los casos GET/POST con pruebas de estructura de cinco secciones, selección inicial en HTML, señales de JS para historial y ocultación, accesibilidad de los SVG, `rp<=1`, contenido físico y conservación del POST sin JS. Se verificaron **27 pruebas específicas** y una suite de **532 pruebas descubiertas: 523 correctas, 9 omitidas opcionales y 0 fallidas**. Las pruebas estáticas de JS **no prueban que el navegador lo dibuje correctamente**; la inspección interactiva posterior en Windows sigue siendo recomendable. No se trata de validación experimental.
