from django.urls import path

from .views import (
    AnalyticsSummaryAPIView,
    LocationListAPIView,
    OrderDetailAPIView,
    OrderListAPIView,
    TransportListAPIView,
    TripListAPIView,
)

app_name = "api"

urlpatterns = [
    path("locations/", LocationListAPIView.as_view(), name="locations"),
    path("transports/", TransportListAPIView.as_view(), name="transports"),
    path("orders/", OrderListAPIView.as_view(), name="orders"),
    path("orders/<int:pk>/", OrderDetailAPIView.as_view(), name="order_detail"),
    path("trips/", TripListAPIView.as_view(), name="trips"),
    path("analytics/summary/", AnalyticsSummaryAPIView.as_view(), name="analytics_summary"),
]
