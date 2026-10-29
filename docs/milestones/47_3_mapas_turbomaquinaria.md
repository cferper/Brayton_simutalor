# Milestone 47.3 — Mapas de compresor y turbina de NASA T-MATS

## Arquitectura y fuentes

Se seleccionan exclusivamente los componentes **HPC** y **HPT** públicos de NASA T-MATS como **formas de mapa** reutilizables, no como el modelo del motor JT9D. Los demás componentes de un JT9D biflujo y de dos ejes **no se importan**. El simulador sigue siendo turborreactor monoeje. Datos, ficheros, licencia y extracción: [`data/tmats_47/README.md`](../../data/tmats_47/README.md). El apartado alfa=0 del HPC define una sola configuración de geometría variable, que se mantiene fija; no se extrapola entre geometrías. La turbina se tabula contra velocidad corregida de mapa y relación de expansión.

Referencia para conceptos, no dependencia: [NASA T-MATS](https://github.com/nasa/T-MATS), [NASA/TM-2014-218410](https://ntrs.nasa.gov/citations/20150002325). Se usa **interpolación bilineal en el dominio tabulado**; las referencias originales admiten en ocasiones extrapolación lineal, pero este proyecto **la prohíbe**.

## Punto de diseño explícito

Se obtiene con el **núcleo ya existente** (`resolver_turborreactor_con_combustible`) y una masa de aire prescrita. Los valores de referencia didácticos son:

| Magnitud | Diseño |
| --- | ---: |
| Aire | 20 kg/s |
| Ambiente, motor estático | 288,15 K, 100 kPa, Mach 0 |
| Recuperación del difusor | 1 |
| Relación compresor | 10 |
| Rendimiento isentrópico compresor | 0,85 |
| Entrada turbina | 1600 K |
| Pérdida presión cámara | 4 % |
| Rendimiento turbina | 0,90 |
| Rendimiento mecánico | 0,98 |
| Combustión / PCI | ηb=0,99 / 43 000 kJ/kg |
| Tobera | Convergente, ηn=0,95, geometría de garganta obtenida del caudal de diseño M45 |
| Giro mecánico de ambos componentes | **20 000 rpm** (elección educativa explícita, no dato JT9D) |

El solver físico de base produce `f≈0,0280282078 kg/kg aire`, `mdot_g≈20,560564 kg/s`, `pt3≈960 kPa`, `pt4≈415,514766 kPa`, por lo que `PR_t≈2,3103872`. Se comprueba positividad de márgenes y balance de eje del modelo de diseño. El giro mecánico no interviene en el modelo histórico; en M47 se emplea para relacionar ambos mapas mediante una única variable `N`.

## Caudales y giro corregidos

Se fijan expresamente las referencias `Tref=288,15 K`, `pref=101,325 kPa`, para **ambas** entradas; no se confunden con los estados ambientales del problema ni con las unidades internas de las tablas NPSS.

\[\dot m_{corr}=\dot m\sqrt{T_t/T_{ref}}\;(p_t/p_{ref})^{-1}\]
\[N_{corr}=N/\sqrt{T_t/T_{ref}}\]

**El mismo eje tiene un único N físico**, pero el compresor corrige respecto a `Tt2` y la turbina respecto a `Tt3`. En el diseño, `Ncorr_c=20 000 rpm` y `Ncorr_t≈8487,49 rpm`. Las coordenadas del mapa nativo son `Nc_c=1`, `Rline=2` y `Nc_t=100`, `PRmap_t=5`; sus escalas de velocidad son distintas.

Escalas (subíndice `d` = diseño, `m` = valor interpolado del mapa nativo):

- Flujo: `k_W=mdot_corr,d / Wcorr_m,d`; durante consulta `mdot_corr=k_W Wcorr_m`.
- Compresor: `PR_c=1+k_PRc(PRmap_c−1)` con `k_PRc=(PRc,d−1)/(PRmapc,d−1)`; `eta_c=k_eta_c eta_mapc`.
- Turbina: `PRmap_t=1+(PR_t−1)/k_PRt` con `k_PRt=(PRt,d−1)/(PRmapt,d−1)`; `eta_t=k_eta_t eta_mapt`.
- Giro: `Nmap_c=k_Nc Ncorr(Tt2)` y `Nmap_t=k_Nt Ncorr(Tt3)`; se ajusta cada factor en el mismo **N de diseño**.

Estas escalas son hipótesis educativas explícitas. No se presentan como resultados medidos. Una eficiencia fuera de `(0,1]`, presión sin margen o consulta fuera de una tabla se rechaza. La `Rline=1` procede del parámetro nativo `RlineStall=1` del archivo del compresor; delimita únicamente la referencia de bombeo **representada**, no garantiza margen frente a fenómenos dinámicos.

## Comprobaciones

`tests/test_mapas_turbomaquinaria_47_3.py`: extracción en ejes (13×11 HPC alfa=0, 6×20 HPT), interpolación en nudos y centros de celda, unidades corregidas, escalas, reproducción exacta de diseño, igualdad del giro mecánico y rechazo de extrapolación. La prueba de reproducción coteja dos flujos, ambas eficiencias, relación de compresión, relación de expansión y dosados.

La entrega M47.4 implementa el acoplamiento de mapas, continuidad, cámara, eje y tobera para el área fija de diseño y rechaza resultados fuera del dominio; véase [M47.4](47_4_acoplamiento_motor.md). Estas comprobaciones no validan un motor físico real.
