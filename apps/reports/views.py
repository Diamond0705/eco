from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.core.permissions import is_admin, is_manager, manager_required
from apps.trips.models import Trip

from .models import ArchivedDocument
from .services.document_archive import DocumentArchiveDisabledError, DocumentArchiveService
from .services.emissions_report import EmissionsReportPdfService, EmissionsReportService
from .services.excel_export import TripExcelExportService, build_xlsx_response
from .services.waybill_pdf import WaybillPdfService


def _manager_trips_queryset(request):
    return (
        Trip.objects.filter(order__manager=request.user)
        .select_related(
            "order",
            "order__manager",
            "order__transport",
            "order__transport__eco_standard",
            "route_option",
        )
        .prefetch_related("order__points__location")
    )


def _archive_queryset_for_user(user):
    queryset = ArchivedDocument.objects.select_related(
        "owner",
        "created_by",
        "related_order",
        "related_trip",
    )
    if is_admin(user):
        return queryset
    if is_manager(user):
        return queryset.filter(owner=user)
    raise PermissionDenied


def _emissions_report_from_request(request):
    service = EmissionsReportService()
    filters = service.parse_filters(request.GET if request.method == "GET" else request.POST)
    report = service.build(request.user, filters)
    return filters, report


def _trips_for_export(request):
    trips = _manager_trips_queryset(request)
    selected_status = (request.GET if request.method == "GET" else request.POST).get("status", "")
    valid_statuses = {choice.value for choice in Trip.Status}
    if selected_status in valid_statuses:
        trips = trips.filter(status=selected_status)
    return selected_status, list(trips.order_by("-created_at"))


def _archive_success(request, document):
    messages.success(request, f"Документ «{document.title}» сохранен в архив.")


def _archive_disabled(request):
    messages.error(request, "Архив документов временно отключен.")


@manager_required
@require_GET
def trip_waybill(request, pk):
    trip = get_object_or_404(_manager_trips_queryset(request), pk=pk)
    pdf_bytes = WaybillPdfService().build(trip)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="waybill_trip_{trip.pk}.pdf"'
    return response


@manager_required
@require_POST
def trip_waybill_archive(request, pk):
    trip = get_object_or_404(_manager_trips_queryset(request), pk=pk)
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
                "source": "waybill",
            },
        )
    except DocumentArchiveDisabledError:
        _archive_disabled(request)
    else:
        _archive_success(request, document)
    return redirect("trips:detail", pk=trip.pk)


@manager_required
@require_GET
def emissions_report(request):
    service = EmissionsReportService()
    filters = service.parse_filters(request.GET)
    report = service.build(request.user, filters)
    return render(
        request,
        "reports/emissions_report.html",
        {
            "report": report,
            "filters": filters,
            "date_from": request.GET.get("date_from", ""),
            "date_to": request.GET.get("date_to", ""),
        },
    )


@login_required
@require_GET
def archive(request):
    documents = _archive_queryset_for_user(request.user).order_by("-created_at")
    return render(request, "reports/archive.html", {"documents": documents})


@login_required
@require_GET
def archive_download(request, pk):
    document = get_object_or_404(_archive_queryset_for_user(request.user), pk=pk)
    service = DocumentArchiveService()
    response = FileResponse(
        document.file.open("rb"),
        as_attachment=True,
        filename=service.download_filename(document),
        content_type=service.content_type_for(document),
    )
    response["Content-Length"] = str(document.file_size_bytes)
    return response


@login_required
@require_POST
def archive_delete(request, pk):
    document = get_object_or_404(_archive_queryset_for_user(request.user), pk=pk)
    title = document.title
    document.file.delete(save=False)
    document.delete()
    messages.success(request, f"Документ «{title}» удален из архива.")
    return redirect("reports:archive")


@manager_required
@require_GET
def emissions_report_pdf(request):
    _filters, report = _emissions_report_from_request(request)
    pdf_bytes = EmissionsReportPdfService().build(request.user, report)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="emissions_report.pdf"'
    return response


@manager_required
@require_POST
def emissions_report_pdf_archive(request):
    filters, report = _emissions_report_from_request(request)
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
                "source": "emissions_report",
                "trips_count": report["summary"]["trips_count"],
            },
        )
    except DocumentArchiveDisabledError:
        _archive_disabled(request)
    else:
        _archive_success(request, document)
    return redirect("reports:archive")


@manager_required
@require_GET
def emissions_report_xlsx(request):
    _filters, report = _emissions_report_from_request(request)
    xlsx_bytes = TripExcelExportService().build_emissions_report(request.user, report)
    return build_xlsx_response(xlsx_bytes, "emissions_report.xlsx")


@manager_required
@require_POST
def emissions_report_xlsx_archive(request):
    filters, report = _emissions_report_from_request(request)
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
                "source": "emissions_report",
                "trips_count": report["summary"]["trips_count"],
            },
        )
    except DocumentArchiveDisabledError:
        _archive_disabled(request)
    else:
        _archive_success(request, document)
    return redirect("reports:archive")


@manager_required
@require_GET
def trips_xlsx(request):
    _selected_status, trips = _trips_for_export(request)
    xlsx_bytes = TripExcelExportService().build_trips_export(trips)
    return build_xlsx_response(xlsx_bytes, "trips_export.xlsx")


@manager_required
@require_POST
def trips_xlsx_archive(request):
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
                "source": "trips_export",
                "status": selected_status,
                "trips_count": len(trips),
            },
        )
    except DocumentArchiveDisabledError:
        _archive_disabled(request)
    else:
        _archive_success(request, document)
    return redirect("reports:archive")
