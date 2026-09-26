const KEY = 'continuum_premium_v2';
const DOC_DB = 'continuum_docs_v2';

function db(){
  return new Promise((resolve,reject)=>{
    const r=indexedDB.open(DOC_DB,1);
    r.onupgradeneeded=()=>{ if(!r.result.objectStoreNames.contains('files')) r.result.createObjectStore('files',{keyPath:'key'}); };
    r.onsuccess=()=>resolve(r.result);
    r.onerror=()=>reject(r.error);
  });
}
function fileData(f){return new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(r.result);r.onerror=()=>rej(r.error);r.readAsDataURL(f);});}
async function saveDocs(missionId,files){
  if(!files?.length)return;
  const d=await db(), tx=d.transaction('files','readwrite'), st=tx.objectStore('files');
  for(const f of files) st.put({key:missionId+'::'+crypto.randomUUID(),missionId,name:f.name,type:f.type||'application/octet-stream',size:f.size,data:await fileData(f)});
  return new Promise((res,rej)=>{tx.oncomplete=res;tx.onerror=()=>rej(tx.error);});
}
async function docsFor(missionId){
  const d=await db();
  return new Promise((res,rej)=>{const out=[],r=d.transaction('files','readonly').objectStore('files').openCursor();r.onsuccess=e=>{const c=e.target.result;if(!c)return res(out);if(c.value.missionId===missionId)out.push(c.value);c.continue();};r.onerror=()=>rej(r.error);});
}
function continuumId(){return 'CTM-'+Math.random().toString(36).slice(2,8).toUpperCase()+'-'+Math.floor(100+Math.random()*900);}

const seed={theme:'light',currentUser:null,premiumUsers:[],users:[],missions:[],requests:[],messages:[],purchases:[],termsAccepted:[],saved:[]};
let S=JSON.parse(localStorage.getItem(KEY)||'null')||seed;
// Migrate the previous prototype state instead of making users start again.
if(!S.users?.length){
  const old=JSON.parse(localStorage.getItem('continuum_premium_v1')||localStorage.getItem('continuum_v2')||'null');
  if(old){S={...seed,...old};}
}
S.premiumUsers ||= []; S.users ||= []; S.missions ||= []; S.requests ||= []; S.messages ||= []; S.purchases ||= []; S.termsAccepted ||= []; S.saved ||= [];
S.users.forEach((u,i)=>{if(!u.username){const base=String(u.name||'creator').toLowerCase().replace(/[^a-z0-9]/g,'').slice(0,20)||'creator';u.username=base+(i?String(i+1):'');}});
const save=()=>localStorage.setItem(KEY,JSON.stringify(S));
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const me=()=>S.users.find(u=>u.email===S.currentUser);
const userByEmail=email=>S.users.find(u=>u.email===email);
const publicMissionsFor=user=>S.missions.filter(m=>m.owner===user.email&&m.privacy==='public');
const profileUrl=user=>`user.html?username=${encodeURIComponent(user.username||'')}`;
const q=n=>new URLSearchParams(location.search).get(n);
const auth=()=>!!S.currentUser && !!me();
function theme(){document.documentElement.dataset.theme=S.theme||'light';}
function toast(x){const t=document.querySelector('#toast');if(!t)return;t.textContent=x;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2400);}
function requireAuth(){if(!auth()){location.href='login.html';return false;}return true;}
function signOut(e){e?.preventDefault();S.currentUser=null;save();location.href='index.html';}
function nav(){
  const u=me();
  const avatar=u?.profilePhoto ? `<img src="${u.profilePhoto}" alt="Profile photo">` : `<span class="avatar-fallback">${esc((u?.name||'U').trim().charAt(0).toUpperCase())}</span>`;
  return `<header class="topbar"><div class="container nav"><a class="brand" href="index.html">Continuum</a><nav class="navlinks"><a href="index.html">Home</a><a href="explore.html">Explore</a><a href="marketplace.html">Marketplace</a><a href="about.html">About</a><a href="dashboard.html">Dashboard</a></nav><div class="nav-actions">${auth()?`<a class="nav-icon" href="messages.html" title="Messages">Messages</a><a class="profile-chip" href="settings.html" title="Profile settings">${avatar}<span class="profile-name">${esc(u.username||u.name||'Profile')}</span></a><a class="btn premium" href="premium.html">Premium</a><a class="btn" href="index.html" data-signout>Sign out</a>`:`<a class="btn" href="login.html">Log in</a><a class="btn primary" href="signup.html">Create account</a><a class="btn premium" href="premium.html">Premium</a>`}</div></div></header>`;
}
function banner(){return auth()&&S.premiumUsers.includes(S.currentUser)?'':`<div class="premium-banner"><div class="container"><span>Premium gives creators advanced continuity and marketplace tools.</span><a href="premium.html">Go Premium for R100/month</a></div></div>`;}
function side(active){return `<aside class="sidebar"><a class="side ${active==='dashboard'?'active':''}" href="dashboard.html">Dashboard</a><a class="side ${active==='create'?'active':''}" href="create.html">Create mission</a><a class="side ${active==='missions'?'active':''}" href="my-missions.html">My missions</a><a class="side ${active==='saved'?'active':''}" href="saved.html">Saved</a><a class="side ${active==='explore'?'active':''}" href="explore.html">Explore</a><a class="side ${active==='collaboration'?'active':''}" href="collaboration.html">Collaboration</a><a class="side ${active==='marketplace'?'active':''}" href="marketplace.html">Marketplace</a><a class="side ${active==='messages'?'active':''}" href="messages.html">Messages</a><a class="side ${active==='settings'?'active':''}" href="settings.html">Settings</a><a class="side ${active==='provenance'?'active':''}" href="provenance.html">Provenance</a><a class="side" href="premium.html">Premium</a></aside>`;}
function footer(){return `<footer class="footer"><div class="container">Continuum is a private prototype. Final agreements, payment flow and compliance documents should be reviewed before production use.</div><a href="terms.html">Terms &amp; Conditions</a></footer>`;}
function shell(content,active=''){return nav()+banner()+(auth()?`<div class="layout">${side(active)}<main class="main">${content}</main></div>`:`<main class="page-main">${content}</main>`)+footer()+`<div id="toast" class="toast"></div>`;}

