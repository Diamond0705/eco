from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.reports.services.pdf_fonts import register_pdf_font
from apps.reports.services.pdf_layout import draw_key_value_table, key_value_table_height
from apps.reports.services.waybill_pdf import WaybillPdfService
from apps.routing.services.route_calculation_service import RouteCalculationService
from apps.trips.services import TripLifecycleService

User = get_user_model()

TOLL_WARNING = (
    "На маршруте есть платные участки. "
    "Их стоимость не включена в итоговую стоимость перевозки."
)


@pytest.fixture
def manager():
    return User.objects.create_user(
        username="waybill_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def other_manager():
    return User.objects.create_user(
        username="waybill_other_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="waybill_admin",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        username="waybill_superuser",
        email="waybill_superuser@example.com",
        password="StrongPass12345",
    )


@pytest.fixture
def transport():
    standard = EcoStandard.objects.create(
        name="Euro VI",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    return Transport.objects.create(
        plate_number="Р701РР777",
        model="КАМАЗ 5490",
        category=Transport.Category.N3,
        capacity_kg=20000,
        fuel_consumption_l_per_100km=Decimal("29.00"),
        eco_standard=standard,
        year=2021,
    )


@pytest.fixture
def locations():
    origin = Location.objects.create(
        name="Москва",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )
    destination = Location.objects.create(
        name="Подольск",
        latitude=Decimal("55.4312"),
        longitude=Decimal("37.5447"),
    )
    return origin, destination


def create_trip(manager, transport, locations, cargo_name="Оборудование"):
    origin, destination = locations
    order = ShipmentOrder.objects.create(
        manager=manager,
        transport=transport,
        cargo_name=cargo_name,
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("1000.00"),
        desired_delivery_date="2026-06-01",
    )
    OrderPoint.objects.create(
        order=order,
        location=origin,
        sequence=1,
        point_type=OrderPoint.PointType.PICKUP,
    )
    OrderPoint.objects.create(
        order=order,
        location=destination,
        sequence=2,
        point_type=OrderPoint.PointType.DELIVERY,
    )
    RouteCalculationService().calculate_for_order(order)
    return TripLifecycleService().approve_route(order, order.route_options.first(), manager)


@pytest.mark.django_db
def test_waybill_pdf_download_for_own_trip(client, manager, transport, locations):
    trip = create_trip(manager, transport, locations)
    client.force_login(manager)

    response = client.get(reverse("trips:waybill", kwargs={"pk": trip.pk}))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == f'attachment; filename="waybill_trip_{trip.pk}.pdf"'
    assert response.content.startswith(b"%PDF")
    trip.refresh_from_db()
    assert not trip.waybill_pdf


@pytest.mark.django_db
def test_waybill_anonymous_user_redirected_to_login(client, manager, transport, locations):
    trip = create_trip(manager, transport, locations)

    response = client.get(reverse("trips:waybill", kwargs={"pk": trip.pk}))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_waybill_for_another_manager_trip_returns_404(
    client, manager, other_manager, transport, locations
):
    trip = create_trip(other_manager, transport, locations)
    client.force_login(manager)

    response = client.get(reverse("trips:waybill", kwargs={"pk": trip.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_waybill_admin_and_superuser_get_403(
    client, manager, admin_user, superuser, transport, locations
):
    trip = create_trip(manager, transport, locations)

    for user in (admin_user, superuser):
        client.force_login(user)
        assert client.get(reverse("trips:waybill", kwargs={"pk": trip.pk})).status_code == 403


@pytest.mark.django_db
def test_waybill_pdf_includes_calculation_summary_and_euro_class(
    manager, transport, locations
):
    trip = create_trip(manager, transport, locations)
    route = trip.route_option
    route.calculation_model_version = "v2.1"
    route.calculation_details_json = {
        "calculation_model_version": "v2.1",
        "final_fuel_multiplier": "1.15",
        "average_speed_kmh": "41.17",
        "co2_kg_per_km": "0.987",
        "co2_kg_per_ton_km": "0.1234",
    }
    route.save(update_fields=["calculation_model_version", "calculation_details_json"])
    captured_rows = []

    def capture_table(pdf, x, y, width, rows, font_name, label_width=55):
        captured_rows.extend(rows)
        return y - 1

    with patch("apps.reports.services.waybill_pdf.draw_key_value_table", capture_table):
        pdf_bytes = WaybillPdfService().build(trip)

    assert pdf_bytes.startswith(b"%PDF")
    assert ("Евро-класс", "Euro VI") in captured_rows
    assert ("Модель расчета", "v2.1") in captured_rows
    assert ("Итоговый множитель расхода", "1.15") in captured_rows
    assert ("Средняя скорость, км/ч", "41.17") in captured_rows
    assert ("CO2, кг/км", "0.987") in captured_rows
    assert ("CO2, кг/тонно-км", "0.1234") in captured_rows


@pytest.mark.django_db
def test_waybill_pdf_handles_old_snapshot_without_calculation_details(
    manager, transport, locations
):
    trip = create_trip(manager, transport, locations)
    route = trip.route_option
    route.calculation_model_version = "v1"
    route.calculation_details_json = {}
    route.route_facts_json = {}
    route.save(
        update_fields=[
            "calculation_model_version",
            "calculation_details_json",
            "route_facts_json",
        ]
    )
    captured_rows = []

    def capture_table(pdf, x, y, width, rows, font_name, label_width=55):
        captured_rows.extend(rows)
        return y - 1

    with patch("apps.reports.services.waybill_pdf.draw_key_value_table", capture_table):
        pdf_bytes = WaybillPdfService().build(trip)

    assert pdf_bytes.startswith(b"%PDF")
    assert ("Модель расчета", "v1") in captured_rows
    assert ("Итоговый множитель расхода", "—") in captured_rows
    assert ("Средняя скорость, км/ч", "—") in captured_rows
    assert ("CO2, кг/км", "—") in captured_rows
    assert ("CO2, кг/тонно-км", "—") in captured_rows


@pytest.mark.django_db
def test_waybill_pdf_shows_toll_notice_once(manager, transport, locations):
    trip = create_trip(manager, transport, locations)
    route = trip.route_option
    duplicate_warning = TOLL_WARNING
    route.route_facts_json = {
        "has_tolls": True,
        "toll_cost_rub": "0.00",
        "warnings": [duplicate_warning],
    }
    route.calculation_details_json = {"warnings": [duplicate_warning]}
    route.save(update_fields=["route_facts_json", "calculation_details_json"])
    captured_rows = []

    def capture_table(pdf, x, y, width, rows, font_name, label_width=55):
        captured_rows.extend(rows)
        return y - 1

    with patch("apps.reports.services.waybill_pdf.draw_key_value_table", capture_table):
        WaybillPdfService().build(trip)

    assert (
        "Платные участки",
        TOLL_WARNING,
    ) in captured_rows
    assert (
        captured_rows.count(
            (
                "Платные участки",
                TOLL_WARNING,
            )
        )
        == 1
    )


def test_waybill_pdf_reserves_space_for_all_rows_in_section():
    service = WaybillPdfService()

    assert service._section_height([("Показатель", "Значение")] * 6) == 53 * mm


def test_waybill_key_value_table_wraps_long_values():
    pdf = canvas.Canvas(BytesIO(), pagesize=A4)
    font_name = register_pdf_font()
    width = A4[0] - 30 * mm
    rows = [("Платные участки", TOLL_WARNING)]
    drawn_strings = []

    original_draw_string = pdf.drawString

    def capture_draw_string(x, y, text):
        drawn_strings.append((x, y, text))
        return original_draw_string(x, y, text)

    pdf.drawString = capture_draw_string
    height = key_value_table_height(pdf, width, rows, font_name)

    draw_key_value_table(pdf, 15 * mm, 250 * mm, width, rows, font_name)

    value_lines = [text for x, _y, text in drawn_strings if x == 15 * mm + 55 * mm]
    assert height > 7 * mm
    assert len(value_lines) >= 2
    assert "".join(value_lines).replace(" ", "")
