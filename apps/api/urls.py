from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    AnalyticsSummaryAPIView,
    CurrentUserAPIView,
    LocationListAPIView,
    OrderDetailAPIView,
    OrderListAPIView,
    TransportListAPIView,
    TripListAPIView,
)

app_name = "api"

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/me/", CurrentUserAPIView.as_view(), name="auth_me"),
    path("locations/", LocationListAPIView.as_view(), name="locations"),
    path("transports/", TransportListAPIView.as_view(), name="transports"),
    path("orders/", OrderListAPIView.as_view(), name="orders"),
    path("orders/<int:pk>/", OrderDetailAPIView.as_view(), name="order_detail"),
    path("trips/", TripListAPIView.as_view(), name="trips"),
    path("analytics/summary/", AnalyticsSummaryAPIView.as_view(), name="analytics_summary"),
]