function dashboard(){
  const root=document.querySelector('#dash-root'); if(!root)return;
  const user=me(); if(!user){location.href='login.html';return;}
  const mine=S.missions.filter(m=>m.owner===S.currentUser), received=S.requests.filter(r=>r.to===S.currentUser&&r.status==='pending');
  root.innerHTML=`<div class="topline"><div><span class="eyebrow">Dashboard</span><h2>Welcome back, ${esc(user.name.split(/\s+/)[0])}</h2><p class="muted">Your missions, documents, collaboration and marketplace activity.</p></div><a class="btn primary" href="create.html">Create mission</a></div><div class="stats"><div class="card stat"><span class="muted small">Missions</span><strong>${mine.length}</strong></div><div class="card stat"><span class="muted small">Public</span><strong>${mine.filter(m=>m.privacy==='public').length}</strong></div><div class="card stat"><span class="muted small">Documents</span><strong>${mine.reduce((n,m)=>n+Number(m.documentsCount||0),0)}</strong></div><div class="card stat"><span class="muted small">For sale</span><strong>${mine.filter(m=>m.transfer?.listed).length}</strong></div><div class="card stat"><span class="muted small">Requests</span><strong>${received.length}</strong></div></div><div class="grid2"><div class="card"><div class="sectionhead"><h3>My missions</h3><a class="btn" href="my-missions.html">View all</a></div>${mine.length?`<div class="list">${mine.map(m=>`<div class="list-row"><div><b>${esc(m.title)}</b><div class="muted small">${esc(m.problem||m.description||'No problem statement yet.')}</div><div class="muted tiny">${esc(m.privacy)} · R ${Number(m.projectValue||0).toLocaleString('en-ZA')} worth</div></div><a class="btn" href="mission.html?id=${encodeURIComponent(m.id)}">Open</a></div>`).join('')}</div>`:`<div class="empty"><h3>No missions yet</h3><p class="muted">Create your first mission or add your project documents.</p><a class="btn primary" href="create.html">Create your first mission</a></div>`}</div><div class="card"><h3>Continuity snapshot</h3><div class="list"><div class="list-row"><span>Account ID</span><b>${esc(user.id)}</b></div><div class="list-row"><span>Location</span><b>${esc([user.city,user.province,user.country].filter(Boolean).join(', ')||'Not supplied')}</b></div><div class="list-row"><span>Premium</span><b>${S.premiumUsers.includes(S.currentUser)?'Active':'Not active'}</b></div><div class="list-row"><span>Pending collaboration</span><b>${received.length}</b></div></div><br><a class="btn" href="settings.html">Manage profile</a></div></div>`;
}

function bindCreate(){
  const f=document.querySelector('#create-form'); if(!f)return;
  f.addEventListener('submit',async e=>{
    e.preventDefault(); if(!requireAuth())return;
    const fd=new FormData(f), terms=document.querySelector('#terms'), ownership=document.querySelector('#ownership');
    if(!terms?.checked||!ownership?.checked){toast('You must accept the terms and confirm ownership.');return;}
    const a=[...(document.querySelector('#mission-documents')?.files||[])], b=[...(document.querySelector('#projectDocuments')?.files||[])];
    const files=[...a,...b]; const total=files.reduce((n,x)=>n+x.size,0);
    if(!S.premiumUsers.includes(S.currentUser)&&total>50*1024*1024){toast('Free missions are limited to 50 MB of documents.');return;}
    const unit=fd.get('inactiveUnit')||'months', amount=Number(fd.get('inactiveAmount')||12), days=unit==='years'?amount*365:amount*30;
    const m={id:crypto.randomUUID(),title:String(fd.get('title')||'').trim(),category:fd.get('category')||'Other',description:String(fd.get('description')||'').trim(),problem:String(fd.get('problem')||'').trim(),findings:String(fd.get('findings')||'').trim(),lessons:String(fd.get('lessons')||'').trim(),funding:String(fd.get('funding')||'').trim(),amountSpent:Number(fd.get('amountSpent')||0),projectValue:Number(fd.get('projectValue')||fd.get('projectWorth')||0),owner:S.currentUser,privacy:fd.get('privacy')||'private',status:'active',createdAt:new Date().toISOString(),lastActivity:new Date().toISOString(),contributors:[],documentsCount:files.length,transfer:{inactiveAmount:amount,inactiveUnit:unit,inactiveDays:days,automatic:fd.get('automatic')==='yes',deathRelease:fd.get('deathRelease')==='yes',deathRecipient:String(fd.get('deathRecipient')||'').trim(),deathContact:String(fd.get('deathContact')||'').trim(),payoutRecipient:String(fd.get('payoutRecipient')||'').trim(),payoutContact:String(fd.get('payoutContact')||'').trim(),price:Number(fd.get('salePrice')||0),listed:false,evaluation:'not submitted',statement:''},termsVersion:'1.0',ownershipConfirmedAt:new Date().toISOString()};
    S.missions.push(m);S.termsAccepted.push({user:S.currentUser,version:'1.0',signature:String(fd.get('signature')||'').trim(),at:new Date().toISOString(),mission:m.id});save();
    try{await saveDocs(m.id,files);}catch(err){console.error(err);toast('Mission saved, but document storage failed in this prototype.');}
    location.href='mission.html?id='+encodeURIComponent(m.id);
  });
}

