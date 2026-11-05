import { projects, scenarios, longAnswer, FIXTURE_KEY, LIMITS, fixtureStorage, fixturePrompt } from './fixtures.js';
const $=selector=>document.querySelector(selector);
const studio=$('.studio');
let selected=projects[0];
let responseTimer = null;
let pendingResponse = null;
let evidenceReturn = null;
let activeResponse = null;
const persistence=fixtureStorage(()=>localStorage);
let loaded=persistence.load();
let saved=loaded.data;
let storageNotice=loaded.notice;
let currentChat=null;
let dialogAction=null;
let dialogReturn=null;
function storageStatus(){ $('#storage-status').textContent=storageNotice||'LOCAL FIXTURES · Scripted messages and fictional names saved on this browser.'; }
function persist(){
  const notice=persistence.save(saved);
  if(notice==='conflict'){
    loaded=persistence.load();saved=loaded.data;storageNotice='Another tab changed saved fixtures. Latest records loaded; please retry your action.';
    route(false);return false;
  }
  if(notice)storageNotice=notice;
  storageStatus();return true;
}
function createChat(project=selected.id){
  if(saved.chats.length>=LIMITS.chats){storageNotice='Limit reached: 12 fixture chats. Delete a chat to create another.';storageStatus();return null;}
  const chat={id:'fx-'+crypto.randomUUID(),title:'Fixture chat '+(saved.chats.length+1),project,turns:[]};
  saved.chats.push(chat);saved.active=chat.id;
  return persist()?chat:null;
}
function openChat(id){const hash='#conversation/'+id;if(location.hash===hash)route();else location.hash=hash;}
function renderChats(){
  $('#chat-list').replaceChildren();
  for(const chat of saved.chats){const link=document.createElement('a');link.href='#conversation/'+chat.id;link.textContent=chat.title;link.setAttribute('aria-current',chat.id===currentChat?.id?'page':'false');$('#chat-list').append(link);}
  $('#rename-chat').disabled=!currentChat;$('#delete-chat').disabled=!currentChat;
}

