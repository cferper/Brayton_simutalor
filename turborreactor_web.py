"""Adaptador web del turborreactor: formulario, estaciones y SVG educativos.

No calcula balances termodinámicos: el único solucionador físico es el de
combustible_cp_variable. Magnitudes: K, kPa, kJ/kg, m/s y kg/(N·h).
"""

from html import escape
from math import isfinite

from combustible_cp_variable import resolver_turborreactor_con_combustible
from propiedades_aire import h


DEFAULTS_TURBO = {
    "modo_ambiente": "directo", "T_amb": "288.15", "p_amb": "100",
    "altitud_geopotencial": "", "mach": "0", "rp": "10", "eta_c": "0.85",
    "T3": "1600", "delta_pct": "4", "eta_t": "0.90", "eta_m": "0.98",
    "eta_n": "0.95", "pi_d": "1", "eta_b": "0.99", "PCI": "43000",
}

EJEMPLOS_TURBO = {
    "estatico": dict(DEFAULTS_TURBO),
    "vuelo": {**DEFAULTS_TURBO, "mach": "0.7"},
    "isa": {**DEFAULTS_TURBO, "modo_ambiente": "ISA", "T_amb": "",
            "p_amb": "", "altitud_geopotencial": "10000", "mach": "0.5"},
}

GRUPOS_TURBO = (
    ("Ambiente y vuelo", (
        ("mach", "Mach de vuelo", "–", "Velocidad respecto a la del sonido; sólo régimen subsónico."),
        ("T_amb", "Temperatura ambiente", "K", "Temperatura estática; sólo en modo directo."),
        ("p_amb", "Presión ambiente", "kPa", "Presión estática; sólo en modo directo."),
        ("altitud_geopotencial", "Altitud ISA", "m", "Altitud geopotencial de 0 a 20 000 m; sólo modo ISA."),
    )),
    ("Compresor y cámara", (
        ("rp", "Relación de compresión", "–", "Presión total de salida dividida por la de entrada; mayor que uno."),
        ("eta_c", "Rendimiento isentrópico del compresor", "–", "Eficiencia entre cero y uno."),
        ("T3", "Temperatura de entrada a turbina", "K", "Temperatura total prescrita; entre 200 y 2000 K."),
        ("delta_pct", "Pérdida de presión en cámara", "%", "Porcentaje de pérdida total, desde cero hasta menos de 100 %."),
    )),
    ("Turbina, difusor y tobera", (
        ("eta_t", "Rendimiento isentrópico de turbina", "–", "Eficiencia de expansión de la turbina."),
        ("eta_m", "Rendimiento mecánico del eje", "–", "Fracción del trabajo de turbina que llega al compresor."),
        ("pi_d", "Recuperación de presión del difusor", "–", "Relación de presiones totales; hasta uno."),
        ("eta_n", "Rendimiento de tobera", "–", "Conversión del salto entálpico en velocidad."),
    )),
    ("Combustible equivalente", (
        ("eta_b", "Rendimiento de combustión", "–", "Fracción efectiva del PCI que aporta energía."),
        ("PCI", "Poder calorífico inferior", "kJ/kg", "Energía química específica del combustible equivalente."),
    )),
)


def valores_turborreactor(formulario=None):
    """Devuelve dict de cadenas; conserva incluso las entradas erróneas en POST."""
    if formulario is None:
        return dict(DEFAULTS_TURBO)
    return {clave: formulario.get(clave, "") for clave in DEFAULTS_TURBO}


def leer_turborreactor(valores):
    """Valida campos y modo (sin mezcla), adapta %->fracción y devuelve kwargs.

    Entrada dict[str,str]; salida dict[str,float|None]. ValueError se muestra
    en Flask; el solucionador valida de nuevo los dominios físicos.
    """
    modo = valores["modo_ambiente"]
    if modo not in ("directo", "ISA"):
        raise ValueError("Selecciona ambiente directo o atmósfera ISA.")
    activos = ["mach", "rp", "eta_c", "T3", "delta_pct", "eta_t",
               "eta_m", "eta_n", "pi_d", "eta_b", "PCI"]
    if modo == "directo":
        if valores["altitud_geopotencial"].strip():
            raise ValueError("No combines altitud ISA con temperatura y presión directas.")
        activos += ["T_amb", "p_amb"]
    else:
        if valores["T_amb"].strip() or valores["p_amb"].strip():
            raise ValueError("En modo ISA deja vacías temperatura y presión directas.")
        activos.append("altitud_geopotencial")
    datos = {}
    for nombre in activos:
        try:
            valor = float(valores[nombre].strip())
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError(f"El campo {nombre} debe ser un número.") from exc
        if not isfinite(valor):
            raise ValueError(f"El campo {nombre} debe ser finito.")
        datos[nombre] = valor
    porcentaje = datos.pop("delta_pct")
    if not 0 <= porcentaje < 100:
        raise ValueError("La pérdida de presión debe estar entre 0 % y menos de 100 %.")
    datos["delta"] = porcentaje / 100
    return datos


