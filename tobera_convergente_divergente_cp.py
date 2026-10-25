"""Tobera C-D ideal cuasi-1D con aire cp(T), independiente del motor.

K, kPa, J/(kg K), kJ/kg y m/s. Las ramas con choques no se resuelven.
La estimación de choque normal a la salida es solo un *indicador* basado
en gamma local constante; nunca se emplea para calcular empuje.
"""

from math import exp, isfinite, log, sqrt
from numbers import Real

from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo
from propiedades_aire import R_AIRE, T_MAX, T_MIN, gamma, h, s, s0


_R_KJ = R_AIRE / 1000.0
_TOL_K = 1e-9


def _biseccion(funcion, inferior, superior, *, iteraciones=110):
    """Raíz acotada de función continua con signos opuestos; devuelve float."""
    fi, fs = funcion(inferior), funcion(superior)
    if fi == 0:
        return inferior
    if fs == 0:
        return superior
    if fi * fs > 0:
        raise ErrorNumericoCiclo("La raíz no está encerrada en el intervalo físico.")
    for _ in range(iteraciones):
        medio = (inferior + superior) / 2
        fm = funcion(medio)
        if fm == 0 or superior - inferior < _TOL_K:
            return medio
        if fi * fm > 0:
            inferior, fi = medio, fm
        else:
            superior = medio
    raise ErrorNumericoCiclo("La raíz no converge en el intervalo físico.")


def _estado(T, Tt, pt):
    """Estado estático isentrópico para T [K], Tt [K], pt [kPa]."""
    v = sqrt(max(0.0, 2000 * (h(Tt) - h(T))))
    p = pt * exp((s0(T) - s0(Tt)) / _R_KJ)
    rho = 1000 * p / (R_AIRE * T)
    a = sqrt(gamma(T) * R_AIRE * T)
    return dict(T=T, p=p, V=v, a=a, M=v/a, rho=rho, G=rho*v)


def _sonico(Tt, pt):
    """Estado M=1 o None si la correlación termina antes de alcanzarlo."""
    if _estado(T_MIN, Tt, pt)['M'] < 1:
        return None
    tg = _biseccion(lambda T: _estado(T, Tt, pt)['M']-1, T_MIN, Tt)
    return _estado(tg, Tt, pt)


def _temperatura_para_presion(Tt, pt, p):
    """Inversión de s0(T) a presión prescrita dentro de 200–2000 K."""
    objetivo = s0(Tt) + _R_KJ * (log(p)-log(pt))
    if objetivo < s0(T_MIN)-1e-12:
        raise EstadoFueraDeRango("La expansión requiere T<200 K.")
    if objetivo > s0(T_MAX)+1e-12:
        raise EstadoFueraDeRango("La inversión requiere T>2000 K.")
    return _biseccion(lambda T: s0(T)-objetivo, T_MIN, Tt)


def _salida_area(Tt, pt, critico, epsilon, *, supersonica):
    """Raíz de G_e=G*/epsilon en el tramo de Mach solicitado."""
    limite = T_MIN if supersonica else Tt
    objetivo = critico['G']/epsilon
    if supersonica:
        if _estado(limite, Tt, pt)['G'] > objetivo:
            raise EstadoFueraDeRango(
                "La rama supersónica supera el dominio inferior de 200 K.")
        return _estado(_biseccion(
            lambda T: _estado(T, Tt, pt)['G']-objetivo,
            limite, critico['T']), Tt, pt)
    return _estado(_biseccion(
        lambda T: _estado(T, Tt, pt)['G']-objetivo,
        critico['T'], limite), Tt, pt)


def _validar(Tt, pt, p_amb, epsilon):
    for x in (Tt, pt, p_amb, epsilon):
        if isinstance(x, bool) or not isinstance(x, Real):
            raise ValueError("Se requieren cuatro parámetros reales finitos (sin bool).")
        try:
            finito = isfinite(x)
        except (OverflowError, TypeError, ValueError):
            raise ValueError("Se requieren cuatro parámetros reales finitos (sin bool).") from None
        if not finito:
            raise ValueError("Se requieren cuatro parámetros reales finitos (sin bool).")
    if not T_MIN < Tt <= T_MAX or not pt > p_amb > 0 or epsilon < 1:
        raise ValueError("Se exige 200<Tt<=2000 K, pt>p_amb>0 kPa y Ae/Ag>=1.")


