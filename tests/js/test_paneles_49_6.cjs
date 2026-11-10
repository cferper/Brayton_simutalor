const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const raiz=path.resolve(__dirname,'../..');

test('Alternar estudios/punto repetidamente conserva panel y controles',()=>{
  class Elemento {
    constructor(){this.hidden=false;this.dataset={};this.eventos={};this.atributos={};}
    addEventListener(tipo,fn){this.eventos[tipo]=fn;}
    setAttribute(k,v){this.atributos[k]=v;}
    querySelectorAll(){return [];}
    scrollIntoView(){}
  }
  const ids={};
  const get=id=>ids[id]||(ids[id]=new Elemento());
  get('study49-tipo').value='mach';
  get('turbo-form').elements={modo_caudal:{value:'impuesto'}};
  get('estudio49').hidden=true;
  const botones=['punto','estudios'].map(v=>{const b=new Elemento();b.dataset.study49View=v;return b;});
  let inicio;
  const doc={getElementById:get,querySelectorAll:()=>botones,
    addEventListener:(_tipo,fn)=>{inicio=fn;}};
  vm.runInNewContext(fs.readFileSync(path.join(raiz,'static/estudios_parametricos_49_5.js'),'utf8'),
    {document:doc,fetch:()=>{throw Error('El cambio de panel no debe calcular');}});
  inicio();
  for(let i=0;i<4;i++){
    botones[1].eventos.click();
    assert.equal(get('estudio49').hidden,false);
    assert.equal(get('configuracion').hidden,true);
    assert.equal(botones[1].atributos['aria-pressed'],'true');
    botones[0].eventos.click();
    assert.equal(get('estudio49').hidden,true);
    assert.equal(get('configuracion').hidden,false);
  }
  // La CSS real debe permitir que el controlador muestre el panel.
  const css=fs.readFileSync(path.join(raiz,'static/turborreactor.css'),'utf8');
  assert.match(css,/\.turbo-section:not\(#configuracion\):not\(#estudio49\)\{display:none!important\}/);
  assert.match(css,/\.turbo-study49\[hidden\]/);
});
