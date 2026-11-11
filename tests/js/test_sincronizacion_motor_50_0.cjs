const test=require('node:test');
const assert=require('node:assert/strict');
const {iniciarSincronizacion50_0}=require('../../static/turborreactor_interactivo.js');

function punto(atributo,clave){
  const atributos={[atributo]:clave};
  const clases=new Set();
  return {hasAttribute:k=>k in atributos,getAttribute:k=>atributos[k],
    classList:{toggle(k,activo){if(activo)clases.add(k);else clases.delete(k);},
      contains:k=>clases.has(k)}};
}
const e=(id,T,p,tipo='Remanso')=>({id,nombre:id,T,p,tipo});

test('Selección destaca estaciones calculadas y trabajo, sin disparar fetch',()=>{
  const nodos=[...['pt2','pt3','pt4','pt5','salida','garganta'].map(k=>punto('data-engine-station',k)),
    ...['compresor','turbina','eje'].map(k=>punto('data-engine-work',k)),
    ...['compresor','camara','turbina','tobera'].map(k=>punto('data-engine-energy',k))];
  const estado={textContent:''};
  const documento={getElementById:()=>estado,querySelectorAll:()=>nodos};
  const sync=iniciarSincronizacion50_0(documento);
  const marcados=()=>nodos.filter(n=>n.classList.contains('is-engine-related'));
  assert.equal(marcados().length,0);
  sync.actualizar({estaciones:[e('pt2',300,100),e('pt3',600,850),
    e('pt4',1500,820),e('pt5',800,200),e('salida',550,101,'Estático')]});
  sync.seleccionar('compresor');
  assert.equal(marcados().length,4); // dos gráficos por estación no: dos puntos, trabajo y energía
  assert.match(estado.textContent,/entrada: pt2.*salida: pt3/);
  sync.seleccionar('eje');
  assert.equal(marcados().length,1);
  assert.match(estado.textContent,/no constituye una estación termodinámica/);
  sync.seleccionar('tobera');
  assert.equal(marcados().length,3); // entrada, salida existente y barra energética
  assert.doesNotMatch(estado.textContent,/garganta/);
  sync.pendiente();
  assert.equal(marcados().length,0);
  assert.match(estado.textContent,/pendientes/);
  assert.equal(sync.seleccionar('inventado'),false);
});
