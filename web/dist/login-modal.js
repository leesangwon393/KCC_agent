/* Reuse the original login form and its session/CSRF handler inside a native modal. */
(()=>{
 const login=document.getElementById('agent-login');
 if(!login)return;
 const prompt=document.createElement('div');prompt.className='login-prompt note-block';
 prompt.innerHTML='<p>로그인하면 연결된 Mac과 파일 상태를 확인할 수 있어요.</p><button class="primary" data-login>로그인</button>';
 login.before(prompt);
 const modal=document.createElement('dialog');modal.id='login-modal';modal.className='login-modal';
 modal.setAttribute('aria-labelledby','login-modal-title');modal.setAttribute('aria-describedby','login-modal-description');
 modal.innerHTML='<button class="login-modal-close" type="button" aria-label="로그인 팝업 닫기">×</button>';
 document.body.append(modal);modal.append(login);
 login.querySelector('h2').id='login-modal-title';login.querySelector('h2').textContent='다시 만나 반가워요';
 const description=login.querySelector('p');description.id='login-modal-description';description.textContent='모아에 로그인하고 파일 정리를 이어가세요.';
 const username=login.querySelector('[name="username"]');username.autocapitalize='none';username.spellcheck=false;
 const password=login.querySelector('[name="password"]');
 let previousFocus=null,scrollStyle='';
 function open(){
  if(login.hidden||modal.open)return;
  previousFocus=document.activeElement;
  window.closeMenu?.();
  scrollStyle=document.body.style.overflow;document.body.style.overflow='hidden';
  modal.showModal();username.focus({preventScroll:true});
 }
 function close(){if(modal.open)modal.close()}
 modal.querySelector('.login-modal-close').addEventListener('click',close);
 // A click must begin and end on the backdrop, so dragging out of a field stays safe.
 let backdropDown=false;
 modal.addEventListener('pointerdown',e=>{backdropDown=e.target===modal});
 modal.addEventListener('click',e=>{if(backdropDown&&e.target===modal)close();backdropDown=false});
 modal.addEventListener('close',()=>{
  document.body.style.overflow=scrollStyle;password.value='';
  document.getElementById('agent-login-error').textContent='';
  if(previousFocus?.isConnected&&previousFocus.getClientRects().length)previousFocus.focus({preventScroll:true});
 });
 document.addEventListener('click',e=>{
  const trigger=e.target.closest('[data-login],.header-login,#onboarding-login [data-page="connection"],#signup .text-link[data-page="connection"]');
  if(trigger){e.preventDefault();e.stopImmediatePropagation();open();}
 },true);
 document.addEventListener('moa-page',close);
 // agent.js already updates this visibility only after a successful session check.
 function sync(){prompt.hidden=login.hidden;if(login.hidden)close()}
 new MutationObserver(sync).observe(login,{attributes:true,attributeFilter:['hidden']});sync();
})();
