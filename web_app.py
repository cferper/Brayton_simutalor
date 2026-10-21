"""Formulario local Flask que reutiliza el simulador y sus informes."""

from math import isfinite
from html import escape
from pathlib import Path

from flask import Flask, Response, abort, redirect, request, url_for

from viabilidad import ErrorNumerico
from main import ErrorModelo, PARAMETROS_PREDETERMINADOS, main
from reporting import MARCA_FINAL, MARCA_INICIO, PATRON_INFORME
from sensibilidad import PARAMETROS_ESTUDIO, ejecutar_sensibilidad, validar_configuracion
from dashboard import CAMPOS, GRUPOS, renderizar_dashboard, separar_presentacion


app = Flask(__name__)
app.config["OUTPUTS_DIR"] = Path(__file__).resolve().parent / "outputs"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024



def valores_formulario():
    """Valores para GET; solo en la interfaz la pérdida se expresa en porcentaje."""
    valores = PARAMETROS_PREDETERMINADOS.copy()
    valores["perdida_presion_combustor"] *= 100
    return valores


def leer_parametros(formulario):
    """Convierte y valida los nueve campos; devuelve parámetros y errores por campo."""
    parametros = {}
    errores = {}
    for nombre in CAMPOS:
        texto = formulario.get(nombre, "").strip()
        if not texto:
            errores[nombre] = "Este campo es obligatorio."
            continue
        try:
            valor = float(texto)
        except ValueError:
            errores[nombre] = "Introduce un número válido."
            continue
        if not isfinite(valor):
            errores[nombre] = "El valor debe ser finito: no se admiten NaN ni infinitos."
        elif nombre in ("T1", "T3", "p1", "cp") and valor <= 0:
            errores[nombre] = "El valor debe ser estrictamente mayor que 0."
        elif nombre in ("gamma", "relacion_presiones") and valor <= 1:
            errores[nombre] = "El valor debe ser estrictamente mayor que 1."
        elif nombre in ("eta_c", "eta_t") and not 0 < valor <= 1:
            errores[nombre] = "La eficiencia debe cumplir 0 < eta ≤ 1."
        elif nombre == "perdida_presion_combustor" and not 0 <= valor < 100:
            errores[nombre] = "La pérdida debe cumplir 0 % ≤ pérdida < 100 %."
        else:
            parametros[nombre] = valor / 100 if nombre == "perdida_presion_combustor" else valor
    return parametros, errores


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
            tipo = "Sensibilidad OFAT" if metadata["tipo"] == "sensibilidad" else "Simulación normal"
            resumen = f"T1={p['T1']:g} K · T3={p['T3']:g} K · rp={p['relacion_presiones']:g}"
            fecha = metadata["fecha"]
            commit = metadata.get("git", {}).get("commit") or "No disponible"
        else:
            tipo = "Sensibilidad OFAT (formato anterior)" if "Análisis de sensibilidad paramétrica" in contenido else "Informe anterior"
            resumen = "Parámetros y metadatos: consultar el informe original."
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
    valores = valores_formulario() if request.method == "GET" else request.form.to_dict()
    errores = {}
    if request.method == "POST":
        parametros, errores = leer_parametros(request.form)
        configuracion = None
        if request.form.get("accion") == "sensibilidad":
            try:
                configuracion = validar_configuracion(
                    request.form.get("sens_parametro", "T3"),
                    float(request.form.get("sens_minimo", "800")),
                    float(request.form.get("sens_maximo", "2000")),
                    int(request.form.get("sens_muestras", "41")))
            except ValueError as error:
                errores["sensibilidad"] = f"Configuración de sensibilidad inválida: {error}"
        if not errores:
            try:
                if configuracion is None:
                    ruta = main(app.config["OUTPUTS_DIR"], parametros=parametros)
                else:
                    if parametros["T3"] <= parametros["T1"]:
                        raise ErrorModelo("La referencia debe cumplir T3 > T1; el barrido sí admite muestras no motoras.")
                    ruta = ejecutar_sensibilidad(app.config["OUTPUTS_DIR"], parametros,
                        **{k: configuracion[k] for k in ("parametro", "minimo", "maximo", "muestras")})
            except ErrorModelo as error:
                errores["modelo"] = str(error)
            except ErrorNumerico as error:
                errores["modelo"] = f"Límite numérico del cálculo: {error} No implica por sí mismo inviabilidad física."
            else:
                return redirect(url_for("ver_informe", nombre=ruta.name), code=303)
    return renderizar_dashboard(valores, errores=errores, informes=listar_informes(),
        seccion_inicial="sensibilidad" if request.form.get("accion") == "sensibilidad" else "simulacion"), 400 if errores else 200


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
    if presentacion is not None:
        metadata, paneles = presentacion
        valores = metadata["parametros"].copy()
        valores["perdida_presion_combustor"] *= 100
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
        return Response(renderizar_dashboard(valores, contenidos=paneles, metadata=metadata,
            informes=listar_informes(), informe_actual=actual,
            seccion_inicial="sensibilidad" if metadata["tipo"] == "sensibilidad" else "resultados"), mimetype="text/html")
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
    ), 500



def iniciar_servidor():
    """Servidor de uso local, sin depurador, recarga ni simulaciones paralelas."""
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=False)


if __name__ == "__main__":
    iniciar_servidor()
