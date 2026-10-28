# Milestone 44.4 — Perfiles cuasiunidimensionales de tobera C-D

## Objetivo, partida y alcance

Última ampliación del milestone 44: transformar los estados discretos de la tobera del 44.2 en dos **perfiles físicos calculados** de número de Mach y presión estática en función de la relación geométrica de áreas `A/Ag`, **sin fabricar distancias axiales** ni interpolar propiedades de flujo entre dos estados de salida. Se conserva la representación discreta y todas las entregas 44.1–44.3.

La referencia científica es el solucionador publicado de la rama `mejoras/cp-variable`, commit `d61ef3795ae58027927adc5077409bb3dfe6b018`. Se partió de la copia acumulada de 44.1–44.3, no de una reconstrucción de memoria. No se han modificado los solucionadores anteriores ni realizado commit/push.

## Hipótesis y reutilización del cálculo

- Gas ideal equivalente con `cp(T)` variable y `R_AIRE` de `propiedades_aire.py`; funciones `h`, `s`, `s0`, `gamma`.
- Flujo estacionario, cuasiunidimensional, adiabático y sin trabajo en tobera; no se modelan fricción, separación, chorros libres ni capa límite.
- Regiones suaves isentrópicas; un choque normal, si existe, está definido exclusivamente por el modelo C-D ya resuelto.
- Dominio térmico 200–2000 K y estados finitos. No se extrapola fuera del dominio.

Se reutilizan en `tobera_convergente_divergente_cp.py` los auxiliares existentes `_estado`, `_sonico`, `_salida_area` y `_biseccion`. `_estado` evalúa densidad, presión, velocidad, Mach y caudal superficial `G=ρV`; `_salida_area` resuelve la rama supersónica prescrita. Para la rama subsónica se encierra con `_biseccion` la raíz `G(T,Tt,pt)=Gg/(A/Ag)` en `[T*,Tt]`. El perfil **no vuelve a localizar el choque**: utiliza el área y los estados calculados por `resolver_tobera_convergente_divergente`, que a su vez aplica `resolver_choque_normal` de `choque_normal_cp.py`.

## Ecuaciones y escala geométrica

Para cada punto estático (T,p,V,ρ), se conservan:

\[
h(T_t)=h(T)+\frac{V^2}{2000},\qquad
\rho=\frac{1000p}{RT},\qquad
G=\rho V,\qquad G\frac{A}{A_g}=G_g.
\]

`h` está en kJ/kg; `p` en kPa, `R` en J/(kg·K), `V` en m/s, `G` en kg/(m²·s). El factor 2000 convierte energía cinética a kJ/kg. En una región isentrópica `s(T,p)=s(Tt,pt)` y la presión estática sale de `s0(T)-R ln(p)`; no se utiliza la relación de potencias con γ constante.

Se usa **A/Ag como única abscisa física común**, `Ag` la garganta geométrica. El área crítica de **cada región** cumple:

\[
\frac{A}{A^*_{\text{región}}}=\frac{G^*_{\text{región}}}{G(A)},
\quad\frac{A_g}{A^*_{\text{región}}}=\frac{G^*_{\text{región}}}{G_g}.
\]

En garganta bloqueada previa al choque, `Ag=A*1` y `A/Ag=A/A*1`. Después de un choque, la presión total `pt2<pt1` reduce `G*2` y, para conservar el mismo caudal, **A*2>A*1**. Por tanto `A/A*2` y `A/Ag` ya no coinciden. La implementación registra ambos factores de conversión sin desplazar gráficamente el choque ni intercambiar escalas.

## Regímenes y muestreo

`perfil_tobera_cp_variable(resultado, *, puntos_por_region=41)` recibe el diccionario científico completo y devuelve `disponible`, `motivo`, `regimen`, `segmentos` (tuplas de estados calculados), `choque` opcional (dos estados), `p_ambiente`, `relacion_areas`, `flujo_masico_por_garganta` y `area_critica` (`antes`, `despues`). El número de puntos debe ser entero entre 3 y 121, con ambos extremos incluidos por segmento.

