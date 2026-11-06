from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Device, FileRecord, Folder, ReviewRequest
from .serializers import (
    DeviceSerializer, FileRecordSerializer, FolderSerializer,
    ReviewAnswerSerializer, ReviewRequestSerializer,
)


class OwnedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@extend_schema_view(list=extend_schema(summary="내 기기 목록"), create=extend_schema(summary="기기 기록 등록"))
class DeviceViewSet(OwnedViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]


@extend_schema_view(list=extend_schema(summary="내 분류 폴더 목록"), create=extend_schema(summary="폴더 지침 초안 만들기"))
class FolderViewSet(OwnedViewSet):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]


@extend_schema_view(list=extend_schema(summary="내 파일 기록 목록"), create=extend_schema(summary="파일 메타데이터 접수"))
class FileRecordViewSet(OwnedViewSet):
    queryset = FileRecord.objects.all()
    serializer_class = FileRecordSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("folder", "source_device")
        status_filter = self.request.query_params.get("status")
        if status_filter in FileRecord.Status.values:
            queryset = queryset.filter(status=status_filter)
        return queryset


@extend_schema_view(list=extend_schema(summary="내 분류 확인 요청"), create=extend_schema(summary="기타 파일의 확인 요청 만들기"))
class ReviewRequestViewSet(OwnedViewSet):
    queryset = ReviewRequest.objects.all()
    serializer_class = ReviewRequestSerializer
    http_method_names = ["get", "post", "head", "options"]

    @extend_schema(
        summary="분류 질문에 자연어로 답하기",
        description="답변을 저장하고 요청을 answered로 표시합니다. AI 분류, 폴더 생성, iCloud 파일 이동은 아직 실행하지 않습니다.",
        request=ReviewAnswerSerializer,
        responses={200: ReviewRequestSerializer},
    )
    @action(detail=True, methods=["post"], url_path="answer")
    def answer(self, request, pk=None):
        review = self.get_object()
        if review.status == ReviewRequest.Status.ANSWERED:
            return Response({"detail": "이미 답변한 요청입니다."}, status=status.HTTP_409_CONFLICT)
        serializer = ReviewAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review.answer = serializer.validated_data["answer"]
        review.status = ReviewRequest.Status.ANSWERED
        review.answered_at = timezone.now()
        review.save(update_fields=["answer", "status", "answered_at"])
        return Response(ReviewRequestSerializer(review).data)
