from django.db.models import Q
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.services import ManagerAnalyticsService
from apps.fleet.models import Transport
from apps.locations.models import Location
from apps.orders.models import ShipmentOrder
from apps.reports.models import ArchivedDocument
from apps.reports.services.document_archive import (
    DocumentArchiveDisabledError,
    DocumentArchiveService,
)
from apps.reports.services.emissions_report import EmissionsReportPdfService, EmissionsReportService
from apps.reports.services.excel_export import TripExcelExportService, build_xlsx_response
from apps.reports.services.waybill_pdf import WaybillPdfService
from apps.routing.models import RouteOption
from apps.routing.services.provider_factory import EXTENDED_MODE, STANDARD_MODE
from apps.routing.services.route_calculation_service import RouteCalculationService
from apps.trips.models import Trip
from apps.trips.services import TripLifecycleService

from .serializers import (
    AnalyticsSummarySerializer,
    ArchivedDocumentSerializer,
    ArchiveDocumentResponseSerializer,
    AvatarUploadSerializer,
    CurrentUserSerializer,
    EmissionsReportSerializer,
    LocationSerializer,
    ManagerDashboardSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    ProfileSerializer,
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


def archive_queryset_for_user(user):
    queryset = ArchivedDocument.objects.select_related(
        "owner",
        "created_by",
        "related_order",
        "related_trip",
    ).order_by("-created_at")
    if is_admin_user(user):
        return queryset
    if is_manager_user(user):
        return queryset.filter(owner=user)
    raise PermissionDenied("Архив документов доступен менеджерам и администраторам.")


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


def _avatar_content_type(name):
    name = name.lower()
    if name.endswith(".png"):
        return "image/png"
    if name.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


def _emissions_report_for_request(request):
    service = EmissionsReportService()
    source = request.query_params if request.method == "GET" else request.data
    filters = service.parse_filters(source)
    report = service.build(request.user, filters)
    return filters, report


def _emissions_report_payload(filters, report):
    return {
        "filters": {
            "date_from": filters.date_from.isoformat() if filters.date_from else None,
            "date_to": filters.date_to.isoformat() if filters.date_to else None,
            "error_message": filters.error_message,
        },
        "summary": report["summary"],
        "rows": report["rows"],
    }


def _trips_for_export(request):
    source = request.query_params if request.method == "GET" else request.data
    queryset = manager_trip_queryset(request.user)
    selected_status = source.get("status", "")
    valid_statuses = {choice.value for choice in Trip.Status}
    if selected_status in valid_statuses:
        queryset = queryset.filter(status=selected_status)
    else:
        selected_status = ""
    return selected_status, list(queryset.order_by("-created_at"))


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


class ProfileAPIView(APIView):
    @extend_schema(responses=ProfileSerializer)
    def get(self, request):
        return Response(ProfileSerializer(request.user).data)

    @extend_schema(request=ProfileSerializer, responses=ProfileSerializer)
    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProfileSerializer(request.user).data)


