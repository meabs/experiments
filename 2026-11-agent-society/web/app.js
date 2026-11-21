"use strict";
const $ = s => document.querySelector(s);
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const colours = ["#d3bb81", "#9fbd8e", "#a4b9d7", "#c5a5cf", "#e0a88a", "#abd3bb", "#c7c5b5", "#ef9366"];
const names = ["Ada","Bram","Cleo","Dara","Eli","Fern","Gus","Rook"];
const costs = {farm:{wood:12,stone:4},well:{wood:6,stone:12},market:{wood:10,stone:8},storehouse:{wood:14,stone:6},clinic:{wood:8,stone:10,tools:2},police:{wood:6,stone:4,tools:1},army:{wood:8,stone:6,tools:2}};
const benefits = {farm:"+1 food gathered per level",well:"Food relief on even days",market:"A civic trading landmark",storehouse:"A civic storage landmark",clinic:"Better recovery when resting",police:"Fewer successful thefts, more thieves caught",army:"Smaller raider losses every 6th day"};
const homes = [[290,150],[420,110],[600,140],[210,305],[720,335],[320,455],[675,470],[460,505]];
const places = {food:[135,200],wood:[160,455],stone:[820,420],farm:[145,160],well:[410,280],market:[525,335],storehouse:[755,220],clinic:[540,460],police:[330,375],army:[690,175]};
let data=null, town="Brook", selected="Rook", filter="all", lastStep=-1, mapTown=null, lastStateKey="", polling=false;

function bundle(v) { return Object.entries(v).map(([r,n])=>`${n} ${r}`).join(" + "); }
function shortNum(n) { return Intl.NumberFormat("en",{notation:"compact",maximumFractionDigits:1}).format(n || 0); }
function toast(text) { $("#notice").textContent=text; $("#notice").style.display="block"; setTimeout(()=>$("#notice").style.display="none",6500); }

function building(x,y,level,type,label) {
  const tint = type === "home" ? "#d8b58e" : "#c6d9b6";
  if (!level && type !== "home") return `<g transform="translate(${x} ${y})"><ellipse cy="12" rx="39" ry="16" fill="#354d35" opacity=".18"/><path d="M-29 5V-17M29 5V-17M-29 -8H29" stroke="#b7b9a0" stroke-width="4" stroke-dasharray="5 4" opacity=".65"/><text y="34" text-anchor="middle" fill="#f7f2d9" font-size="13" font-weight="600">${esc(label)}</text><text y="50" text-anchor="middle" fill="#dde5ce" font-size="10">not built</text></g>`;
  if (!level) return `<g transform="translate(${x} ${y})"><ellipse cy="14" rx="28" ry="10" fill="#324733" opacity=".23"/><path d="M-23 10L0 -24L25 10Z" fill="#d3c3a0"/><path d="M0 -24L4 10H25Z" fill="#b5a281"/><path d="M-4 10L1 -6L8 10Z" fill="#5b5b49"/><path d="M-27 12H28" stroke="#82735b" stroke-width="3"/></g>`;
  const height = 24 + (level-1)*7;
  let special="";
  if(type==="well") return `<g transform="translate(${x} ${y})"><ellipse cy="14" rx="30" ry="13" fill="#284d40" opacity=".2"/><ellipse cy="5" rx="24" ry="12" fill="#a9c0b1"/><path d="M-24 -3V7Q0 23 24 7V-3" fill="#8caaa0"/><ellipse cy="-3" rx="24" ry="12" fill="#aec9ba"/><ellipse cy="-3" rx="15" ry="7" fill="#376e79"/><path d="M-20 -2V-36M20 -2V-36" stroke="#a48566" stroke-width="5"/><path d="M-30 -33L0 -48L32 -33Z" fill="#657f7a"/><text y="37" text-anchor="middle" fill="#f4f3d8" font-size="13">Well · ${level}</text></g>`;
  if(type==="clinic") special=`<path d="M-5 -${height-1}h10v8h8v10h-8v8h-10v-8h-8v-10h8Z" fill="#d3f0cf" transform="translate(0 -2) scale(.7)"/>`;
  if(type==="market") special=`<path d="M-34 -10H34L28 -25H-28Z" fill="#bd8658"/><path d="M-25 -25L-30 -10M-9 -25L-10 -10M9 -25L10 -10M25 -25L30 -10" stroke="#e8d5ab" stroke-width="8"/>`;
  return `<g transform="translate(${x} ${y})"><ellipse cy="18" rx="40" ry="15" fill="#254632" opacity=".24"/><path d="M-27 12V-${height}H25V12Z" fill="${tint}"/><path d="M25 -${height}L39 -${height+8}V4L25 12Z" fill="${type==="home"?"#b18b6b":"#9db49a"}"/><path d="M-36 -${height-1}L-3 -${height+29}L35 -${height-1}Z" fill="${type==="home"?"#95735d":"#658b7c"}"/><path d="M-3 -${height+29}L11 -${height+36}L47 -${height+8}L35 -${height-1}Z" fill="${type==="home"?"#735d50":"#496e65"}"/><rect x="-5" y="-8" width="12" height="20" rx="1" fill="#655f4b"/><rect x="-21" y="-${height-7}" width="10" height="10" fill="#c2deca"/><rect x="11" y="-${height-7}" width="9" height="10" fill="#c2deca"/>${level>1?`<rect x="13" y="-${height+31}" width="8" height="16" fill="#b0a294"/>`:""}${level>2?`<path d="M-35 20H40M-32 13V27M-15 13V27M3 13V27M21 13V27M38 13V27" stroke="#cbbda0" stroke-width="3"/>`:""}${special}${label?`<text y="39" text-anchor="middle" fill="#f4f3d8" font-size="13" font-weight="600">${esc(label)} · ${level}</text>`:""}</g>`;
}

