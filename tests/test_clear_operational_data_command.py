from decimal import Decimal
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.utils import timezone

from apps.fleet.models import EcoCalculationSettings, EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.models import RouteOption
from apps.trips.models import Trip, TripStatusEvent

User = get_user_model()


def create_operational_dataset():
    manager = User.objects.create_user(
        username="cleanup_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )
    Group.objects.create(name="cleanup_reference_group")
    standard = EcoStandard.objects.create(
        name="Euro VI Cleanup",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    transport = Transport.objects.create(
        plate_number="К100КК777",
        model="КАМАЗ Cleanup",
        category=Transport.Category.N3,
        fuel_type=Transport.FuelType.DIESEL,
        capacity_kg=20000,
        fuel_consumption_l_per_100km=Decimal("29.00"),
        eco_standard=standard,
        year=2024,
    )
    origin = Location.objects.create(
        name="Москва Cleanup",
        address="Москва",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )
    destination = Location.objects.create(
        name="Подольск Cleanup",
        address="Подольск",
        latitude=Decimal("55.4312"),
        longitude=Decimal("37.5447"),
    )
    settings = EcoCalculationSettings.get_current()
    order = ShipmentOrder.objects.create(
        manager=manager,
        transport=transport,
        cargo_name="Тестовый груз",
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("1000.00"),
        desired_delivery_date="2026-06-01",
        status=ShipmentOrder.Status.PLANNED,
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
    route_option = RouteOption.objects.create(
        order=order,
        name="Учебный маршрут",
        provider=RouteOption.Provider.MOCK,
        distance_km=Decimal("50.00"),
        duration_minutes=60,
        fuel_multiplier=Decimal("1.00"),
        fuel_liters=Decimal("15.00"),
        cost_rub=Decimal("10000.00"),
        co2_kg=Decimal("40.35"),
        nox_g=Decimal("27.60"),
        pm_g=Decimal("0.600"),
        eco_rating=Decimal("88.00"),
        geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
        calculation_settings=settings,
        is_selected=True,
    )
    trip = Trip.objects.create(
        order=order,
        route_option=route_option,
        status=Trip.Status.IN_PROGRESS,
        actual_start_at=timezone.now(),
    )
    TripStatusEvent.objects.create(
        trip=trip,
        old_status=Trip.Status.PLANNED,
        new_status=Trip.Status.IN_PROGRESS,
        changed_by=manager,
    )
    return {
        "manager": manager,
        "standard": standard,
        "transport": transport,
        "origin": origin,
        "destination": destination,
        "settings": settings,
    }


def operational_counts():
    return {
        "orders": ShipmentOrder.objects.count(),
        "points": OrderPoint.objects.count(),
        "routes": RouteOption.objects.count(),
        "trips": Trip.objects.count(),
        "events": TripStatusEvent.objects.count(),
    }


@pytest.mark.django_db
def test_clear_operational_data_without_yes_does_not_delete_anything():
    create_operational_dataset()
    before = operational_counts()
    output = StringIO()

    call_command("clear_operational_data", stdout=output)

    assert operational_counts() == before
    content = output.getvalue()
    assert "локальной/демонстрационной" in content
    assert "До удаления:" in content
    assert "- ShipmentOrder: 1" in content
    assert "- OrderPoint: 2" in content
    assert "- RouteOption: 1" in content
    assert "- Trip: 1" in content
    assert "- TripStatusEvent: 1" in content
    assert "Удаление не выполнено" in content
    assert "После удаления:" not in content


@pytest.mark.django_db
def test_clear_operational_data_reset_sequences_requires_yes():
    create_operational_dataset()
    before = operational_counts()
    output = StringIO()

    call_command("clear_operational_data", reset_sequences=True, stdout=output)

    assert operational_counts() == before
    content = output.getvalue()
    assert "Удаление не выполнено" in content
    assert "Сброс sequences не выполнен" in content
    assert "Sequences операционных таблиц сброшены." not in content


@pytest.mark.django_db
def test_clear_operational_data_with_yes_deletes_only_operational_data():
    references = create_operational_dataset()
    output = StringIO()

    call_command("clear_operational_data", yes=True, stdout=output)

    assert operational_counts() == {
        "orders": 0,
        "points": 0,
        "routes": 0,
        "trips": 0,
        "events": 0,
    }
    assert User.objects.filter(pk=references["manager"].pk).exists()
    assert Transport.objects.filter(pk=references["transport"].pk).exists()
    assert Location.objects.filter(pk=references["origin"].pk).exists()
    assert Location.objects.filter(pk=references["destination"].pk).exists()
    assert EcoStandard.objects.filter(pk=references["standard"].pk).exists()
    assert EcoCalculationSettings.objects.filter(pk=references["settings"].pk).exists()
    assert Group.objects.filter(name="cleanup_reference_group").exists()

    content = output.getvalue()
    assert "локальной/демонстрационной" in content
    assert "До удаления:" in content
    assert "Операционные данные удалены." in content
    assert "После удаления:" in content
    assert "- ShipmentOrder: 0" in content
    assert "- OrderPoint: 0" in content
    assert "- RouteOption: 0" in content
    assert "- Trip: 0" in content
    assert "- TripStatusEvent: 0" in content


@pytest.mark.django_db(transaction=True)
def test_clear_operational_data_with_reset_sequences_resets_operational_ids():
    references = create_operational_dataset()
    second_order = ShipmentOrder.objects.create(
        manager=references["manager"],
        transport=references["transport"],
        cargo_name="Второй тестовый груз",
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("1000.00"),
        desired_delivery_date="2026-06-01",
        status=ShipmentOrder.Status.NEW,
    )
    assert second_order.pk > 1
    output = StringIO()

    call_command("clear_operational_data", yes=True, reset_sequences=True, stdout=output)
    new_order = ShipmentOrder.objects.create(
        manager=references["manager"],
        transport=references["transport"],
        cargo_name="Новый тестовый груз",
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("1000.00"),
        desired_delivery_date="2026-06-01",
        status=ShipmentOrder.Status.NEW,
    )

    assert new_order.pk == 1
    assert "Sequences операционных таблиц сброшены." in output.getvalue()
