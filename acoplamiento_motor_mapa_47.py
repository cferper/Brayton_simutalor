"""Monoeje estacionario fuera de diseño, mapas T-MATS escalados cp(T).

Resuelve simultáneamente giro, Rline y expansión de turbina para una
geometría fija. No cambia los solucionadores termodinámicos M35–M45.
"""

from math import isfinite, sqrt

from combustible_cp_variable import (_compresor, _combustor, _turbina,
                                      resolver_turborreactor_con_combustible)
from dimensionamiento_turborreactor import dimensionar_tobera
from mapas_turbomaquinaria_47 import (calibrar_mapas, consultar_compresor,
                                      consultar_turbina, cargar_mapas)
from tobera_cp_variable import resolver_tobera_convergente
from tobera_convergente_divergente_cp import resolver_tobera_convergente_divergente
from vuelo_cp_variable import aplicar_difusor, calcular_remanso
from propiedades_aire import R_AIRE


PARAMETROS_DISENO_47 = {
    "T_amb":288.15,"p_amb":100.0,"mach":0.0,"rp":10.0,
    "eta_c":.85,"T3":1600.0,"delta":.04,"eta_t":.9,
    "eta_m":.98,"eta_n":.95,"pi_d":1.0,"eta_b":.99,"PCI":43000.0,
}


def punto_diseno_47(*, mdot_aire=20.0, rpm=20000.0, mapas=None):
    """Diseño matemático de referencia (no potencia nominal de un motor real)."""
    r = resolver_turborreactor_con_combustible(**PARAMETROS_DISENO_47)
    escala = calibrar_mapas(r,mdot_aire,rpm,mapas=mapas)
    areas = dimensionar_tobera(r,mdot_aire)
    if not areas["disponible"] or not areas["garganta_bloqueada"]:
        raise ValueError("El punto de diseño no produce una garganta bloqueada.")
    escala.update(area_garganta_diseno=areas["area_garganta"],
                  area_salida_diseno=areas["area_salida"],
                  parametros_diseno=dict(PARAMETROS_DISENO_47),
                  eta_m=PARAMETROS_DISENO_47["eta_m"],
                  eta_n=PARAMETROS_DISENO_47["eta_n"],
                  eta_b=PARAMETROS_DISENO_47["eta_b"],
                  PCI=PARAMETROS_DISENO_47["PCI"],
                  delta=PARAMETROS_DISENO_47["delta"])
    return escala


def _resultado_punto(x, *, referencia, mapas, ambiente, mach, T3, pi_d, delta,
                     eta_b, PCI, eta_m, eta_n, area_garganta, tipo_tobera,
                     epsilon):
    """Calcula estados y tres residuos independientes de acoplamiento."""
    n_rel, rline, prt_rel = x
    N = referencia["rpm_mecanicas"]*n_rel
    prt = referencia["rp_turbina"]*prt_rel
    remanso = calcular_remanso(ambiente["temperatura"],ambiente["presion"],mach)
    difusor = aplicar_difusor(remanso,pi_d)
    Tt2,pt2 = difusor["temperatura_remanso"],difusor["presion_remanso"]
    comp_map = consultar_compresor(referencia,N,Tt2,pt2,rline,mapas=mapas)
    c = _compresor(Tt2,pt2,comp_map["rp"],comp_map["eta"])
    b = _combustor(c["h2"],T3,c["p2"],delta,eta_b,PCI)
    tur_map = consultar_turbina(referencia,N,T3,b["p3"],prt,mapas=mapas)
    t = _turbina(T3,b["p3"],b["h3"],c["trabajo_compresor"],
                 b["f"],eta_m,tur_map["eta"])
    if t["p4"] <= ambiente["presion"]:
        raise ValueError("La turbina no conserva margen para expansión de tobera.")
    if tipo_tobera == "convergente":
        tob = resolver_tobera_convergente(t["T4"],t["p4"],ambiente["presion"],eta_n)
        Gg = tob["densidad_salida"]*tob["velocidad_salida"]
    elif tipo_tobera == "convergente_divergente":
        tob = resolver_tobera_convergente_divergente(t["T4"],t["p4"],
                                                    ambiente["presion"],epsilon)
        if not tob["resuelto"]:
            raise ValueError("La tobera C-D no dispone de solución física.")
        Gg = tob["flujo_masico_por_area_garganta"]
    else:
        raise ValueError("Tipo de tobera no soportado.")
    ma = comp_map["gasto_masico_aire"]
    mg = ma*(1+b["f"])
    mn = Gg*area_garganta
    mt = tur_map["gasto_masico_gases"]
    # Tres ecuaciones: potencia/presión, continuidad turbina y tobera.
    # El balance de potencia del eje es resuelto exactamente por `_turbina`;
    # la primera ecuación exige que coincida su PR con el del mapa.
    resid = ((prt-b["p3"]/t["p4"])/referencia["rp_turbina"],
             (mg-mt)/referencia["mdot_gases"],
             (mg-mn)/referencia["mdot_gases"])
    return {"residuos":resid,"compresor_mapa":comp_map,"turbina_mapa":tur_map,
            "compresor":c,"combustor":b,"turbina":t,"tobera":tob,
            "remanso":remanso,"difusor":difusor,"ambiente":ambiente,
            "rpm":N,"rline":rline,"rp_turbina":prt,
            "caudal_aire":ma,"caudal_gases":mg,
            "residuo_masa_turbina":mg-mt,"residuo_masa_tobera":mg-mn,
            "residuo_potencia":t["residuo_eje"]*ma*1000}


