/* Mejora progresiva: sin JS el formulario HTML sigue pudiendo enviarse. */
document.addEventListener('DOMContentLoaded',()=>{
  const form=document.getElementById('turbo-form');
  if(!form)return;
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
  const base={rp:'10',eta_c:'0.85',T3:'1600',delta_pct:'4',eta_t:'0.90',eta_m:'0.98',eta_n:'0.95',pi_d:'1',eta_b:'0.99',PCI:'43000'};
  document.querySelectorAll('[data-ejemplo]').forEach(b=>b.addEventListener('click',()=>{
    const caso=casos[b.dataset.ejemplo];if(!caso)return;
    Object.entries({...base,...caso}).forEach(([k,v])=>{
      if(k==='modo_ambiente')modos.forEach(m=>m.checked=m.value===v);
      else if(form.elements[k])form.elements[k].value=v;
    });
    sync();
  }));
  sync();
});