function tree(x,y,s=1) {return `<g transform="translate(${x} ${y}) scale(${s})"><ellipse cy="10" rx="17" ry="7" fill="#304b39" opacity=".2"/><path d="M0 10V-20" stroke="#756b51" stroke-width="5"/><path d="M-23 -8L0 -59L23 -8Z" fill="#426c52"/><path d="M-19 -23L0 -67L19 -23Z" fill="#527c58"/><path d="M-14 -39L0 -72L14 -39Z" fill="#668c5f"/></g>`;}

function terrain() {
  let trees="", grass="";
  for(let i=0;i<40;i++) {const x=45+(i*71)%195,y=375+(i*43)%210;trees+=tree(x,y,.42+(i%4)*.13);}
  for(let i=0;i<90;i++) {const x=35+(i*137)%820,y=50+(i*83)%510;grass+=`<path d="M${x} ${y}l2 -4m2 4l2 -3" stroke="#c4d19a" opacity=".19" stroke-width="2"/>`;}
  return `<defs><linearGradient id="land" x2=".7" y2="1"><stop stop-color="#809369"/><stop offset="1" stop-color="#648166"/></linearGradient><linearGradient id="river" x2="1" y2="1"><stop stop-color="#7cb2ad"/><stop offset="1" stop-color="#529093"/></linearGradient><filter id="soft"><feGaussianBlur stdDeviation="6"/></filter></defs><rect width="960" height="640" fill="url(#land)"/><path d="M-20 335Q210 250 450 120T980 40" fill="none" stroke="#afba84" stroke-width="130" opacity=".1"/>${grass}<path d="M890 -40C825 140 1005 240 908 360S890 555 945 680" fill="none" stroke="#a8b79b" stroke-width="105"/><path d="M890 -40C825 140 1005 240 908 360S890 555 945 680" fill="none" stroke="url(#river)" stroke-width="77"/><path class="waterline" d="M890 -40C825 140 1005 240 908 360S890 555 945 680" fill="none" stroke="#c0ddd0" stroke-width="2" stroke-dasharray="14 29" opacity=".35"/><g stroke="#c5b891" stroke-linecap="round" fill="none"><path d="M285 153Q420 180 410 280T525 335T680 470" stroke-width="19"/><path d="M210 305Q325 350 410 280T600 140" stroke-width="16"/><path d="M420 110L410 280M525 335L720 335M525 335L755 220M525 335L540 460L460 505M525 335L320 455M410 280L145 180" stroke-width="13"/></g><g opacity=".28" stroke="#e2d9af" stroke-width="2" fill="none"><path d="M285 153Q420 180 410 280T525 335T680 470"/><path d="M210 305Q325 350 410 280T600 140"/></g><g transform="translate(85 190) rotate(-12)"><rect width="110" height="65" rx="6" fill="#9e9d60"/>${Array.from({length:6},(_,i)=>`<path d="M9 ${9+i*10}H101" stroke="#c5bf78" stroke-width="4" stroke-dasharray="3 3"/>`).join("")}</g>${trees}<g transform="translate(800 405)"><ellipse cy="20" rx="62" ry="27" fill="#889184"/><path d="M-45 10L-35 -25L-6 -34L12 -15L27 -25L50 -5L45 20Z" fill="#b2b5a5"/><path d="M-6 -34L-12 10L12 -15L27 -25L24 20H45" fill="#979e94"/><path d="M-35 -25L-29 12L-12 10" fill="none" stroke="#c9cbb7" stroke-width="3"/></g><text x="87" y="563" fill="#e8ebd2" font-size="12" letter-spacing="3" opacity=".75">THE WOODLAND</text><text x="776" y="463" fill="#e8ebd2" font-size="12" letter-spacing="2" opacity=".75">QUARRY</text><g transform="translate(855 125) rotate(10)"><path d="M-12 -12H77V13H-12Z" fill="#a28d68"/><path d="M-10 -18H77M-10 19H77" stroke="#d5c6a1" stroke-width="5"/><path d="M0 -10V12M13 -10V12M26 -10V12M39 -10V12M52 -10V12M65 -10V12" stroke="#c6b28c" stroke-width="3"/></g>${tree(800,90,.8)}${tree(775,65,.6)}${tree(80,85,.7)}${tree(670,70,.7)}<g id="structures"></g><g id="links"></g><g id="people"></g><text x="30" y="35" fill="#f4f1d8" font-size="12" letter-spacing="2" id="map-caption"></text>`;
}

