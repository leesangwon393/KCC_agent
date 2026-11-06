"""Small, authenticated API for the Moa web draft."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("MOA_DJANGO_SECRET_KEY", "local-development-only-change-me")
DEBUG = os.environ.get("MOA_DEBUG") == "1"
ALLOWED_HOSTS = [host for host in os.environ.get("MOA_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host]
CSRF_TRUSTED_ORIGINS = [origin for origin in os.environ.get("MOA_CSRF_TRUSTED_ORIGINS", "").split(",") if origin]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "library",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "moa_api.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "moa_api.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.environ.get("MOA_DB_PATH", BASE_DIR / "db.sqlite3")}}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_TZ = True
STATIC_URL = "/django-static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 30,
}
SPECTACULAR_SETTINGS = {
    "TITLE": "모아 API",
    "DESCRIPTION": "메뉴별 모아 API 문서. 각 요청을 펼치면 용도, 인증 방식, 입력값과 응답을 확인할 수 있습니다. 브라우저 요청은 로그인 세션과 변경 요청의 X-CSRFToken이 필요하며, Mac 브리지는 Bearer 토큰을 사용합니다.",
    "VERSION": "0.1.0",
    "POSTPROCESSING_HOOKS": ["drf_spectacular.hooks.postprocess_schema_enums", "library.api_docs.complete_schema"],
    "TAGS": [{"name": name, "description": description} for name, description in [
        ("시작하기", "회원가입 이후 Mac과 iPhone 연결 가이드"),
        ("기기 연결", "회원가입, 로그인, 세션 및 기기 기록"),
        ("대시보드 · 에이전트 상태", "여러 메뉴에서 함께 사용하는 Mac 상태와 명령 기록"),
        ("모든 파일", "파일 메타데이터 조회와 관리"),
        ("폴더", "폴더 정보와 분류 지침"),
        ("분류 대기", "분류 질문 조회와 답변 저장"),
        ("파일 처리 · 보관 · 휴지통", "메뉴별 작업을 Mac 에이전트에 요청"),
        ("Mac 브리지", "Mac 중계 프로그램 전용 동기화"),
        ("로컬 설정", "Mac 설치 환경에서만 사용, 운영 서버에서는 404"),
        ("시스템", "서버 상태 확인"),
    ]],
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": False, "displayRequestDuration": True, "docExpansion": "list", "filter": True},
}

SESSION_COOKIE_SECURE = os.environ.get("MOA_HTTPS") == "1"
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Sign in with Apple. Keep the private key outside source and release bundles.
MOA_PUBLIC_ORIGIN = os.environ.get('MOA_PUBLIC_ORIGIN', 'https://3.38.192.19').rstrip('/')
MOA_CLOUD_ORIGIN = os.environ.get('MOA_CLOUD_ORIGIN', 'https://3.38.192.19').rstrip('/')
APPLE_CLIENT_ID = os.environ.get('MOA_APPLE_CLIENT_ID', '')
APPLE_TEAM_ID = os.environ.get('MOA_APPLE_TEAM_ID', '')
APPLE_KEY_ID = os.environ.get('MOA_APPLE_KEY_ID', '')
APPLE_PRIVATE_KEY_PATH = os.environ.get('MOA_APPLE_PRIVATE_KEY_PATH', '')
