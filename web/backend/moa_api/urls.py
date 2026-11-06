from pathlib import Path

from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

from library.urls import router
from library import agent_api, local_setup, apple_auth, pairing, accounts, onboarding


def health(_request):
    return JsonResponse({"status": "ok", "service": "moa-api", "version": "0.1.0"})


urlpatterns = [
    path("api/v1/onboarding/", onboarding.progress),
    path("api/v1/auth/config/", apple_auth.config),
    path("api/v1/auth/apple/start/", apple_auth.start),
    path("api/v1/auth/apple/callback/", apple_auth.callback),
    path("api/v1/agent/pairing/", pairing.create),
    path("api/v1/agent/pairing/consume/", pairing.consume),
    path("api/v1/agent/pairing/disconnect/", pairing.disconnect),
    path("api/v1/local/cloud/connect/", local_setup.connect_cloud),
    path("api/v1/local/cloud/disconnect/", local_setup.disconnect_cloud),
    path("api/v1/local/unlock/", local_setup.unlock),
    path("api/v1/local/setup/", local_setup.setup),
    path("api/v1/health/", health, name="health"),
    path("api/v1/auth/session/", agent_api.session),
    path("api/v1/auth/login/", agent_api.sign_in),
    path("api/v1/auth/signup/", accounts.sign_up),
    path("api/v1/auth/logout/", agent_api.sign_out),
    path("api/v1/agent/status/", agent_api.agent_status),
    path("api/v1/agent/commands/", agent_api.queue_command),
    path("api/v1/agent/bridge/poll/", agent_api.bridge_poll),
    path("api/v1/agent/bridge/result/", agent_api.bridge_result),
    path("api/v1/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]


if settings.DEBUG:
    # Serve the checked-in web build from the same origin as the local API.
    dist = Path(__file__).resolve().parents[2] / "dist"

    def local_index(_request):
        return FileResponse((dist / "index.html").open("rb"), content_type="text/html")

    urlpatterns += [
        path("", local_index),
        re_path(r"^(?P<path>[^/]+)$", serve, {"document_root": dist}),
    ]
