"""Fase 2C: dominio y optimización Brayton cp(T), sin dependencias externas.

No cambia el solucionador 2B ni las interfaces existentes. Entradas de
temperatura en K, presión en kPa, resultados energéticos en kJ/kg.
"""
from math import exp, isfinite, log, sqrt
from numbers import Real
from ciclo_cp_variable import resolver_ciclo, EstadoFueraDeRango, ErrorNumericoCiclo
from propiedades_aire import T_MIN, T_MAX, h, s0, R_AIRE


def _real_positivo(x):
    return isinstance(x, Real) and not isinstance(x, bool) and isfinite(x) and x > 0


def _raiz_monotona(funcion, inferior, superior, *, creciente=True, tol=1e-11):
    """Bisección sobre raíz encerrada de función monótona (argumento log rp)."""
    fa, fb = funcion(inferior), funcion(superior)
    if fa == 0: return inferior
    if fb == 0: return superior
    if (fa < 0) == (fb < 0):
        raise ValueError('La raíz no está encerrada.')
    for _ in range(100):
        centro = (inferior + superior)/2
        fc = funcion(centro)
        if abs(superior-inferior) <= tol:
            return centro
        if (fc < 0) == (fa < 0):
            inferior, fa = centro, fc
        else:
            superior, fb = centro, fc
    raise ArithmeticError('No converge la raíz acotada.')


def _maximo_acotado(funcion, inferior, superior, tolerancia):
    """Sección áurea en un tramo unimodal, sobre log(rp)."""
    phi = (sqrt(5)-1)/2
    a,b = inferior,superior
    c,d = b-phi*(b-a), a+phi*(b-a)
    fc,fd = funcion(c),funcion(d)
    for _ in range(160):
        if b-a < tolerancia:
            return (a+b)/2
        if fc < fd:
            a,c,fc = c,d,fd
            d = a+phi*(b-a); fd=funcion(d)
        else:
            b,d,fd = d,c,fc
            c = b-phi*(b-a); fc=funcion(c)
    raise ArithmeticError('No converge el maximizador.')


