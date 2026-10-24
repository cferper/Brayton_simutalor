# Aprendizaje 29 — Convertir estados cp(T) en gráficas científicas verificables

**Fecha:** 24 de octubre de 2026 · **Rama prevista:** `mejoras/cp-variable`.
**Base comprobada:** `9fe989bc58bda3fbe031265d694b7dc95b21a2f5`.
**Commit del milestone:** pendiente hasta publicar. Este documento describe la implementación, no una validación experimental.

## 1. Punto de partida y problema

La Fase 2A determina cp(T), γ(T), h(T) y s(T,p); la 2B calcula los cuatro estados del ciclo y sus balances; la 2C encuentra el dominio motor abierto y los extremos A/B. La aplicación web ya conectaba estos tres niveles científicos y mostraba un T–s sencillo y una sola imagen mixta de Optimización. El problema era de **representación y comprensión**, no de falta de ecuaciones.

La solución mantiene los módulos científicos intactos. Antes se veía una sola gráfica en cada una de las dos secciones; después se ven seis en Resultados y tres en Optimización si el caso es motor y está definido el dominio de trabajo. El HTML histórico y las otras seis secciones no cambian.

## 2. Qué se genera, para qué y con qué límites

### 2.1. Resultados

1. **T–s**: estado 1→2→3→4 leído con entropía [kJ/(kg·K)] en x y temperatura [K] en y. Los puntos son exactos dentro del modelo; unirlos no equivale a resolver las transformaciones intermedias. La guía es discontinua.
2. **P–v específico**: presión [kPa] en y, volumen específico [m³/kg] en x. Con el aire como gas ideal:

   \[
   p\,v=R_{\text{aire}}T,\qquad
   v=\frac{R_{\text{aire}}\,T}{1000\,p_{\mathrm{kPa}}}.
   \]

   El factor 1000 convierte kPa en Pa, pues `R_AIRE` se almacena en J/(kg·K). El volumen específico es m³ de fluido ideal por kilogramo, **no** los m³ de un compresor real. No se inventan procesos politrópicos.
3. **cp(T)**: se evalúa `propiedades_aire.cp` en 73 temperaturas del intervalo cerrado 200–2000 K y se marcan los estados. Los valores se expresan en J/(kg·K).
4. **γ(T)**: otra gráfica, de la función `gamma` adimensional, sin mezclar unidades con cp. Es una propiedad derivada, no un γ constante empleado para resolver temperaturas.
5. **Balance energético**: magnitudes `wc`, `wt`, `wnet`, `qin` y `qout` [kJ/kg]. Las barras conservan los signos del solucionador y etiquetan qué equipo **consume** trabajo y cuál lo **entrega**. Deben cumplir:

   \[
   w_{\mathrm{neto}}=w_t-w_c
   =q_{\mathrm{in}}-q_{\mathrm{out}}.
   \]

   Sin caudal másico [kg/s] no puede obtenerse potencia [kW].
6. **Ideal de componentes frente a configurado**: dos llamadas al solucionador científico 2B con las mismas `T1,T3,rp,p1`. La de comparación emplea `ηc=1,ηt=1,δ=0`; la configuración del usuario mantiene sus valores. Ambas usan cp(T). Los tres trabajos [kJ/kg] se dibujan juntos y el rendimiento térmico [%] en **otro panel y otra escala**.

Si uno de los ciclos es no motor o fuera de rango, se muestran mensajes. La gráfica comparativa no presenta prestaciones operativas inexistentes. Los estados de un ciclo calculable pero no motor siguen pudiendo enseñarse en T–s y P–v como **diagnóstico**, no como promesa de operación.

### 2.2. Optimización

Las dos búsquedas del optimizador 2C no cambian:

- **A:** relación de compresión que maximiza el trabajo neto [kJ/kg] si existe máximo interior.
- **B:** relación de compresión que maximiza el rendimiento térmico [%] si existe máximo interior.
- **Compromiso:** posición de las mismas muestras al dibujar W en x y η en y. El orden de los puntos procede de rp creciente; no toda la curva tiene por qué ser de Pareto.

`curvas_optimizacion` ya resolvía noventa relaciones de compresión interiores distribuidas uniformemente en `ln(rp)`; ahora se calcula **una vez** y la lista resultante alimenta las tres imágenes. Si una muestra es no motora, se conserva `None`, creando un hueco y no una barra o una interpolación. La coordenada x de los dos gráficos de rp es logarítmica, pero sus marcas dicen rp=2, rp=10, etc., no ln(rp).

Las letras A/B se crean a partir del resultado preciso de `estudiar_cp_variable`. Su aparición requiere `tipo='maximo_interior'`. Un `supremo_frontera` conserva su ficha textual, pero no recibe marcador circular en una frontera excluida.

