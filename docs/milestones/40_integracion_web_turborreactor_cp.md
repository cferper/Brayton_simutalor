# Milestone 40 — Integración web de turborreactor cp(T)

## Estado anterior

En `mejoras/cp-variable`, commit remoto verificado `c0bce440882e31f10c1ad7dd95bfbc81825e142e`, existían los módulos científicos 34–39 y 505 pruebas; Flask sólo publicaba el dashboard Brayton de ocho secciones y los informes históricos en `/` y `/informes/<nombre>`. El modelo de combustible M37 no tenía pantalla propia.

## Qué se ha añadido

- Ruta GET/POST **`/turborreactor`**, en el **mismo servidor Flask del puerto 5000** (`web_app.py`), con `templates/turborreactor.html` y recursos CSS/JS independientes. Un enlace condicionado por `modo_cp and modo_local` en el dashboard activo lleva a la nueva página; no aparece en informes históricos.
- Adaptador `turborreactor_web.py` para constantes de formulario, lectura y conversión de porcentajes, una llamada a `resolver_turborreactor_con_combustible`, seis estaciones con tipo estático/remanso y tres SVG: componentes/eje, temperaturas totales y presiones totales de cuatro planos del núcleo. El SVG de esquema es conceptual, no a escala.
- Dos formas excluyentes de ambiente: valores estáticos directos `T_amb`, `p_amb`, o altitud geopotencial ISA (0–20 km). Hay catorce campos numéricos posibles (trece activos en modo directo o doce en modo ISA), más el selector de modo. Incluyen `mach`, `rp`, eficiencias, `delta_pct`, `T3` y `PCI`. Tres ejemplos de formulario sin cálculo automático.
- Resultados separados: empuje bruto, empuje neto, TSFC, f, velocidades, presión y temperatura de tobera, Mach de escape, presión total disponible de turbina; diagnósticos de tobera bloqueada, falta de expansión y empuje no positivo. Ninguna magnitud indefinida se sustituye por un número.
- Ocho apartados didácticos en «Fundamentos y procedimiento» más «Uso y configuración». El formulario funciona con POST sin JavaScript; JS mejora la selección de ambiente y carga de ejemplos. En la revisión del 25/10/2026 se dividieron las cinco secciones principales en pantallas independientes cuando hay JS; se amplió el contenido educativo contextual de cada una.
- Pruebas `tests/test_turborreactor_web_40.py`, documentación y CI dedicada.

## Nuevos conceptos de ingeniería

- Distinción de presiones **estáticas** exterior/salida de tobera y **totales** en difusor/compresor/cámara/turbina. No se presenta `p4` como presión estática de escape.
- Ecuación de balance y empuje del solucionador M37 (reutilizada, sin redefinición): `f=(h3−h2)/(eta_b*PCI−h3)`, `eta_m*(1+f)*(h3−h4)=wc`, `Fs=(1+f)*Ve−V_inf+(1+f)*1000*(pe−p_inf)/(rho_e*Ve)` [N/(kg/s)], `TSFC=3600*f/Fs` [kg/(N·h)] sólo con `Fs>0`.
- La pérdida de cámara se introduce en **%**, se adapta a fracción (`4 → 0.04`); `pi_d` es recuperación de presión total, no presión estática exterior.

## Nuevos conceptos de Python

- **Adaptador de presentación:** `leer_turborreactor(dict[str,str])` valida y convierte; `simular_turborreactor` llama una única vez al motor; `preparar_vista_turborreactor` transforma datos comprobados en estados y SVG. Flask sólo acepta la petición, maneja errores y presenta la plantilla Jinja2.
- **Mejora progresiva:** JS desactiva campos alternativos y rellena ejemplos; sin JS el HTML/POST conserva el funcionamiento (para ISA se dejan los dos campos directos vacíos). Con JS, las secciones de Configuración, Resultados, Estaciones, Visualizaciones y Fundamentos son **paneles exclusivos**: la rueda desplaza solo el panel activo; la barra lateral cambia de panel, foco y `aria-current`, y los enlaces `#id` respetan historial atrás/adelante. Sin JS, las cinco secciones permanecen en flujo vertical para no perder contenido. `request.form` se procesa en servidor y todas las entradas se validan de nuevo en el motor.
- **Seguridad de HTML:** Jinja escapa por defecto valores recibidos; `|safe` sólo se utiliza en tres SVG **construidos por el servidor a partir de números calculados o etiquetas fijas**. No se introducen SVG ni HTML del usuario.
- **Compatibilidad:** no se modifica el solucionador M37 ni los ocho paneles, ni el código de lectura/reproducción/descarga de informes. No hay nueva dependencia, servidor o formato histórico.

## Qué hemos aprendido

