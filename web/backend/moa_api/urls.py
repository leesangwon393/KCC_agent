from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

from library.urls import router
from library import agent_api


def health(_request):
    return JsonResponse({"status": "ok", "service": "moa-api", "version": "0.1.0"})


urlpatterns = [
    path("api/v1/health/", health, name="health"),
    path("api/v1/auth/session/", agent_api.session),
    path("api/v1/auth/login/", agent_api.sign_in),
    path("api/v1/auth/logout/", agent_api.sign_out),
    path("api/v1/agent/status/", agent_api.agent_status),
    path("api/v1/agent/commands/", agent_api.queue_command),
    path("api/v1/agent/bridge/poll/", agent_api.bridge_poll),
    path("api/v1/agent/bridge/result/", agent_api.bridge_result),
    path("api/v1/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
