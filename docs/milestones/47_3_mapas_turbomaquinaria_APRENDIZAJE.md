# Milestone 47.3 — Aprendizaje: mapas y régimen de giro

## Por qué el punto de funcionamiento cambia

Hasta ahora, introducíamos una relación de compresión `rp` y un rendimiento `eta_c` fijos. En una máquina real, esos valores dependen del caudal y de la velocidad de giro. El **mapa del compresor** da `Wcorr`, `PR` y `eta` para una velocidad corregida y una posición en su curva `Rline`. El **mapa de turbina** da `Wcorr` y `eta` frente a velocidad corregida y expansión.

La velocidad **mecánica del eje N** es la misma en un monoeje. Sin embargo, como `Tt2` y `Tt3` son muy distintas, `Ncorr=N/sqrt(Tt/Tref)` es diferente en la entrada de cada componente. No igualamos ambos valores corregidos.

## Escalado de mapas existentes

Los mapas públicos no describen nuestro motor. Hemos extraído datos de los componentes `HPC.map` y `HPT.map` del conjunto T-MATS/JT9D; su origen, licencia Apache 2.0 y transformación constan en `data/tmats_47/README.md`.

Para usarlos como **formas representativas**, escogemos un diseño del propio Brayton Simulator: ambiente a 288,15 K y 100 kPa, compresor 10:1 y rendimiento 0,85, entrada de turbina a 1600 K, rendimiento de turbina 0,90, 20 kg/s de aire y giro mecánico elegido de 20 000 rpm. La ecuación del núcleo calcula el dosado y la expansión de turbina; el diseño conserva su balance energético.

En cada mapa se selecciona un nudo interior conocido. Se ajustan por separado **cuatro escalas**: velocidad corregida, caudal corregido, relación de presiones y rendimiento. El ajuste reproduce exactamente el punto de diseño por construcción; **no valida la forma de las curvas en otros puntos**.

El caudal corregido `Wcorr=mdot sqrt(Tt/Tref)/(pt/pref)` permite comparar máquinas a presiones y temperaturas de entrada diferentes. En nuestro programa `Tref=288,15 K` y `pref=101,325 kPa`. El mapa original usa su propia numeración interna de velocidad y flujo; no debe interpretarse un `NcMap=100` de turbina como 100 rpm del eje real.

## Python y verificación

`scripts/extraer_mapas_tmats_47.py` transforma las tablas originales en un JSON legible y reproducible. `interpolar_bilineal` calcula una superficie entre los cuatro nudos adyacentes, sin extrapolar. `calibrar_mapas` obtiene escalas de referencia del núcleo M37, y `consultar_compresor` y `consultar_turbina` devuelven valores dentro del dominio con sus diagnósticos.

Comprueba que cambiar `N` modifica **ambas** coordenadas de velocidad de mapa aunque cada una se corrija con una temperatura distinta. Intenta solicitar una `Rline=3,1`: la función debe lanzar un error, no prolongar ficticiamente la curva de rendimiento.

**Verificación**: las tablas y ecuaciones se reproducen. **Validación real**: harían falta mediciones de compresor/turbina del motor que deseamos describir, así como efectos dinámicos, sangrados, refrigeración y límites reales de bombeo. No tenemos estos datos.