## 3. Ruta de ejecución actual y módulos

`POST /` con acción `normal` u `optimizar`:

1. `web_app.index()` lee las **siete** entradas y llama a `cp_variable_web.preparar_resultados(entradas)`.
2. `resolver_ciclo(**entradas)` obtiene el caso principal y `propiedades_estados(ciclo)` obtiene la tabla.
3. `estudiar_cp_variable(...)` devuelve el dominio y A/B.
4. `graficas_resultados(ciclo,estados,entradas)` crea T–s, P–v, propiedades, balance y la comparación; **solo la comparación** hace otra llamada a `resolver_ciclo`.
5. `curvas_optimizacion(entradas,estudio)` crea noventa muestras motoras o `None`.
6. `graficas_optimizacion(curva,estudio)` crea tres SVG, sin llamar a 2B/2C de nuevo.
7. Jinja recorre los títulos, SVG y explicaciones; `static/dashboard.js` clona el SVG para abrirlo en el diálogo ampliado. El navegador no recalcula física.

El diccionario nuevo devuelve las claves `ciclo`, `estados`, `graficas_resultados`, `diagnostico_comparacion`, `optimizacion` y `graficas_optimizacion`. Las antiguas claves de una sola gráfica `ts` y `grafica` ya no forman parte de la salida del presentador.

## 4. Las funciones nuevas, una por una

### 4.1. Ejes, marcas y discontinuidades

- `_numero(valor) -> str`: de `float` a etiqueta con cuatro cifras significativas; no redondea el valor que usó el solucionador. Lo llaman los ejes y las barras. Ejemplo: `_numero(123.456) == '123.5'`.
- `_margen(valores) -> (float,float)`: lista no vacía de valores ya calculados a límites con 9 % de margen vertical para legibilidad; no inventa temperaturas. Se usa antes de `_marco`.
- `_marco(nombre,x_etiqueta,y_etiqueta,x_lim,y_lim,*,log_x=False) -> (str,función)`: prepara el SVG y una función local de transformación de coordenadas. Acepta etiquetas, pares de límites y, opcionalmente, escala log de x. Rechaza límites no finitos y x no positiva en log. Devuelve el texto de ejes en SVG y `posicion(x,y)` para superponer puntos reales. Lo llaman los gráficos de puntos y curvas.
- `_tramos(muestras,posicion,*,color=AZUL) -> str`: acepta una secuencia de pares (x,y) y `None`. Acumula puntos mientras son válidos y crea una polilínea por grupo; con un único punto dibuja un círculo. Ante `None` termina el tramo; evita unir regiones excluidas.
- `_estado(numero,x,y,posicion,*,color=AZUL,etiqueta=None) -> str`: marca un estado 1–4 o un extremo A/B y añade `data-x`, `data-y`, `data-estado` y `<title>`. Los atributos numéricos permiten contrastar el gráfico con los resultados científicos.

Una función interna de Python se puede devolver como cualquier otro objeto. Por ejemplo:

```python
marco, proyectar = _marco(
    "Ejemplo", "T [K]", "cp [J/(kg·K)]",
    (200.0, 2000.0), (900.0, 1300.0)
)
x_pixel, y_pixel = proyectar(600.0, 1100.0)
```

El punto físico conserva sus valores (600 K, 1100 J/(kg·K)), aunque el SVG necesite píxeles; **proyectar no cambia el dato termodinámico**.

### 4.2. Gráficas de Resultados

- `svg_ts(ciclo) -> str`: recibe el diccionario 2B, llama `_marco` y `_estado` y dibuja cuatro estados más conexión discontinua.
- `svg_pv(ciclo) -> str`: mismas entradas, pero calcula `v=R_AIRE*T/(1000*p)` antes de usar los helpers; retorna P–v en m³/kg y kPa.
- `svg_propiedades(estados) -> tuple[str,str]`: recibe cuatro filas con T [K] y número y llama funciones cp/gamma de 2A; retorna dos SVG separados, con puntos 1–4.
- `svg_balances(ciclo) -> str|None`: toma cinco valores de 2B, crea barras y un eje numérico común [kJ/kg]; si `viable=False` retorna `None`.
- `svg_comparacion(ideal,configurado) -> str|None`: dos diccionarios 2B, crea barras emparejadas de trabajos [kJ/kg] y, separado, rendimiento [%]. Exige ambos `viable=True`.
- `graficas_resultados(ciclo,estados,entradas) -> tuple[list,str]`: recibe los resultados del caso, sus cuatro propiedades y siete entradas; retorna seis triples (título, SVG o None, explicación) y diagnóstico. Hace una llamada opcional a `resolver_ciclo` para ideal con cp(T). Si esa llamada falla por parámetros, rango o convergencia, **atrapa solo ese error**, preservando los demás gráficos. La llama `preparar_resultados`.