Cada punto registra `area_relativa`, `temperatura`, `presion`, `densidad`, `velocidad`, `mach`, `entalpia`, `entropia`, `flujo_masico_por_area`, `flujo_masico_por_garganta`, `residuo_energia`, `residuo_entropia`, `area_sobre_critica`, `presion_remanso_region`, `rama` y `papel`.

| Régimen de la C-D | Perfil | Tratamiento de extremos |
|---|---|---|
| `supersonico_ideal` / `supersonico_sobreexpandido_ideal` | Garganta sónica y rama divergente supersónica | Extremo de salida igual al solver; no se inventa choque exterior ni separación |
| `subsonico_no_bloqueado` | Garganta y divergente subsónicas | No se fija M=1; caudal objetivo a partir de `Gg` real |
| `bloqueado_salida_subsonica_limite` | Garganta sónica y divergente subsónica | Se conserva la rama límite y se evita proyectarla erróneamente en la supersónica |
| `choque_normal_interno` | Supersónica hasta `As/Ag`, dos estados del choque y subsónica posterior | Dos segmentos independientes: no hay polilínea suave a través de choque; `pt2` se utiliza aguas abajo |
| `choque_normal_salida` | Supersónica interna y dos estados distintos en el plano de salida | El estado posterior se representa como punto, sin prolongar artificialmente fuera de la tobera |
| Convergente, C-D sin salida resuelta, `Ae/Ag=1` | Perfil no disponible con motivo | Permanecen los estados discretos del 44.2 y diagnósticos físicos |

El muestreo es uniforme **solo en la coordenada `A/Ag`**; se resuelven por separado las ecuaciones de estado y caudal para cada abscisa. Se calculan de nuevo entre 3 y 121 puntos por segmento; no se utiliza interpolación de Mach o presión. Para cada región se comprueba masa (tolerancia relativa 2×10⁻⁶), residuos de energía (1×10⁻⁷ kJ/kg) y entropía (1×10⁻⁸ kJ/(kg·K)). Se verifica además la coincidencia de Mach y presión de salida con el solucionador original (1×10⁻⁵ absoluto/relativo según magnitud). Estos umbrales **verifican el adaptador nuevo**; no alteran las tolerancias del solver.

## Integración y representación

`turborreactor_web.py` llama al nuevo módulo desde `preparar_vista_turborreactor` y añade `perfil_tobera`, `svg_mach_perfil_tobera` y `svg_presion_perfil_tobera`. `svg_perfil_tobera(datos,magnitud)` genera SVG con el mismo eje A/Ag para Mach y p; ambos usan exactamente los mismos segmentos de estado, colores por rama y salto de choque punteado en la misma posición. Se dibujan las referencias M=1 y p ambiente. En `templates/turborreactor.html` se sitúan en «Visualizaciones y transformaciones», con explicaciones breves. Las gráficas discretas 44.2 **permanecen visibles** como contraste de sus extremos.

La nueva curva no representa una distribución axial ni la posición absoluta del choque en metros. El trazado entre puntos es únicamente la presentación de una sucesión de **soluciones calculadas** en áreas intermedias.

## Casos reproducibles

Usando `resolver_tobera_convergente_divergente(1200 K, 500 kPa, p_amb, 1.5)` y `puntos_por_region=41`:

| p ambiente [kPa] | Régimen | Garganta M | Salida M | Presión salida [kPa] | Detalle |
|---:|---|---:|---:|---:|---|
| 50 | Supersónico ideal | 1,000000 | 1,824570 | 84,122 | Sin choque |
| 350 | Choque interno | 1,000000 | 0,543161 | 350,000 | As/Ag≈1,362058; antes M≈1,70190, p≈102,015; después M≈0,63448, p≈327,088 |
| 490 | Subsónico no bloqueado | 0,268686 | 0,174908 | 490,000 | Ag/A*≈2,267569; sin garganta sónica |

