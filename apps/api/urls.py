from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    AnalyticsSummaryAPIView,
    ApproveRouteAPIView,
    CurrentUserAPIView,
    EmissionsReportAPIView,
    LocationListAPIView,
    ManagerDashboardAPIView,
    OrderCalculateRoutesAPIView,
    OrderCancelAPIView,
    OrderDetailAPIView,
    OrderListAPIView,
    OrderRouteCalculationStatusAPIView,
    OrderRouteOptionsAPIView,
    TransportListAPIView,
    TripDeliverAPIView,
    TripDetailAPIView,
    TripListAPIView,
    TripStartAPIView,
)

app_name = "api"

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/me/", CurrentUserAPIView.as_view(), name="auth_me"),
    path("manager/dashboard/", ManagerDashboardAPIView.as_view(), name="manager_dashboard"),
    path("locations/", LocationListAPIView.as_view(), name="locations"),
    path("transports/", TransportListAPIView.as_view(), name="transports"),
    path("orders/", OrderListAPIView.as_view(), name="orders"),
    path("orders/<int:pk>/", OrderDetailAPIView.as_view(), name="order_detail"),
    path("orders/<int:pk>/cancel/", OrderCancelAPIView.as_view(), name="order_cancel"),
    path(
        "orders/<int:pk>/calculate-routes/",
        OrderCalculateRoutesAPIView.as_view(),
        name="order_calculate_routes",
    ),
    path(
        "orders/<int:pk>/route-calculation-status/",
        OrderRouteCalculationStatusAPIView.as_view(),
        name="order_route_calculation_status",
    ),
    path(
        "orders/<int:pk>/route-options/",
        OrderRouteOptionsAPIView.as_view(),
        name="order_route_options",
    ),
    path(
        "orders/<int:order_pk>/routes/<int:route_option_pk>/approve/",
        ApproveRouteAPIView.as_view(),
        name="approve_route",
    ),
    path("trips/", TripListAPIView.as_view(), name="trips"),
    path("trips/<int:pk>/", TripDetailAPIView.as_view(), name="trip_detail"),
    path("trips/<int:pk>/start/", TripStartAPIView.as_view(), name="trip_start"),
    path("trips/<int:pk>/deliver/", TripDeliverAPIView.as_view(), name="trip_deliver"),
    path("reports/emissions/", EmissionsReportAPIView.as_view(), name="emissions_report"),
    path("analytics/summary/", AnalyticsSummaryAPIView.as_view(), name="analytics_summary"),
]