def estudiar_cp_variable(T1, T3, p1=100., eta_c=.85, eta_t=.9, delta=.05,
                         *, tolerancia=1e-9, muestras=160):
    """Devuelve dominio abierto y máximos A/B, o ausencia de dominio motor.

    Se exige el sentido nominal de ambas turbomáquinas. Los límites térmicos
    se derivan de entropía y entalpía; el trabajo se evalúa con el motor 2B.
    B usa la monotonía del numerador de su derivada con q_in,q_out>0.
    A verifica si su máximo es interior o sólo un supremo de frontera.
    """
    parametros=(T1,T3,p1,eta_c,eta_t,delta,tolerancia)
    if any(not isinstance(v,Real) or isinstance(v,bool) or not isfinite(v) for v in parametros):
        raise ValueError('Se requieren números reales finitos, sin bool.')
    if not (T_MIN <= T1 <= T_MAX and T_MIN <= T3 <= T_MAX and p1>0
            and 0<eta_c<=1 and 0<eta_t<=1 and 0<=delta<1
            and 0<tolerancia<1):
        raise ValueError('Parámetros fuera de dominio.')
    if isinstance(muestras,bool) or not isinstance(muestras,int) or muestras<12 or muestras>10000:
        raise ValueError('muestras debe ser entero entre 12 y 10000.')
    r=R_AIRE/1000
    # El compresor normal se limita por su temperatura REAL, no sólo por 2s.
    # h(T2s)<=h(T1)+eta_c*(h(Tmax)-h(T1)).
    # En extremos, no invertir h: comparar con la identidad directamente.
    from propiedades_aire import T_desde_h
    s2_limit = s0(T_desde_h(h(T1)+eta_c*(h(T_MAX)-h(T1))))
    x_cmax = (s2_limit-s0(T1))/r
    # Para expansión normal, la referencia 4s nunca puede bajar de T_MIN.
    x_tmax = (s0(T3)-s0(T_MIN))/r-log(1-delta)
    xlo = -log(1-delta) # p3 > p4; necesariamente rp>1
    # q_in>0 requiere h2<h3. Es una cota adicional independiente.
    if h(T3)<=h(T1):
        return {"dominio_motor":None,"A":None,"B":None,
                "limites_calculables":None,"tipo":"sin_motor"}
    x_qmax = (s0(T_desde_h(h(T1)+eta_c*(h(T3)-h(T1))))-s0(T1))/r
    # El ciclo sin regeneración también debe rechazar calor hacia el foco frío.
    h4s_critico = h(T3)-(h(T3)-h(T1))/eta_t
    x_outmax = float("inf")
    if h4s_critico > h(T_MIN):
        x_outmax = (s0(T3)-s0(T_desde_h(h4s_critico)))/r-log(1-delta)
    xhi = min(x_cmax,x_tmax,x_qmax,x_outmax)
    datos={'dominio_motor':None,'A':None,'B':None,
           'limites_calculables':(exp(xlo),exp(xhi)) if xhi>xlo else None,
           'tipo':'sin_motor'}
    if xhi<=xlo+2*tolerancia:
        return datos
    def evaluar(x):
        return resolver_ciclo(T1,T3,exp(x),p1,eta_c,eta_t,delta,
                             tolerancia=min(tolerancia,1e-10))
    # Trabajo neto es estrictamente cóncavo en x=ln(rp): el incremento de
    # trabajo de turbina disminuye y el de compresor aumenta con x.
    # Por ello un máximo de w > 0 garantiza una sola región motora.
    def trabajo(x): return evaluar(x)['trabajo_neto']
    def rendimiento(x):
        p=evaluar(x)
        return p['trabajo_neto']/p['calor_aportado'] if p['calor_aportado']>0 else float('-inf')
    # Evitar extremos térmicos flotantes: interior siempre admisible.
    margen=min(1e-7,max(1e-12,(xhi-xlo)*1e-7))
    a,b=xlo+margen,xhi-margen
    if a>=b: return datos
    # w'(x) = R[eta_t*T4s - T2s/eta_c], decreciente estricta.
    # No atribuir un máximo interior cuando el óptimo libre queda fuera.
    def derivada_trabajo(x):
        punto=evaluar(x)
        return r*(eta_t*punto['T4s']-punto['T2s']/eta_c)
    da,db=derivada_trabajo(a),derivada_trabajo(b)
    if da > 0 and db < 0:
        xA=_raiz_monotona(derivada_trabajo,a,b,tol=tolerancia)
        a_interior=True
    elif db >= 0:
        xA=b
        a_interior=False
    else:
        xA=a
        a_interior=False
    if trabajo(xA)<=0: return datos
    # Buscar las dos raíces de trabajo, si existen; la frontera de expansión
    # y la térmica pueden cortar el dominio antes de un cruce de w=0.
    izq = _raiz_monotona(trabajo,a,xA,tol=tolerancia) if trabajo(a)<0 else xlo
    der = _raiz_monotona(trabajo,xA,b,tol=tolerancia) if trabajo(b)<0 else xhi
    if izq>=der: return datos
    datos['dominio_motor']=(exp(izq),exp(der))
    datos['tipo']='motor'
    pa=evaluar(xA)
    if a_interior:
        datos['A']={'rp':exp(xA),'trabajo_neto':pa['trabajo_neto'],
                    'rendimiento':pa['rendimiento'],'tipo':'maximo_interior',
                    'punto':pa}
    else:
        # Los límites del dominio motor están excluidos: sólo supremo.
        extremo=der if db >= 0 else izq
        datos['A']={'rp':None,'trabajo_neto':None,'rendimiento':None,
                    'tipo':'supremo_frontera','limite_rp':exp(extremo),
                    'limite_trabajo_neto':trabajo(xA)}
    # Demostración de unicidad de B: d(eta)/dx tiene el signo de
    # F=b*q_in-a*q_out, con a=R*T2s/eta_c creciente,
    # b=R*eta_t*T4s decreciente. En el dominio con q_in,q_out>0,
    # F'=b'*q_in-a'*q_out<0. Por tanto sólo puede haber un máximo
    # estacionario, y la búsqueda no depende de la malla.
    def numerador_derivada(x):
        p=evaluar(x)
        ca=r*p['T2s']/eta_c
        tb=r*eta_t*p['T4s']
        return tb*p['calor_aportado']-ca*p['calor_rechazado']
    margenB=min(1e-7,(der-izq)*1e-7)
    u,v=izq+margenB,der-margenB
    if u>=v: return datos
    fu,fv=numerador_derivada(u),numerador_derivada(v)
    if fu>0 and fv<0:
        xB=_raiz_monotona(numerador_derivada,u,v,tol=tolerancia)
        pb=evaluar(xB)
        datos['B']={'rp':exp(xB),'trabajo_neto':pb['trabajo_neto'],
                    'rendimiento':pb['rendimiento'],'tipo':'maximo_interior',
                    'punto':pb}
    else:
        # La frontera queda excluida del conjunto motor.
        xl = der if fv>=0 else izq
        cercano = v if fv>=0 else u
        datos['B']={'rp':None,'trabajo_neto':None,'rendimiento':None,
                    'tipo':'supremo_frontera','limite_rp':exp(xl),
                    'limite_rendimiento':rendimiento(cercano)}
    return datos
