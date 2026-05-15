from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.services.mock_provider import MockRouteProvider

User = get_user_model()


@pytest.fixture
def route_order():
    manager = User.objects.create_user(
        username="routing_provider_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )
    standard = EcoStandard.objects.create(
        name="Euro VI",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    transport = Transport.objects.create(
        plate_number="М111ММ777",
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
def test_mock_route_provider_returns_three_routes(route_order):
    candidates = MockRouteProvider().get_candidates(route_order)

    assert [candidate.name for candidate in candidates] == ["Быстрый", "Короткий", "Экологичный"]
    assert [candidate.fuel_multiplier for candidate in candidates] == [
        Decimal("1.08"),
        Decimal("1.00"),
        Decimal("0.92"),
    ]


@pytest.mark.django_db
def test_mock_route_provider_geometry_format_is_leaflet_coordinates(route_order):
    candidates = MockRouteProvider().get_candidates(route_order)
    ordered_points = list(route_order.points.select_related("location").order_by("sequence"))
    origin = [
        float(ordered_points[0].location.latitude),
        float(ordered_points[0].location.longitude),
    ]
    destination = [
        float(ordered_points[-1].location.latitude),
        float(ordered_points[-1].location.longitude),
    ]

    for candidate in candidates:
        assert isinstance(candidate.geometry_json, list)
        assert len(candidate.geometry_json) >= 5
        assert candidate.geometry_json[0] == origin
        assert candidate.geometry_json[-1] == destination
        for coordinate in candidate.geometry_json:
            assert isinstance(coordinate, list)
            assert len(coordinate) == 2
            assert all(isinstance(value, float) for value in coordinate)


@pytest.mark.django_db
def test_mock_route_provider_is_deterministic_and_does_not_use_external_api(
    route_order, monkeypatch
):
    def fail_network(*args, **kwargs):
        raise AssertionError("External API calls are not allowed for mock routes.")

    monkeypatch.setattr("socket.create_connection", fail_network)

    provider = MockRouteProvider()
    first_result = provider.get_candidates(route_order)
    second_result = provider.get_candidates(route_order)

    assert first_result == second_result
