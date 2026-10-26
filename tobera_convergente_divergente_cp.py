"""Tobera C-D cuasi-1D con cp(T): ramas isentrópicas y choque normal interno.

K, kPa, J/(kg K), kJ/kg y m/s. Se omiten fricción y separación.
"""

from math import exp, isfinite, log, sqrt
from numbers import Real

from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo
from choque_normal_cp import resolver_choque_normal
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
               regimen, *, motivo=None, umbral_choque=None, choque=None):
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
        # Referencia isentrópica de cada tramo: tras choque, pt2 (no pt1).
        'residuo_entropia_salida': (s(salida['T'],salida['p'])-s(Tt,choque['pt2'])
                                    if choque else s(salida['T'],salida['p'])-s(Tt,pt))
                                   if disponible else None,
        'umbral_choque_salida_aproximado': umbral_choque,
        'choque_normal': choque,
        'relacion_areas_choque': choque['relacion_areas_choque'] if choque else None,
    }


def _salida_tras_choque(Tt, pt, critico, epsilon, area_choque):
    """Resuelve choque a A/Ag fija y salida subsónica cuasi-1D posterior."""
    antes = _salida_area(Tt, pt, critico, area_choque, supersonica=True)
    choque = resolver_choque_normal(antes['T'], antes['p'], antes['V'])
    pt2 = choque['pt2']
    objetivo = critico['G']/epsilon
    # El estado sónico T* depende de Tt, no de pt2; el flujo sí depende de pt2.
    if _estado(critico['T'], Tt, pt2)['G'] < objetivo*(1-1e-9):
        raise ErrorNumericoCiclo('El flujo posterior excede la capacidad subsónica.')
    Te = _biseccion(lambda T: _estado(T,Tt,pt2)['G']-objetivo,
                    critico['T'], Tt)
    salida = _estado(Te,Tt,pt2)
    choque['relacion_areas_choque'] = area_choque
    choque['residuo_masa_geometrica'] = (area_choque*choque['flujo_masico_por_area']
                                       -critico['G'])
    return salida, choque


def _choque_en_divergente(Tt, pt, p_amb, epsilon, critico):
    """Busca el área de choque que reproduce la contrapresión de salida."""
    salida_limite = _salida_area(Tt,pt,critico,epsilon,supersonica=False)
    # A/Ag=1 es choque degenerado (sin salto); el límite superior es salida.
    presion_max = salida_limite['p']
    salida_choque_e, _ = _salida_tras_choque(Tt,pt,critico,epsilon,epsilon)
    presion_min = salida_choque_e['p']
    anchura = presion_max-presion_min
    # Una tolerancia absoluta fija puede consumir toda la rama si Ae/Ag≈1.
    margen = max(1e-10*pt, min(1e-8*pt, 1e-3*anchura))
    if p_amb > presion_max + margen or p_amb < presion_min - margen:
        raise ValueError('La contrapresión no pertenece a la rama de choque interno.')
    if abs(p_amb-presion_min) <= margen:
        return _salida_tras_choque(Tt,pt,critico,epsilon,epsilon)
    # Cerca de la garganta el choque se debilita, y la evaluación exacta a
    # A/Ag=1 no admite M1>1. Se usa el límite analítico de rama subsónica.
    lo, hi = 1., epsilon
    for _ in range(85):
        medio = (lo+hi)/2
        salida, choque = _salida_tras_choque(Tt,pt,critico,epsilon,medio)
        if salida['p'] > p_amb:
            lo = medio
        else:
            hi = medio
        if abs(salida['p']-p_amb) <= max(1e-10*pt, min(1e-9*pt, 1e-4*anchura)):
            return salida, choque
    raise ErrorNumericoCiclo('La posición del choque no converge.')


def resolver_tobera_convergente_divergente(Tt, pt, p_amb, epsilon):
    """Resuelve ramas isentrópicas y choque normal cuasi-1D (K, kPa, kPa, Ae/Ag).

    Retorna dict con estados, áreas, residuos y empuje específico [N/(kg/s)].
    Puede devolver estado no resuelto cuando faltan datos físicos o dominio.
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
    # Frontera sónico/subsónico: limitar incertidumbre por anchura de rama.
    tol_p = max(1e-10*pt, min(1e-9*pt, 1e-3*(pt-p_inicio_bloqueo)))
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

    # La frontera choque-en-salida se obtiene resolviendo las conservaciones
    # con cp(T), no congelando gamma a la temperatura de salida.
    salida_sup = _salida_area(Tt,pt,critico,epsilon,supersonica=True)
    if epsilon > 1:
        choque_salida = resolver_choque_normal(salida_sup['T'],salida_sup['p'],salida_sup['V'])
        p_choque = choque_salida['p2']
        anchura_choque = max(0., p_inicio_bloqueo-p_choque)
        tol_choque = max(1e-10*pt, min(1e-8*pt, 1e-3*anchura_choque))
        if p_amb >= p_choque-tol_choque:
            try:
                salida, choque = _choque_en_divergente(Tt,pt,p_amb,epsilon,critico)
                regimen = ('choque_normal_salida' if abs(choque['relacion_areas_choque']-epsilon)
                           <= min(1e-8*epsilon, 1e-3*(epsilon-1)) else 'choque_normal_interno')
                return _resultado(Tt,pt,p_amb,epsilon,critico,critico,salida,
                                  regimen,choque=choque,umbral_choque=p_choque)
            except (EstadoFueraDeRango,ErrorNumericoCiclo,ValueError) as exc:
                return _resultado(Tt,pt,p_amb,epsilon,critico,critico,None,
                                  'choque_interno_o_salida_no_resuelto',
                                  motivo=str(exc),umbral_choque=p_choque)
    else:
        p_choque = salida_sup['p']
    if p_amb > salida_sup['p']*(1+1e-6):
        # En la zona sobreexpandida el flujo interior puede mantenerse
        # supersónico y ajustar presión fuera, pero separación no está modelada.
        regimen = 'supersonico_sobreexpandido_ideal'
        motivo = ('Rama supersónica ideal; el choque normal de salida sitúa '
                  'el choque fuera. No predice separación ni choques externos.')
    else:
        regimen = 'supersonico_ideal'
        motivo = None
    return _resultado(Tt,pt,p_amb,epsilon,critico,critico,salida_sup,
                      regimen,motivo=motivo,umbral_choque=p_choque)


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
