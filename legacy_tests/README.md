# Pruebas de la aplicación histórica de gas perfecto

Estos once archivos `test_*.py` son **copias íntegramente conservadas** de los
que existían antes del milestone 30. Sus objetos Git coinciden con los archivos
de `cferper/Brayton_simutalor-gas_perfecto` (`main`) al comprobarlos el
24/10/2026. No se han reescrito expectativas para forzar resultados correctos.

En el simulador actual cp(T), 37 métodos de estos archivos esperan contratos de
la interfaz Flask anterior: nueve entradas (`cp` y `gamma` constantes), creación
de archivos HTML y redirecciones 303, o reutilización de resultados por
`web_app.estudio_conservado`. Esa API ya no existe en `web_app.py`.

El manifiesto explícito de esos **37 métodos históricos** se mantiene en
[`tests/test_compatibilidad_historica.py`](../tests/test_compatibilidad_historica.py).
La suite vigente importa y ejecuta los **127 métodos restantes** desde estos
archivos: sus comprobaciones matemáticas, de datos y de presentación histórica
siguen aportando cobertura. Esto no equivale a cambiar los algoritmos.

## Cómo ejecutar cada versión

### Aplicación cp(T) actual

Desde la raíz de `cferper/Brayton_simutalor`, con las dependencias instaladas:

```bash
python -m unittest discover -s tests -q
```

Este comando ejecuta las pruebas vigentes, incluida la compatibilidad
científica de los 127 casos históricos. No importa automáticamente los 37
contratos Flask obsoletos.

### Aplicación conservada con cp y gamma constantes

Desde una **copia independiente** de `cferper/Brayton_simutalor-gas_perfecto`
con su propio entorno de dependencias:

```bash
python -m unittest discover -s tests -q
```

Allí el código histórico incluye las rutas y funciones que necesitan las
pruebas originales. Esta revisión no modifica ese repositorio. Las pruebas
opcionales de SciPy pueden notificarse como omitidas si no está instalado.

Ejecutar sin adaptación todos los archivos de este directorio contra el
`web_app.py` actual no es un test de regresión válido: mezcla contratos de dos
aplicaciones deliberadamente separadas. Los originales se conservan para
reproducibilidad; no se afirma que su ejecución contra cp(T) deba pasar.
