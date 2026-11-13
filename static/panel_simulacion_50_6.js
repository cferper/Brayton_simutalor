/* M50.6 — distribución de Simulación. Recoloca nodos, no entradas ni cálculos. */
(function(raiz){
  'use strict';
  function iniciarPanelSimulacion50_6(documento){
    if(documento.body?.dataset.interfaz!=='interactivo')return null;
    const form=documento.getElementById('turbo-form');
    const uso=documento.getElementById('turbo-configuracion-vista-uso');
    const live=documento.getElementById('turbo-live');
    const avanzado=documento.getElementById('turbo-bank-advanced-fields');
    const controlAvanzado=documento.getElementById('turbo-bank-advanced-toggle');
    const modos=form?.querySelector('.turbo-bank-mode-buttons');
    if(!form||!uso||!live||!avanzado||!controlAvanzado||!modos||form.dataset.simPanel56)return null;
    const mach=documento.getElementById('mach')?.closest('.field');
    const T3=documento.getElementById('T3')?.closest('.field');
    const caudal=documento.getElementById('gasto_masico_aire')?.closest('.field');
    const tobera=form.querySelector('.turbo-nozzle-config');
    if(!mach||!T3||!caudal||!tobera)return null;
    // Los controladores M48 y M50.3 guardan referencias a estos nodos. Mover
    // con appendChild conserva todos los listeners, valores y atributos data-*.
    const principales=documento.createElement('section');
    principales.className='turbo-sim-primary56';
    principales.setAttribute('aria-label','Condiciones principales del motor');
    const titulo=documento.createElement('h4');titulo.textContent='Condiciones de funcionamiento';
    const ejes=documento.createElement('div');ejes.className='turbo-sim-axes56';
    ejes.append(mach,T3);principales.append(titulo,ejes);
    modos.insertAdjacentElement('afterend',principales);
    const porModo=documento.createElement('section');
    porModo.className='turbo-sim-mode56';
    porModo.setAttribute('aria-label','Caudal y geometría del modo seleccionado');
    const tituloModo=documento.createElement('h4');tituloModo.textContent='Caudal y tobera';
    porModo.append(tituloModo,caudal,tobera);
    principales.insertAdjacentElement('afterend',porModo);
    const nota=documento.createElement('p');nota.className='turbo-sim-magnitude56';
    nota.textContent='Mach [–] y T3 [K] son entradas. Caudal, empuje y rpm solo aparecen cuando el modelo puede resolverlos.';
    principales.append(nota);
    // Mantener ejemplos históricos y ayuda, pero fuera del recorrido habitual.
    const guia=uso.querySelector('.turbo-guide');
    const ejemplos=uso.querySelector('.turbo-examples');
    if(guia||ejemplos){
      const ayuda=documento.createElement('details');ayuda.className='turbo-sim-help56';
      const sum=documento.createElement('summary');sum.textContent='Guía y ejemplos de uso';
      ayuda.append(sum);if(ejemplos)ayuda.append(ejemplos);if(guia)ayuda.append(guia);
      form.appendChild(ayuda);
    }
    // El estado y la galería siguen perteneciendo al único #turbo-live. La
    // navegación M50.5 puede trasladarlo a Termodinámica/Tobera y devolverlo.
    const cabecera=live.querySelector(':scope > h3');
    if(cabecera)cabecera.textContent='Resultados principales · punto motor';
    const galeria=live.querySelector('.turbo-live-plot-viewer');
    if(galeria&&!galeria.querySelector('.turbo-sim-plot-title56')){
      const h=documento.createElement('h4');h.className='turbo-sim-plot-title56';
      h.textContent='Visualización principal';galeria.prepend(h);
    }
    // El control histórico M48 gestiona el desplegable mediante classList.
    // No agregamos otro listener de clic ni eventos input/change.
    controlAvanzado.setAttribute('aria-controls','turbo-bank-advanced-fields');
    avanzado.setAttribute('aria-label','Parámetros avanzados y condiciones ambientales');
    form.dataset.simPanel56='activo';
    documento.body.classList.add('turbo-50-6-ready');
    return {formulario:form,visor:live,principales,porModo};
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={iniciarPanelSimulacion50_6};
  raiz.iniciarPanelSimulacion50_6=iniciarPanelSimulacion50_6;
  if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',()=>iniciarPanelSimulacion50_6(document));
})(typeof window!=='undefined'?window:globalThis);
