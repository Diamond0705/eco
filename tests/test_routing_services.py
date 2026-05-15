from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.fleet.models import EcoCalculationSettings, EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.models import RouteOption
from apps.routing.services.emission_calculator import EmissionCalculator
from apps.routing.services.mock_provider import MockRouteProvider
from apps.routing.services.route_calculation_service import RouteCalculationService

User = get_user_model()


@pytest.fixture
def routing_order():
    manager = User.objects.create_user(
        username="routing_service_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )
    standard = EcoStandard.objects.create(
        name="Euro VI",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    transport = Transport.objects.create(
        plate_number="Р111РР777",
        model="КАМАЗ 5490",
        category=Transport.Category.N3,
        capacity_kg=20000,
        fuel_consumption_l_per_100km=Decimal("29.00"),
        eco_standard=standard,
        year=2021,
    )
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
    order = ShipmentOrder.objects.create(
        manager=manager,
        transport=transport,
        cargo_name="Оборудование",
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
    return order


@pytest.mark.django_db
def test_emission_calculator_returns_positive_values_and_bounded_rating(routing_order):
    settings = EcoCalculationSettings.get_current()
    candidate = MockRouteProvider().get_candidates(routing_order)[0]

    result = EmissionCalculator().calculate(routing_order, candidate, settings)

    assert result["fuel_liters"] > 0
    assert result["cost_rub"] > 0
    assert result["co2_kg"] > 0
    assert result["nox_g"] > 0
    assert result["pm_g"] > 0
    assert Decimal("0") <= result["eco_rating"] <= Decimal("100")


@pytest.mark.django_db
def test_route_calculation_service_creates_snapshots_and_updates_order_status(routing_order):
    route_options = RouteCalculationService().calculate_for_order(routing_order)
    routing_order.refresh_from_db()
    current_settings = EcoCalculationSettings.get_current()

    assert len(route_options) == 3
    assert RouteOption.objects.filter(order=routing_order).count() == 3
    assert routing_order.status == ShipmentOrder.Status.CALCULATED
    assert all(option.calculation_settings == current_settings for option in route_options)
    assert all(option.is_selected is False for option in route_options)


@pytest.mark.django_db
def test_route_recalculation_replaces_old_non_selected_route_options(routing_order):
    RouteCalculationService().calculate_for_order(routing_order)
    old_ids = set(RouteOption.objects.filter(order=routing_order).values_list("id", flat=True))

    RouteCalculationService().calculate_for_order(routing_order)
    new_ids = set(RouteOption.objects.filter(order=routing_order).values_list("id", flat=True))

    assert RouteOption.objects.filter(order=routing_order).count() == 3
    assert old_ids.isdisjoint(new_ids)
