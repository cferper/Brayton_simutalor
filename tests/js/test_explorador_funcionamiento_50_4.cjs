/* Verificaciones JavaScript M50.4 sin DOM ni navegador. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'../..');
const estudio=require(path.join(root,'static/estudios_parametricos_49_5.js'));
const banco=require(path.join(root,'static/turborreactor_interactivo.js'));
const {aplicarPunto50_4}=banco;
const n=require('node:test');

n('CSV incorpora nuevas métricas C sin convertir nulos en cero',()=>{
  const datos={tipo:'mapa',modo:'acoplado',constantes:{area_garganta_fija:'0.047'},
    unidades:{rpm:'rpm',caudal_corregido:'kg/s ref.'},puntos:[
      {mach:0,T3:1600,estado:'valido',clasificacion:'convergencia_verificada',
       empuje_N:19165,rpm:20000,caudal_corregido:20},
      {mach:.4,T3:1600,estado:'sin_solucion',clasificacion:'fuera_mapa',
       empuje_N:null,rpm:null,caudal_corregido:null}]};
  const csv=estudio.csv49(datos);
  assert.match(csv,/caudal_corregido/);assert.match(csv,/fuera_mapa/);
  assert.match(csv,/# constante area_garganta_fija=0\.047/);
  const filas=csv.trim().split('\r\n');
  assert.ok(filas.at(-1).includes('""'));
  assert.doesNotMatch(filas.at(-1),/"0"/);
});

n('reclasificación visual conserva diferencia entre estado y magnitud ausente',()=>{
  const descripcion=estudio.descripcionPunto({mach:.2,T3:1400,estado:'sin_solucion',
    clasificacion:'sin_convergencia_numerica',rpm:null,motivo:'Sin descenso del residuo'},
    'rpm','rpm');
  assert.match(descripcion,/no disponible/i);
  assert.match(descripcion,/Sin convergencia numérica/);
  assert.match(descripcion,/Sin descenso del residuo/);
});

n('aplicación completa llama una única simulación y guarda la referencia externa',()=>{
  let llamadas=0,aplicaciones=0,preparaciones=0;
  const referencia={valor:'Punto 1 conservado'};
  const formulario={};const entradas={modo_caudal:'acoplado',mach:'0.4',T3:'1550',
    area_garganta_fija:'0.04734811643457149',area_salida_fija:'0.04734811643457149'};
  const exito=aplicarPunto50_4({formulario,entradas,
    aplicarEntradas:(f,e)=>{assert.equal(f,formulario);f.entradas={...e};aplicaciones++;},
    preparar:()=>preparaciones++,solicitar:()=>llamadas++});
  assert.equal(exito,true);assert.equal(llamadas,1);assert.equal(aplicaciones,1);
  assert.equal(preparaciones,1);assert.deepEqual(formulario.entradas,entradas);
  assert.equal(referencia.valor,'Punto 1 conservado');
});

n('no aplica punto de A/B ni ejecuta el motor',()=>{
  let llamadas=0;
  assert.throws(()=>aplicarPunto50_4({formulario:{},entradas:{modo_caudal:'impuesto'},
    aplicarEntradas:()=>llamadas++,preparar:()=>llamadas++,solicitar:()=>llamadas++}));
  assert.equal(llamadas,0);
});

n('reutiliza 49.5 y API sin crear un endpoint paralelo ni interpolaciones',()=>{
  const html=fs.readFileSync(path.join(root,'templates/turborreactor.html'),'utf8');
  const js=fs.readFileSync(path.join(root,'static/estudios_parametricos_49_5.js'),'utf8');
  const api=fs.readFileSync(path.join(root,'web_app.py'),'utf8');
  assert.match(html,/id="study49-apply"/);
  assert.match(html,/id="study49-base"/);
  assert.match(html,/id="study49-metrica"/);
  assert.match(js,/brayton:aplicar-estudio-50-4/);
  assert.match(js,/control=new AbortController\(\)/);
  assert.match(js,/if\(peticion\)return;/);
  assert.match(js,/if\(actual!==version\)return;/);
  assert.match(js,/sin interpolación/);
  assert.match(api,/\/api\/turborreactor\/estudio/);
  assert.match(api,/\/api\/turborreactor\/simular/);
});
