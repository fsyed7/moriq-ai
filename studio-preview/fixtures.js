export const projects = [
  {id:'F-01',name:'Demo Residence 01',description:'Residential · Concept study',stage:'Concept'},
  {id:'F-02',name:'Demo Studio 02',description:'Workspace · Material study',stage:'Material study'},
  {id:'F-03',name:'Demo Pavilion 03',description:'Landscape · Spatial study',stage:'Spatial study'}
];
export const passage = 'Fictional design note: explore a shaded transition between the arrival space and the central courtyard. Compare light, circulation and material continuity during the next design review.';
export const scenarios = {
  passage:{label:'Sample passage',status:'Fixture passage available',body:passage},
  empty:{label:'No sources',status:'No fixture sources selected',body:null},
  scope:{label:'Scope gap',status:'Jurisdiction / edition not supported',body:null},
  mismatch:{label:'Identity mismatch',status:'Citation identity mismatch — passage withheld',body:null},
  unavailable:{label:'Unavailable',status:'Fixture source unavailable',body:null},
  revoked:{label:'Access removed',status:'Simulated access removal — passage cleared',body:null}
};
export const evidence = Object.freeze({id:'FX-NOTE-001',revision:'demo-r1',jurisdiction:'Not applicable — fictional',edition:'Not applicable',claim_status:'not_assessed',release_allowed:false});
export const longAnswer = [
  '01 / Arrival. This fictional study considers a shaded threshold before the central court. Compare a direct route with a slower sequence of enclosed and open spaces. Record the trade-offs as questions for review, not conclusions about a real building.',
  '02 / Light. Sketch how the transition could feel at different times of day. The fixture contains no solar analysis, site measurements or climate data. A future design review would need those inputs before making performance claims.',
  '03 / Materials. Use the sample note to discuss continuity between the entrance and court. Compare texture, joint rhythm and maintenance questions. No product, assembly, dimension or specification is approved by this demonstration.',
  '04 / Next review. Bring the unresolved questions together: circulation, shade, material transitions and the relationship between inside and outside. The citation below identifies only a fictional passage. It does not validate the proposal or authorize release.'
].join('\n\n');

// Prototype-only persistence contract. Never store typed prompt/answer bodies.
export const FIXTURE_KEY = 'moriq.preview.fixture-chats';
export const STORE_VERSION = 1;
export const LIMITS = Object.freeze({chats:12, turns:40, title:60, bytes:65536});
export const emptyStore = () => ({version:STORE_VERSION, kind:'fixture-only', active:null, chats:[]});
export function validateStore(value){
  if(!value || value.version!==STORE_VERSION || value.kind!=='fixture-only' || !Array.isArray(value.chats) || value.chats.length>LIMITS.chats)throw Error('Invalid fixture store');
  const ids=new Set();
  const chats=value.chats.map(chat=>{
    if(!chat || typeof chat.id!=='string' || !/^fx-[a-zA-Z0-9-]{1,64}$/.test(chat.id) || ids.has(chat.id))throw Error('Invalid chat ID');
    ids.add(chat.id);
    if(typeof chat.title!=='string' || !chat.title.trim() || chat.title.length>LIMITS.title || !projects.some(p=>p.id===chat.project) || !Array.isArray(chat.turns) || chat.turns.length>LIMITS.turns)throw Error('Invalid chat');
    const turns=chat.turns.map(turn=>{
      if(!turn || !['concept','long','gap'].includes(turn.kind) || !Object.hasOwn(scenarios,turn.state))throw Error('Invalid fixture turn');
      return {kind:turn.kind,state:turn.state};
    });
    return {id:chat.id,title:chat.title.trim(),project:chat.project,turns};
  });
  const clean={version:STORE_VERSION,kind:'fixture-only',active:ids.has(value.active)?value.active:null,chats};
  if(new TextEncoder().encode(JSON.stringify(clean)).length>LIMITS.bytes)throw Error('Fixture storage limit');
  return clean;
}
export function fixtureStorage(getStorage){
  let writable=true, baseline;
  return {
    load(){
      try{
        const raw=getStorage().getItem(FIXTURE_KEY);baseline=raw;writable=true;
        if(raw===null)return {data:emptyStore(),notice:''};
        if(raw.length>LIMITS.bytes || new TextEncoder().encode(raw).length>LIMITS.bytes)throw Error('Oversized');
        const parsed=JSON.parse(raw);
        if(parsed?.version!==STORE_VERSION){writable=false;return {data:emptyStore(),notice:'Unsupported saved version. Using temporary fixtures; saved data left untouched.'};}
        return {data:validateStore(parsed),notice:''};
      }catch(error){
        try{getStorage().removeItem(FIXTURE_KEY);baseline=null;return {data:emptyStore(),notice:'Invalid fixture storage was reset. Other browser data was not changed.'};}
        catch{writable=false;return {data:emptyStore(),notice:'Browser storage unavailable. Changes are temporary until refresh.'};}
      }
    },
    save(data){
      if(!writable)return 'Temporary fixture session; saved data is unavailable or uses an unsupported version.';
      try{
        const storage=getStorage();
        if(storage.getItem(FIXTURE_KEY)!==baseline)return 'conflict';
        const raw=JSON.stringify(validateStore(data));
        storage.setItem(FIXTURE_KEY,raw);baseline=raw;
        return '';
      }catch{return 'Could not save locally. Current changes are temporary until refresh.';}
    }
  };
}
export const fixturePrompt = kind => ({concept:'Explore the fictional courtyard concept',long:'Show the long scripted example',gap:'Show a fictional evidence gap'}[kind]);
