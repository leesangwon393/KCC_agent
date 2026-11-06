# KCC 파일 라이프사이클 에이전트 · 모아

- [`file-lifecycle-agent/`](file-lifecycle-agent/) — 파일 판단, 계획 검증, 승인 실행과 되돌리기 실험
- [`web/`](web/) — 모아 운영 데모, Django API, EC2 배포 소스
- [`web/INTEGRATION.md`](web/INTEGRATION.md) — 웹과 로컬 실행기 연결 계약 및 미구현 항목
- [`file-lifecycle-agent/docs/local_api.md`](file-lifecycle-agent/docs/local_api.md) — 맥 에이전트의 로컬 HTTP API (웹 연결용 엔드포인트·응답 형식)
- [`LOCAL_SETUP.md`](LOCAL_SETUP.md) — Mac에서 클론 후 웹·API·에이전트·브리지 실행

웹의 **에이전트 연결** 화면은 Mac 브리지를 통해 실제 에이전트 상태와 명령을 주고받습니다. 다른 웹 화면은 시연 데이터로 동작합니다.
