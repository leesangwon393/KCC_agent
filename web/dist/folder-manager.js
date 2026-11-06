/* Folder additions are always available; filesystem access stays in the Mac app. */
(()=>{
 const button=document.getElementById('folder-add');
 const status=document.getElementById('folder-add-status');
 if(!button)return;
 const phone=/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
 async function open(target=status,create=false){
  const status=target;
  if(phone){status.textContent='연결한 Mac에서 폴더 화면을 열어 추가해 주세요.';return;}
  try{
   const response=await fetch('/api/v1/auth/session/',{credentials:'same-origin',cache:'no-store'});
   if(!response.ok)throw Error('로그인 상태를 확인하지 못했어요. 다시 시도해 주세요.');
   const session=await response.json();
   if(!session.authenticated){status.textContent='모아에 로그인한 뒤 폴더를 추가해 주세요.';document.querySelector('[data-login]')?.click();return;}
   status.textContent=(create?'Mac 선택창에서 ‘새로운 폴더’로 폴더를 만들고 선택하세요. 준비가 끝나면 이 파일의 폴더 목록에서 새 폴더를 골라 답변을 보내세요. ': '')+'Mac 연결 앱에서 새 폴더를 선택해 주세요. 기존 폴더는 유지하고, 추가한 폴더의 지침이 준비되면 목록에 자동 반영됩니다. 앱이 열리지 않으면 최신 Mac 연결 앱을 다운로드해 한 번 실행해 주세요.';
   window.location.href=create?'moa-helper://folders?create=1':'moa-helper://folders';
  }catch(error){status.textContent=error.message;}
 }
 window.MoaFolders={open};
 button.onclick=()=>open();
 document.addEventListener('click',event=>{
  const create=event.target.closest('[data-new-folder]');
  if(create&&!create.disabled)open(create.closest('[data-asset]').querySelector('[data-folder-create-status]'),true);
 });
})();
