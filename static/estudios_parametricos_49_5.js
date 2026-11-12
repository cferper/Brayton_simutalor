/* M49.5 ampliado M50.4: el servidor calcula; JS presenta muestras sin interpolación. */
(function(root){
  'use strict';
  const NS='http://www.w3.org/2000/svg';
  const LABEL={empuje_N:'Empuje neto',empuje_especifico:'Empuje específico',TSFC:'TSFC',
    caudal_aire:'Caudal de aire',caudal_corregido:'Caudal corregido',rpm:'Giro mecánico',
    rpm_corregidas:'Giro corregido',relacion_compresion:'Relación de compresión',
    rendimiento_compresor:'Rendimiento del compresor',rline:'Rline',
    iteraciones:'Iteraciones',norma_residual:'Norma residual',
    estado_convergencia:'Estado de convergencia'};
  const CLASES={convergencia_verificada:'Convergencia verificada',
    entrada_fuera_dominio:'Entrada fuera de dominio',fuera_mapa:'Fuera del mapa tabulado',
    sin_convergencia_numerica:'Sin convergencia numérica',
    modelo_no_resuelto:'Modelo no resuelto',causa_indeterminada:'Causa indeterminada'};
  const COLOR_CLASE={convergencia_verificada:'#1c806c',entrada_fuera_dominio:'#a65727',
    fuera_mapa:'#744aaa',sin_convergencia_numerica:'#ad4247',
    modelo_no_resuelto:'#9b6d23',causa_indeterminada:'#75818e'};
  const COLORES=['#2563a6','#c05621','#087e74'];
  const valido=p=>p.estado==='valido'&&(!p.clasificacion||p.clasificacion==='convergencia_verificada');
  const numero=v=>typeof v==='number'&&Number.isFinite(v)
    ?v.toLocaleString('es-ES',{maximumSignificantDigits:6}):'No disponible';
  const nulo=v=>v===null||v===undefined;
  function colorMapa49(valor,min,max){
    const f=max===min?.5:(valor-min)/(max-min);
    const h=220-195*Math.max(0,Math.min(1,f));return `hsl(${h} 73% 53%)`;
  }
  function csv49(datos){
    const primeras=['mach','T3','estado','motivo','regimen_tobera','empuje_N','empuje_especifico','TSFC'];
    const adicionales=datos.modo==='acoplado'?['clasificacion','caudal_aire','caudal_corregido',
      'rpm','rpm_corregidas','relacion_compresion','rendimiento_compresor',
      'rline','iteraciones','norma_residual']:[];
    const columnas=[...primeras,...adicionales];
    const escapar=v=>'"'+String(nulo(v)?'':v).replace(/"/g,'""')+'"';
    const unidades=columnas.map(k=>datos.unidades?.[k]?`${k} [${datos.unidades[k]}]`:k).join('; ');
    const encabezado=['# modo='+datos.modo,'# estudio='+datos.tipo,
      ...Object.entries(datos.constantes||{}).map(([k,v])=>'# constante '+k+'='+v),
      '# '+unidades];
    return '\ufeff'+encabezado.join('\r\n')+'\r\n'+columnas.join(';')+'\r\n'+
      datos.puntos.map(p=>columnas.map(c=>escapar(p[c])).join(';')).join('\r\n')+'\r\n';
  }
  function descripcionPunto(p,metrica,unidad){
    const estado=p.clasificacion?CLASES[p.clasificacion]||p.clasificacion:p.estado;
    const valor=metrica==='estado_convergencia'?estado:
      valido(p)&&typeof p[metrica]==='number'?`${LABEL[metrica]} ${numero(p[metrica])} ${unidad}`:
      'Magnitud no disponible';
    return `Mach ${numero(p.mach)}; T3 ${numero(p.T3)} K; ${valor}; ${estado}. ${p.motivo||''}`;
  }
  function iniciar49(doc,fetcher){
    const pagina=doc.getElementById('estudio49');if(!pagina)return null;
    const formMotor=doc.getElementById('turbo-form'),form=doc.getElementById('turbo-study49-form');
    const tipo=doc.getElementById('study49-tipo'),metrica=doc.getElementById('study49-metrica');
    const visor=doc.getElementById('study49-chart'),lectura=doc.getElementById('study49-reading');
    const estado=doc.getElementById('study49-status'),resumen=doc.getElementById('study49-summary');
    const boton=doc.getElementById('study49-run'),cancelar=doc.getElementById('study49-cancel');
    const detalle=doc.getElementById('study49-point'),aplicar=doc.getElementById('study49-apply');
    const origen=doc.getElementById('study49-base');
    let datos=null,guardados=[],peticion=null,version=0,zoom=1,obsoleto=false,seleccion=null;
    let origenCalculado=null;
    const crear=(tag,atributos={},contenido='')=>{
      const e=doc.createElementNS(NS,tag);
      Object.entries(atributos).forEach(([k,v])=>e.setAttribute(k,String(v)));
      if(contenido)e.textContent=contenido;return e;
    };
    const texto=(svg,x,y,valor,extra={})=>svg.appendChild(crear('text',{x,y,'font-size':12,fill:'#243b53',...extra},valor));
    const linea=(svg,x1,y1,x2,y2,color='#64748b')=>svg.appendChild(crear('line',{x1,y1,x2,y2,stroke:color}));
    const grafico=(w=750,h=390)=>crear('svg',{xmlns:NS,viewBox:`0 0 ${w} ${h}`,role:'img',
      'aria-label':'Estudio paramétrico con muestras individuales calculadas'});
    const actual=()=>datos?.puntos||[];
    const clave=()=>metrica.value;
    const tooltip=(elemento,p,index,metrica,unidad)=>{
      const descripcion=descripcionPunto(p,metrica,unidad);
      elemento.dataset.study49Info=descripcion;
      elemento.dataset.study49Index=String(index);
      elemento.setAttribute('tabindex','0');elemento.setAttribute('role','button');
      elemento.setAttribute('aria-label',descripcion);
      elemento.appendChild(crear('title',{},descripcion));
    };
    function svgLineas(){
      const svg=grafico(),eje=datos.ejes.eje_x,m=clave(),unidad=datos.unidades[m]||'–';
      const series=[...guardados.filter(g=>g.tipo===datos.tipo&&g.metrica===m).map(g=>g.datos),datos];
      const valores=series.flatMap(s=>s.puntos.filter(p=>valido(p)&&Number.isFinite(p[m])));
      if(!valores.length)texto(svg,90,120,'Magnitud no disponible: consulta los marcadores grises para conocer la causa.');
      const xmin=Math.min(...series.flatMap(s=>s.ejes.x)),xmax=Math.max(...series.flatMap(s=>s.ejes.x));
      const ymin=valores.length?Math.min(...valores.map(p=>p[m])):0;
      const ymax=valores.length?Math.max(...valores.map(p=>p[m])):1;
      const margen=Math.max((ymax-ymin)*.08,Math.abs(ymax)*.01,1e-8);
      const y0=ymin-margen,y1=ymax+margen;
      const x=v=>75+620*(v-xmin)/(xmax-xmin),y=v=>320-265*(v-y0)/(y1-y0);
      linea(svg,75,40,75,320);linea(svg,75,320,704,320);
      texto(svg,76,22,`${LABEL[m]} [${unidad}]`);
      texto(svg,354,377,eje==='mach'?'Mach [–]':'T3 [K]',{'text-anchor':'middle'});
      for(let i=0;i<=4;i++){
        const v=y0+(y1-y0)*i/4;texto(svg,67,y(v)+4,numero(v),{'text-anchor':'end'});
        const h=xmin+(xmax-xmin)*i/4;texto(svg,x(h),340,numero(h),{'text-anchor':'middle'});
      }
      series.forEach((s,serie)=>{
        let tramo=[];const color=COLORES[serie%COLORES.length];let regimenAnterior=null;
        const terminar=()=>{if(tramo.length>1)svg.appendChild(crear('polyline',{
          points:tramo.join(' '),fill:'none',stroke:color,'stroke-width':2.5}));tramo=[];};
        s.puntos.forEach((p,i)=>{
          if(!valido(p)||!Number.isFinite(p[m])){
            terminar();regimenAnterior=null;
            if(serie===series.length-1){
              // No inventar valores de ordenada: marcador distinto a pie de eje.
              const sinDato=crear('circle',{cx:x(p[eje]),cy:320,
                r:i===seleccion?7:5,fill:'#75818e',stroke:'#fff','stroke-width':1});
              tooltip(sinDato,p,i,m,unidad);svg.appendChild(sinDato);
            }
            return;
          }
          if(regimenAnterior!==null&&p.regimen_tobera!==regimenAnterior)terminar();
          regimenAnterior=p.regimen_tobera;
          tramo.push(`${x(p[eje]).toFixed(3)},${y(p[m]).toFixed(3)}`);
          const punto=crear('circle',{cx:x(p[eje]),cy:y(p[m]),r:serie===series.length-1&&i===seleccion?7:4.5,fill:color});
          if(serie===series.length-1)tooltip(punto,p,i,m,unidad);
          svg.appendChild(punto);
        });terminar();
        const fijo=eje==='mach'?`T3=${s.constantes.T3} K`:`Mach=${s.constantes.mach}`;
        texto(svg,85,359-serie*16,`${serie===series.length-1?'Actual':'Comparación '+(serie+1)}: ${s.modo}; ${fijo}`,{fill:color});
      });return svg;
    }
    function svgMapa(){
      const svg=grafico(770,445),xs=datos.ejes.x,ys=datos.ejes.y,m=clave(),unidad=datos.unidades[m]||'–';
      const categoria=m==='estado_convergencia';
      const validos=actual().filter(p=>valido(p)&&Number.isFinite(p[m]));
      const min=validos.length?Math.min(...validos.map(p=>p[m])):null;
      const max=validos.length?Math.max(...validos.map(p=>p[m])):null;
      const ancho=585/xs.length,alto=295/ys.length;
      linea(svg,80,45,80,345);linea(svg,80,345,675,345);
      texto(svg,80,23,categoria?'Estado de convergencia':`${LABEL[m]} [${unidad}]`);
      texto(svg,365,407,'Mach de vuelo [–]',{'text-anchor':'middle'});
      texto(svg,18,195,'T3 [K]',{transform:'rotate(-90 18 195)','text-anchor':'middle'});
      for(let j=0;j<ys.length;j++)texto(svg,74,55+(ys.length-j-.5)*alto,numero(ys[j]),{'text-anchor':'end'});
      xs.forEach((v,i)=>texto(svg,85+(i+.5)*ancho,365,numero(v),{'text-anchor':'middle','font-size':10}));
      actual().forEach((p,index)=>{
        const i=index%xs.length,j=Math.floor(index/xs.length);
        const bueno=valido(p)&&Number.isFinite(p[m]);
        const clase=p.clasificacion||(valido(p)?'convergencia_verificada':'causa_indeterminada');
        const relleno=categoria?(COLOR_CLASE[clase]||'#75818e'):
          bueno?colorMapa49(p[m],min,max):'#b7bdc7';
        const rect=crear('rect',{x:85+i*ancho,y:50+(ys.length-1-j)*alto,
          width:ancho-1,height:alto-1,fill:relleno,stroke:index===seleccion?'#172e48':'#fff',
          'stroke-width':index===seleccion?3:1});
        tooltip(rect,p,index,m,unidad);
        svg.appendChild(rect);
      });
      if(!categoria&&validos.length){
        for(let i=0;i<=20;i++)svg.appendChild(crear('rect',{x:690,y:50+i*13,
          width:16,height:13,fill:colorMapa49(max-(max-min)*i/20,min,max)}));
        texto(svg,714,57,numero(max));texto(svg,714,318,numero(min));
      }
      if(categoria){
        const clases=datos.resumen.por_clasificacion||{};
        const presentes=Object.entries(clases).filter(([k,v])=>v>0);
        presentes.slice(0,6).forEach(([k,v],i)=>{
          svg.appendChild(crear('rect',{x:80+(i%3)*225,y:414+Math.floor(i/3)*14-7,
            width:9,height:9,fill:COLOR_CLASE[k]}));
          texto(svg,93+(i%3)*225,414+Math.floor(i/3)*14,`${CLASES[k]} (${v})`,{'font-size':9});
        });
      }else texto(svg,89,430,'Gris: sin solución o magnitud ausente · Celdas discretas, sin interpolación',{'font-size':11});
      return svg;
    }
    function aplicarZoom(){
      const svg=visor.querySelector('svg');if(!svg)return;
      svg.style.width=(zoom*100)+'%';svg.style.maxWidth='none';svg.style.maxHeight='none';
    }
    function seleccionada(index){
      if(!datos||!Number.isInteger(index)||index<0||index>=datos.puntos.length)return;
      seleccion=index;const p=datos.puntos[index];
      const items=[['Mach',p.mach,'–'],['T3',p.T3,'K'],
        ['Estado',p.clasificacion?CLASES[p.clasificacion]||p.clasificacion:p.estado,''],
        ['Motivo',p.motivo||p.diagnostico?.resumen||'Sin incidencias',''],
        ['Empuje neto',p.empuje_N,'N'],['Empuje específico',p.empuje_especifico,'N/(kg/s)'],
        ['TSFC',p.TSFC,'kg/(N·h)']];
      if(datos.modo==='acoplado')items.push(
        ['Caudal de aire',p.caudal_aire,'kg/s'],['Caudal corregido',p.caudal_corregido,'kg/s ref.'],
        ['Giro del eje',p.rpm,'rpm'],['Giro corregido',p.rpm_corregidas,'rpm corr.'],
        ['Relación compresión',p.relacion_compresion,'–'],
        ['Rendimiento compresor',p.rendimiento_compresor,'–'],['Rline',p.rline,'–'],
        ['Iteraciones',p.iteraciones,'–'],['Norma residual',p.norma_residual,'–']);
      detalle.replaceChildren();
      const titulo=doc.createElement('h4');titulo.textContent=`Punto ${index+1}: Mach ${numero(p.mach)} · T3 ${numero(p.T3)} K`;
      detalle.appendChild(titulo);
      const tabla=doc.createElement('dl');tabla.className='study49-point-grid';
      items.forEach(([nombre,valor,unidad])=>{
        const dt=doc.createElement('dt');dt.textContent=nombre;
        const dd=doc.createElement('dd');dd.textContent=typeof valor==='number'?`${numero(valor)} ${unidad}`:
          nulo(valor)?'No disponible':String(valor);
        tabla.append(dt,dd);
      });detalle.appendChild(tabla);
      const fijos=doc.createElement('details');fijos.className='study49-fixed';
      const summary=doc.createElement('summary');summary.textContent='Condiciones mantenidas constantes (incluida geometría)';
      const lista=doc.createElement('p');lista.textContent=Object.entries(datos.constantes||{})
        .map(([k,v])=>`${k}: ${v}`).join(' · ');
      fijos.append(summary,lista);detalle.appendChild(fijos);
      aplicar.hidden=!(datos.modo==='acoplado'&&valido(p)&&p.entradas&&!obsoleto);
      lectura.textContent=descripcionPunto(p,clave(),datos.unidades[clave()]||'–');
    }
    function pintar(){
      if(!datos)return;
      const m=clave();const cual=datos.tipo==='mapa'?svgMapa():svgLineas();
      visor.replaceChildren(cual);zoom=1;aplicarZoom();
      const r=datos.resumen;
      resumen.textContent=`${r.validos}/${r.total} puntos con solución verificada en el modelo · ${r.sin_solucion} sin solución · ${numero(r.segundos)} s de cálculo. `+
        `Modo: ${datos.modo}. ${obsoleto?'Atención: configuración cambiada desde este estudio.':''}`;
      if(datos.modo==='acoplado'&&r.por_clasificacion){
        const p=doc.createElement('p');p.textContent=Object.entries(r.por_clasificacion)
          .filter(([k,v])=>v>0).map(([k,v])=>`${CLASES[k]}: ${v}`).join(' · ');
        resumen.appendChild(p);
      }
      if(guardados.length&&datos.tipo!=='mapa'){
        guardados.forEach((anterior,i)=>{
          if(anterior.tipo!==datos.tipo||anterior.metrica!==m)return;
          const dif=Object.keys(datos.constantes).filter(k=>datos.constantes[k]!==anterior.datos.constantes[k]);
          const nota=doc.createElement('p');
          nota.textContent=`Comparación ${i+1}: ${dif.length?dif.map(k=>k+': '+anterior.datos.constantes[k]+' → '+datos.constantes[k]).join('; '):'Parámetros constantes iguales'}; variable barrida: ${datos.ejes.eje_x}.`;
          resumen.appendChild(nota);
        });
      }
      if(seleccion!==null)seleccionada(seleccion);
    }
    function alternar(){
      const esMapa=tipo.value==='mapa',esT3=tipo.value==='T3';
      if(!esMapa&&metrica.value==='estado_convergencia')metrica.value='empuje_N';
      pagina.querySelectorAll('[data-study49-axis]').forEach(fs=>{
        const visible=esMapa||fs.dataset.study49Axis===(esT3?'T3':'mach');
        fs.hidden=!visible;fs.querySelectorAll('input').forEach(e=>e.disabled=!visible);
      });
      const modo=origen.value==='diseno_c'?'acoplado':formMotor.elements.modo_caudal.value;
      const limite=modo==='acoplado'?(esMapa?6:9):(esMapa?11:21);
      pagina.querySelectorAll('input[name$="_puntos"]').forEach(e=>{
        e.max=String(limite);if(Number(e.value)>limite)e.value=String(limite);
      });
      pagina.querySelectorAll('option[data-study49-c]').forEach(e=>{e.disabled=modo!=='acoplado';});
      if(modo!=='acoplado'&&metrica.options?.[metrica.selectedIndex]?.dataset.study49C!==undefined)
        metrica.value='empuje_N';
    }
    function descargar(nombre,blob){
      const url=URL.createObjectURL(blob),a=doc.createElement('a');
      a.href=url;a.download=nombre;doc.body.appendChild(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    }
    async function exportar(formato){
      if(!datos)return;
      const nombre=`brayton_estudio_${datos.tipo}_${clave()}`;
      if(formato==='csv'){descargar(nombre+'.csv',new Blob([csv49(datos)],{type:'text/csv;charset=utf-8'}));return;}
      const svg=visor.querySelector('svg');if(!svg)return;
      const copia=svg.cloneNode(true);copia.removeAttribute('style');copia.setAttribute('xmlns',NS);
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
    }
    doc.querySelectorAll('[data-study49-view]').forEach(b=>b.addEventListener('click',()=>{
      const estudios=b.dataset.study49View==='estudios';
      pagina.hidden=!estudios;doc.getElementById('configuracion').hidden=estudios;
      doc.querySelectorAll('[data-study49-view]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
      if(estudios)pagina.scrollIntoView({block:'start'});
    }));
    tipo.addEventListener('change',()=>{alternar();guardados=[];datos=null;seleccion=null;
      aplicar.hidden=true;detalle.textContent='';visor.replaceChildren();resumen.textContent='';});
    origen.addEventListener('change',()=>{alternar();datos=null;seleccion=null;
      aplicar.hidden=true;detalle.textContent='';visor.replaceChildren();resumen.textContent='';});
    metrica.addEventListener('change',()=>{guardados=[];pintar();});
    const cambiaron=mensaje=>{
      if(!datos||origenCalculado!=='banco')return;
      obsoleto=true;resumen.textContent=mensaje;aplicar.hidden=true;
      detalle.textContent='Resultados del estudio desactualizados; vuelve a calcular.';
    };
    formMotor.addEventListener('input',()=>cambiaron('Los parámetros cambiaron. Ejecuta un estudio nuevo para actualizar los resultados.'));
    formMotor.addEventListener('change',()=>{alternar();cambiaron('Configuración modificada: vuelve a calcular el estudio.');});
    cancelar.addEventListener('click',()=>{version++;peticion?.abort();peticion=null;
      boton.disabled=false;cancelar.hidden=true;estado.textContent='Solicitud cancelada. No se han incorporado resultados atrasados.';});
    form.addEventListener('submit',async evento=>{
      evento.preventDefault();if(peticion)return;
      const config={tipo:tipo.value};new FormData(form).forEach((v,k)=>{config[k]=v;});
      let parametros={};
      if(origen.value==='diseno_c'){
        try{
          const ejemplos=JSON.parse(doc.getElementById('turbo-configuraciones-c-datos').textContent);
          parametros={...ejemplos.find(e=>e.id==='diseno').entradas};
        }catch(_error){estado.textContent='No está disponible la configuración verificada C.';return;}
      }else new FormData(formMotor).forEach((v,k)=>{parametros[k]=v;});
      const fuente=origen.value;
      const actual=++version,control=new AbortController();peticion=control;
      boton.disabled=true;cancelar.hidden=false;estado.textContent='Calculando puntos del estudio…';
      lectura.textContent='Esperando el cálculo solicitado…';visor.replaceChildren();
      resumen.textContent='';detalle.textContent='';aplicar.hidden=true;seleccion=null;datos=null;
      try{
        const res=await fetcher('/api/turborreactor/estudio',{method:'POST',
          headers:{'Content-Type':'application/json'},body:JSON.stringify({parametros,estudio:config}),signal:control.signal});
        const salida=await res.json();if(actual!==version)return;
        if(!res.ok||!salida.ok)throw Error(salida.error||'Error del estudio.');
        datos=salida.estudio;origenCalculado=fuente;obsoleto=false;estado.textContent='Estudio calculado.';
        if(metrica.value==='empuje_N'&&
           !datos.puntos.some(p=>Number.isFinite(p.empuje_N))&&
           datos.puntos.some(p=>Number.isFinite(p.empuje_especifico))){
          metrica.value='empuje_especifico';
          estado.textContent='Estudio calculado. Sin gasto absoluto: se muestra empuje específico.';
        }
        lectura.textContent='Selecciona un punto o celda para consultar sus resultados.';pintar();
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
    const leerPunto=e=>e.target.closest?.('[data-study49-info]');
    visor.addEventListener('pointerover',e=>{const p=leerPunto(e);if(p)lectura.textContent=p.dataset.study49Info;});
    visor.addEventListener('click',e=>{const p=leerPunto(e);if(p){seleccionada(Number(p.dataset.study49Index));pintar();}});
    visor.addEventListener('focusin',e=>{const p=leerPunto(e);if(p)lectura.textContent=p.dataset.study49Info;});
    visor.addEventListener('keydown',e=>{
      if(e.key!=='Enter'&&e.key!==' ')return;
      const p=leerPunto(e);if(!p)return;
      e.preventDefault();seleccionada(Number(p.dataset.study49Index));
      // No redibujar aquí: preserva el foco del elemento activado por teclado.
      p.setAttribute('stroke','#172e48');p.setAttribute('stroke-width','3');
    });
    aplicar.addEventListener('click',()=>{
      const p=datos?.puntos[seleccion];
      if(!p||datos.modo!=='acoplado'||!valido(p)||!p.entradas||obsoleto)return;
      doc.dispatchEvent(new CustomEvent('brayton:aplicar-estudio-50-4',{
        detail:{entradas:{...p.entradas}},bubbles:false}));
      lectura.textContent='Punto trasladado al banco. Se ejecuta una única simulación; el resultado nuevo sustituirá al anterior.';
    });
    alternar();return {csv49};
  }
  if(typeof module!=='undefined'&&module.exports)
    module.exports={csv49,colorMapa49,descripcionPunto,CLASES};
  if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',()=>iniciar49(document,fetch));
})(typeof window!=='undefined'?window:globalThis);
