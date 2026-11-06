from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

from library.urls import router


def health(_request):
    return JsonResponse({"status": "ok", "service": "moa-api", "version": "0.1.0"})


urlpatterns = [
    path("api/v1/health/", health, name="health"),
    path("api/v1/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
