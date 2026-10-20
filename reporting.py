"""Presentación HTML y conservación de informes; no contiene ecuaciones del ciclo."""

from base64 import b64encode
from html import escape
from pathlib import Path
import re
import subprocess
from uuid import uuid4
from warnings import warn


MARCA_INICIO = "<!-- Brayton Simulator report v1 -->"
MARCA_FINAL = "<!-- Brayton Simulator report complete -->"
PATRON_INFORME = re.compile(
    r"brayton_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-\d{6}_[0-9a-f]{32}\.html"
)


def obtener_version_git(carpeta):
    """Consulta HEAD y cambios locales sin modificar el repositorio."""
    try:
        commit = subprocess.run(
            ["git", "-C", str(carpeta), "rev-parse", "--verify", "HEAD"],
            capture_output=True, text=True, check=True, timeout=5,
        ).stdout.strip()
        estado = subprocess.run(
            ["git", "-C", str(carpeta), "status", "--porcelain", "--untracked-files=normal"],
            capture_output=True, text=True, check=True, timeout=5,
        ).stdout
        return {"commit": commit, "modificado": bool(estado.strip())}
    except (OSError, subprocess.SubprocessError):
        # Una copia sin Git sigue pudiendo generar resultados; no se asume limpia.
        return {"commit": None, "modificado": None}


def tabla_html(encabezados, filas):
    """Convierte encabezados y filas de valores ya formateados en una tabla."""
    cabecera = "".join(f"<th scope='col'>{escape(str(valor))}</th>" for valor in encabezados)
    cuerpo = "".join(
        "<tr>" + "".join(f"<td>{escape(str(valor))}</td>" for valor in fila) + "</tr>"
        for fila in filas
    )
    return f"<div class='table-wrap'><table><thead><tr>{cabecera}</tr></thead><tbody>{cuerpo}</tbody></table></div>"


def imagen_html(imagen, titulo):
    """Incorpora los bytes PNG de esta ejecución como una URL de datos Base64."""
    if not imagen.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("La gráfica debe contener una imagen PNG válida.")
    contenido = b64encode(imagen).decode("ascii")
    etiqueta = escape(titulo)
    return (
        f"<figure><img src='data:image/png;base64,{contenido}' alt='{etiqueta}'>"
        f"<figcaption>{etiqueta}</figcaption></figure>"
    )