La presentación web de un cálculo de propulsión exige declarar el tipo de estado termodinámico, las unidades y los valores indefinidos; la seguridad de un formulario y el aislamiento de las ecuaciones son parte de su fiabilidad científica. Un gráfico de evolución del núcleo debe representar sólo propiedades totales; los extremos estáticos se muestran aparte en la tabla.

## Revisión funcional y educativa · 25/10/2026

Sobre el commit verificado del milestone 40 `96f75e683d888e76815d3c82ae97b2b8824dc9e0`, después de la inspección funcional en Windows, se realizaron las siguientes correcciones **sin modificar ningún motor científico**:

1. **Navegación:** `static/turborreactor.js` activa sólo la sección seleccionada, oculta las demás con la propiedad HTML `hidden`, actualiza `aria-current` y admite `#configuracion`, `#resultados`, `#estaciones`, `#graficas` y `#fundamentos`. Al recibir HTML nuevo tras POST, la etiqueta `<body data-initial-panel>` indica Resultados si el cálculo ha sido correcto y Configuración si hay un error. La navegación interna no recarga la página, por lo que mantiene parámetros y resultados. `pushState`, `popstate` y `hashchange` respetan atrás/adelante. Los enlaces y las secciones son accesibles con teclado, incluido el foco de título al cambiar de pantalla.
2. **Educación contextual:** Configuración incorpora cuatro bloques desplegables de parámetros físicos, resultados define magnitudes y criterios de TSFC, Estaciones incluye explicación del paso del aire y distingue estados estáticos/de remanso, Visualizaciones explica variables, unidades y eje mecánico; Fundamentos amplía la distinción entre idealizaciones, aire equivalente, verificación y validación y estudio de diseño.
3. **SVG y responsive:** `static/turborreactor.css` da a los SVG una anchura mínima de 660 px, con desplazamiento horizontal dentro de una región con `tabindex="0"` y nombre accesible. No provoca desplazamiento horizontal de toda la página. No cambian los puntos o ecuaciones representados.
4. **Unidades:** cada sumando del desglose de empuje muestra `N/(kg/s de aire)` y se explica su contribución al bruto/neto.
5. **Ejemplos:** los tres usan `pi_d=1` (difusor ideal), sin cambios. Se explica que algunas referencias M36/37 empleaban `0.97` en Mach 0.7 y `0.98` a 10 km/Mach 0.5.
6. **Validación específica:** `leer_turborreactor` rechaza `rp<=1` antes de invocar M37 con `ValueError('La relación de compresión rp debe ser mayor que 1.')`. La ruta devuelve HTTP 400 y conserva los valores introducidos. El solucionador científico sigue validando sus propios dominios.

Las pruebas añadidas comprueban estructura HTML, estado inicial declarado, contrato JS/CSS, SVG desplazable, errores, contenidos educativos y compatibilidad histórica. Pruebas ejecutadas el 25/10/2026 en entorno aislado: **27 específicas correctas**; suite general **532 descubiertas, 523 superadas, 9 omitidas opcionales y 0 fallidas**. Esta comprobación de estructura y código JavaScript **no equivale** a una inspección visual interactiva en un navegador real. El resto de pruebas científicas siguen siendo regresión y no validación experimental.

## Casos reproducibles

Valores comunes: `rp=10, eta_c=.85, T3=1600 K, delta_pct=4, eta_t=.90, eta_m=.98, eta_n=.95, pi_d=1, eta_b=.99, PCI=43000 kJ/kg`.

| Caso | Ambiente | Mach | Empuje bruto [N/(kg/s)] | Empuje neto [N/(kg/s)] | TSFC [kg/(N·h)] | Tobera |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Estático | 288.15 K; 100 kPa | 0 | 958.257683 | 958.257683 | 0.105297 | Bloqueada |
| Vuelo | 288.15 K; 100 kPa | 0.7 | 996.600204 | 758.381570 | 0.126252 | Bloqueada |
| ISA | 10 000 m geopotenciales | 0.5 | 1048.467227 | 898.674568 | 0.123240 | Bloqueada |

Estos números provienen de llamadas al **motor científico existente** en el entorno local de pruebas del milestone, no de ecuaciones duplicadas en Jinja. El ambiente ISA de 10 km tiene menor presión estática que el caso de superficie.

## Comprobaciones

Prueba específica: `python -m unittest discover -s tests -p 'test_turborreactor_web_40.py' -q`. Suite completa: `python -m unittest discover -s tests -q`. Los resultados finales se recogen en la entrega de este milestone. La verificación de interfaz y matemáticas no es validación física frente a motores experimentales.

## Limitaciones que siguen existiendo

No se dispone de gasto másico absoluto, geometría, mapas de compresor/turbina, química de combustión, composición real de gases ni empuje absoluto. La atmósfera ISA es simplificada; no hay entrada de vuelo supersónico. No se integran mapas de prestaciones o Pareto en la interfaz.

## Commit asociado

Pendiente de SHA definitivo hasta la publicación del commit coherente, según `AGENTS.md`.