function residentPosition(a,t) {
  const i=names.indexOf(a.name);
  const last=data.events.find(e=>e.town===town&&e.actor===a.name&&!['message','message_rejected','sunset'].includes(e.kind));
  let p=homes[i];
  if(last?.kind==='gather') p=places[last.resource];
  else if(last?.kind==='contribute') p=places[last.project];
  else if(['offer','trade','give'].includes(last?.kind)) p=places.market;
  else if(String(last?.kind||'').startsWith('theft')) p=places.police;
  else if(last?.kind==='craft') p=places.storehouse;
  return [p[0]+(i%3-1)*20,p[1]+36+Math.floor(i/3)*15];
}

function renderMap() {
  const t=data.world.towns[town];
  if(mapTown!==town) {$("#map").innerHTML=terrain();mapTown=town;lastStep=-1;}
  $("#map-caption").textContent=`${town.toUpperCase()}  /  DAY ${data.world.day}  /  ${data.pilot?'PILOT':'LIVE WORLD'}`;
  $("#structures").innerHTML=Object.values(t.agents).map((a,i)=>building(...homes[i],a.home,'home','')).join('')+Object.entries(t.projects).map(([p,v])=>building(...places[p],v.level,p,p.charAt(0).toUpperCase()+p.slice(1))).join('');
  const residents=Object.values(t.agents);
  $("#people").innerHTML=residents.map(a=>{
    const i=names.indexOf(a.name),p=residentPosition(a,t),active=data.runtime.actor===a.name&&data.runtime.town===town&&data.runtime.phase==='thinking';
    return `<g class="map-agent" tabindex="0" role="button" aria-label="Inspect ${esc(a.name)}" data-person="${esc(a.name)}" transform="translate(${p[0]} ${p[1]})" opacity="${a.health?1:.35}"><circle class="agent-halo ${active?'thinking-ring':''}" cy="-9" r="22" fill="none" stroke="${colours[i]}" stroke-width="2" opacity="${a.name===selected||active?1:0}"/><ellipse cy="11" rx="13" ry="5" fill="#203d31" opacity=".28"/><path d="M-7 8V-3Q0 -10 7 -3V8Z" fill="${colours[i]}"/><circle cy="-12" r="8" fill="#e5c5a3"/><path d="M-8 -16Q0 -27 8 -16V-13H-8Z" fill="${a.name==='Rook'?'#3f3d43':'#6c6d4d'}"/><circle cx="3" cy="-12" r="1" fill="#344232"/><rect x="-26" y="18" width="52" height="19" rx="5" fill="${a.name===selected?'#172d2a':'#354d3edb'}"/><text y="31" text-anchor="middle" fill="#f3f0df" font-size="11" font-weight="600">${esc(a.name)}</text>${a.name==='Rook'?'<circle cx="22" cy="-26" r="5" fill="#ef9366"/>':''}</g>`;
  }).join('');
  const trades=data.events.filter(e=>e.town===town&&['trade','give'].includes(e.kind)).slice(0,3);
  $("#links").innerHTML=trades.map(e=>{const a=residentPosition(t.agents[e.actor],t),b=residentPosition(t.agents[e.partner],t);return `<path class="trade-line" d="M${a[0]} ${a[1]}Q${(a[0]+b[0])/2} ${Math.min(a[1],b[1])-55} ${b[0]} ${b[1]}" fill="none" stroke="#f2db9a" stroke-width="2" opacity=".6"/>`;}).join('');
  $("#map").querySelectorAll('[data-person]').forEach(el=>{el.onclick=()=>selectPerson(el.dataset.person);el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectPerson(el.dataset.person);}};});
  lastStep=data.world.step;
}

