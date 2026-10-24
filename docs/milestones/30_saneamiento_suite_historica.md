# Milestone 30 — Auditoría y saneamiento de la suite histórica

**Fecha de intervención:** 24/10/2026.
**Repositorio:** `cferper/Brayton_simutalor`.
**Rama objetivo:** `mejoras/cp-variable`.
**Commit base confirmado por GitHub:** `f689d53e613ef78024530dad1d178a7b28379a7d`.
**Commit de publicación:** pendiente hasta su verificación y publicación.

## Estado anterior

El dashboard principal usa exclusivamente propiedades variables cp(T), con
siete entradas. La aplicación de gas perfecto está conservada en
`cferper/Brayton_simutalor-gas_perfecto`. La última ampliación de las gráficas
había superado 110 pruebas web en GitHub Actions.

Al ejecutar `python -m unittest discover -s tests -v` en un entorno Python
3.12 con dependencias de `requirements.txt` se descubrieron **439 métodos**:
**394 correctos, 18 fallos, 62 errores y ocho omisiones opcionales por SciPy**.
Los 80 incidentes correspondían a **37 métodos** (varios casos `subTest`
pueden generar más de un error por método).

## Diagnóstico de los 80 incidentes

| Causa raíz identificada | Errores | Fallos | Contrato histórico |
|---|---:|---:|---|
| Ya no existe `web_app.estudio_conservado` | 40 | 0 | Recuperación y actualización de estudios JSON antes de calcular un nuevo HTML. |
| Ya no existe `web_app.main` | 14 | 0 | Ejecución mediante la antigua fachada Flask. |
| Ya no existen `web_app.ejecutar_sensibilidad`, `ejecutar_mapa`, `ejecutar_segunda_ley` | 7 | 0 | Orquestación histórica de informes. |
| Ya no existe `web_app.leer_parametros` | 1 | 0 | Lectura de nueve entradas y conversión de porcentaje. |
| Se esperaba redirección HTTP 303; ahora el resultado es 200 o 400 | 0 | 14 | Generación de un archivo HTML y navegación al mismo. |
| Se esperaban datos, nombres o textos de la antigua presentación | 0 | 4 | Retención de cuatro informes, campos y secciones anteriores. |
| **Total** | **62** | **18** | |

El problema es la comparación contra contratos que cambiaron, no un resultado
de las correlaciones termodinámicas. Esta clasificación **no demuestra que no
existan otros defectos**: se deben seguir ejecutando los tests de producción y
de integridad adecuados a la arquitectura actual.

## Qué se ha añadido

1. **Conservación exacta.** Once archivos históricos permanecen sin editar en
   `legacy_tests/`. Sus identificadores de objeto se compararon con los once
   archivos homónimos del repositorio `Brayton_simutalor-gas_perfecto` y son
   idénticos. No se ha escrito nada en ese repositorio.
2. **Separación explícita.** `tests/test_compatibilidad_historica.py` declara
   los 37 métodos incompatibles con la Flask cp(T). Su función `load_tests`
   importa desde el archivo histórico y ejecuta los **127 métodos restantes**
   que sí siguen siendo aplicables. Si un método nombrado desaparece del
   archivo, el descubrimiento falla; la separación no es silenciosa ni usa
   `skip` o `expectedFailure`.
3. **Cobertura vigente reforzada.** `tests/test_integridad_historica_actual.py`
   incorpora ocho tests que comprueban validación estructural/física del JSON
   del gas perfecto, alteraciones de tipos, valores no finitos, referencias de
   parámetros, estados, entropía, exergía, respuesta Flask a metadatos dañados,
   descarga exacta y ausencia de reutilización del informe en un cálculo cp(T).
4. **CI completa.** `.github/workflows/verificacion_web_cp_variable.yml`
   continúa con las 110 pruebas web focalizadas y ahora ejecuta también
   `python -m unittest discover -s tests -q`, sin ocultar fallos no previstos.
5. **Documentación.** Se han actualizado los apartados afectados del manual
   actual y se ha creado [la guía educativa 30](30_saneamiento_suite_historica_APRENDIZAJE.md).

## Verificación y criterios de aceptación

| Comprobación | Antes | Después de la separación |
|---|---:|---:|
| Métodos en el descubrimiento vigente | 439 | **410** (37 contratos antiguos separados, ocho tests actuales nuevos) |
| Correctos | 394 | **402** |
| Fallos | 18 | **0** |
| Errores | 62 | **0** |
| Omisiones opcionales | 8 | **8** (SciPy no instalado) |
| Web cp(T) focalizado | 110/110 | Debe conservarse en CI |
| Núcleo cp(T) 2A–2G | 85/85 | No debe modificarse |

**Comandos:**

```bash
python -m unittest discover -s tests -q
python -m unittest discover -s tests -p 'test_integridad_historica_actual.py' -v
```

Para ejecutar la aplicación y pruebas del gas perfecto debe usarse el
repositorio conservado, no mezclar esas pruebas Flask con la nueva fachada
`web_app.py`. SciPy es opcional y sus omisiones se notifican individualmente.

**Ejecución local de la suite vigente:** `410 tests in 46.623s`, `OK
(skipped=8)` en Linux/Python 3.12, con NumPy 2.5.4, Matplotlib 3.11.2 y
Flask 3.1.3 instalados desde `requirements.txt` en un entorno virtual
independiente. Los ocho tests nuevos de integridad histórica se ejecutaron
aparte: `8 tests in 0.622s`, `OK`. Los 110 tests web y los 85 tests
científicos cp(T) ya habían superado la ejecución focalizada sobre la base.
La verificación definitiva en GitHub Actions de este commit se realizará
después de subir el árbol de validación.

## Nuevos conceptos de ingeniería

- Una prueba del antiguo gas perfecto puede seguir verificando sus propias
  ecuaciones y balances sin ser una prueba del modelo variable cp(T).
- Rechazar un JSON histórico incoherente impide atribuir a estados alterados
  propiedades físicas o exergías que el código no calculó.
- La seguridad de lectura de un informe no equivale a validación experimental
  ni a garantía criptográfica de autenticidad.

## Nuevos conceptos de Python

- Descubrimiento de `unittest` y protocolo `load_tests`.
- `TestSuite` frente a `TestCase` y separación explícita de contratos.
- `subTest` y diferencia entre métodos ejecutados e incidencias notificadas.
- `importlib.util.spec_from_file_location` para cargar pruebas conservadas sin
  insertar rutas de producción ni instalar herramientas adicionales.
- Integración continua y dependencia opcional SciPy.

## Limitaciones que siguen existiendo

- Los 37 métodos Flask archivados solo tienen significado operativo completo
  con el código del repositorio histórico; sus sustitutos cp(T) no hacen que
  la interfaz anterior exista en la aplicación nueva.
- Los nuevos tests de JSON examinan alteraciones conocidas, no todos los
  posibles documentos corruptos ni ataques maliciosos.
- Las comprobaciones son **verificación interna del software**, no contraste
  experimental del modelo termodinámico.

## Commit asociado

Pendiente de publicación. No se incluye un SHA supuesto para este documento.
