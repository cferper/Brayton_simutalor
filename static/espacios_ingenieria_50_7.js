/* M50.7: organización de vistas; sin física, peticiones HTTP ni nuevos SVG. */
(function(raiz){
  'use strict';
  const GRAFICAS={
    termodinamica:[
      ['ts','T–s'],['temperaturas','Temperaturas'],['presiones','Presiones'],
      ['trabajos','Trabajos'],['balance','Balance'],['informe','Informe y fundamentos']],
    tobera:[
      ['mach','Mach'],['presion','Presión estática'],
      ['temperatura_tobera','Temperatura'],['velocidad_tobera','Velocidad'],
      ['geometria','Geometría'],['funcionamiento','Funcionamiento']]
  };
  const TITULOS={
    motor:'Selecciona un componente y consulta sus estados calculados y ecuaciones.',
    termodinamica:'Estados y balances del núcleo: magnitudes totales frente a estáticas.',
    tobera:'Expansión, geometría y régimen de salida: únicamente resultados calculados.',
    turbomaquinas:'Compresor, turbina y eje: mapas educativos y magnitudes disponibles.'
  };
  function iniciarEspaciosIngenieria50_7(documento,ventana=raiz){
    if(documento.body?.dataset.interfaz!=='interactivo'||documento.body.classList.contains('turbo-50-7-ready'))return null;
    const ids=['motor','termodinamica','tobera','turbomaquinas'];
    const paneles=Object.fromEntries(ids.map(id=>[id,documento.getElementById('espacio-'+id)]));
    const live=documento.getElementById('turbo-live');
    const tabsOriginales=[...documento.querySelectorAll('[data-plot-tab]')];
    const gruposOriginales=[...documento.querySelectorAll('[data-plot-group-button]')];
    if(!live||Object.values(paneles).some(p=>!p)||!tabsOriginales.length)return null;
    // No crear espacios aparentando funciones si falta un nodo real de M48–M50.2.
    if(['estaciones','graficas','turbo-diagnostic-50-2'].some(id=>!documento.getElementById(id))||
        !documento.querySelector('.turbo-engine-educational')||
        !documento.querySelector('.turbo-characterization'))return null;
    const vistas={},hosts={};
    const crear=(tag,clase,texto)=>{
      const el=documento.createElement(tag);
      if(clase)el.className=clase;
      if(texto)el.textContent=texto;
      return el;
    };
    const preparar=(id,opciones)=>{
      const panel=paneles[id];
      const intro=crear('p','turbo-ing57-intro',TITULOS[id]);
      const nav=crear('div','turbo-ing57-subnav');
      nav.setAttribute('role','group');nav.setAttribute('aria-label','Vistas de '+id);
      const botones=new Map(),contenedores=new Map();
      opciones.forEach(([clave,nombre])=>{
        const boton=crear('button','turbo-ing57-tab',nombre);
        boton.type='button';boton.dataset.ing57Tab=clave;
        boton.setAttribute('aria-pressed','false');nav.appendChild(boton);botones.set(clave,boton);
      });
      const titulo=panel.querySelector('.turbo-work-title50');
      if(titulo){titulo.insertAdjacentElement('afterend',intro);intro.insertAdjacentElement('afterend',nav);}
      else panel.prepend(intro,nav);
      let actual=null;
      function seleccionar(clave,{foco=false}={}){
        if(!botones.has(clave))return false;
        actual=clave;panel.dataset.ing57Vista=clave;
        botones.forEach((b,k)=>b.setAttribute('aria-pressed',String(k===clave)));
        contenedores.forEach((elemento,k)=>{elemento.hidden=k!==clave;});
        if(id==='termodinamica'||id==='tobera'){
          const grafica=GRAFICAS[id].some(([k])=>k===clave)&&
            !['informe','funcionamiento'].includes(clave);
          const zona=hosts[id]?.parentElement;
          if(zona)zona.hidden=!grafica;
          // M48 sigue siendo el único responsable de mostrar el SVG activo.
          if(grafica&&documento.body.dataset.activeWorkspace===id){
            const familia=id==='termodinamica'?'ciclo':'tobera';
            const grupo=gruposOriginales.find(b=>b.dataset.plotGroupButton===familia);
            if(grupo&&grupo.getAttribute('aria-pressed')!=='true')grupo.click();
            const original=tabsOriginales.find(b=>b.dataset.plotTab===clave);
            original?.click();
          }
        }
        if(foco)botones.get(clave).focus();
        return true;
      }
      const lista=[...botones.keys()];
      lista.forEach((clave,i)=>{
        const b=botones.get(clave);
        b.addEventListener('click',()=>seleccionar(clave));
        b.addEventListener('keydown',e=>{
          const destino=e.key==='ArrowRight'?(i+1)%lista.length:
            e.key==='ArrowLeft'?(i+lista.length-1)%lista.length:
            e.key==='Home'?0:e.key==='End'?lista.length-1:null;
          if(destino===null)return;
          e.preventDefault();seleccionar(lista[destino],{foco:true});
        });
      });
      const contenido=(clave,elemento)=>{
        elemento.classList.add('turbo-ing57-content');
        elemento.setAttribute('aria-label',opciones.find(x=>x[0]===clave)[1]);
        contenedores.set(clave,elemento);panel.appendChild(elemento);
      };
      vistas[id]={seleccionar,actual:()=>actual,contenido,panel,botones,contenedores};
      return vistas[id];
    };
    // Motor: nodos existentes de M49.7/49.8/50.0 y tablas del informe.
    const motor=preparar('motor',[
      ['componentes','Esquema y ficha'],['estaciones','Estaciones y propiedades']]);
    const esquema=documento.querySelector('.turbo-engine-educational');
    const estaciones=documento.getElementById('estaciones');
    if(esquema)motor.contenido('componentes',esquema);
    if(estaciones){
      const envoltura=estaciones.closest('.turbo-work-legacy50');
      estaciones.hidden=false;motor.contenido('estaciones',estaciones);
      if(envoltura&&!envoltura.querySelector('.turbo-section'))envoltura.remove();
    }
    motor.seleccionar('componentes');

    // Termodinámica: el propio M50.5 mueve #turbo-live al host cuando se navega.
    const termo=preparar('termodinamica',GRAFICAS.termodinamica);
    const crearHost=id=>{
      const caja=crear('div','turbo-ing57-graph');
      const destino=crear('div','turbo-ing57-graph-host');
      destino.id='turbo-ing57-graph-'+id;
      caja.appendChild(destino);paneles[id].appendChild(caja);
      hosts[id]=destino;return caja;
    };
    crearHost('termodinamica');
    const informe=documento.getElementById('graficas');
    if(informe){
      const envoltura=informe.closest('.turbo-work-legacy50');
      informe.hidden=false;termo.contenido('informe',informe);
      if(envoltura&&!envoltura.querySelector('.turbo-section'))envoltura.remove();
    }
    termo.seleccionar('ts');

    // Tobera: las mismas figuras M48 (Mach, p estática, temperatura, velocidad y geometría).
    const tobera=preparar('tobera',GRAFICAS.tobera);
    crearHost('tobera');
    const explicacion=crear('section','turbo-ing57-guide card');
    explicacion.append(
      crear('h3','', 'Interpretación del flujo y límites del modelo'),
      crear('p','', 'La tobera convergente se bloquea en la salida; en una convergente-divergente, el bloqueo se produce en la garganta. El régimen de salida depende de las condiciones y de la geometría.'),
      crear('p','', 'Los perfiles muestran únicamente los estados o tramos que resuelve el modelo. Las curvas y los choques no representan automáticamente la evolución real de una tobera con separación de capa límite.'),
      crear('p','', 'Los parámetros de tobera y sus áreas se modifican en Simulación. El estado y el régimen vigentes proceden de la misma respuesta del motor.')
    );
    const irFicha=crear('button','turbo-ing57-link','Consultar ficha de la tobera en Motor');
    irFicha.type='button';irFicha.addEventListener('click',()=>{
      ventana.controladorNavegacion50_5?.navegar('motor');
      vistas.motor.seleccionar('componentes');
      documento.querySelector('[data-engine-part="tobera"]')
        ?.dispatchEvent(new Event('click',{bubbles:true}));
    });
    explicacion.appendChild(irFicha);
    tobera.contenido('funcionamiento',explicacion);
    tobera.seleccionar('mach');

    // Turbomáquinas: M50.2 es la única fuente del mapa HPC; M49.9 aporta
    // indicadores de compresor, turbina y eje, sin generar mapa gráfico HPT.
    const turb=preparar('turbomaquinas',[
      ['compresor','Compresor y mapa HPC'],['eje','Turbina, eje y rendimientos'],
      ['limites','Alcance y limitaciones']]);
    const diagnostico=documento.getElementById('turbo-diagnostic-50-2');
    const caracterizacion=documento.querySelector('.turbo-characterization');
    if(diagnostico)turb.contenido('compresor',diagnostico);
    if(caracterizacion)turb.contenido('eje',caracterizacion);
    const limitaciones=crear('section','turbo-ing57-guide card');
    limitaciones.append(
      crear('h3','', 'Dominio de los mapas y convergencia'),
      crear('p','', 'Solo el modo C resuelve rpm y un equilibrio del eje con los mapas escalados de NASA T-MATS. En A/B, las magnitudes que requieren ese equilibrio permanecen no disponibles.'),
      crear('p','', 'Rline representa una coordenada de consulta del mapa HPC, no un margen de surge certificado. Un fallo de Newton no demuestra inestabilidad física ni imposibilidad de funcionamiento.'),
      crear('p','', 'No hay visor de mapa HPT validado ni datos experimentales del motor; las lecturas numéricas están limitadas al modelo educativo existente.')
    );
    turb.contenido('limites',limitaciones);
    turb.seleccionar('compresor');

    // Solo la navegación superior M50.5 decide la ubicación de #turbo-live.
    ventana.destinoVisor50_7=espacio=>hosts[espacio]||null;
    ventana.activarEspacioIngenieria50_7=espacio=>{
      const vista=vistas[espacio];
      if(vista&&vista.actual())vista.seleccionar(vista.actual());
    };
    // M48 puede cambiar la pestaña original al reconciliar la disponibilidad.
    // Restituir la selección técnica, incluso si ahora muestra «no disponible».
    if(typeof ventana.MutationObserver==='function'){
      new ventana.MutationObserver(()=>{
        const espacio=documento.body.dataset.activeWorkspace;
        if(hosts[espacio])ventana.activarEspacioIngenieria50_7(espacio);
      }).observe(live,{attributes:true,attributeFilter:['data-estado']});
    }
    documento.body.classList.add('turbo-50-7-ready');
    // Reubicar el visor inicial si la URL ya abre directamente un espacio técnico.
    const activo=documento.body.dataset.activeWorkspace;
    if(['termodinamica','tobera'].includes(activo)){
      // Solo M50.5 recoloca el visor; también en la carga mediante fragmento.
      ventana.controladorNavegacion50_5?.activar(activo);
    }
    return {vistas,hosts,seleccionar:(id,v)=>vistas[id]?.seleccionar(v)??false};
  }
  if(typeof module!=='undefined'&&module.exports)
    module.exports={GRAFICAS,iniciarEspaciosIngenieria50_7};
  raiz.iniciarEspaciosIngenieria50_7=iniciarEspaciosIngenieria50_7;
  if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',
    ()=>iniciarEspaciosIngenieria50_7(document,raiz));
})(typeof window!=='undefined'?window:globalThis);
