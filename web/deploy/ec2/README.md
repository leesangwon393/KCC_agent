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

## 운영 주소

현재 무료 주소는 https://moa.3-38-192-19.sslip.io 입니다. sslip.io가 주소에 포함된 IP를 DNS로 반환하므로 서버 IP가 바뀌면 주소도 갱신해야 합니다. 기존 https://3.38.192.19 접속도 유지합니다.

nginx의 `/etc/nginx/moa-ssl.conf`에 두 HTTPS 호스트를 등록했습니다. 새 주소의 Let's Encrypt 인증서는 `/etc/letsencrypt/live/moa.3-38-192-19.sslip.io/`에 있으며 `moa-certbot-renew.timer`가 갱신하고 nginx를 다시 읽습니다. `/etc/moa.env`의 `MOA_ALLOWED_HOSTS`, `MOA_CSRF_TRUSTED_ORIGINS`, `MOA_PUBLIC_ORIGIN`, `MOA_CLOUD_ORIGIN`도 새 주소를 사용합니다. 헬퍼 배포본은 새 운영 주소로 빌드해야 합니다.
