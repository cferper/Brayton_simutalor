# Brayton Simulator — Documentación en español

[Inicio / Idiomas](README.md) · [English documentation](README.en.md)

Brayton Simulator es un proyecto educativo en Python para estudiar la **termodinámica del ciclo Brayton** y las **prestaciones simplificadas de un turborreactor aeronáutico**. Combina modelos numéricos y una interfaz web local con Flask para modificar condiciones de funcionamiento, examinar balances físicos y comprender la respuesta de una turbina de gas.

Está concebido para aprender y verificar software, **no para dimensionar o certificar un motor real**.

## Qué permite estudiar

### Ciclo Brayton

- Cálculos de ciclos ideales y no ideales: compresor, turbina, pérdidas de presión, calor aportado, trabajo específico y rendimiento térmico.
- El modelo histórico de propiedades constantes y un modelo independiente y posterior de propiedades variables del aire, con capacidad calorífica dependiente de la temperatura, **cp(T)**.
- Búsqueda numérica de dominios de funcionamiento y óptimos; estudios de sensibilidad de una variable y mapas de diseño presión–temperatura.
- Tablas de estados, balances energéticos, análisis de segunda ley y exergía, diagramas e informes locales. La disponibilidad de cada gráfico depende del modelo y la vista.

Los informes históricos se conservan como documentos: abrirlos no recalcula sus resultados con un modelo posterior.

### Turborreactor

El modelo independiente de turborreactor representa admisión/difusor, compresor, aporte simplificado de energía en la cámara de combustión, turbina y tobera. Según la configuración, permite obtener:

- Estados de remanso y estáticos, variaciones de presión y temperatura, balance de trabajo de eje y consumo equivalente de combustible.
- Toberas convergentes y convergentes-divergentes (C-D), con los regímenes de flujo compresible y tratamientos de choque normal implementados cuando corresponda.
- Caudal por la tobera, áreas de garganta y salida, diámetros equivalentes y geometría cónica simplificada.
- Velocidades de vuelo y escape, empuje específico, **empuje absoluto si se conoce el caudal**, contribuciones al empuje y consumo específico de combustible respecto al empuje (TSFC).
- Resolución del punto de funcionamiento de un motor monoeje acoplado mediante mapas normalizados de compresor y turbina.

El tratamiento del combustible y la cámara de combustión es una aproximación mediante balance energético, no un modelo detallado de química de combustión.

### Banco interactivo de motores

Entra en **`/turborreactor/interactivo`** para utilizar las tres modalidades:

| Modalidad | Qué fija el usuario | Qué calcula el simulador |
| --- | --- | --- |
| **A — Caudal impuesto** | Caudal de aire y condiciones del motor/vuelo | Comportamiento de la tobera y prestaciones para ese caudal |
| **B — Geometría fija** | Áreas de garganta y salida, y condiciones del motor/vuelo | Caudal compatible y prestaciones bajo las restricciones geométricas |
| **C — Motor acoplado** | Condiciones de vuelo/térmicas y geometría de la tobera | Punto de equilibrio numéricamente verificado, si se encuentra, acoplando mapas de compresor y turbina con la tobera |

Las tres modalidades permiten explorar parámetros, pero las magnitudes impuestas y calculadas no son intercambiables.

En la **modalidad C**, el botón **«Restablecer geometría de diseño»** recupera explícitamente las áreas de garganta y salida de referencia calculadas por el modelo de diseño existente. La referencia es **convergente** (Ag = Ae) incluso si se ha seleccionado una tobera C-D: **no es una geometría C-D óptima**. Es posible editar posteriormente ambas áreas; cambiar de modalidad no sobrescribe los valores sin intervención del usuario. Algunas geometrías no permiten obtener una solución acoplada numéricamente verificada, lo que por sí solo no demuestra imposibilidad física.

## Gráficas y análisis interactivo

El banco agrupa las representaciones en:

- **Ciclo:** diagrama T–s esquemático; temperaturas y presiones totales en estaciones calculadas; trabajos del compresor, turbina y eje; balance energético.
- **Tobera:** geometría y, cuando la solución geométrica lo permite, perfiles axiales de Mach, presión estática, temperatura estática y velocidad. Los saltos de choque se muestran sin interpolaciones ficticias.
- **Prestaciones:** descomposición del empuje específico y absoluto (si existe el dato), y velocidades de vuelo y salida.

Las gráficas técnicas ofrecen consulta puntual, zoom y exportación SVG o PNG cuando sus controles lo permiten. Solo se presentan las magnitudes disponibles: si faltan datos o no existe un perfil geométrico resuelto, se omite la gráfica correspondiente. Unir estados discretos **no significa** haber resuelto el flujo espacial dentro de cada componente.

### Estudios paramétricos

El banco interactivo incorpora:

- Empuje frente al número de Mach de vuelo.
- Empuje y TSFC frente a la temperatura de entrada a la turbina **T3**.
- Mapas de prestaciones Mach–T3.
- Comparación de configuraciones y curvas compatibles.
- Exportación CSV de datos y exportación gráfica cuando está disponible.

