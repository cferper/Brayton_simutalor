# Fase 2 — Optimización del trabajo neto no ideal

## Estado anterior

En la base verificada `f9f9a0495c4231a4d48399fba4bccdcc0f6bcf6f` existían dominio motor ideal/no ideal, búsqueda del máximo exclusivamente ideal, nueve campos Flask, seis gráficas HTML, metadatos Git y retención de cuatro informes. La rama inicial y activa es `feature/fase-2-optimizacion-noideal` y el árbol estaba limpio antes del desarrollo. Documentación del 20 de octubre de 2026.

## Qué se ha añadido

`optimizacion.py` calcula el candidato estacionario, busca independientemente el máximo dentro del dominio de Fase 1 y compara ambos resultados; reutiliza `evaluar_punto`. `main.py` coordina ambos modelos; `viabilidad.py` enriquece el barrido y expone su ventana visual sin recorte fijo. `reporting.py` añade resultados, intervalos y estados óptimos. Las comparaciones marcan ambos máximos y muestran un detalle no ideal si las escalas difieren mucho. No cambian las 13 funciones físicas originales, los nueve campos ni las dependencias.

## Nuevos conceptos de ingeniería

Derivación del máximo de trabajo no ideal a temperaturas, eficiencias y pérdida fijas; concavidad en x=rp^a y ln(rp), demostración de pertenencia interior si existe motor. Candidato matemático, máximo motor y vacío son distintos. El rendimiento en el máximo de trabajo no es el máximo rendimiento. Los intervalos físicos, numéricos y visuales se recalculan por ejecución y cumplen funciones diferentes.

## Nuevos conceptos de Python

Módulo independiente, función local con cierre y caché de una búsqueda, malla logarítmica, sección áurea, selección de registros con `max(key=...)`, estructuras anidadas y controles de precisión/coste. Se reutilizan NumPy, Matplotlib, Flask y unittest sin SciPy.

## Qué hemos aprendido

Caso predeterminado: rp óptimo no ideal analítico 12.8950516696, numérico 12.8950517350; máximo 373.210827 kJ/kg, rendimiento en ese punto 39.212614 %. Ideal: rp analítico 20.0852562921, máximo 532.802230 kJ/kg. La suite completa ejecutada el 20 de octubre de 2026 supera 55 pruebas (40 anteriores, 15 nuevas). Se comprueban óptimos menores que 2 y mayores que 50, límites visuales superiores a 10000, pérdidas elevadas, dominios estrechos/vacíos, integración y retención. Revisión visual de tres casos, fuera del historial del proyecto. Es verificación interna, sin validación experimental externa.

## Limitaciones que siguen existiendo

Gas ideal con cp/gamma constantes, pérdida y eficiencias fijas; sin caudal, combustible ni mapas. Coma flotante y banda cero limitan los dominios casi degenerados. La anchura final no garantiza igual precisión de rp en máximos planos. La referencia inviable conserva el rechazo de Fase 1; el vacío puede estudiarse con la API independiente. No se implementa optimización de rendimiento ni fases posteriores.

## Commit asociado

Pendiente: Fase 2 se entrega sin commit, merge, push ni cambio de rama. La base anterior no contiene estos cambios. Guía detallada: [04_optimizacion_noideal_APRENDIZAJE.md](04_optimizacion_noideal_APRENDIZAJE.md).
