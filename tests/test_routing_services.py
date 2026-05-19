from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.fleet.models import EcoCalculationSettings, EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.models import RouteOption
from apps.routing.services.emission_calculator import EmissionCalculator
from apps.routing.services.mock_provider import MockRouteProvider
from apps.routing.services.providers import RouteCandidate, RoutingProviderResponseError
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
    assert all(option.route_facts_json["schema_version"] == 1 for option in route_options)
    assert all(
        option.route_facts_json["provider"] == RouteOption.Provider.MOCK
        for option in route_options
    )
    assert all(option.route_facts_json["toll_cost_rub"] == "0.00" for option in route_options)


@pytest.mark.django_db
def test_route_recalculation_replaces_old_non_selected_route_options(routing_order):
    RouteCalculationService().calculate_for_order(routing_order)
    old_ids = set(RouteOption.objects.filter(order=routing_order).values_list("id", flat=True))

    RouteCalculationService().calculate_for_order(routing_order)
    new_ids = set(RouteOption.objects.filter(order=routing_order).values_list("id", flat=True))

    assert RouteOption.objects.filter(order=routing_order).count() == 3
    assert old_ids.isdisjoint(new_ids)


class OneCandidateProvider:
    provider = RouteOption.Provider.GRAPHHOPPER

    def get_candidates(self, order):
        return [
            RouteCandidate(
                name="Маршрут GraphHopper",
                provider=RouteOption.Provider.GRAPHHOPPER,
                distance_km=Decimal("10.00"),
                duration_minutes=20,
                fuel_multiplier=Decimal("1.00"),
                geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
            )
        ]


class FailingGraphHopperProvider:
    def get_candidates(self, order):
        raise RoutingProviderResponseError("GraphHopper failed in test.")


@pytest.mark.django_db
def test_route_calculation_service_accepts_single_graphhopper_candidate(routing_order):
    route_options = RouteCalculationService(provider=OneCandidateProvider()).calculate_for_order(
        routing_order
    )

    assert len(route_options) == 1
    assert RouteOption.objects.filter(order=routing_order).count() == 1
    assert route_options[0].provider == RouteOption.Provider.GRAPHHOPPER
    assert route_options[0].fuel_multiplier == Decimal("1.00")
    assert route_options[0].route_facts_json["provider"] == RouteOption.Provider.GRAPHHOPPER


@pytest.mark.django_db
def test_route_calculation_service_uses_standard_graphhopper_options(
    routing_order,
    monkeypatch,
):
    captured = {}

    def fake_get_route_provider(options):
        captured["options"] = options
        return OneCandidateProvider()

    monkeypatch.setattr(
        "apps.routing.services.route_calculation_service.get_route_provider",
        fake_get_route_provider,
    )

    service = RouteCalculationService(calculation_mode="standard")
    service.calculate_for_order(routing_order)

    assert captured["options"].requested_candidates == 3
    assert captured["options"].alternative_max_paths == 3
    assert captured["options"].max_candidates == 3
    assert captured["options"].enable_strategy_requests is False
    assert service.last_requested_count == 3
    assert service.last_found_count == 1


@pytest.mark.django_db
def test_route_calculation_service_uses_extended_graphhopper_options(
    routing_order,
    monkeypatch,
):
    captured = {}

    def fake_get_route_provider(options):
        captured["options"] = options
        return OneCandidateProvider()

    monkeypatch.setattr(
        "apps.routing.services.route_calculation_service.get_route_provider",
        fake_get_route_provider,
    )

    RouteCalculationService(calculation_mode="extended").calculate_for_order(routing_order)

    assert captured["options"].requested_candidates == 5
    assert captured["options"].alternative_max_paths == 5
    assert captured["options"].max_candidates == 5
    assert captured["options"].enable_strategy_requests is True
    assert captured["options"].max_strategy_requests == 2


@pytest.mark.django_db
@override_settings(
    ROUTE_PROVIDER="graphhopper",
    GRAPHHOPPER_API_KEY="",
    GRAPHHOPPER_FALLBACK_TO_MOCK=True,
)
def test_route_calculation_falls_back_to_mock_when_graphhopper_key_missing(routing_order):
    service = RouteCalculationService()

    route_options = service.calculate_for_order(routing_order)

    assert len(route_options) == 3
    assert {option.provider for option in route_options} == {RouteOption.Provider.MOCK}
    assert service.last_warning == (
        "GraphHopper недоступен, поэтому маршруты рассчитаны "
        "демонстрационным mock-провайдером."
    )


@pytest.mark.django_db
@override_settings(
    ROUTE_PROVIDER="graphhopper",
    GRAPHHOPPER_API_KEY="",
    GRAPHHOPPER_FALLBACK_TO_MOCK=False,
)
def test_route_calculation_reports_missing_graphhopper_key_without_fallback(routing_order):
    with pytest.raises(ValueError, match="Провайдер маршрутизации настроен некорректно"):
        RouteCalculationService().calculate_for_order(routing_order)

    assert RouteOption.objects.filter(order=routing_order).count() == 0


@pytest.mark.django_db
@override_settings(
    ROUTE_PROVIDER="graphhopper",
    GRAPHHOPPER_API_KEY="test-key",
    GRAPHHOPPER_FALLBACK_TO_MOCK=False,
)
def test_failed_graphhopper_calculation_keeps_old_route_options(routing_order, monkeypatch):
    RouteCalculationService(provider=MockRouteProvider()).calculate_for_order(routing_order)
    old_ids = set(RouteOption.objects.filter(order=routing_order).values_list("id", flat=True))

    monkeypatch.setattr(
        "apps.routing.services.route_calculation_service.get_route_provider",
        lambda options: FailingGraphHopperProvider(),
    )

    with pytest.raises(ValueError, match="Не удалось получить маршруты"):
        RouteCalculationService().calculate_for_order(routing_order)

    new_ids = set(RouteOption.objects.filter(order=routing_order).values_list("id", flat=True))
    assert new_ids == old_ids


@pytest.mark.django_db
@override_settings(
    ROUTE_PROVIDER="graphhopper",
    GRAPHHOPPER_API_KEY="test-key",
    GRAPHHOPPER_FALLBACK_TO_MOCK=True,
)
def test_graphhopper_api_error_falls_back_to_mock(routing_order, monkeypatch):
    monkeypatch.setattr(
        "apps.routing.services.route_calculation_service.get_route_provider",
        lambda options: FailingGraphHopperProvider(),
    )
    service = RouteCalculationService()

    route_options = service.calculate_for_order(routing_order)

    assert len(route_options) == 3
    assert {option.provider for option in route_options} == {RouteOption.Provider.MOCK}
    assert service.last_warning
