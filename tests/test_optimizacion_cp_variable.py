"""Pruebas Fase 2C; contrastes independientes por muestreo de rp."""
import unittest
from math import isclose
from optimizacion_cp_variable import estudiar_cp_variable,_maximo_acotado,_raiz_monotona
from ciclo_cp_variable import resolver_ciclo

class Fase2CTests(unittest.TestCase):
 def test_caso_base(self):
  d=estudiar_cp_variable(288.15,1600)
  self.assertEqual(d['tipo'],'motor')
  self.assertAlmostEqual(d['dominio_motor'][0],1.069645087,places=5)
  self.assertAlmostEqual(d['dominio_motor'][1],229.221073,places=3)
 def test_maximo_trabajo(self):
  d=estudiar_cp_variable(288.15,1600)
  self.assertAlmostEqual(d['A']['rp'],15.8779,delta=.015)
  self.assertAlmostEqual(d['A']['trabajo_neto'],414.0858,delta=.03)
 def test_maximo_rendimiento(self):
  d=estudiar_cp_variable(288.15,1600)
  self.assertAlmostEqual(d['B']['rp'],46.819,delta=.05)
  self.assertAlmostEqual(d['B']['rendimiento'],.43745,delta=.0001)
 def test_objetivos_separados(self):
  d=estudiar_cp_variable(288.15,1600)
  self.assertGreater(d['A']['trabajo_neto'],d['B']['trabajo_neto'])
  self.assertGreater(d['B']['rendimiento'],d['A']['rendimiento'])
 def test_primera_ley(self):
  d=estudiar_cp_variable(288.15,1600)
  for tipo in ('A','B'):
   p=d[tipo]['punto']
   self.assertAlmostEqual(p['trabajo_neto'],p['calor_aportado']-p['calor_rechazado'],places=8)
   self.assertTrue(p['viable'])
 def test_estabilidad_malla(self):
  a=estudiar_cp_variable(288.15,1600,muestras=80)
  b=estudiar_cp_variable(288.15,1600,muestras=240)
  self.assertAlmostEqual(a['A']['rp'],b['A']['rp'],delta=.005)
  self.assertAlmostEqual(a['B']['rp'],b['B']['rp'],delta=.05)
 def test_caso_sin_motor(self):
  d=estudiar_cp_variable(500,500)
  self.assertIsNone(d['A']);self.assertIsNone(d['B'])
 def test_reversible_supremo(self):
  d=estudiar_cp_variable(288.15,1600,eta_c=1,eta_t=1,delta=0)
  self.assertEqual(d['B']['tipo'],'supremo_frontera')
  self.assertIsNone(d['B']['rp'])
 def test_concavidad_y_bordes_termicos_no_crean_optimo_ficticio(self):
  # En esta física, el máximo A libre es interior del conjunto motor:
  # cerca de la expansión la turbina no produce trabajo, y en la cota
  # de q_in=0 se tiene w=-q_out<0. Si se activa la cota T4s=200 K,
  # w'(x)=R*(eta_t*T4s-T2s/eta_c)<0 por T2s>=T1>=200 K.
  from math import log
  from propiedades_aire import R_AIRE
  for parametros in ((288.15,1600,.85,.90,.05), (200,2000,1.,1.,0.),
                     (300,1000,.65,.8,.1)):
   T1,T3,ec,et,delta=parametros
   d=estudiar_cp_variable(T1,T3,eta_c=ec,eta_t=et,delta=delta)
   if d['tipo']!='motor':continue
   self.assertEqual(d['A']['tipo'],'maximo_interior')
   lo,hi=d['dominio_motor']
   self.assertLess(lo,d['A']['rp'])
   self.assertLess(d['A']['rp'],hi)
   p=d['A']['punto']
   self.assertAlmostEqual(et*p['T4s']-p['T2s']/ec,0,delta=2e-5)
   self.assertLessEqual(abs(p['residuo_primera_ley']),1e-8)

 def test_entradas_invalidas(self):
  for kw in ({'T1':True},{'T1':100},{'delta':1},{'eta_c':0},{'muestras':1}):
   args={'T1':288.15,'T3':1600};args.update(kw)
   with self.subTest(kw=kw),self.assertRaises(ValueError):estudiar_cp_variable(**args)
 def test_cotas_y_no_motor(self):
  d=estudiar_cp_variable(288.15,1600)
  for r in d['dominio_motor']:
   # fronteras excluidas: no afirmar viabilidad con datos redondeados
   self.assertGreater(r,0)
  self.assertLess(d['A']['rp'],d['dominio_motor'][1])
 def test_convergencia_controlada(self):
  with self.assertRaises(ValueError):_raiz_monotona(lambda x:x*x+1,0,2)
  self.assertAlmostEqual(_maximo_acotado(lambda x:-(x-2)**2,0,4,1e-10),2,delta=1e-6)
 def test_referencia_malla_independiente(self):
  d=estudiar_cp_variable(288.15,1600)
  lo,hi=d['dominio_motor'];bestw=-1e99;besteta=-1e99
  for j in range(1,501):
   rp=lo+(hi-lo)*j/501
   p=resolver_ciclo(288.15,1600,rp,100,.85,.9,.05)
   if p['viable']:
    bestw=max(bestw,p['trabajo_neto']);besteta=max(besteta,p['rendimiento'])
  self.assertLessEqual(bestw,d['A']['trabajo_neto']+1e-5)
  self.assertLessEqual(besteta,d['B']['rendimiento']+1e-6)
if __name__=='__main__':unittest.main()
