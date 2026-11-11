const test=require('node:test');
const assert=require('node:assert/strict');
const {diferencia50_1,compatibilidad50_1,extraer50_1,valor50_1,
  dibujarEstados50_1,dibujarPrestaciones50_1}=require('../../static/laboratorio_comparativo_50_1.js');

const caracterizacion={funcionamiento:[{id:'rp',valor:10}],consumo:[
  {id:'fs',valor:500},{id:'tsfc',valor:0.0005},{id:'fn',valor:null},{id:'mf',valor:null}],rendimientos:[]};
const estaciones=[['pt2',300,101,0.1],['pt3',600,1010,0.15],['pt4',1500,960,0.9],['pt5',830,230,0.95]]
  .map(([id,T,p,s])=>({id,T,p,s,tipo:'Remanso'}));
const respuesta={ok:true,modo:'impuesto',caracterizacion,estaciones,
  magnitudes:{empuje_especifico_neto:500},diagnosticos:{}};
const crear=(mach='0.3',T3='1500',modo='impuesto')=>extraer50_1({...respuesta,modo},{mach,T3,modo_caudal:modo,area_salida:'0.2'});

test('Diferencias firmadas, cero y puntos porcentuales',()=>{
  assert.deepEqual(diferencia50_1(10,12,'K'),{absoluta:2,relativa:20,unidadAbsoluta:'K'});
  assert.equal(diferencia50_1(0,10).relativa,null);
  assert.equal(diferencia50_1(null,10).absoluta,null);
  assert.equal(diferencia50_1(40,35,'%').unidadAbsoluta,'puntos porcentuales');
  assert.equal(diferencia50_1(40,35,'%').relativa,-12.5);
});
test('Referencia independiente, sustitución posible y diferencias de modo o geometría',()=>{
  const ref=crear(),actual=crear('0.6','1550');
  assert.ok(compatibilidad50_1(ref,actual).homogenea);
  assert.deepEqual(compatibilidad50_1(ref,actual).cambios.sort(),['T3','mach']);
  actual.estaciones[0].T=400;
  assert.equal(ref.estaciones[0].T,300);
  assert.ok(!compatibilidad50_1(ref,crear('0.4','1500','acoplado')).compatible);
  const otro=crear();otro.entradas.area_salida='0.3';
  assert.ok(!compatibilidad50_1(ref,otro).homogenea);
  const equivalente=crear('0.30','1500.0');
  assert.equal(compatibilidad50_1(ref,equivalente).cambios.length,0);
  assert.equal(valor50_1(ref,'fn'),null);
  assert.equal(extraer50_1({...respuesta,ok:false},{mach:1}),null);
});
test('Gráficas usan dos series de valores calculados y omiten ausencias',()=>{
  const a=crear(),b=crear('0.5');
  assert.equal((dibujarEstados50_1(a,b,'ts').match(/data-engine-station/g)||[]).length,8);
  assert.equal((dibujarEstados50_1(a,b,'T').match(/data-engine-station/g)||[]).length,8);
  const svg=dibujarPrestaciones50_1(a,b,true);
  assert.match(svg,/Punto 1/);
  assert.doesNotMatch(svg,/fn \(N\)/);
  assert.equal(dibujarPrestaciones50_1(a,b,false),'');
});
