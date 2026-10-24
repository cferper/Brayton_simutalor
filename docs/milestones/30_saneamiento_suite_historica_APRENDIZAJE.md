# Aprendizaje del milestone 30 — Mantener pruebas mientras cambia una aplicación

**Fecha:** 24/10/2026. **Repositorio:** `cferper/Brayton_simutalor`.
**Rama de desarrollo:** `mejoras/cp-variable`.
**Base comprobada:** `f689d53e613ef78024530dad1d178a7b28379a7d`.

## 1. Situación de partida y problema real

El simulador nació con un modelo de gas ideal de cp y gamma constantes.
Durante aquella etapa, la aplicación Flask recibía **nueve parámetros**,
generaba un informe HTML autocontenido por operación y respondía mediante
una redirección HTTP **303**. Las pruebas de aquel diseño tenían razón al
exigir ese contrato **en ese momento**.

Ahora hay dos repositorios con responsabilidades distintas:

- `Brayton_simutalor-gas_perfecto`: mantiene intacto el diseño histórico.
- `Brayton_simutalor` (`mejoras/cp-variable`): recibe **siete parámetros**,
  calcula con cp(T), muestra el resultado directamente con HTTP **200** y
  permite **consultar y descargar** informes anteriores sin generarlos de nuevo.

Una prueba del antiguo Flask puede fallar aunque el nuevo ciclo sea correcto.
Por ejemplo, `assertEqual(respuesta.status_code, 303)` falla si la respuesta
actual prevista es 200; cambiar la aplicación para que regrese a 303
rompería el requisito del nuevo dashboard. Tampoco sería correcto sustituir
303 por 200 en la prueba y afirmar que sigue verificando la generación de
informes: **esa operación ya no existe**.

## 2. Qué hizo `unittest` durante el diagnóstico

```bash
python -m unittest discover -s tests -v
```

`python -m` ejecuta un módulo de la biblioteca estándar como programa.
`unittest` proporciona `TestCase` y sus aserciones. `discover` busca archivos
`test_*.py` dentro de `tests`; `-s` indica su directorio y `-v` imprime cada
método. `TestCase.setUp` prepara sus datos, normalmente en carpetas
temporales, y cada método `test_*` verifica una propiedad concreta.

En la copia inicial de la rama se descubrieron **439 métodos**:
394 terminaron correctamente, ocho se omitieron explícitamente por depender
de SciPy y 37 produjeron en conjunto **18 `FAIL` y 62 `ERROR`**.

**Diferencia importante:**

- `FAIL` significa que una aserción (`assertEqual`, `assertTrue`, etc.) no se
  cumplió. Ejemplo: se esperaba HTTP 303 y se recibió HTTP 200.
- `ERROR` significa que no se pudo completar el método por una excepción no
  esperada. Ejemplo: `patch.object(web_app, "main")` solicita un atributo que
  ya no existe en la fachada actual y lanza `AttributeError`.
- `subTest` repite casos dentro de un método: siete adulteraciones de JSON
  pueden generar siete errores, pero la suite cuenta **un método** descubierto.
- `skip` es una omisión declarada. Las ocho del diagnóstico procedieron de
  contrastes independientes opcionales con SciPy, no del cambio de fachada.

Por eso 18 + 62 **no** significa que existan 80 métodos distintos defectuosos.

## 3. Decisión de arquitectura de pruebas

Se han preservado sin ninguna alteración once archivos en `legacy_tests/`.
Los once corresponden exactamente a los que existen en el repositorio de
conservación. Sus pruebas Flask originales pueden ejecutarse con el código
histórico, donde sí están las funciones que necesitaban.

Pero esos archivos también contienen pruebas matemáticas, físicas y de
presentación que **sí** siguen siendo útiles en el repositorio nuevo. De los
164 métodos existentes en los once archivos, solo 37 dependían de contratos
Flask incompatibles; los otros **127** continúan ejecutándose en la suite
vigente. No se han eliminado, convertido en `skip` ni debilitado.

El archivo `tests/test_compatibilidad_historica.py` funciona como un
manifiesto **visible y revisable** de los 37 métodos históricos, con nombres
exactos. Cada vez que `unittest` carga las pruebas vigentes, comprueba que
el inventario sigue correspondiendo a métodos que realmente existen.

