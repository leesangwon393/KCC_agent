# KCC 파일 라이프사이클 에이전트 · 모아

> 다운로드한 강의자료와 아이폰·맥 캡처를 맞는 폴더에 알아서 정리하는 **맥 로컬 에이전트**와,
> 그 상태를 보고 결정을 내리는 **웹(모아)** 입니다.

![architecture](file-lifecycle-agent/docs/figures/architecture.png)

## 🚀 간편 시작: Mac 웹앱 + iCloud Drive

최상위 **모아 시작.command**를 더블클릭 → 모아에서 **iCloud Drive 연결** → 이후 **Dock의 모아**로 실행합니다. Python과 실행기 설정은 자동으로 진행합니다. 자세한 내용은 [설치와 동작 범위](web/local/README.md)를 보세요.

## 구성

| 폴더 | 내용 |
|---|---|
| 📂 [`file-lifecycle-agent/`](file-lifecycle-agent/) | 맥에서 도는 에이전트: 파일 판단(Qwen3-1.7B + 규칙), 계획 검증, 승인 실행과 되돌리기 |
| 🌐 [`web/`](web/) | 모아 웹, Django API, EC2 배포 소스 |
| 🔌 [`web/bridge/`](web/bridge/) | 맥 에이전트 상태를 API로 보내고 웹의 명령을 전달하는 브리지 |
| 🖥️ [`web/local/`](web/local/) | Mac 웹앱 설치와 실행 (`모아 시작.command`) |

## 시연

### 1. 아이폰 캡처 → 에이전트가 이름 짓고 폴더에 저장

![demo1](file-lifecycle-agent/docs/figures/demo1_iphone_capture.png)

- **캡처:** 아이폰 뒷면을 두 번 탭하면 단축어가 스크린샷을 iCloud `KCC-inbox`에 저장합니다.
- **가져오기:** 맥의 감시기가 새 파일을 2초 안에 감지합니다. iCloud에 아직 안 내려온 파일은 `brctl download`로 내려받기를 요청합니다.
- **이름 짓기:** macOS Vision OCR로 글자를 읽고, Qwen3-1.7B가 `set_caption` 도구로 짧은 이름을 붙입니다(`Shot_….png` → `KCC 대회 공지.png`). 이름은 화면 속 단어만 쓸 수 있고, 경로 문자와 지시문은 거부합니다.
- **분류:** 내용과 폴더별 `_project.md`를 비교해 맞는 폴더에 자동 저장합니다. 되돌리기도 됩니다.

### 2. eCampus 강의자료 → 한 번 답하면 다음부터 자동

![demo2](file-lifecycle-agent/docs/figures/demo2_lecture_download.png)

- **출처 읽기:** 브라우저가 파일에 남긴 다운로드 페이지 주소(`kMDItemWhereFroms`)로 어느 강의실에서 받았는지 알아냅니다.
- **처음 한 번:** 처음 보는 강의실이면 맥에 **"어느 폴더에 저장할까요?"** 선택 창이 뜹니다.
- **학습:** 고르면 `강의실 → 폴더` 규칙을 저장하고, Qwen이 `update_profile` 도구로 그 폴더 `_project.md`에 메모를 한 줄 덧붙입니다.
- **다음부터:** 같은 강의실에서 받은 파일은 모델 없이 규칙으로 바로 저장합니다. 잘못 저장했으면 되돌리기를 누르면 되고, 그때 배운 규칙도 같이 지워집니다.
- **문서 읽기:** PDF·PPTX·DOCX는 파일 이름과 본문을 읽습니다. 그래서 강의실 주소가 남지 않는 문서 뷰어로 받은 파일도 분류할 수 있습니다.

### 3. 설치 파일 → 3일 뒤 휴지통, 언제든 복구

![demo3](file-lifecycle-agent/docs/figures/demo3_installer_cleanup.png)

- **대상:** 다운로드·바탕화면의 `.dmg`, `.pkg`, 그리고 setup/install이 이름에 들어간 `.zip`·`.exe`입니다. 강의자료는 건드리지 않습니다.
- **기한:** 처음 본 시각부터 N일(기본 3일)이 지나면 `~/.Trash`로 옮깁니다. 지우지 않고 옮기기만 합니다.
- **시연:** 기준이 맥 시계라서, 시계를 3일 앞으로 돌리면 1분 안에 동작합니다.
- **복구:** 웹 화면의 복구 버튼을 누르면 원래 자리로 되돌아갑니다. 모델은 관여하지 않고 정해진 규칙으로만 처리합니다.

### 그 밖의 기능

- **모아서 물어보기:** 5시간마다 맥을 쓰고 있을 때만 확인이 필요한 파일을 번호 목록으로 보여 줍니다. "1,2는 제어공학 폴더 새로 만들어서 넣어"처럼 자연어로 답하면 새 폴더와 에이전트 지침을 만들고 옮깁니다.
- **안전장치:** 모델에는 이동·삭제·셸 도구가 없습니다. 근거는 원문을 그대로 인용해야 하고, 파일 속 지시문은 차단합니다. 모든 이동은 저널에 남고 되돌릴 수 있습니다.

## 웹 실제 데이터 모드

웹은 기본적으로 실제 데이터 모드로 열립니다.

- **로그인하면:** 대시보드, 파일 검색, 폴더, 분류 대기, 보관 대기, Mac 휴지통, 명령 기록이 계정별 에이전트 상태를 사용합니다.
- **명령 전달:** 답변, 이동 승인, 유지, 되돌리기, 휴지통 복구는 브리지 명령 API로 Mac에 전달되고, 상태는 5초마다 갱신됩니다.
- **시연 모드:** 상단의 **시연 모드 보기**를 누르면 브라우저 예시 데이터로 따로 볼 수 있습니다.
- **Mac에서만 바꿀 수 있는 것:** 실제 모드에서는 폴더 설명이 읽기 전용입니다. 지침, 감시, 모델, 정책 변경은 Mac에서 합니다.
- 브리지를 업데이트한 뒤에는 브리지를 다시 실행해야 파일별 프로젝트 정보가 전송됩니다.

## 문서

| 문서 | 내용 |
|---|---|
| [`LOCAL_SETUP.md`](LOCAL_SETUP.md) | Mac에서 클론 후 웹·API·에이전트·브리지 실행 |
| [`file-lifecycle-agent/README.md`](file-lifecycle-agent/README.md) | 에이전트 동작 방식, 실행 옵션, 결과 요약 |
| [`file-lifecycle-agent/docs/local_api.md`](file-lifecycle-agent/docs/local_api.md) | 맥 에이전트의 로컬 HTTP API (웹 연결용 엔드포인트·응답 형식) |
| [`web/INTEGRATION.md`](web/INTEGRATION.md) | 웹과 로컬 실행기 연결 계약 및 미구현 항목 |
| [`file-lifecycle-agent/docs/experiments.md`](file-lifecycle-agent/docs/experiments.md) | 모델·가드·학습 실험 기록 |