function renderCards() {
  $("#town-cards").innerHTML=Object.entries(data.world.towns).map(([name,t])=>{
    const n=data.counts[name];
    return `<button class="town-card ${name===town?'active':''}" data-town="${name}" aria-pressed="${name===town}"><div class="town-card-head"><h3>${name}</h3><span>${name===town?'●':'○'}</span></div><p class="fee">${t.fee?'1 coin per message':'Free conversation'}</p><div class="town-numbers"><div><strong>${Object.values(t.agents).filter(a=>a.health).length}/8</strong><span>residents</span></div><div><strong>${n.trade||0}</strong><span>trades</span></div><div><strong>${n.message||0}</strong><span>messages</span></div></div></button>`;
  }).join('');
  $("#town-cards").querySelectorAll('button').forEach(b=>b.onclick=()=>{town=b.dataset.town;render();});
}

function renderResidents() {
  const t=data.world.towns[town];
  $("#roster").innerHTML=Object.values(t.agents).map((a,i)=>`<button class="person ${a.name===selected?'active':''} ${a.health?'':'dead'}" data-person="${a.name}" style="--person:${colours[i]}" aria-pressed="${a.name===selected}"><span class="face">${a.name[0]}</span><strong>${a.name}</strong><span class="role">${a.role}</span><span class="health-pips" aria-label="Health ${a.health} out of 5">${'●'.repeat(a.health)}${'○'.repeat(5-a.health)}</span></button>`).join('');
  $("#roster").querySelectorAll('button').forEach(b=>b.onclick=()=>selectPerson(b.dataset.person));
  const a=t.agents[selected],i=names.indexOf(selected);
  const goal=a.goal==='home'?`Build a level ${a.target} home`:a.goal==='public'?`Contribute ${a.target} resource units to public projects`:`Hold ${a.target} ${a.goal}`;
  const held=a.goal==='home'?a.home:a.goal==='public'?a.donated:a.inventory[a.goal];
  $("#resident").innerHTML=`<div class="resident-title" style="--person:${colours[i]}"><div class="large-face">${a.name[0]}</div><div><h2>${a.name}</h2><p>${a.role.charAt(0).toUpperCase()+a.role.slice(1)} · ${town}</p></div></div>${a.name==='Rook'?'<span class="competitive">MORE AGGRESSIVE RESIDENT</span>':''}<p class="personality">${esc(a.temperament)}</p><div class="health-row"><span>${a.health?'Health':'Inactive · zero health'}</span><strong>${a.health} / 5</strong></div><div class="inventory">${Object.entries(a.inventory).map(([r,n])=>`<div><strong>${n}</strong>${r}</div>`).join('')}</div><div class="private-goal"><span>PRIVATE OBJECTIVE</span>${esc(goal)}<br><strong>${held} / ${a.target}</strong></div><div class="last-action">${esc(a.last_action)}</div>`;
  $("#memory").textContent=a.memory||'No private notes yet. Notes will appear after this resident takes a turn.';
}

