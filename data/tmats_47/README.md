# Datos públicos NASA T-MATS adaptados a mapas monoeje educativos

`mapas_normalizados.json` contiene una extracción **sin interpolar ni cambiar los valores tabulados** de:

- [NASA T-MATS `Resources/JT9D_Public_NPSSv241/Maps_and_Elements/HPC.map`](https://github.com/nasa/T-MATS/blob/master/Resources/JT9D_Public_NPSSv241/Maps_and_Elements/HPC.map): `TB_Wc`, `TB_PR`, `TB_eff`, solo `alphaMap=0`; otros valores de alpha no se usan.
- [NASA T-MATS `Resources/JT9D_Public_NPSSv241/Maps_and_Elements/HPT.map`](https://github.com/nasa/T-MATS/blob/master/Resources/JT9D_Public_NPSSv241/Maps_and_Elements/HPT.map): `TB_Wp` y `TB_eff`, todos sus valores tabulados.

La procedencia y el SHA-256 de cada archivo original están registrados en el JSON. Reproducir la extracción descargando ambos originales y ejecutando:

```
python scripts/extraer_mapas_tmats_47.py HPC.map HPT.map data/tmats_47/mapas_normalizados.json
```

Licencia original del repositorio NASA T-MATS: **Apache License 2.0**, [licencia íntegra](https://github.com/nasa/T-MATS/blob/master/LICENSE). Los mapas fueron incluidos por NASA como recursos públicos derivados de tablas NEPP; se conserva la atribución. El JSON es una transformación tabular de dos mapas **de componentes** de un JT9D de dos ejes. No constituye un mapa experimental de un turborreactor monoeje. La adaptación de escala a un monoeje es posterior y se calcula explícitamente en `mapas_turbomaquinaria_47.py`. No se distribuye el archivo completo de modelos MATLAB/Simulink.

Los números `WcorrMap` originales son **unidades internas de la tabla NPSS**, no el gasto de nuestro motor en kg/s. La calibración de `Wcorr` a kg/s se efectúa usando un caudal de referencia y los factores de escala. Del mismo modo, los valores originales de `Ncorr` tienen unidades internas de mapa, no rpm mecánicas. Nunca se deben multiplicar directamente por la velocidad de eje.
