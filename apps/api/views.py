from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.services import ManagerAnalyticsService
from apps.fleet.models import Transport
from apps.locations.models import Location
from apps.orders.models import ShipmentOrder
from apps.reports.services.emissions_report import EmissionsReportService
from apps.routing.models import RouteOption
from apps.routing.services.provider_factory import EXTENDED_MODE, STANDARD_MODE
from apps.routing.services.route_calculation_service import RouteCalculationService
from apps.trips.models import Trip
from apps.trips.services import TripLifecycleService

from .serializers import (
    AnalyticsSummarySerializer,
    CurrentUserSerializer,
    EmissionsReportSerializer,
    LocationSerializer,
    ManagerDashboardSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    RouteOptionDetailSerializer,
    ShipmentOrderWriteSerializer,
    TransportSummarySerializer,
    TripDeliverSerializer,
    TripDetailSerializer,
    TripSerializer,
    TripStartSerializer,
    build_analytics_summary,
)


def is_admin_user(user):
    return user.is_superuser or getattr(user, "role", "") == "admin"


def is_manager_user(user):
    return getattr(user, "role", "") == "manager"


def manager_order_queryset(user):
    return (
        ShipmentOrder.objects.filter(manager=user)
        .select_related("manager", "transport", "transport__eco_standard", "trip")
        .prefetch_related("points__location", "route_options")
    )


def manager_trip_queryset(user):
    return (
        Trip.objects.filter(order__manager=user)
        .select_related(
            "order",
            "order__manager",
            "order__transport",
            "order__transport__eco_standard",
            "route_option",
            "route_option__calculation_settings",
        )
        .prefetch_related("order__points__location", "status_events__changed_by")
    )


def can_cancel_order(order):
    return (
        order.status in {ShipmentOrder.Status.NEW, ShipmentOrder.Status.CALCULATED}
        and not hasattr(order, "trip")
    )


