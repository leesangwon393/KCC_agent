from rest_framework import serializers

from .models import Device, FileRecord, Folder, ReviewRequest


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["id", "name", "platform", "last_seen_at", "created_at"]
        read_only_fields = ["id", "last_seen_at", "created_at"]


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ["id", "name", "instructions_md", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class FileRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileRecord
        fields = [
            "id", "name", "source_device", "source_kind", "mime_type",
            "size_bytes", "sha256", "status", "folder",
            "classification_reason", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_source_device(self, device):
        if device and device.owner_id != self.context["request"].user.id:
            raise serializers.ValidationError("내 기기만 지정할 수 있습니다.")
        return device

    def validate_folder(self, folder):
        if folder and folder.owner_id != self.context["request"].user.id:
            raise serializers.ValidationError("내 폴더만 지정할 수 있습니다.")
        return folder

    def validate(self, attrs):
        status = attrs.get("status", getattr(self.instance, "status", FileRecord.Status.NEW))
        folder = attrs.get("folder", getattr(self.instance, "folder", None))
        if status == FileRecord.Status.SORTED and folder is None:
            raise serializers.ValidationError({"folder": "분류됨 상태에는 폴더가 필요합니다."})
        if status != FileRecord.Status.SORTED and folder is not None:
            raise serializers.ValidationError({"folder": "분류됨 상태에서만 폴더를 지정할 수 있습니다."})
        return attrs


class ReviewRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewRequest
        fields = ["id", "file", "question", "status", "answer", "answered_at", "created_at"]
        read_only_fields = ["id", "status", "answer", "answered_at", "created_at"]

    def validate_file(self, file):
        if file.owner_id != self.context["request"].user.id:
            raise serializers.ValidationError("내 파일만 지정할 수 있습니다.")
        if file.status != FileRecord.Status.OTHER:
            raise serializers.ValidationError("기타 상태의 파일만 확인 요청을 만들 수 있습니다.")
        if ReviewRequest.objects.filter(file=file).exists():
            raise serializers.ValidationError("이 파일의 확인 요청이 이미 있습니다.")
        return file


class ReviewAnswerSerializer(serializers.Serializer):
    answer = serializers.CharField(min_length=2, max_length=2000, help_text="사용자의 자연어 답변. 저장만 하며 폴더 생성이나 파일 이동은 실행하지 않습니다.")
