"""Segunda ley sobre estados existentes. s relativa [kJ/(kg K)], eD [kJ/kg]."""
from copy import deepcopy
from math import isfinite, log

from viabilidad import ErrorNumerico


class InconsistenciaSegundaLey(ValueError):
    """Generación adiabática negativa fuera de la banda de redondeo."""


def validar_referencia(T0):
    """Temperatura de referencia independiente del ciclo, positiva y finita [K]."""
    if isinstance(T0, bool) or not isfinite(T0) or T0 <= 0:
        raise ValueError('T0 debe ser positiva y finita, en K.')
    return float(T0)


def cambio_entropia(Ti, pi, Tj, pj, cp, gamma):
    """Cambio del fluido, no necesariamente generación; descompone T y p."""
    if not all(isfinite(x) and x > 0 for x in (Ti, pi, Tj, pj, cp)) or not isfinite(gamma) or gamma <= 1:
        raise ValueError('Estados positivos finitos, cp > 0 y gamma > 1 requeridos.')
    if cp/1000 == 0:
        raise ErrorNumerico('Escala de entropía menor que la resolución representable.')
    # Diferencias de logaritmos evitan desbordar o subdesbordar Tj/Ti y pj/pi.
    termica = cp / 1000 * (log(Tj) - log(Ti))
    presion = -(cp / 1000) * (1 - 1/gamma) * (log(pj) - log(pi))
    total = termica + presion
    if not all(isfinite(x) for x in (termica, presion, total)):
        raise ErrorNumerico('Cambio de entropía no representable.')
    return dict(termica=termica, presion=presion, total=total)


def generacion_adiabatica(s_entrada, s_salida, escala=1.):
    """Conserva valor bruto y tolerancia; sólo corrige negativos de redondeo."""
    if not all(isfinite(x) for x in (s_entrada, s_salida, escala)) or escala <= 0:
        raise ValueError('Entropías finitas y escala positiva requeridas.')
    bruto = s_salida - s_entrada
    tolerancia = 1e-10 * max(abs(s_entrada), abs(s_salida), escala)
    if not isfinite(bruto):
        raise ErrorNumerico('Diferencia de entropías no representable.')
    if bruto < -tolerancia:
        raise InconsistenciaSegundaLey('Generación de entropía adiabática negativa fuera de tolerancia.')
    return dict(valor=max(0., bruto), bruto=bruto, tolerancia=tolerancia)


def analizar_estados(punto, cp, gamma, T0=288.15):
    """No resuelve ni reclasifica el ciclo: recibe el registro de evaluar_punto."""
    T0 = validar_referencia(T0)
    temperaturas, presiones = tuple(punto['temperaturas']), tuple(punto['presiones'])
    if len(temperaturas) != 4 or len(presiones) != 4:
        raise ValueError('Se requieren exactamente cuatro estados T,p.')
    s = tuple(cambio_entropia(temperaturas[0], presiones[0], T, p, cp, gamma)['total']
              for T, p in zip(temperaturas, presiones))
    componentes = {}
    for nombre, i, j in (('compresor', 0, 1), ('turbina', 2, 3)):
        try:
            generacion = generacion_adiabatica(s[i], s[j], cp/1000)
        except InconsistenciaSegundaLey as error:
            return dict(estado='inconsistencia', motivo=nombre+': '+str(error),
                        entropias=s, temperaturas=temperaturas, presiones=presiones)
        componentes[nombre] = {**generacion, 'exergia_destruida': T0 * generacion['valor']}
    suma = sum(c['exergia_destruida'] for c in componentes.values())
    if not isfinite(suma):
        raise ErrorNumerico('Destrucción de exergía no representable.')
    return dict(estado='motor' if punto['viable'] else 'diagnostico_no_motor',
                viable=punto['viable'], motivos=tuple(punto['motivos']),
                temperaturas=temperaturas, presiones=presiones, entropias=s,
                componentes=componentes, suma_componentes=suma,
                camara=cambio_entropia(temperaturas[1], presiones[1], temperaturas[2], presiones[2], cp, gamma))


def analizar_segunda_ley(estados, cp, gamma, T0=288.15):
    """Compara ideal/noideal; separa límite numérico e inconsistencia física."""
    T0 = validar_referencia(T0)
    resultado = dict(T0=T0, cp=cp, gamma=gamma, modelos={})
    for nombre in ('ideal', 'noideal'):
        try:
            resultado['modelos'][nombre] = analizar_estados(estados[nombre], cp, gamma, T0)
        except ErrorNumerico as error:
            resultado['modelos'][nombre] = dict(estado='limite_numerico', motivo=str(error))
        except InconsistenciaSegundaLey as error:
            resultado['modelos'][nombre] = dict(estado='inconsistencia', motivo=str(error))
    return resultado


