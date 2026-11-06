from rest_framework.routers import DefaultRouter

from .views import DeviceViewSet, FileRecordViewSet, FolderViewSet, ReviewRequestViewSet

router = DefaultRouter()
router.register("devices", DeviceViewSet, basename="device")
router.register("folders", FolderViewSet, basename="folder")
router.register("files", FileRecordViewSet, basename="file")
router.register("reviews", ReviewRequestViewSet, basename="review")
