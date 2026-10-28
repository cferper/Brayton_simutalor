"""Adaptador web del turborreactor: formulario, estaciones y SVG educativos.

No calcula balances termodinámicos: el único solucionador físico es el de
combustible_cp_variable. Magnitudes: K, kPa, kJ/kg, m/s y kg/(N·h).
"""

from html import escape
from math import exp, isfinite
from numbers import Real

from combustible_cp_variable import resolver_turborreactor_con_combustible
from propiedades_aire import h
from propiedades_aire import R_AIRE, T_MIN, s, s0
from tobera_convergente_divergente_cp import _sonico, relacion_areas_adaptada
from perfil_tobera_cp_variable import perfil_tobera_cp_variable


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


def datos_empuje_grafica(resultado):
    """Cuatro términos específicos [N/(kg/s aire)]; None si faltan datos."""
    p = resultado['prestaciones']
    claves = ('empuje_especifico_salida', 'resistencia_entrada',
              'empuje_especifico_presion', 'empuje_especifico_neto')
    valores = [p.get(clave) for clave in claves]
    if any(v is None or not isinstance(v, Real) or not isfinite(v)
           for v in valores):
        return None
    salida, resistencia, presion, neto = valores
    # El solucionador ya incluye (1+f) en salida y presión.
    if abs(salida - resistencia + presion - neto) > 1e-8 * max(1, *(abs(v) for v in valores)):
        raise ValueError('Las contribuciones no reproducen el empuje neto.')
    return (salida, -resistencia if resistencia else 0.0, presion, neto)


def svg_descomposicion_empuje(resultado):
    """Barras firmadas de contribuciones y resultante, sin nueva física."""
    datos = datos_empuje_grafica(resultado)
    if datos is None:
        return None
    nombres = ('Salida (1+f) Ve', 'Entrada −V0', 'Presión (pe−p∞)', 'Neto Fs')
    colores = ('#267c72', '#b05c47', '#8c64ac', '#225f9b')
    escala = max(abs(v) for v in datos) or 1
    cero, amplitud = 365, 258
    piezas = ['<path d="M365 38 V258" stroke="#66798c" stroke-width="1.5"/>',
              '<text x="365" y="21" text-anchor="middle">0</text>']
    for i, (nombre, valor, color) in enumerate(zip(nombres, datos, colores)):
        y = 50 + 55*i
        largo = abs(valor)/escala*amplitud
        x = cero if valor >= 0 else cero - largo
        piezas.append(f'<text x="14" y="{y+17}" font-size="14">{escape(nombre)}</text>')
        piezas.append(f'<rect x="{x:.2f}" y="{y}" width="{largo:.2f}" height="24" rx="4" fill="{color}"/>')
        texto_x = min(690, cero+largo+8) if valor >= 0 else max(8, cero-largo-8)
        ancla = 'start' if valor >= 0 else 'end'
        piezas.append(f'<text x="{texto_x:.2f}" y="{y+17}" text-anchor="{ancla}" font-size="12">{valor:+.2f}</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 710 300" '
            'role="img" aria-label="Descomposición firmada del empuje específico neto">'
            '<g font-family="sans-serif" fill="#172b42">'
            '<text x="14" y="289" font-size="13">Contribuciones y neto [N/(kg/s de aire)]</text>'
            + ''.join(piezas) + '</g></svg>')


def datos_ts_turborreactor(estaciones):
    """Puntos discretos (estación, s, T, tipo) de remanso y salida estática."""
    nucleo = [e for e in estaciones if e['tipo'] == 'Remanso']
    if len(nucleo) != 4:
        raise ValueError('El diagrama T–s requiere cuatro estados de remanso.')
    puntos = []
    for indice, e in enumerate(nucleo, 1):
        puntos.append((str(indice), s(e['T'], e['p']), e['T'], 'Remanso'))
    salida = next((e for e in estaciones if e['nombre'] == 'Salida de tobera'), None)
    if salida and salida['T'] is not None and salida['p'] is not None:
        puntos.append(('E', s(salida['T'], salida['p']), salida['T'], 'Estático'))
    return tuple(puntos)


