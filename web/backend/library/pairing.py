"""Short-lived, single-use Mac pairing tickets issued by a logged-in owner."""
import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AgentLink, MacPairing


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@extend_schema(exclude=True)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create(request):
    now = timezone.now()
    MacPairing.objects.filter(expires_at__lt=now).delete()
    # The newest ticket replaces earlier, unused links for this account.
    MacPairing.objects.filter(owner=request.user, consumed_at=None).delete()
    secret = secrets.token_urlsafe(48)
    MacPairing.objects.create(owner=request.user, secret_hash=digest(secret), expires_at=now + timedelta(minutes=5))
    response = Response({'pairing_secret': secret, 'expires_in': 300}, status=201)
    response['Cache-Control'] = 'no-store'
    return response


@extend_schema(exclude=True)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def consume(request):
    secret = request.data.get('pairing_secret')
    if not isinstance(secret, str) or not 32 <= len(secret) <= 128:
        return Response({'detail': '연결 요청이 올바르지 않습니다.'}, status=400)
    with transaction.atomic():
        ticket = MacPairing.objects.filter(secret_hash=digest(secret), consumed_at=None, expires_at__gt=timezone.now()).first()
        if ticket is None or not ticket.owner.is_active:
            return Response({'detail': '연결 요청이 만료되었거나 이미 사용되었습니다. AWS 화면에서 다시 연결하세요.'}, status=403)
        if not MacPairing.objects.filter(pk=ticket.pk, consumed_at=None).update(consumed_at=timezone.now()):
            return Response({'detail': '이미 사용된 연결 요청입니다.'}, status=403)
        token = secrets.token_urlsafe(48)
        AgentLink.objects.create(owner=ticket.owner, label='내 Mac · ' + timezone.now().strftime('%m/%d %H:%M'), token_hash=digest(token))
    response = Response({'bridge_token': token})
    response['Cache-Control'] = 'no-store'
    return response


@extend_schema(exclude=True)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def disconnect(request):
    from .agent_api import _bridge_link
    link = _bridge_link(request)
    if link is None:
        return Response({'detail': 'Invalid bridge token'}, status=403)
    link.delete()
    return Response({'disconnected': True})
