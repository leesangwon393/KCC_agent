import uuid

from django.conf import settings
from django.db import models


class OwnedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Device(OwnedModel):
    class Platform(models.TextChoices):
        MAC = "mac", "Mac"
        IPHONE = "iphone", "iPhone"
        IPAD = "ipad", "iPad"

    name = models.CharField(max_length=120)
    platform = models.CharField(max_length=12, choices=Platform.choices)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]


class Folder(OwnedModel):
    name = models.CharField(max_length=120)
    instructions_md = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["owner", "name"], name="unique_folder_per_owner")]


class FileRecord(OwnedModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        SORTED = "sorted", "Sorted"
        OTHER = "other", "Other"

    name = models.CharField(max_length=255)
    source_device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True)
    source_kind = models.CharField(max_length=32, default="unknown")
    mime_type = models.CharField(max_length=120, blank=True)
    size_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True)
    classification_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]


class ReviewRequest(OwnedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ANSWERED = "answered", "Answered"

    file = models.OneToOneField(FileRecord, on_delete=models.CASCADE, related_name="review")
    question = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    answer = models.TextField(blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