def svg_ts_turborreactor(estaciones):
    """Estados cp(T) y conexiones esquemáticas; nunca curvas de proceso."""
    puntos = datos_ts_turborreactor(estaciones)
    xs = [p[1] for p in puntos]
    ys = [p[2] for p in puntos]
    dx = max(max(xs)-min(xs), 0.1)
    dy = max(max(ys)-min(ys), 100.0)
    xmin, ymin = min(xs)-0.16*dx, min(ys)-0.14*dy
    xmax, ymax = max(xs)+0.16*dx, max(ys)+0.15*dy
    escalar = lambda p: (82 + (p[1]-xmin)/(xmax-xmin)*526,
                         275 - (p[2]-ymin)/(ymax-ymin)*232)
    coords = [escalar(p) for p in puntos]
    nombres = ('Compresión', 'Cámara (aire equivalente)', 'Turbina', 'Tobera (estático)')
    colores = ('#2563a6', '#b35d2e', '#277b71', '#8155a8')
    piezas = ['<path d="M72 26 V275 H648" stroke="#6d8093" fill="none"/>']
    for i in range(len(puntos)-1):
        x1,y1 = coords[i]
        x2,y2 = coords[i+1]
        color = colores[i]
        piezas.append(f'<path d="M{x1:.2f},{y1:.2f} L{x2:.2f},{y2:.2f}" '
                      f'stroke="{color}" stroke-width="2.5" stroke-dasharray="6 5" fill="none"/>')
    for p, (x,y) in zip(puntos, coords):
        label, entropia, temperatura, tipo = p
        piezas.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5" fill="#133d61"/>')
        a_la_derecha = x < 450
        texto_x = x + 9 if a_la_derecha else x - 9
        anclaje = 'start' if a_la_derecha else 'end'
        # E puede quedar muy próximo a 4 tras un choque: rotularlo debajo.
        texto_y = y + 20 if label == 'E' else y - 9
        piezas.append(f'<text x="{texto_x:.2f}" y="{texto_y:.2f}" '
                      f'text-anchor="{anclaje}" font-size="12" '
                      'paint-order="stroke" stroke="white" stroke-width="3" '
                      'stroke-linejoin="round">'
                      f'{label}: {temperatura:.1f} K; s={entropia:.3f}</text>')
    for i, (nombre, color) in enumerate(zip(nombres[:len(puntos)-1], colores)):
        x = 35 if i % 2 == 0 else 360
        y = 313 + 20*(i//2)
        piezas.append(f'<path d="M{x} {y} h23" stroke="{color}" stroke-width="2.5" '
                      'stroke-dasharray="6 5"/>')
        piezas.append(f'<text x="{x+30}" y="{y+4}" font-size="12">{escape(nombre)}</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 710 366" '
            'style="max-height:420px" '
            'role="img" aria-label="Diagrama T–s de estaciones discretas, con uniones esquemáticas">'
            '<g font-family="sans-serif" fill="#172b42">'
            '<text x="76" y="16" font-size="13">T [K]</text>'
            '<text x="360" y="296" text-anchor="middle" font-size="13">s [kJ/(kg·K)]</text>'
            + ''.join(piezas) + '</g></svg>')


def datos_tobera_graficas(resultado):
    """Estados estáticos discretos (Mach, p[kPa]) ya resueltos por la tobera.

    No calcula perfiles intermedios. None indica falta de salida resuelta.
    """
    n = resultado.get('tobera')
    if not n or n.get('mach_salida') is None or n.get('presion_salida') is None:
        return None

    def punto(nombre, mach, presion, papel):
        if mach is None or presion is None or not all(
                isinstance(v, Real) and not isinstance(v, bool) and isfinite(v)
                for v in (mach, presion)) or mach < 0 or presion <= 0:
            raise ValueError('Estado estático de tobera inválido para el gráfico.')
        return {'nombre': nombre, 'mach': float(mach),
                'presion': float(presion), 'papel': papel}

    estados = []
    tipo = resultado['diagnosticos']['tipo_tobera']
    choque = n.get('choque_normal')
    if tipo == 'convergente_divergente':
        if n.get('mach_garganta') is not None and n.get('presion_garganta') is not None:
            estados.append(punto('Garganta', n['mach_garganta'], n['presion_garganta'], 'garganta'))
        if choque:
            estados.append(punto('Antes choque', choque['M1'], choque['p1'], 'choque_antes'))
            estados.append(punto('Después choque', choque['M2'], choque['p2'], 'choque_despues'))
        estados.append(punto('Salida', n['mach_salida'], n['presion_salida'], 'salida'))
    else:
        etiqueta = ('Salida = garganta' if n.get('regimen') == 'bloqueado'
                    else 'Salida')
        estados.append(punto(etiqueta, n['mach_salida'], n['presion_salida'], 'salida'))

    ambiente = resultado['ambiente']['presion']
    if not isinstance(ambiente, Real) or not isfinite(ambiente) or ambiente <= 0:
        raise ValueError('Presión ambiente inválida para el gráfico.')
    return {'estados': tuple(estados), 'ambiente': float(ambiente),
            'regimen': n['regimen'], 'tipo': tipo}


def svg_estados_tobera(datos, magnitud):
    """SVG discreto con las mismas abscisas para Mach y presión estática.

    Los ordinales de estado no son distancia axial ni relación de áreas.
    """
    if datos is None:
        return None
    if magnitud not in ('mach', 'presion'):
        raise ValueError('Magnitud gráfica de tobera desconocida.')
    estados = datos['estados']
    valores = [e[magnitud] for e in estados]
    referencia = 1.0 if magnitud == 'mach' else datos['ambiente']
    maximo = max(max(valores), referencia, 0.01) * 1.18
    x_inicio, x_fin = 94, 659
    xs = [x_inicio + (x_fin-x_inicio)*(i+1)/(len(estados)+1)
          for i in range(len(estados))]
    convertir_y = lambda v: 240 - 191*v/maximo
    ref_y = convertir_y(referencia)
    nombre = 'Número de Mach [–]' if magnitud == 'mach' else 'Presión estática [kPa]'
    ref_nombre = 'M = 1' if magnitud == 'mach' else 'p∞ ambiente'
    piezas = ['<path d="M77 27 V240 H681" fill="none" stroke="#8293a7"/>',
              f'<path d="M77 {ref_y:.2f} H681" stroke="#be743a" '
              'stroke-dasharray="7 5" fill="none"/>',
              f'<text x="83" y="{ref_y-8:.2f}" text-anchor="start" '
              f'font-size="12" fill="#9c4e22">{ref_nombre}: {referencia:.3f}</text>',
              f'<text x="77" y="16" font-size="13">{nombre}</text>',
              '<text x="380" y="323" text-anchor="middle" font-size="12">'
              'Estados discretos (sin escala de posición axial)</text>']
    colores = {'garganta': '#2563a6', 'choque_antes': '#a1548e',
               'choque_despues': '#b05d37', 'salida': '#217a70'}
    for i, (e, x) in enumerate(zip(estados, xs)):
        y = convertir_y(e[magnitud])
        color = colores[e['papel']]
        piezas.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="6" '
                      f'fill="{color}" stroke="white" stroke-width="1.5"/>')
        piezas.append(f'<text x="{x:.2f}" y="{max(30, y-13):.2f}" '
                      f'text-anchor="middle" font-size="12">{e[magnitud]:.3f}</text>')
        # Rótulos en dos líneas para no confundir ambos lados del choque.
        etiqueta = {'choque_antes': 'Choque: antes',
                    'choque_despues': 'Choque: después'}.get(e['papel'], e['nombre'])
        piezas.append(f'<text x="{x:.2f}" y="{261 + (i%2)*17}" '
                      f'text-anchor="middle" font-size="11">{escape(etiqueta)}</text>')
    aria = ('Mach en estados discretos con referencia Mach uno' if magnitud == 'mach'
            else 'Presiones estáticas discretas con presión ambiente de referencia')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 340" '
            f'role="img" aria-label="{aria}"><g font-family="sans-serif" '
            'fill="#172b42">' + ''.join(piezas) + '</g></svg>')


