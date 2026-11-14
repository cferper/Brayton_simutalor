/* M50.7: interacción sobre DOM de prueba sin navegador ni física. */
'use strict';
const assert=require('node:assert/strict');
const {iniciarNavegacion50_5,ESPACIOS}=require('../../static/navegacion_superior_50_5');
const {GRAFICAS,iniciarEspaciosIngenieria50_7}=require('../../static/espacios_ingenieria_50_7');
class Nodo{
  constructor(tag='div',id=''){
    this.tagName=tag.toUpperCase();this.id=id;this.children=[];this.parentNode=null;
    this.dataset={};this.attributes={};this.listeners={};this.hidden=false;
    this.className='';this.textContent='';this.style={};this.focused=false;
    this.classList={add:x=>{if(!this.className.split(/\s+/).includes(x))this.className+=' '+x;},
      contains:x=>this.className.split(/\s+/).includes(x)};
  }
  get parentElement(){return this.parentNode;}
  appendChild(x){if(x.parentNode)x.parentNode.children=x.parentNode.children.filter(n=>n!==x);
    this.children.push(x);x.parentNode=this;return x;}
  append(...xs){xs.forEach(x=>this.appendChild(x));}
  prepend(...xs){xs.forEach(x=>this.insertBefore(x,this.children[0]));}
  insertBefore(x,ref){if(x.parentNode)x.parentNode.children=x.parentNode.children.filter(n=>n!==x);
    const i=this.children.indexOf(ref);this.children.splice(i<0?this.children.length:i,0,x);x.parentNode=this;return x;}
  insertAdjacentElement(pos,x){assert.equal(pos,'afterend');const p=this.parentNode;
    const i=p.children.indexOf(this);p.insertBefore(x,p.children[i+1]);}
  remove(){if(this.parentNode)this.parentNode.children=this.parentNode.children.filter(n=>n!==this);this.parentNode=null;}
  setAttribute(k,v){this.attributes[k]=String(v);}
  getAttribute(k){return this.attributes[k]??null;}
  removeAttribute(k){delete this.attributes[k];}
  addEventListener(k,f){(this.listeners[k]??=[]).push(f);}
  fire(k,e={}){for(const f of this.listeners[k]||[])f(e);}
  dispatchEvent(event){this.fire(event.type,event);return true;}
  click(){this.fire('click',{preventDefault(){},stopPropagation(){}});}
  focus(){this.focused=true;}
  walk(){return this.children.flatMap(x=>[x,...x.walk()]);}
  matches(q){if(q==='.turbo-section')return this.className.split(/\s+/).includes('turbo-section');
    if(q.startsWith('.'))return this.className.split(/\s+/).includes(q.slice(1));
    if(q.startsWith('#'))return this.id===q.slice(1);
    if(q==='h2')return this.tagName==='H2';
    if(q==='[data-engine-part="tobera"]')return this.dataset.enginePart==='tobera';
    return false;
  }
  closest(q){for(let n=this;n;n=n.parentNode)if(n.matches(q))return n;return null;}
  querySelector(q){return this.walk().find(x=>x.matches(q))||null;}
  querySelectorAll(q){if(q==='[data-workspace-view]')return this.walk().filter(n=>n.dataset.workspaceView);
    return this.walk().filter(n=>n.matches(q));}
}
let checks=0;function ok(x,msg){assert.ok(x,msg);checks++;}
function eq(a,b,msg){assert.deepEqual(a,b,msg);checks++;}
function preparar(hashInicial='#espacio-simulacion'){
  const body=new Nodo('body'),main=new Nodo('main','contenido');
  body.dataset.interfaz='interactivo';body.dataset.simulacionInicial='pendiente';body.appendChild(main);
  const config=new Nodo('section','configuracion'),form=new Nodo('form','turbo-form');
  const live=new Nodo('div','turbo-live');live.dataset.estado='actualizado';
  form.elements={modo_caudal:{value:'acoplado'},mach:{value:'0.4'},T3:{value:'1600'}};
  main.appendChild(config);config.append(form,live);
  const engine=new Nodo('section');engine.className='turbo-engine-educational';live.appendChild(engine);
  const part=new Nodo('g');part.click=undefined;part.dataset.enginePart='tobera';part.addEventListener('click',()=>{part.seleccionado=true;});engine.appendChild(part);
  const ch=new Nodo('section');ch.className='turbo-characterization';live.appendChild(ch);
  const diagnosis=new Nodo('section','turbo-diagnostic-50-2');live.appendChild(diagnosis);
  const lab=new Nodo('section');lab.className='turbo-lab50';lab.referencia={id:37};live.appendChild(lab);
  const plots=new Nodo('div');plots.className='turbo-live-plot-viewer';live.appendChild(plots);
  const plotTabs=[];const groups=[];
  for(const grupo of ['ciclo','tobera','prestaciones','estudios']){
    const g=new Nodo('button');g.dataset.plotGroupButton=grupo;g.setAttribute('aria-pressed',String(grupo==='ciclo'));
    groups.push(g);plots.appendChild(g);
    g.addEventListener('click',()=>{groups.forEach(b=>b.setAttribute('aria-pressed',String(b===g)));});
  }
  for(const [clave,grupo] of [
    ['ts','ciclo'],['temperaturas','ciclo'],['presiones','ciclo'],['trabajos','ciclo'],['balance','ciclo'],
    ['mach','tobera'],['presion','tobera'],['temperatura_tobera','tobera'],['velocidad_tobera','tobera'],['geometria','tobera']]){
    const b=new Nodo('button');b.dataset.plotTab=clave;b.dataset.plotGroup=grupo;
    b.setAttribute('aria-selected',String(clave==='ts'));plotTabs.push(b);plots.appendChild(b);
    b.addEventListener('click',()=>{plotTabs.forEach(x=>x.setAttribute('aria-selected',String(x===b)));});
  }
  for(const id of ['resultados','estaciones','graficas','estudio49','sensibilidad','mapa']){
    const x=new Nodo('section',id);x.className='turbo-section';main.appendChild(x);
  }
  const nav=new Nodo('nav','turbo-work-nav50');body.appendChild(nav);
  const links=ESPACIOS.map(id=>{const a=new Nodo('a');a.dataset.workspaceView=id;nav.appendChild(a);return a;});
  for(const id of ['turbo-work-mode50','turbo-work-mach50','turbo-work-t350','turbo-work-status50'])
    body.appendChild(new Nodo('span',id));
  body.appendChild(new Nodo('button','turbo-configuracion-tab-uso'));
  const eventWindows={},location={hash:hashInicial},calls=[],observadores=[];
  const win={location,history:{pushState(_x,_y,h){calls.push(h);location.hash=h;}},
    addEventListener:(k,f)=>eventWindows[k]=f,scrollTo(){},
    MutationObserver:class{constructor(f){observadores.push(f);}observe(){}}};
  const eventoDoc={};
  const doc={body,getElementById:k=>body.walk().find(n=>n.id===k)||null,
    querySelector:q=>body.querySelector(q),
    querySelectorAll:q=>q==='[data-plot-group-button]'?groups:q==='[data-plot-tab]'?plotTabs:body.querySelectorAll(q),
    createElement:tag=>new Nodo(tag),
    addEventListener:(k,f)=>(eventoDoc[k]??=[]).push(f)};
  return {body,main,form,live,engine,ch,diagnosis,lab,part,doc,win,links,calls,groups,plotTabs,observadores};
}
const r=preparar();const nav=iniciarNavegacion50_5(r.doc,r.win);
// Equivalente a la asignación en DOMContentLoaded del módulo 50.5.
r.win.controladorNavegacion50_5=nav;
ok(nav,'Navegación 50.5 inicializada');
const x=iniciarEspaciosIngenieria50_7(r.doc,r.win);
ok(x,'Paneles 50.7 creados');
eq(Object.keys(x.vistas).length,4);
ok(r.body.classList.contains('turbo-50-7-ready'));
for(const id of ['motor','termodinamica','tobera','turbomaquinas']){
  const panel=r.doc.getElementById('espacio-'+id);
  ok(panel,'Existe '+id);
  ok(panel.querySelector('.turbo-ing57-subnav'),'Subnavegación de '+id);
}
eq(r.engine,x.vistas.motor.contenedores.get('componentes'),'Esquema único en Motor');
eq(r.ch,x.vistas.turbomaquinas.contenedores.get('eje'),'Caracterización solo en Turbomáquinas');
eq(r.diagnosis,x.vistas.turbomaquinas.contenedores.get('compresor'),'Mapa HPC único');
ok(r.doc.getElementById('estaciones')===x.vistas.motor.contenedores.get('estaciones'));
nav.navegar('motor');eq(nav.activo(),'motor');
x.vistas.motor.seleccionar('estaciones');
ok(!r.doc.getElementById('estaciones').hidden,'Estaciones visibles');
ok(r.engine.hidden,'Esquema oculto');
nav.navegar('termodinamica');
eq(r.live.parentNode,x.hosts.termodinamica,'M50.5 ha movido el visor a Termodinámica');
x.vistas.termodinamica.seleccionar('balance');
eq(r.plotTabs.find(p=>p.getAttribute('aria-selected')==='true').dataset.plotTab,'balance');
x.vistas.termodinamica.seleccionar('informe');
ok(x.hosts.termodinamica.parentNode.hidden,'Solo informe visible, visor oculto');
ok(!r.doc.getElementById('graficas').hidden,'Informe accesible');
nav.navegar('tobera');
eq(r.live.parentNode,x.hosts.tobera,'M50.5 ha movido el mismo visor a Tobera');
x.vistas.tobera.seleccionar('geometria');
const geometria=r.plotTabs.find(b=>b.dataset.plotTab==='geometria');
r.plotTabs.find(b=>b.dataset.plotTab==='mach').click();
r.observadores.at(-1)();
eq(geometria.getAttribute('aria-selected'),'true','La subvista se restaura tras actualizar el motor');
eq(r.plotTabs.find(p=>p.getAttribute('aria-selected')==='true').dataset.plotTab,'geometria');
nav.navegar('simulacion');
eq(r.live.parentNode,r.doc.getElementById('configuracion'),'Se restaura visor original');
eq(r.form.elements.mach.value,'0.4');
eq(r.lab.referencia.id,37,'Referencia 50.1 intacta');
nav.navegar('tobera');eq(x.vistas.tobera.actual(),'geometria','Pestaña secundaria recordada');
nav.navegar('motor');
ok(r.doc.getElementById('estaciones').hidden===false,'Visibilidad controlada por selección Motor');
const sub=x.vistas.motor.botones.get('componentes');
sub.fire('keydown',{key:'ArrowRight',preventDefault(){}});
eq(x.vistas.motor.actual(),'estaciones','Flechas entre vistas');
ok(x.vistas.motor.botones.get('estaciones').focused,'Foco en nueva pestaña');
x.vistas.tobera.botones.get('funcionamiento').click();
const link=x.vistas.tobera.contenedores.get('funcionamiento').querySelector('.turbo-ing57-link');
link.click();eq(nav.activo(),'motor','Enlace a ficha Tobera');eq(x.vistas.motor.actual(),'componentes','Ficha visible desde enlace');ok(r.part.seleccionado,'Componente real seleccionado');
for(const id of ['turbo-live','turbo-form','turbo-diagnostic-50-2','estaciones','graficas'])
  eq(r.body.walk().filter(n=>n.id===id).length,1,'Un solo '+id);
const contar=()=>r.win.history.calls||r.calls;
const antes=r.calls.length;
x.vistas.termodinamica.seleccionar('ts');
eq(r.calls.length,antes,'Sin historia nueva ni navegación al cambiar subvista');
ok(!GRAFICAS.termodinamica.some(([c])=>c==='maquinaria'),'No se inventan representaciones');
assert.equal(iniciarEspaciosIngenieria50_7(r.doc,r.win),null);
// Recarga con enlace directo: el visor se recoloca en el host sin recrearlo.
for(const destino of ['termodinamica','tobera']){
  const d=preparar('#espacio-'+destino);
  const navegador=iniciarNavegacion50_5(d.doc,d.win);
  d.win.controladorNavegacion50_5=navegador;
  const nuevo=iniciarEspaciosIngenieria50_7(d.doc,d.win);
  eq(navegador.activo(),destino,'Enlace profundo válido '+destino);
  eq(d.live.parentNode,nuevo.hosts[destino], 'Reubicación inicial '+destino);
  ok(!d.live.hidden,'El visor original permanece disponible');
}
console.log('M50.7 JS: '+checks+' comprobaciones correctas');