function bindSignup(){
  const f=document.querySelector('#signup-form'); if(!f)return;
  const submit=f.querySelector('button[type="submit"]');
  const refreshPhotoGate=()=>{
    const captured=sessionStorage.getItem('continuum_live_photo_captured')==='true';
    if(submit){submit.disabled=!captured;submit.setAttribute('aria-disabled',String(!captured));}
    const gate=document.querySelector('#photo-gate');
    if(gate)gate.textContent=captured?'Live photo captured. You can create your account.':'Take your live profile photo before you can create your account.';
  };
  refreshPhotoGate();
  window.addEventListener('continuum-photo-captured',refreshPhotoGate);
  f.addEventListener('submit',e=>{
    e.preventDefault(); const fd=new FormData(f);
    if(sessionStorage.getItem('continuum_live_photo_captured')!=='true')return toast('Your live profile photo is required before creating the account.');
    if(fd.get('password')!==fd.get('confirm'))return toast('Passwords do not match.');
    if(!document.querySelector('#terms')?.checked)return toast('Please accept the Terms and Conditions.');
    const email=String(fd.get('email')||'').trim().toLowerCase();
    const username=String(fd.get('username')||'').trim().toLowerCase().replace(/[^a-z0-9._-]/g,'');
    if(!username)return toast('Please choose a username.');
    if(S.users.some(u=>u.email===email))return toast('An account already exists for that email.');
    if(S.users.some(u=>u.username===username))return toast('That username is already taken.');
    const id=continuumId(), livePhoto=sessionStorage.getItem('continuum_live_photo_data')||'';
    S.users.push({id,name:String(fd.get('name')||'').trim(),username,email,password:String(fd.get('password')||''),bio:'',city:'',province:'',country:'',profilePhoto:livePhoto});
    S.currentUser=email;S.termsAccepted.push({user:email,version:'1.0',at:new Date().toISOString(),account:true});save();
    sessionStorage.removeItem('continuum_live_photo_captured');sessionStorage.removeItem('continuum_live_photo_data');location.href='dashboard.html';
  });
}
function bindLogin(){const f=document.querySelector('#login-form');if(!f)return;f.addEventListener('submit',e=>{e.preventDefault();const fd=new FormData(f),identifier=String(fd.get('identifier')||fd.get('email')||'').trim().toLowerCase(),password=String(fd.get('password')||'');const u=S.users.find(x=>(x.email===identifier||x.username===identifier)&&x.password===password);if(!u)return toast('Incorrect username/email or password.');S.currentUser=u.email;save();location.href='dashboard.html';});}
function bindRecovery(){const f=document.querySelector('#recovery-form');if(!f)return;f.addEventListener('submit',e=>{e.preventDefault();const fd=new FormData(f),id=String(fd.get('id')||'').trim().toUpperCase(),u=S.users.find(x=>x.id===id);if(!u)return toast('We could not find that Continuum ID.');if(sessionStorage.getItem('continuum_recovery_photo_captured')!=='true')return toast('Please take the live recovery photo.');const requests=JSON.parse(localStorage.getItem('continuum_recovery')||'[]');requests.push({id:crypto.randomUUID(),continuumId:id,photo:sessionStorage.getItem('continuum_recovery_photo_data')||'',at:new Date().toISOString()});localStorage.setItem('continuum_recovery',JSON.stringify(requests));document.querySelector('#recovery-result').innerHTML='<div class="notice">Recovery request recorded for this prototype. Production recovery requires compliant identity and liveness verification.</div>';});}
function bindGlobal(){document.querySelectorAll('[data-signout],[data-action="logout"]').forEach(b=>b.addEventListener('click',signOut));}

