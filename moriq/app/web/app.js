import {renderAnswer} from '/answer.js';
import {FACTS, askAbout, shuffled} from '/facts.js';

const $ = selector => document.querySelector(selector);
const DISCIPLINES = {
  architecture: {image: '/projects/villa-430.jpg', caption: 'Villa 430, Hyderabad', prompts: [
    ['Climate', 'How can a courtyard help cool a home in a hot climate?'],
    ['Planning', 'How does vaastu affect kitchen placement on a narrow linear plot?'],
    ['Structure', 'How do beams and columns carry load to the foundation?'],
    ['Approvals', 'How do I get a building permit in Bahrain?'],
  ]},
  interiors: {image: '/projects/apartment-11.jpg', caption: 'Apartment @ 11, Hyderabad', prompts: [
    ['Materials', 'Which marble care issues matter in a kitchen?'],
    ['Lighting', 'How should I layer lighting in a living room?'],
    ['Joinery', 'How should timber joinery be detailed for air-conditioned rooms?'],
    ['Procurement', 'What should I check before ordering imported furniture?'],
  ]},
  landscape: {image: '/assets/courtyard-villa.jpg', caption: 'Courtyard Villa, Hyderabad', prompts: [
    ['Junctions', 'What should I check where timber decking meets pebble paving?'],
    ['Planting', 'What should I check before planting trees near a structure?'],
    ['Water', 'What does a water feature in a courtyard need?'],
    ['Thresholds', 'How do I connect indoor and outdoor floors at a threshold?'],
  ]},
};
const studio = $('.studio');
const LABELS = {
  general: 'GENERAL EXPLANATION · NOT A MORIQ SOURCE',
  source_supported: 'DRAFT USING RETRIEVED SOURCE · NOT REVIEWED',
  code_evidence: 'DRAFT USING CODE SOURCE · NOT A COMPLIANCE DECISION',
  evidence_gap: 'EVIDENCE GAP · NO ANSWER GENERATED',
  out_of_scope: 'OUTSIDE MORIQ AI SCOPE',
  starter_guide: 'DRAFT USING AI-WRITTEN STARTER GUIDE · NOT A MORIQ DOCUMENT',
  moriq_document: 'DRAFT USING LOADED MORIQ DOCUMENT · NOT INDEPENDENTLY REVIEWED',
  moriq_public: 'DRAFT USING PUBLIC MORIQ RECORD · NOT CONFIRMED BY MORIQ',
  code_gap: 'GENERAL EXPLANATION · NOT A CODE REQUIREMENT',
  public_profile: 'PUBLIC LISTINGS · NOT AN APPROVED MORIQ SOURCE',
  stopped: 'STOPPED · PARTIAL DRAFT',
  failed: 'NO ANSWER',
};
const CHECKS = {
  identity_valid: 'Cited references match the retrieved sources. This does not show the claims are true.',
  uncited: 'The draft did not cite the retrieved sources, so treat it as unsupported.',
  unknown_reference: 'The draft cited a source number that does not exist. Do not rely on it.',
  stale_or_invalid: 'A cited source could not be confirmed as current. Do not rely on it.',
  unexpected_citation: 'The draft shows a citation, but no source was retrieved. Ignore that citation.',
  not_applicable: 'No approved source was retrieved. This is general explanation.',
  unsupported_reference: 'The draft names a code or section that no retrieved source contains. It may be invented, so verify it against the adopted text.',
  unsupported_limit: 'The draft states a measurement that no retrieved source contains. It may be invented, so verify it.',
};
const ERRORS = {
  busy: 'The model is busy with other people\u2019s questions. Try again in a few minutes.',
  unknown_chat: 'This chat no longer exists. Start a new one.',
  invalid_message: 'Enter a message of up to 1,200 characters.',
  chat_full: 'This chat is full. Start a new one.',
  model_unavailable: 'The local model is unavailable. Check that Ollama is running, then try again.',
  empty_response: 'The model returned nothing. Try again.',
};
let workspaces = [], workspace = 'architecture', chats = [], current = null, activeRequest = null;
let reader = null, evidenceReturn = null, dialogAction = null, dialogReturn = null;
let me = null, sessionState = {}, authMode = 'signin', statusLoaded = false, level = 'standard', latestMeta = null, thinkingTimer = null;
const rawText = new WeakMap();
const calm = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
let factOrder = shuffled(), factIndex = 0, factPinned = false;
function nextFact() {
  if (factIndex >= factOrder.length) { factOrder = shuffled(); factIndex = 0; }
  return factOrder[factIndex++];
}
const AUTH_ERRORS = {
  bad_credentials: 'That username or password is not right.',
  locked: 'Too many failed attempts. Wait 15 minutes, then try again.',
  weak_password: 'Use at least 10 characters that are hard to guess and don\u2019t contain your username.',
  wrong_password: 'Your current password is not right.',
  invalid_username: 'Use 2 to 40 lowercase letters, numbers, dots, dashes or underscores.',
  invalid_name: 'Enter a name.',
  username_taken: 'That username is already in use.',
  bad_setup_code: 'That setup code is not right.',
  already_set_up: 'This app is already set up. Sign in instead.',
  cannot_disable_self: 'You can\u2019t disable your own account.',
  last_admin: 'The team needs at least one active admin.',
};

