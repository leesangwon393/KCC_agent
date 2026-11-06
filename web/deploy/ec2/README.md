# EC2 배포

`update_ssm.py`는 `web/dist`와 `web/backend`를 아카이브로 묶어 AWS Systems Manager를 통해 기존 EC2 인스턴스에 배포합니다. 서버에 설정된 HTTPS 인증서와 nginx SSL 설정은 별도로 관리합니다. GitHub Actions는 현재 검사만 수행하며 자동 배포하지 않습니다.

필수 환경변수:

- `MOA_EC2_INSTANCE`: 배포할 인스턴스 ID
- `MOA_PUBLIC_HOST`: 사이트의 호스트명 또는 IP

선택 환경변수: `MOA_AWS_REGION`(기본 `ap-northeast-2`), `MOA_AWS_PROFILE`, `MOA_AWS_CLI`(기본 `aws`), `MOA_AWS_TIME_PRELOAD`(로컬 시계 오차 보정이 필요한 환경에만 사용).

```sh
MOA_EC2_INSTANCE=... MOA_PUBLIC_HOST=... python deploy/ec2/update_ssm.py
```

배포 전 해당 인스턴스에 SSM 권한과 nginx가 있어야 합니다. Django 개인 데이터 API는 로그인 세션이 필요하며, 실제 파일 수집·이동과 에이전트 실행은 아직 연결되지 않았습니다.
