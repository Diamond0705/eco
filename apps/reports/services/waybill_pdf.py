from io import BytesIO

from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .pdf_fonts import register_pdf_font


class WaybillPdfService:
    def build(self, trip):
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        font_name = register_pdf_font()
        width, height = A4
        y = height - 20 * mm

        def line(label, value=""):
            nonlocal y
            if y < 25 * mm:
                pdf.showPage()
                pdf.setFont(font_name, 10)
                y = height - 20 * mm
            pdf.drawString(20 * mm, y, f"{label}: {value}")
            y -= 7 * mm

        pdf.setTitle(f"Путевой лист рейса {trip.pk}")
        pdf.setFont(font_name, 16)
        pdf.drawString(20 * mm, y, "Путевой лист")
        y -= 12 * mm
        pdf.setFont(font_name, 10)

        order = trip.order
        route = trip.route_option
        transport = order.transport
        standard = transport.eco_standard
        points = order.points.select_related("location").order_by("sequence")

        line("Рейс", f"№{trip.pk}")
        line("Заявка", f"№{order.pk}")
        line("Менеджер", order.manager.get_full_name() or order.manager.username)
        line("Груз", order.cargo_name)
        line("Тип груза", order.cargo_type)
        line("Вес груза, кг", order.cargo_weight_kg)
        line("Транспорт", f"{transport.plate_number}, {transport.model}")
        line("Экологический стандарт", standard.name)
        line("Маршрут", route.name)
        line("Расстояние, км", route.distance_km)
        line("Время, мин", route.duration_minutes)
        line("Топливо, л", route.fuel_liters)
        line("Стоимость, руб", route.cost_rub)
        line("CO2, кг", route.co2_kg)
        line("NOx, г", route.nox_g)
        line("PM, г", route.pm_g)
        line("Эко-рейтинг", route.eco_rating)
        line("Статус рейса", trip.get_status_display())
        line("Сформировано", timezone.localtime().strftime("%d.%m.%Y %H:%M"))

        y -= 4 * mm
        pdf.setFont(font_name, 12)
        pdf.drawString(20 * mm, y, "Точки маршрута")
        y -= 8 * mm
        pdf.setFont(font_name, 10)
        for point in points:
            line(point.get_point_type_display(), point.location.name)

        pdf.showPage()
        pdf.save()
        return buffer.getvalue()
