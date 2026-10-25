# Milestone 40 — Aprendizaje: la primera web del turborreactor

**Fase iniciada y documentada el 25/10/2026.** Base remota `mejoras/cp-variable` en `c0bce440882e31f10c1ad7dd95bfbc81825e142e`. Los modelos 34–39 ya existían. Este milestone presenta sus cálculos sin modificarlos. El commit propio está pendiente hasta publicar el cambio.

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
