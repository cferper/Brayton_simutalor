/* Pruebas focalizadas del control de eventos sin navegador ni dependencias. */
const test=require('node:test');
const assert=require('node:assert/strict');
const {crearControlador48,acoplarControl48}=require('../../static/turborreactor_interactivo.js');

class Campo {
  constructor(valor, min='0', max='2000'){
    this.value=valor;this.min=min;this.max=max;this.listeners={};this.textContent='';
  }
  addEventListener(tipo,fn){this.listeners[tipo]=fn;}
  emitir(tipo){this.listeners[tipo]?.();}
}

test('Mach: deslizador y número sincronizados',()=>{
  const numero=new Campo('0.3');const rango=new Campo('0.3','0','0.999');const lectura=new Campo('');
  let cambios=0;
  acoplarControl48({numero,deslizador:rango,lectura,unidad:'–',onCambio:()=>cambios++});
  rango.value='0.7';rango.emitir('input');
  assert.equal(numero.value,'0.7');assert.equal(lectura.textContent,'0.7 –');
  numero.value='0.42';numero.emitir('input');
  assert.equal(rango.value,'0.42');assert.equal(cambios,2);
});

test('T3: número exacto y rango sincronizados',()=>{
  const numero=new Campo('1600');const rango=new Campo('1600','200','2000');const lectura=new Campo('');
  acoplarControl48({numero,deslizador:rango,lectura,unidad:'K',onCambio:()=>{}});
  numero.value='1750.5';numero.emitir('input');
  assert.equal(rango.value,'1750.5');assert.equal(lectura.textContent,'1750.5 K');
  rango.value='1400';rango.emitir('input');assert.equal(numero.value,'1400');
});

test('valor exacto fuera de muestreo del deslizador no se sobreescribe',()=>{
  const numero=new Campo('0.9999');const rango=new Campo('0.5','0','0.999');const lectura=new Campo('');
  acoplarControl48({numero,deslizador:rango,lectura,unidad:'–',onCambio:()=>{}});
  numero.emitir('input');assert.equal(numero.value,'0.9999');
  assert.equal(rango.value,'0.999');
});

test('debounce: de dos cambios se envía solo el último a los 350 ms',async()=>{
  const pendientes=new Map();let id=0,envios=0;
  const gestor=crearControlador48({solicitar:async()=>{envios++;return {ok:true};},
    onEstado:()=>{},onRespuesta:()=>{},onError:()=>{},
    setTimer:fn=>{pendientes.set(++id,fn);return id;},clearTimer:n=>pendientes.delete(n)});
  gestor.cambiar();gestor.cambiar();
  assert.equal(pendientes.size,1);assert.equal(envios,0);
  await [...pendientes.values()][0]();assert.equal(envios,1);
});

test('una respuesta antigua no sobrescribe una más reciente',async()=>{
  const pendientes=[];const resolver=[];const aceptadas=[];
  const gestor=crearControlador48({solicitar:()=>new Promise(resolve=>resolver.push(resolve)),
    onEstado:()=>{},onRespuesta:v=>aceptadas.push(v),onError:e=>{throw e;},
    setTimer:fn=>{pendientes.push(fn);return pendientes.length;},clearTimer:()=>{}});
  gestor.cambiar();const primera=pendientes.pop()();
  gestor.cambiar();const segunda=pendientes.pop()();
  resolver[1]('nueva');await segunda;
  resolver[0]('antigua');await primera;
  assert.deepEqual(aceptadas,['nueva']);
});

test('fallo y cambio posterior: permite reintentar sin resultados falsos',async()=>{
  const pendientes=[];let fallo=true,errores=0,correctos=0;
  const gestor=crearControlador48({solicitar:async()=>{if(fallo)throw new Error('fuera del mapa');return true;},
    onEstado:()=>{},onRespuesta:()=>correctos++,onError:()=>errores++,
    setTimer:fn=>{pendientes.push(fn);return pendientes.length;},clearTimer:()=>{}});
  gestor.cambiar();await pendientes.pop()();assert.equal(errores,1);
  fallo=false;gestor.cambiar();await pendientes.pop()();assert.equal(correctos,1);
});

test('el envío manual invalida una respuesta HTTP tardía',async()=>{
  const temporizadores=[];let resolver;const aceptadas=[];
  const gestor=crearControlador48({
    solicitar:()=>new Promise(resolve=>{resolver=resolve;}),
    onEstado:()=>{},onRespuesta:v=>aceptadas.push(v),onError:e=>{throw e;},
    setTimer:fn=>{temporizadores.push(fn);return temporizadores.length;},
    clearTimer:()=>{}
  });
  gestor.cambiar();const peticion=temporizadores.pop()();
  gestor.cancelar();resolver({resultado:'obsoleto'});
  await peticion;
  assert.deepEqual(aceptadas,[]);
});

test('invalidar por otro campo también descarta respuestas antiguas',async()=>{
  const temporizadores=[];let resolver;const aceptadas=[];
  const gestor=crearControlador48({
    solicitar:()=>new Promise(resolve=>{resolver=resolve;}),
    onEstado:()=>{},onRespuesta:v=>aceptadas.push(v),onError:e=>{throw e;},
    setTimer:fn=>{temporizadores.push(fn);return temporizadores.length;},
    clearTimer:()=>{}
  });
  gestor.cambiar();const peticion=temporizadores.pop()();
  gestor.invalidar();resolver({resultado:'obsoleto'});
  await peticion;
  assert.deepEqual(aceptadas,[]);
});
