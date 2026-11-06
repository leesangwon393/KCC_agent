/* Mac first run: no user-facing account, token or terminal configuration. */
(async()=>{
 const panel=document.createElement('div');panel.className='note-block';panel.id='local-onboarding';
 document.querySelector('#connection .page-heading').after(panel);
 const request=async(path,body,extra={})=>{
  const headers={'Content-Type':'application/json',...extra};
  if(body){
   await window.MoaAuthReady;
   const token=document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)?.[1];
   if(!token)throw new Error('로그인 보안 쿠키를 읽을 수 없습니다. 페이지를 새로고침해 주세요.');
   headers['X-CSRFToken']=decodeURIComponent(token);
  }
  const r=await fetch('/api/v1/local/'+path,{method:body?'POST':'GET',credentials:'same-origin',headers,body:body?JSON.stringify(body):undefined});
  const data=await r.json();if(!r.ok)throw new Error(data.detail||'연결 실패');return data;
 };
 const key=location.hash.startsWith('#local-key=')?decodeURIComponent(location.hash.slice(11)):'';
 if(key){
  history.replaceState(null,'','#connection');
  try{await request('unlock/',{},{'X-Moa-Local-Key':key});location.reload();return;}
  catch(e){panel.textContent='모아 시작 파일을 다시 열어 주세요. '+e.message;return;}
 }
 let deferredInstall;
 window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredInstall=e;const b=document.getElementById('install-webapp');if(b)b.textContent='모아 앱 설치'});
 async function show(){
  try{
   const s=await request('setup/');
   document.getElementById('agent-logout').hidden=true;document.getElementById('agent-account').textContent='이 Mac에서 사용 중';
   panel.innerHTML=`<h2>${s.configured?'iCloud Drive 연결됨':'모아 시작하기'}</h2><p>1. iCloud Drive를 켜고 아래 연결 버튼을 눌러 주세요.</p><p>2. iCloud Drive의 <b>모아 / 받은 파일</b>에 새 파일을 넣으면 이 Mac에서 분류합니다. 원본은 남겨두고 작업 사본을 처리합니다.</p><p>${window.MoaDesktop?"3. 다음부터 Dock의 모아 아이콘으로 여세요.":"3. Safari에서 <b>파일 → Dock에 추가</b>를 선택하면 모아를 앱처럼 열 수 있습니다."}</p><div class="actions"><button class="primary" id="connect-icloud">${s.configured?'연결 다시 확인':'iCloud Drive 연결'}</button><button class="ghost" id="install-webapp">Dock에 추가 안내</button></div><p id="icloud-setup-status" role="status">${s.available?(s.configured?'새 파일을 기다리고 있습니다. Mac이 켜져 있을 때 처리됩니다.':'연결하면 iCloud Drive에 모아 전용 폴더를 만듭니다.'):'시스템 설정 → Apple 계정 → iCloud → Drive를 켜 주세요.'}</p>`;
   document.getElementById('connect-icloud').onclick=async e=>{e.target.disabled=true;try{await request('setup/',{});await show();}catch(err){document.getElementById('icloud-setup-status').textContent=err.message;}finally{e.target.disabled=false;}};
   document.getElementById('install-webapp').hidden=!!window.MoaDesktop;
   document.getElementById('install-webapp').onclick=async()=>{if(deferredInstall){await deferredInstall.prompt();deferredInstall=null;}else alert('Safari: 파일 → Dock에 추가 → 이름을 모아로 지정 → 추가. 이후 Dock의 모아 아이콘으로 여세요.');};
  }catch{panel.innerHTML='<h2>Mac에서 간편하게 시작</h2><p>처음 한 번 저장소의 <b>모아 시작.command</b>를 열어 설치하고, iCloud Drive를 연결하세요. 이후 Safari의 <b>파일 → Dock에 추가</b>로 앱처럼 사용할 수 있습니다.</p>';}
 }
 await show();
})();
