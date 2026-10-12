
# Mi primer programa de ingeniería aeroespacial
# Rendimiento térmico de un ciclo Brayton ideal

from pathlib import Path
from math import isclose, isfinite, log

import numpy as np
import matplotlib

# Agg permite guardar la gráfica sin abrir ventanas ni utilizar Tkinter.
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def calcular_rendimiento(gamma, relacion_presiones):
    # Comprobamos que los datos sean válidos para el ciclo Brayton ideal.
    if not isfinite(gamma) or gamma <= 1:
        raise ValueError("gamma debe ser mayor que 1.")
    if not isfinite(relacion_presiones) or relacion_presiones <= 1:
        raise ValueError("La relación de presiones debe ser mayor que 1.")

    # Devolvemos el rendimiento como una fracción, no como un porcentaje.
    return 1 - 1 / (relacion_presiones ** ((gamma - 1) / gamma))


def calcular_rendimientos(gamma, relaciones_presiones=(5, 10, 15, 20, 25)):
    # Reutilizamos el cálculo del ciclo y ordenamos las relaciones de menor a mayor.
    return [
        (relacion, calcular_rendimiento(gamma, relacion) * 100)
        for relacion in sorted(relaciones_presiones)
    ]


def calcular_temperaturas(T1, T3, gamma, relacion_presiones):
    # Reutilizamos las validaciones de gamma y de la relación de presiones.
    calcular_rendimiento(gamma, relacion_presiones)
    if not all(isfinite(T) and T > 0 for T in (T1, T3)):
        raise ValueError("T1 y T3 deben ser temperaturas absolutas positivas y finitas.")

    # Compresión 1→2 y expansión 3→4 isentrópicas, con gamma constante.
    factor = relacion_presiones ** ((gamma - 1) / gamma)
    T2 = T1 * factor
    T4 = T3 / factor
    if not all(isfinite(T) for T in (T2, T4)):
        raise ValueError("Las temperaturas calculadas deben ser finitas.")
    if T3 <= T2:
        raise ValueError("T3 debe superar T2 para aportar calor y producir trabajo neto.")
    return T1, T2, T3, T4


def calcular_balance_energetico(T1, T2, T3, T4, cp):
    if not isfinite(cp) or cp <= 0:
        raise ValueError("cp debe ser positivo y finito, en J/(kg·K).")
    if not all(isfinite(T) and T > 0 for T in (T1, T2, T3, T4)):
        raise ValueError("Todas las temperaturas deben ser positivas y finitas.")
    if not (T2 > T1 and T3 > T2 and T3 > T4 and T4 > T1):
        raise ValueError("Las temperaturas deben permitir compresión, calentamiento, expansión y enfriamiento.")

    # cp·ΔT da J/kg; dividimos entre 1000 para obtener kJ/kg.
    # El trabajo del compresor se expresa como consumo positivo.
    trabajo_compresor = cp * (T2 - T1) / 1000
    trabajo_turbina = cp * (T3 - T4) / 1000
    trabajo_neto = trabajo_turbina - trabajo_compresor
    calor_aportado = cp * (T3 - T2) / 1000
    if not all(isfinite(valor) and valor > 0 for valor in (
        trabajo_compresor, trabajo_turbina, trabajo_neto, calor_aportado
    )):
        raise ValueError("Los trabajos y el calor deben ser finitos y positivos para un ciclo motor.")
    rendimiento_balance = trabajo_neto / calor_aportado
    if not 0 < rendimiento_balance < 1:
        raise ValueError("El rendimiento térmico debe estar entre 0 y 1.")
    return {
        "trabajo_compresor": trabajo_compresor,
        "trabajo_turbina": trabajo_turbina,
        "trabajo_neto": trabajo_neto,
        "calor_aportado": calor_aportado,
        "rendimiento": rendimiento_balance,
    }


