/* M49.5: presentación de muestras reales; el cálculo físico es exclusivo de Python. */
(function (root) {
  'use strict';
  const NS='http://www.w3.org/2000/svg';
  const LABEL={empuje_N:'Empuje neto',empuje_especifico:'Empuje específico',TSFC:'TSFC'};
  const COLORES=['#2563a6','#c05621','#087e74'];
  const valido=p=>p.estado==='valido';
  const numero=v=>Number.isFinite(v)?Number(v).toLocaleString('es-ES',{maximumSignificantDigits:6}):'No disponible';
  function colorMapa49(valor,min,max){
    const f=max===min?.5:(valor-min)/(max-min);
    const h=220-195*Math.max(0,Math.min(1,f));
    return `hsl(${h} 73% 53%)`;
  }
  function csv49(datos){
    const columnas=['mach','T3','estado','motivo','regimen_tobera','empuje_N','empuje_especifico','TSFC'];
    const escapar=v=>'"'+String(v===null||v===undefined?'':v).replace(/"/g,'""')+'"';
    const encabezado=['# modo='+datos.modo,'# estudio='+datos.tipo,
      ...Object.entries(datos.constantes).map(([k,v])=>'# constante '+k+'='+v),
      '# empuje_N [N]; empuje_especifico [N/(kg/s)]; TSFC [kg/(N·h)]'];
    return '\ufeff'+encabezado.join('\r\n')+'\r\n'+columnas.join(';')+'\r\n'+
      datos.puntos.map(p=>columnas.map(c=>escapar(p[c])).join(';')).join('\r\n')+'\r\n';
  }
  function iniciar49(doc,fetcher){
    const pagina=doc.getElementById('estudio49');if(!pagina)return null;
    const formMotor=doc.getElementById('turbo-form'),form=doc.getElementById('turbo-study49-form');
    const tipo=doc.getElementById('study49-tipo'),metrica=doc.getElementById('study49-metrica');
    const visor=doc.getElementById('study49-chart'),lectura=doc.getElementById('study49-reading');
    const estado=doc.getElementById('study49-status'),resumen=doc.getElementById('study49-summary');
    const boton=doc.getElementById('study49-run'),cancelar=doc.getElementById('study49-cancel');
    let datos=null,guardados=[],peticion=null,version=0,zoom=1,obsoleto=false;
    const crear=(tag,atributos={},contenido='')=>{
      const e=doc.createElementNS(NS,tag);
      Object.entries(atributos).forEach(([k,v])=>e.setAttribute(k,String(v)));
      if(contenido)e.textContent=contenido;
      return e;
    };
    const texto=(svg,x,y,valor,extra={})=>svg.appendChild(crear('text',{x,y,'font-size':12,fill:'#243b53',...extra},valor));
    const linea=(svg,x1,y1,x2,y2,color='#64748b')=>svg.appendChild(crear('line',{x1,y1,x2,y2,stroke:color}));
    const grafico=(w=750,h=390)=>crear('svg',{xmlns:NS,viewBox:`0 0 ${w} ${h}`,role:'img',
      'aria-label':'Estudio paramétrico con puntos calculados'});
    const actual=()=>datos?.puntos||[];
    const clave=()=>metrica.value;
    const tooltip=(elemento,descripcion)=>{
      elemento.setAttribute('data-study49-info',descripcion);
      elemento.setAttribute('tabindex','0');elemento.setAttribute('role','button');
      elemento.setAttribute('aria-label',descripcion);
    };
    const svgLineas=()=>{
      const svg=grafico(),eje=datos.ejes.eje_x,seleccion=clave(),unidad=datos.unidades[seleccion];
      const series=[...guardados.filter(g=>g.tipo===datos.tipo&&g.metrica===seleccion)
        .map(g=>g.datos),datos];
      const valores=series.flatMap(s=>s.puntos.filter(p=>valido(p)&&Number.isFinite(p[seleccion])));
      if(!valores.length){texto(svg,90,120,'Magnitud no disponible para estos puntos.');return svg;}
      const xmin=Math.min(...series.flatMap(s=>s.ejes.x)),xmax=Math.max(...series.flatMap(s=>s.ejes.x));
      const ymin=Math.min(...valores.map(p=>p[seleccion]));
      const ymax=Math.max(...valores.map(p=>p[seleccion]));
      const margen=Math.max((ymax-ymin)*.08,Math.abs(ymax)*.01,1e-8);
      const y0=ymin-margen,y1=ymax+margen;
      const x=p=>75+620*(p-xmin)/(xmax-xmin),y=p=>320-265*(p-y0)/(y1-y0);
      linea(svg,75,40,75,320);linea(svg,75,320,704,320);
      texto(svg,76,22,`${LABEL[seleccion]} [${unidad}]`);
      texto(svg,354,377,eje==='mach'?'Mach [–]':'T3 [K]',{'text-anchor':'middle'});
      for(let i=0;i<=4;i++){
        const v=y0+(y1-y0)*i/4;texto(svg,67,y(v)+4,numero(v),{'text-anchor':'end'});
        const h=xmin+(xmax-xmin)*i/4;texto(svg,x(h),340,numero(h),{'text-anchor':'middle'});
      }
      series.forEach((s,indice)=>{
        let tramo=[];const color=COLORES[indice%COLORES.length];
        let regimenAnterior=null;
        const acabar=()=>{if(tramo.length>1)svg.appendChild(crear('polyline',{
          points:tramo.join(' '),fill:'none',stroke:color,'stroke-width':2.5}));tramo=[];};
        s.puntos.forEach(p=>{
          if(!valido(p)||!Number.isFinite(p[seleccion])){acabar();regimenAnterior=null;return;}
          if(regimenAnterior!==null&&p.regimen_tobera!==regimenAnterior)acabar();
          regimenAnterior=p.regimen_tobera;
          tramo.push(`${x(p[eje]).toFixed(3)},${y(p[seleccion]).toFixed(3)}`);
          const punto=crear('circle',{cx:x(p[eje]),cy:y(p[seleccion]),r:4.5,fill:color});
          tooltip(punto,`${eje}=${numero(p[eje])} ${eje==='mach'?'–':'K'}; ${LABEL[seleccion]}=${numero(p[seleccion])} ${unidad}; régimen ${p.regimen_tobera||'sin dato'}; modo ${s.modo}`);
          svg.appendChild(punto);
        });acabar();
        const fijo=eje==='mach'?`T3=${s.constantes.T3} K`:`Mach=${s.constantes.mach}`;
        texto(svg,85,359-indice*16,`${indice===series.length-1?'Actual':'Comparación '+(indice+1)}: ${s.modo}; ${fijo}`,{fill:color});
      });
      return svg;
    };
    const svgMapa=()=>{
      const svg=grafico(770,440),xs=datos.ejes.x,ys=datos.ejes.y,m=clave(),unidad=datos.unidades[m];
      const validos=actual().filter(p=>valido(p)&&Number.isFinite(p[m]));
      const min=validos.length?Math.min(...validos.map(p=>p[m])):null;
      const max=validos.length?Math.max(...validos.map(p=>p[m])):null;
      const ancho=585/xs.length,alto=295/ys.length;
      linea(svg,80,45,80,345);linea(svg,80,345,675,345);
      texto(svg,80,23,`${LABEL[m]} [${unidad}]`);
      texto(svg,365,405,'Mach de vuelo [–]',{'text-anchor':'middle'});
      texto(svg,18,195,'T3 [K]',{transform:'rotate(-90 18 195)','text-anchor':'middle'});
      for(let j=0;j<ys.length;j++){
        texto(svg,74,55+(ys.length-j-.5)*alto,numero(ys[j]),{'text-anchor':'end'});
      }
      xs.forEach((v,i)=>texto(svg,85+(i+.5)*ancho,365,numero(v),{'text-anchor':'middle','font-size':10}));
      actual().forEach((p,index)=>{
        const i=index%xs.length,j=Math.floor(index/xs.length);
        const bueno=valido(p)&&Number.isFinite(p[m]);
        const rect=crear('rect',{x:85+i*ancho,y:50+(ys.length-1-j)*alto,
          width:ancho-1,height:alto-1,fill:bueno?colorMapa49(p[m],min,max):'#b7bdc7',stroke:'#fff'});
        tooltip(rect,`Mach ${numero(p.mach)}; T3 ${numero(p.T3)} K: `+
          (bueno?`${LABEL[m]} ${numero(p[m])} ${unidad}; régimen ${p.regimen_tobera||'sin dato'}`:`${p.estado}: ${p.motivo||'magnitud no definida'}`));
        svg.appendChild(rect);
      });
      if(validos.length){
        for(let i=0;i<=20;i++)svg.appendChild(crear('rect',{x:690,y:50+i*13,
          width:16,height:13,fill:colorMapa49(max-(max-min)*i/20,min,max)}));
        texto(svg,714,57,numero(max));texto(svg,714,318,numero(min));
      }
      texto(svg,89,425,'Gris: sin solución o magnitud no definida · Celdas discretas, sin interpolación',{'font-size':11});
      return svg;
    };
    const pintar=()=>{
      if(!datos)return;
      visor.replaceChildren(datos.tipo==='mapa'?svgMapa():svgLineas());
      zoom=1;aplicarZoom();
      const r=datos.resumen;
      resumen.textContent=`${r.validos}/${r.total} puntos con solución física · ${r.sin_solucion} sin solución · ${numero(r.segundos)} s de cálculo. `+
        `Estado A/B/C: ${datos.modo}. ${obsoleto?'Atención: parámetros del motor cambiados desde este estudio.':''}`;
      if(guardados.length&&datos.tipo!=='mapa'){
        guardados.forEach((anterior,i)=>{
          if(anterior.tipo!==datos.tipo||anterior.metrica!==clave())return;
          const dif=Object.keys(datos.constantes).filter(k=>datos.constantes[k]!==anterior.datos.constantes[k]);
          const nota=doc.createElement('p');
          nota.textContent=`Comparación ${i+1}: ${dif.length?dif.map(k=>k+': '+anterior.datos.constantes[k]+' → '+datos.constantes[k]).join('; '):'Parámetros constantes iguales'}; variable barrida: ${datos.ejes.eje_x}.`;
          resumen.appendChild(nota);
        });
      }
    };
    const aplicarZoom=()=>{
      const svg=visor.querySelector('svg');if(!svg)return;
      svg.style.width=(zoom*100)+'%';svg.style.maxWidth='none';svg.style.maxHeight='none';
    };
    const alternar=()=>{
      const esMapa=tipo.value==='mapa',esT3=tipo.value==='T3';
      pagina.querySelectorAll('[data-study49-axis]').forEach(fs=>{
        const visible=esMapa||fs.dataset.study49Axis===(esT3?'T3':'mach');
        fs.hidden=!visible;fs.querySelectorAll('input').forEach(e=>e.disabled=!visible);
      });
      const limite=formMotor.elements.modo_caudal.value==='acoplado'?(esMapa?6:9):(esMapa?11:21);
      pagina.querySelectorAll('input[name$="_puntos"]').forEach(e=>{
        e.max=String(limite);if(Number(e.value)>limite)e.value=String(limite);
      });
    };
    const descargar=(nombre,blob)=>{
      const url=URL.createObjectURL(blob),a=doc.createElement('a');
      a.href=url;a.download=nombre;doc.body.appendChild(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    };
    const exportar=async formato=>{
      if(!datos)return;
      const nombre=`brayton_estudio_${datos.tipo}_${clave()}`;
      if(formato==='csv'){descargar(nombre+'.csv',new Blob([csv49(datos)],{type:'text/csv;charset=utf-8'}));return;}
      const svg=visor.querySelector('svg');if(!svg)return;
      const copia=svg.cloneNode(true);copia.removeAttribute('style');
      copia.setAttribute('xmlns',NS);
      const fuente=new XMLSerializer().serializeToString(copia);
      if(formato==='svg'){descargar(nombre+'.svg',new Blob([fuente],{type:'image/svg+xml;charset=utf-8'}));return;}
      const img=new Image(),url=URL.createObjectURL(new Blob([fuente],{type:'image/svg+xml'}));
      try{
        await new Promise((ok,fallo)=>{img.onload=ok;img.onerror=fallo;img.src=url;});
        const canvas=doc.createElement('canvas'),vb=svg.viewBox.baseVal;
        canvas.width=vb.width*2;canvas.height=vb.height*2;
        const context=canvas.getContext('2d');if(!context)throw Error('Canvas no disponible');
        context.drawImage(img,0,0,canvas.width,canvas.height);
        const blob=await new Promise(ok=>canvas.toBlob(ok,'image/png'));
        if(!blob)throw Error('PNG no disponible');descargar(nombre+'.png',blob);
      }catch(_error){lectura.textContent='No se pudo exportar PNG; utiliza SVG.';}
      finally{URL.revokeObjectURL(url);}
    };
    doc.querySelectorAll('[data-study49-view]').forEach(b=>b.addEventListener('click',()=>{
      const estudios=b.dataset.study49View==='estudios';
      pagina.hidden=!estudios;doc.getElementById('configuracion').hidden=estudios;
      doc.querySelectorAll('[data-study49-view]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
      if(estudios)pagina.scrollIntoView({block:'start'});
    }));
    tipo.addEventListener('change',()=>{alternar();guardados=[];datos=null;visor.replaceChildren();resumen.textContent='';});
    metrica.addEventListener('change',()=>{guardados=[];pintar();});
    formMotor.addEventListener('input',()=>{if(datos){obsoleto=true;resumen.textContent='Los parámetros cambiaron. Ejecuta un estudio nuevo para actualizar los resultados.';}});
    formMotor.addEventListener('change',()=>{alternar();if(datos){obsoleto=true;resumen.textContent='Configuración modificada: vuelve a calcular el estudio.';}});
    cancelar.addEventListener('click',()=>{version++;peticion?.abort();peticion=null;
      boton.disabled=false;cancelar.hidden=true;estado.textContent='Solicitud cancelada. No se han incorporado resultados atrasados.';});
    form.addEventListener('submit',async evento=>{
      evento.preventDefault();if(peticion)return;
      const config={tipo:tipo.value};new FormData(form).forEach((v,k)=>{config[k]=v;});
      const parametros={};new FormData(formMotor).forEach((v,k)=>{parametros[k]=v;});
      const actual=++version,control=new AbortController();peticion=control;
      boton.disabled=true;cancelar.hidden=false;estado.textContent='Calculando puntos del estudio…';
      lectura.textContent='Esperando el cálculo solicitado…';visor.replaceChildren();
      resumen.textContent='';datos=null;
      try{
        const res=await fetcher('/api/turborreactor/estudio',{method:'POST',
          headers:{'Content-Type':'application/json'},body:JSON.stringify({parametros,estudio:config}),signal:control.signal});
        const salida=await res.json();if(actual!==version)return;
        if(!res.ok||!salida.ok)throw Error(salida.error||'Error del estudio.');
        datos=salida.estudio;obsoleto=false;estado.textContent='Estudio calculado.';
        if(metrica.value==='empuje_N'&&
           !datos.puntos.some(p=>Number.isFinite(p.empuje_N))&&
           datos.puntos.some(p=>Number.isFinite(p.empuje_especifico))){
          metrica.value='empuje_especifico';
          estado.textContent='Estudio calculado. Sin gasto absoluto: se muestra empuje específico.';
        }
        lectura.textContent='Selecciona un punto o una celda para consultar su valor real.';pintar();
      }catch(err){if(actual!==version||err.name==='AbortError')return;
        estado.textContent='No se pudo calcular: '+err.message;lectura.textContent='Sin resultados nuevos.';
      }finally{if(actual===version){peticion=null;boton.disabled=false;cancelar.hidden=true;}}
    });
    doc.getElementById('study49-save').addEventListener('click',()=>{
      if(!datos||datos.tipo==='mapa'){lectura.textContent='Comparación disponible solo para curvas Mach o T3.';return;}
      if(guardados.length>=2)guardados.shift();
      guardados.push({tipo:datos.tipo,metrica:clave(),datos:JSON.parse(JSON.stringify(datos))});
      lectura.textContent=`${guardados.length} configuración(es) guardada(s) para superposición.`;pintar();
    });
    doc.getElementById('study49-clear').addEventListener('click',()=>{guardados=[];pintar();});
    pagina.querySelectorAll('[data-study49-tool]').forEach(b=>b.addEventListener('click',()=>{
      const accion=b.dataset.study49Tool;
      if(accion==='in')zoom=Math.min(4,zoom*1.25);
      else if(accion==='out')zoom=Math.max(1,zoom*.8);
      else if(accion==='reset')zoom=1;
      else{exportar(accion);return;}aplicarZoom();
    }));
    visor.addEventListener('pointerover',e=>{
      const punto=e.target.closest?.('[data-study49-info]');if(punto)lectura.textContent=punto.dataset.study49Info;
    });
    visor.addEventListener('click',e=>{
      const punto=e.target.closest?.('[data-study49-info]');if(punto)lectura.textContent=punto.dataset.study49Info;
    });
    visor.addEventListener('focusin',e=>{
      const punto=e.target.closest?.('[data-study49-info]');if(punto)lectura.textContent=punto.dataset.study49Info;
    });
    alternar();return {csv49};
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={csv49,colorMapa49};
  if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',()=>iniciar49(document,fetch));
})(typeof window!=='undefined'?window:globalThis);
