/* Execute the actual CNPJ form module with a small DOM and controlled API responses. */
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const fields = new Map();
const ids = ['f_cnpj','cnpjStatus','f_nome','f_endereco','f_cidade','f_estado','f_telefone','f_whatsapp','f_email','f_site','f_responsavel','f_whatsapp_status','btnPreencherCnpj','f_maps_place_id','f_maps_url','observacoes','status_prospeccao','data_retorno','hora_retorno','csrf_token','segmento'];
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
    fields.set('formLead',{querySelector:selector=>fields.get(selector.match(/name="([^"]+)"/)[1])});
    fields.get('f_cnpj').value=first;
    respond=async()=>({ok:true,json:async()=>sample});
}
const fill = module.namespace.preencherDadosCNPJ;
reset();
await fill();
assert.equal(fields.get('f_nome').value,'Loja Teste');
assert.equal(fields.get('f_telefone').value,'(11) 99999-4321');
assert.equal(fields.get('f_email').value,'teste@example.com');
assert.equal(fields.get('f_whatsapp').value,'(11) 99999-4321');
assert.equal(fields.get('f_site').value,'');
assert.equal(fields.get('f_responsavel').value,'');
assert.match(fields.get('cnpjStatus').textContent,/confirmação/);
reset();
fields.get('f_nome').value='Nome revisado';
fields.get('f_whatsapp').value='11988881234';
fields.get('f_email').value='comercial@example.com';
await fill();
assert.equal(fields.get('f_nome').value,'Loja Teste');
assert.equal(fields.get('f_email').value,'teste@example.com');
assert.equal(fields.get('f_whatsapp').value,'(11) 99999-4321');
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
console.log('CNPJ fill: suggested WhatsApp, previous company replaced, stale responses ignored, API errors and partial/inactive data handled.');

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
assert.equal(fields.get('f_whatsapp').value,'(16) 98139-9874');
reset();
respond=async()=>({ok:true,json:async()=>({...sample,consulta_versao:undefined})});
await fill();
assert.match(fields.get('cnpjStatus').textContent,/Reinicie o aplicativo/);
console.log('Default contact response populates phone and suggested WhatsApp, replaces previous WhatsApp and identifies an outdated backend.');
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

// A -> B -> partial C must never mix contacts, Maps identity or notes across companies.
reset();
await fill();
fields.get('f_site').value='https://old.example.com';
fields.get('f_responsavel').value='Responsável antigo';
fields.get('f_maps_place_id').value='old-place';
fields.get('f_maps_url').value='https://maps.google.com/old';
for (const key of ['observacoes','status_prospeccao','data_retorno','hora_retorno']) fields.get(key).value='old value';
fields.get('csrf_token').value='keep-token';
fields.get('segmento').value='Lojas de carros';
context.window.__mapsUseCurrentKey='old-place';
fields.get('f_cnpj').value=second;
respond=async()=>({ok:true,json:async()=>({...sample,cnpj:second,data:{nome_fantasia:'Outra Loja',endereco:'Rua B',cidade:'Mogi das Cruzes',estado:'SP',telefone:'(11) 9370-3015'}})});
await fill();
assert.equal(fields.get('f_nome').value,'Outra Loja');
assert.equal(fields.get('f_cidade').value,'Mogi das Cruzes');
assert.equal(fields.get('f_telefone').value,'(11) 99370-3015');
assert.equal(fields.get('f_whatsapp').value,'(11) 99370-3015');
for (const key of ['f_site','f_responsavel','f_maps_place_id','f_maps_url','f_email','observacoes','status_prospeccao','data_retorno','hora_retorno']) assert.equal(fields.get(key).value,'',key);
assert.equal(context.window.__mapsUseCurrentKey,null);
assert.equal(fields.get('csrf_token').value,'keep-token');
assert.equal(fields.get('segmento').value,'Lojas de carros');
assert.equal(fields.get('f_cnpj').value,second);
respond=async()=>({ok:true,json:async()=>({...sample,cnpj:second,data:{razao_social:'Sem telefone'}})});
await fill();
assert.equal(fields.get('f_nome').value,'Sem telefone');
assert.equal(fields.get('f_telefone').value,'');
assert.equal(fields.get('f_whatsapp').value,'');
assert.equal(fields.get('f_whatsapp_status').hidden,true);
// Landlines and complete mobiles retain their original number of digits.
for (const [input, expected, wa] of [
    ['(11) 3222-1234','(11) 3222-1234',''],
    ['+55 (11) 99370-3015','(11) 99370-3015','(11) 99370-3015'],
    ['(11) 7370-3015','(11) 7370-3015',''],
    ['93703015','9370-3015',''],
]) {
    respond=async()=>({ok:true,json:async()=>({...sample,cnpj:second,data:{razao_social:'Exemplo',telefone:input}})});
    await fill();
    assert.equal(fields.get('f_telefone').value,expected);
    assert.equal(fields.get('f_whatsapp').value,wa);
}
console.log('Sequential CNPJ lookups replace the full company, clear absent contacts/notes/Maps links, preserve selected segments and format legacy mobiles correctly.');

if(process.env.CRM_LIVE_CNPJ_SEQUENCE_JSON){
    reset();
    const sequence=JSON.parse(readFileSync(process.env.CRM_LIVE_CNPJ_SEQUENCE_JSON,'utf8'));
    for(const real of sequence){
        fields.get('f_cnpj').value=real.cnpj;
        respond=async()=>({ok:true,json:async()=>real});
        await fill();
        assert.equal(fields.get('f_nome').value,real.data.nome_fantasia?.trim() || real.data.razao_social);
        assert.equal(fields.get('f_telefone').value,real.data.telefone);
        assert.equal(fields.get('f_whatsapp').value,real.data.whatsapp || '');
        assert.equal(fields.get('f_email').value,real.data.email || '');
        console.log('LIVE SEQUENCE:',real.cnpj,fields.get('f_nome').value,fields.get('f_telefone').value);
    }
}