function renderProjects() {
  const t=data.world.towns[town];
  $("#projects").innerHTML=Object.entries(t.projects).map(([p,v])=>{
    const total=Object.values(costs[p]).reduce((a,b)=>a+b,0),have=Object.values(v.stock).reduce((a,b)=>a+b,0);
    return `<article class="project"><span class="project-icon">${{farm:'♧',well:'◉',market:'▤',storehouse:'▥',clinic:'✚',police:'⚑',army:'⚔'}[p]}</span><h4>${p.charAt(0).toUpperCase()+p.slice(1)}</h4><span class="level">Level ${v.level} / 3</span><p>${Object.entries(costs[p]).map(([r,n])=>`${v.stock[r]}/${n} ${r}`).join('<br>')}</p><progress value="${v.level===3?total:have}" max="${total}" aria-label="${p} construction progress"></progress><p>${benefits[p]}</p></article>`;
  }).join('') + `<article class="project"><span class="project-icon">✦</span><h4>Inventions</h4><span class="level">${Object.keys(t.techs||{}).length} made</span><p>${Object.values(t.techs||{}).length?Object.values(t.techs).map(x=>`${esc(x.name)} by ${esc(x.inventor)}: ${esc(x.effect.replaceAll('_',' '))}`).join('<br>'):'Nothing invented yet.'}</p></article>`;
  $("#offer-count").textContent=t.offers.length;
  $("#offers").innerHTML=t.offers.length?t.offers.slice(-8).reverse().map(o=>`<div class="offer"><strong>#${o.id} · ${esc(o.owner)}</strong> to ${esc(o.target)}<br>Offers ${esc(bundle(o.give))}<br>Wants ${esc(bundle(o.want))}<br>Expires after day ${o.expires}</div>`).join(''):'<p class="empty">No open offers. Residents can propose their own exchanges.</p>';
}

function renderJournal() {
  let events=data.events.filter(e=>e.town===town);
  if(filter==='message') events=events.filter(e=>e.kind==='message');
  if(filter==='trade') events=events.filter(e=>['trade','give','offer','cancel'].includes(e.kind));
  if(filter==='build') events=events.filter(e=>['home','contribute','craft'].includes(e.kind));
  if(filter==='all') events=events.filter(e=>e.kind!=='sunset'||e.hungry);
  if(filter==='crime') events=events.filter(e=>e.kind.startsWith('theft')||e.kind==='raid');
  $("#journal").innerHTML=events.length?events.slice(0,60).map(e=>`<div class="event ${e.kind==='message'&&e.to!=='all'?'private':''} ${e.kind.includes('reject')?'rejected':''}"><span class="event-day">Day ${e.day}</span><span class="actor" style="color:${colours[names.indexOf(e.actor)]||'#b8c7c1'}">${esc(e.actor)}</span><div class="detail"><span class="event-kind">${e.kind==='message'?(e.to==='all'?'public message':`private to ${esc(e.to)}`):esc(e.kind.replaceAll('_',' '))}</span>${esc(e.detail)}</div></div>`).join(''):`<p class="empty">${data.totals.calls?'No matching events yet.':'The town is ready. Real decisions will appear here once the model download and technical pilot finish.'}</p>`;
}