def calcular_trabajo_neto(T1, T3, gamma, cp, relacion_presiones):
    # Reutilizamos el cálculo de estados y las validaciones del ciclo motor.
    temperaturas = calcular_temperaturas(T1, T3, gamma, relacion_presiones)
    return calcular_balance_energetico(*temperaturas, cp)["trabajo_neto"]


def calcular_relacion_optima(T1, T3, gamma):
    calcular_rendimiento(gamma, 2)  # Validación de gamma.
    if not all(isfinite(T) and T > 0 for T in (T1, T3)) or T3 <= T1:
        raise ValueError("Se requieren temperaturas finitas con T3 > T1 > 0.")
    # Con x = rp**((gamma-1)/gamma), dw_neto/dx = cp·(T3/x² - T1).
    # La segunda derivada es negativa: x = sqrt(T3/T1) es un máximo.
    relacion_optima = (T3 / T1) ** (gamma / (2 * (gamma - 1)))
    if not isfinite(relacion_optima) or relacion_optima <= 1:
        raise ValueError("La relación óptima debe ser finita y mayor que 1.")
    return relacion_optima


def buscar_optimo_numerico(T1, T3, gamma, cp):
    # El paso de aproximadamente 0.00049 permite localizar bien el máximo.
    relaciones = np.linspace(1.01, 50, 100001)
    trabajos = np.array([
        calcular_trabajo_neto(T1, T3, gamma, cp, relacion)
        for relacion in relaciones
    ])
    indice_maximo = int(np.argmax(trabajos))
    return relaciones, trabajos, indice_maximo


def guardar_grafica_trabajo_neto(relaciones, trabajos, rp_optima, trabajo_maximo, ruta):
    figura, ejes = plt.subplots(figsize=(9, 6))
    ejes.plot(relaciones, trabajos, label="Trabajo específico neto")
    ejes.scatter([rp_optima], [trabajo_maximo], color="red", s=70, zorder=5,
                 label="Máximo analítico (verificado numéricamente)")
    ejes.annotate(f"rp = {rp_optima:.4f}\nTrabajo máximo = {trabajo_maximo:.2f} kJ/kg",
                  xy=(rp_optima, trabajo_maximo), xytext=(15, -55),
                  textcoords="offset points", arrowprops={"arrowstyle": "->"})
    ejes.set_title("Trabajo neto del ciclo Brayton ideal")
    ejes.set_xlabel("Relación de presiones")
    ejes.set_ylabel("Trabajo específico neto [kJ/kg]")
    ejes.grid(True)
    ejes.legend(loc="lower right")
    figura.tight_layout()
    figura.savefig(ruta, dpi=150)
    plt.close(figura)


