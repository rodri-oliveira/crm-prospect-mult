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
