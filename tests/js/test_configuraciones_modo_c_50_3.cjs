const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {aplicarEjemplo50_3,iniciarConfiguraciones50_3}=require('../../static/configuraciones_modo_c_50_3.js');
const principal=fs.readFileSync(path.resolve(__dirname,'../../static/turborreactor_interactivo.js'),'utf8');
const ayuda=fs.readFileSync(path.resolve(__dirname,'../../static/configuraciones_modo_c_50_3.js'),'utf8');
function formFake(){
 const ids=['modo_caudal','mach','T3','tipo_tobera','area_garganta_fija','area_salida_fija','gasto_masico_aire'];
 const elements=Object.fromEntries(ids.map(id=>[id,{value:'',dispatchEvent(){this.events=(this.events||0)+1;}}]));
 const radios=[{value:'directo',checked:true,dispatchEvent(){this.events=(this.events||0)+1;}},
               {value:'ISA',checked:false,dispatchEvent(){this.events=(this.events||0)+1;}}];
 const controls={mach_deslizador:{value:''},T3_deslizador:{value:''},mach_lectura:{textContent:''},T3_lectura:{textContent:''}};
 return {elements,radios,controls,querySelectorAll:q=>q.includes('modo_ambiente')?radios:[],
   querySelector:q=>q.includes('modo_ambiente')?radios.find(x=>x.checked):null,
   ownerDocument:{getElementById:id=>controls[id]}};
}
test('configuración completa y sliders, sin emitir input de simulación',()=>{
 const form=formFake();const entradas={modo_caudal:'acoplado',modo_ambiente:'directo',
 mach:'0.4',T3:'1600',tipo_tobera:'convergente',area_garganta_fija:'0.047',
 area_salida_fija:'0.047',gasto_masico_aire:''};
 aplicarEjemplo50_3(form,entradas);
 assert.equal(form.elements.mach.value,'0.4');
 assert.equal(form.controls.mach_deslizador.value,'0.4');
 assert.equal(form.controls.T3_lectura.textContent,'1600 K');
 assert.equal(form.elements.tipo_tobera.events,1);
 assert.equal(form.radios[0].events,1);
 assert.equal(form.elements.mach.events,undefined);
});
test('rechazar un caso incompleto no altera controles',()=>{
 const form=formFake();form.elements.mach.value='0.8';
 assert.throws(()=>aplicarEjemplo50_3(form,{modo_caudal:'acoplado',mach:'0.4',desconocido:'0'}));
 assert.equal(form.elements.mach.value,'0.8');
});
test('solo una ruta de simulación; ayuda no usa red',()=>{
 assert.equal((principal.match(/fetcher\('\/api\/turborreactor\/simular'/g)||[]).length,1);
 assert.doesNotMatch(ayuda,/\bfetch\s*\(|\bXMLHttpRequest\b/);
 assert.match(principal,/iniciarConfiguraciones50_3\(documento,formulario,/);
 assert.match(principal,/controlador\.cambiar\(\); \/\/ Una sola solicitud/);
});
test('sin panel: salida segura',()=>{
 assert.equal(iniciarConfiguraciones50_3({getElementById:()=>null},{},()=>{}),null);
});