def svg_perfil_tobera(datos, magnitud):
    """Curva de estados calculados contra A/Ag; choque con salto explícito.

    Las dos magnitudes comparten exactamente el mismo eje, las regiones y
    el emplazamiento geométrico del choque. No presupone eje longitudinal.
    """
    if magnitud not in ("mach", "presion"):
        raise ValueError("Magnitud de perfil desconocida.")
    if not datos or not datos["disponible"]:
        return None
    clave = "mach" if magnitud == "mach" else "presion"
    referencia = 1.0 if magnitud == "mach" else datos["p_ambiente"]
    valores = [p[clave] for segmento in datos["segmentos"] for p in segmento]
    maximo = max(*valores, referencia) * 1.17
    epsilon = datos["relacion_areas"]
    x0, x1, y0, y1 = 92, 691, 249, 32
    x = lambda area: x0 + (area-1)*(x1-x0)/(epsilon-1)
    y = lambda valor: y0-(valor/maximo)*(y0-y1)
    trazos = [
        f'<path d="M{x0} {y1} V{y0} H{x1}" fill="none" stroke="#8293a7"/>',
        f'<path d="M{x0} {y(referencia):.2f} H{x1}" fill="none" '
        'stroke="#bb703c" stroke-dasharray="7 5"/>',
        f'<text x="{x0+105}" y="{max(y1+11,y(referencia)-7):.2f}" '
        f'font-size="11" fill="#9c4e22">'
        f'{"M = 1" if clave == "mach" else "p∞"}: {referencia:.3g}</text>',
        f'<text x="{x0}" y="18" font-size="13">'
        f'{"Número de Mach [–]" if clave == "mach" else "Presión estática [kPa]"}</text>',
        '<text x="394" y="323" text-anchor="middle" font-size="13">'
        'Relación geométrica A/Ag [–] · no es longitud axial</text>',
    ]
    colores = {"subsonica": "#287b82", "supersonica": "#376cb3"}
    for segmento in datos["segmentos"]:
        puntos = " ".join(f'{x(p["area_relativa"]):.2f},{y(p[clave]):.2f}'
                          for p in segmento)
        color = colores[segmento[0]["rama"]]
        if len(segmento) > 1:
            trazos.append(f'<polyline points="{puntos}" fill="none" '
                          f'stroke="{color}" stroke-width="3" stroke-linejoin="round"/>')
        for p in (segmento[0], segmento[-1]):
            trazos.append(f'<circle cx="{x(p["area_relativa"]):.2f}" '
                          f'cy="{y(p[clave]):.2f}" r="4" fill="{color}" '
                          'stroke="white" stroke-width="1"/>')
    if datos["choque"]:
        antes, despues = datos["choque"]
        xx = x(antes["area_relativa"])
        trazos.append(f'<path d="M{xx:.2f} {y(antes[clave]):.2f} '
                      f'V{y(despues[clave]):.2f}" stroke="#a55a73" '
                      'stroke-width="2.5" stroke-dasharray="5 3"/>')
        trazos.append(f'<text x="{xx:.2f}" y="{y1+12}" '
                      'text-anchor="middle" font-size="11" fill="#8f3859">Choque</text>')
        for p in (antes, despues):
            trazos.append(f'<circle cx="{xx:.2f}" cy="{y(p[clave]):.2f}" '
                          'r="4" fill="#a55a73" stroke="white"/>')
    for a, etiqueta in ((1.0, "Garganta"), (epsilon, "Salida")):
        xx = x(a)
        trazos.append(f'<path d="M{xx:.2f} {y0} V{y0+6}" stroke="#8293a7"/>')
        trazos.append(f'<text x="{xx:.2f}" y="{y0+21}" text-anchor="middle" '
                      f'font-size="12">{a:.3g}</text>')
        trazos.append(f'<text x="{xx:.2f}" y="{y0+39}" text-anchor="middle" '
                      f'font-size="11">{etiqueta}</text>')
    trazos.append('<text x="98" y="304" font-size="11" fill="#376cb3">'
                  'Azul: supersónica</text><text x="310" y="304" '
                  'font-size="11" fill="#287b82">Verde: subsónica</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 344" '
            f'role="img" aria-label="Perfil cuasiunidimensional de '
            f'{"Mach" if clave == "mach" else "presión estática"} '
            'frente a relación de áreas de garganta">'
            '<g font-family="sans-serif" fill="#172b42">'
            + ''.join(trazos) + '</g></svg>')