function myMissions(){const root=document.querySelector('#missions-root');if(!root)return;const ms=S.missions.filter(m=>m.owner===S.currentUser);root.innerHTML=ms.length?ms.map(m=>`<article class="card mission-card"><div class="sectionhead"><span class="pill ${m.privacy}">${m.privacy==='public'?'Public':'Private'}</span><span class="pill">${m.transfer?.evaluation==='pending'?'Evaluation pending':m.transfer?.listed?'Listed':'Not listed'}</span></div><h3>${esc(m.title)}</h3><p>${esc(m.problem||m.description)}</p><div class="price-line"><span class="muted small">Spent: R ${Number(m.amountSpent||0).toLocaleString('en-ZA')} · Worth: R ${Number(m.projectValue||0).toLocaleString('en-ZA')}</span><a class="btn" href="mission.html?id=${encodeURIComponent(m.id)}">Open</a></div></article>`).join(''):`<div class="empty"><h3>No missions yet</h3><a class="btn primary" href="create.html">Create mission</a></div>`;}
function savedMissions(){
  const root=document.querySelector('#saved-root');if(!root)return;
  const ids=S.saved.filter(x=>x.user===S.currentUser).map(x=>x.mission);
  const ms=S.missions.filter(m=>ids.includes(m.id));
  root.innerHTML=`<div class="topline"><div><span class="eyebrow">Saved</span><h2>Missions to review later</h2><p class="muted">Keep promising public missions here when you might be interested in them later.</p></div><a class="btn" href="explore.html">Explore missions</a></div>${ms.length?`<div class="missions">${ms.map(m=>`<article class="card mission-card"><span class="pill public">Saved</span><h3>${esc(m.title)}</h3><p>${esc(m.problem||'No problem statement.')}</p><div class="price-line"><a class="btn primary" href="mission.html?id=${encodeURIComponent(m.id)}">Review mission</a><button class="btn" data-unsave="${m.id}">Remove</button></div></article>`).join('')}</div>`:`<div class="empty"><h3>No saved missions</h3><p class="muted">Save public missions from Explore when you want to review them later.</p><a class="btn primary" href="explore.html">Explore public missions</a></div>`}`;
  root.querySelectorAll('[data-unsave]').forEach(b=>b.onclick=()=>{S.saved=S.saved.filter(x=>!(x.user===S.currentUser&&x.mission===b.dataset.unsave));save();savedMissions();});
}
function toggleSaveMission(id){
  if(!requireAuth())return;
  const exists=S.saved.some(x=>x.user===S.currentUser&&x.mission===id);
  S.saved=exists?S.saved.filter(x=>!(x.user===S.currentUser&&x.mission===id)):[...S.saved,{user:S.currentUser,mission:id,at:new Date().toISOString()}];save();toast(exists?'Removed from saved missions.':'Saved for later.');
  const b=document.querySelector(`[data-save="${id}"]`);if(b)b.textContent=exists?'Save for later':'Saved';
}
function collaboration(){const root=document.querySelector('#collab-root');if(!root)return;const received=S.requests.filter(r=>r.to===S.currentUser),sent=S.requests.filter(r=>r.from===S.currentUser),mine=S.missions.filter(m=>m.owner===S.currentUser);root.innerHTML=`<div class="card" style="margin-bottom:18px"><h3>Direct invitation</h3><p class="muted small">Private missions cannot receive public collaboration requests. Use a direct invitation instead.</p><form id="invite-form" class="row2"><div class="field"><label>Mission</label><select name="mission">${mine.map(m=>`<option value="${m.id}">${esc(m.title)}</option>`).join('')}</select></div><div class="field"><label>Username or email</label><input name="identifier" required></div><button class="btn primary">Send invitation</button></form></div><div class="grid2"><div class="card"><h3>Requests received</h3>${received.length?received.map(r=>`<div class="list-row"><div><b>${esc(r.fromName||r.from||'Unknown')}</b><div class="muted small">${esc(r.missionTitle||r.mission||'Mission')}</div></div><span class="pill">${esc(r.status)}</span></div>`).join(''):'<p class="muted">No requests.</p>'}</div><div class="card"><h3>Requests sent</h3>${sent.length?sent.map(r=>`<div class="list-row"><div><b>${esc(r.missionTitle||'Mission')}</b><div class="muted small">To ${esc(r.toName||r.to||'Unknown')}</div></div><span class="pill">${esc(r.status)}</span></div>`).join(''):'<p class="muted">No requests.</p>'}</div></div>`;const invite=document.querySelector('#invite-form');if(invite)invite.onsubmit=e=>{e.preventDefault();const fd=new FormData(invite),m=S.missions.find(x=>x.id===fd.get('mission')),identifier=String(fd.get('identifier')||'').trim().toLowerCase(),u=S.users.find(x=>x.email===identifier||x.username===identifier);const email=u?.email;if(!m)return;if(!u)return toast('The invited user must have a Continuum account in this prototype.');S.requests.push({id:crypto.randomUUID(),from:S.currentUser,fromName:me().name,to:email,toName:u.name,mission:m.id,missionTitle:m.title,status:'invited',at:new Date().toISOString(),direct:true});save();toast('Invitation sent.');invite.reset();collaboration();};}
function messages(){const root=document.querySelector('#messages-root');if(!root)return;const msgs=S.messages.filter(m=>m.from===S.currentUser||m.to===S.currentUser);root.innerHTML=`<div class="card chat"><div class="chat-list"><h3>Conversations</h3><p class="muted small">Messaging is available for collaboration relationships and approved access.</p></div><div class="chat-window"><div class="messages">${msgs.length?msgs.map(m=>`<div class="bubble ${m.from===S.currentUser?'mine':''}">${esc(m.text)}</div>`).join(''):'<p class="muted">No messages yet.</p>'}</div><form id="message-form" class="row2"><div class="field"><label>Recipient email</label><input name="to" type="email" required></div><div class="field"><label>Message</label><input name="text" required></div><button class="btn primary">Send message</button></form></div></div>`;document.querySelector('#message-form').onsubmit=e=>{e.preventDefault();const fd=new FormData(e.target);S.messages.push({from:S.currentUser,to:String(fd.get('to')).trim().toLowerCase(),text:String(fd.get('text')).trim(),at:new Date().toISOString()});save();e.target.reset();messages();};}
function bindCollabRequest(){document.querySelectorAll('[data-collab]').forEach(b=>b.onclick=()=>{if(!requireAuth())return;const m=S.missions.find(x=>x.id===b.dataset.collab);if(!m)return;if(m.privacy!=='public')return toast('Private missions require a direct invitation.');if(m.owner===S.currentUser)return toast('You already own this mission.');if(S.requests.some(r=>r.mission===m.id&&r.from===S.currentUser&&r.status==='pending'))return toast('Your request is already pending.');const owner=S.users.find(x=>x.email===m.owner);S.requests.push({id:crypto.randomUUID(),from:S.currentUser,fromName:me().name,to:m.owner,toName:owner?.name||'',mission:m.id,missionTitle:m.title,status:'pending',at:new Date().toISOString()});save();toast('Collaboration request sent.');});}
function renderUserCard(u){
  const avatar=u.profilePhoto?'<img class="user-avatar" src="'+u.profilePhoto+'" alt="'+esc(u.name||u.username)+' profile photo">':'<div class="user-avatar fallback">'+esc((u.name||'U').charAt(0).toUpperCase())+'</div>';
  const pubs=publicMissionsFor(u);
  return '<article class="card user-card"><div class="profile-hero">'+avatar+'<div><h3>'+esc(u.name||u.username)+'</h3><p class="muted">@'+esc(u.username||'username')+'</p></div></div><p>'+esc(u.bio||'No public bio yet.')+'</p><div class="muted small">'+pubs.length+' public mission'+(pubs.length===1?'':'s')+'</div><div class="price-line" style="margin-top:10px"><a class="btn primary" href="'+profileUrl(u)+'">View profile</a></div></article>';
}
function renderExploreMission(m){
  const owner=userByEmail(m.owner);
  return '<article class="card mission-card"><span class="pill public">Public</span><h3>'+esc(m.title)+'</h3><p>'+esc(m.problem||'No problem statement.')+'</p><div class="mission-owner"><span class="muted small">Created by</span><a href="'+(owner?profileUrl(owner):'#')+'"><b>'+esc(owner?.name||'Continuum creator')+'</b> '+(owner?.username?'<span class="muted">@'+esc(owner.username)+'</span>':'')+'</a></div><div class="price-line"><a class="btn" href="mission.html?id='+encodeURIComponent(m.id)+'">View mission</a>'+(auth()&&m.owner!==S.currentUser?'<button class="btn" data-save="'+m.id+'" onclick="toggleSaveMission(\''+m.id+'\')">'+(S.saved.some(x=>x.user===S.currentUser&&x.mission===m.id)?'Saved':'Save for later')+'</button>':'')+(auth()&&m.owner!==S.currentUser?'<button class="btn" data-collab="'+m.id+'">Request collaboration</button>':'')+'</div></article>';
}
function explore(){
  const root=document.querySelector('#explore-root');if(!root)return;
  const term=(q('q')||'').trim().toLowerCase();
  const allUsers=S.users.filter(u=>u.email!==S.currentUser&&(!term||`${u.name||''} ${u.username||''}`.toLowerCase().includes(term)));
  const ms=S.missions.filter(m=>m.privacy==='public'&&(!term||`${m.title} ${m.problem} ${m.category}`.toLowerCase().includes(term)));
  root.innerHTML=`<div class="topline"><div><span class="eyebrow">Explore</span><h2>Find people & public missions</h2><p class="muted">Search by a person's name or username to view their public profile, bio and public missions, or search for public missions directly.</p></div></div>
  <div class="field" style="margin-bottom:18px"><label>Search people or missions</label><input id="explore-search" value="${esc(term)}" placeholder="Search by full name, username, mission title or category"></div>
  ${term?`<section style="margin-bottom:26px"><div class="sectionhead"><h3>People</h3><span class="muted small">${allUsers.length} result${allUsers.length===1?'':'s'}</span></div><div class="grid2" style="margin-top:12px">${allUsers.length?allUsers.map(renderUserCard).join(''):'<div class="empty"><h3>No people found</h3><p class="muted">Try the person&#39;s full name or username.</p></div>'}</div></section>`:''}
  <section><div class="sectionhead"><h3>Public missions</h3><span class="muted small">Only missions explicitly made public are shown.</span></div><div class="missions" style="margin-top:12px">${ms.length?ms.map(renderExploreMission).join(''):'<div class="empty"><h3>No public missions found</h3><p class="muted">Try a different mission title, problem or category.</p></div>'}</div></section>`;
  document.querySelector('#explore-search').onkeydown=e=>{if(e.key==='Enter')location.href='explore.html?q='+encodeURIComponent(e.target.value)};
  bindCollabRequest();
} 
function userProfile(){
  const root=document.querySelector('#user-root');if(!root)return;
  const username=(q('username')||'').toLowerCase();
  const u=S.users.find(x=>(x.username||'').toLowerCase()===username);
  if(!u){root.innerHTML='<div class="empty"><h2>User not found</h2><p class="muted">Check the username and try again.</p><a class="btn" href="explore.html">Back to Explore</a></div>';return;}
  const pubs=publicMissionsFor(u);
  const avatar=u.profilePhoto?`<img class="profile-avatar-large" src="${u.profilePhoto}" alt="${esc(u.name)} profile photo">`:`<div class="profile-avatar-large fallback">${esc((u.name||'U').charAt(0).toUpperCase())}</div>`;
  root.innerHTML=`<div class="topline"><div><span class="eyebrow">Public profile</span><h2>${esc(u.name||u.username)}</h2><p class="muted">@${esc(u.username||'username')}</p></div><a class="btn" href="explore.html">Search people</a></div><div class="grid2"><div class="card"><div class="profile-hero">${avatar}<div><h3>${esc(u.name||u.username)}</h3><p class="muted">@${esc(u.username||'username')}</p>${[u.city,u.province,u.country].filter(Boolean).length?`<p class="muted small">${esc([u.city,u.province,u.country].filter(Boolean).join(', '))}</p>`:''}</div></div><h3>Bio</h3><p>${esc(u.bio||'This user has not added a public bio yet.')}</p></div><div class="card"><h3>Public missions</h3><p class="muted small">These are the missions this creator has chosen to make public.</p>${pubs.length?`<div class="list">${pubs.map(m=>`<div class="list-row"><div><b>${esc(m.title)}</b><div class="muted small">${esc(m.problem||'No problem statement.')}</div></div><a class="btn" href="mission.html?id=${encodeURIComponent(m.id)}">View</a></div>`).join('')}</div>`:'<div class="empty"><p>No public missions yet.</p></div>'}</div></div>`;
}

