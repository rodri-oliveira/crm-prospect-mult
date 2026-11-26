/* Execute the actual CNPJ form module with a small DOM and controlled API responses. */
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const fields = new Map();
const ids = ['f_cnpj','cnpjStatus','f_nome','f_endereco','f_cidade','f_estado','f_telefone','f_whatsapp','f_email','f_site','f_responsavel','f_whatsapp_status','btnPreencherCnpj'];
const first = '11222333000181';
const second = '11444777000161';
const sample = {ok:true,consulta_versao:'20261126-contatos-1', cnpj:first, ativo:true, data:{nome_fantasia:'Loja Teste',razao_social:'Teste LTDA',endereco:'Rua A, 123',cep:'01234567',cidade:'São Paulo',estado:'SP',telefone:'5511999994321',email:'teste@example.com'}};
let respond;
const context = vm.createContext({window:{},document:{getElementById:id=>fields.get(id)},
    Event:class {constructor(type){this.type=type;}}, fetch: (...args)=>respond(...args)});
const module = new vm.SourceTextModule(readFileSync('static/js/modules/cnpj.js','utf8'),{context});
await module.link(()=>{throw new Error('unexpected import');});
await module.evaluate();
function reset() {
    for(const id of ids) fields.set(id,{value:'',textContent:'',className:'',dispatchEvent(){}});
    fields.get('f_cnpj').value=first;
    respond=async()=>({ok:true,json:async()=>sample});
}
const fill = module.namespace.preencherDadosCNPJ;
reset();
await fill();
assert.equal(fields.get('f_nome').value,'Loja Teste');
assert.equal(fields.get('f_telefone').value,'(11) 99999-4321');
assert.equal(fields.get('f_email').value,'teste@example.com');
assert.equal(fields.get('f_whatsapp').value,'');
assert.equal(fields.get('f_site').value,'');
assert.equal(fields.get('f_responsavel').value,'');
assert.match(fields.get('cnpjStatus').textContent,/confirmação/);
reset();
fields.get('f_nome').value='Nome revisado';
fields.get('f_whatsapp').value='11988881234';
fields.get('f_email').value='comercial@example.com';
await fill();
assert.equal(fields.get('f_nome').value,'Nome revisado');
assert.equal(fields.get('f_email').value,'comercial@example.com');
assert.equal(fields.get('f_whatsapp').value,'11988881234');
reset();
let finish;
respond=()=>new Promise(resolve=>{finish=resolve;});
const pending=fill();
fields.get('f_cnpj').value=second;
finish({ok:true,json:async()=>sample});
await pending;
assert.equal(fields.get('f_nome').value,'');
assert.equal(fields.get('f_cnpj').value,second);
reset();
respond=()=>new Promise(resolve=>{finish=resolve;});
const edited=fill();
fields.get('f_telefone').value='11977771234';
finish({ok:true,json:async()=>sample});
await edited;
assert.equal(fields.get('f_telefone').value,'11977771234');
reset();
respond=async()=>({ok:false,json:async()=>({ok:false,message:'Serviço indisponível'})});
await fill();
assert.equal(fields.get('f_nome').value,'');
assert.equal(fields.get('cnpjStatus').textContent,'Serviço indisponível');
reset();
respond=async()=>({ok:true,json:async()=>({...sample,ativo:false,situacao:'BAIXADA',data:{razao_social:'Teste LTDA'}})});
await fill();
assert.equal(fields.get('f_nome').value,'Teste LTDA');
assert.equal(fields.get('f_telefone').value,'');
assert.match(fields.get('cnpjStatus').textContent,/BAIXADA/);
console.log('CNPJ fill: no assumed WhatsApp, manual values preserved, stale responses ignored, API errors and partial/inactive data handled.');

reset();
const contacts={...sample, data:{...sample.data,telefone:'(16) 98139-9874',
    whatsapp:'(16) 98139-9874',whatsapp_confirmado:false,email:'contato@example.com',
    fonte_telefone:'ReceitaWS',telefones:[{nono_digito_ajustado:true}]}};
respond=async()=>({ok:true,json:async()=>contacts});
await fill();
assert.equal(fields.get('f_telefone').value,'(16) 98139-9874');
assert.equal(fields.get('f_whatsapp').value,'(16) 98139-9874');
assert.match(fields.get('f_whatsapp_status').textContent,/não confirmado/);
assert.match(fields.get('cnpjStatus').textContent,/ReceitaWS/);
assert.match(fields.get('cnpjStatus').textContent,/nono dígito/);
assert.equal(fields.get('btnPreencherCnpj').disabled,false);
reset();
fields.get('f_whatsapp').value='(16) 99999-4321';
respond=async()=>({ok:true,json:async()=>contacts});
await fill();
assert.equal(fields.get('f_whatsapp').value,'(16) 99999-4321');
reset();
respond=async()=>({ok:true,json:async()=>({...sample,consulta_versao:undefined})});
await fill();
assert.match(fields.get('cnpjStatus').textContent,/Reinicie o aplicativo/);
console.log('Default contact response populates phone and suggested WhatsApp, preserves manual WhatsApp and identifies an outdated backend.');
// Optional local end-to-end check against the JSON from a real Flask/API lookup.
if(process.env.CRM_LIVE_CNPJ_JSON){
    reset();
    const real=JSON.parse(readFileSync(process.env.CRM_LIVE_CNPJ_JSON,'utf8'));
    respond=async()=>({ok:true,json:async()=>real});
    await fill();
    assert.equal(fields.get('f_telefone').value,real.data.telefone);
    assert.equal(fields.get('f_whatsapp').value,real.data.whatsapp);
    assert.ok(fields.get('f_telefone').value);
    assert.ok(fields.get('f_whatsapp').value);
    console.log('LIVE RESPONSE rendered through the real CNPJ form module:',fields.get('f_telefone').value,fields.get('f_whatsapp').value);
}