def _resultado(Tt, pt, p_amb, epsilon, critico, garganta, salida,
               regimen, *, motivo=None, umbral_choque=None):
    """Contrato homogéneo: None para salidas y empujes físicamente no resueltos."""
    disponible = salida is not None and garganta is not None
    diferencia = salida['p']-p_amb if disponible else None
    tolerancia = 1e-6 * max(pt, p_amb)
    adaptacion = ("adaptada" if abs(diferencia) <= tolerancia else
                  "subexpandida" if diferencia > 0 else "sobreexpandida") if disponible else None
    ae_mdot = 1/(salida['G']) if disponible else None
    fp = 1000*diferencia*ae_mdot if disponible else None
    ht = h(Tt)
    return {
        'regimen': regimen, 'resuelto': disponible, 'diagnostico': motivo,
        'relacion_areas': epsilon, 'temperatura_remanso': Tt,
        'presion_remanso': pt, 'presion_ambiente': p_amb,
        'presion_critica': critico['p'] if critico else None,
        'temperatura_critica': critico['T'] if critico else None,
        'flujo_masico_critico_por_area': critico['G'] if critico else None,
        'temperatura_garganta': garganta['T'] if garganta else None,
        'presion_garganta': garganta['p'] if garganta else None,
        'densidad_garganta': garganta['rho'] if garganta else None,
        'velocidad_garganta': garganta['V'] if garganta else None,
        'mach_garganta': garganta['M'] if garganta else None,
        'temperatura_salida': salida['T'] if disponible else None,
        'presion_salida': salida['p'] if disponible else None,
        'densidad_salida': salida['rho'] if disponible else None,
        'velocidad_salida': salida['V'] if disponible else None,
        'velocidad_sonido_salida': salida['a'] if disponible else None,
        'mach_salida': salida['M'] if disponible else None,
        'flujo_masico_por_area_garganta': garganta['G'] if disponible else None,
        'flujo_masico_por_area_salida': salida['G'] if disponible else None,
        'area_salida_por_caudal': ae_mdot,
        'diferencia_presiones': diferencia, 'adaptacion': adaptacion,
        'empuje_especifico_momento': salida['V'] if disponible else None,
        'empuje_especifico_presion': fp,
        'empuje_especifico_total': salida['V']+fp if disponible else None,
        'residuo_masa': garganta['G']-epsilon*salida['G'] if disponible else None,
        'residuo_energia_garganta': ht-h(garganta['T'])-garganta['V']**2/2000 if disponible else None,
        'residuo_energia_salida': ht-h(salida['T'])-salida['V']**2/2000 if disponible else None,
        'residuo_entropia_garganta': s(garganta['T'],garganta['p'])-s(Tt,pt) if disponible else None,
        'residuo_entropia_salida': s(salida['T'],salida['p'])-s(Tt,pt) if disponible else None,
        'umbral_choque_salida_aproximado': umbral_choque,
    }


