import vm from 'node:vm';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const source=readFileSync('static/js/agenda-alerts.js','utf8');
const nodes=new Map();
for(const suffix of ['', '-mobile']){
    for(const name of ['nav-agendamentos','badge-agendamentos','aviso-agendamentos']){
        const classes=new Set();
        nodes.set(name+suffix,{hidden:true,textContent:'',title:'',attributes:{},style:{},
            setAttribute(key,value){this.attributes[key]=value;},
            classList:{toggle(key,on){if(on)classes.add(key);else classes.delete(key);},contains:key=>classes.has(key)}});
    }
}
for(const id of ['sidebar-agenda-callout','sidebar-agenda-callout-link','sidebar-agenda-callout-title','sidebar-agenda-callout-text']){
    nodes.set(id,{hidden:true,textContent:'',style:{},attributes:{},setAttribute(key,value){this.attributes[key]=value;}});
}
const events={},timers=[];
let calls=0,reloads=0;
let payload={total:0,hoje:0,atrasados:0,urgentes:0};
let respond=async()=>({ok:true,json:async()=>payload});
const document={visibilityState:'visible',getElementById:id=>nodes.get(id),
    addEventListener:(name,fn)=>{(events[name]??=[]).push(fn);}};
const context=vm.createContext({window:{location:{pathname:'/prospeccao',reload(){reloads++;}},
    addEventListener:(name,fn)=>{(events[name]??=[]).push(fn);}},document,
    AbortController,clearInterval:()=>{},setInterval:(fn,ms)=>{timers.push({fn,ms});return timers.length;},fetch:(url,options)=>{
        calls++;assert.equal(url,'/api/retornos/stats');assert.equal(options.cache,'no-store');return respond();
    }});
const flush=()=>new Promise(resolve=>setTimeout(resolve,0));
vm.runInContext(source,context);
await flush();
assert.equal(timers.length,1);assert.equal(timers[0].ms,30000);
assert.equal(nodes.get('badge-agendamentos').hidden,true);
assert.equal(nodes.get('sidebar-agenda-callout').hidden,true);
payload={total:1,hoje:1,atrasados:0,urgentes:1};
await context.window.__crmAgendaAlerts.refresh();
for(const suffix of ['', '-mobile']){
    assert.equal(nodes.get('badge-agendamentos'+suffix).hidden,false);
    assert.equal(nodes.get('badge-agendamentos'+suffix).textContent,'1');
    assert.ok(nodes.get('nav-agendamentos'+suffix).classList.contains('agenda-urgente'));
}
payload={total:2,hoje:1,atrasados:1,urgentes:1};
await context.window.__crmAgendaAlerts.refresh();
assert.ok(nodes.get('nav-agendamentos').classList.contains('agenda-atrasado'));
assert.ok(nodes.get('badge-agendamentos').classList.contains('animate-pulse-red'));
assert.equal(nodes.get('aviso-agendamentos').textContent,'Atrasados: 1 · Em até 1h: 1');
assert.equal(nodes.get('sidebar-agenda-callout').hidden,false);
assert.equal(nodes.get('sidebar-agenda-callout-title').textContent,'⚠ RETORNOS ATRASADOS');
assert.equal(nodes.get('sidebar-agenda-callout').style.borderColor,'#dc2626');
assert.equal(nodes.get('sidebar-agenda-callout-text').textContent,'Atrasados: 1 · Em até 1h: 1');
assert.equal(nodes.get('nav-agendamentos').style.backgroundColor,'#fef2f2');
payload={total:0,hoje:0,atrasados:0,urgentes:0};
await context.window.__crmAgendaAlerts.refresh();
assert.equal(nodes.get('badge-agendamentos').hidden,true);
payload={total:1,hoje:1,atrasados:0,urgentes:0};
await context.window.__crmAgendaAlerts.refresh();
assert.equal(nodes.get('badge-agendamentos').hidden,false);
respond=async()=>({ok:false,json:async()=>({total:0,hoje:0,atrasados:0,urgentes:0})});
await context.window.__crmAgendaAlerts.refresh();
assert.equal(nodes.get('badge-agendamentos').textContent,'1'); // Failed refresh preserves the last good alert.
assert.equal(nodes.get('sidebar-agenda-callout').hidden,false);
assert.equal(nodes.get('sidebar-agenda-callout-title').textContent,'⚠ VERIFIQUE A AGENDA');
assert.match(nodes.get('sidebar-agenda-callout-text').textContent,/Atualização indisponível/);
respond=async()=>{throw Error('offline');};
await context.window.__crmAgendaAlerts.refresh();
assert.equal(nodes.get('badge-agendamentos').hidden,false);
respond=async()=>({ok:true,json:async()=>payload});
// Re-execution after an HTMX navigation must not install another interval/listener.
vm.runInContext(source,context);await flush();
assert.equal(timers.length,1);assert.equal(events['htmx:afterSwap'].length,1);
const before=calls;document.visibilityState='hidden';
await context.window.__crmAgendaAlerts.refresh();assert.equal(calls,before);
document.visibilityState='visible';events.visibilitychange[0]();await flush();
assert.ok(calls>before);assert.equal(reloads,0);
assert.equal(context.window.location.pathname,'/prospeccao');
console.log('GLOBAL SIDEBAR on Prospecção: prominent overdue notice and unavailable-monitor warning; Agenda alerts: empty -> upcoming -> overdue -> empty -> visible; desktop/mobile updates, no reloads, no duplicate timers, failures preserve valid alerts.');
