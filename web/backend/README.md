# 모아 Django API 초안

`Django 5.2` + Django REST Framework + drf-spectacular로 만든 API입니다. Mac 브리지가 `file-lifecycle-agent`의 로컬 API와 상태·명령을 중계합니다.

## 로컬 실행

```sh
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
MOA_DJANGO_SECRET_KEY=local-secret .venv/bin/python manage.py migrate
MOA_DJANGO_SECRET_KEY=local-secret .venv/bin/python manage.py runserver
```

- Swagger UI: `http://127.0.0.1:8000/swagger/`
- OpenAPI JSON: `http://127.0.0.1:8000/api/schema/?format=json`
- 헬스 체크: `http://127.0.0.1:8000/api/v1/health/`

## API 범위

| 경로 | 의미 |
| --- | --- |
| `/api/v1/devices/` | Mac, iPhone, iPad 기기 기록 |
| `/api/v1/folders/` | 폴더 이름과 `instructions_md` 관리 |
| `/api/v1/files/` | 파일 메타데이터와 분류 상태 (`new`, `sorted`, `other`) |
| `/api/v1/reviews/` | 기타 파일에 대한 분류 질문 |
| `/api/v1/reviews/{id}/answer/` | 자연어 답변 저장 |
| `/api/v1/agent/status/`, `/api/v1/agent/commands/` | 로그인 사용자의 Mac 상태와 승인 요청 |
| `/api/v1/agent/bridge/poll/`, `/api/v1/agent/bridge/result/` | 토큰 인증 Mac 브리지의 상태·명령 동기화 |

개인 데이터 엔드포인트는 Django 로그인 세션이 필요하고 소유자별로 격리됩니다. Swagger와 헬스 체크만 공개됩니다. 브라우저 로그인과 Mac 브리지 연결은 **에이전트 연결** 화면에서 동작합니다. Apple 계정 연동은 아직 없습니다. 기존 파일·폴더·질문 API는 데이터 계약입니다. Mac 감시와 파일 실행은 `file-lifecycle-agent/`의 로컬 프로세스가 담당하며, 브리지가 실행되지 않으면 웹 연결 화면은 오프라인입니다. 푸시 알림과 기기 간 전체 화면 동기화는 구현 전입니다. 기존 답변 API는 질문에 대한 텍스트만 저장합니다.
