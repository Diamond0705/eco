from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from apps.core.permissions import manager_required
from apps.trips.models import Trip

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


@manager_required
@require_GET
def trip_waybill(request, pk):
    trip = get_object_or_404(_manager_trips_queryset(request), pk=pk)
    pdf_bytes = WaybillPdfService().build(trip)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="waybill_trip_{trip.pk}.pdf"'
    return response


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


@manager_required
@require_GET
def emissions_report_pdf(request):
    service = EmissionsReportService()
    filters = service.parse_filters(request.GET)
    report = service.build(request.user, filters)
    pdf_bytes = EmissionsReportPdfService().build(request.user, report)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="emissions_report.pdf"'
    return response


@manager_required
@require_GET
def emissions_report_xlsx(request):
    service = EmissionsReportService()
    filters = service.parse_filters(request.GET)
    report = service.build(request.user, filters)
    xlsx_bytes = TripExcelExportService().build_emissions_report(request.user, report)
    return build_xlsx_response(xlsx_bytes, "emissions_report.xlsx")


@manager_required
@require_GET
def trips_xlsx(request):
    trips = _manager_trips_queryset(request)
    selected_status = request.GET.get("status", "")
    valid_statuses = {choice.value for choice in Trip.Status}
    if selected_status in valid_statuses:
        trips = trips.filter(status=selected_status)
    xlsx_bytes = TripExcelExportService().build_trips_export(list(trips.order_by("-created_at")))
    return build_xlsx_response(xlsx_bytes, "trips_export.xlsx")
