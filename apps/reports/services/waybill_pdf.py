from io import BytesIO

from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from apps.routing.services.route_snapshot_metrics import (
    TOLL_WITHOUT_COST_NOTICE,
    average_speed_kmh,
    calculation_model_version,
    co2_kg_per_km,
    co2_kg_per_ton_km,
    display_decimal,
    final_fuel_multiplier,
    has_unpriced_tolls,
)

from .pdf_fonts import register_pdf_font
from .pdf_layout import (
    LEFT,
    draw_footer,
    draw_header,
    draw_key_value_table,
    draw_section_title,
    draw_title,
    ensure_space,
    key_value_table_height,
)


class WaybillPdfService:
    def build(self, trip):
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        font_name = register_pdf_font()
        width, height = A4
        document_title = f"Путевой лист рейса №{trip.pk}"

        pdf.setTitle(document_title)
        y = draw_header(pdf, width, height, font_name, document_title)
        y = draw_title(pdf, "Путевой лист", LEFT, y, font_name)

        order = trip.order
        route = trip.route_option
        transport = order.transport
        standard = transport.eco_standard
        manager_name = order.manager.get_full_name() or order.manager.username
        points = order.points.select_related("location").order_by("sequence")

        sections = [
            (
                "Основная информация",
                [
                    ("Рейс", f"№{trip.pk}"),
                    ("Заявка", f"№{order.pk}"),
                    ("Менеджер", manager_name),
                    ("Статус рейса", trip.get_status_display()),
                    (
                        "Фактическое начало",
                        self._datetime_label(trip.actual_start_at),
                    ),
                    (
                        "Фактическое завершение",
                        self._datetime_label(trip.actual_finish_at),
                    ),
                    ("Сформировано", timezone.localtime().strftime("%d.%m.%Y %H:%M")),
                ],
            ),
            (
                "Груз и транспорт",
                [
                    ("Груз", order.cargo_name),
                    ("Тип груза", order.cargo_type),
                    ("Вес груза, кг", order.cargo_weight_kg),
                    ("Транспорт", f"{transport.plate_number}, {transport.model}"),
                    ("Евро-класс", standard.name),
                ],
            ),
            (
                "Маршрут",
                [
                    ("Маршрут", route.name),
                    ("Точки", " → ".join(point.location.name for point in points)),
                    ("Расстояние, км", route.distance_km),
                    ("Время, мин", route.duration_minutes),
                    ("Топливо, л", route.fuel_liters),
                    ("Стоимость, руб", route.cost_rub),
                ],
            ),
            (
                "Экологические показатели",
                [
                    ("CO2, кг", route.co2_kg),
                    ("NOx, г", route.nox_g),
                    ("PM, г", route.pm_g),
                    ("Эко-рейтинг", route.eco_rating),
                ],
            ),
            (
                "Краткий расчет",
                [
                    ("Модель расчета", calculation_model_version(route)),
                    (
                        "Итоговый множитель расхода",
                        display_decimal(final_fuel_multiplier(route), "0.01"),
                    ),
                    ("Средняя скорость, км/ч", display_decimal(average_speed_kmh(route), "0.01")),
                    ("Эко-рейтинг", route.eco_rating),
                    ("CO2, кг/км", display_decimal(co2_kg_per_km(route), "0.001")),
                    ("CO2, кг/тонно-км", display_decimal(co2_kg_per_ton_km(route), "0.0001")),
                ],
            ),
        ]

        if has_unpriced_tolls(route):
            sections.append(
                ("Особенности маршрута", [("Платные участки", TOLL_WITHOUT_COST_NOTICE)])
            )

        for section_title, rows in sections:
            y = ensure_space(
                pdf,
                y,
                width,
                height,
                font_name,
                document_title,
                self._section_height(rows, pdf, width - 30 * mm, font_name),
            )
            y = draw_section_title(pdf, section_title, LEFT, y, font_name)
            y = draw_key_value_table(pdf, LEFT, y, width - 30 * mm, rows, font_name)

        draw_footer(pdf, width, font_name)
        pdf.showPage()
        pdf.save()
        return buffer.getvalue()

    def _datetime_label(self, value):
        if not value:
            return "-"
        return timezone.localtime(value).strftime("%d.%m.%Y %H:%M")

    def _section_height(self, rows, pdf=None, table_width=None, font_name=None):
        if pdf is None or table_width is None or font_name is None:
            return (len(rows) * 7 + 11) * mm
        return key_value_table_height(pdf, table_width, rows, font_name) + 11 * mm