### 4.3. Gráficas de Optimización

- `graficas_optimizacion(curva,estudio) -> tuple`: recibe hasta 90 muestras de `curvas_optimizacion` y el diccionario de 2C. Extrae x=rp, y=trabajo [kJ/kg] o η [%], construye un tercer par W–η, llama los helpers y marca A/B **solo si son interiores**. Devuelve tres triples o tupla vacía sin suficientes muestras motoras; la llama `preparar_resultados`. No importa ni ejecuta ningún optimizador: consume sus resultados ya calculados.

No hay ficheros HTML adicionales, ni nuevas bibliotecas, ni JavaScript de termodinámica.

## 5. Ejemplo reproducible y significado

Con las entradas por defecto (T1=288,15 K, T3=1600 K, rp=10, p1=100 kPa, ηc=0,85, ηt=0,90, δ=0,05):

| Magnitud | Componentes ideales cp(T) | Configurado cp(T) |
|---|---:|---:|
| Trabajo compresor [kJ/kg] | 268,800217 | 316,235549 |
| Trabajo turbina [kJ/kg] | 811,618642 | 718,306347 |
| Trabajo neto [kJ/kg] | 542,818426 | 402,070798 |
| Rendimiento térmico [%] | 45,2455 | 34,8934 |

Son dos resoluciones del **mismo** aire de propiedades variables, no una mezcla con γ constante. Las cifras se obtienen de `resolver_ciclo` y sirven para comprobar la comparación numérica, no para describir un motor real.

Prueba educativa: toma el estado 1 del ciclo, T=288,15 K y p=100 kPa. Utiliza el `R_AIRE` real del programa para calcular `v1`. Comprueba que dividir p por 1000 en vez de multiplicarlo produce una cifra errónea por seis órdenes de magnitud. Observa luego cómo la marca del estado 1 aparece en el gráfico P–v.

## 6. Verificación y criterio de aceptación

`tests/test_graficas_cp_variable.py` verifica:

1. Cantidad de gráficas y estructura XML/SVG.
2. Valores de los cuatro estados T–s y P–v directamente contra 2B.
3. Unidades y evaluación de cp/γ en el intervalo permitido.
4. Cinco balances y coherencia con primera ley.
5. Ideal/configurado calculados con 2B, separando kJ/kg de %.
6. No motores y comparación no calculable sin barras engañosas.
7. Marcadores A/B procedentes del estudio 2C y ausencia de B para supremo.
8. Cortes por `None` y funcionamiento de Flask/visor.

GitHub Actions vuelve a ejecutar la batería web existente junto a estas pruebas. Los módulos científicos 2A–2G no se editan. Las pruebas de XML y comparación de números constituyen **verificación del software**; la inspección visual en un navegador Windows y la validación experimental son pasos distintos.

**Ejecución registrada (24/10/2026):** 110 pruebas web relevantes correctas, incluidas 12 nuevas. La suite *histórica total* ya tenía 18 fallos y 62 errores sobre 427 métodos antes de este trabajo, por tests de contratos Flask antiguos; tras incorporar las nuevas pruebas son 439 métodos con esos mismos 18 fallos y 62 errores. Se conservan los tests históricos para su futura revisión, sin alterar código fuera del alcance. Se rasterizaron y observaron seis representaciones SVG en un entorno aislado; no sustituye la revisión real en Windows.

## 7. Experimentos y límites para continuar aprendiendo

1. Compara los trazados cp/γ con las T1–T4 de dos ciclos que tengan T3 muy diferente; identifica por qué un γ fijo no describiría todos los estados.
2. Reduce ηc o ηt sin cambiar T1, T3 y rp. Comprueba la diferencia entre el caso configurado y el ideal de componentes cp(T).
3. Usa ηc=ηt=1 y δ=0. Observa que el óptimo B puede ser supremo abierto, sin círculo B sobre la curva.
4. Prueba rp=1, δ=0. Los estados pueden ser calculables, pero no debe aparecer una barra de rendimiento operativo.
5. Aumenta la vista ampliada de cada gráfica y revisa que se leen ejes y leyendas; esta comprobación manual no se sustituye con `unittest`.

La evolución futura de imágenes de Sensibilidad, Mapa o Segunda ley no forma parte de este milestone. La documentación científica detallada está en [CODE_WALKTHROUGH §4.67](../../CODE_WALKTHROUGH.md) y el resumen en [milestone técnico 29](29_graficas_resultados_optimizacion_cp.md).
