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
AUTH_PASSWORD_VALIDATORS = []
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
    "DESCRIPTION": "파일 수집·폴더 지침·분류 확인을 위한 API 초안. 개인 데이터 엔드포인트는 로그인 세션이 필요합니다. Apple/iCloud 연동과 에이전트 실행은 아직 구현되지 않았습니다.",
    "VERSION": "0.1.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": False, "displayRequestDuration": True},
}

SESSION_COOKIE_SECURE = os.environ.get("MOA_HTTPS") == "1"
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
if SESSION_COOKIE_SECURE:
    # nginx sets this header on the HTTPS vhost; Django needs it for CSRF Origin checks.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