async function api(path, options = {}) {
  const response = await fetch(path, options.body
    ? {...options, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(options.body)} : options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && data.code === 'signed_out') signedOut();
    if (response.status === 403 && data.code === 'password_change_required') showAuth('change');
    throw Object.assign(Error(response.status), {code: data.code});
  }
  return data;
}
function signedOut() {
  me = null; sessionState = {user: null}; chats = []; current = null; statusLoaded = false;
  $('#conversation').replaceChildren();
  showAuth('signin');
}
function field(id, visible) { $(id).hidden = !visible; }
function showAuth(mode, cancellable = false) {
  authMode = mode;
  closeDialogs();
  $('#arrival').hidden = true; studio.hidden = true; $('#signin').hidden = false;
  const setup = mode === 'setup', change = mode === 'change';
  $('#auth-title').textContent = setup ? 'Set Up MORIQ AI' : change ? 'Change Password' : 'Sign In';
  $('#auth-intro').textContent = setup ? 'Create the first account. It becomes the admin, who can add the rest of the team.'
    : change ? (me?.must_change ? 'Choose your own password to finish signing in.' : 'Other devices will need to sign in again.')
    : 'Sign in with the account your admin gave you.';
  field('#auth-code-row', setup && Boolean(sessionState.setup_code_required));
  field('#auth-name-row', setup);
  field('#auth-username-row', !change);
  field('#auth-new-row', change);
  $('#auth-password-label').textContent = change ? 'Current password' : setup ? 'Choose a password' : 'Password';
  $('#auth-password').autocomplete = setup ? 'new-password' : 'current-password';
  $('#auth-submit').textContent = setup ? 'Create Account' : change ? 'Save Password' : 'Sign In';
  $('#auth-cancel').hidden = !cancellable;
  $('#auth-help').textContent = setup || change ? 'Use at least 10 characters.' : 'Forgotten your password? Ask your admin to reset it.';
  $('#auth-error').textContent = '';
  for (const id of ['#auth-password', '#auth-new', '#auth-code']) $(id).value = '';
  (setup && sessionState.setup_code_required ? $('#auth-code') : setup ? $('#auth-name') : change ? $('#auth-password') : $('#auth-username')).focus();
}
async function acceptSession(state) {
  sessionState = state; me = state.user;
  if (me?.must_change) { showAuth('change'); return; }
  $('#signin').hidden = true;
  await loadStatus();
  if (location.hash.slice(1).startsWith('conversation/') || location.hash === '#workspace') route(); else location.hash = '#workspace';
}
async function loadStatus() {
  $('#account-name').textContent = me.name;
  $('#account-initial').textContent = me.name[0].toUpperCase();
  try {
    const status = await api('/api/status');
    workspaces = status.workspaces; statusLoaded = true;
    $('#model-state').textContent = `${status.model_label} ${status.model_ready ? 'ready' : 'offline'}`;
    $('#model-state').classList.toggle('offline', !status.model_ready);
  } catch { $('#model-state').textContent = 'App unavailable'; }
}
function closeDialogs() { document.querySelectorAll('dialog[open]').forEach(dialog => dialog.close()); }
async function renderTeam() {
  const {users} = await api('/api/users');
  $('#team-list').replaceChildren(...users.map(user => {
    const row = element('div', undefined, 'team-row');
    const label = element('span');
    label.append(element('strong', user.name), element('small', `${user.username} \u00b7 ${user.role}${user.active ? '' : ' \u00b7 disabled'}${user.must_change ? ' \u00b7 temporary password' : ''}`));
    const reset = element('button', 'Reset', 'plain');
    reset.setAttribute('aria-label', `Reset password for ${user.name}`);
    reset.addEventListener('click', async () => {
      try { showTemporary(user.username, (await api(`/api/users/${user.id}/reset`, {method: 'POST', body: {}})).temporary_password); await renderTeam(); }
      catch (error) { $('#team-error').textContent = AUTH_ERRORS[error.code] || 'That did not work.'; }
    });
    const toggle = element('button', user.active ? 'Disable' : 'Enable', 'plain' + (user.active ? ' destructive' : ''));
    toggle.setAttribute('aria-label', `${user.active ? 'Disable' : 'Enable'} ${user.name}`);
    toggle.addEventListener('click', async () => {
      $('#team-error').textContent = '';
      try { await api(`/api/users/${user.id}/active`, {method: 'POST', body: {active: !user.active}}); await renderTeam(); }
      catch (error) { $('#team-error').textContent = AUTH_ERRORS[error.code] || 'That did not work.'; }
    });
    row.append(label, reset, toggle);
    return row;
  }));
}
function showTemporary(username, password) {
  const box = $('#team-result');
  box.hidden = false;
  box.replaceChildren(element('strong', `Temporary password for ${username}`), element('code', password), element('small', 'Shown once. Share it privately. They must change it when they first sign in.'));
}
function closeMenus() { document.querySelectorAll('details[open]').forEach(item => { item.open = false; }); }
function setStatus(text) { $('#chat-status').textContent = text; }
function busy() { return reader !== null; }
function sendControl() {
  $('.send').disabled = !busy() && !$('#prompt').value.trim();
  $('.send').textContent = busy() ? '■' : '↑';
  $('.send').setAttribute('aria-label', busy() ? 'Stop answer' : 'Send message');
}
function panels() {
  const evidenceOpen = studio.classList.contains('inspector-open');
  const navOpen = innerWidth <= 700 && studio.classList.contains('nav-open');
  $('.main-shell').inert = evidenceOpen || navOpen;
  $('#navigation').inert = evidenceOpen;
  $('#inspector').inert = !evidenceOpen;
}
function navigation(open) {
  studio.classList.toggle('nav-open', open);
  studio.classList.toggle('nav-collapsed', !open);
  $('#project-toggle').setAttribute('aria-expanded', String(open));
  panels();
}
function inspector(open, trigger = null) {
  if (open) { evidenceReturn = trigger || document.activeElement; if (innerWidth <= 700) navigation(false); }
  studio.classList.toggle('inspector-open', open);
  studio.classList.toggle('evidence-closed', !open);
  $('#evidence-toggle').setAttribute('aria-expanded', String(open));
  panels();
  if (open) $('#close-evidence').focus();
  else if (evidenceReturn) {
    (evidenceReturn.isConnected && !evidenceReturn.disabled ? evidenceReturn : $('#evidence-toggle')).focus();
    evidenceReturn = null;
  }
}
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function evidenceItem(title, lines, number) {
  const item = element('div', undefined, 'evidence-item');
  if (number) item.dataset.number = number;
  item.append(element('h3', title));
  lines.forEach(line => item.append(element('p', line)));
  return item;
}
function showEvidence(meta, trigger, focus = null) {
  $('#evidence-title').textContent = LABELS[meta.label] ? meta.label === 'general' ? 'General explanation' : meta.label === 'evidence_gap' ? 'Evidence gap' : meta.label === 'public_profile' ? 'Public listings' : 'Retrieved sources' : 'This answer';
  $('#evidence-summary').textContent = CHECKS[meta.citation_check] || (meta.label === 'evidence_gap' ? 'No approved source supports an answer, so the model was not asked.' : meta.label === 'public_profile' ? 'These details come from public listings and the firm should confirm them.' : '');
  const items = $('#evidence-items');
  items.replaceChildren();
  const KINDS = {starter_guide: 'AI-written starter guide, not reviewed', owner_document: 'Loaded MORIQ document, not independently reviewed', moriq_public: 'Public listings and press, not confirmed by MORIQ', registry: 'Registry source'};
  (meta.sources || []).forEach(source => items.append(evidenceItem(`[${source.number}] ${source.title}`, [
    `${KINDS[source.kind]} · ${source.source_id}${source.revision ? ' · revision ' + source.revision : ''}`,
    ...(source.jurisdiction ? [`${source.jurisdiction} · ${source.edition}`] : []),
    source.passage,
  ], source.number)));
  (meta.links || []).forEach(link => {
    const item = element('div', undefined, 'evidence-item');
    const anchor = element('a', link.source);
    anchor.href = link.url; anchor.target = '_blank'; anchor.rel = 'noopener noreferrer';
    item.append(element('p', link.text), anchor);
    items.append(item);
  });
  inspector(true, trigger);
  const target = focus && items.querySelector(`[data-number="${focus}"]`);
  if (target) { target.scrollIntoView({block: 'center'}); target.classList.add('focus'); }
}
function setAnswer(article, body, text, meta = null) {
  rawText.set(article, text);
  renderAnswer(body, text, {
    sourceCount: meta?.sources?.length || 0, final: Boolean(meta),
    onCite: meta ? (number, chip) => showEvidence(meta, chip, number) : null,
  });
}
function addMessage(label, text) {
  const article = element('article', undefined, 'message ' + (label === 'YOU' ? 'user' : 'assistant'));
  article.append(element('div', label, 'message-label'));
  const body = element(label === 'YOU' ? 'p' : 'div', label === 'YOU' ? text : undefined, label === 'YOU' ? undefined : 'answer-body');
  article.append(body);
  if (label !== 'YOU') renderAnswer(body, '');
  $('#conversation').append(article);
  return {article, body};
}
function decorate(article, meta) {
  if (meta.label && LABELS[meta.label]) {
    const kind = meta.label === 'evidence_gap' || meta.label === 'out_of_scope' ? ' gap' : meta.label === 'failed' ? ' failed' : '';
    article.querySelector('.message-label').after(element('div', LABELS[meta.label], 'answer-label' + kind));
  }
  if (['unsupported_reference', 'unsupported_limit', 'unknown_reference', 'stale_or_invalid', 'unexpected_citation'].includes(meta.citation_check)) {
    article.querySelector('.answer-label').after(element('p', CHECKS[meta.citation_check], 'answer-warning'));
  }
  const cited = meta.status === 'draft' || (meta.status === 'blocked' && meta.label === 'evidence_gap') || meta.status === 'profile';
  if (cited || meta.status === 'cancelled') {
    const actions = element('div', undefined, 'answer-actions');
    if (cited) {
      latestMeta = meta;
      const button = element('button', `Evidence${meta.sources?.length ? ` · ${meta.sources.length} ${meta.sources.length === 1 ? 'source' : 'sources'}` : ''}`, 'citation');
      button.addEventListener('click', () => showEvidence(meta, button));
      actions.append(button);
    }
    const copy = element('button', 'Copy', 'answer-action');
    copy.setAttribute('aria-label', 'Copy this answer');
    copy.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(rawText.get(article) || ''); copy.textContent = 'Copied'; }
      catch { copy.textContent = 'Could not copy'; }
      setTimeout(() => { copy.textContent = 'Copy'; }, 1800);
    });
    actions.append(copy);
    article.append(actions);
  }
}
function renderChats() {
  $('#chat-list').replaceChildren();
  for (const chat of chats) {
    const link = element('a', chat.title);
    link.href = '#conversation/' + chat.id;
    link.setAttribute('aria-current', chat.id === current?.id ? 'page' : 'false');
    $('#chat-list').append(link);
  }
  $('#rename-chat').disabled = !current;
  $('#delete-chat').disabled = !current;
}
function renderWorkspaces() {
  $('#projects').replaceChildren();
  for (const item of workspaces) {
    const button = element('button', undefined, 'project' + (item.id === workspace ? ' active' : ''));
    button.setAttribute('aria-current', item.id === workspace ? 'page' : 'false');
    const label = element('span');
    label.append(element('strong', item.name), element('small', item.description));
    const symbol = element('span', item.name[0], 'project-symbol');
    symbol.setAttribute('aria-hidden', 'true');
    button.append(symbol, label);
    button.addEventListener('click', () => { workspace = item.id; current = null; location.hash = '#workspace'; route(); });
    $('#projects').append(button);
  }
  const name = workspaces.find(item => item.id === workspace)?.name || 'Architecture';
  $('#project-title').textContent = current?.title || name;
  renderStart();
}
function renderStart() {
  const discipline = DISCIPLINES[workspace] || DISCIPLINES.architecture;
  const hour = new Date().getHours();
  $('#greeting').textContent = `Good ${hour < 12 ? 'morning' : hour < 17 ? 'afternoon' : 'evening'}, ${(me?.name || '').split(' ')[0]}.`;
  const cover = $('#cover-image');
  if (!cover.src.endsWith(discipline.image)) {
    cover.closest('figure').hidden = false;
    cover.src = discipline.image;
    $('#cover-caption').textContent = discipline.caption;
  }
  $('#suggestions').replaceChildren(...discipline.prompts.map(([tag, prompt]) => {
    const button = element('button');
    button.type = 'button';
    button.append(element('small', tag), element('span', prompt));
    button.addEventListener('click', () => ask(prompt));
    return button;
  }));
}
function nearBottom() { const view = $('#workspace'); return view.scrollHeight - view.scrollTop - view.clientHeight < 140; }
function followBottom(follow) { if (follow) $('#workspace').scrollTop = $('#workspace').scrollHeight; updateJump(); }
function updateJump() { $('#jump').hidden = !$('#welcome').hidden || nearBottom(); }
function thinking(article) {
  const box = element('div', undefined, 'thinking');
  const line = element('div', undefined, 'thinking-line');
  const label = element('span', 'Checking what this needs', 'thinking-text');
  const time = element('span', '', 'thinking-time');
  const sources = element('div', undefined, 'thinking-sources');
  const note = element('div', '', 'thinking-note');
  const sketch = $('#sketch-template').content.firstElementChild.cloneNode(true);
  const fact = element('p', '', 'thinking-fact');
  line.append(label, time);
  box.append(sketch, line, sources, fact, note);
  article.querySelector('.answer-body').before(box);
  const started = Date.now();
  clearInterval(thinkingTimer);
  thinkingTimer = setInterval(() => {
    const seconds = Math.round((Date.now() - started) / 1000);
    time.textContent = seconds >= 2 ? `${seconds}s` : '';
    if (seconds >= 12) note.textContent = 'This model runs on your own computer, so answers can take a little while.';
    if (seconds === 4 || (seconds > 4 && (seconds - 4) % 14 === 0)) {
      fact.textContent = `While you wait: ${nextFact().text}`;
      fact.classList.remove('show');
      void fact.offsetWidth;
      fact.classList.add('show');
    }
  }, 1000);
  return {box, label, sources};
}
function endThinking(state) { clearInterval(thinkingTimer); state?.box.remove(); }
function renderConversation() {
  latestMeta = null;
  const hasMessages = Boolean(current?.messages?.length);
  studio.classList.toggle('chat-active', hasMessages);
  $('#welcome').hidden = hasMessages;
  $('#conversation').hidden = !hasMessages;
  $('#conversation').replaceChildren();
  for (const message of current?.messages || []) {
    const isUser = message.role === 'user';
    const {article, body} = addMessage(isUser ? 'YOU' : 'MORIQ AI', message.text);
    if (!isUser) { setAnswer(article, body, message.text, message.meta); decorate(article, message.meta); }
  }
}
async function refreshChats() {
  try { chats = (await api('/api/chats')).chats; } catch { setStatus('Could not load saved chats.'); }
}
let sending = false;
async function ask(text) {
  if (busy()) { await stop(); return; }
  if (sending) return;
  sending = true;
  try { await sendQuestion(text); } finally { sending = false; }
}
async function sendQuestion(text) {
  const message = text.trim();
  if (!message) { setStatus('Enter a question to start.'); return; }
  if (!current) {
    try { current = {...await api('/api/chats', {method: 'POST', body: {workspace}}), messages: []}; }
    catch { setStatus('Could not start a chat. The chat limit may be reached.'); return; }
    history.replaceState(null, '', '#conversation/' + current.id);
  }
  studio.classList.add('chat-active');
  $('#welcome').hidden = true;
  $('#conversation').hidden = false;
  addMessage('YOU', message);
  const {article, body} = addMessage('MORIQ AI', '');
  const progress = thinking(article);
  $('#prompt').value = '';
  $('#prompt').style.height = 'auto';
  closeMenus();
  showFact(false);
  launch();
  $('#workspace').scrollTop = $('#workspace').scrollHeight;
  setStatus('');
  let response;
  try {
    response = await fetch('/api/ask', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({
      chat: current.id, message, jurisdiction: $('#jurisdiction').value, edition: $('#edition').value, level,
    })});
    if (response.status === 401) { endThinking(progress); signedOut(); return; }
    if (response.status === 403) { endThinking(progress); showAuth('change'); return; }
    reader = response.body.getReader();
    sendControl();
    const decoder = new TextDecoder();
    let buffer = '';
    for (;;) {
      const {value, done} = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, {stream: true});
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) if (line) handle(JSON.parse(line), article, body, progress);
    }
  } catch {
    if (!article.querySelector('.answer-label')) decorate(article, {label: 'failed'});
    setStatus('The connection to the local app was lost.');
  }
  endThinking(progress);
  body.classList.remove('streaming');
  reader = null; activeRequest = null;
  sendControl();
  await refreshChats();
  try { current = await api('/api/chats/' + current.id); } catch { /* keep what is on screen */ }
  renderChats(); renderWorkspaces();
  updateJump();
  $('#prompt').focus();
}
function handle(event, article, body, progress) {
  const follow = nearBottom();
  if (event.type === 'queued') progress.label.textContent = 'Someone else is getting an answer. You\u2019re next in the queue';
  if (event.type === 'start') {
    activeRequest = event.request_id;
    const titles = event.sources || [];
    progress.label.textContent = titles.length ? `Reading ${titles.length} ${titles.length === 1 ? 'source' : 'sources'}` : 'Thinking it through';
    progress.sources.replaceChildren(...titles.map(title => element('span', title)));
  }
  if (event.type === 'token') {
    endThinking(progress);
    body.classList.add('streaming');
    setAnswer(article, body, (rawText.get(article) || '') + event.text);
  }
  if (event.type === 'error') { endThinking(progress); setAnswer(article, body, ERRORS[event.code] || 'Something went wrong.'); decorate(article, {label: 'failed'}); setStatus(''); }
  if (event.type === 'done') {
    endThinking(progress);
    body.classList.remove('streaming');
    const final = event.status === 'failed' ? ERRORS[event.code] || 'Something went wrong.' : event.text || rawText.get(article) || '';
    setAnswer(article, body, final, event);
    decorate(article, event);
    setStatus(event.status === 'cancelled' ? 'Stopped. The local model may finish its current step in the background.' : '');
  }
  followBottom(follow);
}
async function stop() {
  if (!activeRequest) return;
  setStatus('Stopping…');
  try { await api('/api/cancel', {method: 'POST', body: {request_id: activeRequest}}); } catch { setStatus('Could not stop the answer.'); }
}
async function route() {
  closeMenus();
  if ($('#chat-dialog').open) $('#chat-dialog').close();
  inspector(false);
  const hash = location.hash.slice(1);
  const requested = hash.startsWith('conversation/') ? hash.slice(13) : null;
  const enter = hash === 'workspace' || Boolean(requested);
  $('#signin').hidden = true;
  if (enter && !me) { showAuth(sessionState.needs_setup ? 'setup' : 'signin'); return; }
  if (enter && me.must_change) { showAuth('change'); return; }
  $('#arrival').hidden = enter;
  studio.hidden = !enter;
  if (!enter) { document.querySelectorAll('.enter-workspace').forEach(link => { link.textContent = me ? 'Open MORIQ AI' : 'Sign In'; }); return; }
  if (!statusLoaded) await loadStatus();
  navigation(innerWidth > 700);
  await refreshChats();
  setStatus('');
  if (requested) {
    try { current = await api('/api/chats/' + requested); workspace = current.workspace; }
    catch { current = null; setStatus('This chat is missing or was deleted. Choose a saved chat or start a new one.'); }
  } else if (hash === 'workspace') current = null;
  renderWorkspaces(); renderChats(); renderConversation(); sendControl();
  $('#workspace').scrollTop = current?.messages?.length ? $('#workspace').scrollHeight : 0;
  updateJump();
  $('#prompt').focus();
}
function openDialog(action) {
  if (!current) return;
  closeMenus();
  dialogAction = action; dialogReturn = document.activeElement;
  $('#dialog-title').textContent = action === 'rename' ? 'Rename chat' : 'Delete chat?';
  $('#dialog-description').textContent = action === 'rename' ? 'Use 1 to 60 characters.' : `Delete “${current.title}”? This cannot be undone.`;
  $('#rename-field').hidden = action !== 'rename';
  $('#chat-name').required = action === 'rename';
  $('#chat-name').value = current.title;
  $('#dialog-confirm').textContent = action === 'rename' ? 'Save name' : 'Delete chat';
  $('#dialog-error').textContent = '';
  $('#chat-dialog').showModal();
  (action === 'rename' ? $('#chat-name') : $('#dialog-cancel')).focus();
}
$('#composer').addEventListener('submit', event => { event.preventDefault(); ask($('#prompt').value); });
$('#prompt').addEventListener('input', () => {
  sendControl();
  $('#prompt').style.height = 'auto';
  $('#prompt').style.height = `${Math.min($('#prompt').scrollHeight, 160)}px`;
});
document.addEventListener('click', event => { if (!event.target.closest('details')) closeMenus(); });
$('#prompt').addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); ask(event.target.value); }
});
document.querySelectorAll('[data-level]').forEach(button => button.addEventListener('click', () => {
  level = button.dataset.level;
  document.querySelectorAll('[data-level]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
}));
for (const id of ['#jurisdiction', '#edition']) $(id).addEventListener('input', () => {
  $('#code-options').dataset.filled = String(Boolean($('#jurisdiction').value.trim() && $('#edition').value.trim()));
});
$('#workspace').addEventListener('scroll', updateJump, {passive: true});
function launch() {
  const button = $('.send');
  button.classList.remove('launch');
  void button.offsetWidth;
  button.classList.add('launch');
}
function setFact(fact) {
  $('#fact-text').textContent = fact.text;
  $('#fact-ask').onclick = () => { factPinned = false; ask(askAbout(fact)); };
  const text = $('#fact-text');
  text.classList.remove('swap');
  void text.offsetWidth;
  text.classList.add('swap');
}
function showFact(open) {
  $('#fact-card').hidden = !open;
  $('#fact-toggle').setAttribute('aria-expanded', String(open));
  $('#fact-dock').classList.toggle('open', open);
  if (open && !$('#fact-text').textContent) setFact(nextFact());
  if (!open) factPinned = false;
}
$('#fact-toggle').addEventListener('click', () => {
  const open = $('#fact-toggle').getAttribute('aria-expanded') === 'true' && factPinned;
  factPinned = !open;
  showFact(!open);
});
$('#fact-dock').addEventListener('mouseenter', () => showFact(true));
$('#fact-dock').addEventListener('mouseleave', () => { if (!factPinned) showFact(false); });
$('#fact-next').addEventListener('click', () => { factPinned = true; setFact(nextFact()); });
$('#surprise').addEventListener('click', () => {
  const prompts = Object.values(DISCIPLINES).flatMap(item => item.prompts.map(pair => pair[1]));
  const mark = $('#surprise-mark');
  mark.classList.remove('spin');
  void mark.offsetWidth;
  mark.classList.add('spin');
  const pick = prompts[Math.floor(Math.random() * prompts.length)];
  if (calm()) { ask(pick); return; }
  setTimeout(() => ask(pick), 450);
});
// A blueprint grid follows the pointer, and the start cards tilt towards it.
let pointerFrame = null;
$('.main-shell').addEventListener('pointermove', event => {
  if (calm() || event.pointerType === 'touch' || pointerFrame) return;
  const {clientX, clientY} = event;
  pointerFrame = requestAnimationFrame(() => {
    pointerFrame = null;
    const box = $('.main-shell').getBoundingClientRect();
    $('.main-shell').style.setProperty('--mx', `${clientX - box.left}px`);
    $('.main-shell').style.setProperty('--my', `${clientY - box.top}px`);
    $('.main-shell').classList.add('glow');
    const cover = $('#cover-image');
    cover.style.setProperty('--px', `${((clientX - box.left) / box.width - .5) * -14}px`);
    cover.style.setProperty('--py', `${((clientY - box.top) / box.height - .5) * -10}px`);
  });
});
$('.main-shell').addEventListener('pointerleave', () => $('.main-shell').classList.remove('glow'));
$('#suggestions').addEventListener('pointermove', event => {
  const card = event.target.closest('button');
  if (!card || calm() || event.pointerType === 'touch') return;
  const box = card.getBoundingClientRect();
  card.style.setProperty('--rx', `${((event.clientY - box.top) / box.height - .5) * -7}deg`);
  card.style.setProperty('--ry', `${((event.clientX - box.left) / box.width - .5) * 7}deg`);
});
$('#suggestions').addEventListener('pointerout', event => {
  const card = event.target.closest('button');
  if (card) { card.style.removeProperty('--rx'); card.style.removeProperty('--ry'); }
});
$('#jump').addEventListener('click', () => { $('#workspace').scrollTop = $('#workspace').scrollHeight; });
$('#new-session').addEventListener('click', () => { current = null; if (location.hash === '#workspace') route(); else location.hash = '#workspace'; });
$('#project-toggle').addEventListener('click', () => navigation($('#project-toggle').getAttribute('aria-expanded') !== 'true'));
$('#close-navigation').addEventListener('click', () => { navigation(false); $('#project-toggle').focus(); });
$('#evidence-toggle').addEventListener('click', () => {
  const open = $('#evidence-toggle').getAttribute('aria-expanded') === 'true';
  if (!open && latestMeta) showEvidence(latestMeta, $('#evidence-toggle'));
  else inspector(!open);
});
$('#close-evidence').addEventListener('click', () => inspector(false));
$('#rename-chat').addEventListener('click', () => openDialog('rename'));
$('#delete-chat').addEventListener('click', () => openDialog('delete'));
$('#dialog-cancel').addEventListener('click', () => $('#chat-dialog').close());
$('#chat-dialog').addEventListener('close', () => {
  (dialogReturn?.isConnected && !dialogReturn.disabled ? dialogReturn : $('#prompt')).focus();
  dialogReturn = null; dialogAction = null;
});
$('#chat-dialog-form').addEventListener('submit', async event => {
  event.preventDefault();
  try {
    if (dialogAction === 'rename') {
      const title = $('#chat-name').value.trim();
      if (!title) { $('#dialog-error').textContent = 'Enter a chat name.'; return; }
      await api('/api/chats/' + current.id, {method: 'PATCH', body: {title}});
      current.title = title;
      $('#chat-dialog').close();
      await refreshChats(); renderChats(); renderWorkspaces();
    } else {
      await api('/api/chats/' + current.id, {method: 'DELETE'});
      current = null;
      $('#chat-dialog').close();
      if (location.hash === '#workspace') route(); else location.hash = '#workspace';
    }
  } catch { $('#dialog-error').textContent = 'That did not work. Try again.'; }
});
document.addEventListener('keydown', event => {
  if (document.querySelector('dialog[open]')) return;
  if (event.key !== 'Escape') return;
  if (document.querySelector('details[open]')) { closeMenus(); return; }
  if ($('#fact-toggle').getAttribute('aria-expanded') === 'true') { showFact(false); $('#fact-toggle').focus(); return; }
  if (studio.classList.contains('inspector-open')) inspector(false);
  else if (innerWidth <= 700 && studio.classList.contains('nav-open')) { navigation(false); $('#project-toggle').focus(); }
});
matchMedia('(min-width: 701px)').addEventListener('change', event => navigation(event.matches));
addEventListener('hashchange', route);
$('#auth-photo').addEventListener('error', () => { $('#auth-photo').hidden = true; $('#auth-photo-caption').hidden = true; });
$('#cover-image').addEventListener('error', () => { $('#cover-image').closest('figure').hidden = true; });
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
$('#auth-form').addEventListener('submit', async event => {
  event.preventDefault();
  const username = $('#auth-username').value, password = $('#auth-password').value;
  $('#auth-error').textContent = '';
  $('#auth-submit').disabled = true;
  try {
    if (authMode === 'setup') await acceptSession(await api('/api/setup', {method: 'POST', body: {username, password, name: $('#auth-name').value, code: $('#auth-code').value}}));
    else if (authMode === 'change') await acceptSession(await api('/api/password', {method: 'POST', body: {current: password, new: $('#auth-new').value}}));
    else await acceptSession(await api('/api/login', {method: 'POST', body: {username, password}}));
  } catch (error) {
    if (!$('#signin').hidden) $('#auth-error').textContent = AUTH_ERRORS[error.code] || 'That did not work. Check your connection and try again.';
  } finally { $('#auth-submit').disabled = false; }
});
$('#auth-cancel').addEventListener('click', () => { $('#signin').hidden = true; route(); });
$('#account-button').addEventListener('click', () => {
  $('#account-title').textContent = me.name;
  $('#account-detail').textContent = `${me.username} \u00b7 ${me.role === 'admin' ? 'Admin' : 'Member'}`;
  $('#manage-team').hidden = me.role !== 'admin';
  $('#account-dialog').showModal();
});
$('#account-close').addEventListener('click', () => $('#account-dialog').close());
$('#change-password').addEventListener('click', () => showAuth('change', true));
$('#manage-team').addEventListener('click', async () => {
  $('#account-dialog').close();
  $('#team-result').hidden = true; $('#team-error').textContent = '';
  $('#team-dialog').showModal();
  try { await renderTeam(); } catch { $('#team-error').textContent = 'Could not load the team.'; }
});
$('#team-close').addEventListener('click', () => $('#team-dialog').close());
$('#team-form').addEventListener('submit', async event => {
  event.preventDefault();
  $('#team-error').textContent = '';
  try {
    const reply = await api('/api/users', {method: 'POST', body: {name: $('#team-name').value, username: $('#team-username').value, role: $('#team-role').value}});
    showTemporary(reply.user.username, reply.temporary_password);
    $('#team-form').reset();
    await renderTeam();
  } catch (error) { $('#team-error').textContent = AUTH_ERRORS[error.code] || 'That did not work.'; }
});
$('#sign-out').addEventListener('click', async () => {
  try { await api('/api/logout', {method: 'POST', body: {}}); } catch { /* the screen still locks */ }
  location.hash = '#workspace';
  signedOut();
});
(async () => {
  try {
    sessionState = await api('/api/session'); me = sessionState.user;
    if (me && !me.must_change) await loadStatus();
  } catch { sessionState = {user: null}; }
  route();
})();
