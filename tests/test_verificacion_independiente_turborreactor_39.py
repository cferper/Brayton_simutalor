"""Verificación M39: referencia analítica ajena a ecuaciones de producción.

Gas caloríficamente perfecto con h=cp*(T-298.15), s=cp ln(T/Tref)-R ln(p/pref).
No importa solucionadores de producción dentro del modelo de referencia.
"""

import importlib.util
from math import exp, isfinite, log, sqrt
from copy import deepcopy
import unittest
from unittest.mock import patch

from acoplamiento_turbomaquinaria_cp import resolver_acoplamiento
from combustible_cp_variable import resolver_turborreactor_con_combustible
from mapas_prestaciones_turborreactor_cp import barrer_rp_t3, frente_pareto
from propiedades_aire import R_AIRE, cp, gamma, h, s, s0
from tobera_cp_variable import resolver_tobera_convergente
from vuelo_cp_variable import calcular_remanso, resolver_turborreactor_vuelo


TREF = 298.15  # K, coincide por convención con las entalpías sensibles.
R = R_AIRE  # J/(kg K); mantener la constante de gas para aislar cp(T).
CP = 1.08  # kJ/(kg K), referencia deliberadamente caloríficamente perfecta.
GAMMA = CP/(CP-R/1000)
BASE = dict(rp=10, eta_c=.85, T3=1600, delta=.04, eta_t=.9,
            eta_m=.98, eta_n=.95, eta_b=.99, PCI=43000)


def referencia_perfecta(*, mach, rp, eta_c, T3, delta, eta_t, eta_m,
                       eta_n, eta_b, PCI, pi_d, T_amb, p_amb):
    """Solución analítica independiente, constantes CP/GAMMA/R coherentes.

    No llama a h/s, inversores ni a ecuaciones de los módulos de producción.
    Se emplea solo como comparación de modelo, NO como gas de combustión real.
    """
    a0 = sqrt(GAMMA*R*T_amb)
    vinf = mach*a0
    t0t = T_amb + vinf**2/(2000*CP)
    p0t = p_amb*(t0t/T_amb)**(GAMMA/(GAMMA-1))
    p1 = pi_d*p0t
    t1 = t0t
    t2s = t1*rp**((GAMMA-1)/GAMMA)
    t2 = t1+(t2s-t1)/eta_c
    p2, p3 = p1*rp, p1*rp*(1-delta)
    h1, h2, h3 = (CP*(t-TREF) for t in (t1,t2,T3))
    wc = h2-h1
    f = (h3-h2)/(eta_b*PCI-h3)
    wt = wc/(eta_m*(1+f))
    t4 = T3-wt/CP
    t4s = T3-wt/(eta_t*CP)
    p4 = p3*(t4s/T3)**(GAMMA/(GAMMA-1))
    if not (0 < p4 < p3 and p4 > p_amb and t4s > 0):
        raise ValueError("Sin expansión disponible en esta referencia.")
    # Condición crítica Mach=1 en la salida real; el estado isentrópico
    # correspondiente depende de eta_n, y por tanto también p_crit.
    tcrit_real = t4/(1+GAMMA*R/(2000*CP))
    tcrit_s = t4-(t4-tcrit_real)/eta_n
    pcrit = p4*(tcrit_s/t4)**(GAMMA/(GAMMA-1))
    if p_amb <= pcrit:
        pe, tes, regimen = pcrit, tcrit_s, "bloqueado"
    else:
        pe = p_amb
        tes = t4*(pe/p4)**((GAMMA-1)/GAMMA)
        regimen = "no_bloqueado"
    te = t4-eta_n*(t4-tes)
    ve = sqrt(2000*CP*(t4-te))
    me = ve/sqrt(GAMMA*R*te)
    rho = pe*1000/(R*te)
    presion = (1+f)*1000*(pe-p_amb)/(rho*ve)
    bruto = (1+f)*ve+presion
    fs = bruto-vinf
    return {"Tt0":t0t,"pt0":p0t,"p1":p1,"T2":t2,"p2":p2,
            "wc":wc,"f":f,"T4":t4,"T4s":t4s,"p4":p4,
            "pcrit":pcrit,"Te":te,"pe":pe,"Ve":ve,"Me":me,
            "rho":rho,"regimen":regimen,"bruto":bruto,"Fs":fs,
            "TSFC":3600*f/fs if fs>0 else None}


def comparar(valor_cp, referencia):
    """Par (error absoluto, error relativo); valores finitos comparables."""
    if not all(isfinite(x) for x in (valor_cp, referencia)):
        raise ValueError("Comparación no finita.")
    error = abs(valor_cp-referencia)
    return error, error/max(abs(referencia), 1e-15)


