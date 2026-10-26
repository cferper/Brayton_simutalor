"""Adaptador web del turborreactor: formulario, estaciones y SVG educativos.

No calcula balances termodinámicos: el único solucionador físico es el de
combustible_cp_variable. Magnitudes: K, kPa, kJ/kg, m/s y kg/(N·h).
"""

from html import escape
from math import exp, isfinite
from numbers import Real

from combustible_cp_variable import resolver_turborreactor_con_combustible
from propiedades_aire import h
from propiedades_aire import R_AIRE, T_MIN, s0
from tobera_convergente_divergente_cp import _sonico, relacion_areas_adaptada


DEFAULTS_TURBO = {
    "modo_ambiente": "directo", "T_amb": "288.15", "p_amb": "100",
    "altitud_geopotencial": "", "mach": "0", "rp": "10", "eta_c": "0.85",
    "T3": "1600", "delta_pct": "4", "eta_t": "0.90", "eta_m": "0.98",
    "eta_n": "0.95", "pi_d": "1", "eta_b": "0.99", "PCI": "43000",
    "tipo_tobera": "convergente", "epsilon": "1.5",
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
        ("eta_n", "Rendimiento de tobera", "–", "Convergente: afecta a la expansión. C-D: se valida (0 < ηn ≤ 1), pero no interviene en el modelo actual, que admite choques normales irreversibles."),
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
    return {clave: formulario.get(clave, DEFAULTS_TURBO[clave] if clave in ("tipo_tobera", "epsilon") else "")
            for clave in DEFAULTS_TURBO}


def leer_turborreactor(valores):
    """Valida campos y modo (sin mezcla), adapta %->fracción y devuelve kwargs.

    Entrada dict[str,str]; salida dict[str,float|None]. ValueError se muestra
    en Flask; el solucionador valida de nuevo los dominios físicos.
    """
    modo = valores["modo_ambiente"]
    if modo not in ("directo", "ISA"):
        raise ValueError("Selecciona ambiente directo o atmósfera ISA.")
    tipo = valores.get("tipo_tobera", "convergente")
    if tipo not in ("convergente", "convergente_divergente"):
        raise ValueError("Selecciona una tobera convergente o convergente-divergente.")
    activos = ["mach", "rp", "eta_c", "T3", "delta_pct", "eta_t",
               "eta_m", "eta_n", "pi_d", "eta_b", "PCI"]
    if tipo == "convergente_divergente":
        activos.append("epsilon")
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
    if datos["rp"] <= 1:
        raise ValueError("La relación de compresión rp debe ser mayor que 1.")
    if not 0 < datos["eta_n"] <= 1:
        raise ValueError("eta_n debe estar en (0,1], incluso cuando no se aplica a la C-D.")
    porcentaje = datos.pop("delta_pct")
    if not 0 <= porcentaje < 100:
        raise ValueError("La pérdida de presión debe estar entre 0 % y menos de 100 %.")
    datos["delta"] = porcentaje / 100
    datos["tipo_tobera"] = tipo
    if tipo == "convergente_divergente":
        if datos["epsilon"] < 1:
            raise ValueError("Ae/Ag debe ser mayor o igual a 1.")
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
    if n and "temperatura_garganta" in n:
        T_g = n["temperatura_garganta"]
        lista.append({"nombre": "Garganta de tobera C-D", "tipo": "Estático",
                      "T": T_g, "p": n["presion_garganta"],
                      "h": h(T_g) if T_g is not None else None})
    T_e = n["temperatura_salida"] if n else None
    lista.append({"nombre": "Salida de tobera", "tipo": "Estático",
                  "T": T_e,
                  "p": n["presion_salida"] if n else None,
                  "h": (n.get("entalpia_salida", h(T_e) if T_e is not None else None)
                        if n else None)})
    return lista


def svg_componentes(tipo_tobera="convergente"):
    """SVG fijo del flujo y del eje; sin geometría real ni datos físicos."""
    nombres = ("Difusor", "Compresor", "Cámara", "Turbina",
               "Tobera C-D" if tipo_tobera == "convergente_divergente" else "Tobera")
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


def _presion_adaptacion_cd(Tt, pt, epsilon):
    """Presión adaptada [kPa] para Ae/Ag, invirtiendo el área pública de 42.A.

    Tt [K], pt [kPa], epsilon>=1 [-]. ValueError si el área supera la
    expansión disponible en 200–2000 K o falta un intervalo con raíz.
    """
    if any(isinstance(x, bool) or not isinstance(x, Real) for x in (Tt, pt, epsilon)):
        raise ValueError("Tt, pt y Ae/Ag deben ser números reales finitos.")
    try:
        if not all(isfinite(x) for x in (Tt, pt, epsilon)):
            raise ValueError("Tt, pt y Ae/Ag deben ser finitos.")
    except (OverflowError, TypeError) as exc:
        raise ValueError("Tt, pt y Ae/Ag deben ser finitos.") from exc
    if not T_MIN < Tt <= 2000 or pt <= 0 or epsilon < 1:
        raise ValueError("Se exige 200<Tt<=2000 K, pt>0 kPa y Ae/Ag>=1.")
    critico = _sonico(Tt, pt)
    if critico is None:
        raise ValueError("No se alcanza Mach 1 dentro del dominio cp(T).")
    if epsilon == 1:
        # La garganta y la salida coinciden en el límite sónico.
        return critico["p"]
    inferior = pt * exp((s0(T_MIN) - s0(Tt)) / (R_AIRE / 1000)) * (1 + 1e-6)
    area_inferior = relacion_areas_adaptada(Tt, pt, inferior)
    if area_inferior < epsilon:
        raise ValueError("Ae/Ag requiere una salida por debajo del límite de 200 K.")

    # La relación de áreas decrece desde el límite térmico inferior hasta 1
    # al aumentar la contrapresión hacia p*. Nunca tomar la primera presión
    # supersónica válida como cota: su área puede superar el objetivo.
    superior = critico["p"]
    for _ in range(100):
        medio = (inferior + superior) / 2
        try:
            area_medio = relacion_areas_adaptada(Tt, pt, medio)
        except ValueError:
            # Muy cerca del punto sónico, la función pública sólo permite
            # la rama estrictamente supersónica. Área límite = 1 < epsilon.
            superior = medio
            continue
        if area_medio > epsilon:
            inferior = medio
        else:
            superior = medio
        if abs(area_medio-epsilon) <= 2e-10 * epsilon:
            return medio
    candidato = (inferior + superior) / 2
    try:
        residuo = abs(relacion_areas_adaptada(Tt, pt, candidato)-epsilon)
    except ValueError as exc:
        raise ValueError("No se ha encerrado una adaptación supersónica válida.") from exc
    if residuo > 2e-8 * epsilon:
        raise ValueError("No converge la presión de adaptación dentro del dominio cp(T).")
    return candidato


def _adaptacion_cd(resultado):
    """Comparaciones geométrica y ambiental independientes, con diagnóstico."""
    n = resultado["tobera"]
    if n is None or "relacion_areas" not in n:
        return None
    t = resultado["turbina"]
    presion = resultado["ambiente"]["presion"]
    respuesta = {"presion_adaptada": None, "epsilon_adaptada": None,
                 "error_presion": None, "error_epsilon": None}
    try:
        respuesta["presion_adaptada"] = _presion_adaptacion_cd(
            t["T4"], t["p4"], n["relacion_areas"])
    except (ValueError, ArithmeticError) as exc:
        respuesta["error_presion"] = str(exc)
    try:
        respuesta["epsilon_adaptada"] = relacion_areas_adaptada(
            t["T4"], t["p4"], presion)
    except (ValueError, ArithmeticError) as exc:
        respuesta["error_epsilon"] = str(exc)
    return respuesta


def preparar_vista_turborreactor(resultado):
    """Retorna dict de estaciones y tres SVG seguros para Jinja; sin física nueva."""
    estados = estaciones_turborreactor(resultado)
    return {"estaciones": estados,
            "adaptacion_cd": _adaptacion_cd(resultado),
            "svg_componentes": svg_componentes(resultado["diagnosticos"].get("tipo_tobera")),
            "svg_temperaturas": svg_evolucion(estados,"T","Temperatura total","K"),
            "svg_presiones": svg_evolucion(estados,"p","Presión total","kPa")}
