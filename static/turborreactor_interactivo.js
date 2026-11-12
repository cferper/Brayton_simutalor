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

  // M49.4: el zoom solo transforma la presentación SVG, nunca los datos físicos.
  function escalaGrafica49(valor, factor) {
    return Math.max(1,Math.min(4,Math.round(valor*factor*100)/100));
  }

  function aplicarGeometriaDiseno49(garganta,salida,datos) {
    const ag=datos?.area_garganta_m2,ae=datos?.area_salida_m2;
    if(!Number.isFinite(ag)||!Number.isFinite(ae)||ag<=0||ae<ag)
      throw new Error('La referencia de diseño contiene áreas inválidas.');
    garganta.value=String(ag);
    salida.value=String(ae);
    return {ag,ae};
  }

  function iniciarExplorador49(documento,panel) {
    const visor=panel.querySelector('.turbo-live-plot-viewer');
    if(!visor || !visor.querySelector('[data-plot-action]'))return null;
    const lectura=visor.querySelector('[data-plot-reading]');
    const indicador=visor.querySelector('[data-plot-scale]');
    const escalas=new Map();
    const claveActiva=()=>visor.querySelector('[data-plot-tab][aria-selected="true"]')?.dataset.plotTab;
    const contenedor=clave=>visor.querySelector('[data-live-plot="'+clave+'"]');
    const grafica=()=>contenedor(claveActiva())?.querySelector('svg');
    const informar=texto=>{lectura.textContent=texto;};
    const aplicar=()=>{
      const clave=claveActiva(), escala=escalas.get(clave)||1;
      const svg=grafica();
      if(svg){svg.style.width=(escala*100)+'%';svg.style.maxWidth='none';svg.style.maxHeight='none';}
      indicador.textContent=Math.round(escala*100)+' %';
      visor.querySelectorAll('[data-plot-action]').forEach(b=>b.disabled=!svg);
    };
    const restaurar=()=>{
      escalas.clear();
      visor.querySelectorAll('[data-live-plot]').forEach(e=>{e.scrollLeft=0;e.scrollTop=0;});
      informar('Selecciona un punto marcado para consultar datos calculados.');
      aplicar();
    };
    const ampliar=factor=>{
      const clave=claveActiva(), elemento=contenedor(clave);
      if(!elemento?.querySelector('svg'))return;
      escalas.set(clave,escalaGrafica49(escalas.get(clave)||1,factor));
      if(factor===0){elemento.scrollLeft=0;elemento.scrollTop=0;}
      aplicar();
    };
    const descargar=(nombre,blob)=>{
      const url=URL.createObjectURL(blob), enlace=documento.createElement('a');
      enlace.href=url;enlace.download=nombre;documento.body.appendChild(enlace);enlace.click();enlace.remove();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    };
    const exportar=async tipo=>{
      const svg=grafica();if(!svg)return;
      const copia=svg.cloneNode(true);
      copia.removeAttribute('style');
      copia.setAttribute('xmlns','http://www.w3.org/2000/svg');
      const texto=new XMLSerializer().serializeToString(copia);
      const nombre='brayton_'+claveActiva();
      if(tipo==='svg'){
        descargar(nombre+'.svg',new Blob([texto],{type:'image/svg+xml;charset=utf-8'}));
        return;
      }
      // Rasterización local del mismo SVG: sin servidor ni biblioteca externa.
      const caja=svg.viewBox.baseVal,ancho=caja.width||svg.clientWidth,alto=caja.height||svg.clientHeight;
      const imagen=new Image(),url=URL.createObjectURL(new Blob([texto],{type:'image/svg+xml'}));
      try{
        await new Promise((resolve,reject)=>{imagen.onload=resolve;imagen.onerror=reject;imagen.src=url;});
        const canvas=documento.createElement('canvas');canvas.width=ancho*2;canvas.height=alto*2;
        const contexto=canvas.getContext('2d');if(!contexto)throw new Error('Canvas no disponible');
        contexto.drawImage(imagen,0,0,canvas.width,canvas.height);
        const png=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
        if(!png)throw new Error('No se pudo producir PNG');
        descargar(nombre+'.png',png);
      }catch(_error){informar('PNG no disponible en este navegador. Prueba la descarga SVG.');}
      finally{URL.revokeObjectURL(url);}
    };
    visor.querySelectorAll('[data-plot-action]').forEach(b=>b.addEventListener('click',()=>{
      const accion=b.dataset.plotAction;
      if(accion==='in')ampliar(1.25);
      else if(accion==='out')ampliar(.8);
      else if(accion==='reset'){escalas.set(claveActiva(),1);ampliar(1);}
      else exportar(accion);
    }));
    const punto=evento=>evento.target?.closest?.('[data-plot-info]');
    for(const tipo of ['pointerover','focusin','click'])visor.addEventListener(tipo,evento=>{
      const p=punto(evento);if(p)informar(p.getAttribute('data-plot-info'));
    });
    visor.addEventListener('keydown',evento=>{
      if(!['Enter',' '].includes(evento.key))return;
      const p=punto(evento);
      if(p){evento.preventDefault();informar(p.getAttribute('data-plot-info'));}
    });
    visor.addEventListener('wheel',evento=>{
      if(!evento.ctrlKey || !grafica())return;
      evento.preventDefault();ampliar(evento.deltaY<0?1.25:.8);
    },{passive:false});
    return {aplicar,restaurar};
  }

  // M49.7: estado visual local; no recibe fetcher ni referencia al controlador físico.
  function iniciarEsquemaEducativo49_7(documento, alSeleccionar) {
    const esquema=documento.querySelector('.turbo-engine-educational');
    if(!esquema)return null;
    const piezas=[...esquema.querySelectorAll('[data-engine-part]')];
    const titulo=esquema.querySelector('#turbo-engine-part-title');
    const descripcion=esquema.querySelector('#turbo-engine-part-description');
    const lista=esquema.querySelector('#turbo-engine-data-list');
    const estadoDatos=esquema.querySelector('#turbo-engine-data-status');
    const ecuaciones=esquema.querySelector('#turbo-engine-equations');
    const botonesFicha=[...esquema.querySelectorAll('[data-engine-tab]')];
    const panelesFicha=[...esquema.querySelectorAll('[data-engine-panel]')];
    let seleccionActual='difusor';
    let datosActuales=null;
    let mensajeDatos='Pendiente de cálculo.';
    const fichas={
      difusor:['Entrada y difusor','Recibe el aire exterior y lo desacelera para proporcionar al compresor unas condiciones de entrada adecuadas. La recuperación de presión total depende de las pérdidas del difusor.'],
      compresor:['Compresor','Incrementa la presión total del aire gracias al trabajo que recibe de la turbina a través del eje. En la compresión también aumenta la temperatura total.'],
      camara:['Cámara de combustión','Aporta energía al flujo mediante un combustible equivalente, elevando su temperatura total. El modelo simplifica la combustión como un balance energético.'],
      turbina:['Turbina','Extrae energía del flujo caliente para accionar el compresor. Al expandirse, el gas reduce su presión y temperatura totales.'],
      eje:['Eje de transmisión','Conecta mecánicamente la turbina con el compresor en el motor monoeje. Transmite trabajo y puede presentar pérdidas mecánicas.'],
      tobera:['Tobera de escape','Expande y acelera los gases de salida, convirtiendo parte de la entalpía disponible en velocidad y contribuyendo al empuje del motor.']
    };
    const formulas={
      difusor:[['h(Tt0) = h(T∞) + V∞²/2000','h en kJ/kg, V∞ en m/s; el aire en vuelo eleva su entalpía total.'],['pt2 = πd · pt0','pt en kPa; πd es la recuperación de presión total (adimensional).']],
      compresor:[['wc = h(T2) − h(T1)','Trabajo específico en kJ/kg de aire, usando entalpías de remanso cp(T).'],['ηc = [h(T2s) − h(T1)] / [h(T2) − h(T1)]','Rendimiento isentrópico adimensional. T2s es la salida isentrópica de referencia.']],
      camara:[['h(T2) + ηb · f · PCI = (1+f) · h(T3)','Entalpías y PCI en kJ/kg; f en kg combustible/kg aire. T3 es la entrada a turbina.'],['p3 = (1−δ) · p2','Presiones totales en kPa; δ es la pérdida relativa de presión en cámara.']],
      turbina:[['wt = (1+f) · [h(T3) − h(T4)]','Trabajo específico por kg de aire, con el factor másico de gases.'],['ηm · wt = wc','Balance monoeje: el trabajo transmitido por el eje alimenta el compresor.']],
      eje:[['weje = ηm · wt','Trabajos específicos por kg de aire, en kJ/kg; ηm es adimensional.'],['Peje = ṁaire · weje','Potencia en kW si existe caudal absoluto en kg/s; no es el empuje.']],
      tobera:[['h(Tt,entrada) = h(Te) + Ve²/2000','Entalpías en kJ/kg de gas y velocidad de salida en m/s; balance energético de la expansión.'],['Ae/Ag = ε','Relación geométrica adimensional para tobera C-D; solo si existen ambas áreas.']]
    };
    function mostrarFicha() {
      if(estadoDatos)estadoDatos.textContent=datosActuales?'Resultados del punto motor actualizado.':mensajeDatos;
      if(lista?.replaceChildren){
        lista.replaceChildren();
        if(datosActuales){
          for(const dato of datosActuales[seleccionActual]||[]){
            const fila=documento.createElement('div');
            const nombre=documento.createElement('dt');
            const valor=documento.createElement('dd');
            const origen=documento.createElement('small');
            nombre.textContent=dato.etiqueta+' · '+(dato.clase==='total'?'total':dato.clase==='estatica'?'estática':'operación');
            const v=dato.valor;
            const disponible=(typeof v==='number'&&Number.isFinite(v))||(typeof v==='string'&&v.length>0);
            valor.textContent=disponible?(typeof v==='number'?Number(v.toPrecision(6)).toLocaleString('es-ES'):v)+' '+dato.unidad:'No disponible';
            origen.textContent='Origen: '+dato.origen;
            fila.append(nombre,valor,origen);
            lista.append(fila);
          }
        }
      }
      if(ecuaciones?.replaceChildren){
        ecuaciones.replaceChildren();
        for(const [explicacion,significado] of formulas[seleccionActual]||[]){
          const fila=documento.createElement('div');
          fila.className='turbo-engine-equation';
          const expresion=documento.createElement('code');
          expresion.textContent=explicacion;
          const texto=documento.createElement('p');
          texto.textContent=significado;
          fila.append(expresion,texto);
          ecuaciones.append(fila);
        }
      }
    }
    function cambiarApartado(clave){
      if(!['funcionamiento','resultados','ecuaciones'].includes(clave))return false;
      botonesFicha.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.engineTab===clave)));
      panelesFicha.forEach(p=>{p.hidden=p.dataset.enginePanel!==clave;});
      return true;
    }
    botonesFicha.forEach(b=>b.addEventListener('click',()=>cambiarApartado(b.dataset.engineTab)));
    function seleccionar(clave) {
      const ficha=fichas[clave];
      if(!ficha || !piezas.some(p=>p.dataset.enginePart===clave))return false;
      piezas.forEach(p=>{
        const activa=p.dataset.enginePart===clave;
        p.classList.toggle('is-selected',activa);
        p.setAttribute('aria-pressed',String(activa));
      });
      titulo.textContent=ficha[0];
      descripcion.textContent=ficha[1];
      seleccionActual=clave;
      mostrarFicha();
      if(typeof alSeleccionar==='function')alSeleccionar(clave);
      return true;
    }
    function actualizar(datos){
      datosActuales=datos?.componentes||null;
      mensajeDatos='Resultados no disponibles para el punto actual.';
      mostrarFicha();
    }
    function pendiente(mensaje){
      datosActuales=null;
      mensajeDatos=mensaje||'Pendiente de cálculo.';
      mostrarFicha();
    }
    piezas.forEach(p=>{
      p.addEventListener('click',()=>seleccionar(p.dataset.enginePart));
      p.addEventListener('keydown',evento=>{
        if(evento.key!=='Enter' && evento.key!==' ' && evento.key!=='Spacebar')return;
        evento.preventDefault();
        seleccionar(p.dataset.enginePart);
      });
    });
    seleccionar('difusor');
    return {seleccionar,actualizar,pendiente,cambiarApartado};
  }

  // M50.0: relación declarativa entre piezas y estados efectivamente calculados.
  // No contiene ecuaciones, coordenadas ni referencias al controlador de peticiones.
  function iniciarSincronizacion50_0(documento){
    const estado=documento.getElementById('turbo-engine-sync-status');
    if(!estado)return null;
    const relaciones={
      difusor:{entrada:['ambiente'],salida:['pt2']},
      compresor:{entrada:['pt2'],salida:['pt3'],trabajo:'compresor',energia:'compresor'},
      camara:{entrada:['pt3'],salida:['pt4'],energia:'camara'},
      turbina:{entrada:['pt4'],salida:['pt5'],trabajo:'turbina',energia:'turbina'},
      eje:{trabajo:'eje'},
      tobera:{entrada:['pt5'],salida:['garganta','salida'],energia:'tobera'}
    };
    let componente='difusor',estaciones=null;
    const leer=estacion=>estaciones?.find(e=>e.id===estacion&&Number.isFinite(e.T)&&Number.isFinite(e.p));
    function pintar(){
      const relacion=relaciones[componente];
      const validos=new Set();
      const fragmentos=[];
      if(estaciones){
        for(const tipo of ['entrada','salida']){
          const encontrados=(relacion[tipo]||[]).map(leer).filter(Boolean);
          for(const e of encontrados){
            validos.add(e.id);
            const categoria=e.tipo==='Remanso'?'total':'estática';
            fragmentos.push(`${tipo}: ${e.nombre} (${categoria}), T=${Number(e.T.toPrecision(6))} K, p=${Number(e.p.toPrecision(6))} kPa`);
          }
        }
        if(componente==='eje')fragmentos.push('Acoplamiento mecánico: no constituye una estación termodinámica. Véase la barra de trabajo del eje.');
      }
      estado.textContent=!estaciones?'Sin punto motor vigente: las correspondencias gráficas están pendientes.':
        fragmentos.length?fragmentos.join(' · '):'No hay estaciones calculadas disponibles para este componente.';
      for(const punto of documento.querySelectorAll('[data-engine-station],[data-engine-work],[data-engine-energy]')){
        const esEstacion=punto.hasAttribute('data-engine-station');
        const clave=esEstacion?punto.getAttribute('data-engine-station'):
          punto.getAttribute(punto.hasAttribute('data-engine-work')?'data-engine-work':'data-engine-energy');
        const coincide=esEstacion?validos.has(clave):
          (punto.hasAttribute('data-engine-work')?relacion.trabajo===clave:relacion.energia===clave);
        const activo=Boolean(estaciones&&coincide);
        punto.classList.toggle('is-engine-related',activo);
        punto.classList.toggle('is-engine-muted',Boolean(estaciones&&!activo));
      }
    }
    function seleccionar(clave){if(!relaciones[clave])return false;componente=clave;pintar();return true;}
    function actualizar(respuesta){estaciones=Array.isArray(respuesta?.estaciones)?respuesta.estaciones:null;pintar();}
    function pendiente(){estaciones=null;pintar();}
    pintar();
    return {seleccionar,actualizar,pendiente};
  }

  // M49.9: presentación de indicadores, independiente de la API y del solver.
  function iniciarCaracterizacion49_9(documento) {
    const raiz=documento.querySelector('.turbo-characterization');
    if(!raiz)return null;
    const lista=raiz.querySelector('#turbo-characterization-list');
    const estado=raiz.querySelector('#turbo-characterization-status');
    const botones=[...raiz.querySelectorAll('[data-characterization-tab]')];
    const grupos=['funcionamiento','consumo','rendimientos'];
    let grupo='funcionamiento', datos=null, mensaje='Pendiente de cálculo.';
    function renderizar(){
      if(estado)estado.textContent=datos?'Indicadores del punto motor actualizado.':mensaje;
      if(!lista?.replaceChildren)return;
      lista.replaceChildren();
      if(!datos)return;
      for(const indicador of datos[grupo]||[]){
        const tarjeta=documento.createElement('article');
        tarjeta.className='turbo-characterization-card';
        tarjeta.dataset.estado=indicador.estado;
        const titulo=documento.createElement('h5');
        titulo.textContent=indicador.nombre+' · '+indicador.simbolo;
        const lectura=documento.createElement('div');
        lectura.className='turbo-characterization-reading';
        const valor=documento.createElement('strong');
        const n=indicador.valor;
        valor.textContent=typeof n==='number'&&Number.isFinite(n)?Number(n.toPrecision(6)).toLocaleString('es-ES'):'No disponible';
        const unidad=documento.createElement('small');
        unidad.textContent=indicador.unidad;
        lectura.append(valor,unidad);
        const clase=documento.createElement('span');
        clase.className='turbo-characterization-class';
        clase.textContent=indicador.estado==='derivado'?'Derivado':indicador.estado==='calculado'?'Calculado':'No disponible';
        const ayuda=documento.createElement('details');
        const resumen=documento.createElement('summary');
        resumen.textContent='Definición y procedencia';
        const explicacion=documento.createElement('p');
        explicacion.textContent=indicador.formula+' · Origen: '+indicador.fuente+(indicador.nota?' · '+indicador.nota:'');
        ayuda.append(resumen,explicacion);
        tarjeta.append(titulo,lectura,clase,ayuda);
        lista.append(tarjeta);
      }
    }
    function seleccionarGrupo(clave){
      if(!grupos.includes(clave))return false;
      grupo=clave;
      botones.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.characterizationTab===clave)));
      renderizar();
      return true;
    }
    botones.forEach(b=>b.addEventListener('click',()=>seleccionarGrupo(b.dataset.characterizationTab)));
    function actualizar(respuesta){datos=respuesta?.caracterizacion||null;renderizar();}
    function pendiente(texto){datos=null;mensaje=texto||'Pendiente de cálculo.';renderizar();}
    seleccionarGrupo(grupo);
    return {actualizar,pendiente,seleccionarGrupo};
  }

  function inicializar48(documento, fetcher) {
    const formulario=documento.getElementById('turbo-form');
    const panel=documento.getElementById('turbo-live');
    if(!formulario || !panel)return null;
    panel.hidden=false;
    const estado=documento.getElementById('turbo-live-status');
    const banco=documento.body.dataset.interfaz==='interactivo';
    const sincronizacion=banco?iniciarSincronizacion50_0(documento):null;
    const fichaEducativa=banco?iniciarEsquemaEducativo49_7(documento,clave=>sincronizacion?.seleccionar(clave)):null;
    const caracterizacion=banco?iniciarCaracterizacion49_9(documento):null;
    const diagnostico50=banco&&typeof raiz.iniciarDiagnostico50_2==='function'?
      raiz.iniciarDiagnostico50_2(documento):null;
    const laboratorio=banco&&typeof raiz.iniciarLaboratorio50_1==='function'?
      raiz.iniciarLaboratorio50_1(documento,formulario):null;
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
    const grupos=[...panel.querySelectorAll('[data-plot-group-button]')];
    let grupoActivo='ciclo';
    const explorador=banco?iniciarExplorador49(documento,panel):null;
    const activarGrafica=(clave)=>{
      pestañas.forEach(b=>{
        const activo=b.dataset.plotTab===clave;
        b.setAttribute('aria-selected',String(activo));
        b.tabIndex=activo?0:-1;
      });
      panel.querySelectorAll('[data-plot-panel]').forEach(p=>{
        p.hidden=p.dataset.plotPanel!==clave;
      });
      explorador?.aplicar();
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
    const reconciliarPestañas=()=>{
      const actual=pestañas.find(b=>b.getAttribute('aria-selected')==='true');
      if(actual&&!actual.hidden)return;
      const primera=pestañas.find(b=>!b.hidden);
      if(primera)activarGrafica(primera.dataset.plotTab);
    };
    const seleccionarGrupo=(grupo)=>{
      grupoActivo=grupo;
      grupos.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.plotGroupButton===grupo)));
      pestañas.forEach(b=>{b.hidden=b.dataset.plotGroup!==grupo||b.dataset.available==='false';});
      reconciliarPestañas();
    };
    grupos.forEach(b=>b.addEventListener('click',()=>{
      if(b.dataset.plotGroupButton==='estudios'){
        documento.querySelector('[data-study49-view="estudios"]')?.click();
      }else seleccionarGrupo(b.dataset.plotGroupButton);
    }));
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
      explorador?.restaurar();
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
      if(pestaña){
        pestaña.dataset.available=String(disponible);
        pestaña.hidden=!disponible||(banco&&pestaña.dataset.plotGroup!==grupoActivo);
      }
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
        if(tipo==='pendiente'||tipo==='actualizando')sincronizacion?.pendiente();
        if(tipo==='pendiente'||tipo==='actualizando')laboratorio?.pendiente();
        if(tipo==='pendiente'||tipo==='actualizando')diagnostico50?.pendiente('Entradas modificadas: diagnóstico anterior retirado.');
        const badge=documento.querySelector('#resultados .badge');
        if(tipo==='pendiente'){
          fichaEducativa?.pendiente('Entradas modificadas: resultados pendientes de actualización.');
          caracterizacion?.pendiente('Entradas modificadas: indicadores pendientes de actualización.');
        }
        if(tipo==='actualizando'){
          fichaEducativa?.pendiente('Calculando: los resultados anteriores no corresponden a las entradas actuales.');
          caracterizacion?.pendiente('Calculando: indicadores anteriores retirados.');
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
        fichaEducativa?.actualizar(datos);
        caracterizacion?.actualizar(datos);
        diagnostico50?.actualizado(datos);
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
        if(banco){
          dibujar('temperaturas',svg.svg_temperaturas);
          dibujar('presiones',svg.svg_presiones);
          dibujar('trabajos',svg.svg_trabajos_motor);
          dibujar('balance',svg.svg_balance_energetico);
          dibujar('temperatura_tobera',svg.svg_temperatura_axial);
          dibujar('velocidad_tobera',svg.svg_velocidad_axial);
          dibujar('empuje',svg.svg_empuje);
          dibujar('empuje_absoluto',svg.svg_empuje_absoluto);
          dibujar('velocidades',svg.svg_velocidades_extremos);
        }
        reconciliarPestañas();
        explorador?.restaurar();
        laboratorio?.actualizado(datos);
        sincronizacion?.actualizar(datos);
      },
      onError:error=>{
        sincronizacion?.pendiente();
        laboratorio?.pendiente();
        diagnostico50?.pendiente('No hay un punto motor válido para el diagnóstico.');
        fichaEducativa?.pendiente('Sin resultados numéricos verificados para este punto motor.');
        caracterizacion?.pendiente('Sin indicadores verificados para este punto motor.');
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

    const botonGeometria=documento.getElementById('turbo-reset-design-geometry');
    const estadoGeometria=documento.getElementById('turbo-design-geometry-status');
    botonGeometria?.addEventListener('click',async()=>{
      const garganta=formulario.elements.area_garganta_fija;
      const salida=formulario.elements.area_salida_fija;
      if(!banco||selectorModo.value!=='acoplado'||!garganta||!salida)return;
      const anteriores=[garganta.value,salida.value];
      botonGeometria.disabled=true;
      estadoGeometria.textContent='Consultando las áreas del punto de diseño del modelo…';
      try{
        const respuesta=await fetcher('/api/turborreactor/geometria-diseno',{
          headers:{'Accept':'application/json'}
        });
        const datos=await respuesta.json();
        if(!respuesta.ok||datos.ok!==true)throw new Error(datos.error||'Referencia no disponible.');
        if(selectorModo.value!=='acoplado'||garganta.value!==anteriores[0]||
           salida.value!==anteriores[1]){
          estadoGeometria.textContent='Se modificaron los controles durante la consulta; no se han sustituido los valores.';
          return;
        }
        const {ag,ae}=aplicarGeometriaDiseno49(garganta,salida,datos);
        garganta.dispatchEvent(new Event('input',{bubbles:true}));
        salida.dispatchEvent(new Event('input',{bubbles:true}));
        estadoGeometria.textContent='Referencia aplicada: Ag = '+ag.toPrecision(11)+
          ' m²; Ae = '+ae.toPrecision(11)+' m² (Ae/Ag = '+(ae/ag).toPrecision(5)+
          '). Referencia convergente, no C-D optimizada. Puedes editar ambas áreas.';
        controlador.cambiar();
      }catch(error){
        estadoGeometria.textContent='No se han cambiado las áreas: '+(error.message||'consulta fallida');
      }finally{botonGeometria.disabled=false;}
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
      const datosIniciales=documento.getElementById('turbo-engine-initial-data');
      if(fichaEducativa&&datosIniciales){
        try{fichaEducativa.actualizar({componentes:JSON.parse(datosIniciales.textContent)});}
        catch(_error){fichaEducativa.pendiente('No se pueden leer los datos de la ficha inicial.');}
      }
      const diagnosticoInicial=documento.getElementById('turbo-diagnostic-initial-data');
      if(diagnostico50&&diagnosticoInicial){
        try{const datos=JSON.parse(diagnosticoInicial.textContent);
          diagnostico50.actualizado({ok:true,diagnostico_50_2:datos,svg:{}});}
        catch(_error){diagnostico50.pendiente('No se puede leer el diagnóstico inicial.');}
      }
      const caracterizacionInicial=documento.getElementById('turbo-characterization-initial-data');
      if(caracterizacion&&caracterizacionInicial){
        try{caracterizacion.actualizar({caracterizacion:JSON.parse(caracterizacionInicial.textContent)});}
        catch(_error){caracterizacion.pendiente('No se pueden leer los indicadores iniciales.');}
      }
    }
    return controlador;
  }

  if(typeof module!=='undefined'&&module.exports){
    module.exports={crearControlador48,acoplarControl48,escalaGrafica49,
                    iniciarEsquemaEducativo49_7,iniciarCaracterizacion49_9,iniciarSincronizacion50_0,
                    aplicarGeometriaDiseno49,inicializar48};
  }
  if(typeof document!=='undefined'){
    document.addEventListener('DOMContentLoaded',()=>inicializar48(document,fetch));
  }
})(typeof window!=='undefined'?window:globalThis);
