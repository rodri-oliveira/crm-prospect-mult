import vm from 'node:vm';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const source=readFileSync('static/js/agenda-alerts.js','utf8');
const nodes=new Map();
for(const suffix of ['', '-mobile']){
    for(const name of ['nav-agendamentos','badge-agendamentos','aviso-agendamentos']){
        const classes=new Set();
        nodes.set(name+suffix,{hidden:true,textContent:'',title:'',attributes:{},
            setAttribute(key,value){this.attributes[key]=value;},
            classList:{toggle(key,on){if(on)classes.add(key);else classes.delete(key);},contains:key=>classes.has(key)}});
    }
}
const events={},timers=[];
let calls=0,reloads=0;
let payload={total:0,hoje:0,atrasados:0,urgentes:0};
let respond=async()=>({ok:true,json:async()=>payload});
const document={visibilityState:'visible',getElementById:id=>nodes.get(id),
    addEventListener:(name,fn)=>{(events[name]??=[]).push(fn);}};
const context=vm.createContext({window:{location:{pathname:'/agendamentos',reload(){reloads++;}},
    addEventListener:(name,fn)=>{(events[name]??=[]).push(fn);}},document,
    setInterval:(fn,ms)=>{timers.push({fn,ms});},fetch:(url,options)=>{
        calls++;assert.equal(url,'/api/retornos/stats');assert.equal(options.cache,'no-store');return respond();
    }});
const flush=()=>new Promise(resolve=>setTimeout(resolve,0));
vm.runInContext(source,context);
await flush();
assert.equal(timers.length,1);assert.equal(timers[0].ms,30000);
assert.equal(nodes.get('badge-agendamentos').hidden,true);
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
payload={total:0,hoje:0,atrasados:0,urgentes:0};
await context.window.__crmAgendaAlerts.refresh();
assert.equal(nodes.get('badge-agendamentos').hidden,true);
payload={total:1,hoje:1,atrasados:0,urgentes:0};
await context.window.__crmAgendaAlerts.refresh();
assert.equal(nodes.get('badge-agendamentos').hidden,false);
respond=async()=>({ok:false,json:async()=>({total:0,hoje:0,atrasados:0,urgentes:0})});
await context.window.__crmAgendaAlerts.refresh();
assert.equal(nodes.get('badge-agendamentos').textContent,'1'); // Failed refresh preserves the last good alert.
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
console.log('Agenda alerts: empty -> upcoming -> overdue -> empty -> visible; desktop/mobile updates, no reloads, no duplicate timers, failures preserve valid alerts.');