def actualizar_T0(estudio, T0):
    """Copia el estudio y cambia sólo T0/eD, sin evaluar estados ni entropías."""
    T0 = validar_referencia(T0)
    nuevo = deepcopy(estudio)
    nuevo['T0'] = T0
    for modelo in nuevo['modelos'].values():
        if modelo['estado'] not in ('motor', 'diagnostico_no_motor'):
            continue
        for c in modelo['componentes'].values():
            c['exergia_destruida'] = T0*c['valor']
        modelo['suma_componentes'] = sum(c['exergia_destruida'] for c in modelo['componentes'].values())
        if not isfinite(modelo['suma_componentes']):
            raise ErrorNumerico('Destrucción de exergía no representable para T0.')
    return nuevo


def crear_graficas_segunda_ley(estudio):
    """Dos SVG en memoria: estados T-s y eD de los dos equipos adiabáticos."""
    from io import StringIO
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figuras = {}
    for nombre in ('estados_ts', 'exergia_componentes'):
        fig, ax = plt.subplots(figsize=(8, 5))
        try:
            for indice, (modelo, datos) in enumerate(estudio['modelos'].items()):
                etiqueta = 'Ideal' if modelo == 'ideal' else 'No ideal'
                if datos['estado'] not in ('motor', 'diagnostico_no_motor'):
                    ax.text(.03, .95-.08*indice, etiqueta+': '+datos['estado'], transform=ax.transAxes)
                    continue
                etiqueta += ' · diagnóstico no motor' if not datos['viable'] else ' · motor'
                if nombre == 'estados_ts':
                    s, t = datos['entropias'], datos['temperaturas']
                    ax.plot((*s, s[0]), (*t, t[0]), 'o--', label=etiqueta+'; guía entre estados')
                    for i, (x, y) in enumerate(zip(s, t), 1):
                        ax.annotate(str(i), (x, y), xytext=(5, 4+indice*9), textcoords='offset points')
                else:
                    ax.bar([x+indice*.35 for x in (0, 1)],
                           [datos['componentes'][c]['exergia_destruida'] for c in ('compresor', 'turbina')],
                           width=.35, label=etiqueta)
            if nombre == 'estados_ts':
                ax.set(xlabel='Entropía específica relativa s [kJ/(kg·K)]', ylabel='Temperatura [K]',
                       title='Cuatro estados; conexiones sólo como guía visual')
                ax.grid(alpha=.2)
            else:
                ax.set_xticks([.175, 1.175], ['Compresor', 'Turbina'])
                ax.set(ylabel='Destrucción de exergía [kJ/kg]', title=f"Equipos adiabáticos · T0={estudio['T0']:g} K")
            if ax.get_legend_handles_labels()[0]: ax.legend(fontsize=8)
            fig.tight_layout()
            salida = StringIO(); fig.savefig(salida, format='svg')
            svg = salida.getvalue(); svg = svg[svg.index('<svg'):]
            # Identificadores aislados entre los dos SVG incrustados.
            svg = svg.replace('id="', f'id="{nombre}-').replace('href="#', f'href="#{nombre}-').replace('url(#', f'url(#{nombre}-')
            figuras[nombre] = svg
        finally:
            plt.close(fig)
    return figuras


def ejecutar_segunda_ley(carpeta_salida, parametros, T0=288.15, estudio_previo=None):
    """Modo diagnóstico o actualización T0; sin optimización ni barridos."""
    from datetime import datetime
    from pathlib import Path
    from sensibilidad import argumentos_fisicos
    from viabilidad import evaluar_punto
    from reporting import crear_informe_segunda_ley_html, guardar_informe_html, obtener_version_git
    T0 = validar_referencia(T0)
    if estudio_previo is not None:
        estudio = actualizar_T0(estudio_previo, T0)
    else:
        T1, T3, gamma, cp, p1, ec, et, delta = argumentos_fisicos(parametros)
        rp = parametros['relacion_presiones']
        estados = dict(ideal=evaluar_punto(T1, T3, gamma, cp, rp, p1),
                       noideal=evaluar_punto(T1, T3, gamma, cp, rp, p1, ec, et, delta))
        estudio = analizar_segunda_ley(estados, cp, gamma, T0)
    fecha = datetime.now().astimezone()
    html = crear_informe_segunda_ley_html(parametros, estudio, fecha, obtener_version_git(Path(__file__).resolve().parent))
    return guardar_informe_html(html, carpeta_salida, fecha)