En el choque a 350 kPa, `Ag/A*2≈0,847456` mientras `Ag/A*1=1`. La diferencia responde a la caída de presión total y no a una variación de geometría física.

## Verificación previa del desarrollo — 27/10/2026

Los resultados y limitaciones siguientes son antecedentes de desarrollo; la revisión local Windows se registra más abajo.

- Pruebas específicas: `python3 -m unittest -q tests.test_perfiles_tobera_44_4`: **16 correctas, cero fallos, errores u omisiones**. Cubren masa, energía, entropía, regímenes, extremos, choque interno y en salida, pérdida de pt y crecimiento de s, área crítica posterior, dominio, discretización 11 frente a 61 puntos, SVG, cambio de parámetros y preservación de entregas previas.
- Regresión científica ampliada de entregas 44.1–44.4 y módulos 35, 37–39 y 42: **141 métodos, 140 correctos, 0 fallos, 0 errores, 1 omisión**. La única omisión es la comparación opcional con Cantera no instalada. La lista de módulos y comando completo figuran en la sección 4.84 de `CODE_WALKTHROUGH.md`.
- Ambas salidas SVG para un choque interno se exportaron y observaron como imágenes, sin detectar trayectorias continuas falsas.
- No se dispone de Flask/Jinja2 en este entorno; por instrucción no se instalaron. La prueba visual completa en navegador, la compilación Jinja en ejecución y la regresión web general deben repetirse en Windows tras integrar el ZIP. Esta copia de revisión no contiene toda la suite histórica, por lo que no se presenta la batería como regresión total del proyecto.

**Verificación no equivale a validación:** la coincidencia con el solver y las leyes discretizadas corrobora la implementación, no acredita datos de ensayo ni exactitud de flujo tridimensional real.

## Problemas conocidos y trabajo pendiente

- En tobera convergente faltan áreas de secciones internas: solo estaciones discretas.
- `Ae/Ag=1` no define una expansión divergente que representar.
- No se modelan ubicación axial del choque, oblicuos/exteriores, separación, pérdidas distribuidas, mezcla del combustible ni propiedades variables de composición.
- Las curvas se restringen al dominio 200–2000 K; si el solver no resuelve la tobera, no se inventan puntos.
- La revisión Windows de los casos y tamaños indicados más abajo está completada; no cubre todos los navegadores ni todo el dominio de entradas.

## Integración Windows y revisión completa — cierre 28/10/2026

### Base verificada y comparación segura

Rama inicial y final: `mejoras/cp-variable`; HEAD sin cambios:
`d61ef3795ae58027927adc5077409bb3dfe6b018`
(`feat: add milestone 43 educational turbojet interface`). Ya había cuatro
archivos versionados modificados por 44.1/44.2 y seis archivos nuevos de esa
entrega. También existían dos archivos personales no versionados.

Se usa exclusivamente el nuevo `milestone_44_completo_para_revision.zip`:
CRC correcto y exactamente las 16 rutas anunciadas, relativas, sin enlaces
simbólicos ni rutas de escape. Se extrae fuera del repositorio y se comparan
los archivos antes de copiar: **7 nuevos, 2 idénticos y 7 con trabajo local
previo**. La clasificación no presupone un árbol limpio.

- Nuevos: módulo de perfil, pruebas 44.3/44.4 y cuatro documentos 44.3/44.4.
- Idénticos: las pruebas entregadas de 44.1 y 44.2, sin volver a copiarlas.
- Adaptador y plantilla: se incorporan las ampliaciones del ZIP. La plantilla
  solo añade bloques; se conservan todas las funciones anteriores salvo la
  ampliación del preparador. `svg_ts_turborreactor` conserva exactamente el
  ajuste local de rótulo E, contorno blanco y altura de 420 px.
- Manual: conserva las explicaciones locales y añade 4.83/4.84 y la evolución
  correspondiente. Los cuatro documentos previos 44.1/44.2 se conservan byte
  a byte, incluidas sus comprobaciones Windows históricas.