def calcular_entropias(T1, T2, T3, T4, cp):
    # Aplicamos las mismas validaciones físicas que al balance energético.
    calcular_balance_energetico(T1, T2, T3, T4, cp)
    cp_kj = cp / 1000  # kJ/(kg·K).
    incremento_23 = cp_kj * log(T3 / T2)
    incremento_14 = cp_kj * log(T4 / T1)
    # Comparamos sin redondear: la tolerancia es menor que la precisión impresa.
    if not isclose(incremento_23, incremento_14, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("Los incrementos de entropía 2→3 y 1→4 no coinciden: el ciclo no es isentrópico.")
    s1 = 0.0  # Referencia arbitraria de entropía específica relativa.
    s2 = s1  # Compresión isentrópica.
    s3 = s2 + incremento_23
    s4 = s3  # Expansión isentrópica.
    return s1, s2, s3, s4


def guardar_diagrama_ts(temperaturas, entropias, cp, ruta):
    T1, T2, T3, T4 = temperaturas
    # Validamos también las entradas cuando se llama a esta función por separado.
    esperadas = calcular_entropias(T1, T2, T3, T4, cp)
    if len(entropias) != 4 or not all(
        isclose(s, esperado, rel_tol=1e-9, abs_tol=1e-12)
        for s, esperado in zip(entropias, esperadas)
    ):
        raise ValueError("Las entropías deben corresponder al ciclo con s1 = 0.")
    s1, s2, s3, s4 = entropias
    cp_kj = cp / 1000

    # En una isóbara, s(T) = s_inicial + cp·ln(T/T_inicial).
    # Muestreamos las curvas en el sentido de recorrido del ciclo.
    temperaturas_23 = np.linspace(T2, T3, 100)
    entropias_23 = s2 + cp_kj * np.log(temperaturas_23 / T2)
    temperaturas_41 = np.linspace(T4, T1, 100)
    entropias_41 = s4 + cp_kj * np.log(temperaturas_41 / T4)
    procesos = (
        ([s1, s2], [T1, T2], "1→2: compresión isentrópica"),
        (entropias_23, temperaturas_23, "2→3: calentamiento a presión constante"),
        ([s3, s4], [T3, T4], "3→4: expansión isentrópica"),
        (entropias_41, temperaturas_41, "4→1: enfriamiento a presión constante"),
    )
    figura, ejes = plt.subplots(figsize=(9, 6))
    for valores_s, valores_T, etiqueta in procesos:
        linea, = ejes.plot(valores_s, valores_T, label=etiqueta)
        # Una flecha sobre cada proceso indica el sentido del ciclo.
        if len(valores_s) == 2:
            inicio = (valores_s[0], valores_T[0] + 0.4 * (valores_T[1] - valores_T[0]))
            fin = (valores_s[1], valores_T[0] + 0.6 * (valores_T[1] - valores_T[0]))
        else:
            inicio = (valores_s[40], valores_T[40])
            fin = (valores_s[60], valores_T[60])
        ejes.annotate("", xy=fin, xytext=inicio,
                      arrowprops={"arrowstyle": "->", "color": linea.get_color(), "lw": 2})

    ejes.scatter(entropias, temperaturas, color="black", zorder=5)
    for estado, s, T in zip((1, 2, 3, 4), entropias, temperaturas):
        ejes.annotate(str(estado), (s, T), xytext=(8, 8), textcoords="offset points")
    ejes.set_title("Diagrama T-s del ciclo Brayton ideal")
    ejes.set_xlabel("Entropía específica relativa [kJ/(kg·K)]")
    ejes.set_ylabel("Temperatura [K]")
    ejes.grid(True)
    ejes.margins(x=0.12, y=0.12)
    ejes.legend(loc="upper left", fontsize=8)
    figura.tight_layout()
    figura.savefig(ruta, dpi=150)
    plt.close(figura)


def comprobar_estados_pv(temperaturas, presiones, volumenes, R, gamma):
    # Las presiones se reciben en kPa; Pv = RT requiere Pa si R está en J/(kg·K).
    if not all(len(valores) == 4 for valores in (temperaturas, presiones, volumenes)):
        raise ValueError("Se requieren cuatro temperaturas, presiones y volúmenes.")
    if not isfinite(R) or R <= 0 or not isfinite(gamma) or gamma <= 1:
        raise ValueError("Se requieren R positivo y gamma mayor que 1, ambos finitos.")
    if not all(isfinite(valor) and valor > 0
               for valores in (temperaturas, presiones, volumenes) for valor in valores):
        raise ValueError("Las temperaturas, presiones y volúmenes deben ser positivos y finitos.")
    for estado, (T, p, v) in enumerate(zip(temperaturas, presiones, volumenes), start=1):
        if not isclose(p * 1000 * v, R * T, rel_tol=1e-9, abs_tol=1e-12):
            raise ValueError(f"El estado {estado} no cumple la ecuación del gas ideal.")
    p1, p2, p3, p4 = presiones
    v1, v2, v3, v4 = volumenes
    if not (p2 > p1 and isclose(p2, p3, rel_tol=1e-9)
            and isclose(p4, p1, rel_tol=1e-9)):
        raise ValueError("Las presiones deben corresponder a las dos isóbaras del ciclo Brayton.")
    # Usar kPa en ambos extremos no altera la comprobación de Pv^gamma constante.
    for inicio, fin in ((0, 1), (2, 3)):
        if not isclose(presiones[inicio] * volumenes[inicio] ** gamma,
                       presiones[fin] * volumenes[fin] ** gamma, rel_tol=1e-9):
            raise ValueError("Los estados no cumplen Pv^gamma constante en las isentrópicas.")
    if not (v2 < v1 and v3 > v2 and v4 > v3 and v1 < v4):
        raise ValueError("Los volúmenes no permiten el recorrido del ciclo motor.")


def calcular_estados_pv(temperaturas, cp, gamma, relacion_presiones, p1):
    calcular_rendimiento(gamma, relacion_presiones)
    # Validamos las temperaturas, cp y la coherencia de las etapas isentrópicas.
    calcular_entropias(*temperaturas, cp)
    if not isfinite(p1) or p1 <= 0:
        raise ValueError("p1 debe ser positiva y finita, en kPa.")
    R = cp * (1 - 1 / gamma)  # J/(kg·K), pues R = cp - cv y cv = cp/gamma.
    presiones = (p1, relacion_presiones * p1, relacion_presiones * p1, p1)
    volumenes = tuple(R * T / (p * 1000) for T, p in zip(temperaturas, presiones))
    comprobar_estados_pv(temperaturas, presiones, volumenes, R, gamma)
    return R, presiones, volumenes


def guardar_diagrama_pv(temperaturas, presiones, volumenes, R, gamma, ruta):
    comprobar_estados_pv(temperaturas, presiones, volumenes, R, gamma)
    p1, p2, p3, p4 = presiones
    v1, v2, v3, v4 = volumenes
    # Muestreamos en el sentido del ciclo: las isentrópicas son curvas, no rectas.
    volumenes_12 = np.linspace(v1, v2, 200)
    presiones_12 = p1 * (v1 / volumenes_12) ** gamma
    volumenes_34 = np.linspace(v3, v4, 200)
    presiones_34 = p3 * (v3 / volumenes_34) ** gamma
    procesos = (
        (volumenes_12, presiones_12, "1→2: compresión isentrópica"),
        (np.linspace(v2, v3, 200), np.full(200, p2), "2→3: calentamiento a presión constante"),
        (volumenes_34, presiones_34, "3→4: expansión isentrópica"),
        (np.linspace(v4, v1, 200), np.full(200, p4), "4→1: enfriamiento a presión constante"),
    )
    figura, ejes = plt.subplots(figsize=(9, 6))
    for valores_v, valores_p, etiqueta in procesos:
        linea, = ejes.plot(valores_v, valores_p, label=etiqueta)
        ejes.annotate("", xy=(valores_v[110], valores_p[110]),
                      xytext=(valores_v[90], valores_p[90]),
                      arrowprops={"arrowstyle": "->", "color": linea.get_color(), "lw": 2})
    ejes.scatter(volumenes, presiones, color="black", zorder=5)
    for estado, v, p in zip((1, 2, 3, 4), volumenes, presiones):
        ejes.annotate(str(estado), (v, p), xytext=(8, 8), textcoords="offset points")
    ejes.set_title("Diagrama P-v del ciclo Brayton ideal")
    ejes.set_xlabel("Volumen específico [m³/kg]")
    ejes.set_ylabel("Presión [kPa]")
    ejes.grid(True)
    ejes.margins(x=0.08, y=0.12)
    ejes.legend(loc="upper right", fontsize=8)
    figura.tight_layout()
    figura.savefig(ruta, dpi=150)
    plt.close(figura)


# Datos del ciclo: gas ideal con cp y gamma constantes; gamma = cp/cv.
gamma = 1.4
relacion_presiones = 10
T1 = 288.15  # K: entrada al compresor.
T3 = 1600  # K: entrada a la turbina.
cp = 1005  # J/(kg·K).
p1 = 100  # kPa: presión de entrada al compresor.

# Calculamos el rendimiento utilizando la función.
rendimiento = calcular_rendimiento(gamma, relacion_presiones)
T1, T2, T3, T4 = calcular_temperaturas(T1, T3, gamma, relacion_presiones)
balance = calcular_balance_energetico(T1, T2, T3, T4, cp)
s1, s2, s3, s4 = calcular_entropias(T1, T2, T3, T4, cp)
R, presiones, volumenes = calcular_estados_pv((T1, T2, T3, T4), cp, gamma, relacion_presiones, p1)
p1, p2, p3, p4 = presiones
v1, v2, v3, v4 = volumenes

# Comparamos los valores sin redondear, admitiendo el error numérico de cálculo.
if not isclose(balance["rendimiento"], rendimiento, rel_tol=1e-9, abs_tol=1e-12):
    raise ValueError("El rendimiento del balance no coincide con la fórmula del ciclo ideal.")

# Mostramos el rendimiento en porcentaje, redondeado a dos decimales.
print("SIMULADOR DEL CICLO BRAYTON")
print("Relación de presiones:", relacion_presiones)
print("Rendimiento térmico:", round(rendimiento * 100, 2), "%")
print()
for nombre, temperatura in zip(("T1", "T2", "T3", "T4"), (T1, T2, T3, T4)):
    print(f"{nombre}: {temperatura:.2f} K")
for etiqueta, clave in (
    ("Trabajo específico del compresor (consumido)", "trabajo_compresor"),
    ("Trabajo específico de la turbina (producido)", "trabajo_turbina"),
    ("Trabajo neto", "trabajo_neto"),
    ("Calor aportado", "calor_aportado"),
):
    print(f"{etiqueta}: {balance[clave]:.2f} kJ/kg")
print(f"Rendimiento por balance energético: {balance['rendimiento'] * 100:.2f} %")
print("Comprobación: el balance energético coincide con la fórmula original.")
print()
for estado, entropia in zip((1, 2, 3, 4), (s1, s2, s3, s4)):
    print(f"s{estado}: {entropia:.6f} kJ/(kg·K)")
print(f"Incremento de entropía 2->3: {s3 - s2:.6f} kJ/(kg·K)")
print(f"Incremento de entropía 1->4: {cp / 1000 * log(T4 / T1):.6f} kJ/(kg·K)")
print("Comprobación: ambos incrementos de entropía coinciden.")
print(f"\nConstante específica del gas R: {R:.6f} J/(kg·K)")
print(f"{'Estado':>6} | {'Presión [kPa]':>14} | {'Volumen específico [m³/kg]':>27}")
print("-" * 53)
for estado, p, v in zip((1, 2, 3, 4), presiones, volumenes):
    print(f"{estado:>6} | {p:>14.2f} | {v:>27.6f}")
print("Comprobación: los cuatro estados cumplen Pv = RT y las isentrópicas conservan Pv^gamma.")

# Mostramos una tabla alineada con el rendimiento de cada relación de presiones.
print()
print(f"{'Relación de presiones':>21} | {'Rendimiento térmico (%)':>23}")
print("-" * 47)
for relacion, rendimiento_porcentaje in calcular_rendimientos(gamma):
    print(f"{relacion:>21} | {rendimiento_porcentaje:>23.2f}")

# Generamos 100 relaciones de presiones, incluyendo los extremos 2 y 30.
relaciones_presiones = np.linspace(2, 30, 100)

# Calculamos cada rendimiento con la función y lo convertimos a porcentaje.
rendimientos_porcentaje = np.array([
    calcular_rendimiento(gamma, relacion) * 100
    for relacion in relaciones_presiones
])

# Representamos la relación de presiones (sin unidades) y el rendimiento (%).
plt.figure()
plt.plot(relaciones_presiones, rendimientos_porcentaje)
plt.title(f"Rendimiento térmico del ciclo Brayton ideal (γ = {gamma})")
plt.xlabel("Relación de presiones p₂/p₁ (adimensional)")
plt.ylabel("Rendimiento térmico (%)")
plt.grid(True)
plt.tight_layout()
# Guardamos la gráfica junto a este archivo, aunque se ejecute desde otra carpeta.
ruta_grafica = Path(__file__).resolve().parent / "rendimiento_brayton.png"
plt.savefig(ruta_grafica)
plt.close()

# Guardamos también el diagrama T-s junto al programa, sin abrir ventanas.
ruta_diagrama_ts = Path(__file__).resolve().parent / "diagrama_ts_brayton.png"
guardar_diagrama_ts((T1, T2, T3, T4), (s1, s2, s3, s4), cp, ruta_diagrama_ts)

ruta_diagrama_pv = Path(__file__).resolve().parent / "diagrama_pv_brayton.png"
guardar_diagrama_pv((T1, T2, T3, T4), presiones, volumenes, R, gamma, ruta_diagrama_pv)

# Estudio independiente del óptimo: conservamos los estados del ciclo con rp = 10.
rp_optima_analitica = calcular_relacion_optima(T1, T3, gamma)
relaciones_busqueda, trabajos_busqueda, indice_optimo = buscar_optimo_numerico(T1, T3, gamma, cp)
rp_optima_numerica = float(relaciones_busqueda[indice_optimo])
paso_busqueda = float(relaciones_busqueda[1] - relaciones_busqueda[0])

# Solo podemos verificar el máximo analítico si está dentro del intervalo barrido.
if not relaciones_busqueda[0] <= rp_optima_analitica <= relaciones_busqueda[-1]:
    raise ValueError("El óptimo analítico queda fuera del intervalo de búsqueda [1.01, 50].")
if not isclose(rp_optima_numerica, rp_optima_analitica, rel_tol=0, abs_tol=paso_busqueda):
    raise ValueError("Los óptimos numérico y analítico difieren en más de un paso de búsqueda.")

temperaturas_optimas = calcular_temperaturas(T1, T3, gamma, rp_optima_analitica)
balance_optimo = calcular_balance_energetico(*temperaturas_optimas, cp)
trabajo_maximo = calcular_trabajo_neto(T1, T3, gamma, cp, rp_optima_analitica)
rendimiento_optimo = calcular_rendimiento(gamma, rp_optima_analitica)
if not isclose(balance_optimo["rendimiento"], rendimiento_optimo, rel_tol=1e-9, abs_tol=1e-12):
    raise ValueError("El balance energético no coincide con el rendimiento en el óptimo.")

print("\nÓPTIMO DE TRABAJO ESPECÍFICO NETO")
print(f"Relación de presiones óptima analítica: {rp_optima_analitica:.6f}")
print(f"Relación de presiones óptima numérica: {rp_optima_numerica:.6f}")
print(f"Comprobación: los óptimos coinciden dentro del paso de búsqueda ({paso_busqueda:.6f}).")
print(f"Trabajo neto máximo analítico: {trabajo_maximo:.6f} kJ/kg")
print(f"Trabajo neto máximo numérico: {trabajos_busqueda[indice_optimo]:.6f} kJ/kg")
print(f"T2 en el óptimo analítico: {temperaturas_optimas[1]:.2f} K")
print(f"T4 en el óptimo analítico: {temperaturas_optimas[3]:.2f} K")
print(f"Rendimiento térmico en el óptimo analítico: {rendimiento_optimo * 100:.2f} %")

ruta_trabajo_neto = Path(__file__).resolve().parent / "trabajo_neto_vs_rp.png"
guardar_grafica_trabajo_neto(relaciones_busqueda, trabajos_busqueda,
                            rp_optima_analitica, trabajo_maximo, ruta_trabajo_neto)
