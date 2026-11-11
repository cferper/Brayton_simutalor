const test=require('node:test');
const assert=require('node:assert/strict');
const {iniciarEsquemaEducativo49_7}=require('../../static/turborreactor_interactivo.js');

test('La ficha conserva componente al actualizar, invalida valores y no solicita API',()=>{
  class Nodo {
    constructor(){this.dataset={};this.children=[];this.eventos={};this.atributos={};this.textContent='';this.hidden=false;this.classList={toggle:()=>{}};}
    addEventListener(tipo,fn){this.eventos[tipo]=fn;}
    setAttribute(k,v){this.atributos[k]=v;}
    replaceChildren(...h){this.children=h;}
    append(...h){this.children.push(...h);}
  }
  const nombres=['difusor','compresor','camara','turbina','eje','tobera'];
  const piezas=nombres.map(n=>{const x=new Nodo();x.dataset.enginePart=n;return x;});
  const botones=['funcionamiento','resultados','ecuaciones'].map(n=>{const x=new Nodo();x.dataset.engineTab=n;return x;});
  const paneles=botones.map(b=>{const x=new Nodo();x.dataset.enginePanel=b.dataset.engineTab;return x;});
  const ids=Object.fromEntries(['turbo-engine-part-title','turbo-engine-part-description','turbo-engine-data-list','turbo-engine-data-status','turbo-engine-equations'].map(k=>['#'+k,new Nodo()]));
  const esquema={querySelector:s=>ids[s],querySelectorAll:s=>s==='[data-engine-part]'?piezas:s==='[data-engine-tab]'?botones:paneles};
  const documento={querySelector:()=>esquema,createElement:()=>new Nodo()};
  const ficha=iniciarEsquemaEducativo49_7(documento);
  assert.ok(ficha.seleccionar('compresor'));
  ficha.cambiarApartado('resultados');
  ficha.actualizar({componentes:{compresor:[{etiqueta:'T total',valor:505.5,unidad:'K',clase:'total',origen:'compresor.T2'}]}});
  assert.match(ids['#turbo-engine-data-list'].children[0].children[1].textContent,/505/);
  assert.equal(ids['#turbo-engine-part-title'].textContent,'Compresor');
  ficha.pendiente('Calculando otro punto');
  assert.equal(ids['#turbo-engine-data-list'].children.length,0);
  assert.match(ids['#turbo-engine-data-status'].textContent,/Calculando/);
  ficha.actualizar({componentes:{compresor:[{etiqueta:'T total',valor:560,unidad:'K',clase:'total',origen:'compresor.T2'}]}});
  assert.match(ids['#turbo-engine-data-list'].children[0].children[1].textContent,/560/);
  assert.equal(ids['#turbo-engine-part-title'].textContent,'Compresor');
  assert.equal(botones[1].atributos['aria-pressed'],'true');
  assert.equal(paneles[1].hidden,false);
  assert.equal(paneles[0].hidden,true);
});
