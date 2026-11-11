/* M50.1: dos instantáneas de la misma API; no contiene un solucionador físico. */
(function(raiz){
  'use strict';
  const finito=v=>typeof v==='number'&&Number.isFinite(v);
  const formato=v=>finito(v)?Number(v.toPrecision(6)).toLocaleString('es-ES'):'No disponible';
  function diferencia50_1(referencia,actual,unidad='–'){
    if(!finito(referencia)||!finito(actual))return {absoluta:null,relativa:null};
    const absoluta=actual-referencia;
    return {absoluta,relativa:referencia!==0?100*absoluta/referencia:null,
      unidadAbsoluta:unidad==='%'?'puntos porcentuales':unidad};
  }
  function compatibilidad50_1(ref,actual){
    if(!ref||!actual)return {compatible:false,mensaje:'Se requieren ambos puntos válidos.',cambios:[]};
    const claves=new Set([...Object.keys(ref.entradas),...Object.keys(actual.entradas)]);
    const mismo=(a,b)=>a===b||(a!==''&&b!==''&&a!==undefined&&b!==undefined&&
      Number.isFinite(Number(a))&&Number.isFinite(Number(b))&&Number(a)===Number(b));
    const cambios=[...claves].filter(k=>!mismo(ref.entradas[k],actual.entradas[k]));
    const modo=ref.modo===actual.modo;
    const adicionales=cambios.filter(k=>!['mach','T3'].includes(k));
    return {compatible:modo,homogenea:modo&&adicionales.length===0,cambios,
      mensaje:!modo?'Modalidades A/B/C distintas: se omiten diferencias de prestaciones y trabajos por sus bases de caudal/restricciones.':
        adicionales.length?'Han cambiado condiciones avanzadas, geometría o contorno: no se puede atribuir la variación solo a Mach o TIT.':
        cambios.length>1?'Mach y TIT han cambiado simultáneamente; no se puede asignar causalidad a uno solo.':
        'Mismo modelo y modalidad; la comparación es descriptiva, no una validación experimental.'};
  }
  function extraer50_1(datos,entradas){
    if(!datos?.ok||!Array.isArray(datos.estaciones)||!datos.caracterizacion)return null;
    // Copia profunda de los datos físicos recibidos y de las entradas del formulario.
    return JSON.parse(JSON.stringify({modelo:'Turborreactor monoeje educativo cp(T), combustión energética equivalente',
      modo:datos.modo,entradas,estaciones:datos.estaciones,caracterizacion:datos.caracterizacion,
      magnitudes:datos.magnitudes,diagnosticos:datos.diagnosticos}));
  }
  const indicadores=[
    ['Condiciones','mach','Mach de vuelo','–'],['Condiciones','T3','TIT / T3 interna','K'],
    ['Funcionamiento','rp','Relación de compresión','–'],['Funcionamiento','npr','NPR','–'],
    ['Prestaciones','fs','Empuje específico neto','N/(kg/s)'],['Prestaciones','fn','Empuje neto absoluto','N'],
    ['Prestaciones','f','Dosado','kg/kg aire'],['Prestaciones','mf','Consumo de combustible','kg/s'],
    ['Prestaciones','tsfc','TSFC','kg/(N·h)'],['Prestaciones','v0','Velocidad de vuelo','m/s'],
    ['Prestaciones','ve','Velocidad de escape','m/s'],
    ['Trabajo','wc','Trabajo compresor','kJ/kg aire'],['Trabajo','wt','Trabajo turbina','kJ/kg aire'],
    ['Trabajo','weje','Trabajo transmitido por eje','kJ/kg aire']
  ];
  const todos=p=>Object.values(p.caracterizacion).flat();
  function valor50_1(p,id){
    if(id==='mach'||id==='T3'){
      const v=p.entradas[id];return v===''?null:Number(v);
    }
    return todos(p).find(i=>i.id===id)?.valor??null;
  }
  const escapeSvg=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
  const colores=['#1364a5','#b85c16'];
  function dibujarEstados50_1(ref,actual,tipo){
    const ids=['pt2','pt3','pt4','pt5'];
    if(tipo==='ts')ids.push('salida');
    const series=[ref,actual].map(p=>ids.map(id=>p.estaciones.find(e=>e.id===id)));
    const valido=e=>e&&finito(tipo==='ts'?e.s:e[tipo])&&finito(e.T);
    const puntos=series.flat().filter(valido);
    if(!puntos.length)return '';
    const yvals=puntos.map(e=>tipo==='ts'?e.T:e[tipo]);
    const xvals=tipo==='ts'?puntos.map(e=>e.s):[0,1,2,3];
    const minX=Math.min(...xvals),maxX=Math.max(...xvals),minY=Math.min(...yvals),maxY=Math.max(...yvals);
    const dx=Math.max(maxX-minX,.01),dy=Math.max(maxY-minY,1);
    const x=e=>tipo==='ts'?70+(e.s-minX+.12*dx)/(1.24*dx)*555:90+ids.indexOf(e.id)*175;
    const y=e=>275-( (tipo==='ts'?e.T:e[tipo])-minY+.12*dy)/(1.24*dy)*222;
    const parts=['<path d="M65 32 V275 H672" fill="none" stroke="#789"/>'];
    for(let serie=0;serie<2;serie++){
      let previo=null;
      for(const e of series[serie]){
        if(!valido(e)){previo=null;continue;}
        if(previo)parts.push(`<path d="M${x(previo).toFixed(2)},${y(previo).toFixed(2)} L${x(e).toFixed(2)},${y(e).toFixed(2)}" fill="none" stroke="${colores[serie]}" stroke-dasharray="5 5" stroke-width="2"/>`);
        const lectura=`Punto ${serie+1}; ${e.id}; ${e.tipo}: T=${formato(e.T)} K, p=${formato(e.p)} kPa${tipo==='ts'?`, s=${formato(e.s)} kJ/(kg·K)`:''}`;
        parts.push(`<circle cx="${x(e).toFixed(2)}" cy="${y(e).toFixed(2)}" r="${serie===0?5:7}" fill="${colores[serie]}" stroke="white" stroke-width="2" tabindex="0" role="button" data-plot-info="${escapeSvg(lectura)}" aria-label="${escapeSvg(lectura)}" data-engine-station="${e.id}"/>`);
        previo=e;
      }
    }
    parts.push(`<text x="70" y="18" font-size="12">${tipo==='ts'?'T [K] frente a s [kJ/(kg·K)]':tipo==='T'?'Temperatura total [K]':'Presión total [kPa]'}</text>`);
    if(tipo!=='ts')ids.slice(0,4).forEach((id,i)=>parts.push(`<text x="${90+i*175}" y="296" text-anchor="middle" font-size="12">${id}</text>`));
    else parts.push('<text x="345" y="315" text-anchor="middle" font-size="12">s [kJ/(kg·K)] · uniones esquemáticas</text>');
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 710 335" role="img" aria-label="Comparación ${tipo}: referencia azul y actual naranja">${parts.join('')}${leyenda50_1()}</svg>`;
  }
  function leyenda50_1(){return `<g font-size="12"><circle cx="486" cy="20" r="5" fill="${colores[0]}"/><text x="496" y="24">Referencia</text><circle cx="585" cy="20" r="5" fill="${colores[1]}"/><text x="595" y="24">Actual</text></g>`;}
  function dibujarPrestaciones50_1(ref,actual,compatible){
    if(!compatible)return '';
    const claves=['fs','fn','tsfc','mf'].filter(id=>finito(valor50_1(ref,id))&&finito(valor50_1(actual,id)));
    if(!claves.length)return '';
    const parts=['<path d="M390 30 V280" stroke="#879" fill="none"/>'];
    claves.forEach((id,i)=>{
      const pares=[valor50_1(ref,id),valor50_1(actual,id)];
      const max=Math.max(...pares.map(Math.abs),1e-12);
      const y=53+i*56;
      parts.push(`<text x="10" y="${y+8}" font-size="13">${id} (${indicadores.find(k=>k[1]===id)[3]})</text>`);
      pares.forEach((v,j)=>{
        const width=250*Math.abs(v)/max;
        parts.push(`<rect x="${v<0?390-width:390}" y="${y+j*15}" width="${width.toFixed(2)}" height="12" fill="${colores[j]}" tabindex="0" role="button" data-plot-info="${escapeSvg(`Punto ${j+1}; ${id}: ${formato(v)}`)}" aria-label="${escapeSvg(`Punto ${j+1}; ${id}: ${formato(v)}`)}"/>`);
      });
    });
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 710 325" role="img" aria-label="Comparación de prestaciones; cada par de barras usa escala propia">${parts.join('')}${leyenda50_1()}<text x="10" y="313" font-size="11">Escala independiente por magnitud; leer valores al seleccionar cada barra</text></svg>`;
  }
  function iniciarLaboratorio50_1(documento,formulario){
    const raiz=documento.querySelector('.turbo-lab50');if(!raiz)return null;
    const buscar=s=>raiz.querySelector(s);
    const botonGuardar=buscar('[data-lab-action="save"]'),botonBorrar=buscar('[data-lab-action="clear"]');
    const estado=buscar('[data-lab-status]'),condiciones=buscar('[data-lab-conditions]');
    const aviso=buscar('[data-lab-warning]'),filas=buscar('[data-lab-rows]');
    const diagnostico=buscar('[data-lab-diagnosis]'),lectura=buscar('[data-lab-reading]');
    let referencia=null,actual=null,escala=1,activa='ts';
    const entradas=()=>Object.fromEntries(new FormData(formulario).entries());
    const elemento=(tag,texto)=>{const e=documento.createElement(tag);e.textContent=texto;return e;};
    function render(){
      botonGuardar.disabled=!actual;
      botonGuardar.textContent=referencia?'Sustituir referencia':'Guardar como referencia';
      botonBorrar.disabled=!referencia;
      estado.textContent=!referencia?'No hay referencia guardada.':actual?
        'Punto 1 guardado; Punto 2 actualizado.':'Referencia conservada. Punto actual pendiente o no disponible.';
      condiciones.replaceChildren();filas.replaceChildren();diagnostico.textContent='';
      aviso.hidden=true;aviso.textContent='';
      const serializar=p=>p?`${p.modelo} · modo ${p.modo} · ${Object.entries(p.entradas).map(([k,v])=>`${k}=${v}`).join(' · ')}`:'No disponible';
      condiciones.append(elemento('p','Referencia: '+serializar(referencia)),elemento('p','Actual: '+serializar(actual)));
      for(const clave of ['ts','T','p','prestaciones'])buscar(`[data-lab-chart="${clave}"]`).replaceChildren();
      if(!referencia||!actual)return;
      const compatible=compatibilidad50_1(referencia,actual);
      aviso.hidden=compatible.homogenea;
      aviso.textContent=compatible.mensaje;
      let grupoAnterior='';
      for(const [grupo,id,nombre,unidad] of indicadores){
        if(grupo!==grupoAnterior){const row=documento.createElement('tr');const th=elemento('th',grupo);th.colSpan=5;row.append(th);filas.append(row);grupoAnterior=grupo;}
        const v1=valor50_1(referencia,id),v2=valor50_1(actual,id);
        const permite=compatible.compatible||['mach','T3'].includes(id);
        const delta=permite?diferencia50_1(v1,v2,unidad):{absoluta:null,relativa:null};
        const tr=documento.createElement('tr');
        for(const texto of [nombre,`${formato(v1)} ${unidad}`,`${formato(v2)} ${unidad}`,
          finito(delta.absoluta)?`${delta.absoluta>=0?'+':''}${formato(delta.absoluta)} ${delta.unidadAbsoluta}`:'—',
          finito(delta.relativa)?`${delta.relativa>=0?'+':''}${formato(delta.relativa)} %`:'—']){
          tr.append(elemento('td',texto));
        }
        filas.append(tr);
      }
      const cambios=compatible.cambios;
      const mensajes=[`Parámetros modificados: ${cambios.length?cambios.join(', '):'ninguno'}.`,compatible.mensaje];
      for(const id of ['fs','tsfc']){
        const a=valor50_1(referencia,id),b=valor50_1(actual,id);
        const d=diferencia50_1(a,b);
        if(compatible.compatible&&finito(d.relativa))mensajes.push(`${id==='fs'?'El empuje específico':'El TSFC'} ${d.absoluta>=0?'aumenta':'disminuye'} un ${formato(Math.abs(d.relativa))} % respecto a la referencia.`);
        else if(!finito(a)||!finito(b))mensajes.push(`${id.toUpperCase()}: comparación no disponible en alguno de los puntos; puede faltar caudal o empuje positivo.`);
      }
      diagnostico.textContent=mensajes.join(' ');
      for(const clave of ['ts','T','p','prestaciones']){
        const svg=clave==='prestaciones'?dibujarPrestaciones50_1(referencia,actual,compatible.compatible):
          dibujarEstados50_1(referencia,actual,clave);
        const destino=buscar(`[data-lab-chart="${clave}"]`);
        if(svg)destino.innerHTML=svg;else destino.textContent='No disponible para esta comparación.';
      }
      aplicarEscala();
    }
    function aplicarEscala(){
      for(const svg of raiz.querySelectorAll('[data-lab-chart] svg'))svg.style.width=`${100*escala}%`;
      buscar('[data-lab-scale]').textContent=`${Math.round(100*escala)} %`;
    }
    function actualizado(datos){actual=extraer50_1(datos,entradas());render();}
    function pendiente(){actual=null;render();}
    function guardar(){if(!actual)return false;referencia=JSON.parse(JSON.stringify(actual));render();return true;}
    function borrar(){referencia=null;render();}
    botonGuardar.addEventListener('click',guardar);botonBorrar.addEventListener('click',borrar);
    for(const nombre of ['out','in','reset','export'])buscar(`[data-lab-action="${nombre}"]`).addEventListener('click',()=>{
      if(nombre==='in')escala=Math.min(3,escala*1.25);
      else if(nombre==='out')escala=Math.max(.7,escala*.8);
      else if(nombre==='reset')escala=1;
      else{
        const svg=buscar(`[data-lab-chart="${activa}"] svg`);if(!svg)return;
        const copia=svg.cloneNode(true);copia.removeAttribute('style');
        const blob=new Blob([new XMLSerializer().serializeToString(copia)],{type:'image/svg+xml'});
        const url=URL.createObjectURL(blob),a=documento.createElement('a');
        a.href=url;a.download=`brayton_comparacion_${activa}.svg`;a.click();
        setTimeout(()=>URL.revokeObjectURL(url),1000);
      }
      aplicarEscala();
    });
    for(const [evento,handler] of [['click',e=>{
      const p=e.target.closest?.('[data-plot-info]');if(p)lectura.textContent=p.getAttribute('data-plot-info');
      const panel=e.target.closest?.('[data-lab-chart]');if(panel)activa=panel.dataset.labChart;
    }],['keydown',e=>{
      if(!['Enter',' '].includes(e.key))return;
      const p=e.target.closest?.('[data-plot-info]');if(p){e.preventDefault();lectura.textContent=p.getAttribute('data-plot-info');}
    }]])raiz.addEventListener(evento,handler);
    render();return {actualizado,pendiente,guardar,borrar,referencia:()=>referencia,actual:()=>actual};
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={diferencia50_1,compatibilidad50_1,extraer50_1,valor50_1,iniciarLaboratorio50_1,dibujarEstados50_1,dibujarPrestaciones50_1};
  raiz.iniciarLaboratorio50_1=iniciarLaboratorio50_1;
})(typeof window!=='undefined'?window:globalThis);