- Excepción autorizada expresamente por el usuario: la prueba de M40 pasa de
  esperar 7 a **8** regiones SVG en el caso base. La C-D con perfil tiene 10;
  el caso base convergente no agrega esos dos perfiles. Se preservan foco,
  nombres accesibles y desplazamiento. No se cambia otra prueba histórica.

No hay cambios incompatibles pendientes ni pérdida de trabajo anterior.
No se modifican los solucionadores, ecuaciones, CSS, JS ni dependencias.

### Pruebas ejecutadas el 27/10/2026

Entorno: Python **3.13.0** de `.venv`, Windows **11 / 10.0.26300**.
Flask y Jinja2 ya estaban instalados. No se instalan paquetes. Para los
procesos de prueba se fijan `TMPDIR`, `TEMP` y `TMP` a una carpeta temporal
autorizada externa al repositorio; no se cambia la configuración persistente
Windows. Así se evitan las restricciones de temporales de la sandbox ya conocidas.

```powershell
.\.venv\Scripts\python.exe -B -m unittest -v tests.test_graficas_turborreactor_44_1 tests.test_graficas_tobera_44_2 tests.test_balance_energetico_turborreactor_44_3 tests.test_perfiles_tobera_44_4
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -q
.\.venv\Scripts\python.exe -B -m unittest -q tests.test_turborreactor_web_40 tests.test_prestaciones_turborreactor_web_41 tests.test_turborreactor_web_42b tests.test_turborreactor_web_43
```

| Batería | Total | Correctas | Fallos | Errores | Omisiones |
|---|---:|---:|---:|---:|---:|
| Específicas 44.1–44.4 (7+9+10+16) | 42 | 42 | 0 | 0 | 0 |
| Regresión vigente definitiva | 651 | 641 | 0 | 0 | 10 |
| Integración web M40/M41/M42.B/M43 | 74 | 74 | 0 | 0 | 0 |

La regresión definitiva dura 208.416 s. No se suman baterías solapadas.
Omisiones: ocho métodos de contraste con SciPy opcional ausente, uno con
Cantera opcional ausente y un subcaso que necesita crear enlace simbólico
sin privilegio Windows. El resto de comprobaciones del método parcialmente
omitido se mantiene. El perfil vigente carga su selección histórica existente;
no se descubre indiscriminadamente toda `legacy_tests`.

La primera regresión (202.114 s) había cargado la expectativa antigua de M40:
651 pruebas, 640 correctas, 1 fallo, 0 errores y 10 omisiones. Un diagnóstico
individual confirma `8 != 7`. Se aplica la corrección autorizada y se repite
la regresión completa, obteniendo el resultado definitivo anterior. La línea
de fuente del primer traceback puede mostrar el archivo ya corregido; el
proceso había cargado la constante 7 antes de esa edición.

### Casos científicos, HTTP y navegador

Ocho configuraciones cubren los nueve casos pedidos: el inicial es estático
y, a la vez, convergente bloqueado. Todos se reproducen desde el formulario
y también mediante el solucionador y el cliente Flask: ocho POST HTTP 200,
SVG idénticos a los generados por el presentador y XML bien formado. Se
contrastan empuje, cinco residuos, perfiles e invariantes regionales.

| Caso | Cambios sobre formulario inicial | Régimen | Mach salida | p salida [kPa] | Puntos de perfil |
|---|---|---|---:|---:|---:|
| estatico_bloqueado | Valores iniciales | bloqueado | 1.000000 | 216.986053 | 0 |
| vuelo | mach=0.7 | bloqueado | 1.000000 | 274.467801 | 0 |
| convergente_no_bloqueada | mach=0.9; rp=3; pi_d=0.7; T3=600 | no_bloqueado | 0.399724 | 100.000000 | 0 |
| cd_supersonica | tipo_tobera=convergente_divergente; epsilon=1.5 | supersonico_sobreexpandido_ideal | 1.821278 | 70.516456 | 41 |
| cd_subsonica | mach=0.9; rp=3; pi_d=0.7; T3=600; tipo_tobera=convergente_divergente; epsilon=1.5 | subsonico_no_bloqueado | 0.410438 | 100.000000 | 41 |
| choque_interno | tipo_tobera=convergente_divergente; epsilon=6 | choque_normal_interno | 0.399778 | 100.000000 | 82 |
| choque_salida | tipo_tobera=convergente_divergente; epsilon=5.206112788473547 | choque_normal_salida | 0.458852 | 100.000000 | 42 |
| sin_expansion | mach=0.9; rp=3; pi_d=0.7; T3=500 | sin_expansion | No disponible | No disponible | 0 |

