const test=require('node:test');
const assert=require('node:assert/strict');
const {iniciarCaracterizacion49_9}=require('../../static/turborreactor_interactivo.js');

test('Tres pestañas locales, detalle y retirada de datos obsoletos sin API',()=>{
  class Nodo{
    constructor(){this.dataset={};this.children=[];this.events={};this.attrs={};this.textContent='';}
    addEventListener(nombre,callback){this.events[nombre]=callback;}
    setAttribute(nombre,valor){this.attrs[nombre]=valor;}
    replaceChildren(...nodos){this.children=nodos;}
    append(...nodos){this.children.push(...nodos);}
  }
  const pestañas=['funcionamiento','consumo','rendimientos'].map(clave=>{
    const n=new Nodo();n.dataset.characterizationTab=clave;return n;
  });
  const lista=new Nodo(),estado=new Nodo();
  const raiz={querySelector:s=>s==='#turbo-characterization-list'?lista:estado,
    querySelectorAll:()=>pestañas};
  const documento={querySelector:()=>raiz,createElement:()=>new Nodo()};
  const ui=iniciarCaracterizacion49_9(documento);
  let llamadas=0;
  const datos={funcionamiento:[{id:'tit',nombre:'TIT',simbolo:'Tt4',valor:1600,unidad:'K',estado:'calculado',formula:'T3',fuente:'combustor.T3'}],
    consumo:[{id:'tsfc',nombre:'TSFC',simbolo:'TSFC',valor:null,unidad:'kg/(N·h)',estado:'no_disponible',formula:'f/Fs',fuente:'prestaciones',nota:'Fs no positivo'}],rendimientos:[]};
  ui.actualizar({caracterizacion:datos});
  assert.match(lista.children[0].children[1].children[0].textContent,/1.?600/);
  pestañas[1].events.click();
  assert.equal(pestañas[1].attrs['aria-pressed'],'true');
  assert.match(lista.children[0].children[1].children[0].textContent,/No disponible/);
  ui.pendiente('Entradas modificadas');
  assert.equal(lista.children.length,0);
  assert.match(estado.textContent,/modificadas/);
  ui.actualizar({caracterizacion:datos});
  assert.equal(lista.children.length,1);
  assert.equal(llamadas,0);
});
