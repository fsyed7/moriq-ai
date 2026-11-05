import assert from 'node:assert/strict';
import {fixtureStorage, emptyStore, validateStore, FIXTURE_KEY, LIMITS} from './fixtures.js';
const memory=()=>{const map=new Map();return {map,getItem:key=>map.get(key)??null,setItem:(key,value)=>map.set(key,value),removeItem:key=>map.delete(key)};};
const sample=()=>({version:1,kind:'fixture-only',active:'fx-test',chats:[{id:'fx-test',title:'Fictional courtyard study',project:'F-01',turns:[{kind:'concept',state:'passage'}]}]});
const disk=memory();let adapter=fixtureStorage(()=>disk);
assert.deepEqual(adapter.load().data,emptyStore());assert.equal(adapter.save(sample()),'');assert.deepEqual(fixtureStorage(()=>disk).load().data,sample());
const withPrivateFields=sample();withPrivateFields.chats[0].turns[0].prompt='DO NOT STORE';withPrivateFields.secret='DO NOT STORE';assert.equal(adapter.save(withPrivateFields),'');assert(!disk.getItem(FIXTURE_KEY).includes('DO NOT STORE'));
const stale=sample();stale.active='fx-deleted';assert.equal(validateStore(stale).active,null);
for(const change of [v=>v.chats.push(v.chats[0]),v=>v.chats[0].id='../secret',v=>v.chats[0].project='real-project',v=>v.chats[0].turns[0].kind='custom',v=>v.chats[0].turns[0].state='toString',v=>v.chats[0].title=' ',v=>v.chats[0].title='x'.repeat(61),v=>v.chats[0].turns=Array(41).fill({kind:'concept',state:'passage'}),v=>v.chats=Array.from({length:13},(_,i)=>({...v.chats[0],id:'fx-'+i}))]){const v=sample();change(v);assert.throws(()=>validateStore(v));}
const max=sample();max.chats=Array.from({length:12},(_,i)=>({...max.chats[0],id:'fx-'+i,title:'x'.repeat(60),turns:Array(40).fill({kind:'long',state:'unavailable'})}));assert.equal(validateStore(max).chats.length,12);assert(new TextEncoder().encode(JSON.stringify(max)).length<LIMITS.bytes);
for(const raw of ['{broken',JSON.stringify({...sample(),kind:'backend'}),'x'.repeat(LIMITS.bytes+1)]){disk.setItem(FIXTURE_KEY,raw);disk.setItem('unrelated','keep');const result=fixtureStorage(()=>disk).load();assert.deepEqual(result.data,emptyStore());assert(result.notice.includes('reset'));assert.equal(disk.getItem('unrelated'),'keep');}
disk.setItem(FIXTURE_KEY,JSON.stringify({...sample(),version:99}));adapter=fixtureStorage(()=>disk);assert(adapter.load().notice.includes('Unsupported'));adapter.save(sample());assert.equal(JSON.parse(disk.getItem(FIXTURE_KEY)).version,99);
const blocked=fixtureStorage(()=>{throw Error('blocked');});assert(blocked.load().notice.includes('unavailable'));assert(blocked.save(sample()).includes('Temporary'));
const full=memory();adapter=fixtureStorage(()=>full);adapter.load();full.setItem=()=>{throw Error('quota');};assert(adapter.save(sample()).includes('Could not save'));
const shared=memory();const one=fixtureStorage(()=>shared),two=fixtureStorage(()=>shared);one.load();two.load();assert.equal(one.save(sample()),'');assert.equal(two.save(emptyStore()),'conflict');assert.equal(JSON.parse(shared.getItem(FIXTURE_KEY)).chats.length,1);
one.load();const deleted=emptyStore();assert.equal(one.save(deleted),'');assert.deepEqual(fixtureStorage(()=>shared).load().data,deleted);
console.log('PASS: fixture storage roundtrip, text exclusion, validation, bounds, corrupt recovery, unknown version preservation, blocked/quota handling, conflict detection and deletion.');
