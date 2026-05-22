from django.utils.dateparse import parse_date
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.fleet.models import Transport
from apps.locations.models import Location
from apps.orders.models import ShipmentOrder
from apps.trips.models import Trip

from .serializers import (
    AnalyticsSummarySerializer,
    LocationSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    TransportSummarySerializer,
    TripSerializer,
    build_analytics_summary,
)


def is_admin_user(user):
    return user.is_superuser or getattr(user, "role", "") == "admin"


class LocationListAPIView(ListAPIView):
    serializer_class = LocationSerializer

    def get_queryset(self):
        return Location.objects.filter(is_active=True).order_by("name")


class TransportListAPIView(ListAPIView):
    serializer_class = TransportSummarySerializer

    def get_queryset(self):
        return Transport.objects.filter(is_active=True).select_related("eco_standard")


class OrderQuerysetMixin:
    def get_queryset(self):
        queryset = (
            ShipmentOrder.objects.select_related("manager", "transport", "transport__eco_standard")
            .prefetch_related("points__location", "route_options")
            .order_by("-created_at")
        )
        if is_admin_user(self.request.user):
            return queryset
        return queryset.filter(manager=self.request.user)


class OrderListAPIView(OrderQuerysetMixin, ListAPIView):
    serializer_class = OrderListSerializer


class OrderDetailAPIView(OrderQuerysetMixin, RetrieveAPIView):
    serializer_class = OrderDetailSerializer


class TripListAPIView(ListAPIView):
    serializer_class = TripSerializer

    def get_queryset(self):
        queryset = (
            Trip.objects.select_related(
                "order",
                "order__manager",
                "order__transport",
                "order__transport__eco_standard",
                "route_option",
            )
            .prefetch_related("order__points__location")
            .order_by("-created_at")
        )
        if not is_admin_user(self.request.user):
            queryset = queryset.filter(order__manager=self.request.user)

        status = self.request.query_params.get("status", "").strip()
        if status:
            queryset = queryset.filter(status=status)

        date_from = parse_date(self.request.query_params.get("date_from", "").strip())
        date_to = parse_date(self.request.query_params.get("date_to", "").strip())
        if date_from:
            queryset = queryset.filter(actual_finish_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(actual_finish_at__date__lte=date_to)
        return queryset


class AnalyticsSummaryAPIView(APIView):
    def get(self, request):
        trips = Trip.objects.filter(status=Trip.Status.DELIVERED).select_related("route_option")
        if not is_admin_user(request.user):
            trips = trips.filter(order__manager=request.user)
        summary = build_analytics_summary(trips)
        return Response(AnalyticsSummarySerializer(summary).data)
