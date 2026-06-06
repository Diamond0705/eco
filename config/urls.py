from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.views import healthz
from apps.dashboard.views import home

urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("", home, name="home"),
    path("", include("apps.accounts.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/", include("apps.api.urls")),
    path("", include("apps.dashboard.urls")),
    path("", include("apps.orders.urls")),
    path("", include("apps.routing.urls")),
    path("", include("apps.trips.urls")),
    path("", include("apps.reports.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
