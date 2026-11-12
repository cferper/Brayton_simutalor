const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {formatear50_2,iniciarDiagnostico50_2}=require('../../static/diagnostico_motor_50_2.js');
const principal=fs.readFileSync(path.join(__dirname,'../../static/turborreactor_interactivo.js'),'utf8');
const visor=fs.readFileSync(path.join(__dirname,'../../static/diagnostico_motor_50_2.js'),'utf8');

test('solo controlador físico envía una petición, diagnóstico reutiliza respuesta',()=>{
  assert.equal((principal.match(/fetcher\('\/api\/turborreactor\/simular'/g)||[]).length,1);
  assert.doesNotMatch(visor, /\bfetch\s*\(|new\s+XMLHttpRequest|\bWebSocket\s*\(/);
  assert.match(principal,/diagnostico50\?\.actualizado\(datos\)/);
  assert.match(principal,/diagnostico50\?\.pendiente\(/);
});
test('formato de ausencias y números sin inventar cero',()=>{
  assert.equal(formatear50_2(null),'No disponible');
  assert.equal(formatear50_2(NaN),'No disponible');
  assert.match(formatear50_2(101.325),/101/);
});
test('salida segura si la interfaz no dispone del panel',()=>{
  assert.equal(iniciarDiagnostico50_2({getElementById:()=>null}),null);
});
