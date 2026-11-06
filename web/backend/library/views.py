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


@extend_schema(tags=['기기 연결'])
@extend_schema_view(
    list=extend_schema(summary='기기 기록 목록 조회', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 기기 메타데이터를 관리합니다. 실제 Mac 연결 상태는 agent/status API에서 조회합니다. 목록은 페이지당 30개이며 page로 다음 페이지를 조회합니다.'),
    create=extend_schema(summary='기기 기록 등록', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 기기 메타데이터를 관리합니다. 실제 Mac 연결 상태는 agent/status API에서 조회합니다. 요청 본문의 정보를 새 기록으로 저장합니다.'),
    retrieve=extend_schema(summary='기기 기록 상세 조회', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 기기 메타데이터를 관리합니다. 실제 Mac 연결 상태는 agent/status API에서 조회합니다. 경로의 id에 해당하는 기록을 조회합니다.'),
    partial_update=extend_schema(summary='기기 기록 일부 수정', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 기기 메타데이터를 관리합니다. 실제 Mac 연결 상태는 agent/status API에서 조회합니다. 요청 본문에 보낸 필드만 수정합니다.'),
    destroy=extend_schema(summary='기기 기록 삭제', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 기기 메타데이터를 관리합니다. 실제 Mac 연결 상태는 agent/status API에서 조회합니다. DB 기록을 삭제합니다. 실제 기기나 Mac 폴더를 삭제하지 않습니다.'),
)
class DeviceViewSet(OwnedViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]


@extend_schema(tags=['폴더'])
@extend_schema_view(
    list=extend_schema(summary='분류 폴더 목록 조회', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 폴더 이름과 instructions_md 지침을 관리합니다. Mac의 실제 폴더나 지침 파일을 변경하지 않습니다. 목록은 페이지당 30개이며 page로 다음 페이지를 조회합니다.'),
    create=extend_schema(summary='분류 폴더 등록', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 폴더 이름과 instructions_md 지침을 관리합니다. Mac의 실제 폴더나 지침 파일을 변경하지 않습니다. 요청 본문의 정보를 새 기록으로 저장합니다.'),
    retrieve=extend_schema(summary='분류 폴더 상세 조회', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 폴더 이름과 instructions_md 지침을 관리합니다. Mac의 실제 폴더나 지침 파일을 변경하지 않습니다. 경로의 id에 해당하는 기록을 조회합니다.'),
    partial_update=extend_schema(summary='분류 폴더 일부 수정', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 폴더 이름과 instructions_md 지침을 관리합니다. Mac의 실제 폴더나 지침 파일을 변경하지 않습니다. 요청 본문에 보낸 필드만 수정합니다.'),
    destroy=extend_schema(summary='분류 폴더 삭제', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 폴더 이름과 instructions_md 지침을 관리합니다. Mac의 실제 폴더나 지침 파일을 변경하지 않습니다. DB 기록을 삭제합니다. 실제 기기나 Mac 폴더를 삭제하지 않습니다.'),
)
class FolderViewSet(OwnedViewSet):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]


@extend_schema(tags=['모든 파일'])
@extend_schema_view(
    list=extend_schema(summary='파일 기록 목록 조회', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 파일 메타데이터를 관리합니다. 실제 파일 이동은 에이전트 명령 API를 사용합니다. 목록은 status=new/sorted/other로 필터링할 수 있습니다. 목록은 페이지당 30개이며 page로 다음 페이지를 조회합니다.'),
    create=extend_schema(summary='파일 기록 등록', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 파일 메타데이터를 관리합니다. 실제 파일 이동은 에이전트 명령 API를 사용합니다. 목록은 status=new/sorted/other로 필터링할 수 있습니다. 요청 본문의 정보를 새 기록으로 저장합니다.'),
    retrieve=extend_schema(summary='파일 기록 상세 조회', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 파일 메타데이터를 관리합니다. 실제 파일 이동은 에이전트 명령 API를 사용합니다. 목록은 status=new/sorted/other로 필터링할 수 있습니다. 경로의 id에 해당하는 기록을 조회합니다.'),
    partial_update=extend_schema(summary='파일 기록 일부 수정', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. 파일 메타데이터를 관리합니다. 실제 파일 이동은 에이전트 명령 API를 사용합니다. 목록은 status=new/sorted/other로 필터링할 수 있습니다. 요청 본문에 보낸 필드만 수정합니다.'),
)
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


@extend_schema(tags=['분류 대기'])
@extend_schema_view(
    list=extend_schema(summary='분류 질문 목록 조회', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. DB에 저장된 분류 질문을 관리합니다. Mac 에이전트의 실시간 분류 대기는 agent/status의 snapshot에서 확인합니다. 목록은 페이지당 30개이며 page로 다음 페이지를 조회합니다.'),
    create=extend_schema(summary='분류 질문 등록', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. DB에 저장된 분류 질문을 관리합니다. Mac 에이전트의 실시간 분류 대기는 agent/status의 snapshot에서 확인합니다. 요청 본문의 정보를 새 기록으로 저장합니다.'),
    retrieve=extend_schema(summary='분류 질문 상세 조회', description='로그인한 사용자 본인의 데이터만 접근할 수 있습니다. DB에 저장된 분류 질문을 관리합니다. Mac 에이전트의 실시간 분류 대기는 agent/status의 snapshot에서 확인합니다. 경로의 id에 해당하는 기록을 조회합니다.'),
)
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