def _norma(res):
    return sqrt(sum(v*v for v in res))


def _resolver_3x3(A,b):
    """Eliminación gaussiana con pivotado parcial y control de singularidad."""
    m=[list(A[i])+[b[i]] for i in range(3)]
    for j in range(3):
        k=max(range(j,3),key=lambda i:abs(m[i][j]))
        if abs(m[k][j]) < 1e-12:
            raise ValueError("Jacobiano singular: problema insuficientemente determinado.")
        m[j],m[k]=m[k],m[j]
        divisor=m[j][j]
        for l in range(j,4):
            m[j][l]/=divisor
        for i in range(j+1,3):
            fac=m[i][j]
            for l in range(j,4):
                m[i][l]-=fac*m[j][l]
    x=[0.0]*3
    for i in (2,1,0):
        x[i]=m[i][3]-sum(m[i][j]*x[j] for j in range(i+1,3))
    return x


def resolver_motor_acoplado(*, referencia=None, mapas=None,
                           T_amb=288.15,p_amb=100.,mach=0.,T3=1600.,
                           pi_d=1.,delta=.04,eta_b=.99,PCI=43000.,
                           eta_m=.98,eta_n=.95,area_garganta=None,
                           tipo_tobera="convergente",epsilon=1.,
                           max_iteraciones=35,tolerancia=2e-7):
    """Acoplamiento estacionario monoeje; fallo explícito sin estado inventado.

    Incógnitas (N, Rline, PRt). Se prescribe Tt3 (control de combustible)
    y área física de garganta; no se imponen simultáneamente rp y mdot.
    """
    mapas=cargar_mapas() if mapas is None else mapas
    ref=punto_diseno_47(mapas=mapas) if referencia is None else referencia
    area=ref["area_garganta_diseno"] if area_garganta is None else area_garganta
    if isinstance(area,bool) or not isinstance(area,(int,float)) or not isfinite(area) or area<=0:
        raise ValueError("El área fija de garganta debe ser positiva y finita.")
    if tipo_tobera=="convergente_divergente" and (not isfinite(epsilon) or epsilon<1):
        raise ValueError("La C-D requiere epsilon ≥ 1.")
    if tipo_tobera not in ("convergente","convergente_divergente"):
        raise ValueError("Tipo de tobera incompatible.")
    if not 0 < tolerancia <= 1e-3 or not 1 <= max_iteraciones <= 100:
        raise ValueError("Tolerancia o iteraciones fuera del dominio numérico.")
    if not 0 < eta_m <= 1:
        raise ValueError("Rendimiento mecánico inválido.")
    if not 0 <= mach < 1:
        raise ValueError("Mach de vuelo fuera del modelo subsónico.")
    ambiente={"temperatura":T_amb,"presion":p_amb,
              "densidad":p_amb*1000/(R_AIRE*T_amb)}
    kwargs=dict(referencia=ref,mapas=mapas,ambiente=ambiente,mach=mach,
                T3=T3,pi_d=pi_d,delta=delta,eta_b=eta_b,PCI=PCI,
                eta_m=eta_m,eta_n=eta_n,area_garganta=area,
                tipo_tobera=tipo_tobera,epsilon=epsilon)
    x=[1.,2.,1.]
    historico=[]
    estado=None
    for it in range(max_iteraciones+1):
        try:
            estado=_resultado_punto(x,**kwargs)
        except (ValueError,ArithmeticError,OverflowError) as exc:
            return {"disponible":False,"motivo":str(exc),"iteraciones":it,
                    "historico_normas":historico}
        f=estado["residuos"]
        norma=_norma(f)
        historico.append(norma)
        if norma <= tolerancia:
            # Comprobaciones finales *dimensionales*, además de residuo normalizado.
            ma,mg=estado["caudal_aire"],estado["caudal_gases"]
            if (abs(estado["residuo_masa_turbina"]) > tolerancia*ref["mdot_gases"]
                or abs(estado["residuo_masa_tobera"]) > tolerancia*ref["mdot_gases"]
                or abs(estado["residuo_potencia"]) > 1e-4*max(1,ma*estado["compresor"]["trabajo_compresor"]*1000)):
                return {"disponible":False,"motivo":"Cierres físicos insuficientes.","iteraciones":it,
                        "historico_normas":historico}
            t=estado["tobera"]
            fcomb=estado["combustor"]["f"]
            v0=estado["remanso"]["velocidad_vuelo"]
            termino_presion=(1+fcomb)*t["empuje_especifico_presion"]
            Fs=(1+fcomb)*t["velocidad_salida"]+termino_presion-v0
            estado.update(disponible=True,iteraciones=it,
                          norma_residual=norma,historico_normas=historico,
                          empuje_especifico=Fs,empuje_absoluto=ma*Fs,
                          caudal_combustible=ma*fcomb,
                          aviso="Punto de equilibrio de mapas escalados; no es un motor real validado.")
            return estado
        if it==max_iteraciones:
            break
        # Jacobiano por diferencias centrales cuando el dominio lo permite;
        # unilateral si un límite del mapa excluye una perturbación.
        J=[[0.]*3 for _ in range(3)]
        try:
            for j in range(3):
                paso=2e-5*max(1,abs(x[j]))
                xp=x.copy(); xm=x.copy()
                xp[j]+=paso; xm[j]-=paso
                try:
                    fp=_resultado_punto(xp,**kwargs)["residuos"]
                except (ValueError,ArithmeticError,OverflowError):
                    fp=None
                try:
                    fm=_resultado_punto(xm,**kwargs)["residuos"]
                except (ValueError,ArithmeticError,OverflowError):
                    fm=None
                if fp is not None and fm is not None:
                    diferencia=2*paso
                elif fp is not None:
                    fm=f;diferencia=paso
                elif fm is not None:
                    fp=f;diferencia=paso
                else:
                    raise ValueError("No hay perturbación admisible en el mapa para derivar.")
                for i in range(3):
                    J[i][j]=(fp[i]-fm[i])/diferencia
            paso_newton=_resolver_3x3(J,[-v for v in f])
        except (ValueError,ArithmeticError,OverflowError) as exc:
            return {"disponible":False,"motivo":f"No se construye Jacobiano: {exc}",
                    "iteraciones":it,"historico_normas":historico}
        aceptado=False
        for k in range(22):
            factor=.5**k
            prueba=[x[j]+factor*paso_newton[j] for j in range(3)]
            try:
                fprueba=_resultado_punto(prueba,**kwargs)["residuos"]
                if _norma(fprueba) < norma*(1-1e-4*factor):
                    x=prueba;aceptado=True;break
            except (ValueError,ArithmeticError,OverflowError):
                continue
        if not aceptado:
            return {"disponible":False,"motivo":"Sin descenso del residuo en línea de búsqueda.",
                    "iteraciones":it,"historico_normas":historico}
    return {"disponible":False,"motivo":"No convergió el balance simultáneo.",
            "iteraciones":max_iteraciones,"historico_normas":historico}
