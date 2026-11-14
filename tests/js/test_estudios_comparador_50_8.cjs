/* M50.8: comprobación real de lógica de interfaz con DOM simulado.
   No equivale a prueba de navegador ni a regresión termodinámica. */
'use strict';
const assert=require('node:assert/strict');
const {iniciarAnalisis50_8,ETIQUETAS_ESTUDIOS,ETIQUETAS_COMPARADOR}=
  require('../../static/estudios_comparador_50_8');
let count=0;function ok(expr,msg){assert.ok(expr,msg);count++;}
function eq(a,b,msg){assert.deepEqual(a,b,msg);count++;}
class Elem{
  constructor(tag='div',id=''){
    this.tagName=tag.toUpperCase();this.id=id;this.children=[];this.parentNode=null;
    this.dataset={};this.attributes={};this.listeners={};this.hidden=false;
    this.className='';this.textContent='';this.style={};this.value='';this.disabled=false;
    this._focus=false;this.tabIndex=0;this.type='';
    this.classList={contains:x=>this.className.split(/\s+/).includes(x),
      add:x=>{if(!this.className.split(/\s+/).includes(x))this.className=(this.className+' '+x).trim();}};
  }
  get firstChild(){return this.children[0]||null;}
  get parentElement(){return this.parentNode;}
  append(...v){v.forEach(x=>this.appendChild(x));}
  appendChild(x){if(x.parentNode)x.parentNode.children=x.parentNode.children.filter(z=>z!==x);
    x.parentNode=this;this.children.push(x);return x;}
  insertBefore(x,ref){if(x.parentNode)x.parentNode.children=x.parentNode.children.filter(z=>z!==x);
    x.parentNode=this;const i=this.children.indexOf(ref);this.children.splice(i<0?this.children.length:i,0,x);return x;}
  setAttribute(k,v){this.attributes[k]=String(v);}
  getAttribute(k){return this.attributes[k]??null;}
  removeAttribute(k){delete this.attributes[k];}
  addEventListener(t,fn,capture=false){(this.listeners[t]??=[]).push({fn,capture:!!capture});}
  dispatchEvent(e){
    e.target??=this;e.preventDefault??=()=>{};
    const raiz=e.target===this;
    if(raiz){e._stopped=false;e.stopImmediatePropagation=()=>{e._stopped=true;};}
    const eventos=this.listeners[e.type]||[];
    const cola=raiz?[...eventos.filter(x=>x.capture),...eventos.filter(x=>!x.capture)]:eventos;
    for(const {fn} of cola){if(e._stopped)break;fn(e);}
    if(e.bubbles&&!e._stopped&&this.parentNode)this.parentNode.dispatchEvent(e);
    return true;
  }
  click(){if(!this.disabled)this.dispatchEvent({type:'click',bubbles:true});}
  focus(){this._focus=true;}
  remove(){if(this.parentNode)this.parentNode.children=this.parentNode.children.filter(x=>x!==this);this.parentNode=null;}
  walk(){return this.children.flatMap(x=>[x,...x.walk()]);}
  matches(selector){
    const q=selector.trim();
    if(q.includes(' ')){
      const pieces=q.split(/\s+/),last=pieces.pop();
      if(!this.matches(last))return false;
      return this.parentNode?.closest(pieces.join(' '))!=null;
    }
    if(q.startsWith('#'))return this.id===q.slice(1);
    const classMatch=q.match(/^\.([\w-]+)/);
    if(classMatch)return this.className.split(/\s+/).includes(classMatch[1]);
    const dataMatch=q.match(/^\[data-([a-z-]+)(?:="([^"]+)")?\]$/);
    if(dataMatch){const k=dataMatch[1].replace(/-([a-z])/g,(_,c)=>c.toUpperCase());
      return this.dataset[k]!==undefined&&(dataMatch[2]===undefined||this.dataset[k]===dataMatch[2]);}
    return q.toUpperCase()===this.tagName;
  }
  closest(q){for(let p=this;p;p=p.parentNode)if(p.matches(q))return p;return null;}
  querySelectorAll(q){return this.walk().filter(x=>x.matches(q));}
  querySelector(q){return this.querySelectorAll(q)[0]||null;}
}
const el=(t,id,cls)=>{const x=new Elem(t,id);x.className=cls||'';return x;};
function fixture(){
  const body=el('body'),main=el('main'),estudios=el('section','espacio-estudios');
  const comparador=el('section','espacio-comparador');
  body.dataset.interfaz='interactivo';body.classList.add('turbo-50-5-ready');
  body.appendChild(main);main.append(estudios,comparador);
  const e=el('section','estudio49','turbo-study49');e.hidden=true;estudios.appendChild(e);
  const grid=el('div',undefined,'turbo-study49-grid');e.append(grid);
  const form=el('form','turbo-study49-form'),result=el('div',undefined,'turbo-study49-results');
  grid.append(form,result);
  const tipo=el('select','study49-tipo');tipo.value='mach';form.appendChild(tipo);
  const fuente=el('select','study49-base');fuente.value='banco';form.appendChild(fuente);
  const axis=el('input');form.appendChild(axis);
  const chart=el('div','study49-chart'),point=el('section',undefined,'study49-point');
  result.append(chart,point);
  const apply=el('button','study49-apply');point.appendChild(apply);
  const mapOld=el('svg');chart.appendChild(mapOld);
  const legacy=[];
  for(const id of ['sensibilidad','mapa']){
    const details=el('details',undefined,'turbo-work-legacy50');
    details.append(el('summary'),el('section',id,'turbo-section'));
    legacy.push(details);estudios.append(details);
  }
  const lab=el('section',undefined,'turbo-lab50');comparador.appendChild(lab);
  const heading=el('h4');lab.append(heading,el('p'));
  const act=el('div',undefined,'turbo-lab50-actions');const save=el('button');
  save.dataset.labAction='save';act.append(save);lab.append(act);
  const status=el('p');status.dataset.labStatus='';lab.append(status);
  const conditions=el('details');conditions.append(el('summary'),el('div'));lab.append(conditions);
  const warning=el('p');warning.dataset.labWarning='';lab.append(warning);
  const table=el('div',undefined,'turbo-lab50-table'),diagnosis=el('p');
  diagnosis.dataset.labDiagnosis='';lab.append(table,diagnosis);
  const charts=el('div',undefined,'turbo-lab50-charts');lab.append(charts);
  const figures={};const keys=['ts','T','p','prestaciones'];
  for(const k of keys){const figure=el('figure');const inner=el('div');inner.dataset.labChart=k;
    figure.append(inner);charts.appendChild(figure);figures[k]=figure;}
  const tools=el('div',undefined,'turbo-lab50-tools');lab.append(tools);
  const reading=el('p');reading.dataset.labReading='';lab.append(reading);
  const motor=el('form','turbo-form');body.append(motor);
  let fetches=0,reset=0,active='simulacion',activeChart='ts';
  const events={};const doc={body,createElement:t=>el(t),getElementById:id=>body.walk().find(x=>x.id===id)||null,
    querySelector:q=>body.querySelector(q),querySelectorAll:q=>body.querySelectorAll(q),
    addEventListener:(t,fn)=>events[t]=fn};
  const win={Event:class{constructor(type,opts={}){this.type=type;this.bubbles=!!opts.bubbles;}},
    confirm:()=>true,controladorNavegacion50_5:{navegar(id){active=id;return true;}}};
  tipo.addEventListener('change',()=>{reset++;chart.children=[];apply.hidden=true;});
  lab.addEventListener('click',evt=>{const v=evt.target.closest('[data-lab-chart]');if(v)activeChart=v.dataset.labChart;});
  return {doc,win,body,main,estudios,comparador,e,grid,form,result,tipo,fuente,axis,chart,mapOld,
    point,apply,legacy,lab,heading,conditions,warning,table,diagnosis,charts,figures,tools,reading,
    save,motor,get active(){return active;},get activeChart(){return activeChart;},
    get reset(){return reset;},get fetches(){return fetches;}};
}
const a=fixture();
const ui=iniciarAnalisis50_8(a.doc,a.win);
ok(ui,'Se inicializa M50.8');ok(a.body.classList.contains('turbo-50-8-ready'));
eq(ETIQUETAS_ESTUDIOS.length,3);eq(ETIQUETAS_COMPARADOR.length,3);
eq(ui.estudios.actual(),'barridos');ok(!ui.estudios.paneles.get('barridos').hidden);
eq(a.e.parentNode,ui.estudios.paneles.get('barridos'),'Explorador original reutilizado');
eq(a.point.parentNode.className,'turbo-ana58-info','Detalle a tercera columna');
eq(a.grid.querySelectorAll('.turbo-ana58-info').length,1);
for(const n of a.legacy)eq(n.parentNode,ui.estudios.paneles.get('clasicos'),'OFAT y mapa clásico accesibles');
eq(a.form.parentNode,a.grid,'Formulario del estudio original');
ui.estudios.seleccionar('clasicos');ok(!ui.estudios.paneles.get('clasicos').hidden);
ok(a.e.parentNode.hidden,'Explorador oculto sin destruir sus datos');
eq(a.chart.querySelector('svg'),a.mapOld,'Conservar datos al abrir Clásicos');
eq(a.reset,0,'Sin cambios de tipo al entrar en Clásicos');
ui.estudios.seleccionar('barridos');eq(a.chart.querySelector('svg'),a.mapOld);
let confirms=0;a.win.confirm=()=>{confirms++;return false;};
eq(ui.estudios.seleccionar('mapa'),false,'El usuario puede cancelar el cambio de tipo');
eq(ui.estudios.actual(),'barridos');eq(a.tipo.value,'mach');eq(a.chart.querySelector('svg'),a.mapOld);
a.win.confirm=()=>{confirms++;return true;};
ok(ui.estudios.seleccionar('mapa'),'Se puede seleccionar mapa');eq(confirms,2);
eq(a.tipo.value,'mapa');eq(a.reset,1,'Se reutiliza el listener original de tipo');
ok(!ui.aviso.hidden,'Se avisa de la sustitución del estudio');
eq(a.e.parentNode,ui.estudios.paneles.get('mapa'));
eq(a.fetches,0,'La navegación no ejecuta HTTP');
ui.estudios.seleccionar('clasicos');ui.estudios.seleccionar('mapa');
eq(a.reset,1,'Regresar a la misma vista no reinicia el estudio');
// Desactualización conservando datos reales históricos.
a.chart.appendChild(a.mapOld);a.apply.disabled=false;
a.axis.dispatchEvent({type:'input',bubbles:true});
ok(!ui.aviso.hidden);ok(ui.aviso.textContent.includes('desactualizada'));ok(a.apply.disabled);
eq(a.chart.querySelector('svg'),a.mapOld);
a.apply.disabled=false;a.motor.dispatchEvent({type:'input',bubbles:true});ok(a.apply.disabled);
a.form.dispatchEvent({type:'submit',bubbles:true});ok(ui.aviso.hidden);ok(!a.apply.disabled);
// El selector interno M49.5 debe solicitar confirmación ANTES de limpiar.
a.chart.appendChild(a.mapOld);const cambiosAntes=a.reset;
a.win.confirm=()=>false;
a.tipo.value='T3';a.tipo.dispatchEvent({type:'change',bubbles:true});
eq(a.tipo.value,'mapa','Cancelar cambio manual deja el estudio actual');
eq(a.reset,cambiosAntes,'No se limpia el estudio si se cancela');
eq(a.chart.querySelector('svg'),a.mapOld);
a.win.confirm=()=>true;
a.tipo.value='T3';a.tipo.dispatchEvent({type:'change',bubbles:true});
eq(a.tipo.value,'T3');eq(a.reset,cambiosAntes+1);
eq(ui.estudios.actual(),'barridos','Selección manual sincroniza subvista');
a.chart.appendChild(a.mapOld);a.fuente.value='diseno_c';a.win.confirm=()=>false;
a.apply.disabled=false;ui.aviso.hidden=true;
a.fuente.dispatchEvent({type:'input',bubbles:true});
a.fuente.dispatchEvent({type:'change',bubbles:true});
eq(a.fuente.value,'banco','Cancelar cambio de referencia evita borrado');
ok(!a.apply.disabled&&ui.aviso.hidden,'Cancelar conserva el botón y el aviso anteriores');
// Comparador: los mismos componentes, la misma referencia y cuatro gráficas.
ok(ui.comparador.actual()==='prestaciones');
eq(a.table.parentNode,ui.comparador.paneles.get('prestaciones'));
eq(a.warning.parentNode,ui.comparador.paneles.get('prestaciones'));
eq(a.conditions.parentNode,ui.comparador.paneles.get('condiciones'));
eq(a.charts.parentNode,ui.comparador.paneles.get('graficas'));
eq(a.tools.parentNode,ui.comparador.paneles.get('graficas'));
let referencia={valor:42};a.lab.referencia=referencia;
ui.comparador.seleccionar('graficas');ok(!ui.comparador.paneles.get('graficas').hidden);
eq(a.figures.ts.hidden,false);eq(a.figures.T.hidden,true);
ui.comparador.seleccionarGrafica('T');eq(a.figures.T.hidden,false);
eq(Object.values(a.figures).filter(f=>!f.hidden).length,1,'Una gráfica a la vez');
eq(a.activeChart,'T','La exportación M50.1 queda vinculada a la gráfica visible');
ui.comparador.seleccionar('condiciones');ok(!a.conditions.parentNode.hidden);
ui.comparador.seleccionar('prestaciones');eq(a.lab.referencia,referencia);
// Enlaces cruzados operan mediante la navegación principal y no reinician nada.
const enlaces=a.body.querySelectorAll('.turbo-ana58-link');ok(enlaces.length>=4);
enlaces[0].click();eq(a.active,'simulacion');enlaces[1].click();eq(a.active,'comparador');
eq(a.lab.referencia,referencia);eq(a.fetches,0);
// Teclado y foco de la subnavegación.
const bt=ui.comparador.botones.get('prestaciones');
bt.dispatchEvent({type:'keydown',key:'ArrowRight',preventDefault(){}});
eq(ui.comparador.actual(),'graficas');ok(ui.comparador.botones.get('graficas')._focus);
for(const id of ['estudio49','turbo-study49-form','study49-chart','study49-apply'])
  eq(a.body.walk().filter(n=>n.id===id).length,1,'Sin duplicación de '+id);
ok(iniciarAnalisis50_8(a.doc,a.win)===null,'Inicialización idempotente');
const otro=fixture();otro.body.dataset.interfaz='clasico';
eq(iniciarAnalisis50_8(otro.doc,otro.win),null,'Ruta clásica sin modificar');
console.log(`M50.8 JavaScript: ${count} verificaciones correctas`);
