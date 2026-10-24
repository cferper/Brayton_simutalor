"""Dashboard Flask cp(T) y consulta de informes históricos de solo lectura."""

from html import escape
from pathlib import Path

from flask import Flask, Response, abort, redirect, request, url_for

from reporting import MARCA_FINAL, MARCA_INICIO, PATRON_INFORME
from dashboard import renderizar_dashboard, separar_presentacion
from segunda_ley import validar_estudio_reutilizable
from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo
from cp_variable_web import (DEFAULTS, FIELDS, leer_entradas, preparar_resultados,
                             preparar_sensibilidad, preparar_mapa, preparar_segunda_ley)
from sensibilidad_cp_variable import PARAMETROS_CP
from mapa_diseno_cp_variable import DEFAULT_MAPA


app = Flask(__name__)
app.config["OUTPUTS_DIR"] = Path(__file__).resolve().parent / "outputs"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024



def valores_formulario():
    """Las siete entradas del modelo cp(T), sin cp ni gamma constantes."""
    return DEFAULTS.copy()


def listar_informes():
    """Historial de sólo lectura: archivos propios completos, sin borrar ni inventar datos."""
    carpeta = Path(app.config["OUTPUTS_DIR"])
    if not carpeta.is_dir():
        return []
    informes = []
    for ruta in carpeta.iterdir():
        if not PATRON_INFORME.fullmatch(ruta.name) or ruta.is_symlink() or not ruta.is_file():
            continue
        try:
            contenido = ruta.read_text(encoding="utf-8")
        except (UnicodeError, FileNotFoundError):
            continue
        if not contenido.startswith(MARCA_INICIO) or not contenido.endswith(MARCA_FINAL):
            continue
        presentacion = separar_presentacion(contenido)
        if presentacion:
            metadata = presentacion[0]
            p = metadata["parametros"]
            tipo = {'sensibilidad': 'Sensibilidad OFAT', 'mapa': 'Mapa de diseño', 'segunda_ley': 'Segunda ley'}.get(metadata['tipo'], 'Simulación normal')
            resumen = f"T1={p['T1']:g} K · T3={p['T3']:g} K · rp={p['relacion_presiones']:g}"
            fecha = metadata["fecha"]
            commit = metadata.get("git", {}).get("commit") or "No disponible"
        else:
            danado = 'id="brayton-metadata"' in contenido
            tipo = ("Informe con metadatos inválidos" if danado else
                    "Sensibilidad OFAT (formato anterior)" if "Análisis de sensibilidad paramétrica" in contenido else "Informe anterior")
            resumen = ("El JSON no puede recuperarse; el archivo original sigue disponible."
                       if danado else "Parámetros y metadatos: consultar el informe original.")
            fecha, commit = "Fecha: consultar original", "No disponible en el índice"
        informes.append({"nombre": ruta.name, "tipo": tipo, "resumen": resumen,
                         "fecha": fecha, "commit": commit, "mtime": ruta.stat().st_mtime_ns})
    return sorted(informes, key=lambda i: (i["mtime"], i["nombre"]), reverse=True)


@app.route("/documentacion/<nombre>")
def ver_documentacion(nombre):
    """Sirve sólo README/walkthrough como texto; sin exploración arbitraria de rutas."""
    if nombre not in ("README.md", "CODE_WALKTHROUGH.md"):
        abort(404)
    ruta = Path(__file__).resolve().parent / nombre
    return Response(ruta.read_text(encoding="utf-8"), mimetype="text/plain")


