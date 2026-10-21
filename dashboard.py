"""Presentación compartida local/autónoma. No calcula ciclos ni optimizaciones."""

from base64 import b64encode
from html import escape
import json
from pathlib import Path
import re

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sensibilidad import PARAMETROS_ESTUDIO

RAIZ = Path(__file__).resolve().parent
SECCIONES = (("simulacion", "Simulación"), ("resultados", "Resultados"),
             ("optimizacion", "Optimización"), ("sensibilidad", "Sensibilidad"),
             ("informes", "Informes"), ("ayuda", "Ayuda"))
GRUPOS = (("Condiciones de entrada", ("T1", "T3", "p1")),
          ("Propiedades del fluido", ("cp", "gamma")),
          ("Configuración y pérdidas", ("relacion_presiones", "eta_c", "eta_t", "perdida_presion_combustor")))
CAMPOS = {
    "T1": ("T1 · Entrada del compresor", "K", "Temperatura absoluta mayor que 0", "0", None),
    "T3": ("T3 · Entrada de la turbina", "K", "Temperatura absoluta mayor que 0", "0", None),
    "p1": ("p1 · Presión de entrada", "kPa", "Presión absoluta mayor que 0", "0", None),
    "relacion_presiones": ("rp · Relación de presiones", "adimensional", "Mayor que 1; rp = p2/p1", "1", None),
    "cp": ("cp · Calor específico", "J/(kg·K)", "Mayor que 0; constante en el modelo", "0", None),
    "gamma": ("gamma · Relación cp/cv", "adimensional", "Mayor que 1", "1", None),
    "eta_c": ("eta_c · Eficiencia del compresor", "fracción", "0 < eta_c ≤ 1", "0", "1"),
    "eta_t": ("eta_t · Eficiencia de la turbina", "fracción", "0 < eta_t ≤ 1", "0", "1"),
    "perdida_presion_combustor": ("delta · Pérdida del combustor", "%", "0 ≤ pérdida < 100 %; 5 significa 5 %", "0", "100"),
}
AYUDA = (
    ("El ciclo Brayton", "Compresión, aporte de calor, expansión y rechazo de calor. El modelo describe un ciclo, no un motor completo."),
    ("Ideal y no ideal", "El ideal utiliza equipos isentrópicos. El no ideal incorpora eficiencias de compresor/turbina y pérdida de presión en el combustor."),
    ("Relación de presiones rp", "rp = p2/p1 es la relación de compresión. No es la relación real de expansión cuando hay pérdida de presión."),
    ("Dominio motor viable", "Exige compresión y expansión disponibles, calor aportado positivo y trabajo neto positivo. Sus fronteras están excluidas."),
    ("Dos criterios de diseño", "A maximiza el trabajo específico. B maximiza el rendimiento térmico cuando existe un máximo interior. Un supremo no alcanzado no es un punto operativo."),
    ("OFAT y limitaciones", "OFAT varía una entrada conservando las demás. No mide interacciones. Gas ideal con cp/gamma constantes; sin combustible, caudal, potencia, empuje ni mapas. Verificación interna, no validación experimental."),
)


def json_seguro(datos):
    """JSON incrustable en script inerte, sin cierres HTML aportados por valores."""
    return json.dumps(datos, ensure_ascii=True, allow_nan=False).replace("<", "\\u003c").replace("&", "\\u0026")


def renderizar_dashboard(valores, *, contenidos=None, metadata=None, informes=(), errores=None,
                         modo_local=True, informe_actual="", seccion_inicial="simulacion"):
    """HTML de seis secciones; recursos locales o incrustados, sin cálculo físico."""
    css = (RAIZ / "static/style.css").read_text(encoding="utf-8")
    js = (RAIZ / "static/dashboard.js").read_text(encoding="utf-8")
    if modo_local:
        css = '<link rel="stylesheet" href="/static/style.css">'
        js = '<script src="/static/dashboard.js" defer></script>'
    else:
        for fuente in (RAIZ / "static/fonts").glob("*.woff2"):
            css = css.replace(f"fonts/{fuente.name}", "data:font/woff2;base64," + b64encode(fuente.read_bytes()).decode("ascii"))
        css = "<style>" + css + "</style>"
        js = "<script>" + js + "</script>"
    entorno = Environment(loader=FileSystemLoader(RAIZ / "templates"), autoescape=select_autoescape(["html"]))
    return entorno.get_template("index.html").render(
        titulo="Configuración del ciclo" if modo_local else "Informe técnico",
        css=css, js=js, motor=(RAIZ / "static/images/engine-cutaway.svg").read_text(encoding="utf-8"),
        valores=valores, grupos=GRUPOS, campos=CAMPOS, estudios=PARAMETROS_ESTUDIO,
        secciones=SECCIONES, ayuda=AYUDA, errores=errores or {}, informes=informes,
        contenidos=contenidos or {k: "" for k in ("resultados", "optimizacion", "sensibilidad")},
        informe_actual=informe_actual, modo_local=modo_local, seccion_inicial=seccion_inicial,
        catalogo=json_seguro(PARAMETROS_ESTUDIO), metadata=json_seguro(metadata or {}),
        licencia_fuentes=(RAIZ / "static/fonts/OFL.txt").read_text(encoding="utf-8"))