def resolver_tobera_convergente_divergente(Tt, pt, p_amb, epsilon):
    """Resuelve sólo ramas físicas isentrópicas C-D (K, kPa, kPa, Ae/Ag).

    Retorna dict con estados, áreas, residuos y empuje específico [N/(kg/s)].
    Las contrapresiones que pueden requerir choques producen resuelto=False,
    sin salida/empuje; el criterio de choque a la salida es aproximado.
    """
    _validar(Tt, pt, p_amb, epsilon)
    Tt, pt, p_amb, epsilon = map(float,(Tt,pt,p_amb,epsilon))
    critico = _sonico(Tt,pt)
    salida_amb = _estado(_temperatura_para_presion(Tt,pt,p_amb),Tt,pt)
    if critico is None:
        if salida_amb['M'] >= 1:
            raise EstadoFueraDeRango("No se alcanza el estado sónico en el dominio.")
        objetivo = epsilon*salida_amb['G']
        if objetivo > _estado(T_MIN,Tt,pt)['G']:
            raise EstadoFueraDeRango("La garganta excede el dominio 200 K.")
        garganta = _estado(_biseccion(lambda T:_estado(T,Tt,pt)['G']-objetivo,
                                      T_MIN,Tt),Tt,pt)
        return _resultado(Tt,pt,p_amb,epsilon,critico,garganta,salida_amb,
                          'subsonico_no_bloqueado')

    salida_sub = _salida_area(Tt,pt,critico,epsilon,supersonica=False)
    p_inicio_bloqueo = salida_sub['p']
    tol_p = 1e-9*pt
    if p_amb >= p_inicio_bloqueo-tol_p:
        # A p_inicio_bloqueo la garganta es sónica, pero la salida sigue subsónica.
        if abs(p_amb-p_inicio_bloqueo) <= tol_p:
            return _resultado(Tt,pt,p_amb,epsilon,critico,critico,salida_sub,
                              'bloqueado_salida_subsonica_limite')
        if salida_amb['M'] >= 1:
            raise ErrorNumericoCiclo("Incoherencia en la rama no bloqueada.")
        flujo_g = epsilon*salida_amb['G']
        garganta = _estado(_biseccion(
            lambda T:_estado(T,Tt,pt)['G']-flujo_g,critico['T'],Tt),Tt,pt)
        return _resultado(Tt,pt,p_amb,epsilon,critico,garganta,salida_amb,
                          'subsonico_no_bloqueado')

    # En una C-D bloqueada la raíz supersónica es matemática; su validez
    # exige excluir choques dentro del divergente. Para ello se utiliza una
    # cota indicativa (gamma_e local) y se rehúsa inferir el estado ambiguo.
    salida_sup = _salida_area(Tt,pt,critico,epsilon,supersonica=True)
    g = gamma(salida_sup['T'])
    p_choque_aprox = salida_sup['p']*(1+2*g/(g+1)*(salida_sup['M']**2-1))
    if p_amb >= p_choque_aprox*(1-1e-6):
        return _resultado(Tt,pt,p_amb,epsilon,critico,critico,None,
                          'choque_interno_o_salida_no_resuelto',
                          motivo='Contrapresión compatible con choque interno/salida; '
                          'sin solucionador de choques no se predice la salida.',
                          umbral_choque=p_choque_aprox)
    if p_amb > salida_sup['p']*(1+1e-6):
        # En la zona sobreexpandida el flujo interior puede mantenerse
        # supersónico y ajustar presión fuera, pero separación no está modelada.
        regimen = 'supersonico_sobreexpandido_ideal'
        motivo = ('Rama supersónica ideal; la estimación con gamma local sitúa '
                  'el choque fuera. No predice separación ni choques externos.')
    else:
        regimen = 'supersonico_ideal'
        motivo = None
    return _resultado(Tt,pt,p_amb,epsilon,critico,critico,salida_sup,
                      regimen,motivo=motivo,umbral_choque=p_choque_aprox)


def relacion_areas_adaptada(Tt, pt, p_amb):
    """Ae/Ag [-] para salida supersónica ideal adaptada a p_amb [kPa].

    Devuelve float>1; ValueError para salida no supersónica y
    EstadoFueraDeRango para temperaturas fuera del aire modelado.
    """
    _validar(Tt,pt,p_amb,1.0)
    critico = _sonico(float(Tt),float(pt))
    if critico is None:
        raise ValueError("Sin garganta sónica dentro del dominio del aire.")
    salida = _estado(_temperatura_para_presion(float(Tt),float(pt),float(p_amb)),
                     float(Tt),float(pt))
    if salida['M'] <= 1+1e-8:
        raise ValueError("La contrapresión no permite adaptación supersónica.")
    epsilon = critico['G']/salida['G']
    if not isfinite(epsilon) or epsilon <= 1:
        raise ErrorNumericoCiclo("Relación de áreas adaptada inconsistente.")
    return epsilon