function renderStatus() {
  const life=data.lifecycle,r=data.runtime;
  let phase=life.phase||'ready',detail='The engine is ready; no model decisions yet.';
  if(phase==='downloading') detail=life.total?`${((life.completed||0)/1e9).toFixed(1)} / ${(life.total/1e9).toFixed(1)} GB · ${life.status||'downloading weights'}`:life.status||'Contacting local Ollama';
  else if(phase==='pilot') detail=`Technical pilot · ${r.actor||'starting'} in ${r.town||'the towns'} · ${data.totals.calls}/16 decisions`;
  else if(phase==='running') {phase=r.phase==='thinking'?'running':r.phase;detail=r.phase==='thinking'?`${r.actor} in ${r.town} is deciding · ${Math.max(0,Math.floor(data.now-r.call_started))}s this turn`:r.reason||r.error||'Between turns';}
  else if(phase==='error') detail=life.error||r.error||'Check the run log';
  else if(phase==='finished') detail=life.reason||r.reason||'All records retained';
  else if(phase==='selftest') detail='Checking the rules before any model calls';
  if(data.paused) {phase='paused';detail='Current call may finish; the run deadline continues.';}
  $("#phase").textContent=({downloading:'Downloading the local model',pilot:'Checking the first town-day',running:'The towns are alive',paused:'Exploration paused',finished:'Exploration finished',error:'Runner needs attention',selftest:'Testing the town rules',ready:'Ready for local inference',stopped:'Exploration stopped'})[phase]||phase;
  $("#phase-detail").textContent=detail;
  $("#download").hidden=phase!=='downloading';
  $("#download").value=life.total?(life.completed||0)/life.total*100:0;
  $("#connection").textContent=data.pilot?'PILOT · NOT MAIN DATA':phase==='running'?'LIVE EXPLORATION':'CONNECTED';
  $("#pause").textContent=data.paused?'Resume':'Pause';
  $("#pause").disabled=!['running','paused'].includes(life.phase)&&!data.paused;
  $("#stop").disabled=['finished','stopped'].includes(life.phase);
  if(r.deadline) {const remaining=Math.max(0,r.deadline-data.now);$("#countdown").textContent=`${Math.floor(remaining/3600)}h ${Math.floor(remaining%3600/60)}m remaining`;}
  $("#run-stats").innerHTML=`<strong>${shortNum(data.totals.calls)}</strong> model decisions<br><strong>${shortNum(data.totals.input_tokens+data.totals.output_tokens)}</strong> tokens processed<br><strong>${Math.round(data.totals.mean_seconds)}s</strong> average decision<br><strong>$0</strong> paid API cost<br>Electricity unmeasured`;
  $("#audit").textContent=data.verification.passed?`Independent audit passed through ${data.verification.completed_days} completed day(s). ${data.verification.events} ledger events checked.`:'Independent audit runs after each complete day. Free rule checks passed before launch.';
  $("#last-update").textContent=`Updated ${new Date().toLocaleTimeString()} · Records saved after every turn`;
}

function render() {
  if(!data) return;
  renderStatus();renderCards();renderResidents();renderProjects();renderJournal();renderMap();
  $("#town-tag").textContent=`${town.toUpperCase()} · ${data.world.towns[town].fee?'WORDS COST ONE COIN':'FREE CONVERSATION'}`;
  $("#town-title").textContent=data.world.day===1&&!data.totals.calls?'A town with room to grow.':`Every choice leaves a trace.`;
  $("#day").textContent=String(data.world.day).padStart(2,'0');
}
function selectPerson(name) {selected=name;renderResidents();renderMap();}
async function refresh() {
  if(polling) return;polling=true;
  try {const response=await fetch('/api/state',{cache:'no-store'});if(!response.ok)throw Error(`HTTP ${response.status}`);data=await response.json();render();}
  catch(error){$("#connection").textContent='DISCONNECTED';$("#phase-detail").textContent='Observer connection lost. The simulation may still be running; retrying…';}
  finally{polling=false;}
}
async function control(command) {try{const response=await fetch(`/api/${command}`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});const result=await response.json();if(!response.ok)throw Error(result.error);toast(result.note);await refresh();}catch(error){toast(`Control failed: ${error.message}`);}}
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x===b));if(data)renderJournal();});
$("#pause").onclick=()=>control(data?.paused?'resume':'pause');
$("#stop").onclick=()=>$("#stop-dialog").showModal();
$("#cancel-stop").onclick=()=>$("#stop-dialog").close();
$("#confirm-stop").onclick=()=>{$("#stop-dialog").close();control('stop');};
refresh();setInterval(refresh,2500);