Para el choque en salida se elige una relación de áreas cuya contrapresión
umbral calculada por el modelo es 100 kPa: no se fuerza un régimen imposible.
Las regiones del choque interno contienen 41+41 puntos. En choque de salida
hay 41 estados previos y un único estado posterior, sin prolongación exterior.
En convergente no se inventa una curva, y ante ausencia de expansión no se
conservan los perfiles de la simulación anterior. La cinética y el residuo de
tobera se muestran como «No disponible»; los otros balances y el T–s de cuatro
estados de remanso permanecen calculados.

### Inspección de funcionamiento y presentación

Se revisan las seis secciones, teoría anterior, simulación, OFAT de dos
puntos y mapa 2×2, con actualización de resultados y sin errores JavaScript
al terminar. Las figuras 44.1/44.2 siguen presentes junto al balance 44.3 y
los dos perfiles 44.4. Se distinguen leyendas, unidades, ramas de color y el
salto punteado de choque; ambos perfiles usan la misma relación de área.

Se comprueban tamaño normal, 1920×1080, 1280×900 y estrecho 390×844 mediante
configuraciones de viewport. En estrecho se apilan los perfiles y cada región
SVG permite desplazamiento horizontal con teclado y foco visible. Se comprueba
que el ancho del documento no excede el viewport. Los recortes dentro del
contenedor desplazable son deliberados: para ver el extremo de salida se
usa la barra o las flechas. No se ensancha toda la página. No se añaden mejoras
de diseño ni se modifican CSS/JS; se preserva el T–s corregido previamente.
Las capturas se guardan fuera del repositorio.

**Incidencia operativa.** Una instancia previa en 127.0.0.1:5000 devolvía
HTTP 500 al combinar código cargado anterior y la plantilla actualizada;
el cliente de pruebas ya daba 200. Al reiniciar la instancia local con rutas
explícitas al proyecto, GET y POST reales dan 200, sin corregir código. Se
conserva el log del servidor de revisión fuera del repositorio. No queda un
fallo Flask/Jinja pendiente en los escenarios revisados.

La inspección no cubre todos los navegadores ni todos los parámetros; la
comprobación interna y visual no equivale a validación experimental ni a un
modelo de motor real de alta fidelidad. El cierre documental se realiza el
28/10/2026; no se declara una nueva ejecución de las baterías en esa fecha.

### Conservación y revisión personal

El SHA-256 del documento personal es idéntico antes y después:
`c58291a9699493e31cf0d5f5828275c10f2e35ba86052455308716996ab5c07d`.
El otro archivo personal también conserva su hash y condición no versionada.
Los 16 archivos de la entrega y la excepción M40 son todo el alcance técnico.
No se hacen staging, commit, push, merge, rebase ni cambio de rama. `main`
permanece en su referencia inicial y `main.py` no cambia.

Servidor local: `http://127.0.0.1:5000/turborreactor`. Para una ejecución propia,
abrir `Abrir_Brayton_Simulator.cmd` o ejecutar
`.\.venv\Scripts\python.exe -B web_app.py`. Simular y abrir Resultados y
Visualizaciones. Para el choque interno, C-D y Ae/Ag=6 con valores iniciales.
Si ya hay una instancia anterior, reiniciarla para cargar el código actual.

## Publicación

**Sin commit ni push.** Esta entrega se empaqueta con las anteriores del milestone 44 para su revisión antes de publicar.