## 4. PYTHON — cargar y filtrar un conjunto de pruebas

### `load_tests(loader, tests, pattern) -> unittest.TestSuite`

Esta es una función especial que reconoce `unittest` al importar el módulo
`test_compatibilidad_historica`. No mide trabajo ni rendimiento del ciclo.

**Argumentos:** `loader` es un `unittest.TestLoader`; `tests` es una
`TestSuite` ya descubierta; `pattern` es el patrón de búsqueda o `None`.
**Retorno:** una `TestSuite` cuyos elementos son métodos científicos y de
integración aún válidos de los archivos archivados. **Unidades:** ninguna,
porque solo organiza pruebas de software. **Errores:** si un método que figura
en la lista de contratos antiguos ya no existe, se lanza `AssertionError`;
lo mismo sucede si el total inventariado deja de ser 37.

Flujo resumido del código:

```python
especificacion = importlib.util.spec_from_file_location(nombre, ruta)
modulo = importlib.util.module_from_spec(especificacion)
especificacion.loader.exec_module(modulo)
casos = list(_casos(loader.loadTestsFromModule(modulo)))
```

1. `Path` identifica el archivo conservado, sin depender de la carpeta desde
   la que se ejecutó Python.
2. `spec_from_file_location` prepara cómo importar un archivo cuya ubicación
   es explícita.
3. `module_from_spec` construye el objeto módulo; `exec_module` carga su
   código. No lo ejecuta como programa principal, por lo que sus bloques
   `if __name__ == '__main__'` no arrancan nuevos tests por separado.
4. `loader.loadTestsFromModule` identifica sus clases `TestCase`.
5. `_casos(suite)` recorre recursivamente las suites anidadas con `yield from`
   y entrega instancias individuales de `TestCase`.
6. Para cada método, se consulta su nombre en el manifiesto. Los 37 antiguos
   quedan preservados en el archivo histórico; los restantes se añaden a la
   `TestSuite` vigente con `addTest`.

**Por qué no usar `skip`:** marcar un test obsoleto como omitido ocultaría el
hecho estructural de que pertenece a una **aplicación diferente**. El
manifiesto conserva esa distinción y la obligación de justificar cambios
futuros. Los 127 métodos que aún importan se ejecutan de verdad.

**Prueba mental:** si mañana se añade otro `test_balance_energia` a uno de
los archivos históricos y no se registra como antiguo, será descubierto y
ejecutado; no quedará silenciosamente excluido. Si desaparece un nombre del
manifiesto, fallará la carga hasta revisarlo.

## 5. INTERPRETACIÓN FÍSICA — mantener las invariantes adecuadas

Conservar pruebas no significa confundir modelos:

- El gas perfecto de cp constante sigue necesitando contrastar su primera
  ley, límites motores, exergía y máximos en **sus propios** algoritmos.
- El nuevo cp(T) necesita sus pruebas independientes de propiedades del aire,
  inversión de entalpía y entropía, optimizaciones A/B, sensibilidad, mapas
  y exergía dependiente de T0. Son las pruebas de las fases 2A–2G.
- Un informe histórico guardado puede contener estados antiguos y un estudio
  de exergía. La aplicación cp(T) **solo debe leerlos**, verificar su
  coherencia y permitir descargarlos. No debe reutilizarlos como si fueran
  una solución del nuevo modelo variable.

El nuevo archivo `tests/test_integridad_historica_actual.py` contiene ocho
métodos que protegen esa interfaz de lectura. Reutilizan deliberadamente el
validador científico **existente** de los informes viejos:
`segunda_ley.validar_estudio_reutilizable(estudio, parametros)`.

Por ejemplo, si una temperatura histórica `T2` se sustituye por `444 K` en
un JSON, la validación debe detectar que ya no coincide con los parámetros
de aquel ciclo. Lo mismo ocurre con una presión, una entropía, la generación
de un componente o una exergía destruida inconsistente. No se cambian las
ecuaciones para obtener ese resultado.

### Comprobación de referencia y descarga

El test construye un estudio histórico real a partir de los módulos antiguos
con propiedades constantes, lo serializa como JSON y crea un informe dentro
de `TemporaryDirectory`, nunca entre los informes del usuario. Comprueba:

