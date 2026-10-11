
# Mi primer programa de ingeniería aeroespacial
# Rendimiento térmico de un ciclo Brayton ideal

from pathlib import Path

import numpy as np
import matplotlib

# Agg permite guardar la gráfica sin abrir ventanas ni utilizar Tkinter.
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def calcular_rendimiento(gamma, relacion_presiones):
    # Comprobamos que los datos sean válidos para el ciclo Brayton ideal.
    if gamma <= 1:
        raise ValueError("gamma debe ser mayor que 1.")
    if relacion_presiones <= 1:
        raise ValueError("La relación de presiones debe ser mayor que 1.")

    # Devolvemos el rendimiento como una fracción, no como un porcentaje.
    return 1 - 1 / (relacion_presiones ** ((gamma - 1) / gamma))


# Datos del ciclo: gamma es el cociente entre cp y cv.
#cp = 
#cv = 
#ganma # cp/cv
gamma = 1.4
relacion_presiones = 10

# Calculamos el rendimiento utilizando la función.
rendimiento = calcular_rendimiento(gamma, relacion_presiones)

# Mostramos el rendimiento en porcentaje, redondeado a dos decimales.
print("SIMULADOR DEL CICLO BRAYTON")
print("Relación de presiones:", relacion_presiones)
print("Rendimiento térmico:", round(rendimiento * 100, 2), "%")

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

