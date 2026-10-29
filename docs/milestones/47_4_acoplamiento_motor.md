# Milestone 47.4 — Solución estacionaria monoeje con mapas escalados

## Alcance

`acoplamiento_motor_mapa_47.py` determina un punto **estacionario condicionado** de un turborreactor monoeje idealizado. Utiliza los mapas HPC/HPT de NASA T-MATS adaptados en 47.3 como funciones de compresor y turbina, y las funciones existentes de propiedades `cp(T)`, difusor, cámara, eje y tobera. El JT9D original no se reproduce ni se atribuyen al modelo dimensiones o ensayos reales. El estado de diseño y el origen de los mapas se documentan en [47.3](47_3_mapas_turbomaquinaria.md).

## Grados de libertad y cierre matemático

Datos prescritos: ambiente, Mach exterior subsónico, recuperación del difusor, `Tt3` (consigna térmica), pérdida de presión en cámara, eficiencia mecánica, rendimiento y PCI del combustible equivalente, área de garganta fija, tipo de tobera y `Ae/Ag` si es C-D. No se permite imponer adicionalmente el caudal, la compresión o el rendimiento de las turbomáquinas. Las incógnitas independientes son:

1. `N`: revoluciones mecánicas **comunes a compresor y turbina**.
2. `Rline`: coordenada de carga del mapa del compresor.
3. `PRt`: relación de expansión del mapa de turbina.

Para cada tentativa `(N,Rline,PRt)`, las consultas de mapas determinan `mdot_a`, `PRc`, `ηc`, `mdot_g,mapa` y `ηt`. El compresor existente determina `h2` y trabajo específico. La cámara resuelve `f` a partir de `Tt3`; el módulo de turbina existente calcula `p4` **satisfaciendo el balance de potencia** por su ecuación de eje, con el rendimiento del mapa. La tobera física proporciona un flujo superficial `Gg` dependiente del régimen. Las tres ecuaciones independientes (adimensionalizadas) son:

\[
R_1=\frac{PR_{t,map}-p_{t3}/p_{t4,eje}}{PR_{t,d}},\qquad
R_2=\frac{\dot m_a(1+f)-\dot m_{g,map}}{\dot m_{g,d}},\qquad
R_3=\frac{\dot m_a(1+f)-G_g A_g}{\dot m_{g,d}}.
\]

El combustible cumple `mdot_f=f·mdot_a`; por tanto `mdot_g=mdot_a+mdot_f`. La corrección de giro se aplica individualmente a `Tt2` y `Tt3`, manteniendo **una sola** `N` física. Se verifican además en unidades dimensionales los cierres de masa, el trabajo del eje y el área prescrita. Para admisión, un área y Mach locales opcionales se contrastan con el caudal del motor: una sección incompatible se rechaza; un área de captación exterior no constituye por sí sola un cierre de aspiración estática.

## Método numérico y diagnósticos

Newton en tres variables con Jacobiano por diferencias finitas, pivotado parcial en el sistema lineal y búsqueda de paso reducido hasta disminuir estrictamente la norma residual. Cerca de los bordes de mapas puede emplearse derivada unilateral **dentro** del dominio, sin extrapolación. La convergencia requiere `||R||₂ ≤ 2·10⁻⁷` y cierres dimensionales; una detención por agotamiento, singularidad o salida del dominio produce `disponible=False`, con motivo, sin empuje inventado. Máximo 35 iteraciones por defecto. Las escalas de residuo son los valores de diseño; la tolerancia representa aproximadamente un error relativo máximo de masa de 2·10⁻⁷ sobre `mdot_g,d` y se verifica de nuevo dimensionalmente. La temperatura y presión de entrada de los mapas se calculan con las propiedades de la solución, sin `γ` constante.

## Resultados reproducibles

Con el diseño 47.3: `T∞=288,15 K`, `p∞=100 kPa`, `M∞=0`, `Tt3=1600 K`, `A_g=0,047348116435 m²`, tobera convergente, `πd=1`, `ηn=0,95`: el punto reproducido tiene `N=20 000 rpm`, `Rline=2`, `mdot_a=20 kg/s`, `mdot_g≈20,560564 kg/s`, `PRc=10` y empuje absoluto ≈ `19,165 kN`. La igualdad es consecuencia **intencional de la calibración del punto de diseño**, no validación independiente. En vuelo a `M∞=0,4`, manteniendo los demás datos, el algoritmo requiere tres iteraciones y predice aproximadamente `mdot_a=21,29 kg/s`, `N=20 139 rpm`; este resultado solo caracteriza el modelo hipotético y sus mapas escalados. El área de garganta incrementada un 10 % respecto al diseño se rechaza por salir del dominio admitido, sin extrapolar.

## Limitaciones y aspectos pendientes

- Geometría de captación no determina la aspiración en estático. La admisión usa remanso y `πd`, y opcionalmente verifica continuidad local; **no** resuelve un campo de velocidades tridimensional.
- El modelo supone flujo estacionario monoeje, único control térmico `Tt3`, una cámara simplificada de aire equivalente y pérdidas prescritas. No implementa control de régimen, dinámica, surge real ni límites térmicos y mecánicos certificados.
- Los mapas HPC/HPT son formas públicas adaptadas; su escalado no garantiza correspondencia con ningún motor. Se rechaza extrapolar fuera de las mallas y una ausencia de solución es un resultado válido.
- Una tobera C-D puede exigir estados de choque cuyo solucionador histórico declare no resueltos; no se introducen nuevos algoritmos de choque ni pérdidas externas. Las modalidades previas A (caudal impuesto) y B (geometría fija) permanecen independientes.

## Pruebas

`tests/test_acoplamiento_motor_47_4.py`: reproducción del diseño; continuidad de compresor, combustible, turbina y tobera; balance de eje y cámara; perturbaciones de Mach, presión, temperatura y garganta; salida de dominio; reproducibilidad; máximo de iteraciones; integración web A/B/C y comprobación opcional de continuidad de admisión. El cierre global y la regresión relacionada figuran en [47.5](47_5_verificacion_cierre.md).
