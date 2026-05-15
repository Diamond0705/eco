from dataclasses import dataclass
from decimal import Decimal

from django.utils import timezone

from apps.trips.models import Trip


@dataclass(frozen=True)
class ReportFilters:
    date_from: object = None
    date_to: object = None
    error_message: str = ""


class EmissionsReportService:
    def parse_filters(self, query_params):
        date_from_raw = query_params.get("date_from", "").strip()
        date_to_raw = query_params.get("date_to", "").strip()
        error_message = ""
        date_from = None
        date_to = None

        if date_from_raw:
            try:
                date_from = timezone.datetime.fromisoformat(date_from_raw).date()
            except ValueError:
                error_message = "Некорректная дата начала периода."
        if date_to_raw:
            try:
                date_to = timezone.datetime.fromisoformat(date_to_raw).date()
            except ValueError:
                error_message = "Некорректная дата окончания периода."

        return ReportFilters(date_from=date_from, date_to=date_to, error_message=error_message)

    def build(self, manager, filters=None):
        filters = filters or ReportFilters()
        trips = (
            Trip.objects.filter(order__manager=manager, status=Trip.Status.DELIVERED)
            .select_related("order", "order__transport", "route_option")
            .order_by("-actual_finish_at", "-created_at")
        )
        if filters.date_from:
            trips = trips.filter(actual_finish_at__date__gte=filters.date_from)
        if filters.date_to:
            trips = trips.filter(actual_finish_at__date__lte=filters.date_to)

        rows = [self._row_for_trip(trip) for trip in trips]
        summary = {
            "trips_count": len(rows),
            "distance_km": sum((row["distance_km"] for row in rows), Decimal("0.00")),
            "fuel_liters": sum((row["fuel_liters"] for row in rows), Decimal("0.00")),
            "cost_rub": sum((row["cost_rub"] for row in rows), Decimal("0.00")),
            "co2_kg": sum((row["co2_kg"] for row in rows), Decimal("0.00")),
            "nox_g": sum((row["nox_g"] for row in rows), Decimal("0.00")),
            "pm_g": sum((row["pm_g"] for row in rows), Decimal("0.000")),
        }
        return {"filters": filters, "summary": summary, "rows": rows}

    def _row_for_trip(self, trip):
        route = trip.route_option
        return {
            "trip": trip,
            "finish_date": trip.actual_finish_at,
            "cargo": trip.order.cargo_name,
            "transport": trip.order.transport,
            "route_name": route.name,
            "distance_km": route.distance_km,
            "fuel_liters": route.fuel_liters,
            "cost_rub": route.cost_rub,
            "co2_kg": route.co2_kg,
            "nox_g": route.nox_g,
            "pm_g": route.pm_g,
            "eco_rating": route.eco_rating,
        }


class EmissionsReportPdfService:
    def build(self, manager, report):
        from io import BytesIO

        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas

        from .pdf_fonts import register_pdf_font

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
        font_name = register_pdf_font()
        width, height = landscape(A4)
        y = height - 15 * mm

        def text(value, x, current_y, size=8):
            pdf.setFont(font_name, size)
            pdf.drawString(x, current_y, str(value))

        filters = report["filters"]
        period = self._period_label(filters)
        pdf.setTitle("Отчет по выбросам")
        text("Отчет по выбросам", 15 * mm, y, 14)
        y -= 9 * mm
        text(f"Менеджер: {manager.get_full_name() or manager.username}", 15 * mm, y)
        y -= 6 * mm
        text(f"Период: {period}", 15 * mm, y)
        y -= 6 * mm
        text(f"Сформировано: {timezone.localtime().strftime('%d.%m.%Y %H:%M')}", 15 * mm, y)
        y -= 9 * mm

        summary = report["summary"]
        text(
            "Итого: рейсов {trips_count}, расстояние {distance_km} км, топливо "
            "{fuel_liters} л, стоимость {cost_rub} руб., CO2 {co2_kg} кг, "
            "NOx {nox_g} г, PM {pm_g} г".format(**summary),
            15 * mm,
            y,
        )
        y -= 10 * mm

        headers = ["Рейс", "Дата", "Груз", "Транспорт", "Маршрут", "км", "л", "руб.", "CO2"]
        x_positions = [15, 28, 52, 88, 124, 158, 174, 190, 215]
        for header, x in zip(headers, x_positions, strict=True):
            text(header, x * mm, y)
        y -= 6 * mm

        for row in report["rows"]:
            if y < 15 * mm:
                pdf.showPage()
                y = height - 15 * mm
            values = [
                f"№{row['trip'].pk}",
                timezone.localtime(row["finish_date"]).strftime("%d.%m.%Y"),
                row["cargo"][:18],
                str(row["transport"])[:18],
                row["route_name"][:16],
                row["distance_km"],
                row["fuel_liters"],
                row["cost_rub"],
                row["co2_kg"],
            ]
            for value, x in zip(values, x_positions, strict=True):
                text(value, x * mm, y)
            y -= 6 * mm

        pdf.showPage()
        pdf.save()
        return buffer.getvalue()

    def _period_label(self, filters):
        if filters.date_from and filters.date_to:
            return f"{filters.date_from:%d.%m.%Y} - {filters.date_to:%d.%m.%Y}"
        if filters.date_from:
            return f"с {filters.date_from:%d.%m.%Y}"
        if filters.date_to:
            return f"по {filters.date_to:%d.%m.%Y}"
        return "весь период"
