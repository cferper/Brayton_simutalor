/* M48.2: interacción nativa. Los estados físicos solo los calcula Flask. */
(function (raiz) {
  'use strict';

  function crearControlador48({solicitar, onEstado, onRespuesta, onError,
                              demora=350, setTimer=setTimeout,
                              clearTimer=clearTimeout, Abort=AbortController}) {
    let version=0, temporizador=null, pendiente=null;
    function cancelar() {
      if (temporizador !== null) clearTimer(temporizador);
      temporizador=null;
      if (pendiente) pendiente.abort();
      pendiente=null;
    }
    function invalidar() {
      version+=1;
      cancelar();
      onEstado('pendiente');
    }
    function detener() {
      // El POST manual puede iniciar la navegación antes de que termine fetch.
      // Invalidamos también su versión aunque abortar no detenga al servidor.
      version+=1;
      cancelar();
    }
    function cambiar() {
      version+=1;
      cancelar();
      const actual=version;
      onEstado('actualizando');
      temporizador=setTimer(async ()=>{
        temporizador=null;
        const controlador=new Abort();
        pendiente=controlador;
        try {
          const respuesta=await solicitar(controlador.signal);
          if(actual!==version)return;
          onRespuesta(respuesta);
          onEstado('actualizado');
        } catch(error) {
          if(actual!==version || error?.name==='AbortError')return;
          onError(error);
        } finally {
          if(actual===version)pendiente=null;
        }
      },demora);
    }
    return {cambiar,invalidar,cancelar:detener,version:()=>version};
  }

  function acoplarControl48({numero,deslizador,lectura,unidad,onCambio}) {
    const mostrar=()=>{lectura.textContent=(numero.value||'—')+' '+unidad;};
    const desdeNumero=()=>{
      const valor=Number(numero.value);
      if(numero.value.trim()!=='' && Number.isFinite(valor)){
        deslizador.value=String(Math.max(Number(deslizador.min),
                                  Math.min(Number(deslizador.max),valor)));
      }
      mostrar();onCambio();
    };
    const desdeDeslizador=()=>{
      numero.value=deslizador.value;
      mostrar();onCambio();
    };
    numero.addEventListener('input',desdeNumero);
    deslizador.addEventListener('input',desdeDeslizador);
    mostrar();
    return {mostrar,desdeNumero,desdeDeslizador};
  }

  function inicializar48(documento, fetcher) {
    const formulario=documento.getElementById('turbo-form');
    const panel=documento.getElementById('turbo-live');
    if(!formulario || !panel)return null;
    panel.hidden=false;
    const estado=documento.getElementById('turbo-live-status');
    const banco=documento.body.dataset.interfaz==='interactivo';
    const selectorModo=formulario.elements.modo_caudal;
    const botonesModo=[...formulario.querySelectorAll('[data-bank-mode]')];
    const actualizarModo=()=>{
      const modo=selectorModo?.value||'impuesto';
      formulario.dataset.bankMode=modo;
      botonesModo.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.bankMode===modo)));
    };
    botonesModo.forEach(b=>b.addEventListener('click',()=>{
      if(selectorModo.value===b.dataset.bankMode)return;
      selectorModo.value=b.dataset.bankMode;
      selectorModo.dispatchEvent(new Event('change',{bubbles:true}));
    }));
    selectorModo?.addEventListener('change',actualizarModo);
    actualizarModo();
    const avanzado=documento.getElementById('turbo-bank-advanced-toggle');
    avanzado?.addEventListener('click',()=>{
      const abierto=formulario.classList.toggle('turbo-bank-show-advanced');
      avanzado.setAttribute('aria-expanded',String(abierto));
      avanzado.textContent=abierto?'Ocultar configuración avanzada ▴':'Configuración avanzada ▾';
    });
    const pestañas=[...panel.querySelectorAll('[data-plot-tab]')];
    const activarGrafica=(clave)=>{
      pestañas.forEach(b=>{
        const activo=b.dataset.plotTab===clave;
        b.setAttribute('aria-selected',String(activo));
        b.tabIndex=activo?0:-1;
      });
      panel.querySelectorAll('[data-plot-panel]').forEach(p=>{
        p.hidden=p.dataset.plotPanel!==clave;
      });
    };
    pestañas.forEach((b,i)=>{
      b.addEventListener('click',()=>activarGrafica(b.dataset.plotTab));
      b.addEventListener('keydown',evento=>{
        if(!['ArrowRight','ArrowLeft','Home','End'].includes(evento.key))return;
        evento.preventDefault();
        const visibles=pestañas.filter(t=>!t.hidden);
        const actual=visibles.indexOf(b);
        const siguiente=evento.key==='Home'?0:evento.key==='End'?visibles.length-1:
          (actual+(evento.key==='ArrowRight'?1:-1)+visibles.length)%visibles.length;
        activarGrafica(visibles[siguiente].dataset.plotTab);
        visibles[siguiente].focus();
      });
    });
    if(pestañas.length)activarGrafica('ts');
    const estudioDesactualizado=()=>documento.querySelectorAll('.turbo-study-stale').forEach(aviso=>{
      aviso.hidden=false;
    });
    const valor=(clave,contenido)=>{
      const destino=panel.querySelector('[data-live-value="'+clave+'"]');
      if(destino)destino.textContent=contenido;
    };
    const formatear=(v)=>typeof v==='number' && Number.isFinite(v)
      ?v.toLocaleString('es-ES',{maximumSignificantDigits:7}):String(v);
    const mostrarTodos=(contenido)=>{
      panel.querySelectorAll('[data-live-value]').forEach(item=>{
        item.textContent=contenido;
      });
      panel.querySelectorAll('[data-live-plot]').forEach(item=>{
        item.replaceChildren(documento.createTextNode(contenido));
      });
    };
    const paneles=['resultados','estaciones','graficas'];
    const marcarPaneles=(mensaje)=>{
      paneles.forEach(id=>{
        const destino=documento.getElementById('turbo-'+id+'-vista-uso');
        if(!destino)return;
        const aviso=documento.createElement('p');
        aviso.className='card empty-state';
        aviso.textContent=mensaje;
        destino.replaceChildren(aviso);
      });
    };
    const dibujar=(panelClave,svg)=>{
      const destino=panel.querySelector('[data-live-plot="'+panelClave+'"]');
      if(!destino)return;
      const disponible=typeof svg==='string'&&svg.includes('<svg');
      if(disponible)destino.innerHTML=svg;
      else destino.textContent='Gráfica no disponible para este punto.';
      const pestaña=panel.querySelector('[data-plot-tab="'+panelClave+'"]');
      if(pestaña)pestaña.hidden=!disponible;
    };
    const reconciliarPestañas=()=>{
      const actual=pestañas.find(b=>b.getAttribute('aria-selected')==='true');
      if(actual&&!actual.hidden)return;
      const primera=pestañas.find(b=>!b.hidden);
      if(primera)activarGrafica(primera.dataset.plotTab);
    };
    const controlador=crearControlador48({
      solicitar:async signal=>{
        const respuesta=await fetcher('/api/turborreactor/simular',{
          method:'POST',body:new FormData(formulario),signal,
          headers:{'Accept':'application/json'}
        });
        const datos=await respuesta.json();
        if(!respuesta.ok || datos.ok!==true){
          const error=new Error(datos?.error?.mensaje||'La simulación no está disponible.');
          error.fueraMapa=formulario.elements.modo_caudal?.value==='acoplado' &&
            /mapa|rline|extrapol|fuera del dominio de (?:los )?mapas/i.test(error.message);
          throw error;
        }
        return datos;
      },
      onEstado:tipo=>{
        panel.dataset.estado=tipo;
        const badge=documento.querySelector('#resultados .badge');
        if(tipo==='actualizando'){
          estado.textContent='Actualizando…';
          if(badge)badge.textContent='Actualizando…';
          mostrarTodos('Pendiente de cálculo');
          marcarPaneles('Calculando las prestaciones con los parámetros actuales…');
        }else if(tipo==='actualizado')estado.textContent='Actualizado';
        else{
          estado.textContent='Parámetros modificados. Ajusta Mach o T3, o pulsa Simular.';
          if(badge)badge.textContent='Pendiente de cálculo';
        }
      },
      onRespuesta:datos=>{
        /* Comprobamos las tres regiones antes de aplicar ningún cambio visual. */
        const nuevo=new DOMParser().parseFromString(datos.html_documento,'text/html');
        const cambios=paneles.map(id=>{
          const destino=documento.getElementById('turbo-'+id+'-vista-uso');
          const origen=nuevo.getElementById('turbo-'+id+'-vista-uso');
          if(!destino||!origen)throw new Error('Falta una región HTML de la simulación.');
          return [destino,Array.from(origen.childNodes,n=>documento.importNode(n,true))];
        });
        cambios.forEach(([destino,nodos])=>destino.replaceChildren(...nodos));
        // Un error antiguo del formulario no corresponde a esta nueva solución.
        documento.querySelector('#turbo-configuracion-vista-uso > .error-summary')?.remove();
        const badge=documento.querySelector('#resultados .badge');
        if(badge)badge.textContent='Caso calculado';
        const m=datos.magnitudes;
        ['empuje_absoluto_N','empuje_especifico_neto','gasto_masico_aire_kg_s',
         'gasto_masico_combustible_kg_s','TSFC_kg_N_h','velocidad_salida_m_s',
         'rpm_eje','regimen_tobera']
          .forEach(k=>{
            const disponible=m[k]!==null&&m[k]!==undefined;
            valor(k,disponible?formatear(m[k]):'No disponible');
            const tarjeta=panel.querySelector('[data-live-card="'+k+'"]');
            if(tarjeta&&banco)tarjeta.hidden=!disponible;
          });
        const ausentes=panel.querySelector('#turbo-live-unavailable');
        if(ausentes&&banco){
          const motivos=[];
          if(m.empuje_absoluto_N==null&&datos.modo==='impuesto')
            motivos.push('Empuje absoluto: prescribe un gasto másico de aire para calcular la fuerza [N].');
          if(m.rpm_eje==null&&datos.modo!=='acoplado')
            motivos.push('Régimen de giro: solo se determina con el acoplamiento por mapas (modo C).');
          ausentes.replaceChildren(...motivos.map(motivo=>{
            const p=documento.createElement('p');p.textContent=motivo;return p;
          }));
        }
        const svg=datos.svg||{};
        dibujar('ts',svg.svg_ts);
        dibujar('mach',svg.svg_mach_axial||svg.svg_mach_perfil_tobera||svg.svg_mach_tobera);
        dibujar('presion',svg.svg_presion_axial||svg.svg_presion_perfil_tobera||svg.svg_presion_tobera);
        dibujar('geometria',svg.svg_geometria_conica);
        reconciliarPestañas();
      },
      onError:error=>{
        const fuera=Boolean(error.fueraMapa);
        panel.dataset.estado=fuera?'fuera-mapa':'error';
        const mensaje=fuera?'Fuera del mapa':'Error de cálculo';
        estado.textContent=mensaje+': '+(error.message||'No se ha podido calcular.');
        mostrarTodos('No disponible');
        marcarPaneles(estado.textContent);
        const badge=documento.querySelector('#resultados .badge');
        if(badge)badge.textContent=mensaje;
      }
    });

    [['mach','–'],['T3','K']].forEach(([id,unidad])=>{
      const numero=formulario.elements[id];
      const deslizador=documento.getElementById(id+'_deslizador');
      const lectura=documento.getElementById(id+'_lectura');
      if(numero&&deslizador&&lectura){
        acoplarControl48({numero,deslizador,lectura,unidad,onCambio:controlador.cambiar});
      }
    });
    formulario.addEventListener('input',evento=>{
      estudioDesactualizado();
      if(evento.target.id==='mach'||evento.target.id==='T3'||evento.target.dataset.turboSlider)return;
      controlador.invalidar();
      mostrarTodos('Pendiente de cálculo');
      marcarPaneles('Parámetros distintos del resultado anterior; pulsa Simular para calcular.');
    });
    formulario.addEventListener('change',evento=>{
      estudioDesactualizado();
      if(evento.target.name==='modo_ambiente'){
        if(banco)controlador.cambiar();
        else{
          controlador.invalidar();
          mostrarTodos('Pendiente de cálculo');
          marcarPaneles('El ambiente ha cambiado; ajusta Mach o T3, o pulsa Simular.');
        }
      }
      else if(evento.target.id==='modo_caudal'||evento.target.id==='tipo_tobera')controlador.cambiar();
      else if(banco&&evento.target.tagName==='INPUT'&&
              !['mach','T3'].includes(evento.target.id)&&
              !evento.target.dataset.turboSlider)controlador.cambiar();
    });
    documento.querySelectorAll('[data-ejemplo]').forEach(b=>b.addEventListener('click',()=>{
      /* El manejador histórico del ejemplo está registrado antes de este. */
      for(const id of ['mach','T3']){
        const elemento=formulario.elements[id];
        elemento.dispatchEvent(new Event('input',{bubbles:true}));
      }
    }));
    formulario.addEventListener('submit',()=>controlador.cancelar());
    // GET inicial sin resultados: se calcula una sola vez tras la espera.
    // POST manual o POST de estudios: ya calculado en Python, no repetirlo.
    if(documento.body.dataset.simulacionInicial==='pendiente')controlador.cambiar();
    else if(documento.body.dataset.simulacionInicial==='resuelta'){
      estado.textContent='Resultados del cálculo manual disponibles en «Resultados».';
    }
    return controlador;
  }

  if(typeof module!=='undefined'&&module.exports){
    module.exports={crearControlador48,acoplarControl48,inicializar48};
  }
  if(typeof document!=='undefined'){
    document.addEventListener('DOMContentLoaded',()=>inicializar48(document,fetch));
  }
})(typeof window!=='undefined'?window:globalThis);
