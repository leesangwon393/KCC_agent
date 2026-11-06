/* AWS onboarding: Apple identity + explicit pairing with the local Mac helper. */
(async()=>{
 if(['localhost','127.0.0.1'].includes(location.hostname))return;
 const phone=/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
 const panel=document.createElement('div');panel.className='note-block';panel.id='cloud-onboarding';
 document.querySelector('#connection .page-heading').after(panel);
 const title=document.createElement('h2');title.textContent='이 Mac을 모아에 연결';panel.append(title);
 const instructions=document.createElement('p');instructions.textContent='① 회원가입 / 로그인 → ② 이 Mac 연결 → ③ iCloud Drive 폴더 연결 → ④ Safari의 파일 → Dock에 추가';panel.append(instructions);
 const privacy=document.createElement('p');privacy.textContent='모아 계정으로 로그인하고 Mac의 iCloud 동기화 폴더를 연결합니다. Apple 비밀번호를 모아에 입력하지 않습니다.';panel.append(privacy);
 const loginArea=document.createElement('div');panel.append(loginArea);
 const pair=document.createElement('button');pair.className='primary';pair.textContent='이 Mac 연결';pair.hidden=true;panel.append(pair);
 const status=document.createElement('p');status.setAttribute('role','status');panel.append(status);
 const helper=document.createElement('p');helper.textContent='처음 한 번 모아 연결 앱을 다운로드해 열어 주세요. 앱이 필요한 프로그램을 자동으로 설치합니다. 이후에는 아래 연결 버튼으로 앱이 실행됩니다.';panel.append(helper);const download=document.createElement('a');download.className='ghost';download.href='/downloads/moa-mac-helper.zip';download.download='moa-mac-helper.zip';download.textContent='모아 연결 앱 다운로드';panel.append(download);
 const dock=document.createElement('button');dock.className='ghost';dock.textContent='Dock에 추가 안내';dock.onclick=()=>alert('Safari에서 이 AWS 사이트를 연 뒤 파일 → Dock에 추가를 선택하고 이름을 “모아 AWS”로 지정하세요. Mac 연결 후에도 연결 도우미가 실행 중이어야 파일 상태가 갱신됩니다.');panel.append(dock);
 try{
  const config=await fetch('/api/v1/auth/config/',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json()});
  if(config.apple_enabled){
   const apple=document.createElement('a');apple.className='primary';apple.href='/api/v1/auth/apple/start/';apple.textContent='Apple로 계속하기';loginArea.append(apple);
   // Existing accounts remain available without being confused with Apple login.
   document.querySelector('#agent-login h2').textContent='기존 모아 계정으로 로그인';
  }else{
   const signup=document.createElement('button');signup.className='primary';signup.dataset.page='signup';signup.textContent='무료 회원가입';loginArea.append(signup);
  }
  if(location.hash.includes('apple_error=')){
   status.textContent='Apple 로그인을 완료하지 못했습니다. 다시 시도해 주세요.';
   history.replaceState(null,'','#connection');page('connection');
  }
  async function update(){
   const s=await fetch('/api/v1/auth/session/',{credentials:'same-origin',cache:'no-store'}).then(r=>r.json());
   pair.hidden=!s.authenticated;pair.disabled=phone;if(phone)pair.textContent='Mac에서 같은 계정으로 로그인해 연결하세요';loginArea.hidden=s.authenticated;
  }
  document.addEventListener('moa-session',update);await update();
  pair.onclick=async()=>{
   pair.disabled=true;status.textContent='Mac 연결 요청을 준비하고 있습니다.';
   try{
    const session=await fetch('/api/v1/auth/session/',{credentials:'same-origin',cache:'no-store'}).then(r=>r.json());
    const r=await fetch('/api/v1/agent/pairing/',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':session.csrf},body:'{}'});
    const data=await r.json();if(!r.ok)throw Error(data.detail||'로그인 후 다시 연결하세요.');
    const link=document.createElement('a');link.className='primary';link.textContent='모아 연결 앱 열기';
    link.href='moa-helper://connect?ticket='+encodeURIComponent(data.pairing_secret);
    link.rel='noreferrer';link.referrerPolicy='no-referrer';
    status.textContent='아래 링크를 누르고 연결 앱 열기를 허용해 주세요. 준비 후 연결 승인 화면이 열립니다. 링크는 5분간 유효합니다.';
    panel.querySelector('[data-pair-link]')?.remove();link.dataset.pairLink='true';panel.append(link);
    setTimeout(()=>{link.removeAttribute('href');link.textContent='연결 링크가 만료되었습니다. 이 Mac 연결을 다시 누르세요.'},300000);
   }catch(e){status.textContent=e.message}finally{pair.disabled=false}
  };
 }catch{status.textContent='연결 설정을 불러오지 못했습니다. 잠시 후 새로고침하세요.'}
})();
