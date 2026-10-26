"""Choque normal estacionario en aire ideal con cp(T) variable.

Estados estáticos en K, kPa y m/s; conservación exacta de flujo cuasi-1D.
No presupone gamma constante ni modela separación de capa límite.
"""

from math import exp, isfinite, log, sqrt

from ciclo_cp_variable import EstadoFueraDeRango, ErrorNumericoCiclo
from propiedades_aire import R_AIRE, T_MAX, T_MIN, gamma, h, s, s0


def resolver_choque_normal(T1, p1, V1, *, tolerancia=1e-9):
    """Resuelve el estado 2 para M1>1; retorna estados, pérdidas y residuos.

    T1 [K], p1 [kPa], V1 [m/s], tolerancia relativa [-]. ValueError para
    estado no físico, EstadoFueraDeRango para 200–2000 K insuficientes y
    ErrorNumericoCiclo para raíz o residuos no convergentes.
    """
    from numbers import Real
    for valor in (T1, p1, V1, tolerancia):
        if isinstance(valor, bool) or not isinstance(valor, Real):
            raise ValueError('El choque requiere parámetros reales finitos.')
        try:
            if not isfinite(valor):
                raise ValueError('El choque requiere parámetros reales finitos.')
        except OverflowError:
            raise ValueError('El choque requiere parámetros reales finitos.') from None
    T1, p1, V1 = float(T1), float(p1), float(V1)
    if not T_MIN <= T1 <= T_MAX or p1 <= 0 or V1 <= 0 or not 0 < tolerancia < 1e-3:
        raise ValueError('Estado de choque fuera del dominio físico.')
    a1 = sqrt(gamma(T1)*R_AIRE*T1)
    if V1 <= a1*(1+1e-8):
        raise ValueError('Un choque normal exige Mach anterior mayor que uno.')
    H = h(T1) + V1*V1/2000
    if H >= h(T_MAX):
        raise EstadoFueraDeRango('El remanso del choque supera 2000 K.')
    rho1 = 1000*p1/(R_AIRE*T1)
    j = rho1*V1
    # p2(T)=p1+j*(V1-V2(T))/1000 por cantidad de movimiento.
    # La ecuación residual impone además rho2*V2=j (gas ideal).
    def estado_residual(T):
        V2 = sqrt(max(0., 2000*(H-h(T))))
        p2 = p1 + j*(V1-V2)/1000
        return 1000*p2*V2/(R_AIRE*T)-j

    from propiedades_aire import T_desde_h
    Tt = T_desde_h(H)
    # M2=1 está entre la rama trivial supersónica y la rama subsónica.
    def mach_isentropico(T):
        return sqrt(max(0., 2000*(H-h(T))))/sqrt(gamma(T)*R_AIRE*T)
    lo, hi = T1, Tt
    for _ in range(90):
        mid = (lo+hi)/2
        if mach_isentropico(mid) > 1:
            lo = mid
        else:
            hi = mid
    Tstar = (lo+hi)/2
    f_lo = estado_residual(Tstar)
    f_hi = estado_residual(Tt)
    if f_lo <= 0 or f_hi >= 0:
        raise ErrorNumericoCiclo('No hay rama subsónica de choque encerrada.')
    lo, hi = Tstar, Tt
    for _ in range(115):
        mid = (lo+hi)/2
        fm = estado_residual(mid)
        if fm > 0:
            lo = mid
        else:
            hi = mid
        if (hi-lo) < max(1e-10, tolerancia*T1*1e-3):
            break
    T2 = (lo+hi)/2
    V2 = sqrt(2000*(H-h(T2)))
    p2 = p1+j*(V1-V2)/1000
    rho2 = 1000*p2/(R_AIRE*T2)
    M2 = V2/sqrt(gamma(T2)*R_AIRE*T2)
    ds = s(T2,p2)-s(T1,p1)
    log_pt1 = log(p1)+(s0(Tt)-s0(T1))/(R_AIRE/1000)
    log_pt2 = log(p2)+(s0(Tt)-s0(T2))/(R_AIRE/1000)
    pt1, pt2 = exp(log_pt1), exp(log_pt2)
    residuos = dict(
        masa=rho2*V2-j,
        momento=p2+rho2*V2*V2/1000-p1-rho1*V1*V1/1000,
        energia=h(T2)+V2*V2/2000-H,
    )
    if not (T2>T1 and M2<1 and ds>0 and pt2<pt1):
        raise ErrorNumericoCiclo('El choque calculado incumple la segunda ley.')
    if (abs(residuos['masa'])>max(1e-7, tolerancia*j*20)
            or abs(residuos['momento'])>max(1e-7, tolerancia*p2*20)
            or abs(residuos['energia'])>1e-7):
        raise ErrorNumericoCiclo('Los residuos del choque exceden la tolerancia.')
    return dict(T1=T1, p1=p1, V1=V1, M1=V1/a1, rho1=rho1,
                T2=T2, p2=p2, V2=V2, M2=M2, rho2=rho2,
                Tt=Tt, pt1=pt1, pt2=pt2, perdida_presion_total=pt1-pt2,
                generacion_entropia=ds, flujo_masico_por_area=j,
                residuos=residuos)
