"""First-run setup for the opt-in, loopback-only Mac installation."""
import json
import os
import secrets
from pathlib import Path

from django.contrib.auth import get_user_model, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_POST


def enabled(request):
    return (bool(os.environ.get('MOA_LOCAL_KEY'))
            and request.META.get('REMOTE_ADDR') in {'127.0.0.1', '::1'}
            and request.get_host().split(':')[0] in {'localhost', '127.0.0.1'})


def storage():
    return Path(os.environ['MOA_LOCAL_DATA'])


def cloud_root():
    return Path.home() / 'Library/Mobile Documents/com~apple~CloudDocs'


@require_POST
@csrf_protect
def unlock(request):
    if not enabled(request):
        return JsonResponse({'detail': 'Local installation required'}, status=404)
    if not secrets.compare_digest(request.headers.get('X-Moa-Local-Key', ''), os.environ['MOA_LOCAL_KEY']):
        return JsonResponse({'detail': 'Invalid local key'}, status=403)
    user = get_user_model().objects.get(username='local-owner')
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return JsonResponse({'ok': True})


@require_http_methods(['GET', 'POST'])
@csrf_protect
def setup(request):
    if not enabled(request):
        return JsonResponse({'detail': 'Local installation required'}, status=404)
    if not request.user.is_authenticated or request.user.get_username() != 'local-owner':
        return JsonResponse({'detail': 'Open Moa from the installed Mac launcher'}, status=403)
    root = cloud_root()
    config_path = storage() / 'icloud.json'
    if request.method == 'POST' and not config_path.exists():
        if not root.is_dir():
            return JsonResponse({'detail': '시스템 설정에서 iCloud Drive를 먼저 켜 주세요.'}, status=409)
        try:
            base = root / '모아'
            inbox = base / '받은 파일'
            inbox.mkdir(parents=True, exist_ok=True)
            projects = {}
            for pid, name, desc, keywords in [
                ('documents', '문서', '보고서, 기획서와 일반 문서를 보관합니다.', ['보고서', '기획서', '문서']),
                ('receipts', '영수증', '결제 영수증과 구매 증빙을 보관합니다.', ['영수증', '결제', 'receipt']),
                ('meetings', '회의', '회의록과 회의 자료를 보관합니다.', ['회의록', '회의', 'meeting']),
            ]:
                folder = base / name
                folder.mkdir(exist_ok=True)
                guide = folder / '_project.md'
                if not guide.exists():
                    guide.write_text('# ' + name + '\n\n' + desc + '\n', encoding='utf-8')
                projects[pid] = {'name': name, 'folder': str(folder), 'desc': desc, 'keywords': keywords}
            (storage() / 'projects.json').write_text(json.dumps(projects, ensure_ascii=False), encoding='utf-8')
            tmp = config_path.with_suffix('.tmp')
            tmp.write_text(json.dumps({'inbox': str(inbox)}, ensure_ascii=False), encoding='utf-8')
            tmp.replace(config_path)
        except OSError:
            return JsonResponse({'detail': 'iCloud Drive 폴더에 접근할 수 없습니다. Mac의 파일 접근 권한을 확인해 주세요.'}, status=409)
    return JsonResponse({'available': root.is_dir(), 'configured': config_path.exists(),
                         'folder': 'iCloud Drive / 모아 / 받은 파일'})
