"""Aire seco ideal de composición fija con capacidad calorífica variable.

N2 (78 % molar) y O2 (21 %) usan Shomate del NIST Chemistry WebBook;
Ar (1 %) usa cp,molar=5 R_u/2 (gas ideal monoatómico).

Rango cerrado: 200–2000 K. Presión en kPa, referencia 100 kPa (1 bar).
cp en J/(kg K), h en kJ/kg y s0/s en kJ/(kg K). Tanto h como s0
valen cero en 298,15 K; son diferencias, NO magnitudes absolutas.
Este módulo no interviene todavía en el solucionador Brayton existente.

NIST, consultado el 23-10-2026:
https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Mask=1 (N2)
https://webbook.nist.gov/cgi/cbook.cgi?ID=C7782447&Mask=1 (O2)
https://webbook.nist.gov/cgi/cbook.cgi?ID=C7440371&Mask=1 (Ar)
"""

from math import isfinite, log
from numbers import Real


T_MIN = 200.0  # K, inclusive
T_MAX = 2000.0  # K, inclusive
T_REF = 298.15  # K
P_REF = 100.0  # kPa = 1 bar, presión estándar del NIST
R_UNIVERSAL = 8.31446261815324  # J/(mol K)

# Fracciones MOLARES y masas molares en kg/mol; NIST Chemistry WebBook.
_ESPECIES = (
    ("N2", 0.78, 0.0280134),
    ("O2", 0.21, 0.0319988),
    ("Ar", 0.01, 0.039948),
)
MASA_MOLAR = sum(y * M for _, y, M in _ESPECIES)  # kg/mol
R_AIRE = R_UNIVERSAL / MASA_MOLAR  # J/(kg K)

# (límite entre tramos [K], tramo inferior, tramo superior).
# Coeficientes NIST (A, B, C, D, E, F, G, H); t = T/1000.
# N2: 100–500 / 500–2000 K; O2: 100–700 / 700–2000 K.
_SHOMATE = {
    "N2": (
        500.0,
        (28.98641, 1.853978, -9.647459, 16.63537, 0.000117,
         -8.671914, 226.4168, 0.0),
        (19.50583, 19.88705, -8.598535, 1.369784, 0.527601,
         -4.935202, 212.3900, 0.0),
    ),
    "O2": (
        700.0,
        (31.32234, -20.23531, 57.86644, -36.50624, -0.007374,
         -8.903471, 246.7945, 0.0),
        (30.03235, 8.772972, -3.988133, 0.788313, -0.741599,
         -11.32468, 236.1663, 0.0),
    ),
}


def _real_finito(valor):
    """Distingue números reales finitos de bool y tipos no numéricos."""
    if isinstance(valor, bool) or not isinstance(valor, Real):
        return False
    try:
        return isfinite(valor)
    except (OverflowError, TypeError, ValueError):
        return False


def _temperatura(T):
    if not _real_finito(T) or not T_MIN <= T <= T_MAX:
        raise ValueError(f"T debe ser un número real finito entre {T_MIN:g} y {T_MAX:g} K.")
    return float(T)


def _coeficientes(nombre, T):
    limite, bajo, alto = _SHOMATE[nombre]
    return bajo if T <= limite else alto


def _cp_shomate(T, c):
    A, B, C, D, E, _, _, _ = c
    t = T / 1000.0
    return A + B*t + C*t*t + D*t*t*t + E/(t*t)  # J/(mol K)


def _h_shomate(T, c):
    A, B, C, D, E, F, _, H = c
    t = T / 1000.0
    return 1000.0 * (A*t + B*t*t/2 + C*t**3/3 + D*t**4/4 - E/t + F - H)


def _s_shomate(T, c):
    A, B, C, D, E, _, G, _ = c
    t = T / 1000.0
    return A*log(t) + B*t + C*t*t/2 + D*t**3/3 - E/(2*t*t) + G


def _incremento_molar(nombre, T, primitiva):
    """Integral desde T_REF, enlazando tramos sin saltos de h ni s0."""
    limite, bajo, alto = _SHOMATE[nombre]
    if T <= limite:
        return primitiva(T, bajo) - primitiva(T_REF, bajo)
    return (primitiva(limite, bajo) - primitiva(T_REF, bajo)
            + primitiva(T, alto) - primitiva(limite, alto))


def cp(T):
    """Capacidad calorífica másica del aire, J/(kg K), 200 <= T <= 2000 K."""
    T = _temperatura(T)
    suma = 0.01 * 2.5 * R_UNIVERSAL  # Ar: monoatómico
    for nombre, y, _ in _ESPECIES[:2]:
        suma += y * _cp_shomate(T, _coeficientes(nombre, T))
    return suma / MASA_MOLAR


def h(T):
    """Entalpía másica relativa a T_REF, kJ/kg; h(T_REF)=0."""
    T = _temperatura(T)
    suma = 0.01 * 2.5 * R_UNIVERSAL * (T - T_REF)
    for nombre, y, _ in _ESPECIES[:2]:
        suma += y * _incremento_molar(nombre, T, _h_shomate)
    return suma / (1000.0 * MASA_MOLAR)


def s0(T):
    """Entropía térmica relativa a T_REF y P_REF, kJ/(kg K)."""
    T = _temperatura(T)
    suma = 0.01 * 2.5 * R_UNIVERSAL * log(T / T_REF)
    for nombre, y, _ in _ESPECIES[:2]:
        suma += y * _incremento_molar(nombre, T, _s_shomate)
    return suma / (1000.0 * MASA_MOLAR)


def s(T, p):
    """Entropía específica relativa al estado (T_REF,P_REF), kJ/(kg K).

    p en kPa: s(T,p) = s0(T) - (R_AIRE/1000) ln(p/P_REF).
    """
    T = _temperatura(T)
    if not _real_finito(p) or p <= 0:
        raise ValueError("p debe ser una presión real, positiva y finita, en kPa.")
    # Diferencia de logaritmos: evita que p/P_REF subdesborde para p > 0.
    return s0(T) - (R_AIRE / 1000.0) * (log(p) - log(P_REF))


def gamma(T):
    """Cociente de calores específicos cp(T)/cv(T), adimensional."""
    calor = cp(T)
    return calor / (calor - R_AIRE)


def T_desde_h(entalpia):
    """Invierte h(T) [kJ/kg] por bisección y devuelve temperatura [K].

    Rechaza entradas fuera del intervalo entálpico 200–2000 K.
    Monotonía asegurada por cp(T)>0 en todo el intervalo.
    """
    if not _real_finito(entalpia):
        raise ValueError("La entalpía debe ser un número real finito en kJ/kg.")
    inferior, superior = T_MIN, T_MAX
    h_min, h_max = h(inferior), h(superior)
    if not h_min <= entalpia <= h_max:
        raise ValueError("La entalpía está fuera del dominio de 200–2000 K.")
    if entalpia == h_min:
        return inferior
    if entalpia == h_max:
        return superior
    for _ in range(80):
        medio = (inferior + superior) / 2.0
        if h(medio) < entalpia:
            inferior = medio
        else:
            superior = medio
        if superior - inferior <= 1e-10:  # K; error de intervalo, no error físico
            return (inferior + superior) / 2.0
    return (inferior + superior) / 2.0
