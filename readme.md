# 간편 시작: Mac 웹앱 + iCloud Drive

최상위 **모아 시작.command**를 더블클릭 → 모아에서 **iCloud Drive 연결** → 이후 **Dock의 모아**로 실행. Python과 실행기 설정은 자동으로 진행합니다. [설치와 동작 범위](web/local/README.md)를 참고하세요.

# KCC 파일 라이프사이클 에이전트 · 모아

- [`file-lifecycle-agent/`](file-lifecycle-agent/) — 파일 판단, 계획 검증, 승인 실행과 되돌리기 실험
- [`web/`](web/) — 모아 운영 데모, Django API, EC2 배포 소스
- [`web/INTEGRATION.md`](web/INTEGRATION.md) — 웹과 로컬 실행기 연결 계약 및 미구현 항목
- [`file-lifecycle-agent/docs/local_api.md`](file-lifecycle-agent/docs/local_api.md) — 맥 에이전트의 로컬 HTTP API (웹 연결용 엔드포인트·응답 형식)
- [`LOCAL_SETUP.md`](LOCAL_SETUP.md) — Mac에서 클론 후 웹·API·에이전트·브리지 실행

웹의 **에이전트 연결** 화면은 Mac 브리지를 통해 실제 에이전트 상태와 명령을 주고받습니다. 주요 운영 화면도 로그인한 계정의 실제 데이터를 사용하며, 상단 버튼으로 시연 모드를 선택할 수 있습니다.


## 웹 실제 데이터 모드

웹은 기본적으로 실제 데이터 모드로 열립니다. 연결 화면에서 로그인하면 대시보드·파일 검색·폴더·분류 대기·보관 대기·Mac 휴지통·명령 기록이 계정별 에이전트 상태를 사용합니다. 답변·이동 승인·유지·되돌리기·휴지통 복구는 기존 브리지 명령 API로 전달되며 5초마다 상태를 갱신합니다. 상단의 **시연 모드 보기**로 브라우저 예시 데이터를 별도로 사용할 수 있습니다. 실제 모드에서 폴더 설명은 읽기 전용이고 지침·감시·모델·정책 변경은 Mac에서 진행합니다. 브리지 업데이트 후 다시 실행해야 파일별 프로젝트 정보가 전송됩니다.