def tarjeta_kpi(clave, etiqueta, valor, unidad, explicacion, decimales=3):
    """Tarjeta numérica de presentación: None se muestra como no disponible, no cero."""
    numero = f"{valor:.{decimales}f}" if valor is not None else "No disponible"
    estado = "Disponible" if valor is not None else "No disponible"
    return (f'<article class="kpi" data-kpi="{escape(clave)}"><div class="kpi-label">{escape(etiqueta)}</div>'
            f'<div class="kpi-value">{numero} <span class="unit">{escape(unidad)}</span></div>'
            f'<small>{escape(explicacion)}</small><span class="badge {"available" if valor is not None else "unavailable"}">{estado}</span></article>')


def plegable(titulo, contenido):
    """Details nativo cerrado, contenido HTML ya escapado por sus presentadores."""
    return f'<details class="card"><summary>{escape(titulo)}</summary><div class="detail-body">{contenido}</div></details>'


def separar_presentacion(contenido):
    """Extrae metadatos y paneles de un informe nuevo; None para formato histórico."""
    coincidencia = re.search(r'<script type="application/json" id="brayton-metadata">(.*?)</script>', contenido, re.S)
    if not coincidencia:
        return None
    try:
        metadata = json.loads(coincidencia[1])
    except (ValueError, TypeError):
        return None
    if not isinstance(metadata, dict) or metadata.get("dashboard") != 1:
        return None
    paneles = {}
    for clave in ("resultados", "optimizacion", "sensibilidad"):
        parte = re.search(f'<!--PANEL:{clave}-->(.*?)<!--FIN:{clave}-->', contenido, re.S)
        if parte is None:
            return None
        paneles[clave] = parte[1]
    return metadata, paneles


def visor_graficas(legado, imagenes, sensibilidad=False):
    """Extrae los PNG existentes una vez y los organiza en pestañas sin duplicarlos."""
    figuras = re.findall(r"<figure>.*?</figure>", legado, re.S)
    por_png = {b64encode(datos).decode("ascii"): nombre for nombre, datos in imagenes.items()}
    grupos = {"rendimiento_brayton.png": "rendimiento", "comparacion_ideal_noideal.png": "rendimiento",
              "trabajo_neto_vs_rp.png": "trabajo", "trabajo_neto_ideal_noideal.png": "trabajo",
              "diagrama_ts_brayton.png": "diagramas", "diagrama_pv_brayton.png": "diagramas",
              "compromiso_trabajo_rendimiento.png": "compromiso"}
    pestañas = (("trabajo_neto", "Trabajo neto"), ("rendimiento", "Rendimiento térmico"), ("rp", "Relaciones de presiones")) if sensibilidad else (
        ("rendimiento", "Rendimiento"), ("trabajo", "Trabajo"), ("diagramas", "Diagramas termodinámicos"),
        ("compromiso", "Compromiso de diseño"), ("todas", "Todas"))
    ordenadas = []
    for figura in figuras:
        png = re.search(r"data:image/png;base64,([^'\"]+)", figura)[1]
        nombre = por_png[png]
        grupo = nombre if sensibilidad else grupos[nombre]
        ordenadas.append(figura.replace("<figure>", f'<figure data-plot-group="{grupo}">', 1))
    if len(ordenadas) != len(imagenes):
        raise ValueError("El visor debe conservar exactamente todas las gráficas del informe.")
    prefijo = "ofat" if sensibilidad else "normal"
    botones = "".join(f'<button type="button" role="tab" id="tab-{prefijo}-{k}" aria-controls="graficas-{prefijo}" aria-selected="{str(i == 0).lower()}" data-plot-tab="{k}">{escape(t)}</button>' for i, (k, t) in enumerate(pestañas))
    visor = (f'<div class="card" data-plot-viewer="{prefijo}"><div class="card-title"><h3>Visor de gráficas</h3>'
             f'<span class="badge">{len(figuras)} gráficas</span></div><div class="plot-tabs" role="tablist" aria-label="Gráficas de {prefijo}">{botones}</div>'
             f'<p class="plot-help">Selecciona una vista. Amplía una gráfica para revisar sus leyendas y fronteras.</p>'
             f'<div class="plot-grid" id="graficas-{prefijo}" role="tabpanel" aria-labelledby="tab-{prefijo}-{pestañas[0][0]}">{"".join(ordenadas)}</div></div>')
    sin_figuras = re.sub(r"<figure>.*?</figure>", "", legado, flags=re.S)
    cuerpo = re.search(r"<body><main>(.*?)</main></body>", sin_figuras, re.S)[1]
    cabecera = re.search(r"<header>(.*?)</header>", cuerpo, re.S)[1]
    cuerpo = re.sub(r"<header>.*?</header>", "", cuerpo, flags=re.S)
    cuerpo = cuerpo.replace("<section>", '<div class="technical-section">').replace("</section>", "</div>")
    return visor, cuerpo, cabecera