def manager_only(request):
    if not is_manager_user(request.user):
        return Response(
            {"detail": "Действие доступно только менеджеру."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


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

    @extend_schema(request=ShipmentOrderWriteSerializer, responses=OrderDetailSerializer)
    def post(self, request):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        serializer = ShipmentOrderWriteSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        response_serializer = OrderDetailSerializer(
            self.get_queryset().get(pk=order.pk),
            context={"request": request},
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailAPIView(OrderQuerysetMixin, RetrieveAPIView):
    serializer_class = OrderDetailSerializer

    @extend_schema(request=ShipmentOrderWriteSerializer, responses=OrderDetailSerializer)
    def patch(self, request, pk):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        order = get_object_or_404(manager_order_queryset(request.user), pk=pk)
        serializer = ShipmentOrderWriteSerializer(
            order,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        response_serializer = OrderDetailSerializer(
            manager_order_queryset(request.user).get(pk=order.pk),
            context={"request": request},
        )
        return Response(response_serializer.data)


class OrderCancelAPIView(APIView):
    @extend_schema(responses=OrderDetailSerializer)
    def post(self, request, pk):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        order = get_object_or_404(manager_order_queryset(request.user), pk=pk)
        if not can_cancel_order(order):
            return Response(
                {"detail": "Заявку нельзя отменить в текущем состоянии."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = ShipmentOrder.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        serializer = OrderDetailSerializer(
            manager_order_queryset(request.user).get(pk=order.pk),
            context={"request": request},
        )
        return Response(serializer.data)


class OrderCalculateRoutesAPIView(APIView):
    @extend_schema(responses=OrderDetailSerializer)
    def post(self, request, pk):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        order = get_object_or_404(manager_order_queryset(request.user), pk=pk)
        calculation_mode = request.data.get("route_calculation_mode", STANDARD_MODE)
        if calculation_mode not in {STANDARD_MODE, EXTENDED_MODE}:
            calculation_mode = STANDARD_MODE
        service = RouteCalculationService(calculation_mode=calculation_mode)
        try:
            route_options = service.calculate_for_order(order)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        order = manager_order_queryset(request.user).get(pk=order.pk)
        serializer = OrderDetailSerializer(order, context={"request": request})
        return Response(
            {
                "order": serializer.data,
                "route_options_count": len(route_options),
                "warning": service.last_warning,
                "diagnostics": {
                    "requested_count": service.last_requested_count,
                    "found_count": service.last_found_count,
                    "provider": service.last_used_provider,
                },
            }
        )


class OrderRouteCalculationStatusAPIView(APIView):
    def get(self, request, pk):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        order = get_object_or_404(manager_order_queryset(request.user), pk=pk)
        route_options_count = order.route_options.count()
        calculation_status = "completed" if route_options_count else "not_started"
        return Response(
            {
                "status": calculation_status,
                "order_status": order.status,
                "route_options_count": route_options_count,
            }
        )


class OrderRouteOptionsAPIView(APIView):
    @extend_schema(responses=RouteOptionDetailSerializer(many=True))
    def get(self, request, pk):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        order = get_object_or_404(manager_order_queryset(request.user), pk=pk)
        route_options = order.route_options.all().order_by("created_at")
        serializer = RouteOptionDetailSerializer(
            route_options,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class ApproveRouteAPIView(APIView):
    @extend_schema(responses=TripDetailSerializer)
    def post(self, request, order_pk, route_option_pk):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        order = get_object_or_404(manager_order_queryset(request.user), pk=order_pk)
        route_option = get_object_or_404(
            RouteOption.objects.filter(order=order),
            pk=route_option_pk,
        )
        try:
            trip = TripLifecycleService().approve_route(order, route_option, request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = TripDetailSerializer(
            manager_trip_queryset(request.user).get(pk=trip.pk),
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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


class TripDetailAPIView(RetrieveAPIView):
    serializer_class = TripDetailSerializer

    def get_queryset(self):
        if is_admin_user(self.request.user):
            return (
                Trip.objects.select_related(
                    "order",
                    "order__manager",
                    "order__transport",
                    "order__transport__eco_standard",
                    "route_option",
                )
                .prefetch_related("order__points__location", "status_events__changed_by")
                .order_by("-created_at")
            )
        return manager_trip_queryset(self.request.user)


class TripStartAPIView(APIView):
    @extend_schema(request=TripStartSerializer, responses=TripDetailSerializer)
    def post(self, request, pk):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        trip = get_object_or_404(manager_trip_queryset(request.user), pk=pk)
        serializer = TripStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            trip = TripLifecycleService().start_trip(
                trip,
                request.user,
                actual_start_at=serializer.validated_data.get("actual_start"),
                comment=serializer.validated_data.get("comment", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        response_serializer = TripDetailSerializer(
            manager_trip_queryset(request.user).get(pk=trip.pk),
            context={"request": request},
        )
        return Response(response_serializer.data)


class TripDeliverAPIView(APIView):
    @extend_schema(request=TripDeliverSerializer, responses=TripDetailSerializer)
    def post(self, request, pk):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        trip = get_object_or_404(manager_trip_queryset(request.user), pk=pk)
        serializer = TripDeliverSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            trip = TripLifecycleService().deliver_trip(
                trip,
                request.user,
                actual_finish_at=serializer.validated_data.get("actual_finish"),
                comment=serializer.validated_data.get("comment", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        response_serializer = TripDetailSerializer(
            manager_trip_queryset(request.user).get(pk=trip.pk),
            context={"request": request},
        )
        return Response(response_serializer.data)


class AnalyticsSummaryAPIView(APIView):
    @extend_schema(responses=AnalyticsSummarySerializer)
    def get(self, request):
        trips = Trip.objects.filter(status=Trip.Status.DELIVERED).select_related("route_option")
        if not is_admin_user(request.user):
            trips = trips.filter(order__manager=request.user)
        summary = build_analytics_summary(trips)
        return Response(AnalyticsSummarySerializer(summary).data)


class CurrentUserAPIView(APIView):
    @extend_schema(responses=CurrentUserSerializer)
    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class ManagerDashboardAPIView(APIView):
    @extend_schema(responses=ManagerDashboardSerializer)
    def get(self, request):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        analytics = ManagerAnalyticsService().build(request.user)
        serializer = ManagerDashboardSerializer(analytics, context={"request": request})
        return Response(serializer.data)


class EmissionsReportAPIView(APIView):
    @extend_schema(responses=EmissionsReportSerializer)
    def get(self, request):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        service = EmissionsReportService()
        filters = service.parse_filters(request.query_params)
        report = service.build(request.user, filters)
        payload = {
            "filters": {
                "date_from": filters.date_from.isoformat() if filters.date_from else None,
                "date_to": filters.date_to.isoformat() if filters.date_to else None,
                "error_message": filters.error_message,
            },
            "summary": report["summary"],
            "rows": report["rows"],
        }
        serializer = EmissionsReportSerializer(payload, context={"request": request})
        return Response(serializer.data)
