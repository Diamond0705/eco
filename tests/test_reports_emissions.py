from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from reportlab.lib.units import mm

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.reports.services.emissions_report import EmissionsReportPdfService, EmissionsReportService
from apps.routing.services.route_calculation_service import RouteCalculationService
from apps.trips.services import TripLifecycleService

User = get_user_model()


@pytest.fixture
def manager():
    return User.objects.create_user(
        username="emissions_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def other_manager():
    return User.objects.create_user(
        username="emissions_other_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="emissions_admin",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        username="emissions_superuser",
        email="emissions_superuser@example.com",
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
        plate_number="Р801РР777",
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


def create_trip(manager, transport, locations, cargo_name):
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


def deliver_trip(trip, manager):
    service = TripLifecycleService()
    service.start_trip(trip, manager)
    service.deliver_trip(trip, manager)
    trip.refresh_from_db()
    return trip


@pytest.mark.django_db
def test_emissions_report_page_scopes_to_current_manager_delivered_trips(
    client, manager, other_manager, transport, locations
):
    delivered_trip = deliver_trip(
        create_trip(manager, transport, locations, "Свой доставленный груз"),
        manager,
    )
    planned_trip = create_trip(manager, transport, locations, "Свой плановый груз")
    in_progress_trip = create_trip(manager, transport, locations, "Свой рейс в пути")
    TripLifecycleService().start_trip(in_progress_trip, manager)
    deliver_trip(create_trip(other_manager, transport, locations, "Чужой груз"), other_manager)
    client.force_login(manager)

    response = client.get(reverse("reports:emissions"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Отчет по выбросам" in content
    assert "Свой доставленный груз" in content
    assert f"№{delivered_trip.pk}" in content
    assert planned_trip.order.cargo_name not in content
    assert in_progress_trip.order.cargo_name not in content
    assert "Чужой груз" not in content


@pytest.mark.django_db
def test_emissions_report_empty_state(client, manager):
    client.force_login(manager)

    response = client.get(reverse("reports:emissions"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Доставленных рейсов за выбранный период нет." in content


@pytest.mark.django_db
def test_emissions_report_invalid_date_is_safe(client, manager):
    client.force_login(manager)

    response = client.get(reverse("reports:emissions"), {"date_from": "bad-date"})
    content = response.content.decode()

    assert response.status_code == 200
    assert "Некорректная дата начала периода." in content


@pytest.mark.django_db
def test_emissions_pdf_returns_pdf(client, manager, transport, locations):
    deliver_trip(create_trip(manager, transport, locations, "PDF груз"), manager)
    client.force_login(manager)

    response = client.get(reverse("reports:emissions_pdf"))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


@pytest.mark.django_db
def test_emissions_report_aggregates_snapshot_intensity_metrics(
    client, manager, transport, locations
):
    first_trip = deliver_trip(create_trip(manager, transport, locations, "Первый груз"), manager)
    second_trip = deliver_trip(create_trip(manager, transport, locations, "Второй груз"), manager)
    first_route = first_trip.route_option
    second_route = second_trip.route_option
    first_route.co2_kg = Decimal("100.00")
    first_route.nox_g = Decimal("10.00")
    first_route.pm_g = Decimal("1.000")
    first_route.eco_rating = Decimal("80.00")
    first_route.calculation_details_json = {
        "co2_kg_per_km": "0.500",
        "co2_kg_per_ton_km": "0.1000",
    }
    first_route.route_facts_json = {"has_tolls": True, "toll_cost_rub": "0.00"}
    first_route.save(
        update_fields=[
            "co2_kg",
            "nox_g",
            "pm_g",
            "eco_rating",
            "calculation_details_json",
            "route_facts_json",
        ]
    )
    second_route.co2_kg = Decimal("50.00")
    second_route.nox_g = Decimal("5.00")
    second_route.pm_g = Decimal("0.500")
    second_route.eco_rating = Decimal("60.00")
    second_route.calculation_details_json = {"co2_kg_per_km": "1.000"}
    second_route.route_facts_json = {}
    second_route.save(
        update_fields=[
            "co2_kg",
            "nox_g",
            "pm_g",
            "eco_rating",
            "calculation_details_json",
            "route_facts_json",
        ]
    )
    client.force_login(manager)

    response = client.get(reverse("reports:emissions"))
    summary = response.context["report"]["summary"]
    content = response.content.decode()

    assert response.status_code == 200
    assert summary["co2_kg"] == Decimal("150.00")
    assert summary["nox_g"] == Decimal("15.00")
    assert summary["pm_g"] == Decimal("1.500")
    assert summary["average_co2_kg_per_km"] == "0.750"
    assert summary["average_co2_kg_per_ton_km"] == "0.1000"
    assert summary["average_eco_rating"] == "70.00"
    assert summary["toll_routes_count"] == 1
    assert "CO2 на км" in content
    assert "CO2 на тонно-км" in content
    assert "Платные участки" in content
    assert "Euro VI" in content


@pytest.mark.django_db
def test_emissions_report_pdf_includes_new_summary_and_euro_class(
    manager, transport, locations
):
    deliver_trip(create_trip(manager, transport, locations, "PDF показатели"), manager)
    report = EmissionsReportService().build(manager)
    captured_summary_rows = []
    captured_table_headers = []
    captured_table_rows = []
    captured_label_widths = []
    header_calls = []

    def capture_key_value_table(pdf, x, y, width, rows, font_name, label_width=35):
        captured_summary_rows.extend(rows)
        captured_label_widths.append(label_width)
        return y - 1

    def capture_simple_table(pdf, x, y, widths, headers, rows, font_name, row_height=7):
        captured_table_headers.extend(headers)
        captured_table_rows.extend(rows)
        return y - 1

    def capture_header(pdf, width, height, font_name, title):
        header_calls.append(title)
        return height - 30 * mm

    with (
        patch("apps.reports.services.emissions_report.draw_header", capture_header),
        patch(
            "apps.reports.services.emissions_report.draw_key_value_table",
            capture_key_value_table,
        ),
        patch("apps.reports.services.emissions_report.draw_simple_table", capture_simple_table),
    ):
        pdf_bytes = EmissionsReportPdfService().build(manager, report)

    assert pdf_bytes.startswith(b"%PDF")
    assert (
        "Средний CO2 на км",
        report["summary"]["average_co2_kg_per_km"],
    ) in captured_summary_rows
    assert (
        "Средний CO2 на тонно-км",
        report["summary"]["average_co2_kg_per_ton_km"],
    ) in captured_summary_rows
    assert (
        "Маршруты с платными участками",
        report["summary"]["toll_routes_count"],
    ) in captured_summary_rows
    assert 70 * mm in captured_label_widths
    assert header_calls == ["Отчет по выбросам", "Отчет по выбросам"]
    assert "Евро" in captured_table_headers
    assert any("Euro VI" in str(row) for table_row in captured_table_rows for row in table_row)


@pytest.mark.django_db
def test_emissions_report_access_rules(client, manager, admin_user, superuser):
    assert client.get(reverse("reports:emissions")).status_code == 302

    for user in (admin_user, superuser):
        client.force_login(user)
        assert client.get(reverse("reports:emissions")).status_code == 403
        assert client.get(reverse("reports:emissions_pdf")).status_code == 403


@pytest.mark.django_db
def test_no_excel_endpoint_exists(client, manager):
    client.force_login(manager)

    response = client.get("/reports/emissions.xlsx/")

    assert response.status_code == 404


def test_no_new_dependencies_added_for_reports():
    requirements = {
        line.strip()
        for line in Path("requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

    assert requirements == {
        "Django>=5.2.8,<5.3",
        "psycopg[binary]",
        "django-environ",
        "reportlab",
        "pytest",
        "pytest-django",
        "ruff",
    }