@app.route("/", methods=["GET", "POST"])
def index():
    """Único formulario activo: calcula exclusivamente con cp(T)."""
    valores = valores_formulario() if request.method == "GET" else {
        clave: request.form.get(clave, "") for clave in DEFAULTS
    }
    accion = request.form.get('accion') if request.method == 'POST' else None
    rango_sugerido = PARAMETROS_CP['T3']['rango']
    sens_config = {
        'parametro': request.form.get('sens_cp_parametro', 'T3'),
        'minimo': request.form.get('sens_cp_minimo', str(rango_sugerido[0])),
        'maximo': request.form.get('sens_cp_maximo', str(rango_sugerido[1])),
        'muestras': request.form.get('sens_cp_muestras', '41'),
    }
    mapa_config = {key: request.form.get('mapa_cp_'+key, str(value))
                   for key,value in DEFAULT_MAPA.items()}
    segunda_config = {'T0': request.form.get('T0', '288.15'),
                      'p0': request.form.get('p0', '100')}
    errores, datos, sens_datos, mapa_datos, segunda_datos = {}, {}, {}, {}, {}
    if request.method == "POST":
        if accion not in ("normal", "optimizar", "sensibilidad", "mapa", "segunda_ley"):
            errores["modelo"] = "Este estudio aún no está adaptado al modelo cp(T)."
        else:
            try:
                entradas = leer_entradas(request.form)
                if accion == 'sensibilidad':
                    sens_datos = preparar_sensibilidad(
                        entradas, sens_config['parametro'],
                        float(sens_config['minimo']), float(sens_config['maximo']),
                        int(sens_config['muestras']))
                elif accion == 'mapa':
                    mapa_datos = preparar_mapa(
                        entradas,
                        rp_min=float(mapa_config['rp_min']),
                        rp_max=float(mapa_config['rp_max']),
                        T3_min=float(mapa_config['T3_min']),
                        T3_max=float(mapa_config['T3_max']),
                        n_rp=int(mapa_config['n_rp']),
                        n_T3=int(mapa_config['n_T3']))
                elif accion == 'segunda_ley':
                    segunda_datos = preparar_segunda_ley(
                        entradas, float(segunda_config['T0']),
                        float(segunda_config['p0']))
                else:
                    datos = preparar_resultados(entradas)
            except EstadoFueraDeRango as exc:
                errores["modelo"] = f"Estado fuera de 200–2000 K: {exc}"
            except ErrorNumericoCiclo:
                errores["modelo"] = "El solucionador numérico no ha convergido."
            except ValueError as exc:
                errores["modelo"] = f"Entrada no válida: {exc}"
            except ArithmeticError:
                errores["modelo"] = "No ha convergido la búsqueda numérica."
    seccion = ("segunda_ley" if accion == 'segunda_ley' else
               "mapa" if accion == 'mapa' else
               "sensibilidad" if accion == 'sensibilidad' else
               "optimizacion" if accion == "optimizar"
               else "resultados" if datos else "simulacion")
    pagina = renderizar_dashboard(
        valores, errores=errores, informes=listar_informes(),
        seccion_inicial=seccion, modo_cp=True, cp_datos=datos, campos_cp=FIELDS,
        sens_datos=sens_datos, sens_config=sens_config, sens_parametros=PARAMETROS_CP,
        mapa_datos=mapa_datos, mapa_config=mapa_config,
        segunda_datos=segunda_datos, segunda_config=segunda_config)
    return pagina, (400 if errores else 200)


