/* M50.8 — reorganización de Estudios y Comparador sin duplicar datos ni fetch.
   M50.5 es el único propietario de la navegación principal; M49.5 y M50.1
   siguen calculando/presentando sus datos mediante sus propios controladores. */
(function(raiz){
  'use strict';
  const ETIQUETAS_ESTUDIOS=[['barridos','Barridos Mach / T3'],['mapa','Mapa Mach–T3'],
    ['clasicos','Sensibilidad y mapas clásicos']];
  const ETIQUETAS_COMPARADOR=[['prestaciones','Prestaciones'],['graficas','Gráficas comparativas'],
    ['condiciones','Condiciones']];
  const ETIQUETAS_GRAFICAS=[['ts','T–s'],['T','Temperaturas'],['p','Presiones'],
    ['prestaciones','Prestaciones']];

  function iniciarAnalisis50_8(documento,ventana=raiz){
    if(documento.body?.dataset.interfaz!=='interactivo'||
       !documento.body.classList.contains('turbo-50-5-ready')||
       documento.body.classList.contains('turbo-50-8-ready'))return null;
    const estudios=documento.getElementById('espacio-estudios');
    const comparador=documento.getElementById('espacio-comparador');
    const estudio=documento.getElementById('estudio49');
    const forma=documento.getElementById('turbo-study49-form');
    const tipo=documento.getElementById('study49-tipo');
    const grafico=documento.getElementById('study49-chart');
    const detalle=estudio?.querySelector('.study49-point');
    const lab=comparador?.querySelector('.turbo-lab50');
    if(!estudios||!comparador||!estudio||!forma||!tipo||!grafico||!detalle||!lab||
       !ventana.controladorNavegacion50_5)return null;
    const crear=(tag,clase='',contenido='')=>{
      const e=documento.createElement(tag);e.className=clase;
      if(contenido)e.textContent=contenido;return e;
    };
    const navegacion=(id)=>ventana.controladorNavegacion50_5.navegar(id);
    function atajo(destino,texto){
      const b=crear('button','turbo-ana58-link',texto);b.type='button';
      b.addEventListener('click',()=>navegacion(destino));return b;
    }
    function pestañas(padre,config,clase='turbo-ana58',solicitar=null){
      const barra=crear('div',clase+'-tabs');barra.setAttribute('role','tablist');
      barra.setAttribute('aria-label',clase==='turbo-ana58'?'Vistas de Estudios':'Vistas de comparación');
      const paneles=new Map(),botones=new Map();let activa=null;
      for(const [clave,nombre] of config){
        const boton=crear('button',clase+'-tab',nombre);boton.type='button';
        boton.id=clase+'-tab-'+clave;boton.setAttribute('role','tab');
        boton.setAttribute('aria-controls',clase+'-vista-'+clave);
        const panel=crear('section',clase+'-vista');panel.id=clase+'-vista-'+clave;
        panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby',boton.id);
        boton.setAttribute('aria-selected','false');boton.tabIndex=-1;panel.hidden=true;
        barra.appendChild(boton);paneles.set(clave,panel);botones.set(clave,boton);
      }
      padre.appendChild(barra);
      for(const panel of paneles.values())padre.appendChild(panel);
      const claves=config.map(([clave])=>clave);
      function seleccionar(clave,{foco=false}={}){
        if(!paneles.has(clave))return false;
        activa=clave;
        for(const [k,p] of paneles)p.hidden=k!==clave;
        for(const [k,b] of botones){b.setAttribute('aria-selected',String(k===clave));b.tabIndex=k===clave?0:-1;}
        if(foco)botones.get(clave).focus();return true;
      }
      claves.forEach((k,i)=>{
        const b=botones.get(k);
        b.addEventListener('click',()=>solicitar?solicitar(k):seleccionar(k));
        b.addEventListener('keydown',evento=>{
          const v=evento.key, n=claves.length;
          const j=v==='ArrowRight'?(i+1)%n:v==='ArrowLeft'?(i+n-1)%n:
            v==='Home'?0:v==='End'?n-1:-1;
          if(j<0)return;
          evento.preventDefault();
          if(solicitar)solicitar(claves[j],{foco:true});else seleccionar(claves[j],{foco:true});
        });
      });
      return {seleccionar,actual:()=>activa,paneles,botones};
    }

    // ESTUDIOS: los paneles barrido/mapa comparten el MISMO #estudio49.
    // Solo al cambiar realmente el tipo se activa el listener original M49.5;
    // ir a otra ventana no toca selector, parámetros, gráfica ni resultados.
    const seccionEstudios=crear('div','turbo-ana58');
    estudios.appendChild(seccionEstudios);
    const aviso=crear('p','turbo-ana58-warning');aviso.hidden=true;
    aviso.setAttribute('role','status');aviso.setAttribute('aria-live','polite');
    seccionEstudios.appendChild(aviso);
    let solicitarEstudio=null;
    const tabsEstudios=pestañas(seccionEstudios,ETIQUETAS_ESTUDIOS,'turbo-ana58',
      (clave,opciones)=>solicitarEstudio?.(clave,opciones));
    const retorno=crear('div','turbo-ana58-links');
    retorno.append(atajo('simulacion','Volver a Simulación'),
      atajo('comparador','Abrir Comparador'));
    seccionEstudios.appendChild(retorno);
    const interior=estudio.querySelector('.turbo-study49-grid');
    const info=crear('aside','turbo-ana58-info');info.setAttribute('aria-label','Detalle del punto');
    info.appendChild(detalle);interior.appendChild(info);
    estudio.hidden=false;
    const clasicos=tabsEstudios.paneles.get('clasicos');
    const notaClasicos=crear('p','turbo-ana58-note',
      'Las herramientas OFAT y mapas clásicos mantienen sus formularios HTTP independientes; su cálculo no se realiza al cambiar de vista.');
    clasicos.appendChild(notaClasicos);
    for(const [id,nombre] of [['sensibilidad','Sensibilidad OFAT'],['mapa','Mapas clásicos']]){
      const nodo=documento.getElementById(id);
      if(!nodo)continue;
      const anterior=nodo.closest('.turbo-work-legacy50');
      if(anterior){anterior.querySelector('summary').textContent=nombre;clasicos.appendChild(anterior);}
      else{
        const details=crear('details','turbo-work-legacy50');
        const summary=crear('summary','',nombre);details.append(summary,nodo);
        clasicos.appendChild(details);
      }
    }
    let barridoAnterior=tipo.value==='T3'?'T3':'mach';
    let tipoConocido=tipo.value, cambioDesdePestana=false;
    // En el DOM real los listeners de captura se ejecutan antes del listener
    // heredado M49.5 (que limpia resultados al cambiar el selector).
    tipo.addEventListener('change',evento=>{
      if(tipo.value===tipoConocido)return;
      if(!cambioDesdePestana&&grafico.querySelector('svg')&&
        typeof ventana.confirm==='function'&&
        !ventana.confirm('Cambiar de estudio sustituirá los resultados actuales. ¿Continuar?')){
        tipo.value=tipoConocido;evento.preventDefault();evento.stopImmediatePropagation();return;
      }
      tipoConocido=tipo.value;
      if(!cambioDesdePestana){
        aviso.textContent='Se ha cambiado el tipo de estudio. Calcula de nuevo para esta selección.';
        aviso.hidden=false;
      }
    },true);
    const elegirEstudios=(clave,{foco=false,actualizarTipo=true}={})=>{
      if(!tabsEstudios.paneles.has(clave))return false;
      if(clave!=='clasicos'){
        const deseado=clave==='mapa'?'mapa':barridoAnterior;
        if(actualizarTipo&&tipo.value!==deseado){
          // El código M49.5 descarta el gráfico al cambiar de tipo. Advertir
          // antes: nunca hacer esto al navegar entre espacios principales.
          if(grafico.querySelector('svg')&&typeof ventana.confirm==='function'&&
             !ventana.confirm('Cambiar el tipo de estudio sustituirá el gráfico calculado. Exporta los resultados si deseas conservarlos. ¿Continuar?'))return false;
          aviso.textContent='Has cambiado de tipo de estudio. El explorador conserva sus reglas: vuelve a calcular para obtener el nuevo resultado.';
          aviso.hidden=false;
          cambioDesdePestana=true;
          try{tipo.value=deseado;tipo.dispatchEvent(new ventana.Event('change',{bubbles:true}));}
          finally{cambioDesdePestana=false;}
        }
        tabsEstudios.paneles.get(clave).appendChild(estudio);
        estudio.hidden=false;
      }
      return tabsEstudios.seleccionar(clave,{foco});
    };
    solicitarEstudio=elegirEstudios;
    tipo.addEventListener('change',()=>{
      if(tipo.value!=='mapa')barridoAnterior=tipo.value;
      const clave=tipo.value==='mapa'?'mapa':'barridos';
      if(tabsEstudios.actual()!==clave)elegirEstudios(clave,{actualizarTipo:false});
    });
    elegirEstudios(tipo.value==='mapa'?'mapa':'barridos',{actualizarTipo:false});

    // Los cambios de rango no alteran el punto motor; sin embargo hacen que
    // las coordenadas del gráfico guardado no correspondan a la nueva malla.
    // Se conserva el SVG anterior, se marca como obsoleto y se bloquea aplicar.
    const botonAplicar=documento.getElementById('study49-apply');
    const fuente=documento.getElementById('study49-base');
    const hayResultado=()=>!!grafico.querySelector('svg');
    const invalidar=(mensaje)=>{
      if(!hayResultado())return;
      aviso.textContent=mensaje;aviso.hidden=false;
      if(botonAplicar)botonAplicar.disabled=true;
    };
    forma.addEventListener('input',evento=>{
      // Los selectores emiten input antes del change que puede cancelarse.
      if(evento.target===tipo||evento.target===fuente)return;
      invalidar(
        'Has modificado los límites o la resolución del estudio. La gráfica anterior conserva sus valores originales y está desactualizada; vuelve a calcular.');
    });
    let fuenteConocida=fuente?.value;
    fuente?.addEventListener('change',evento=>{
      if(fuente.value===fuenteConocida)return;
      if(grafico.querySelector('svg')&&typeof ventana.confirm==='function'&&
         !ventana.confirm('Cambiar la configuración de partida eliminará el estudio calculado. ¿Continuar?')){
        fuente.value=fuenteConocida;
        evento.preventDefault();evento.stopImmediatePropagation();return;
      }
      fuenteConocida=fuente.value;
    },true);
    fuente?.addEventListener('change',()=>{
      aviso.textContent='Has cambiado la fuente de condiciones fijas; ejecuta un estudio nuevo.';
      aviso.hidden=false;
    });
    const formMotor=documento.getElementById('turbo-form');
    const revisarCondicionesMotor=()=>{
      if(fuente?.value==='banco')invalidar(
        'Las condiciones del motor han cambiado. El estudio anterior es histórico y debe recalcularse para esta configuración.');
    };
    formMotor?.addEventListener('input',revisarCondicionesMotor);
    formMotor?.addEventListener('change',revisarCondicionesMotor);
    forma.addEventListener('submit',()=>{
      if(botonAplicar)botonAplicar.disabled=false;
      aviso.hidden=true;
    });

    // COMPARADOR: mantener UNA raíz .turbo-lab50. Los listeners de M50.1
    // hacen consultas desde esa raíz, por lo que reubicar hijos no los rompe.
    const tabsComparador=pestañas(lab,ETIQUETAS_COMPARADOR,'turbo-ana58-lab');
    const panelPrest=tabsComparador.paneles.get('prestaciones');
    const panelGraf=tabsComparador.paneles.get('graficas');
    const panelCond=tabsComparador.paneles.get('condiciones');
    const asignar=(padre,selector)=>{const nodo=lab.querySelector(selector);if(nodo)padre.appendChild(nodo);};
    asignar(panelPrest,'[data-lab-warning]');
    asignar(panelPrest,'.turbo-lab50-table');
    asignar(panelPrest,'[data-lab-diagnosis]');
    asignar(panelCond,'details');
    asignar(panelGraf,'.turbo-lab50-charts');
    asignar(panelGraf,'.turbo-lab50-tools');
    asignar(panelGraf,'[data-lab-reading]');
    const figuras=[...panelGraf.querySelectorAll('.turbo-lab50-charts figure')];
    const botonesGraficos=crear('div','turbo-ana58-chart-tabs');
    botonesGraficos.setAttribute('role','group');botonesGraficos.setAttribute('aria-label','Gráfica comparativa');
    const elegirGrafica=(tipo)=>{
      if(!ETIQUETAS_GRAFICAS.some(([k])=>k===tipo))return false;
      figuras.forEach(f=>{f.hidden=f.querySelector('[data-lab-chart]')?.dataset.labChart!==tipo;});
      botonesGraficos.querySelectorAll('button').forEach(b=>{
        b.setAttribute('aria-pressed',String(b.dataset.chart58===tipo));
      });
      // M50.1 usa delegación de clic en el contenedor original para indicar
      // qué SVG se amplía/exporta. No se crea ni dibuja otro SVG.
      const original=panelGraf.querySelector('[data-lab-chart="'+tipo+'"]');
      if(original&&typeof original.dispatchEvent==='function')
        original.dispatchEvent(new ventana.Event('click',{bubbles:true}));
      return true;
    };
    for(const [clave,nombre] of ETIQUETAS_GRAFICAS){
      const boton=crear('button','turbo-ana58-chart-tab',nombre);
      boton.type='button';boton.dataset.chart58=clave;
      boton.addEventListener('click',()=>elegirGrafica(clave));
      botonesGraficos.appendChild(boton);
    }
    panelGraf.insertBefore(botonesGraficos,panelGraf.firstChild);
    elegirGrafica('ts');tabsComparador.seleccionar('prestaciones');
    const enlaces=crear('div','turbo-ana58-links');
    enlaces.append(atajo('simulacion','Volver a Simulación'),atajo('estudios','Abrir Estudios'));
    lab.appendChild(enlaces);
    documento.body.classList.add('turbo-50-8-ready');
    return {estudios:{...tabsEstudios,seleccionar:elegirEstudios},
      comparador:{...tabsComparador,seleccionarGrafica:elegirGrafica},
      aviso,referencia:lab,estudio};
  }
  if(typeof module!=='undefined'&&module.exports)
    module.exports={iniciarAnalisis50_8,ETIQUETAS_ESTUDIOS,ETIQUETAS_COMPARADOR};
  raiz.iniciarAnalisis50_8=iniciarAnalisis50_8;
  if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',
    ()=>{raiz.controladorAnalisis50_8=iniciarAnalisis50_8(document,raiz);});
})(typeof window!=='undefined'?window:globalThis);