class IndependienteTurborreactor39(unittest.TestCase):
    def test_referencia_analitica_estatica_y_vuelo(self):
        for mach, pi_d in ((0,1),(.7,.97)):
            with self.subTest(mach=mach):
                ref = referencia_perfecta(**BASE, mach=mach, pi_d=pi_d,
                                          T_amb=288.15,p_amb=100)
                prod = resolver_turborreactor_con_combustible(**BASE,
                    mach=mach,pi_d=pi_d,T_amb=288.15,p_amb=100)
                self.assertEqual(prod["tobera"]["regimen"],ref["regimen"])
                for valor, clave in ((prod["combustor"]["f"],"f"),
                                     (prod["compresor"]["T2"],"T2"),
                                     (prod["turbina"]["p4"],"p4"),
                                     (prod["tobera"]["velocidad_salida"],"Ve"),
                                     (prod["prestaciones"]["empuje_especifico_neto"],"Fs"),
                                     (prod["prestaciones"]["TSFC_kg_N_h"],"TSFC")):
                    self.assertLess(comparar(valor,ref[clave])[1],.15,
                                    f"{clave}, Mach {mach}")

    def test_balance_camara_y_eje_por_algebra_separada(self):
        o=resolver_turborreactor_con_combustible(**BASE, mach=.7,
            pi_d=.97,T_amb=288.15,p_amb=100)
        c,b,t=o["compresor"],o["combustor"],o["turbina"]
        self.assertAlmostEqual(c["h2"]+b["f"]*b["eta_b"]*b["PCI"],
                               (1+b["f"])*b["h3"],places=8)
        self.assertAlmostEqual(b["factor_masico"]*t["trabajo_turbina_por_kg_gas"]*.98,
                               c["trabajo_compresor"],places=8)
        self.assertAlmostEqual(s(t["T4s"],t["p4"]),s(b["T3"],b["p3"]),places=8)

    def test_remanso_difusor_analitico_limite_bajo_mach(self):
        t,p,m=288.15,100,.3
        r=calcular_remanso(t,p,m)
        tref=t*(1+(.4/2)*m*m)
        pref=p*(tref/t)**(1.4/.4)
        self.assertLess(comparar(r["temperatura_remanso"],tref)[1],.01)
        self.assertLess(comparar(r["presion_remanso"],pref)[1],.01)
        self.assertAlmostEqual(r["residuo_energia"],0,places=9)
        self.assertAlmostEqual(r["residuo_entropia"],0,places=9)

    def test_no_combustible_y_caso_estatico(self):
        args=(288.15,100,10,.85,1600,.04,.9,.98)
        nucleo=resolver_acoplamiento(*args)
        estatico=resolver_turborreactor_vuelo(0,10,.85,1600,.04,.9,.98,
            eta_n=.95,pi_d=1,T_amb=288.15,p_amb=100)
        self.assertEqual(estatico["nucleo"]["presiones"],nucleo["presiones"])
        extremo=resolver_turborreactor_con_combustible(**dict(BASE,PCI=1e12),
            mach=0,pi_d=1,T_amb=288.15,p_amb=100)
        self.assertLess(extremo["combustor"]["f"],1e-8)
        self.assertAlmostEqual(extremo["prestaciones"]["empuje_especifico_neto"],
            estatico["empuje_especifico_neto"],places=4)

    def test_tobera_critica_continua(self):
        pt,Tt,eta=400,1100,.95
        caso=resolver_tobera_convergente(Tt,pt,100,eta)
        crit=caso["presion_critica"]
        izq=resolver_tobera_convergente(Tt,pt,crit*(1-1e-6),eta)
        der=resolver_tobera_convergente(Tt,pt,crit*(1+1e-6),eta)
        self.assertEqual(izq["regimen"],"bloqueado")
        self.assertEqual(der["regimen"],"no_bloqueado")
        self.assertAlmostEqual(izq["mach_salida"],1,places=6)
        self.assertLess(abs(der["mach_salida"]-1),1e-4)
        self.assertLess(abs(izq["velocidad_salida"]-der["velocidad_salida"]),.05)

    def test_eficiencias_ideales(self):
        o=resolver_turborreactor_con_combustible(**dict(BASE,eta_c=1,eta_t=1,
            eta_m=1,eta_n=1),mach=0,pi_d=1,T_amb=288.15,p_amb=100)
        self.assertAlmostEqual(o["compresor"]["T2"],o["compresor"]["T2s"],places=8)
        self.assertAlmostEqual(o["turbina"]["T4"],o["turbina"]["T4s"],places=8)
        self.assertAlmostEqual(o["tobera"]["mach_salida"],1,places=7)
        self.assertAlmostEqual(o["turbina"]["residuo_eje"],0,places=7)

    def test_presion_y_tsfc_unidades_independientes(self):
        o=resolver_turborreactor_con_combustible(**BASE, mach=.7,pi_d=.97,
            T_amb=288.15,p_amb=100)
        e=o["tobera"];f=o["combustor"]["f"]
        de=(1+f)*1000*(e["presion_salida"]-100)/(
            e["densidad_salida"]*e["velocidad_salida"])
        fs=(1+f)*e["velocidad_salida"]-o["remanso"]["velocidad_vuelo"]+de
        self.assertAlmostEqual(fs,o["prestaciones"]["empuje_especifico_neto"])
        self.assertAlmostEqual(3600*f/fs,o["prestaciones"]["TSFC_kg_N_h"])

    def test_pareto_sintetico_y_malla(self):
        vals=[(100,2),(110,3),(120,4),(110,2),(90,5)]
        puntos=[dict(estado="valido", Fs=a, TSFC_kg_N_h=b, i=i)
                for i,(a,b) in enumerate(vals)]
        self.assertEqual([p["i"] for p in frente_pareto(puntos)],[2,3])
        m=barrer_rp_t3([5,10,15],[1400,1600])
        elegibles=[p for fila in m["puntos"] for p in fila if p["estado"]=="valido"]
        self.assertEqual(m["maximo_Fs"]["valor"],max(p["Fs"] for p in elegibles))
        self.assertEqual(m["minimo_TSFC"]["valor"],min(p["TSFC_kg_N_h"] for p in elegibles))

    def test_flags_restricciones_cambian_filtro_sin_falsear_fisica(self):
        real=resolver_turborreactor_con_combustible(**BASE,mach=0,pi_d=1,
            T_amb=288.15,p_amb=100)
        negativo=deepcopy(real)
        negativo["prestaciones"]["empuje_especifico_neto"]=-1
        negativo["prestaciones"]["TSFC_kg_N_h"]=None
        sin_tobera=deepcopy(real)
        sin_tobera["tobera"]=None
        for salida,estado,restricciones in (
            (negativo,"empuje_no_positivo",{"exigir_empuje_positivo":False}),
            (sin_tobera,"sin_expansion",{"exigir_empuje_positivo":False,
                                           "exigir_margen_tobera":False})):
            with self.subTest(estado=estado):
                with patch('mapas_prestaciones_turborreactor_cp.resolver_turborreactor_con_combustible',
                           return_value=salida):
                    estricto=barrer_rp_t3([10],[1600])
                    relajado=barrer_rp_t3([10],[1600],restricciones=restricciones)
                p0,p1=estricto["puntos"][0][0],relajado["puntos"][0][0]
                self.assertEqual(p0["estado"],estado)
                self.assertEqual(p1["estado"],estado)
                self.assertFalse(p0["cumple_restricciones"])
                self.assertTrue(p1["cumple_restricciones"])
                self.assertEqual(estricto["cumplen_restricciones"],0)
                self.assertEqual(relajado["cumplen_restricciones"],1)
                self.assertEqual(relajado["validos"],0)  # no optimizar TSFC indefinido
                self.assertIsNone(relajado["minimo_TSFC"])

    def test_restricciones_con_casos_fisicos_sin_empuje_y_sin_expansion(self):
        opciones=dict(mach=.9,rp=3,eta_c=.85,delta=.04,eta_t=.9,eta_m=.98,
                     eta_n=.95,pi_d=.7,eta_b=.99,PCI=43000,T_amb=288.15,p_amb=100)
        a=barrer_rp_t3([3],[500,600],**{k:v for k,v in opciones.items()
                      if k!="rp"})
        b=barrer_rp_t3([3],[500,600],restricciones={"exigir_empuje_positivo":False,
            "exigir_margen_tobera":False},**{k:v for k,v in opciones.items()
                      if k!="rp"})
        self.assertEqual(a["estados"],[["sin_expansion"],["empuje_no_positivo"]])
        self.assertEqual(a["cumplen_restricciones"],0)
        self.assertEqual(b["cumplen_restricciones"],2)
        self.assertEqual(b["validos"],0)
        self.assertIsNone(b["maximo_Fs"])

    def test_limites_termicos_rechazados_sin_valores_ficticios(self):
        m=barrer_rp_t3([10],[200,2000])
        # El extremo superior T3=2000 K no es, por sí mismo, inadmisible:
        # la cota es cerrada. T3=200 K sí incumple aporte térmico positivo.
        bajo, alto=m["puntos"][0][0],m["puntos"][1][0]
        self.assertEqual(bajo["estado"],"inadmisible")
        self.assertIsNone(bajo["Fs"])
        self.assertIn(alto["estado"],("valido","inadmisible","sin_expansion"))

    @unittest.skipUnless(importlib.util.find_spec("cantera"),
                         "Cantera opcional no instalado; no se añade a requirements")
    def test_propiedades_cantera_opcional(self):
        import cantera as ct
        gas=ct.Solution("air.yaml")
        faltantes=set(("N2","O2","AR"))-set(gas.species_names)
        if faltantes:
            self.skipTest(f"Mecanismo sin especies {faltantes}")
        gas.TPX=298.15,101325,"N2:0.78, O2:0.21, AR:0.01"
        h0,s0_ct=gas.enthalpy_mass,gas.entropy_mass
        gas.TPX=700,101325,"N2:0.78, O2:0.21, AR:0.01"
        self.assertLess(comparar(cp(700),gas.cp_mass)[1],.08)
        self.assertLess(comparar(h(700), (gas.enthalpy_mass-h0)/1000)[1],.08)
        self.assertLess(comparar(s0(700)-s0(298.15),
                     (gas.entropy_mass-s0_ct)/1000)[1],.08)


if __name__ == "__main__":
    unittest.main()
