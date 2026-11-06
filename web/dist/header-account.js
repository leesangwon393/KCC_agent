/* Header identity follows the same server session as the workspace. */
(()=>{
 const header=document.querySelector('.header-inner');
 const root=document.createElement('div');root.className='header-account';
 root.innerHTML=`<div class="header-auth-actions" hidden><button class="header-login" data-login>로그인</button><button class="header-signup" data-page="signup">회원가입</button></div>
 <button class="header-account-toggle" hidden aria-expanded="false" aria-controls="header-account-panel"><span class="account-avatar" aria-hidden="true"></span><span class="account-label">계정 정보</span><svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="m3 4.5 3 3 3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
 <div id="header-account-panel" class="header-account-panel" hidden><span class="account-caption">내 계정</span><strong class="account-name"></strong><span class="account-username"></span><button data-page="connection" class="account-manage">계정 및 연결 관리 <span aria-hidden="true">↗</span></button></div>
 <button class="header-account-retry" hidden>계정 확인 재시도</button>`;
 header.insertBefore(root,document.getElementById('menu-toggle'));
 const auth=root.querySelector('.header-auth-actions'),toggle=root.querySelector('.header-account-toggle'),panel=root.querySelector('.header-account-panel'),retry=root.querySelector('.header-account-retry');
 function close(){panel.hidden=true;toggle.setAttribute('aria-expanded','false')}
 toggle.addEventListener('click',()=>{const open=panel.hidden;panel.hidden=!open;toggle.setAttribute('aria-expanded',String(open))});
 document.addEventListener('click',e=>{if(!root.contains(e.target))close()});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!panel.hidden){close();toggle.focus()}});
 root.addEventListener('focusout',e=>{if(!root.contains(e.relatedTarget))close()});
 document.addEventListener('moa-page',close);
 let version=0;
 async function update(snapshot){
  const request=++version;
  try{
   let session=snapshot;
   if(typeof session?.authenticated!=='boolean'){
    const response=await fetch('/api/v1/auth/session/',{credentials:'same-origin',cache:'no-store'});
    if(!response.ok)throw Error('session');
    session=await response.json();
   }
   if(request!==version)return;
   retry.hidden=true;auth.hidden=!!session.authenticated;toggle.hidden=!session.authenticated;
   if(session.authenticated){
    const name=session.display_name||session.username||'모아 계정';
    root.querySelector('.account-avatar').textContent=Array.from(name.trim())[0]||'M';
    root.querySelector('.account-name').textContent=name;
    root.querySelector('.account-username').textContent=session.username||'';
    root.querySelector('.account-username').hidden=!session.username||session.username===name;
    toggle.setAttribute('aria-label',`${name} 계정 정보`);
   }else close();
  }catch{if(request!==version)return;close();auth.hidden=true;toggle.hidden=true;retry.hidden=false;}
 }
 retry.addEventListener('click',update);
 document.addEventListener('moa-session',e=>update(e.detail||window.MoaSession));
 window.addEventListener('pageshow',e=>{if(e.persisted)update()});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)update()});
 if(window.MoaSession)update(window.MoaSession);
 else Promise.resolve(window.MoaAuthReady).then(()=>{if(window.MoaSession)update(window.MoaSession);else update()});
})();