function panels(){
  const evidenceOpen=studio.classList.contains('inspector-open');
  const navOpen=innerWidth<=650 && studio.classList.contains('nav-open');
  $('.main-shell').inert=evidenceOpen||navOpen;
  $('.demo-bar').inert=evidenceOpen||navOpen;
  $('.skip').inert=evidenceOpen||navOpen;
  $('#navigation').inert=evidenceOpen;
  $('#inspector').inert=!evidenceOpen;
  $('#navigation').setAttribute('role',navOpen?'dialog':'complementary');
  if(navOpen)$('#navigation').setAttribute('aria-modal','true');else $('#navigation').removeAttribute('aria-modal');
}
function navigation(open){studio.classList.toggle('nav-open',open);studio.classList.toggle('nav-collapsed',!open);$('#project-toggle').setAttribute('aria-expanded',String(open));panels();}
function inspector(open, trigger=null){
  if(open){evidenceReturn=trigger||document.activeElement;if(innerWidth<=650)navigation(false);}
  studio.classList.toggle('inspector-open',open);studio.classList.toggle('evidence-closed',!open);$('#evidence-toggle').setAttribute('aria-expanded',String(open));panels();
  if(open)$('#close-evidence').focus();
  else if(evidenceReturn){const target=evidenceReturn.isConnected&&!evidenceReturn.disabled?evidenceReturn:$('#evidence-toggle');target.focus();evidenceReturn=null;}
}
function sendControl(){const busy=responseTimer!==null;$('.send').disabled=!busy&&!$('#prompt').value.trim();$('.send').textContent=busy?'■':'↑';$('.send').setAttribute('aria-label',busy?'Stop scripted response':'Send demo message');}
function cancel(){if(responseTimer!==null){clearTimeout(responseTimer);responseTimer=null;pendingResponse?.remove();pendingResponse=null;$('#chat-status').textContent='Scripted response stopped.';sendControl();$('#prompt').focus();}}
function state(key){
  const item=scenarios[key]||scenarios.empty;
  $('#source-status').textContent=item.status;
  $('#passage').textContent=item.body||'';
  $('#passage-panel').hidden=!item.body;
  if(activeResponse){activeResponse.dataset.state=key;const turn=currentChat?.turns[Number(activeResponse.dataset.turn)];if(turn)turn.state=key;}
  activeResponse?.querySelectorAll('.citation').forEach(button=>button.disabled=!item.body);
  activeResponse?.querySelectorAll('.fixture-excerpt').forEach(node=>node.textContent=item.body||'Passage withheld in this fixture state. No fallback answer is generated.');
}
function reset(){ cancel();activeResponse=null;$('#chat-status').textContent=''; studio.classList.remove('chat-active');inspector(false);$('#welcome').hidden=false;$('#conversation').hidden=true;$('#conversation').replaceChildren();$('#prompt').value='';$('#scenario').value='empty';state('empty');sendControl(); }
for(const project of projects){
  const button=document.createElement('button');button.className='project';button.dataset.project=project.id;
  const symbol=document.createElement('span');symbol.className='project-symbol';symbol.textContent='▱';symbol.setAttribute('aria-hidden','true');
  const label=document.createElement('span');const title=document.createElement('strong');title.textContent=project.name;
  const detail=document.createElement('small');detail.textContent=project.description;label.append(title,detail);button.append(symbol,label);
  button.addEventListener('click',()=>{const chat=saved.chats.find(item=>item.project===project.id)||createChat(project.id);if(chat)openChat(chat.id);});
  $('#projects').append(button);
}
function renderProject(){
  $('#project-title').textContent=currentChat?.title||selected.name;$('#project-stage').textContent=selected.stage;
  $('.source-card>p').textContent=selected.name+' · Synthetic source';
  document.querySelectorAll('.project').forEach(button=>{const active=button.dataset.project===selected.id;button.classList.toggle('active',active);button.setAttribute('aria-current',active?'page':'false');});
}
for(const [key,item] of Object.entries(scenarios)){const option=document.createElement('option');option.value=key;option.textContent=item.label;$('#scenario').append(option);}
$('#scenario').addEventListener('change',event=>{state(event.target.value);persist();});
function message(label,text,excerpt=false){const article=document.createElement('article');article.className='message';const heading=document.createElement('div');heading.className='message-label';heading.textContent=label;const body=document.createElement('p');body.textContent=text;if(excerpt)body.className='fixture-excerpt';article.append(heading,body);$('#conversation').append(article);return article;}
function renderTurn(turn,index){
  const gap=turn.kind==='gap';
  const response=message('MORIQ AI · SCRIPTED EXAMPLE',gap?'Evidence gap. No supported answer is available in this fixture.':turn.kind==='long'?longAnswer:'Start with the relationship between arrival and the courtyard. This scripted example draws on the fictional note below.');
  response.dataset.turn=index;response.dataset.state=turn.state;
  const excerpt=document.createElement('p');excerpt.className='fixture-excerpt';response.append(excerpt);
  const cite=document.createElement('button');cite.className='citation';cite.textContent='[01] Inspect fictional design note ↗';
  cite.addEventListener('click',()=>{activeResponse=response;$('#scenario').value=response.dataset.state;state(response.dataset.state);inspector(true,cite);});response.append(cite);
  activeResponse=response;$('#scenario').value=turn.state;state(turn.state);
}
function showChat(){
  if(!currentChat?.turns.length)return;
  studio.classList.add('chat-active');$('#welcome').hidden=true;$('#conversation').hidden=false;
  currentChat.turns.forEach((turn,index)=>{message('YOU · SAVED FIXTURE',fixturePrompt(turn.kind));renderTurn(turn,index);});
}
function send(text){
  if(responseTimer!==null){cancel();return;}
  if(!text.trim()){$('#chat-status').textContent='Enter a message to start the fixture conversation.';return;}
  if(!currentChat){currentChat=createChat();if(!currentChat)return;history.replaceState(null,'','#conversation/'+currentChat.id);renderProject();renderChats();}
  if(currentChat.turns.length>=LIMITS.turns){$('#chat-status').textContent='This fixture chat has reached 40 saved turns. Start a New Chat.';return;}
  studio.classList.add('chat-active');$('#welcome').hidden=true;$('#conversation').hidden=false;
  // Raw input is displayed for this view only; persisted turns contain enum codes, never text.
  message('YOU · UNSAVED INPUT',text.trim());
  const kind=text.toLowerCase().includes('gap')?'gap':text.toLowerCase().includes('long')?'long':'concept';
  const chat=currentChat;
  pendingResponse=message('MORIQ AI · SCRIPTED DEMO','Preparing a scripted response…');
  $('#chat-status').textContent='Loading fixture. No model request is being made.';
  $('#prompt').value='';$('#prompt').focus();
  responseTimer=setTimeout(()=>{
    pendingResponse?.remove();pendingResponse=null;responseTimer=null;
    const turn={kind,state:kind==='gap'?'scope':'passage'};chat.turns.push(turn);
    renderTurn(turn,chat.turns.length-1);
    if(!persist())return;
    $('#chat-status').textContent=kind==='gap'?'Fixture complete. Evidence gap; no fallback answer.':'Scripted response complete. Only the scripted example was saved.';sendControl();
  },900);
  sendControl();
}
$('#composer').addEventListener('submit',event=>{event.preventDefault();send($('#prompt').value);});
$('#prompt').addEventListener('input',sendControl);
$('#prompt').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();send(event.target.value);}});
document.querySelectorAll('[data-prompt]').forEach(button=>button.addEventListener('click',()=>send(button.dataset.prompt)));
$('#new-session').addEventListener('click',()=>{const chat=createChat();if(chat)openChat(chat.id);});
$('#project-toggle').addEventListener('click',()=>{const open=$('#project-toggle').getAttribute('aria-expanded')!=='true';navigation(open);if(open)$('#new-session').focus();});
$('#evidence-toggle').addEventListener('click',()=>{inspector($('#evidence-toggle').getAttribute('aria-expanded')!=='true');});
$('#close-evidence').addEventListener('click',()=>{inspector(false);});
document.addEventListener('keydown',event=>{
  if($('#chat-dialog').open){
    if(event.key==='Tab'){
      const controls=[...$('#chat-dialog').querySelectorAll('input,button')].filter(node=>node.getClientRects().length);
      const first=controls[0],last=controls.at(-1);
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
      else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
    }
    return;
  }
  const overlay=studio.classList.contains('inspector-open')?$('#inspector'):innerWidth<=650&&studio.classList.contains('nav-open')?$('#navigation'):null;
  if(event.key==='Escape'){
    if(studio.classList.contains('inspector-open'))inspector(false);
    else if(studio.classList.contains('nav-open')){navigation(false);$('#project-toggle').focus();}
  }
  if(event.key==='Tab'&&overlay){
    const controls=[...overlay.querySelectorAll('button:not(:disabled),select,a[href]')].filter(node=>node.getClientRects().length);
    const first=controls[0],last=controls.at(-1);
    if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
    else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
  }
});
renderProject();state('empty');$('#scenario').value='empty';inspector(false);navigation(innerWidth>650);sendControl();
// Only the local dev event stream is used; fixtures never leave the browser.
new EventSource('/events').onmessage=event=>{
  const changed=JSON.parse(event.data);
  if(changed.length===1 && changed[0]==='styles.css'){
    document.querySelector('link[rel="stylesheet"]').href='/styles.css?v='+Date.now();
  }else location.reload();
};
matchMedia('(min-width: 651px)').addEventListener('change',event=>navigation(event.matches));
$('#close-navigation').addEventListener('click',()=>{navigation(false);$('#project-toggle').focus();});


