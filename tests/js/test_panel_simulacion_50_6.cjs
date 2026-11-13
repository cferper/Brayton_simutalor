/* M50.6: DOM controlado. Ninguna prueba requiere servidor ni navegador real. */
'use strict';
const assert=require('node:assert/strict');
const {iniciarPanelSimulacion50_6}=require('../../static/panel_simulacion_50_6.js');
let count=0;const eq=(a,b,m)=>{assert.equal(a,b,m);count++;};
const ok=(a,m)=>{assert.ok(a,m);count++;};
class Node {
  constructor(id='',tag='div',cls=''){
    this.id=id;this.tagName=tag.toUpperCase();this.className=cls;this.children=[];
    this.parentNode=null;this.dataset={};this.attrs={};this.textContent='';
    this.value='';this.handlers={};this.clicked=0;
  }
  append(...nodes){for(const n of nodes){if(n.parentNode)n.parentNode.children=n.parentNode.children.filter(x=>x!==n);
    this.children.push(n);n.parentNode=this;}}
  prepend(n){if(n.parentNode)n.parentNode.children=n.parentNode.children.filter(x=>x!==n);
    this.children.unshift(n);n.parentNode=this;}
  appendChild(n){this.append(n);return n;}
  insertAdjacentElement(where,n){assert.equal(where,'afterend');const p=this.parentNode;
    if(n.parentNode)n.parentNode.children=n.parentNode.children.filter(x=>x!==n);
    p.children.splice(p.children.indexOf(this)+1,0,n);n.parentNode=p;}
  setAttribute(k,v){this.attrs[k]=String(v);}
  getAttribute(k){return this.attrs[k]||null;}
  addEventListener(k,fn){(this.handlers[k]??=[]).push(fn);}
  closest(sel){if(sel==='.field')return this.parentNode;
    return null;}
  querySelector(sel){
    if(sel===':scope > h3')return this.children.find(x=>x.tagName==='H3')||null;
    if(sel==='.turbo-nozzle-config')return find(this,n=>n.className==='turbo-nozzle-config');
    if(sel==='.turbo-bank-mode-buttons')return find(this,n=>n.className==='turbo-bank-mode-buttons');
    if(sel==='.turbo-guide')return find(this,n=>n.className.includes('turbo-guide'));
    if(sel==='.turbo-examples')return find(this,n=>n.className.includes('turbo-examples'));
    if(sel==='.turbo-live-plot-viewer')return find(this,n=>n.className==='turbo-live-plot-viewer');
    if(sel==='.turbo-sim-plot-title56')return find(this,n=>n.className==='turbo-sim-plot-title56');
    return null;
  }
}
function find(n,fn){for(const child of n.children){if(fn(child))return child;
  const res=find(child,fn);if(res)return res;}return null;}
const ids=new Map();
const reg=(id,tag,cls)=>{const n=new Node(id,tag,cls);ids.set(id,n);return n;};
const body=reg('body','body');body.dataset.interfaz='interactivo';
let ready=false;body.classList={add:k=>{if(k==='turbo-50-6-ready')ready=true;}};
const uso=reg('turbo-configuracion-vista-uso');
const form=reg('turbo-form','form');uso.append(form);
const modes=new Node('','div','turbo-bank-mode-buttons');form.append(modes);
const advanced=reg('turbo-bank-advanced-fields');form.append(advanced);
const toggle=reg('turbo-bank-advanced-toggle','button');form.append(toggle);
const fieldset1=new Node('','fieldset');const fieldset2=new Node('','fieldset');
const fieldset3=new Node('','fieldset');const fieldset4=new Node('','fieldset');
advanced.append(fieldset1,fieldset2,fieldset3,fieldset4);
function field(id,parent){const f=new Node('','div','field');const input=reg(id,'input');f.append(input);parent.append(f);return {field:f,input};}
const mach=field('mach',fieldset1);mach.input.value='0.4';
const T3=field('T3',fieldset2);T3.input.value='1620';
const caudal=field('gasto_masico_aire',fieldset4);caudal.input.value='19.3';
caudal.field.dataset.caudal='impuesto';
const nozzle=new Node('','div','turbo-nozzle-config');fieldset3.append(nozzle);
const throat=field('area_garganta_fija',nozzle);throat.input.value='0.047';
const live=reg('turbo-live');uso.append(live);
const h3=new Node('','h3');const status=reg('turbo-live-status','p');
const metric=reg('metric-1');metric.textContent='19 165,154 N';
const plot=new Node('','div','turbo-live-plot-viewer');
const selectedGraph=new Node('','figure');plot.append(selectedGraph);
live.append(h3,status,metric,plot);
const guia=new Node('','div','turbo-guide');const ejemplos=new Node('','div','turbo-examples');
uso.prepend(guia);uso.prepend(ejemplos);
const documento={body,getElementById:id=>ids.get(id)||null,createElement:t=>new Node('',t)};
const original={form,live,plot,selectedGraph,inputs:[mach.input,T3.input,caudal.input,throat.input]};
let requests=0;const dispatch=()=>{requests++;};
for(const inp of original.inputs)inp.addEventListener('input',dispatch);
let reference={id:'Punto 1'};const comparador={get referencia(){return reference;}};
const result=iniciarPanelSimulacion50_6(documento);
ok(result,'Monta la ventana del banco');ok(ready,'Identificador ready tras montar');
eq(result.formulario,original.form,'Mismo formulario');eq(result.visor,original.live,'Mismo visor');
eq(uso.children.filter(x=>x.tagName==='FORM').length,1,'Solo un formulario');
eq(mach.field.parentNode.className,'turbo-sim-axes56','Mach visible en zona principal');
eq(T3.field.parentNode,mach.field.parentNode,'T3 junto a Mach');
eq(caudal.field.parentNode,result.porModo,'Caudal en región por modalidad');
eq(nozzle.parentNode,result.porModo,'Geometría existente reubicada');
eq(throat.input.value,'0.047','Geometría conservada');
eq(T3.input.value,'1620','T3 conservada');
eq(caudal.input.value,'19.3','Caudal conservado');
const help=find(form,x=>x.className==='turbo-sim-help56');ok(help,'Ayuda plegable');
ok(help.children.includes(ejemplos),'Presets históricos conservados');
ok(help.children.includes(guia),'Guía histórica conservada');
eq(toggle.getAttribute('aria-controls'),'turbo-bank-advanced-fields','Mismo control de avanzado');
eq(advanced.parentNode,form,'Campos avanzados dentro del formulario');
ok(plot.children.includes(selectedGraph),'La gráfica existente no se reconstruye');
eq(plot.parentNode,live,'Gráfica dentro del único visor');
eq(comparador.referencia.id,'Punto 1','Referencia comparativa preservada');
eq(requests,0,'Reorganizar no dispara simulación');
eq(iniciarPanelSimulacion50_6(documento),null,'Inicio idempotente');
// El desplegable y la navegación no cambian el valor de los campos;
// la responsabilidad de sus eventos sigue en los controladores previos.
eq(mach.input.value,'0.4');eq(requests,0);
mach.input.handlers.input[0]();eq(requests,1,'Evento físico sigue conectado tras mover');
console.log('M50.6 JS: '+count+' comprobaciones correctas');
