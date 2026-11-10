const test=require('node:test');
const assert=require('node:assert/strict');
const {iniciarEsquemaEducativo49_7}=require('../../static/turborreactor_interactivo.js');

test('Seis piezas seleccionables por clic y teclado, sin solicitudes físicas',()=>{
  const claves=['difusor','compresor','camara','turbina','eje','tobera'];
  const elementos=claves.map(clave=>({
    dataset:{enginePart:clave},eventos:{},atributos:{},activa:false,
    classList:{toggle(_nombre,estado){this.activa=estado;}},
    addEventListener(tipo,fn){this.eventos[tipo]=fn;},
    setAttribute(k,v){this.atributos[k]=v;}
  }));
  const titulo={textContent:''}, descripcion={textContent:''};
  const esquema={
    querySelectorAll:()=>elementos,
    querySelector:selector=>selector==='#turbo-engine-part-title'?titulo:descripcion
  };
  const documento={querySelector:()=>esquema};
  const seleccion=iniciarEsquemaEducativo49_7(documento);
  assert.equal(titulo.textContent,'Entrada y difusor');
  assert.equal(elementos[0].atributos['aria-pressed'],'true');
  for(const [indice,pieza] of elementos.entries()){
    if(indice%2){let prevenido=false;pieza.eventos.keydown({key:'Enter',preventDefault(){prevenido=true;}});assert.ok(prevenido);}
    else pieza.eventos.click();
    assert.equal(elementos.filter(p=>p.atributos['aria-pressed']==='true').length,1);
    assert.equal(pieza.atributos['aria-pressed'],'true');
    assert.ok(titulo.textContent && descripcion.textContent);
  }
  let prevenido=false;
  elementos[1].eventos.keydown({key:' ',preventDefault(){prevenido=true;}});
  assert.ok(prevenido);
  assert.equal(titulo.textContent,'Compresor');
  assert.equal(seleccion.seleccionar('inventado'),false);
  assert.equal(elementos.filter(p=>p.atributos['aria-pressed']==='true').length,1);
});
