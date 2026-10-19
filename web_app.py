"""Formulario local Flask que reutiliza el simulador y sus informes."""

from math import isfinite
from pathlib import Path

from flask import Flask, Response, abort, redirect, render_template, request, url_for

from main import ErrorModelo, PARAMETROS_PREDETERMINADOS, main
from reporting import MARCA_FINAL, MARCA_INICIO, PATRON_INFORME


app = Flask(__name__)
app.config["OUTPUTS_DIR"] = Path(__file__).resolve().parent / "outputs"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

GRUPOS = (
    ("Condiciones del ciclo", ("T1", "T3", "p1", "relacion_presiones")),
    ("Propiedades del gas", ("cp", "gamma")),
    ("Componentes no ideales", ("eta_c", "eta_t", "perdida_presion_combustor")),
)
CAMPOS = {
    "T1": ("T1 · Entrada del compresor", "K", "Mayor que 0", "0", None),
    "T3": ("T3 · Entrada de la turbina", "K", "Mayor que 0", "0", None),
    "p1": ("p1 · Presión de entrada", "kPa", "Mayor que 0", "0", None),
    "relacion_presiones": ("Relación de presiones del compresor", "adimensional", "Mayor que 1", "1", None),
    "cp": ("cp · Calor específico", "J/(kg·K)", "Mayor que 0", "0", None),
    "gamma": ("gamma · Relación cp/cv", "adimensional", "Mayor que 1", "1", None),
    "eta_c": ("eta_c · Eficiencia del compresor", "adimensional", "0 < eta_c ≤ 1", "0", "1"),
    "eta_t": ("eta_t · Eficiencia de la turbina", "adimensional", "0 < eta_t ≤ 1", "0", "1"),
    "perdida_presion_combustor": ("Pérdida relativa de presión del combustor", "%", "0 ≤ pérdida < 100 %", "0", "100"),
}


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


@app.route("/", methods=["GET", "POST"])
def index():
    valores = valores_formulario() if request.method == "GET" else request.form.to_dict()
    errores = {}
    if request.method == "POST":
        parametros, errores = leer_parametros(request.form)
        if not errores:
            try:
                ruta = main(app.config["OUTPUTS_DIR"], parametros=parametros)
            except ErrorModelo as error:
                errores["modelo"] = str(error)
            else:
                return redirect(url_for("ver_informe", nombre=ruta.name), code=303)
    return render_template("index.html", grupos=GRUPOS, campos=CAMPOS,
                           valores=valores, errores=errores), 400 if errores else 200


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
    return render_template(
        "index.html", grupos=GRUPOS, campos=CAMPOS,
        valores=request.form.to_dict() if request.method == "POST" else valores_formulario(),
        errores={"servidor": "Se ha producido un error interno. Consulta la terminal de VS Code para ver el detalle; no es un rechazo físico de los parámetros."},
    ), 500


def iniciar_servidor():
    """Servidor de uso local, sin depurador, recarga ni simulaciones paralelas."""
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=False)


if __name__ == "__main__":
    iniciar_servidor()
