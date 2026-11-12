/* Contratos y DOM mínimo M50.5, sin navegador ni servidor. */
'use strict';
const assert=require('node:assert/strict');
const {ESPACIOS,fragmento50_5,estadoFranja50_5,iniciarNavegacion50_5}=require('../../static/navegacion_superior_50_5.js');
class Nodo{
  constructor(id='',tag='div'){
    this.id=id;this.tagName=tag.toUpperCase();this.children=[];this.dataset={};
    this.hidden=false;this.attributes={};this.listeners={};this.parentNode=null;
    this.textContent='';this.className='';this.style={};this.focused=false;
    this.classList={add:x=>{this.className+=(this.className?' ':'')+x;}};
  }
  appendChild(n){if(n.parentNode)n.parentNode.children=n.parentNode.children.filter(x=>x!==n);
    this.children.push(n);n.parentNode=this;return n;}
  insertBefore(n,ref){if(n.parentNode)n.parentNode.children=n.parentNode.children.filter(x=>x!==n);
    const i=this.children.indexOf(ref);this.children.splice(i<0?this.children.length:i,0,n);
    n.parentNode=this;return n;}
  setAttribute(k,v){this.attributes[k]=String(v);}
  getAttribute(k){return this.attributes[k]||null;}
  removeAttribute(k){delete this.attributes[k];}
  addEventListener(k,fn){(this.listeners[k]??=[]).push(fn);}
  fire(k,e={}){for(const fn of this.listeners[k]||[])fn(e);}
  click(){this.fire('click',{preventDefault(){}});}
  focus(){this.focused=true;}
  querySelector(q){if(q==='h2')return this.children.find(x=>x.tagName==='H2')||null;
    const visit=n=>{for(const c of n.children){if(q[0]==='#'&&c.id===q.slice(1))return c;
      const nested=visit(c);if(nested)return nested;}return null;};return visit(this);}
  querySelectorAll(q){if(q==='[data-workspace-view]')return this.links||[];return [];}
}
const registrar=(map,id,tag)=>{const x=new Nodo(id,tag);map['#'+id]=x;return x;};
const obtener=()=>{
  const map={};const body=new Nodo('','body');body.dataset.interfaz='interactivo';
  body.dataset.simulacionInicial='pendiente';
  const main=registrar(map,'contenido','main'),config=registrar(map,'configuracion','section');
  main.appendChild(config);
  const form=registrar(map,'turbo-form','form');
  form.elements={modo_caudal:{value:'acoplado'},mach:{value:'0.4'},T3:{value:'1600'}};
  config.appendChild(form);
  const live=registrar(map,'turbo-live');live.dataset.estado='actualizado';config.appendChild(live);
  for(const id of ['resultados','estaciones','graficas','estudio49','sensibilidad','mapa']){
    const el=registrar(map,id,'section');main.appendChild(el);
  }
  for(const [sel,id] of [['.turbo-engine-educational','engine'],['.turbo-characterization','char'],
    ['#turbo-diagnostic-50-2','turbo-diagnostic-50-2'],['.turbo-lab50','lab']]){
    const el=sel[0]==='#'?registrar(map,id):new Nodo(id);map[sel]=el;live.appendChild(el);
  }
  const nav=registrar(map,'turbo-work-nav50','nav');nav.links=ESPACIOS.map(id=>{
    const a=new Nodo('','a');a.dataset.workspaceView=id;return a;
  });
  for(const id of ['turbo-work-mode50','turbo-work-mach50','turbo-work-t350','turbo-work-status50'])registrar(map,id);
  const graph={};
  for(const id of ['ciclo','tobera']){
    const a=new Nodo('','button');a.dataset.plotGroupButton=id;
    a.setAttribute('aria-pressed',id==='ciclo'?'true':'false');
    a.addEventListener('click',()=>{for(const x of Object.values(graph))
      x.setAttribute('aria-pressed',String(x===a));});graph[id]=a;
  }
  map['#turbo-configuracion-tab-uso']=new Nodo('','button');
  const listeners={};const documento={body,
    getElementById:k=>map['#'+k]||null,
    querySelector:k=>map[k]||null,
    querySelectorAll:k=>k==='[data-plot-group-button]'?Object.values(graph):[],
    createElement:k=>new Nodo('',k),
    addEventListener:(k,fn,captura)=>{(listeners[k]??=[]).push({fn,captura});},
    fire:(k,e)=>{for(const x of listeners[k]||[])x.fn(e);}
  };
  const eventos={};const location={hash:'#espacio-simulacion'};
  const ventana={location,history:{calls:[],pushState(_a,_b,hash){
    this.calls.push(hash);location.hash=hash;}},
    addEventListener:(k,fn)=>{eventos[k]=fn;},
    scrollTo:()=>{},
    MutationObserver:class{constructor(fn){this.fn=fn;}observe(node,opts){
      this.node=node;this.opts=opts;ventana.observer=this;}}
  };
  return {map,body,main,form,live,nav,documento,ventana,eventos,graph};
};
let n=0;const ok=(expr,why)=>{assert.ok(expr,why);n++;};
const eq=(a,b,why)=>{assert.deepEqual(a,b,why);n++;};
eq(ESPACIOS.length,7,'Siete vistas');
eq(fragmento50_5('#espacio-motor'),'motor','Fragmento directo');
eq(fragmento50_5('#desconocido'),'simulacion','Fragmento desconocido');
eq(estadoFranja50_5('acoplado','0.4','1600','actualizado').estado,'Resuelto');
eq(estadoFranja50_5('fijo','','',null).mach,'—','Dato ausente, no cero');
const r=obtener();const c=iniciarNavegacion50_5(r.documento,r.ventana);
ok(Boolean(c),'Inicialización');
for(const id of ESPACIOS)r.map['#espacio-'+id]=r.main.children.find(x=>x.id==='espacio-'+id);
eq(c.activo(),'simulacion');
eq(r.map['#turbo-work-mode50'].textContent,'C · Motor acoplado');
eq(r.map['#turbo-work-t350'].textContent,'1600 K');
ok(r.body.className.includes('turbo-50-5-ready'),'Ready solo tras montar');
const lab=r.map['.turbo-lab50'];lab.referencia={id:1};
c.navegar('comparador');eq(c.activo(),'comparador');
ok(lab.parentNode===r.map['#espacio-comparador'],'Mismo laboratorio, sin clonar');
eq(lab.referencia.id,1,'Referencia preservada');
eq(r.ventana.history.calls.at(-1),'#espacio-comparador');
eq(Object.values(Object.fromEntries(ESPACIOS.map(x=>[x,r.map['#espacio-'+x].hidden]))).filter(v=>!v).length,1,'Solo una vista');
c.navegar('termodinamica');ok(r.live.parentNode===r.map['#espacio-termodinamica'],'Live completo en Termodinámica');
eq(r.graph.ciclo.getAttribute('aria-pressed'),'true');
c.navegar('tobera');ok(r.live.parentNode===r.map['#espacio-tobera'],'Live completo en Tobera');
eq(r.graph.tobera.getAttribute('aria-pressed'),'true');
c.navegar('simulacion');ok(r.live.parentNode===r.map['#configuracion'],'Live restaurado sin clonar');
eq(r.form.elements.mach.value,'0.4','No cambia Mach');
r.live.dataset.estado='actualizando';r.ventana.observer.fn();
eq(r.map['#turbo-work-status50'].textContent,'Calculando');
r.live.dataset.estado='error';r.ventana.observer.fn();
eq(r.map['#turbo-work-status50'].textContent,'Error');
r.live.dataset.estado='pendiente';r.ventana.observer.fn();
eq(r.map['#turbo-work-status50'].textContent,'Pendiente');
r.form.elements.T3.value='1550';r.form.fire('input');
eq(r.map['#turbo-work-t350'].textContent,'1550 K');
r.ventana.location.hash='#espacio-estudios';r.eventos.popstate();
eq(c.activo(),'estudios','Historial restaurado');
const e={target:{closest:q=>q==='[data-study49-view]'?{dataset:{study49View:'punto'}}:null},
 preventDefault(){this.prevented=true;},stopPropagation(){this.stopped=true;}};
r.documento.fire('click',e);eq(c.activo(),'simulacion','Puente del explorador');ok(e.stopped,'No dispara navegación antigua');
r.nav.links[0].fire('keydown',{key:'ArrowRight',preventDefault(){this.prevented=true;}});
ok(r.nav.links[1].focused,'Flecha mueve foco entre enlaces');
console.log('M50.5 JS: '+n+' comprobaciones correctas');