def datos_balance_energetico(resultado):
    """Magnitudes y residuos [kJ/kg aire] usando los estados existentes.

    La energía cinética de escape queda None si la tobera no está resuelta.
    No modela calor perdido ni energía química no recuperada por separado.
    """
    c = resultado['compresor']
    b = resultado['combustor']
    t = resultado['turbina']
    n = resultado['tobera']
    f = b['f']
    factor = b['factor_masico']
    trabajo_c = c['trabajo_compresor']
    quimica = b['aporte_quimico_efectivo']
    trabajo_t = t['trabajo_turbina_por_kg_aire']
    trabajo_eje = t['rendimiento_mecanico'] * trabajo_t
    magnitudes = (trabajo_c, quimica, trabajo_t, trabajo_eje, f, factor)
    if any(not isinstance(v, Real) or isinstance(v, bool) or not isfinite(v)
           for v in magnitudes) or not (trabajo_c > 0 and quimica > 0
                                        and trabajo_t > 0 and f > 0 and factor > 1):
        raise ValueError('Energías o dosado inválidos para visualización.')
    if abs(factor-(1+f)) > 1e-10 * factor:
        raise ValueError('Caudal de gases incoherente con el dosado.')

    residuos = {
        'compresor': c['h1']+trabajo_c-c['h2'],
        'combustor': c['h2']+quimica-factor*b['h3'],
        'turbina': factor*(b['h3']-t['h4'])-trabajo_t,
        'eje': trabajo_eje-trabajo_c,
        'tobera': None,
    }
    cinetica = None
    if n is not None and n.get('velocidad_salida') is not None:
        temperatura = n.get('temperatura_salida')
        velocidad = n['velocidad_salida']
        if temperatura is None or not isinstance(velocidad, Real) or not isfinite(velocidad) or velocidad < 0:
            raise ValueError('Salida de tobera inválida para balance energético.')
        h_salida = h(temperatura)
        cinetica = factor*velocidad**2/2000
        residuos['tobera'] = factor*(t['h4']-h_salida)-cinetica
    escala = max(1, trabajo_c, quimica, trabajo_t,
                 cinetica if cinetica is not None else 0)
    if any(v is not None and (not isfinite(v) or abs(v)>1e-8*escala)
           for v in residuos.values()):
        raise ValueError('No cierran los balances energéticos del modelo.')
    return {'compresor': trabajo_c, 'combustor': quimica,
            'turbina': trabajo_t, 'eje_util': trabajo_eje,
            'tobera_cinetica': cinetica, 'f': f, 'factor_masico': factor,
            'residuos': residuos}