async function mission(){
  const root=document.querySelector('#mission-root');if(!root)return;
  const id=q('id'),m=S.missions.find(x=>x.id===id);
  if(!m){root.innerHTML='<div class="empty"><h2>Mission not found</h2><a class="btn" href="explore.html">Back to Explore</a></div>';return;}
  const owner=m.owner===S.currentUser;
  const ownerUser=userByEmail(m.owner);
  const bought=S.purchases.some(p=>p.mission===m.id&&p.buyer===S.currentUser);
  const canSeeProtected=owner||bought;
  const docs=await docsFor(m.id).catch(()=>[]);
  root.innerHTML=`<div class="topline"><div><span class="eyebrow">${esc(m.category)}</span><h2>${esc(m.title)}</h2><p class="muted">${esc(m.problem||'No problem statement provided.')}</p><div class="mission-owner"><span class="muted small">This mission belongs to</span><a href="${ownerUser?profileUrl(ownerUser):'#'}"><b>${esc(ownerUser?.name||'Continuum creator')}</b> ${ownerUser?.username?`<span class="muted">@${esc(ownerUser.username)}</span>`:''}</a></div></div>${owner?`<a class="btn primary" href="sell.html?id=${encodeURIComponent(m.id)}">Submit for evaluation</a>`:''}</div>
  <div class="grid2">
    <div class="card">
      <h3>Problem statement</h3><p>${esc(m.problem||'No problem statement provided.')}</p>
      ${canSeeProtected?`<h3>Mission overview</h3><p>${esc(m.description||'')}</p><h3>What was found</h3><p>${esc(m.findings||'Not documented yet.')}</p><h3>Lessons learned</h3><p>${esc(m.lessons||'Not documented yet.')}</p><h3>Funding</h3><p>${esc(m.funding||'Not documented yet.')}</p><div class="grid2"><div><span class="muted small">Amount spent</span><h3>R ${Number(m.amountSpent||0).toLocaleString('en-ZA')}</h3></div><div><span class="muted small">Project worth</span><h3>R ${Number(m.projectValue||0).toLocaleString('en-ZA')}</h3></div></div><h3>Documents (${docs.length})</h3>${docs.length?`<div class="list">${docs.map(d=>`<div class="list-row"><div><b>${esc(d.name)}</b><div class="muted small">${Math.ceil(d.size/1024)} KB · ${esc(d.type||'file')}</div></div><a class="btn" href="${d.data}" download="${esc(d.name)}">Download</a></div>`).join('')}</div>`:'<p class="muted">No documents attached.</p>'}`:`<div class="notice public-lock"><b>Public preview only.</b> Continuum protects the work behind the problem statement. Findings, lessons, funding, value and documents are available only to the creator or a user with recorded legal access.</div>`}
    </div>
    <div class="card"><h3>Continuity</h3><div class="list"><div class="list-row"><span>Status</span><b>${esc(m.status)}</b></div><div class="list-row"><span>Visibility</span><b>${esc(m.privacy)}</b></div><div class="list-row"><span>Last activity</span><b>${new Date(m.lastActivity).toLocaleDateString()}</b></div><div class="list-row"><span>Contributors</span><b>${m.contributors?.length||0}</b></div></div>${!owner&&m.privacy==='public'?`<br><button class="btn" data-save="${m.id}" onclick="toggleSaveMission('${m.id}')">${S.saved.some(x=>x.user===S.currentUser&&x.mission===m.id)?'Saved':'Save for later'}</button><br><button class="btn" data-collab="${m.id}">Request collaboration</button>`:''}${!owner&&m.transfer?.listed&&!bought?`<br><br><button class="btn primary" data-purchase="${m.id}">Purchase legal access · R ${Number(m.transfer.price||0).toLocaleString('en-ZA')}</button>`:''}</div>
  </div>`;
  bindCollabRequest();bindPurchasePage();
}

