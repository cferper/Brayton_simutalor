/* Mejora progresiva: sin JS el formulario HTML sigue pudiendo enviarse. */
document.addEventListener('DOMContentLoaded',()=>{
  /* Navegación exclusiva en clientes JS: sin JS, los siete apartados siguen
     visibles en vertical como respaldo accesible y el POST sigue operativo. */
  const paneles=[...document.querySelectorAll('.turbo-section[id]')];
  const enlaces=[...document.querySelectorAll('.section-nav a[href^="#"]')];
  const ids=new Set(paneles.map(p=>p.id));
  const porUrl=()=>location.hash.slice(1);
  const elegir=(id, moverFoco=false)=>{
    if(!ids.has(id))id='configuracion';
    paneles.forEach(p=>{p.hidden=p.id!==id;});
    enlaces.forEach(a=>{
      if(a.getAttribute('href')==='#'+id)a.setAttribute('aria-current','page');
      else a.removeAttribute('aria-current');
    });
    document.body.dataset.activePanel=id;
    if(moverFoco){
      window.scrollTo({top:0,behavior:'auto'});
      const titulo=document.querySelector('#'+id+' h2');
      titulo?.setAttribute('tabindex','-1');
      titulo?.focus({preventScroll:true});
    }
  };
  const solicitado=porUrl();
  elegir(ids.has(solicitado)?solicitado:document.body.dataset.initialPanel);
  document.body.classList.add('turbo-nav-ready');
  enlaces.forEach(a=>a.addEventListener('click',evento=>{
    const id=a.getAttribute('href').slice(1);
    if(!ids.has(id))return;
    evento.preventDefault();
    if(location.hash!=='#'+id)history.pushState(null,'','#'+id);
    elegir(id,true);
  }));
  const sincronizarHistoria=()=>{
    const id=porUrl();
    elegir(ids.has(id)?id:document.body.dataset.initialPanel,true);
  };
  window.addEventListener('popstate',sincronizarHistoria);
  window.addEventListener('hashchange',sincronizarHistoria);
  const form=document.getElementById('turbo-form');
  if(!form)return;
  const selectorTobera=form.querySelector('#tipo_tobera');
  const syncTobera=()=>{
    const tipo=selectorTobera?.value||'convergente';
    form.querySelectorAll('[data-tobera]').forEach(b=>{
      b.hidden=b.dataset.tobera!==tipo;
      /* Conservamos el valor oculto al alternar el tipo de tobera. */
    });
  };
  selectorTobera?.addEventListener('change',syncTobera);
  const modos=[...form.querySelectorAll('input[name="modo_ambiente"]')];
  const sync=()=>{
    const modo=modos.find(r=>r.checked)?.value||'directo';
    form.querySelectorAll('[data-ambiente]').forEach(b=>{
      const activo=b.dataset.ambiente===modo;
      b.dataset.inactivo=String(!activo);
      b.querySelector('input').disabled=!activo;
    });
  };
  modos.forEach(r=>r.addEventListener('change',()=>{
    /* La alternativa excluida queda limpia; ninguna simulación es automática. */
    const modo=r.checked?r.value:modos.find(m=>m.checked)?.value;
    form.querySelectorAll('[data-ambiente]').forEach(b=>{
      if(b.dataset.ambiente!==modo)b.querySelector('input').value='';
    });
    sync();
  }));
  const casos={
    estatico:{modo_ambiente:'directo',T_amb:'288.15',p_amb:'100',altitud_geopotencial:'',mach:'0'},
    vuelo:{modo_ambiente:'directo',T_amb:'288.15',p_amb:'100',altitud_geopotencial:'',mach:'0.7'},
    isa:{modo_ambiente:'ISA',T_amb:'',p_amb:'',altitud_geopotencial:'10000',mach:'0.5'}
  };
  const base={rp:'10',eta_c:'0.85',T3:'1600',delta_pct:'4',eta_t:'0.90',eta_m:'0.98',eta_n:'0.95',pi_d:'1',eta_b:'0.99',PCI:'43000',tipo_tobera:'convergente',epsilon:'1.5'};
  document.querySelectorAll('[data-ejemplo]').forEach(b=>b.addEventListener('click',()=>{
    const caso=casos[b.dataset.ejemplo];if(!caso)return;
    Object.entries({...base,...caso}).forEach(([k,v])=>{
      if(k==='modo_ambiente')modos.forEach(m=>m.checked=m.value===v);
      else if(form.elements[k])form.elements[k].value=v;
    });
    sync();
    syncTobera();
  }));
  /* Los estudios son formularios hermanos (HTML no admite forms anidados).
     Al enviar se capturan todos los valores *actuales* del formulario M40;
     los ocultos del servidor permiten también el envío sin JavaScript. */
  document.querySelectorAll('[data-study-form]').forEach(estudio=>{
    estudio.addEventListener('submit',()=>{
      estudio.querySelectorAll('input[data-motor-field]').forEach(oculto=>{
        if(oculto.name==='modo_ambiente'){
          oculto.value=modos.find(r=>r.checked)?.value||'directo';
        }else if(form.elements[oculto.name]){
          oculto.value=form.elements[oculto.name].value;
        }
      });
    });
  });
  const selectorOfat=document.getElementById('sens_parametro');
  if(selectorOfat){
    const rangos={rp:['5','15'],T3:['1400','1800'],mach:['0','0.8'],
      eta_c:['0.7','1'],eta_t:['0.7','1'],pi_d:['0.8','1'],delta_pct:['0','10']};
    selectorOfat.addEventListener('change',()=>{
      const rango=rangos[selectorOfat.value];if(!rango)return;
      document.getElementById('sens_min').value=rango[0];
      document.getElementById('sens_max').value=rango[1];
    });
  }
  const selectorMapa=document.getElementById('mapa_tipo');
  if(selectorMapa){
    const mostrarMapa=()=>document.querySelectorAll('[data-map-fields]').forEach(grupo=>{
      grupo.hidden=grupo.dataset.mapFields!==selectorMapa.value;
    });
    selectorMapa.addEventListener('change',mostrarMapa);
    mostrarMapa();
  }
  sync();
  syncTobera();
});
