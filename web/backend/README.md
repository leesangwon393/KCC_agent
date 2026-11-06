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

## 메뉴별 요청 설명

Swagger는 메뉴별 태그로 요청을 묶고, 각 요청에 한국어 요약·용도·입력값·응답·오류를 표시합니다. 상단 검색으로 메뉴나 요청을 찾을 수 있습니다.

| 메뉴 | 사용하는 요청 |
| --- | --- |
| 기기 연결 | `GET auth/session`, `POST auth/login`, `POST auth/logout`, `devices` |
| 대시보드 | `GET agent/status`의 연결 상태·파일·최근 명령 |
| 모든 파일 | `files`의 DB 파일 기록, `GET agent/status`의 실제 Mac 파일 |
| 폴더 | `folders`의 DB 지침, `GET agent/status`의 Mac catalog |
| 분류 대기 | `reviews`의 DB 질문·답변, `POST agent/commands`의 `answer`·`approve`·`keep` |
| 보관 대기 | `POST agent/commands`의 `approve`·`keep` |
| Mac 휴지통 | `POST agent/commands`의 `restore_trashed` |
| 명령 기록·되돌리기 | `GET agent/status`의 commands, `POST agent/commands`의 `undo` |
| Mac 브리지 | `POST agent/bridge/poll`, `POST agent/bridge/result` |
| 로컬 설정 | `POST local/unlock`, `GET/POST local/setup` (운영 서버에서는 404) |
| 시스템 | `GET health` |

위 경로의 공통 접두사는 `/api/v1/`이며 끝에 `/`를 붙입니다. 공통 상태·명령 API는 여러 메뉴에서 함께 사용하므로 요청 설명에서 메뉴와 action을 확인하세요. 명령 접수(201) 후 실제 실행 결과는 상태 API로 확인합니다.

설명은 `library/views.py`, `library/api_docs.py`, 메뉴 순서는 `moa_api/settings.py`에 저장합니다. 일반 Django 뷰와 브리지 API의 문서 정보는 OpenAPI 후처리로 추가하여 실제 인증·CSRF 처리에는 영향을 주지 않습니다.

## AWS 웹앱에서 Apple 로그인과 Mac 연결

[설정 및 사용자 흐름](APPLE_LOGIN.md)을 참고하세요. Apple Developer 및 HTTPS 도메인 설정이 없으면 Apple 로그인은 준비 중으로 표시됩니다. 기존 계정으로 로그인하면 **이 Mac 연결**에서 일회용 연결 링크를 발급할 수 있습니다. Mac 도우미에서 승인하면 토큰 입력 없이 AWS 동기화를 시작합니다.

## 일반 회원가입과 계정 DB

운영 사이트 `/#signup`에서 가입할 수 있습니다. `POST /api/v1/auth/signup/`는 아이디·선택 닉네임·비밀번호·비밀번호 확인을 검증하고 가입 즉시 로그인합니다. 먼저 `GET /api/v1/auth/session/`에서 CSRF 토큰을 받아 전송하고, 가입 후 새 토큰을 조회합니다. 가입 이후 Mac 연결을 별도로 승인해야 파일 상태가 동기화됩니다.

계정은 기존 Django `auth_user` 테이블을 사용합니다. 아이디(`username`, 소문자, 고유), 닉네임(`first_name`), 비밀번호 해시(`password`), 가입일(`date_joined`), 최근 로그인(`last_login`), 활성 상태를 저장합니다. 이메일은 수집하지 않으며 이메일 인증·비밀번호 재설정 메일은 현재 제공하지 않습니다. 일반 가입으로 관리자 권한을 부여하지 않습니다. 기존 Apple 계정과 로컬 소유자 계정은 유지합니다.

운영 SQLite DB는 EC2의 `/var/lib/moa/db.sqlite3`에 보관되어 코드 재배포 후에도 유지됩니다. 로컬 Mac DB는 `~/Library/Application Support/Moa/db.sqlite3`입니다. 별도의 사용자 테이블을 중복 생성하지 않으며, Django의 사용자·세션 테이블과 기존 소유자 외래키를 공유합니다. 비밀번호 원문이나 확인 값은 저장하지 않습니다.

회원가입 후에는 [Mac·iPhone 온보딩](../ONBOARDING.md)으로 이동합니다. 사용자별 진행 상황과 파일 수신 테스트 결과를 DB에 저장하고, 연결 메뉴에서 언제든 재개할 수 있습니다.
