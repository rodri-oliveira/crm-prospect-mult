/* Parse and link the actual ES module graph, without needing a browser. */
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
const cache=new Map();
function moduleAt(file) {
    file=resolve(file);
    if (!cache.has(file)) cache.set(file,new vm.SourceTextModule(readFileSync(file,'utf8'),{identifier:file}));
    return cache.get(file);
}
const root=moduleAt('static/js/modules/prospeccao.js');
await root.link((specifier,referencingModule)=>moduleAt(resolve(dirname(referencingModule.identifier),specifier)));
const source=readFileSync('static/js/modules/dom-safety.js','utf8');
const {escapeHtml,safeHttpUrl}=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
assert.equal(escapeHtml('<img src=x onerror="alert(1)">'),'&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');
for(const bad of ['javascript:alert(1)','data:text/html,x','https://user:pass@example.com'])assert.equal(safeHttpUrl(bad),'');
assert.equal(safeHttpUrl('example.com'),'https://example.com/');
console.log(`Linked ${cache.size} frontend modules; escaping and URL checks passed.`);

// Execute cache versioning against real storage/state code, without a browser.
const storage=new Map();
const context=vm.createContext({window:{},document:{getElementById:()=>null},console,
    localStorage:{getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,String(v)),removeItem:k=>storage.delete(k)}});
const isolated=new Map();
function isolatedAt(file) {
    file=resolve(file);
    if(!isolated.has(file))isolated.set(file,new vm.SourceTextModule(readFileSync(file,'utf8'),{identifier:file,context}));
    return isolated.get(file);
}
const cacheModule=isolatedAt('static/js/modules/maps-cache.js');
await cacheModule.link((s,m)=>isolatedAt(resolve(dirname(m.identifier),s)));
await cacheModule.evaluate();
storage.set('mapsResultsCache',JSON.stringify([{nome:'stale college'}]));
storage.set('mapsLastPayloadCache',JSON.stringify({cidade:'Adamantina',estado:'SP'}));
cacheModule.namespace.readMapsCache();
assert.equal(context.window.__mapsResultsCache.length,0);
cacheModule.namespace.writeMapsCache([{nome:'current store'}],{cidade:'Adamantina',estado:'SP'});
cacheModule.namespace.readMapsCache();
assert.equal(context.window.__mapsResultsCache[0].nome,'current store');
assert.equal(context.window.__mapsLastPayloadCache.resultsVersion,cacheModule.namespace.MAPS_RESULTS_VERSION);
console.log('Old result cache invalidated; current results preserved.');