def terminar_informe(legado, parametros, imagenes, fecha, version, *, noideal=None,
                     barrido=None, optimizaciones=None, estudio_rendimiento=None,
                     comparacion=None, sensibilidad=None):
    """Convierte presentación heredada a dashboard conservando datos/PNG sin recalcular."""
    from reporting import MARCA_INICIO, MARCA_FINAL
    visor, detalles, cabecera = visor_graficas(legado, imagenes, sensibilidad is not None)
    paneles = {k: "" for k in ("resultados", "optimizacion", "sensibilidad")}
    metadata = {"dashboard": 1, "tipo": "sensibilidad" if sensibilidad is not None else "normal",
                "parametros": parametros, "fecha": fecha.isoformat(), "git": version}
    valores = parametros.copy()
    valores["perdida_presion_combustor"] *= 100
    if sensibilidad is not None:
        c = sensibilidad["configuracion"]
        metadata["estudio"] = c
        valores.update(sens_parametro=c["parametro"], sens_minimo=c["minimo"], sens_maximo=c["maximo"], sens_muestras=c["muestras"])
        tarjetas = []
        for s in "RAB":
            disponibles = sum(r[s]["estado"] == "disponible" for r in sensibilidad["registros"])
            inviables = sum(r[s]["estado"] in ("inviable", "parametros_inviables", "sin_dominio") for r in sensibilidad["registros"])
            supremos = sum(r[s]["estado"] == "supremo_no_alcanzado" for r in sensibilidad["registros"])
            numericos = sum(r[s]["estado"] == "limite_numerico" for r in sensibilidad["registros"])
            tarjetas.append(tarjeta_kpi(s, f"{s} · Muestras operativas", disponibles, f"/ {c['muestras']}",
                f"{c['muestras'] - disponibles} no disponibles: {inviables} inviables, {supremos} supremos, {numericos} límites numéricos", decimales=0))
        filas_locales = []
        for s in "RAB":
            coeficientes = []
            for k in ("trabajo_neto", "rendimiento", "rp"):
                local = sensibilidad["sensibilidades"][s][k]
                valor = local["normalizada"]
                coeficientes.append(f'<td>{valor:.4f}</td>' if valor is not None else '<td>No disponible</td>')
            filas_locales.append(f'<tr><td>{s}</td>{"".join(coeficientes)}</tr>')
        resumen_local = ('<div class="card"><h3>Sensibilidades locales en la referencia</h3>'
            '<p class="muted">Elasticidades S=(x/Y)dY/dx, adimensionales. Incluyen reajuste de rp en A/B; no son puntos porcentuales ni un ranking universal.</p>'
            '<div class="table-wrap"><table><thead><tr><th>Escenario</th><th>S trabajo</th><th>S rendimiento</th><th>S rp</th></tr></thead><tbody>'
            + "".join(filas_locales) + '</tbody></table></div><small>Derivadas absolutas, paso y motivos de indisponibilidad en la tabla detallada.</small></div>')
        paneles["sensibilidad"] = (f'<div class="card"><h3>{escape(c["parametro"])} [{escape(c["unidad"])}] · {c["minimo"]:g}–{c["maximo"]:g}</h3>'
            f'<p>{c["muestras"]} muestras · R: rp fija · A: máximo trabajo · B: máximo rendimiento alcanzado.</p></div>'
            f'<div class="kpi-grid">{"".join(tarjetas)}</div>' + visor + resumen_local + plegable("Tabla de resultados, tendencias y límites", detalles))
    else:
        a = optimizaciones["noideal"]["analitico"] if optimizaciones else None
        eta = estudio_rendimiento["noideal"] if estudio_rendimiento else None
        b = eta["analitico"] if eta else None
        nota_b = eta["motivo"] if eta else "Estudio no disponible"
        indicadores = (("rp", "Relación de presiones", parametros["relacion_presiones"], "−", "Caso actual no ideal"),
            ("trabajo", "Trabajo específico neto", noideal["trabajo_neto"], "kJ/kg", "Caso actual no ideal"),
            ("rendimiento", "Rendimiento térmico", noideal["rendimiento"] * 100 if noideal["rendimiento"] is not None else None, "%", "Caso actual no ideal"),
            ("calor", "Calor aportado", noideal["calor_aportado"], "kJ/kg", "Caso actual no ideal"),
            ("max_trabajo", "Máximo trabajo específico", a["ciclo"]["trabajo_neto"] if a else None, "kJ/kg", "A · Máximo trabajo no ideal"),
            ("max_rendimiento", "Máximo rendimiento térmico", b["ciclo"]["rendimiento"] * 100 if b else None, "%", "B · Máximo interior" if b else nota_b))
        intervalo = barrido["dominios"]["noideal"]["intervalo"] if barrido else None
        estado = f"Rango motor abierto: {intervalo[0]:.6g} &lt; rp &lt; {intervalo[1]:.6g}." if intervalo else "Dominio no disponible en este informe."
        paneles["resultados"] = ('<div class="kpi-grid">' + "".join(tarjeta_kpi(*i) for i in indicadores) + '</div>'
            '<div class="card status-card"><span class="badge available">Ciclo motor verificado</span><h3>Estado del ciclo</h3>'
            f'<p>{estado} Las fronteras quedan excluidas; consulta las tolerancias en los detalles.</p></div>' + visor +
            plegable("Estados y balances detallados", detalles))
        decisiones = []
        for letra, titulo, punto, motivo in (("A", "Máximo trabajo específico", a, "No disponible"), ("B", "Máximo rendimiento térmico", b, nota_b)):
            if punto:
                datos = (("rp óptima", punto["rp"], "−"), ("Trabajo neto", punto["ciclo"]["trabajo_neto"], "kJ/kg"),
                         ("Rendimiento", punto["ciclo"]["rendimiento"] * 100, "%"), ("Calor aportado", punto["ciclo"]["calor_aportado"], "kJ/kg"))
                contenido = '<dl class="metric-list">' + "".join(f'<dt>{t}</dt><dd>{v:.3f} <small>{u}</small></dd>' for t, v, u in datos) + '</dl>'
            else:
                contenido = f'<span class="badge unavailable">No disponible</span><p>{escape(motivo)}</p>'
            decisiones.append(f'<article class="card design-card"><div class="card-title"><h3>{letra} — {titulo}</h3><span class="letter">{letra}</span></div>{contenido}</article>')
        compromiso = '<p>No hay dos máximos operativos alcanzados para comparar.</p>'
        if comparacion and comparacion["estado"] == "disponible":
            compromiso = '<dl class="metric-list">' + "".join(f'<dt>{t}</dt><dd>{comparacion[k]:.3f} <small>{u}</small></dd>' for k, t, u in (
                ("ganancia_rendimiento_pp", "Ganancia de rendimiento", "pp"), ("reduccion_trabajo_porcentaje", "Reducción relativa del trabajo", "%"),
                ("diferencia_calor", "Diferencia de calor B−A", "kJ/kg"), ("diferencia_rp", "Diferencia de rp B−A", "−"))) + '</dl>'
        paneles["optimizacion"] = f'<div class="two-columns">{"".join(decisiones)}</div><div class="card tradeoff"><h3>Compromiso entre objetivos</h3>{compromiso}<a href="#resultados/compromiso">Ver gráfica de compromiso</a></div>'
    info = '<div class="card metadata">' + cabecera.replace("<h1>", "<h3>").replace("</h1>", "</h3>") + '</div>'
    pagina = renderizar_dashboard(valores, contenidos=paneles, metadata=metadata,
                                  modo_local=False, informe_actual=info,
                                  seccion_inicial="sensibilidad" if sensibilidad is not None else "resultados")
    return MARCA_INICIO + pagina + MARCA_FINAL