def seccion_optimizacion_html(parametros, referencias, optimizaciones, barrido):
    """Presenta resultados ya calculados; None se muestra como no disponible."""
    tablas = []
    for nombre in ("ideal", "noideal"):
        r = optimizaciones[nombre]
        tablas.append(f"<h3>Modelo {nombre}</h3><p>{escape(r['motivo'])}</p>")
        if r["estado"] != "disponible":
            tablas.append("<p>Óptimo motor: No disponible. No se ejecuta una búsqueda en un dominio vacío.</p>")
            continue
        a, n, c = r["analitico"], r["numerico"], r["concordancia"]
        lo, hi = r["dominio"]["intervalo"]
        filas = [
            ("Relación de presiones de referencia", f"{parametros['relacion_presiones']:.10g}", "—"),
            ("Trabajo neto de referencia", f"{referencias[nombre]['trabajo_neto']:.6f}", "kJ/kg"),
            ("rp de máximo trabajo · analítica", f"{a['rp']:.10f}", "—"),
            ("rp de máximo trabajo · numérica", f"{n['rp']:.10f}", "—"),
            ("Trabajo máximo · analítico", f"{a['ciclo']['trabajo_neto']:.6f}", "kJ/kg"),
            ("Trabajo máximo · numérico", f"{n['ciclo']['trabajo_neto']:.6f}", "kJ/kg"),
            ("Rendimiento EN el máximo de trabajo", f"{a['ciclo']['rendimiento'] * 100:.6f}", "%"),
            ("Dominio físico abierto", f"{lo:.10g} < rp < {hi:.10g}", "—"),
            ("Intervalo de optimización numérica", f"{n['intervalo_busqueda'][0]:.10g} a {n['intervalo_busqueda'][1]:.10g}", "—"),
            ("Intervalo final del refinamiento", f"{n['intervalo_final'][0]:.10g} a {n['intervalo_final'][1]:.10g}", "—"),
            ("Muestras iniciales / evaluaciones totales", f"{n['muestras_iniciales']} / {n['evaluaciones']}", "—"),
            ("Paso logarítmico inicial", f"{n['paso_log_inicial']:.6g}", "—"),
            ("Tolerancia de parada en log(rp)", f"{n['tolerancia_log']:.3g}", "—"),
            ("Escala de resolución numérica en rp", f"{n['resolucion_rp']:.6g}", "—"),
            ("Diferencia absoluta en rp / tolerancia", f"{c['diferencia_rp']:.6g} / {c['tolerancia_rp']:.6g}", "—"),
            ("Diferencia absoluta en trabajo / tolerancia", f"{c['diferencia_trabajo']:.6g} / {c['tolerancia_trabajo']:.6g}", "kJ/kg"),
        ]
        tablas.append(tabla_html(("Magnitud", "Resultado", "Unidad"), filas))
        if nombre == "noideal":
            tablas.append("<h3>Estados del ciclo no ideal en el máximo de trabajo</h3>")
            tablas.append(tabla_html(("Estado", "T [K]", "p [kPa]"), [
                (i, f"{T:.6f}", f"{p:.6f}") for i, (T, p) in enumerate(zip(
                    a["ciclo"]["temperaturas"], a["ciclo"]["presiones"]), start=1)]))
    ideal, real = optimizaciones["ideal"], optimizaciones["noideal"]
    if ideal["estado"] == real["estado"] == "disponible":
        ai, ar = ideal["analitico"], real["analitico"]
        tablas.append(tabla_html(("Comparación (ideal menos no ideal)", "Diferencia", "Unidad"), [
            ("Relaciones de máximo trabajo", f"{ai['rp'] - ar['rp']:.10f}", "—"),
            ("Trabajos máximos", f"{ai['ciclo']['trabajo_neto'] - ar['ciclo']['trabajo_neto']:.6f}", "kJ/kg")]))
    if barrido is not None:
        lo, hi = barrido["intervalo_visual"]
        tablas.append(f"<p>Ventana gráfica completa: {lo:.10g} a {hi:.10g}; {len(barrido['relaciones'])} muestras compartidas. "
                      "Incluye fronteras y óptimos; las comparaciones añaden un panel de detalle no ideal "
                      "cuando la amplitud logarítmica o el trabajo máximo difieren mucho.</p>")
    return ("<section><h2>Optimización del trabajo específico neto</h2>"
            "<p>Se maximiza trabajo específico a parámetros fijos, NO rendimiento térmico. "
            "Se distingue candidato estacionario matemático de máximo motor interior. "
            "La segunda derivada en x=rp^a es negativa; si existe dominio motor, "
            "el candidato pertenece a su interior. La búsqueda independiente usa malla logarítmica "
            "y sección áurea dentro de ese dominio, sin usar el candidato analítico para acotarla.</p>"
            "<p>La resolución inicial, el criterio de parada y la precisión en rp son distintos: "
            "cerca del máximo el trabajo es plano y el redondeo impide atribuir al resultado "
            "tantos dígitos fiables como su estrecho intervalo final. Las tolerancias son numéricas, "
            "no incertidumbre experimental.</p>" + "".join(tablas) + "</section>")