function marketplace(){const root=document.querySelector('#market-root');if(!root)return;const ms=S.missions.filter(m=>m.transfer?.listed&&m.transfer.evaluation==='approved');root.innerHTML=ms.length?ms.map(m=>`<article class="card mission-card"><span class="pill">Transfer listing</span><h3>${esc(m.title)}</h3><p>${esc(m.problem)}</p><div class="price-line"><span class="muted">R ${Number(m.transfer.price||0).toLocaleString('en-ZA')}</span><a class="btn primary" href="mission.html?id=${encodeURIComponent(m.id)}">Review</a></div></article>`).join(''):`<div class="empty"><h3>No missions are listed for transfer</h3><p class="muted">Creators can submit missions for evaluation before listing them.</p></div>`;}
function premium(){const b=document.querySelector('#premium-action');if(!b)return;b.onclick=()=>{if(!requireAuth())return;if(!S.premiumUsers.includes(S.currentUser))S.premiumUsers.push(S.currentUser);save();toast('Premium activated in this prototype at R100/month.');setTimeout(()=>location.href='dashboard.html',500);};}
function bindPurchasePage(){document.querySelectorAll('[data-purchase]').forEach(b=>b.onclick=()=>{if(!requireAuth())return;const m=S.missions.find(x=>x.id===b.dataset.purchase);if(!m)return;S.purchases.push({mission:m.id,buyer:S.currentUser,amount:Number(m.transfer.price||0),platformFee:Math.round(Number(m.transfer.price||0)*.08),route:'direct',at:new Date().toISOString(),legalAccess:true});save();location.href='mission.html?id='+encodeURIComponent(m.id);});}
function bindSell(){const f=document.querySelector('#sell-form');if(!f)return;f.addEventListener('submit',e=>{e.preventDefault();if(!requireAuth())return;const m=S.missions.find(x=>x.id===q('id')&&x.owner===S.currentUser);if(!m)return toast('Open the sale review from one of your missions.');const fd=new FormData(f);m.transfer.price=Number(fd.get('price')||0);m.transfer.statement=String(fd.get('statement')||'').trim();m.transfer.evaluation='pending';m.transfer.listed=false;save();toast('Mission submitted for evaluation.');setTimeout(()=>location.href='review.html?id='+encodeURIComponent(m.id),400);});}
function review(){const root=document.querySelector('#review-root');if(!root)return;const m=S.missions.find(x=>x.id===q('id'));if(!m){root.innerHTML='<div class="empty"><h2>Mission not found</h2></div>';return;}root.innerHTML=`<div class="card"><span class="eyebrow">Evaluation</span><h2>${esc(m.title)}</h2><p>${esc(m.transfer.statement||'No creator statement supplied.')}</p><div class="notice">Prototype review status: <b>${esc(m.transfer.evaluation||'not submitted')}</b>. This is not a legal or financial valuation.</div>${m.owner===S.currentUser?`<button class="btn primary" id="approve-demo">Approve for marketplace prototype</button>`:''}</div>`;document.querySelector('#approve-demo')?.addEventListener('click',()=>{m.transfer.evaluation='approved';m.transfer.listed=true;save();toast('Mission approved and listed in the prototype marketplace.');setTimeout(()=>location.href='marketplace.html',400);});}
function settings(){
  const root=document.querySelector('#settings-root');if(!root)return;const u=me();
  const avatar=u?.profilePhoto?`<img class="settings-avatar" src="${u.profilePhoto}" alt="Profile photo">`:`<div class="settings-avatar fallback">${esc((u?.name||'U').charAt(0).toUpperCase())}</div>`;
  root.innerHTML=`<div class="topline"><div><span class="eyebrow">Account</span><h2>Profile & Settings</h2><p class="muted">Manage your username, profile, email, password and appearance.</p></div></div>
  <div class="grid2"><div class="card profile-card"><div class="profile-hero">${avatar}<div><h3>${esc(u.name)}</h3><p class="muted">@${esc(u.username||'username')} · ${esc(u.id)}</p></div></div><form id="settings-form" class="form"><div class="field"><label>Full name</label><input name="name" value="${esc(u.name)}" required></div><div class="field"><label>Username</label><input name="username" value="${esc(u.username||'')}" required pattern="[A-Za-z0-9._-]{3,30}"><p class="muted small">Your username is your public account name. It must be unique.</p></div><div class="field"><label>Bio</label><textarea name="bio">${esc(u.bio||'')}</textarea></div><div class="row2"><div class="field"><label>City / town</label><input name="city" value="${esc(u.city||'')}"></div><div class="field"><label>Province</label><input name="province" value="${esc(u.province||'')}"></div></div><div class="field"><label>Country</label><input name="country" value="${esc(u.country||'')}"></div><div class="field"><label>Theme</label><select name="theme"><option value="light" ${S.theme==='light'?'selected':''}>Warm light</option><option value="dark" ${S.theme==='dark'?'selected':''}>Dark</option></select></div><button class="btn primary">Save profile</button></form></div>
  <div class="card"><h3>Account security</h3><form id="security-form" class="form"><div class="field"><label>Email address</label><input name="email" type="email" value="${esc(u.email)}" required></div><div class="field"><label>Current password</label><input name="currentPassword" type="password" required></div><div class="field"><label>New password</label><input name="newPassword" type="password" minlength="8" placeholder="Leave blank to keep your password"></div><div class="field"><label>Confirm new password</label><input name="confirmPassword" type="password" minlength="8"></div><button class="btn">Save account changes</button></form><div class="notice" style="margin-top:18px"><b>Profile photo:</b> Your live camera photo is part of your account record in this prototype. A production system should store it securely and use compliant identity verification.</div><br><button class="btn danger" data-signout>Sign out</button></div></div>`;
  document.querySelector('#settings-form').onsubmit=e=>{e.preventDefault();const fd=new FormData(e.target),username=String(fd.get('username')||'').trim().toLowerCase().replace(/[^a-z0-9._-]/g,'');if(S.users.some(x=>x.username===username&&x.email!==u.email))return toast('That username is already taken.');Object.assign(u,{name:String(fd.get('name')).trim(),username,bio:String(fd.get('bio')).trim(),city:String(fd.get('city')).trim(),province:String(fd.get('province')).trim(),country:String(fd.get('country')).trim()});S.theme=fd.get('theme');save();theme();toast('Profile saved.');setTimeout(settings,250);};
  document.querySelector('#security-form').onsubmit=e=>{e.preventDefault();const fd=new FormData(e.target),email=String(fd.get('email')).trim().toLowerCase(),current=String(fd.get('currentPassword')||''),next=String(fd.get('newPassword')||''),confirm=String(fd.get('confirmPassword')||'');if(current!==u.password)return toast('Current password is incorrect.');if(S.users.some(x=>x.email===email&&x!==u))return toast('That email is already in use.');if(next&&(next.length<8||next!==confirm))return toast('New passwords must match and be at least 8 characters.');u.email=email;if(next)u.password=next;S.currentUser=email;save();toast('Account security updated.');setTimeout(settings,250);};bindGlobal();
}
function provenance(){const root=document.querySelector('#provenance-root');if(!root)return;const ms=S.missions.filter(m=>m.owner===S.currentUser||m.contributors?.some(c=>c.email===S.currentUser));root.innerHTML=ms.length?ms.map(m=>`<div class="card" style="margin-bottom:18px"><h3>${esc(m.title)}</h3><p class="muted">Owner + ${m.contributors?.length||0} contributor(s)</p><a class="btn" href="mission.html?id=${encodeURIComponent(m.id)}">Open mission</a></div>`).join(''):`<div class="empty"><h3>No provenance yet</h3><p class="muted">Create a mission or contribute to one to start building provenance.</p></div>`;}
function checkAutomaticRelease(){
  let changed=false, now=Date.now();
  S.missions.forEach(m=>{const t=m.transfer;if(!t||!t.automatic||t.listed)return;const age=Math.floor((now-new Date(m.lastActivity).getTime())/86400000);if(age>=Number(t.inactiveDays||Infinity)){m.status='inactive';if(t.price>0&&t.evaluation==='approved')t.listed=true;changed=true;}});
  if(changed)save();
}