def simular_turborreactor(valores):
    """Dict de resultados científicos: llama una vez al solucionador M37."""
    argumentos = leer_turborreactor(valores)
    return resolver_turborreactor_con_combustible(**argumentos)


def estaciones_turborreactor(resultado):
    """Seis dicts con nombre, tipo, T[K], p[kPa] y h[kJ/kg]."""
    a = resultado["ambiente"]
    d = resultado["difusor"]
    c = resultado["compresor"]
    b = resultado["combustor"]
    t = resultado["turbina"]
    n = resultado["tobera"]
    pares = (
        ("Ambiente exterior", "Estático", a["temperatura"], a["presion"]),
        ("Entrada a compresor · tras difusor", "Remanso", d["temperatura_remanso"], d["presion_remanso"]),
        ("Salida de compresor", "Remanso", c["T2"], c["p2"]),
        ("Salida de cámara · entrada a turbina", "Remanso", b["T3"], b["p3"]),
        ("Salida de turbina · entrada a tobera", "Remanso", t["T4"], t["p4"]),
    )
    lista = [{"nombre": nombre, "tipo": tipo, "T": T, "p": p, "h": h(T)}
             for nombre, tipo, T, p in pares]
    lista.append({"nombre": "Salida de tobera", "tipo": "Estático",
                  "T": n["temperatura_salida"] if n else None,
                  "p": n["presion_salida"] if n else None,
                  "h": n["entalpia_salida"] if n else None})
    return lista


def svg_componentes():
    """SVG fijo del flujo y del eje; sin geometría real ni datos físicos."""
    nombres = ("Difusor", "Compresor", "Cámara", "Turbina", "Tobera")
    etiquetas = ("pₜ ↓", "Tₜ, pₜ ↑", "Tₜ ↑", "Tₜ, pₜ ↓", "V ↑")
    figuras = []
    for i, (nombre, etiqueta) in enumerate(zip(nombres, etiquetas)):
        x = 20 + 142*i
        figuras.append(f'<rect x="{x}" y="78" width="118" height="66" rx="8" fill="#e9f2fa" stroke="#174a70"/>')
        figuras.append(f'<text x="{x+59}" y="104" text-anchor="middle" font-weight="600">{nombre}</text>')
        figuras.append(f'<text x="{x+59}" y="125" text-anchor="middle" font-size="13">{etiqueta}</text>')
        if i < 4:
            figuras.append(f'<path d="M{x+120} 111 h17 l-5 -5 m5 5 l-5 5" stroke="#2563a6" stroke-width="2" fill="none"/>')
    figuras.append('<path d="M221 73 V33 H505 V73" stroke="#c08022" stroke-width="3" fill="none"/>')
    figuras.append('<text x="363" y="22" text-anchor="middle" fill="#8b5a16">Eje mecánico · turbina → compresor</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 170" role="img" '
            'aria-label="Difusor, compresor, cámara, turbina y tobera, con eje mecánico">'
            '<g fill="#172b42" font-family="sans-serif" font-size="15">'+''.join(figuras)+'</g></svg>')


def svg_evolucion(estaciones, clave, etiqueta, unidad):
    """Gráfico SVG de cuatro estados de remanso; excluye los estáticos."""
    nucleo = [e for e in estaciones if e["tipo"] == "Remanso"]
    valores = [e[clave] for e in nucleo]
    techo = max(valores)*1.14
    piso = 0
    puntos = [(66 + i*137, 198 - (v-piso)/(techo-piso)*156)
              for i, v in enumerate(valores)]
    trazado = ' '.join(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}' for i,(x,y) in enumerate(puntos))
    piezas = [f'<path d="{trazado}" fill="none" stroke="#2563a6" stroke-width="3"/>',
              '<path d="M55 20 V198 H640" fill="none" stroke="#74859a"/>']
    for i, ((x,y), v) in enumerate(zip(puntos,valores)):
        piezas.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#174a70"/>')
        piezas.append(f'<text x="{x:.1f}" y="{max(y-11, 18):.1f}" text-anchor="middle">{v:.1f}</text>')
        piezas.append(f'<text x="{x:.1f}" y="217" text-anchor="middle">{i+1}</text>')
    titulo=escape(etiqueta)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 690 249" '
            f'role="img" aria-label="{titulo} de cuatro estaciones de remanso">'
            '<g font-family="sans-serif" font-size="12" fill="#172b42">'
            f'<text x="55" y="13">{titulo} [{escape(unidad)}]</text>'
            +''.join(piezas)+'</g></svg>')


def preparar_vista_turborreactor(resultado):
    """Retorna dict de estaciones y tres SVG seguros para Jinja; sin física nueva."""
    estados = estaciones_turborreactor(resultado)
    return {"estaciones": estados, "svg_componentes": svg_componentes(),
            "svg_temperaturas": svg_evolucion(estados,"T","Temperatura total","K"),
            "svg_presiones": svg_evolucion(estados,"p","Presión total","kPa")}