def crear_informe_html(parametros, ideal, noideal, detalles_ideal, optimo,
                       rendimientos, comprobaciones, imagenes, fecha, version, barrido=None,
                       optimizaciones=None):
    """Presenta resultados y seis PNG suministrados por main, sin recalcular física."""
    if len(imagenes) != 6:
        raise ValueError("El informe requiere exactamente seis gráficas de la ejecución.")
    filas_parametros = [
        ("T1 · Entrada del compresor", f"{parametros['T1']:.2f}", "K"),
        ("T3 · Entrada de la turbina", f"{parametros['T3']:.2f}", "K"),
        ("cp", f"{parametros['cp']:.2f}", "J/(kg·K)"),
        ("gamma = cp/cv", f"{parametros['gamma']:.4f}", "—"),
        ("Relación de presiones del compresor", f"{parametros['relacion_presiones']:.4f}", "—"),
        ("p1 · Presión inicial", f"{parametros['p1']:.2f}", "kPa"),
        ("Eficiencia isentrópica del compresor", f"{parametros['eta_c']:.4f}", "—"),
        ("Eficiencia isentrópica de la turbina", f"{parametros['eta_t']:.4f}", "—"),
        ("Pérdida relativa de presión del combustor", f"{parametros['perdida_presion_combustor']:.4f}", "fracción"),
        ("Pérdida de presión del combustor", f"{parametros['perdida_presion_combustor'] * 100:.2f}", "%"),
    ]
    estados_ideal = [
        (i, f"{T:.2f}", f"{p:.2f}", f"{v:.6f}", f"{s:.6f}")
        for i, (T, p, v, s) in enumerate(zip(
            ideal["temperaturas"], ideal["presiones"],
            detalles_ideal["volumenes"], detalles_ideal["entropias"]
        ), start=1)
    ]
    estados_noideal = [
        (i, f"{T:.2f}", f"{p:.2f}")
        for i, (T, p) in enumerate(zip(noideal["temperaturas"], noideal["presiones"]), start=1)
    ]
    magnitudes = (
        ("Trabajo del compresor (consumo)", "trabajo_compresor", 1, "kJ/kg"),
        ("Trabajo de la turbina (producción)", "trabajo_turbina", 1, "kJ/kg"),
        ("Trabajo neto", "trabajo_neto", 1, "kJ/kg"),
        ("Calor aportado", "calor_aportado", 1, "kJ/kg"),
        ("Rendimiento térmico", "rendimiento", 100, "%"),
        ("Back work ratio", "back_work_ratio", 1, "—"),
    )
    balance_ideal = [(nombre, f"{ideal[clave] * factor:.6f}", unidad)
                     for nombre, clave, factor, unidad in magnitudes]
    balance_noideal = [(nombre, f"{noideal[clave] * factor:.6f}", unidad)
                       for nombre, clave, factor, unidad in magnitudes]
    comparacion = [(nombre, f"{ideal[clave] * factor:.6f}",
                    f"{noideal[clave] * factor:.6f}", unidad)
                   for nombre, clave, factor, unidad in magnitudes]
    referencias = [(nombre, f"{ideal[clave]:.6f}", f"{noideal[clave]:.6f}", "K")
                   for nombre, clave in (("T2s", "T2s"), ("T4s", "T4s"))]
    comparacion_estados = [
        (f"T{i} [K]", f"{Ti:.2f}", f"{Tr:.2f}")
        for i, (Ti, Tr) in enumerate(zip(ideal["temperaturas"], noideal["temperaturas"]), start=1)
    ] + [
        (f"p{i} [kPa]", f"{pi:.2f}", f"{pr:.2f}")
        for i, (pi, pr) in enumerate(zip(ideal["presiones"], noideal["presiones"]), start=1)
    ]
    filas_optimo = [
        ("Relación de presiones óptima analítica", f"{optimo['rp_analitica']:.6f}", "—"),
        ("Relación de presiones óptima numérica", f"{optimo['rp_numerica']:.6f}", "—"),
        ("Escala de resolución numérica en rp", f"{optimo['paso']:.7f}", "—"),
        ("Trabajo neto máximo analítico", f"{optimo['trabajo_analitico']:.6f}", "kJ/kg"),
        ("Trabajo neto máximo numérico", f"{optimo['trabajo_numerico']:.6f}", "kJ/kg"),
        ("T2 en el óptimo analítico", f"{optimo['temperaturas'][1]:.2f}", "K"),
        ("T4 en el óptimo analítico", f"{optimo['temperaturas'][3]:.2f}", "K"),
        ("Rendimiento en el óptimo analítico", f"{optimo['rendimiento'] * 100:.6f}", "%"),
    ]
    unidades = ("Magnitud", "Valor", "Unidad")
    lista_comprobaciones = "".join(f"<li>{escape(texto)}</li>" for texto in comprobaciones)
    fecha_texto = escape(fecha.strftime("%d/%m/%Y · %H:%M:%S %z"))
    commit_texto = escape(version["commit"] or "No disponible")
    if version["modificado"] is True:
        estado_version = "Cambios sin confirmar: esta ejecución incluye modificaciones locales o archivos sin seguimiento. El commit identifica la base, no una versión exacta reproducible de estos resultados."
    elif version["modificado"] is False:
        estado_version = "Árbol de trabajo limpio: sin cambios pendientes ni archivos sin seguimiento detectados por Git."
    else:
        estado_version = "Estado Git no disponible: no se ha podido verificar el commit o los cambios locales."
    dominio_html = ""
    if barrido is not None:
        filas = []
        conteos = []
        for nombre in ("ideal", "noideal"):
            d = barrido["dominios"][nombre]
            intervalo = d["intervalo"]
            motor = (f"{intervalo[0]:.10g} < rp < {intervalo[1]:.10g}"
                     if intervalo else "Vacío")
            raices = ", ".join(f"{rp:.10g}" for rp in d["trabajo"]) or "Sin raíces distintas"
            filas.append((nombre, motor, f"rp > {d['expansion']:.10g}",
                          f"rp < {d['calor']:.10g}", raices, "Motor viable"))
            motivos = barrido[nombre]["motivos"]
            conteos.append((nombre, int(barrido[nombre]["viable"].sum()),
                            *(sum(c in fallos for fallos in motivos)
                              for c in ("compresion", "expansion", "calor_aportado", "trabajo_neto"))))
        dominio_html = "<section><h2>Dominio físicamente viable</h2>" + (
            "<p>Se exige compresión rp &gt; 1, expansión p3 &gt; p4, aporte de calor "
            "T3 &gt; T2 y trabajo neto wt &gt; wc. Las fronteras no son puntos motores. "
            "En el ideal: 1 &lt; rp &lt; (T3/T1)^(gamma/(gamma−1)). "
            "Calor positivo no garantiza que la turbina cubra el consumo del compresor.</p>"
        ) + tabla_html(("Modelo", "Intervalo motor abierto", "Expansión", "Calor positivo",
                        "Fronteras wn = 0", "Caso de referencia"), filas) + (
            "<p>En el no ideal, con x=rp^a, h=(T3/T1) eta_c eta_t y k=(1−delta)^(−a), "
            "wn &gt; 0 equivale a Q(x)=(x−1)(x−h)+h(k−1) &lt; 0. "
            "La cuadrática convexa demuestra que el dominio es un intervalo abierto o vacío. "
            "Se localizan las raíces por bisección (tolerancia relativa en x: 1e−12). "
            "Esto localiza fronteras; no optimiza el modelo no ideal.</p>"
            "<p>La clasificación excluye una banda relativa de 1e−10 alrededor del cero "
            "en cada condición, escalada en sus propias unidades. Es una precaución de "
            "redondeo, no incertidumbre experimental ni cambio de las ecuaciones.</p>"
        ) + tabla_html(("Modelo", "Puntos motores", "Sin compresión", "Sin expansión",
                        "Calor no positivo", "Trabajo no positivo"), conteos) + (
            f"<p>Malla representada: {len(barrido['relaciones'])} puntos entre rp = "
            f"{barrido['relaciones'][0]:.10g} y {barrido['relaciones'][-1]:.10g}. "
            "Combina muestreo lineal y logarítmico, fronteras y sus vecindades; "
            "la ventana se adapta al dominio completo sin un recorte fijo de rp. "
            "Las fronteras de la tabla se calculan independientemente del dibujo. "
            "Los motivos pueden solaparse: sus recuentos no deben sumarse. "
            "NaN corta las curvas en puntos excluidos; nunca se publica rendimiento motor allí. "
            "Las bandas tenues y líneas discontinuas indican los dominios y sus fronteras.</p></section>"
        )
    intervalo_busqueda = optimo.get("intervalo_busqueda", (1.01, 50))
    optimizacion_html = (seccion_optimizacion_html(parametros, {"ideal": ideal, "noideal": noideal},
                                                   optimizaciones, barrido)
                         if optimizaciones is not None else "")
    return f"""{MARCA_INICIO}
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Brayton Simulator · {fecha_texto}</title>
<style>
:root {{ color-scheme: light; font-family: 'Segoe UI', Arial, sans-serif; color: #192b3a; background: #edf1f5; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; line-height: 1.6; }}
main {{ max-width: 1120px; margin: 32px auto; padding: 0 24px; }}
header {{ padding: 30px 36px; background: #153c55; color: white; border-radius: 10px; }}
header p {{ margin: 4px 0; }}
header code {{ overflow-wrap: anywhere; }}
.version-warning {{ margin-top: 12px; padding: 10px 14px; background: #fff1cf; color: #624400; border-radius: 4px; }}
h1 {{ margin: 0 0 8px; font-size: 2rem; }}
h2 {{ margin: 0 0 16px; font-size: 1.4rem; color: #153c55; }}
h3 {{ font-size: 1.05rem; margin-top: 24px; }}
section {{ margin-top: 24px; padding: 28px 32px; background: white; border: 1px solid #d7e0e7; border-radius: 10px; }}
.note {{ color: #475969; }}
.status {{ display: inline-block; margin-top: 14px; padding: 3px 12px; background: #dff2e7; color: #185639; border-radius: 4px; }}
.table-wrap {{ overflow-x: auto; margin: 14px 0 22px; }}
table {{ width: 100%; border-collapse: collapse; font-size: .95rem; font-variant-numeric: tabular-nums; }}
th, td {{ padding: 10px 13px; text-align: right; border-bottom: 1px solid #dde5ec; white-space: nowrap; }}
th {{ background: #eaf0f5; color: #153c55; }}
th:first-child, td:first-child {{ text-align: left; white-space: normal; }}
tbody tr:nth-child(even) {{ background: #f7f9fb; }}
figure {{ margin: 24px 0 12px; }}
img {{ display: block; width: 100%; max-width: 950px; height: auto; margin: auto; }}
figcaption {{ text-align: center; font-size: .9rem; color: #475969; }}
li {{ margin: 8px 0; }}
footer {{ padding: 24px 0; font-size: .85rem; color: #475969; }}
@media (max-width: 600px) {{ main {{ margin: 12px auto; padding: 0 10px; }} header, section {{ padding: 20px 16px; }} h1 {{ font-size: 1.6rem; }} }}
@media print {{ body {{ background: white; }} main {{ margin: 0; max-width: none; }} section {{ break-inside: auto; }} figure {{ break-inside: avoid; }} }}
</style>
</head>
<body><main>
<header><h1>Brayton Simulator</h1><p>Informe de resultados · {fecha_texto}</p>
<p>Commit Git: <code>{commit_texto}</code></p>
<p class="{'version-warning' if version['modificado'] is not False else 'version'}">{estado_version}</p>
<span class="status">Ejecución completada · 6 gráficas incorporadas</span></header>
<section><h2>Parámetros de la ejecución</h2>
<p class="note">Modelo educativo de gas ideal con cp y gamma constantes. Equipos adiabáticos en régimen estacionario; se desprecian cambios de energía cinética y potencial. No es un modelo de motor real de alta fidelidad.</p>
{tabla_html(unidades, filas_parametros)}</section>
{dominio_html}
{optimizacion_html}
<section><h2>Ciclo ideal · caso de referencia</h2>
<p>Estados: 1 entrada del compresor, 2 salida del compresor, 3 entrada de turbina y 4 salida de turbina. La entropía es relativa, con s1 = 0.</p>
{tabla_html(("Estado", "T [K]", "p [kPa]", "v [m³/kg]", "s [kJ/(kg·K)]"), estados_ideal)}
{tabla_html(unidades, balance_ideal)}
<p>Constante específica R: {detalles_ideal['R']:.6f} J/(kg·K).</p>
<p>Rendimiento por fórmula ideal: {detalles_ideal['rendimiento_formula'] * 100:.6f} %. Rendimiento por balance: {ideal['rendimiento'] * 100:.6f} %.</p>
<p>Incremento de entropía 2→3: {detalles_ideal['incremento_23']:.6f} kJ/(kg·K). Incremento 1→4: {detalles_ideal['incremento_14']:.6f} kJ/(kg·K).</p>
<h3>Rendimiento ideal frente a relación de presiones</h3>
{tabla_html(("Relación de presiones", "Rendimiento ideal [%]"), [(rp, f"{eta:.2f}" if eta is not None else "Fuera del dominio motor") for rp, eta in rendimientos])}
{imagen_html(imagenes['rendimiento_brayton.png'], 'Rendimiento exclusivamente ideal · dominio motor, eje rp logarítmico')}</section>
<section><h2>Diagramas termodinámicos exclusivamente ideales</h2>
{imagen_html(imagenes['diagrama_ts_brayton.png'], 'Diagrama T-s del ciclo ideal de referencia')}
{imagen_html(imagenes['diagrama_pv_brayton.png'], 'Diagrama P-v del ciclo ideal de referencia')}</section>
<section><h2>Trabajo ideal y comprobación de su máximo</h2>
<p>Máximo de trabajo específico neto a temperaturas extremas fijas. No es una maximización del rendimiento. Búsqueda numérica adaptada entre rp = {intervalo_busqueda[0]:.10g} y {intervalo_busqueda[1]:.10g}. Este intervalo de búsqueda y el intervalo representado son distintos del límite físico.</p>
{tabla_html(unidades, filas_optimo)}
{imagen_html(imagenes['trabajo_neto_vs_rp.png'], 'Trabajo neto ideal y máximo analítico contrastado con la malla numérica')}</section>
<section><h2>Ciclo no ideal · caso de referencia</h2>
<p>Eficiencias isentrópicas de compresor y turbina y pérdida de presión del combustor. No se calculan entropías ni volúmenes no ideales en este informe.</p>
{tabla_html(("Estado", "T [K]", "p [kPa]"), estados_noideal)}
<p>Referencias isentrópicas: T2s = {noideal['T2s']:.6f} K; T4s = {noideal['T4s']:.6f} K. T4s utiliza la presión real de entrada de la turbina tras la pérdida del combustor.</p>
{tabla_html(unidades, balance_noideal)}</section>
<section><h2>Comparación del ciclo ideal y no ideal</h2>
{tabla_html(("Magnitud", "Ideal", "No ideal"), comparacion_estados)}
{tabla_html(("Referencia", "Ideal", "No ideal", "Unidad"), referencias)}
{tabla_html(("Magnitud", "Ideal", "No ideal", "Unidad"), comparacion)}
<p>Ambas curvas usan la misma malla adaptada y los parámetros de esta ejecución; sólo se dibuja el interior motor de cada modelo.</p>
{imagen_html(imagenes['comparacion_ideal_noideal.png'], 'Rendimiento térmico · comparación ideal / no ideal')}
{imagen_html(imagenes['trabajo_neto_ideal_noideal.png'], 'Trabajo específico neto · comparación ideal / no ideal')}</section>
<section><h2>Comprobaciones ejecutadas</h2><ul>{lista_comprobaciones}</ul>
<p class="note">Estas comprobaciones verifican coherencia del código y del modelo; no constituyen validación frente a datos experimentales externos.</p></section>
<footer>Informe autocontenido: HTML, CSS y seis imágenes PNG Base64. No necesita Internet ni archivos de imagen externos. Las energías son específicas (kJ/kg), no potencias.</footer>
</main></body></html>
{MARCA_FINAL}"""


