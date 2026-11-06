"""Account-specific Mac/iPhone setup progress and observable file receipt."""
from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AgentLink, OnboardingProgress


def current_state(user, progress):
    links = list(AgentLink.objects.filter(owner=user))
    cutoff = timezone.now() - timedelta(seconds=30)
    online = [link for link in links if link.last_seen_at and link.last_seen_at > cutoff]
    received = []
    baseline = set(progress.baseline_assets)
    if progress.test_started_at:
        for link in online:
            if link.last_seen_at <= progress.test_started_at:
                continue
            for asset in (link.snapshot or {}).get('assets', []):
                if isinstance(asset, dict) and str(link.id) + ':' + str(asset.get('id')) not in baseline:
                    received.append(str(asset.get('name') or '새 파일'))
    return {'mac_connected': bool(online), 'iphone_icloud_confirmed': progress.iphone_icloud_confirmed,
            'test_started': progress.test_started_at is not None,
            'file_received': bool(received), 'received_filename': received[0] if received else None,
            'completed': progress.completed_at is not None,
            'completed_at': progress.completed_at.isoformat() if progress.completed_at else None}


@extend_schema(exclude=True)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def progress(request):
    record, _ = OnboardingProgress.objects.get_or_create(owner=request.user)
    if request.method == 'POST':
        if not isinstance(request.data, dict):
            return Response({'detail': '온보딩 요청이 올바르지 않습니다.'}, status=400)
        action = request.data.get('action')
        if action == 'confirm_iphone':
            record.iphone_icloud_confirmed = True
            record.save(update_fields=['iphone_icloud_confirmed'])
        elif action == 'start_test':
            state = current_state(request.user, record)
            if not state['mac_connected'] or not record.iphone_icloud_confirmed:
                return Response({'detail': 'Mac 연결과 iPhone iCloud 설정 확인을 먼저 완료하세요.'}, status=409)
            record.baseline_assets = [str(link.id) + ':' + str(asset.get('id'))
                for link in AgentLink.objects.filter(owner=request.user)
                for asset in (link.snapshot or {}).get('assets', []) if isinstance(asset, dict)]
            record.test_started_at = timezone.now()
            record.save(update_fields=['baseline_assets', 'test_started_at'])
        elif action == 'complete':
            state = current_state(request.user, record)
            if not (state['mac_connected'] and state['iphone_icloud_confirmed'] and state['file_received']):
                return Response({'detail': '테스트 시작 후 새 파일이 Mac에서 수신되어야 완료할 수 있습니다.'}, status=409)
            record.completed_at = record.completed_at or timezone.now()
            record.save(update_fields=['completed_at'])
        else:
            return Response({'detail': '지원하지 않는 온보딩 요청입니다.'}, status=400)
    return Response(current_state(request.user, record))
