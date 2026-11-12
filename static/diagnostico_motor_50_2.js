/* M50.2 — visor educativo sin peticiones ni ecuaciones físicas en el navegador. */
(function(raiz){
  'use strict';
  function formatear50_2(valor){
    return typeof valor==='number' && Number.isFinite(valor)
      ?valor.toLocaleString('es-ES',{maximumSignificantDigits:7}):'No disponible';
  }
  function iniciarDiagnostico50_2(documento){
    const region=documento.getElementById('turbo-diagnostic-50-2');
    if(!region)return null;
    const estado=region.querySelector('[data-advanced-status]');
    const valores=region.querySelector('[data-advanced-values]');
    const mapa=region.querySelector('[data-advanced-map]');
    const explicacion=region.querySelector('[data-advanced-domain]');
    const consulta=region.querySelector('[data-advanced-reading]');
    let valido=false;
    function pendiente(mensaje){
      valido=false;
      estado.textContent=mensaje||'Pendiente de punto motor válido.';
      valores.replaceChildren();
      mapa.replaceChildren();
      explicacion.textContent='Sin diagnóstico vigente; no se conservan marcadores anteriores.';
      consulta.textContent='Selecciona un punto tabulado para consultar sus valores.';
    }
    function actualizado(respuesta){
      const datos=respuesta?.diagnostico_50_2;
      if(respuesta?.ok!==true||!datos){pendiente('Diagnóstico no disponible.');return;}
      valido=true;
      estado.textContent='Diagnóstico del punto motor calculado · modo '+
        ({impuesto:'A',fijo:'B',acoplado:'C'}[datos.modo]||datos.modo);
      valores.replaceChildren();
      const filas=[
        ['Caudal corregido',datos.caudal_corregido_kg_s,'kg/s (referencia)'],
        ['Giro mecánico',datos.giro_real_rpm,'rpm'],
        ['Giro corregido',datos.giro_corregido_rpm,'rpm (referencia)'],
        ['Entrada compresor · Tt2',datos.entrada_compresor?.Tt_K,'K'],
        ['Entrada compresor · pt2',datos.entrada_compresor?.pt_kPa,'kPa']
      ];
      for(const [titulo,numero,unidad] of filas){
        const bloque=documento.createElement('div');bloque.className='turbo-diagnostic-reading';
        const termino=documento.createElement('dt');termino.textContent=titulo;
        const valor=documento.createElement('dd');valor.textContent=formatear50_2(numero)+(typeof numero==='number'?' '+unidad:'');
        bloque.append(termino,valor);valores.append(bloque);
      }
      explicacion.textContent=[datos.dominio,datos.limite,...(datos.avisos||[])].join(' ');
      mapa.replaceChildren();
      const svg=respuesta.svg?.svg_mapa_compresor_50_2;
      if(datos.modo==='acoplado'&&typeof svg==='string'&&svg.includes('<svg')){
        const parsed=new DOMParser().parseFromString(svg,'image/svg+xml');
        if(!parsed.querySelector('parsererror')){
          mapa.append(documento.importNode(parsed.documentElement,true));
        }
      }
      if(!mapa.querySelector('svg')){
        const p=documento.createElement('p');p.className='turbo-diagnostic-absent';
        p.textContent=datos.modo==='acoplado'
          ?'Mapa no disponible para un punto acoplado sin datos compatibles.'
          :'El punto de mapa solo se calcula en modo C; los corregidos de A/B no definen por sí solos una línea de operación.';
        mapa.append(p);
      }
      consulta.textContent='Selecciona un marcador tabulado o el punto actual mediante ratón o teclado.';
    }
    function informar(e){
      if(!valido)return;
      const marcador=e.target?.closest?.('[data-plot-info]');
      if(marcador)consulta.textContent=marcador.getAttribute('data-plot-info');
    }
    mapa.addEventListener('pointerover',informar);
    mapa.addEventListener('focusin',informar);
    mapa.addEventListener('click',informar);
    mapa.addEventListener('keydown',e=>{
      if(e.key!=='Enter'&&e.key!==' ')return;
      if(e.target?.closest?.('[data-plot-info]')){e.preventDefault();informar(e);}
    });
    return {pendiente,actualizado};
  }
  raiz.iniciarDiagnostico50_2=iniciarDiagnostico50_2;
  if(typeof module!=='undefined'&&module.exports)module.exports={formatear50_2,iniciarDiagnostico50_2};
})(typeof window!=='undefined'?window:globalThis);
