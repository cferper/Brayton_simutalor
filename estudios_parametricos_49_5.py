"""Barridos educativos M49.5: solo orquesta el solucionador motor existente."""

from math import isfinite
from time import perf_counter

from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo
from turborreactor_web import simular_turborreactor


UNIDADES = {"empuje_N": "N", "empuje_especifico": "N/(kg/s)",
            "TSFC": "kg/(N·h)"}


def configurar_estudio_49_5(configuracion, modo):
    """Valida JSON de configuración y genera dos ejes explícitos sin extrapolar."""
    if not isinstance(configuracion, dict):
        raise ValueError("Configuración del estudio no válida.")
    tipo = configuracion.get("tipo")
    if tipo not in ("mach", "T3", "mapa"):
        raise ValueError("Selecciona un estudio Mach, T3 o mapa Mach–T3.")
    limites = {"mach": (0., .95), "T3": (200., 2000.)}

    def eje(nombre):
        try:
            inicio = float(configuracion[f"{nombre}_inicio"])
            fin = float(configuracion[f"{nombre}_fin"])
            numero = int(configuracion[f"{nombre}_puntos"])
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"Intervalo o resolución de {nombre} inválidos.") from exc
        minimo, maximo = limites[nombre]
        limite_puntos = (6 if modo == "acoplado" else 11) if tipo == "mapa" else (
            9 if modo == "acoplado" else 21)
        if (not all(isfinite(v) for v in (inicio, fin)) or
                not minimo <= inicio < fin <= maximo or
                not 2 <= numero <= limite_puntos):
            raise ValueError(f"{nombre}: usa {minimo} ≤ inicio < fin ≤ {maximo} "
                             f"y de 2 a {limite_puntos} puntos.")
        return [inicio + (fin-inicio)*i/(numero-1) for i in range(numero)]

    xs = eje("mach" if tipo != "T3" else "T3")
    ys = eje("T3") if tipo == "mapa" else None
    if tipo == "mapa" and len(xs)*len(ys) > (36 if modo == "acoplado" else 121):
        raise ValueError("Malla demasiado grande.")
    return {"tipo": tipo, "x": xs, "y": ys,
            "eje_x": "mach" if tipo != "T3" else "T3",
            "eje_y": "T3" if tipo == "mapa" else None}


def calcular_estudio_49_5(valores, configuracion):
    """Ejecuta puntos independientes, conserva su clasificación y unidades.

    valores: dict[str,str] completo del formulario; configuracion: dict JSON.
    Cada punto usa simular_turborreactor(valores modificados), sin otros modelos.
    """
    modo = valores.get("modo_caudal", "impuesto")
    if modo not in ("impuesto", "fijo", "acoplado"):
        raise ValueError("Modalidad A/B/C desconocida.")
    ejes = configurar_estudio_49_5(configuracion, modo)
    inicio_tiempo = perf_counter()
    puntos = []
    for y in (ejes["y"] if ejes["y"] is not None else [None]):
        for x in ejes["x"]:
            parametros = dict(valores)
            parametros[ejes["eje_x"]] = format(x, ".12g")
            if y is not None:
                parametros["T3"] = format(y, ".12g")
            coordenadas = {"mach": float(parametros["mach"]),
                           "T3": float(parametros["T3"])}
            punto = {**coordenadas, "estado": "no_calculado", "motivo": None,
                     "empuje_N": None, "empuje_especifico": None, "TSFC": None,
                     "regimen_tobera": None}
            try:
                resultado = simular_turborreactor(parametros)
                if not resultado.get("tobera") or resultado["tobera"].get("resuelto") is False:
                    punto.update(estado="sin_solucion", motivo="Tobera sin salida resuelta")
                else:
                    fs = resultado["prestaciones"]["empuje_especifico_neto"]
                    absoluto = (resultado.get("prestaciones_absolutas") or {}).get("empuje_neto")
                    tsfc = resultado["prestaciones"].get("TSFC_kg_N_h")
                    punto.update(estado="valido", empuje_N=absoluto,
                                 empuje_especifico=fs,
                                 regimen_tobera=resultado.get("diagnosticos",{}).get("regimen_tobera"),
                                 TSFC=tsfc if fs is not None and fs > 0 and
                                 tsfc is not None and isfinite(tsfc) and tsfc >= 0 else None)
            except EstadoFueraDeRango:
                punto.update(estado="fuera_dominio", motivo="Propiedades fuera de 200–2000 K")
            except ErrorNumericoCiclo:
                punto.update(estado="fallo_numerico", motivo="No convergió el cálculo")
            except (ValueError, ArithmeticError, OverflowError) as exc:
                punto.update(estado="sin_solucion", motivo=str(exc)[:180])
            puntos.append(punto)
    validos = sum(p["estado"] == "valido" for p in puntos)
    return {"tipo": ejes["tipo"], "modo": modo, "ejes": ejes,
            "constantes": {k: v for k, v in valores.items() if k not in
                           ({"mach", "T3"} if ejes["tipo"] == "mapa" else
                            {ejes["eje_x"]})},
            "unidades": UNIDADES.copy(), "puntos": puntos,
            "resumen": {"total": len(puntos), "validos": validos,
                        "sin_solucion": len(puntos)-validos,
                        "segundos": round(perf_counter()-inicio_tiempo, 4)}}
