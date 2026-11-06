from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import FileRecord, Folder, ReviewRequest


class ApiBoundaryTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("owner", password="test-password-123")
        self.other = user_model.objects.create_user("other", password="test-password-123")
        self.client = APIClient()

    def test_public_docs_and_private_records(self):
        self.assertEqual(self.client.get("/api/v1/health/").status_code, 200)
        self.assertEqual(self.client.get("/swagger/").status_code, 200)
        self.assertEqual(self.client.get("/api/schema/?format=json").status_code, 200)
        self.assertIn(self.client.get("/api/v1/files/").status_code, (401, 403))

    def test_owner_isolation_and_foreign_folder_rejected(self):
        other_folder = Folder.objects.create(owner=self.other, name="비공개")
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/v1/folders/").json()["count"], 0)
        result = self.client.post("/api/v1/files/", {
            "name": "sample.pdf", "status": "sorted", "folder": str(other_folder.id),
        }, format="json")
        self.assertEqual(result.status_code, 400)
        self.assertEqual(FileRecord.objects.count(), 0)

    def test_answer_only_records_text(self):
        file = FileRecord.objects.create(owner=self.user, name="unknown.png", status="other")
        review = ReviewRequest.objects.create(owner=self.user, file=file, question="어디에 둘까요?")
        self.client.force_authenticate(self.user)
        result = self.client.post(f"/api/v1/reviews/{review.id}/answer/", {
            "answer": "사진 자료 폴더에 넣어줘",
        }, format="json")
        self.assertEqual(result.status_code, 200)
        review.refresh_from_db()
        file.refresh_from_db()
        self.assertEqual(review.status, "answered")
        self.assertEqual(file.status, "other")
        self.assertIsNone(file.folder)
        self.assertEqual(Folder.objects.count(), 0)
