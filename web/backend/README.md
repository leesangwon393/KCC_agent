# 모아 Django API 초안

`Django 5.2` + Django REST Framework + drf-spectacular로 만든 데이터 계약입니다. 기존 `KCC_agent/file-lifecycle-agent`의 실험용 판단·검증·실행기를 HTTP 서비스로 연결하기 전 단계입니다.

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

개인 데이터 엔드포인트는 Django 로그인 세션이 필요하고 소유자별로 격리됩니다. Swagger와 헬스 체크만 공개됩니다. 운영 사이트가 HTTPS로 제공되어도 브라우저 로그인이나 Apple 계정 연동은 아직 활성화하지 않았습니다. 파일 업로드, 실제 iCloud 이동, Mac 감시, AI 판단, 푸시 알림은 구현 전입니다. 답변 API도 질문에 대한 텍스트만 저장합니다.
