import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root = path.dirname(fileURLToPath(import.meta.url));
const files = new Map([['/','index.html'],['/index.html','index.html'],['/styles.css','styles.css'],['/app.js','app.js'],['/fixtures.js','fixtures.js'],['/review.html','review.html'],['/review.js','review.js'],['/assets/courtyard-villa.jpg','assets/courtyard-villa.jpg']]);
const types = {'.jpg':'image/jpeg','.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8'};
const clients = new Set();
const server = http.createServer(async (req,res) => {
  if (!['127.0.0.1:5175','localhost:5175'].includes(req.headers.host)) {res.writeHead(403).end(); return;}
  if (req.method !== 'GET') {res.writeHead(405).end(); return;}
  res.setHeader('Cache-Control','no-store');
  res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'");
  const route = new URL(req.url,'http://localhost').pathname;
  if (route === '/events') {
    res.writeHead(200,{'Content-Type':'text/event-stream','Connection':'keep-alive'}); res.write(': connected\n\n');
    clients.add(res); req.on('close',()=>clients.delete(res)); return;
  }
  if(route === '/favicon.ico'){res.writeHead(204).end();return;}
  const file = files.get(route);
  if (!file) {res.writeHead(404).end('Not available in fixture preview'); return;}
  try {const body=await readFile(path.join(root,file)); res.writeHead(200,{'Content-Type':types[path.extname(file)]}).end(body);}
  catch {res.writeHead(503).end('Preview file temporarily unavailable');}
});
let prior = new Map();
setInterval(async()=>{
  try {
    const version = new Map(await Promise.all([...new Set(files.values())].map(async f=>[f,(await stat(path.join(root,f))).mtimeMs])));
    const changed = [...version].filter(([f,time])=>prior.has(f)&&prior.get(f)!==time).map(([f])=>f);
    if(changed.length) for(const client of clients) client.write('data: '+JSON.stringify(changed)+'\n\n');
    prior=version;
  } catch {} // A file may briefly disappear during an editor's atomic save.
},500).unref();
server.on('error',error=>{console.error(error.message);process.exit(1);});
server.listen(5175,'127.0.0.1',()=>console.log('MORIQ fixture preview: http://127.0.0.1:5175 — auto-refresh on save'));

