from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.reports.services.waybill_pdf import WaybillPdfService
from apps.routing.services.route_calculation_service import RouteCalculationService
from apps.trips.models import Trip
from apps.trips.services import TripLifecycleService

User = get_user_model()


@pytest.fixture
def manager():
    return User.objects.create_user(
        username="event_time_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def other_manager():
    return User.objects.create_user(
        username="event_time_other_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def transport():
    standard = EcoStandard.objects.create(
        name="Euro VI Event Time",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    return Transport.objects.create(
        plate_number="А800АА777",
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
        name="Москва события",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )
    destination = Location.objects.create(
        name="Подольск события",
        latitude=Decimal("55.4312"),
        longitude=Decimal("37.5447"),
    )
    return origin, destination


def aware_datetime(year, month, day, hour, minute):
    return timezone.datetime(
        year,
        month,
        day,
        hour,
        minute,
        tzinfo=timezone.get_current_timezone(),
    )


def create_order(manager, transport, locations, cargo_name):
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
    order.refresh_from_db()
    return order


def approve_trip(manager, transport, locations, cargo_name, route_name="Быстрый"):
    order = create_order(manager, transport, locations, cargo_name)
    route = order.route_options.get(name=route_name)
    return TripLifecycleService().approve_route(order, route, manager)


def start_trip(trip, manager, value=None):
    return TripLifecycleService().start_trip(
        trip,
        manager,
        actual_start_at=value or aware_datetime(2026, 6, 1, 10, 0),
    )


def deliver_trip(trip, manager, value=None):
    return TripLifecycleService().deliver_trip(
        trip,
        manager,
        actual_finish_at=value or aware_datetime(2026, 6, 1, 12, 0),
    )


@pytest.mark.django_db
def test_trip_list_filters_by_status(client, manager, transport, locations):
    planned_trip = approve_trip(manager, transport, locations, "Плановый груз")
    delivered_trip = approve_trip(manager, transport, locations, "Доставленный груз")
    start_trip(delivered_trip, manager)
    deliver_trip(delivered_trip, manager)
    client.force_login(manager)

    response = client.get(reverse("trips:list"), {"status": Trip.Status.DELIVERED})
    content = response.content.decode()

    assert response.status_code == 200
    assert f"№{delivered_trip.pk}" in content
    assert f"№{planned_trip.pk}" not in content


@pytest.mark.django_db
def test_trip_list_filters_by_route_name(client, manager, transport, locations):
    fast_trip = approve_trip(manager, transport, locations, "Быстрый груз", "Быстрый")
    eco_trip = approve_trip(manager, transport, locations, "Экологичный груз", "Экологичный")
    client.force_login(manager)

    response = client.get(reverse("trips:list"), {"route_name": "Экологичный"})
    content = response.content.decode()

    assert response.status_code == 200
    assert f"№{eco_trip.pk}" in content
    assert f"№{fast_trip.pk}" not in content


@pytest.mark.django_db
def test_trip_filters_ignore_invalid_values_and_keep_manager_scope(
    client, manager, other_manager, transport, locations
):
    own_trip = approve_trip(manager, transport, locations, "Свой груз")
    other_trip = approve_trip(other_manager, transport, locations, "Чужой груз")
    client.force_login(manager)

    response = client.get(
        reverse("trips:list"),
        {"status": "bad-status", "route_name": "GraphHopper"},
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert f"№{own_trip.pk}" in content
    assert f"№{other_trip.pk}" not in content
    assert "Чужой груз" not in content


@pytest.mark.django_db
def test_start_action_stores_provided_actual_start_and_event_time(
    client, manager, transport, locations
):
    trip = approve_trip(manager, transport, locations, "Старт с ручным временем")
    client.force_login(manager)

    response = client.post(
        reverse("trips:start", kwargs={"pk": trip.pk}),
        {"actual_start_at": "2026-06-02T09:30", "comment": "Водитель сообщил по телефону"},
    )
    trip.refresh_from_db()
    event = trip.status_events.get(new_status=Trip.Status.IN_PROGRESS)

    assert response.status_code == 302
    assert trip.status == Trip.Status.IN_PROGRESS
    assert timezone.localtime(trip.actual_start_at).strftime("%Y-%m-%dT%H:%M") == "2026-06-02T09:30"
    assert timezone.localtime(event.event_at).strftime("%Y-%m-%dT%H:%M") == "2026-06-02T09:30"
    assert event.changed_at is not None
    assert event.comment == "Водитель сообщил по телефону"


@pytest.mark.django_db
def test_deliver_action_stores_provided_actual_finish_and_event_time(
    client, manager, transport, locations
):
    trip = approve_trip(manager, transport, locations, "Финиш с ручным временем")
    start_trip(trip, manager, aware_datetime(2026, 6, 2, 9, 30))
    client.force_login(manager)

    response = client.post(
        reverse("trips:deliver", kwargs={"pk": trip.pk}),
        {"actual_finish_at": "2026-06-02T14:45", "comment": "Получатель подтвердил"},
    )
    trip.refresh_from_db()
    trip.order.refresh_from_db()
    event = trip.status_events.get(new_status=Trip.Status.DELIVERED)

    assert response.status_code == 302
    assert trip.status == Trip.Status.DELIVERED
    assert trip.order.status == ShipmentOrder.Status.COMPLETED
    finish_label = timezone.localtime(trip.actual_finish_at).strftime("%Y-%m-%dT%H:%M")
    assert finish_label == "2026-06-02T14:45"
    assert timezone.localtime(event.event_at).strftime("%Y-%m-%dT%H:%M") == "2026-06-02T14:45"
    assert event.changed_at is not None
    assert event.comment == "Получатель подтвердил"


@pytest.mark.django_db
def test_finish_before_start_is_rejected(client, manager, transport, locations):
    trip = approve_trip(manager, transport, locations, "Неверный финиш")
    start_trip(trip, manager, aware_datetime(2026, 6, 2, 10, 0))
    client.force_login(manager)

    response = client.post(
        reverse("trips:deliver", kwargs={"pk": trip.pk}),
        {"actual_finish_at": "2026-06-02T09:00", "comment": "Ошибка ввода"},
    )
    trip.refresh_from_db()
    trip.order.refresh_from_db()

    assert response.status_code == 302
    assert trip.status == Trip.Status.IN_PROGRESS
    assert trip.actual_finish_at is None
    assert trip.order.status == ShipmentOrder.Status.PLANNED
    assert not trip.status_events.filter(new_status=Trip.Status.DELIVERED).exists()


@pytest.mark.django_db
def test_get_start_and_deliver_do_not_change_status(client, manager, transport, locations):
    trip = approve_trip(manager, transport, locations, "GET не меняет")
    client.force_login(manager)

    assert client.get(reverse("trips:start", kwargs={"pk": trip.pk})).status_code == 405
    trip.refresh_from_db()
    assert trip.status == Trip.Status.PLANNED

    start_trip(trip, manager)
    assert client.get(reverse("trips:deliver", kwargs={"pk": trip.pk})).status_code == 405
    trip.refresh_from_db()
    assert trip.status == Trip.Status.IN_PROGRESS


@pytest.mark.django_db
def test_analytics_period_filter_uses_actual_finish_at(client, manager, transport, locations):
    june_trip = approve_trip(manager, transport, locations, "Июньский груз")
    start_trip(june_trip, manager, aware_datetime(2026, 6, 1, 10, 0))
    deliver_trip(june_trip, manager, aware_datetime(2026, 6, 1, 12, 0))

    july_trip = approve_trip(manager, transport, locations, "Июльский груз")
    start_trip(july_trip, manager, aware_datetime(2026, 7, 1, 10, 0))
    deliver_trip(july_trip, manager, aware_datetime(2026, 7, 1, 12, 0))
    client.force_login(manager)

    response = client.get(
        reverse("dashboard:manager_analytics"),
        {"date_from": "2026-07-01", "date_to": "2026-07-31"},
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert "Июльский груз" in content
    assert "Июньский груз" not in content
    assert response.context["analytics"]["delivered"]["trips_count"] == 1


@pytest.mark.django_db
def test_waybill_pdf_includes_actual_start_and_finish_labels(manager, transport, locations):
    trip = approve_trip(manager, transport, locations, "PDF даты")
    start_trip(trip, manager, aware_datetime(2026, 6, 3, 8, 0))
    deliver_trip(trip, manager, aware_datetime(2026, 6, 3, 11, 0))
    trip.refresh_from_db()
    captured_labels = []

    def capture_table(pdf, x, y, width, rows, font_name, label_width=55):
        captured_labels.extend(label for label, _value in rows)
        return y - 1

    with patch("apps.reports.services.waybill_pdf.draw_key_value_table", capture_table):
        pdf_bytes = WaybillPdfService().build(trip)

    assert pdf_bytes.startswith(b"%PDF")
    assert "Фактическое начало" in captured_labels
    assert "Фактическое завершение" in captured_labels