@app.route("/informes/<nombre>")
def ver_informe(nombre):
    """Sirve solo informes propios completos de outputs; nunca rutas arbitrarias."""
    if not PATRON_INFORME.fullmatch(nombre):
        abort(404)
    carpeta = Path(app.config["OUTPUTS_DIR"]).resolve()
    ruta = carpeta / nombre
    if ruta.is_symlink() or not ruta.is_file() or ruta.resolve().parent != carpeta:
        abort(404)
    try:
        contenido = ruta.read_text(encoding="utf-8")
    except (UnicodeError, FileNotFoundError):
        abort(404)
    if not contenido.startswith(MARCA_INICIO) or not contenido.endswith(MARCA_FINAL):
        abort(404)
    if request.args.get("descargar") == "1":
        return Response(contenido, mimetype="text/html", headers={
            "Content-Disposition": f'attachment; filename="{nombre}"',
        })
    presentacion = separar_presentacion(contenido)
    if presentacion is None and 'id="brayton-metadata"' in contenido:
        aviso = ('<main><h1>Metadatos del informe inválidos</h1>'
                 '<p>El JSON conservado no puede recuperarse con seguridad. '
                 'Esto no implica inviabilidad física del ciclo. El archivo histórico no se ha modificado.</p>'
                 f'<p><a href="{url_for("ver_informe", nombre=nombre, descargar=1)}">Descargar HTML original</a></p>'
                 '<p><a href="/">Volver al formulario</a></p></main>')
        return Response(aviso, status=422, mimetype="text/html")
    if presentacion is not None:
        metadata, paneles = presentacion
        valores = metadata["parametros"].copy()
        valores["perdida_presion_combustor"] *= 100
        valores['informe_origen'] = nombre
        if metadata.get('segunda_ley'):
            valores['T0'] = metadata['segunda_ley']['T0']
        if metadata.get('mapa'):
            valores.update({'mapa_' + k: v for k, v in metadata['mapa'].items() if k != 'cortes'})
            valores['mapa_cortes'] = ', '.join(str(t) for t in metadata['mapa']['cortes'])
        if metadata.get("estudio"):
            c = metadata["estudio"]
            valores.update(sens_parametro=c["parametro"], sens_minimo=c["minimo"],
                           sens_maximo=c["maximo"], sens_muestras=c["muestras"])
        version = metadata.get("git", {})
        aviso = {True: "Cambios locales sin confirmar", False: "Árbol de trabajo limpio", None: "Estado local no disponible"}.get(version.get("modificado"))
        actual = ('<div class="card metadata"><h3>Informe actual</h3>'
            f'<p>{escape(str(metadata.get("fecha", "No disponible")))}</p>'
            f'<p>Commit Git: <code>{escape(version.get("commit") or "No disponible")}</code></p>'
            f'<p class="version-warning">{aviso}</p>'
            f'<nav><a href="/">Volver al formulario</a> · <a href="/informes/{nombre}?descargar=1">Descargar informe HTML</a></nav></div>')
        if metadata.get('segunda_ley') is not None and not validar_estudio_reutilizable(metadata['segunda_ley'], metadata['parametros']):
            actual += ('<div class="card metadata"><p><strong>Estudio de Segunda Ley no verificable:</strong> '
                       'los datos JSON de este informe no se reutilizarán. El HTML original se conserva; '
                       'este aviso no significa inviabilidad física ni autenticidad comprobada.</p></div>')
        return Response(renderizar_dashboard(valores, contenidos=paneles, metadata=metadata,
            informes=listar_informes(), informe_actual=actual,
            seccion_inicial={'sensibilidad': 'sensibilidad', 'mapa': 'mapa', 'segunda_ley': 'segunda_ley'}.get(metadata['tipo'], 'resultados')), mimetype="text/html")
    # Solo la respuesta del navegador lleva navegación. El HTML guardado no cambia.
    navegacion = (
        '<nav aria-label="Navegación del informe" style="margin:20px 0">'
        f'<a href="{url_for("index")}">Volver al formulario</a> · '
        f'<a href="{url_for("ver_informe", nombre=nombre, descargar=1)}">Descargar informe HTML</a>'
        '</nav>'
    )
    return Response(contenido.replace("</header>", "</header>" + navegacion, 1), mimetype="text/html")


@app.errorhandler(500)
def error_interno(error):
    """Flask registra la traza en terminal; el navegador recibe un mensaje genérico."""
    return renderizar_dashboard(
        request.form.to_dict() if request.method == "POST" else valores_formulario(),
        informes=listar_informes(),
        errores={"servidor": "Se ha producido un error interno. Consulta la terminal para ver el detalle; no es un rechazo físico de los parámetros."},
        modo_cp=True, campos_cp=FIELDS,
    ), 500



def iniciar_servidor():
    """Servidor de uso local, sin depurador, recarga ni simulaciones paralelas."""
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=False)


if __name__ == "__main__":
    iniciar_servidor()
