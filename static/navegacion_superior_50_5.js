/* M50.5: navegación visual del banco interactivo; ninguna ecuación ni fetch. */
(function(raiz){
  'use strict';
  const ESPACIOS=['simulacion','motor','termodinamica','tobera','turbomaquinas','estudios','comparador'];
  const NOMBRES={simulacion:'Simulación',motor:'Motor',termodinamica:'Termodinámica',
    tobera:'Tobera',turbomaquinas:'Turbomáquinas',estudios:'Estudios',comparador:'Comparador'};
  function fragmento50_5(hash){
    const candidato=String(hash||'').replace(/^#espacio-/,'');
    return ESPACIOS.includes(candidato)?candidato:'simulacion';
  }
  function estadoFranja50_5(modo,mach,T3,estado,estadoInicial='pendiente'){
    const modos={impuesto:'A · Caudal impuesto',fijo:'B · Geometría fija',acoplado:'C · Motor acoplado'};
    const etiquetar=(v,unidad)=>v===null||v===undefined||String(v).trim()===''||
      !Number.isFinite(Number(v))?'—':String(v).trim()+(unidad?' '+unidad:'');
    const cod=estado||(estadoInicial==='resuelta'?'actualizado':estadoInicial);
    const estados={pendiente:['Pendiente','pendiente'],actualizando:['Calculando','calculando'],
      actualizado:['Resuelto','resuelto'],error:['Error','error'],
      'fuera-mapa':['Fuera del mapa','error']};
    const [texto,clase]=estados[cod]||['Pendiente','pendiente'];
    return {modo:modos[modo]||'—',mach:etiquetar(mach,''),T3:etiquetar(T3,'K'),
      estado:texto,clase};
  }
  function iniciarNavegacion50_5(documento,ventana){
    if(documento.body?.dataset.interfaz!=='interactivo')return null;
    const nav=documento.getElementById('turbo-work-nav50');
    const main=documento.getElementById('contenido');
    const form=documento.getElementById('turbo-form');
    const live=documento.getElementById('turbo-live');
    const enlaces=nav?[...nav.querySelectorAll('[data-workspace-view]')]:[];
    if(!nav||!main||!form||!live||enlaces.length!==ESPACIOS.length||
      !ESPACIOS.every((id,i)=>enlaces[i].dataset.workspaceView===id))return null;
    const referencia=main.querySelector('#configuracion');
    if(!referencia)return null;
    // Los nodos se MUEVEN (appendChild), nunca se copian: listeners, datos y
    // referencias privadas del laboratorio M50.1 permanecen intactos.
    const paneles={};
    ESPACIOS.forEach(id=>{
      const panel=documento.createElement('section');
      panel.className='turbo-work-panel50';panel.id='espacio-'+id;
      panel.setAttribute('aria-labelledby','titulo-espacio-'+id);
      panel.setAttribute('role','region');panel.setAttribute('tabindex','-1');
      const titulo=documento.createElement('h2');titulo.id='titulo-espacio-'+id;
      titulo.className='turbo-work-title50';titulo.textContent=NOMBRES[id];
      panel.appendChild(titulo); main.insertBefore(panel,referencia);
      paneles[id]=panel;
    });
    const anexar=(id,selector,plegable)=>{
      const nodo=documento.querySelector(selector);
      if(!nodo)return;
      nodo.hidden=false;
      if(!plegable){paneles[id].appendChild(nodo);return;}
      const details=documento.createElement('details');details.className='turbo-work-legacy50';
      const summary=documento.createElement('summary');summary.textContent=plegable;
      details.appendChild(summary);details.appendChild(nodo);paneles[id].appendChild(details);
    };
    anexar('simulacion','#configuracion');
    anexar('simulacion','#resultados','Resultados del informe y diagnósticos detallados');
    anexar('motor','.turbo-engine-educational');
    anexar('motor','.turbo-characterization');
    anexar('motor','#estaciones','Estaciones y tablas del informe');
    anexar('termodinamica','#graficas','Gráficas y fundamentos del informe');
    anexar('turbomaquinas','#turbo-diagnostic-50-2');
    anexar('estudios','#estudio49');
    anexar('estudios','#sensibilidad','Sensibilidad clásica (estudio HTTP)');
    anexar('estudios','#mapa','Mapas clásicos (estudio HTTP)');
    anexar('comparador','.turbo-lab50');
    // El visor compartido conserva su contenedor #turbo-live para que M48
    // encuentre los paneles SVG por sus selectores históricos.
    const origenLive=live.parentNode;
    const botonesGrafica=[...documento.querySelectorAll('[data-plot-group-button]')];
    const usarGrupo=(grupo)=>{
      const boton=botonesGrafica.find(b=>b.dataset.plotGroupButton===grupo);
      if(boton&&boton.getAttribute('aria-pressed')!=='true')boton.click();
    };
    const status={modo:documento.getElementById('turbo-work-mode50'),
      mach:documento.getElementById('turbo-work-mach50'),
      T3:documento.getElementById('turbo-work-t350'),
      estado:documento.getElementById('turbo-work-status50')};
    if(Object.values(status).some(v=>!v))return null;
    function actualizarContexto(){
      const valores=estadoFranja50_5(form.elements.modo_caudal?.value,
        form.elements.mach?.value,form.elements.T3?.value,live.dataset.estado,
        documento.body.dataset.simulacionInicial);
      for(const id of ['modo','mach','T3','estado'])status[id].textContent=valores[id];
      status.estado.dataset.estado=valores.clase;
    }
    let actual=null;
    function activar(espacio,{foco=false}={}){
      if(!ESPACIOS.includes(espacio))return false;
      // El navegador histórico también escucha popstate/hashchange: restaurar
      // los elementos trasladados tras su posible modificación de hidden.
      for(const id of ['configuracion','resultados','estaciones','graficas',
                       'estudio49','sensibilidad','mapa']){
        const nodo=documento.getElementById(id);if(nodo)nodo.hidden=false;
      }
      if(espacio==='termodinamica'||espacio==='tobera'){
        // El panel de gráficos viaja completo: los eventos registrados por
        // el controlador existente no se pierden, ni se realizan solicitudes.
        paneles[espacio].appendChild(live);
        usarGrupo(espacio==='tobera'?'tobera':'ciclo');
      }else if(live.parentNode!==origenLive){origenLive.appendChild(live);}
      if(espacio==='simulacion'){
        // El formulario puede haber quedado en la subvista educativa.
        documento.getElementById('turbo-configuracion-tab-uso')?.click();
      }
      for(const id of ESPACIOS)paneles[id].hidden=id!==espacio;
      enlaces.forEach(a=>{
        const esActual=a.dataset.workspaceView===espacio;
        if(esActual)a.setAttribute('aria-current','page');
        else a.removeAttribute('aria-current');
      });
      documento.body.dataset.activeWorkspace=espacio;
      actual=espacio;
      actualizarContexto();
      if(foco){
        const titulo=paneles[espacio].querySelector('h2');
        titulo?.focus({preventScroll:true});
        ventana.scrollTo?.({top:0,behavior:'instant'});
      }
      return true;
    }
    function navegar(espacio,{foco=true}={}){
      if(!ESPACIOS.includes(espacio))return false;
      const hash='#espacio-'+espacio;
      if(ventana.location.hash!==hash)ventana.history.pushState(null,'',hash);
      return activar(espacio,{foco});
    }
    function volverPorHistoria(){activar(fragmento50_5(ventana.location.hash),{foco:true});}
    enlaces.forEach((a,i)=>{
      a.addEventListener('click',evento=>{
        evento.preventDefault();navegar(a.dataset.workspaceView);
      });
      a.addEventListener('keydown',evento=>{
        const k=evento.key;const n=ESPACIOS.length;
        const siguiente=k==='ArrowRight'?(i+1)%n:k==='ArrowLeft'?(i+n-1)%n:
          k==='Home'?0:k==='End'?n-1:-1;
        if(siguiente<0)return;
        evento.preventDefault();enlaces[siguiente].focus();
      });
    });
    // M49.5 y M50.4 conservan los botones históricos como puente interno;
    // la visibilidad depende solo de este controlador.
    documento.addEventListener('click',evento=>{
      const boton=evento.target.closest?.('[data-study49-view]');
      if(!boton)return;
      evento.preventDefault();evento.stopPropagation();
      navegar(boton.dataset.study49View==='estudios'?'estudios':'simulacion');
    },true);
    ventana.addEventListener('popstate',volverPorHistoria);
    ventana.addEventListener('hashchange',volverPorHistoria);
    form.addEventListener('input',actualizarContexto);
    form.addEventListener('change',actualizarContexto);
    if(typeof ventana.MutationObserver==='function'){
      const observador=new ventana.MutationObserver(actualizarContexto);
      observador.observe(live,{attributes:true,attributeFilter:['data-estado']});
    }
    documento.body.classList.add('turbo-50-5-ready');
    activar(fragmento50_5(ventana.location.hash));
    return {activar,navegar,actualizarContexto,activo:()=>actual};
  }
  if(typeof module!=='undefined'&&module.exports){
    module.exports={ESPACIOS,fragmento50_5,estadoFranja50_5,iniciarNavegacion50_5};
  }
  raiz.iniciarNavegacion50_5=iniciarNavegacion50_5;
  if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',
    ()=>iniciarNavegacion50_5(document,raiz));
})(typeof window!=='undefined'?window:globalThis);