def svg_balance_energetico(datos):
    """Barras de magnitudes no aditivas; None no se dibuja como cero."""
    barras = (
        ('Compresor · trabajo recibido', datos['compresor'], '#27679b'),
        ('Cámara · combustible efectivo', datos['combustor'], '#c07932'),
        ('Turbina · trabajo extraído', datos['turbina'], '#8e59a5'),
        ('Tobera · energía cinética salida', datos['tobera_cinetica'], '#2b8775'),
    )
    escala = max(v for _, v, _ in barras if v is not None)
    piezas = ['<path d="M270 38 V287" stroke="#70849b" fill="none"/>',
              '<text x="270" y="20" font-size="12" text-anchor="middle">0</text>']
    for i, (titulo, valor, color) in enumerate(barras):
        y = 52+i*57
        piezas.append(f'<text x="12" y="{y+17}" font-size="13">{escape(titulo)}</text>')
        if valor is None:
            piezas.append(f'<text x="282" y="{y+17}" font-size="12">No disponible</text>')
        else:
            largo = 345*valor/escala
            piezas.append(f'<rect x="270" y="{y}" width="{largo:.2f}" height="25" '
                          f'rx="4" fill="{color}"/>')
            piezas.append(f'<text x="{280+largo:.2f}" y="{y+18}" '
                          f'font-size="12">{valor:.2f}</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 330" '
            'role="img" aria-label="Magnitudes energéticas por componentes, no aditivas">'
            '<g font-family="sans-serif" fill="#172b42">'
            '<text x="12" y="320" font-size="13">Magnitudes [kJ/kg de aire entrante]</text>'
            + ''.join(piezas) + '</g></svg>')


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
    """Retorna estaciones y SVG educativos seguros para Jinja; sin física nueva."""
    estados = estaciones_turborreactor(resultado)
    datos_tobera = datos_tobera_graficas(resultado)
    balance = datos_balance_energetico(resultado)
    perfil = perfil_tobera_cp_variable(resultado)
    return {"estaciones": estados,
            "adaptacion_cd": _adaptacion_cd(resultado),
            "svg_componentes": svg_componentes(resultado["diagnosticos"].get("tipo_tobera")),
            "svg_temperaturas": svg_evolucion(estados,"T","Temperatura total","K"),
            "svg_presiones": svg_evolucion(estados,"p","Presión total","kPa"),
            "svg_empuje": svg_descomposicion_empuje(resultado),
            "svg_ts": svg_ts_turborreactor(estados),
            "datos_tobera_graficas": datos_tobera,
            "svg_mach_tobera": svg_estados_tobera(datos_tobera, 'mach'),
            "svg_presion_tobera": svg_estados_tobera(datos_tobera, 'presion'),
            "perfil_tobera": perfil,
            "svg_mach_perfil_tobera": svg_perfil_tobera(perfil, "mach"),
            "svg_presion_perfil_tobera": svg_perfil_tobera(perfil, "presion"),
            "balance_energetico": balance,
            "svg_balance_energetico": svg_balance_energetico(balance)}
