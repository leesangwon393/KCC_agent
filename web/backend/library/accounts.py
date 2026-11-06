"""Public registration using Django's existing hashed-password user database."""
import json
import re

from django.contrib.auth import get_user_model, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST


@require_POST
@csrf_protect
def sign_up(request):
    if request.user.is_authenticated:
        return JsonResponse({'detail': '이미 로그인되어 있습니다.'}, status=409)
    try:
        body = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'detail': 'JSON 형식의 가입 정보를 보내 주세요.'}, status=400)
    if not isinstance(body, dict):
        return JsonResponse({'detail': '가입 정보가 올바르지 않습니다.'}, status=400)
    errors = {}
    username = body.get('username')
    nickname = body.get('nickname', '')
    password = body.get('password')
    confirmation = body.get('password_confirm')
    username = username.strip().lower() if isinstance(username, str) else ''
    nickname = nickname.strip() if isinstance(nickname, str) else None
    if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{3,29}', username):
        errors['username'] = ['아이디는 영문 소문자·숫자로 시작하는 4~30자의 영문·숫자·밑줄·점·하이픈으로 입력하세요.']
    elif username == 'local-owner' or username.startswith(('apple_', 'test_cloud_')):
        errors['username'] = ['사용할 수 없는 아이디입니다. 다른 아이디를 입력하세요.']
    elif get_user_model().objects.filter(username__iexact=username).exists():
        errors['username'] = ['이미 사용 중인 아이디입니다.']
    if nickname is None or len(nickname) > 30 or any(ord(c) < 32 for c in nickname):
        errors['nickname'] = ['닉네임은 30자 이내로 입력하세요.']
    user = get_user_model()(username=username, first_name=nickname or '')
    if not isinstance(password, str) or len(password) > 128:
        errors['password'] = ['비밀번호는 10~128자로 입력하세요.']
    else:
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            errors['password'] = exc.messages
    if not isinstance(confirmation, str) or password != confirmation:
        errors['password_confirm'] = ['비밀번호가 일치하지 않습니다.']
    if errors:
        return JsonResponse({'detail': '입력한 정보를 확인해 주세요.', 'errors': errors}, status=400)
    try:
        with transaction.atomic():
            user.set_password(password)
            user.save()
    except IntegrityError:
        return JsonResponse({'detail': '이미 사용 중인 아이디입니다.',
                             'errors': {'username': ['이미 사용 중인 아이디입니다.']}}, status=409)
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    response = JsonResponse({'authenticated': True, 'username': user.username,
                             'display_name': user.first_name or user.username}, status=201)
    response['Cache-Control'] = 'no-store'
    return response