function normalizeNavigation(){
  const p=location.pathname.split('/').pop()||'index.html';
  const appPages=new Set(['dashboard.html','create.html','my-missions.html','saved.html','collaboration.html','marketplace.html','messages.html','settings.html','provenance.html']);
  const header=document.querySelector('header.topbar');
  if(header)header.outerHTML=nav();else{const temp=document.createElement('div');temp.innerHTML=nav();document.body.insertBefore(temp.firstElementChild,document.body.firstChild);}
  const topKey=p.replace('.html',''); document.querySelectorAll('.navlinks a').forEach(a=>{const href=a.getAttribute('href')||'';a.classList.toggle('active',href===p || (topKey==='index'&&href==='index.html'));});
  if(appPages.has(p)&&auth()){
    const active={ 'dashboard.html':'dashboard','create.html':'create','my-missions.html':'missions','saved.html':'saved','collaboration.html':'collaboration','marketplace.html':'marketplace','messages.html':'messages','settings.html':'settings','provenance.html':'provenance'}[p];
    const existing=document.querySelector('.layout');
    if(existing){const old=existing.querySelector('.sidebar');if(old)old.outerHTML=side(active);}
  }
  bindGlobal();
}

function init(){
  theme();normalizeNavigation();checkAutomaticRelease();
  const p=location.pathname.split('/').pop()||'index.html';
  if(p==='create.html')bindCreate();
  if(p==='signup.html')bindSignup();
  if(p==='recovery.html')bindRecovery();
  if(p==='login.html')bindLogin();
  if(p==='mission.html')mission();
  if(p==='user.html')userProfile();
  if(p==='sell.html')bindSell();
  if(p==='review.html')review();
  if(p==='marketplace.html')marketplace();
  if(p==='settings.html'){if(requireAuth())settings();}
  if(p==='dashboard.html'){if(requireAuth())dashboard();}
  if(p==='my-missions.html'){if(requireAuth())myMissions();}
  if(p==='saved.html'){if(requireAuth())savedMissions();}
  if(p==='collaboration.html'){if(requireAuth())collaboration();}
  if(p==='messages.html'){if(requireAuth())messages();}
  if(p==='explore.html')explore();
  if(p==='premium.html')premium();
  if(p==='provenance.html'){if(requireAuth())provenance();}
  bindPurchasePage();
}
window.addEventListener('DOMContentLoaded',init);
