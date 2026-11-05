import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {projects, scenarios, evidence} from './fixtures.js';
assert.equal(projects.length,3);
assert.equal(new Set(projects.map(x=>x.id)).size,3);
assert.equal(evidence.claim_status,'not_assessed');
assert.equal(evidence.release_allowed,false);
assert.equal(Object.keys(scenarios).length,6);
for(const [key,value] of Object.entries(scenarios)) assert.equal(typeof value.body==='string',key==='passage');
const app=await readFile(new URL('./app.js',import.meta.url),'utf8');
assert(!/innerHTML|outerHTML|fetch\(|XMLHttpRequest|WebSocket/.test(app));
assert(app.includes("new EventSource('/events')"));
const base='http://127.0.0.1:5175';
for(const resource of ['/','/styles.css','/app.js','/fixtures.js','/review.html']){
  const res=await fetch(base+resource); assert.equal(res.status,200);
  assert(res.headers.get('content-security-policy').includes("connect-src 'self'"));
}
for(const resource of ['/api','/openai','/ollama','/oauth','/server.mjs','/package.json','/.env','/../README.md']) assert.equal((await fetch(base+resource)).status,404);
assert.equal((await fetch(base+'/',{method:'POST',body:'fixture'})).status,405);
console.log('PASS: fixture invariants, six states, text-only rendering, same-origin policy, static allowlist and blocked backend routes.');

const photo=await fetch(base+'/assets/courtyard-villa.jpg');
assert.equal(photo.status,200,'Approved local photo must be served');
assert.equal(photo.headers.get('content-type'),'image/jpeg');
assert.deepEqual(Buffer.from(await photo.arrayBuffer()),await readFile(new URL('./assets/courtyard-villa.jpg',import.meta.url)));
console.log('PASS: local approved image response matches project asset.');
