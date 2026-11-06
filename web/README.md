# 모아 웹 · API

운영 데모와 Django API의 GitHub 소스입니다. `dist/`는 [운영 데모](https://3.38.192.19/)의 정적 화면이고, `backend/`는 로그인 사용자별 데이터 계약입니다. `deploy/ec2/`는 현재 EC2 배포 절차입니다.

## 현재 동작 범위

- 화면의 파일, 폴더, 분류 대기, 삭제 관리, 처리 기록은 브라우저 `localStorage`의 시연 데이터입니다. 실제 기기 파일을 읽거나 옮기지 않습니다.
- Django API에는 기기, 폴더, 파일 메타데이터, 분류 질문과 답변 저장이 있습니다. 개인 데이터는 로그인 세션과 소유자 범위로 제한됩니다.
- 에이전트 실행기는 `../file-lifecycle-agent/`에 별도로 있습니다. 웹/API와 실행기가 아직 호출로 연결되지 않았습니다.

## 로컬 확인

```sh
cd web/backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
MOA_DJANGO_SECRET_KEY=local-secret .venv/bin/python manage.py test library
MOA_DJANGO_SECRET_KEY=local-secret .venv/bin/python manage.py runserver
```

정적 화면은 `python3 -m http.server 8765 --directory web/dist`로 확인할 수 있습니다. API 문서는 `/swagger/`, 헬스 체크는 `/api/v1/health/`입니다.

## 다음 연결 단계

[연결 계약 초안](INTEGRATION.md)에 데이터 흐름, 기존 엔드포인트와 구현이 필요한 승인·삭제·저널 계약을 정리했습니다. 실제 파일 작업은 사용자 승인 뒤 로컬 실행기에서 현재 해시와 계획을 다시 검증해야 합니다.