// Landing is explicit; workspace entry restores the last selected fixture chat.
function route(saveSelection=true){
  if($('#chat-dialog').open)$('#chat-dialog').close();
  reset();navigation(innerWidth>650);
  const hash=location.hash.slice(1);
  const requested=hash.startsWith('conversation/')?hash.slice(13):null;
  const legacy=projects.find(p=>p.id===requested);
  let chat=saved.chats.find(item=>item.id===requested);
  let missing=false;
  if(legacy){chat=saved.chats.find(item=>item.project===legacy.id)||createChat(legacy.id);}
  if(hash==='workspace')chat=saved.chats.find(item=>item.id===saved.active)||saved.chats[0];
  else if(requested&&!chat&&!legacy)missing=true;
  const enter=hash==='workspace'||Boolean(requested);
  currentChat=chat||null;
  $('#arrival').hidden=enter;studio.hidden=!enter;
  $('#route-status').textContent=hash&&!enter&&hash!=='landing'?'Unknown link. Enter the fixture workspace to continue.':'';
  if(enter){
    if(chat){saved.active=chat.id;if(saveSelection&&!persist())return;history.replaceState(null,'','#conversation/'+chat.id);selected=projects.find(p=>p.id===chat.project);}
    renderProject();renderChats();showChat();storageStatus();
    if(missing)$('#chat-status').textContent='This fixture chat is missing or was deleted. Choose a saved chat or start a New Chat.';
    $('#prompt').focus();
  }else{renderChats();$('.enter-workspace').focus();}
}
$('#rename-chat').addEventListener('click',()=>openDialog('rename'));
$('#delete-chat').addEventListener('click',()=>openDialog('delete'));
function openDialog(action){
  if(!currentChat)return;
  dialogAction={action,id:currentChat.id};dialogReturn=document.activeElement;
  $('#dialog-title').textContent=action==='rename'?'Rename fixture chat':'Delete fixture chat?';
  $('#dialog-description').textContent=action==='rename'?'Use a fictional name only (1–60 characters). Do not enter private names, documents or secrets.':'Delete “'+currentChat.title+'” and its saved scripted examples from this browser? This cannot be undone.';
  $('#rename-field').hidden=action!=='rename';$('#chat-name').required=action==='rename';$('#chat-name').value=currentChat.title;
  $('#dialog-confirm').textContent=action==='rename'?'Save name':'Delete fixture chat';$('#dialog-error').textContent='';
  $('#chat-dialog').showModal();(action==='rename'?$('#chat-name'):$('#dialog-cancel')).focus();
}
$('#dialog-cancel').addEventListener('click',()=>$('#chat-dialog').close());
$('#chat-dialog').addEventListener('close',()=>{const target=dialogReturn?.isConnected&&!dialogReturn.disabled?dialogReturn:$('#prompt');target.focus();dialogReturn=null;dialogAction=null;});
$('#chat-dialog-form').addEventListener('submit',event=>{
  event.preventDefault();const action=dialogAction;const chat=saved.chats.find(item=>item.id===action?.id);if(!chat){$('#chat-dialog').close();return;}
  if(action.action==='rename'){
    const title=$('#chat-name').value.trim();if(!title){$('#dialog-error').textContent='Enter a fictional chat name.';$('#chat-name').focus();return;}
    chat.title=title;if(!persist())return;renderProject();renderChats();$('#chat-dialog').close();
  }else{
    cancel();saved.chats=saved.chats.filter(item=>item.id!==chat.id);saved.active=saved.chats[0]?.id||null;currentChat=null;
    if(!persist())return;
    $('#chat-dialog').close();history.replaceState(null,'','#workspace');route();
  }
});
addEventListener('hashchange',route);
addEventListener('storage',event=>{
  if(event.key!==FIXTURE_KEY&&event.key!==null)return;
  loaded=persistence.load();saved=loaded.data;storageNotice=loaded.notice||'Saved fixtures changed in another tab. Latest records loaded.';route(false);
});
route();

const courtyardImage=$('#courtyard-image');
function imageFallback(){courtyardImage.hidden=true;$('.arrival-image .asset-placeholder').hidden=false;}
courtyardImage.addEventListener('error',imageFallback);
if(courtyardImage.complete && !courtyardImage.naturalWidth)imageFallback();

const coverImage=$('#cover-image');
function coverFallback(){coverImage.hidden=true;$('.cover-fallback').hidden=false;}
coverImage.addEventListener('error',coverFallback);
if(coverImage.complete && !coverImage.naturalWidth)coverFallback();