- Un estudio coherente satisface el validador.
- Si cambia cualquiera de los nueve parámetros, no puede reutilizarse.
- Faltas de estructura, booleanos usados como números, `None`, `NaN` e
  infinitos se rechazan.
- Si el JSON tiene datos de Segunda Ley manipulados pero los metadatos siguen
  legibles, la aplicación avisa de que el estudio no es verificable.
- Si el JSON principal está roto, la ruta devuelve HTTP 422.
- En ambos casos, la descarga entrega **los mismos bytes originales** y
  el archivo no se modifica.
- Un POST cp(T) con el nombre de un antiguo informe calcula un ciclo nuevo;
  **no** hereda sus estados anteriores ni crea un informe HTML.

Esta comprobación es de **integridad y coherencia interna**, no de autoría
criptográfica: un documento falsificado que mantenga todas las identidades
podría superar el filtro.

## 6. Cómo mantener las pruebas en fases futuras

1. Cuando se cambie una función, decidir primero si su **responsabilidad**
   todavía existe. Si solo cambió el nombre, adaptar las pruebas existentes.
2. Si desapareció deliberadamente un contrato, conservar su comprobación
   histórica junto al código de la versión correspondiente.
3. Comprobar qué requisitos continúan vigentes y escribir pruebas nuevas
   para ellos. No basta con que disminuya el contador de fallos.
4. Ejecutar `python -m unittest discover -s tests -q` y revisar los motivos
   de cada fallo, error u omisión.
5. Usar GitHub Actions para repetir la verificación en cada avance de la
   rama de desarrollo. Un fallo real debe detener la publicación.

Una **regresión** aparece cuando algo que debía seguir funcionando deja de
hacerlo después de un cambio. Que ya no exista una ruta eliminada a propósito
no constituye por sí mismo una regresión. Sí lo sería que al eliminarla
dejase de abrirse un informe antiguo que prometimos conservar.

## 7. Verificación frente a validación científica

- **Verificación:** ¿hemos programado correctamente el modelo y conservado
  sus contratos vigentes? Se comprueba mediante balances, invariantes,
  resultados analíticos y pruebas de integración.
- **Validación:** ¿describe el modelo el comportamiento de una máquina real
  en el dominio de uso previsto? Exigiría contrastes externos independientes,
  idealmente datos experimentales y estimación de incertidumbres.

Ni las 402 pruebas correctas de esta ejecución ni una ejecución de GitHub Actions pueden demostrar
por sí solas que el simulador reproduzca con precisión un motor aeronáutico.

## 8. Archivos, comandos, resultados y límites

Archivos nuevos: `tests/test_compatibilidad_historica.py`,
`tests/test_integridad_historica_actual.py`, `legacy_tests/README.md` y
los documentos 30. Los once archivos originales se trasladan completos a
`legacy_tests/`. El workflow existente incluye ahora la suite vigente
completa, además de sus verificaciones web. `CODE_WALKTHROUGH.md` describe
el estado nuevo de la infraestructura.

```bash
# Perfil vigente (científico + web + integración histórica conservada)
python -m unittest discover -s tests -q

# Solo las ocho pruebas nuevas de conservación de informes
python -m unittest discover -s tests -p 'test_integridad_historica_actual.py' -v
```

En Windows, si el comando `python` no está en PATH, ejecutar desde el
proyecto con `.venv\Scripts\python.exe` en PowerShell. Estos tests se
ejecutan voluntariamente o en CI; **no se ejecutan cada vez que se abre**
el dashboard Flask.

La suite original completa solo es significativa en el repositorio histórico.
Las comparaciones opcionales con SciPy avisan de su omisión si esa biblioteca
no está instalada. No se han tocado fuentes termodinámicas ni el ordenador
del usuario.

**Resultado local de esta intervención:** 410 métodos descubiertos,
402 correctos, ocho omisiones opcionales y cero fallos o errores;
duración 46.623 s. Las ocho comprobaciones nuevas de integridad también
pasaron de forma aislada (0.622 s). No se ha afirmado validación externa.

**Estado de commit:** pendiente de la verificación final y publicación;
la base indicada arriba no es el hash que contendrá este documento.
