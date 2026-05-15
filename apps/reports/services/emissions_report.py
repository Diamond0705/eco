from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO

from django.utils import timezone
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from apps.trips.models import Trip

from .pdf_fonts import register_pdf_font
from .pdf_layout import (
    LEFT,
    draw_footer,
    draw_header,
    draw_key_value_table,
    draw_section_title,
    draw_simple_table,
    ensure_space,
)


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
        buffer = BytesIO()
        page_size = landscape(A4)
        pdf = canvas.Canvas(buffer, pagesize=page_size)
        font_name = register_pdf_font()
        width, height = page_size
        title = "Отчет по выбросам"

        filters = report["filters"]
        period = self._period_label(filters)
        manager_name = manager.get_full_name() or manager.username

        pdf.setTitle(title)
        y = draw_header(pdf, width, height, font_name, title)
        y = draw_section_title(pdf, "Период и менеджер", LEFT, y, font_name)
        y = draw_key_value_table(
            pdf,
            LEFT,
            y,
            width - 30 * mm,
            [
                ("Менеджер", manager_name),
                ("Период", period),
                ("Сформировано", timezone.localtime().strftime("%d.%m.%Y %H:%M")),
            ],
            font_name,
            label_width=35 * mm,
        )

        summary = report["summary"]
        y = draw_section_title(pdf, "Итоговые показатели", LEFT, y, font_name)
        y = draw_key_value_table(
            pdf,
            LEFT,
            y,
            width - 30 * mm,
            [
                ("Рейсы", summary["trips_count"]),
                ("Расстояние, км", summary["distance_km"]),
                ("Топливо, л", summary["fuel_liters"]),
                ("Стоимость, руб", summary["cost_rub"]),
                ("CO2, кг", summary["co2_kg"]),
                ("NOx, г", summary["nox_g"]),
                ("PM, г", summary["pm_g"]),
            ],
            font_name,
            label_width=35 * mm,
        )

        y = ensure_space(pdf, y, width, height, font_name, title, 30 * mm)
        y = draw_section_title(pdf, "Таблица рейсов", LEFT, y, font_name)
        headers = [
            "Рейс",
            "Дата",
            "Груз",
            "Транспорт",
            "Маршрут",
            "км",
            "л",
            "руб.",
            "CO2",
            "Рейтинг",
        ]
        column_widths = [13, 24, 34, 38, 30, 18, 18, 24, 20, 20]
        widths = [value * mm for value in column_widths]
        table_rows = [self._pdf_row(row) for row in report["rows"]]

        if not table_rows:
            y = draw_key_value_table(
                pdf,
                LEFT,
                y,
                width - 30 * mm,
                [("Состояние", "Доставленных рейсов за выбранный период нет.")],
                font_name,
                label_width=35 * mm,
            )
        else:
            for index in range(0, len(table_rows), 18):
                chunk = table_rows[index : index + 18]
                required_height = (len(chunk) + 2) * 7 * mm
                y = ensure_space(pdf, y, width, height, font_name, title, required_height)
                y = draw_simple_table(pdf, LEFT, y, widths, headers, chunk, font_name)

        draw_footer(pdf, width, font_name)
        pdf.showPage()
        pdf.save()
        return buffer.getvalue()

    def _pdf_row(self, row):
        return [
            f"№{row['trip'].pk}",
            timezone.localtime(row["finish_date"]).strftime("%d.%m.%Y"),
            str(row["cargo"])[:20],
            str(row["transport"])[:22],
            str(row["route_name"])[:16],
            row["distance_km"],
            row["fuel_liters"],
            row["cost_rub"],
            row["co2_kg"],
            row["eco_rating"],
        ]

    def _period_label(self, filters):
        if filters.date_from and filters.date_to:
            return f"{filters.date_from:%d.%m.%Y} - {filters.date_to:%d.%m.%Y}"
        if filters.date_from:
            return f"с {filters.date_from:%d.%m.%Y}"
        if filters.date_to:
            return f"по {filters.date_to:%d.%m.%Y}"
        return "весь период"