class ProfileAvatarAPIView(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(responses={(200, "image/*"): OpenApiTypes.BINARY})
    def get(self, request):
        if not request.user.avatar:
            return Response(
                {"detail": "Фото профиля не загружено."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            avatar_file = request.user.avatar.open("rb")
        except OSError:
            return Response(
                {"detail": "Фото профиля не найдено."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return FileResponse(
            avatar_file,
            content_type=_avatar_content_type(request.user.avatar.name),
        )

    @extend_schema(request=AvatarUploadSerializer, responses=ProfileSerializer)
    def post(self, request):
        serializer = AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_avatar_name = user.avatar.name
        user.avatar = serializer.validated_data["avatar"]
        user.save(update_fields=["avatar"])

        if old_avatar_name and old_avatar_name != user.avatar.name:
            user.avatar.storage.delete(old_avatar_name)

        return Response(ProfileSerializer(user).data)

    @extend_schema(responses={204: None})
    def delete(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = ""
            user.save(update_fields=["avatar"])
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        filters, report = _emissions_report_for_request(request)
        payload = _emissions_report_payload(filters, report)
        serializer = EmissionsReportSerializer(payload, context={"request": request})
        return Response(serializer.data)


class EmissionsReportPdfAPIView(APIView):
    @extend_schema(responses={(200, "application/pdf"): OpenApiTypes.BINARY})
    def get(self, request):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        _filters, report = _emissions_report_for_request(request)
        pdf_bytes = EmissionsReportPdfService().build(request.user, report)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="emissions_report.pdf"'
        return response


class EmissionsReportXlsxAPIView(APIView):
    @extend_schema(
        responses={
            (200, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"): (
                OpenApiTypes.BINARY
            )
        }
    )
    def get(self, request):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        _filters, report = _emissions_report_for_request(request)
        xlsx_bytes = TripExcelExportService().build_emissions_report(request.user, report)
        return build_xlsx_response(xlsx_bytes, "emissions_report.xlsx")


class EmissionsReportPdfArchiveAPIView(APIView):
    @extend_schema(responses={201: ArchiveDocumentResponseSerializer})
    def post(self, request):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        filters, report = _emissions_report_for_request(request)
        pdf_bytes = EmissionsReportPdfService().build(request.user, report)
        try:
            document = DocumentArchiveService().save_document(
                content_bytes=pdf_bytes,
                document_type=ArchivedDocument.DocumentType.EMISSIONS_PDF,
                file_format=ArchivedDocument.FileFormat.PDF,
                title="Отчет по выбросам PDF",
                owner=request.user,
                created_by=request.user,
                date_from=filters.date_from,
                date_to=filters.date_to,
                metadata={
                    "source": "emissions_report_api",
                    "trips_count": report["summary"]["trips_count"],
                },
            )
        except DocumentArchiveDisabledError:
            return Response(
                {"detail": "Архив документов временно отключен."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = ArchivedDocumentSerializer(document, context={"request": request})
        return Response({"document": serializer.data}, status=status.HTTP_201_CREATED)


class EmissionsReportXlsxArchiveAPIView(APIView):
    @extend_schema(responses={201: ArchiveDocumentResponseSerializer})
    def post(self, request):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        filters, report = _emissions_report_for_request(request)
        xlsx_bytes = TripExcelExportService().build_emissions_report(request.user, report)
        try:
            document = DocumentArchiveService().save_document(
                content_bytes=xlsx_bytes,
                document_type=ArchivedDocument.DocumentType.EMISSIONS_XLSX,
                file_format=ArchivedDocument.FileFormat.XLSX,
                title="Отчет по выбросам Excel",
                owner=request.user,
                created_by=request.user,
                date_from=filters.date_from,
                date_to=filters.date_to,
                metadata={
                    "source": "emissions_report_api",
                    "trips_count": report["summary"]["trips_count"],
                },
            )
        except DocumentArchiveDisabledError:
            return Response(
                {"detail": "Архив документов временно отключен."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = ArchivedDocumentSerializer(document, context={"request": request})
        return Response({"document": serializer.data}, status=status.HTTP_201_CREATED)


class TripExportXlsxAPIView(APIView):
    @extend_schema(
        responses={
            (200, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"): (
                OpenApiTypes.BINARY
            )
        }
    )
    def get(self, request):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        _selected_status, trips = _trips_for_export(request)
        xlsx_bytes = TripExcelExportService().build_trips_export(trips)
        return build_xlsx_response(xlsx_bytes, "trips_export.xlsx")


class TripExportXlsxArchiveAPIView(APIView):
    @extend_schema(responses={201: ArchiveDocumentResponseSerializer})
    def post(self, request):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        selected_status, trips = _trips_for_export(request)
        xlsx_bytes = TripExcelExportService().build_trips_export(trips)
        try:
            document = DocumentArchiveService().save_document(
                content_bytes=xlsx_bytes,
                document_type=ArchivedDocument.DocumentType.TRIPS_XLSX,
                file_format=ArchivedDocument.FileFormat.XLSX,
                title="Экспорт рейсов Excel",
                owner=request.user,
                created_by=request.user,
                metadata={
                    "source": "trips_export_api",
                    "status": selected_status,
                    "trips_count": len(trips),
                },
            )
        except DocumentArchiveDisabledError:
            return Response(
                {"detail": "Архив документов временно отключен."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = ArchivedDocumentSerializer(document, context={"request": request})
        return Response({"document": serializer.data}, status=status.HTTP_201_CREATED)


class TripWaybillAPIView(APIView):
    @extend_schema(responses={(200, "application/pdf"): OpenApiTypes.BINARY})
    def get(self, request, pk):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        trip = get_object_or_404(manager_trip_queryset(request.user), pk=pk)
        pdf_bytes = WaybillPdfService().build(trip)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="waybill_trip_{trip.pk}.pdf"'
        return response


class TripWaybillArchiveAPIView(APIView):
    @extend_schema(responses={201: ArchiveDocumentResponseSerializer})
    def post(self, request, pk):
        forbidden_response = manager_only(request)
        if forbidden_response:
            return forbidden_response
        trip = get_object_or_404(manager_trip_queryset(request.user), pk=pk)
        pdf_bytes = WaybillPdfService().build(trip)
        try:
            document = DocumentArchiveService().save_document(
                content_bytes=pdf_bytes,
                document_type=ArchivedDocument.DocumentType.WAYBILL_PDF,
                file_format=ArchivedDocument.FileFormat.PDF,
                title=f"Путевой лист рейса №{trip.pk}",
                owner=request.user,
                created_by=request.user,
                related_order=trip.order,
                related_trip=trip,
                metadata={
                    "trip_id": trip.pk,
                    "order_id": trip.order_id,
                    "source": "waybill_api",
                },
            )
        except DocumentArchiveDisabledError:
            return Response(
                {"detail": "Архив документов временно отключен."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = ArchivedDocumentSerializer(document, context={"request": request})
        return Response({"document": serializer.data}, status=status.HTTP_201_CREATED)


class ArchiveListAPIView(APIView):
    @extend_schema(responses=ArchivedDocumentSerializer(many=True))
    def get(self, request):
        documents = archive_queryset_for_user(request.user)
        valid_types = {choice.value for choice in ArchivedDocument.DocumentType}
        valid_formats = {choice.value for choice in ArchivedDocument.FileFormat}

        selected_type = request.query_params.get("document_type", "")
        if selected_type in valid_types:
            documents = documents.filter(document_type=selected_type)

        selected_format = request.query_params.get("file_format", "")
        if selected_format in valid_formats:
            documents = documents.filter(file_format=selected_format)

        date_from = parse_date(request.query_params.get("date_from", "").strip())
        if date_from:
            documents = documents.filter(created_at__date__gte=date_from)

        date_to = parse_date(request.query_params.get("date_to", "").strip())
        if date_to:
            documents = documents.filter(created_at__date__lte=date_to)

        search_query = request.query_params.get("q", "").strip()
        if search_query:
            documents = documents.filter(
                Q(title__icontains=search_query)
                | Q(owner__username__icontains=search_query)
                | Q(owner__first_name__icontains=search_query)
                | Q(owner__last_name__icontains=search_query)
                | Q(created_by__username__icontains=search_query)
                | Q(created_by__first_name__icontains=search_query)
                | Q(created_by__last_name__icontains=search_query)
            )

        serializer = ArchivedDocumentSerializer(
            documents,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class ArchiveDownloadAPIView(APIView):
    @extend_schema(responses={(200, "application/octet-stream"): OpenApiTypes.BINARY})
    def get(self, request, pk):
        document = get_object_or_404(archive_queryset_for_user(request.user), pk=pk)
        service = DocumentArchiveService()
        response = FileResponse(
            document.file.open("rb"),
            as_attachment=True,
            filename=service.download_filename(document),
            content_type=service.content_type_for(document),
        )
        response["Content-Length"] = str(document.file_size_bytes)
        return response


class ArchiveDeleteAPIView(APIView):
    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        document = get_object_or_404(archive_queryset_for_user(request.user), pk=pk)
        document.file.delete(save=False)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
