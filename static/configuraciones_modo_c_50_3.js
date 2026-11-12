/* M50.3: ejemplos validados por el backend; las selecciones no resuelven física. */
(function(raiz){
  'use strict';
  function aplicarEjemplo50_3(formulario,entradas){
    if(!entradas||entradas.modo_caudal!=='acoplado')
      throw new Error('La configuración no pertenece al modo C.');
    // Primero se comprueba que todos los campos existen, antes de escribir nada.
    const claves=Object.keys(entradas);
    for(const clave of claves){
      if(clave==='modo_ambiente')continue;
      if(!formulario.elements[clave])throw new Error('Falta el campo '+clave+'.');
    }
    for(const clave of claves){
      if(clave==='modo_ambiente'){
        formulario.querySelectorAll('input[name="modo_ambiente"]').forEach(r=>{
          r.checked=r.value===entradas.modo_ambiente;
        });
      }else formulario.elements[clave].value=String(entradas[clave]);
    }
    // Disparar eventos sin propagación, para sincronizar visibilidad de ambiente
    // y tobera en el JS anterior, sin programar simulaciones duplicadas.
    const ambiente=formulario.querySelector('input[name="modo_ambiente"]:checked');
    ambiente?.dispatchEvent(new Event('change',{bubbles:false}));
    formulario.elements.tipo_tobera.dispatchEvent(new Event('change',{bubbles:false}));
    for(const [campo,unidad] of [['mach','–'],['T3','K']]){
      const numero=formulario.elements[campo];
      const slider=formulario.ownerDocument.getElementById(campo+'_deslizador');
      const lectura=formulario.ownerDocument.getElementById(campo+'_lectura');
      if(slider)slider.value=numero.value;
      if(lectura)lectura.textContent=numero.value+' '+unidad;
    }
    return entradas;
  }
  function iniciarConfiguraciones50_3(documento,formulario,onAplicar){
    const raizPanel=documento.getElementById('turbo-configuraciones-c-50-3');
    if(!raizPanel)return null;
    const contenido=documento.getElementById('turbo-configuraciones-c-datos');
    const selector=raizPanel.querySelector('[data-c-example]');
    const estado=raizPanel.querySelector('[data-c-help]');
    const error=raizPanel.querySelector('[data-c-error]');
    let ejemplos;
    try{ejemplos=JSON.parse(contenido.textContent);}catch(_e){ejemplos=[];}
    const porClave=new Map(ejemplos.map(e=>[e.id,e]));
    function cargar(clave){
      if(formulario.elements.modo_caudal.value!=='acoplado')return false;
      const caso=porClave.get(clave);
      if(!caso)return false;
      aplicarEjemplo50_3(formulario,caso.entradas);
      estado.textContent=caso.nombre+': '+caso.descripcion+' Se ejecuta el cálculo habitual.';
      error.textContent='';
      selector.value=clave;
      onAplicar();
      return true;
    }
    selector.addEventListener('change',()=>cargar(selector.value));
    raizPanel.querySelector('[data-c-reset]').addEventListener('click',()=>cargar('diseno'));
    function diagnosticar(fallo){
      if(formulario.elements.modo_caudal.value!=='acoplado')return;
      const d=fallo?.diagnostico_50_3;
      error.textContent=d
        ?d.resumen+' '+d.recomendacion
        :'Sin resultado verificado. Recupera el punto de diseño C y modifica una entrada cada vez; no se ha determinado la causa física.';
    }
    function modificada(){
      selector.value='';
      estado.textContent='Configuración modificada manualmente; ya no corresponde íntegramente a un ejemplo comprobado.';
    }
    function exito(){error.textContent='Punto C calculado; puedes variar Mach, T3 u otra entrada.';}
    function pendiente(){error.textContent='Esperando el cálculo actualizado. Los datos anteriores no son vigentes.';}
    return {cargar,diagnosticar,exito,pendiente,modificada};
  }
  raiz.iniciarConfiguraciones50_3=iniciarConfiguraciones50_3;
  if(typeof module!=='undefined'&&module.exports)
    module.exports={aplicarEjemplo50_3,iniciarConfiguraciones50_3};
})(typeof window!=='undefined'?window:globalThis);
