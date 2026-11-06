# 모아 웹 · API

`dist/`는 [운영 사이트](https://3.38.192.19/)의 정적 화면, `backend/`는 사용자별 데이터 API, `bridge/`는 Mac 에이전트와 Django API 사이의 HTTPS 중계 프로그램입니다. `deploy/ec2/`는 EC2 배포 절차입니다.

## 실제 연결 범위

- 사이트의 **에이전트 연결** 화면은 로그인한 사용자의 Mac 상태를 서버에서 읽고, 파일별 답변·승인·유지·되돌리기 명령을 대기열에 넣습니다.
- Mac 브리지는 로컬 에이전트의 `/api/state`를 읽어 요약 메타데이터를 HTTPS 서버에 보내고, 승인 명령을 로컬 API로 전달합니다. Mac 에이전트가 실제 파일 계획과 해시를 다시 검증합니다.
- **서비스 소개·대시보드·모든 파일·폴더·분류 대기·삭제 관리·설정**은 여전히 별도의 브라우저 시연 데이터입니다. 실제 데이터와 시연 데이터를 섞지 않습니다.
- Mac 에이전트와 브리지가 실행 중이지 않으면 실제 연결 화면은 연결 대기로 표시됩니다. 실행 방법은 [`bridge/README.md`](bridge/README.md)를 참고하세요.

## 로컬 확인

```sh
cd web/backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
MOA_DJANGO_SECRET_KEY=local-secret .venv/bin/python manage.py test library
MOA_DJANGO_SECRET_KEY=local-secret .venv/bin/python manage.py runserver
```

정적 화면은 `python3 -m http.server 8765 --directory web/dist`로 볼 수 있지만, 로그인과 실제 연결 화면은 `/api/` 프록시가 있는 배포 환경에서 동작합니다. API 문서는 `/swagger/`, 헬스 체크는 `/api/v1/health/`입니다. [`INTEGRATION.md`](INTEGRATION.md)에 연결 경계와 남은 작업을 정리했습니다.