def guardar_informe_html(contenido, carpeta, fecha):
    """Publica un HTML completo y después conserva los cuatro informes propios recientes."""
    if not contenido.startswith(MARCA_INICIO) or not contenido.endswith(MARCA_FINAL):
        raise ValueError("El informe no contiene las marcas de documento completo.")
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre = f"brayton_{fecha.strftime('%Y-%m-%d_%H-%M-%S-%f')}_{uuid4().hex}.html"
    ruta = carpeta / nombre
    temporal = carpeta / f".{nombre}.tmp"
    # 'x' evita sobrescribir incluso el temporal de otra ejecución.
    archivo = temporal.open("x", encoding="utf-8")
    try:
        with archivo:
            archivo.write(contenido)
        if ruta.exists():
            raise FileExistsError(f"Ya existe el destino del informe: {ruta}")
        # En Windows rename falla si el destino existe: no lo reemplaza.
        temporal.rename(ruta)
    finally:
        temporal.unlink(missing_ok=True)

    # La limpieza solo se alcanza tras publicar correctamente el informe completo.
    # Si la limpieza no es posible, el informe sigue siendo válido y se avisa.
    try:
        informes = []
        for candidato in carpeta.iterdir():
            if (PATRON_INFORME.fullmatch(candidato.name) and not candidato.is_symlink()
                    and candidato.is_file()):
                try:
                    texto = candidato.read_text(encoding="utf-8")
                except UnicodeError:
                    continue  # Un archivo ajeno o ilegible no es un informe propio.
                if texto.startswith(MARCA_INICIO) and texto.endswith(MARCA_FINAL):
                    informes.append(candidato)
        # mtime refleja la finalización de escritura, no el inicio de los cálculos.
        informes.sort(key=lambda archivo: (archivo.stat().st_mtime_ns, archivo.name), reverse=True)
        for antiguo in informes[4:]:
            antiguo.unlink()
    except (OSError, UnicodeError) as error:
        warn(f"Informe guardado en {ruta}; no se pudo completar la conservación de cuatro informes: {error}")
    return ruta