Los puntos inválidos o sin solución se identifican, sin rellenarlos con resultados ficticios. La modalidad C tiene un coste numérico generalmente mayor, por lo que admite mallas y barridos más reducidos que A/B. Son estudios del modelo implementado, **no mapas experimentales de funcionamiento de un motor real**.

La interfaz clásica (`/turborreactor`) conserva sus propias herramientas de resultados, sensibilidad y mapas de prestaciones.

## Instalación y ejecución en Windows

**Requisitos:** Python con `venv` y `pip`, y un navegador moderno. El archivo `requirements.txt` declara las dependencias principales: **NumPy, Matplotlib y Flask**. SciPy es opcional para determinadas comparaciones numéricas; no se necesita para iniciar la aplicación web.

Abre PowerShell en la carpeta donde quieras descargar el proyecto:

```powershell
git clone https://github.com/cferper/Brayton_simutalor.git
cd Brayton_simutalor
git switch mejoras/cp-variable
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python web_app.py
```

Si PowerShell bloquea la activación, puedes ejecutar `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` y `.\.venv\Scripts\python.exe web_app.py` sin activar el entorno.

Como alternativa, cuando ya exista `.venv`, puedes abrir **`Abrir_Brayton_Simulator.cmd`** para iniciar el servidor local y abrir el navegador.

El lanzador incluido utiliza `127.0.0.1:5000`. Se pueden utilizar otros puertos modificando la configuración del servidor: **5001 y 5002 no son requisitos del modelo físico**.

| Dirección | Interfaz |
| --- | --- |
| [`/turborreactor/interactivo`](http://127.0.0.1:5000/turborreactor/interactivo) | Banco interactivo (A/B/C) |
| [`/turborreactor`](http://127.0.0.1:5000/turborreactor) | Turborreactor clásico |
| [`/brayton`](http://127.0.0.1:5000/brayton) | Panel Brayton con propiedades variables |

La ruta raíz (`/`) redirige al banco de turborreactor interactivo. Mantén la terminal abierta mientras utilizas la aplicación; pulsa **Ctrl+C** para detenerla. El servidor de desarrollo Flask está destinado al uso local, no al despliegue público.

## Verificación y limitaciones

El repositorio incluye pruebas automáticas de termodinámica, balances y fronteras numéricas; solucionadores y comparaciones opcionales con SciPy; rutas y contratos API de Flask; lógica de interfaz; gráficas y estudios paramétricos. La [documentación del milestone 49.6](docs/milestones/49_6_ampliacion_graficas_motor.md) recoge una regresión en Windows con **769 pruebas Python correctas, 10 omitidas y ninguna fallida**, así como **9 pruebas JavaScript correctas** tras integrar el restablecimiento de geometría. Son resultados documentados; no significa que se hayan vuelto a ejecutar para editar este README.

**La verificación del software no equivale a la validación experimental.** En particular:

- Se trata de un simulador educativo simplificado, **no de un modelo de motor certificado ni validado experimentalmente**.
- La química del combustible y las propiedades de los productos de combustión se simplifican; los modelos de componentes, rendimientos y mapas tienen dominios de validez definidos.
- Algunas combinaciones no ofrecen una solución numérica verificada. La falta de convergencia no demuestra por sí sola imposibilidad física.
- Algunas magnitudes, especialmente el empuje absoluto y los perfiles axiales, necesitan datos que no están disponibles en todas las modalidades o toberas.
- Los diagramas esquemáticos de estaciones no deben interpretarse como campos de flujo tridimensionales ni transitorios.

## Guía del repositorio

| Ruta | Función |
| --- | --- |
| `web_app.py` | Servidor Flask, rutas y API |
| `ciclo_cp_variable.py`, `cp_variable_web.py` | Cálculos del Brayton con propiedades variables y adaptación web |
| `turborreactor_web.py`, `prestaciones_turborreactor_web.py` | Presentación del turborreactor y estudios de prestaciones |
| `acoplamiento_motor_mapa_47.py` | Punto acoplado del motor y referencia de diseño |
| `estudios_parametricos_49_5.py` | Estudios interactivos Mach/T3 |
| `templates/`, `static/` | Plantillas HTML, JavaScript y estilos |
| `data/tmats_47/` | Datos y procedencia de mapas normalizados |
| `tests/` | Pruebas automatizadas |
| `docs/milestones/` | Decisiones de ingeniería, verificaciones y guías de aprendizaje |
| `requirements.txt`, `Abrir_Brayton_Simulator.cmd` | Dependencias y lanzador Windows |

## Documentación adicional

- [Recorrido técnico por el código](CODE_WALKTHROUGH.md): arquitectura, métodos numéricos e implementación.
- [Documentación de milestones](docs/milestones/): registros técnicos y explicaciones educativas detalladas.
- [Gráficas técnicas interactivas (49.4)](docs/milestones/49_4_graficas_tecnicas_interactivas.md).
- [Estudios paramétricos (49.5)](docs/milestones/49_5_estudios_parametricos_interactivos.md).
- [Gráficas del motor y geometría de referencia de C (49.6)](docs/milestones/49_6_ampliacion_graficas_motor.md).
- [Reglas de desarrollo](AGENTS.md).

Brayton Simulator es un proyecto personal de aprendizaje de ingeniería aeroespacial.
