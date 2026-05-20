from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.fleet.models import EcoCalculationSettings, EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.models import RouteOption
from apps.routing.services.emission_calculator import EmissionCalculator
from apps.routing.services.graphhopper_provider import GraphHopperRouteProvider
from apps.routing.services.mock_provider import MockRouteProvider
from apps.routing.services.providers import (
    RouteCalculationOptions,
    RouteCandidate,
    RouteFacts,
    RoutingProviderResponseError,
)
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
def test_emission_calculator_v1_ignores_route_facts(routing_order):
    settings = EcoCalculationSettings.get_current()
    base_candidate = RouteCandidate(
        name="Маршрут GraphHopper",
        provider=RouteOption.Provider.GRAPHHOPPER,
        distance_km=Decimal("10.00"),
        duration_minutes=20,
        fuel_multiplier=Decimal("1.00"),
        geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
    )
    enriched_candidate = RouteCandidate(
        name=base_candidate.name,
        provider=base_candidate.provider,
        distance_km=base_candidate.distance_km,
        duration_minutes=base_candidate.duration_minutes,
        fuel_multiplier=base_candidate.fuel_multiplier,
        geometry_json=base_candidate.geometry_json,
        route_facts=RouteFacts(
            provider=RouteOption.Provider.GRAPHHOPPER,
            has_tolls=True,
            road_details={"road_class_summary": {"motorway": {"distance_km": "10.00"}}},
        ),
    )

    assert EmissionCalculator(model_version="v1").calculate(
        routing_order,
        base_candidate,
        settings,
    ) == EmissionCalculator(model_version="v1").calculate(
        routing_order,
        enriched_candidate,
        settings,
    )


@pytest.mark.django_db
def test_emission_calculator_v2_uses_average_speed_factor(routing_order):
    settings = EcoCalculationSettings.get_current()
    candidate = RouteCandidate(
        name="Маршрут GraphHopper",
        provider=RouteOption.Provider.GRAPHHOPPER,
        distance_km=Decimal("10.00"),
        duration_minutes=20,
        fuel_multiplier=Decimal("1.00"),
        geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
    )

    result = EmissionCalculator(model_version="v2").calculate(routing_order, candidate, settings)

    assert result["fuel_multiplier"] == Decimal("1.15")
    assert result["calculation_model_version"] == "v2"
    assert result["calculation_details_json"]["average_speed_kmh"] == "30.00"
    assert result["calculation_details_json"]["speed_factor"] == "1.15"


@pytest.mark.django_db
def test_emission_calculator_v2_uses_road_class_and_surface_factors(routing_order):
    settings = EcoCalculationSettings.get_current()
    candidate = RouteCandidate(
        name="Маршрут GraphHopper",
        provider=RouteOption.Provider.GRAPHHOPPER,
        distance_km=Decimal("10.00"),
        duration_minutes=8,
        fuel_multiplier=Decimal("1.00"),
        geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
        route_facts=RouteFacts(
            provider=RouteOption.Provider.GRAPHHOPPER,
            road_details={
                "road_class_summary": {
                    "residential": {"distance_km": "10.00", "share_percent": "100.00"}
                },
                "surface_summary": {
                    "gravel": {"distance_km": "10.00", "share_percent": "100.00"}
                },
            },
        ),
    )

    result = EmissionCalculator(model_version="v2").calculate(routing_order, candidate, settings)
    details = result["calculation_details_json"]

    assert details["road_class_factor"] == "1.10"
    assert details["surface_factor"] == "1.12"
    assert result["fuel_multiplier"] == Decimal("1.23")


@pytest.mark.django_db
def test_emission_calculator_v2_clamps_route_fact_multiplier(routing_order):
    settings = EcoCalculationSettings.get_current()
    candidate = RouteCandidate(
        name="Маршрут GraphHopper",
        provider=RouteOption.Provider.GRAPHHOPPER,
        distance_km=Decimal("10.00"),
        duration_minutes=60,
        fuel_multiplier=Decimal("1.00"),
        geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
        route_facts=RouteFacts(
            provider=RouteOption.Provider.GRAPHHOPPER,
            supports_traffic=True,
            traffic_delay_minutes=60,
            road_details={
                "road_class_summary": {
                    "service": {"distance_km": "10.00", "share_percent": "100.00"}
                },
                "surface_summary": {
                    "ground": {"distance_km": "10.00", "share_percent": "100.00"}
                },
            },
        ),
    )

    result = EmissionCalculator(model_version="v2").calculate(routing_order, candidate, settings)

    assert result["fuel_multiplier"] == Decimal("1.40")
    assert result["calculation_details_json"]["route_fact_multiplier"] == "1.40"


@pytest.mark.django_db
def test_emission_calculator_v2_keeps_mock_demo_multiplier(routing_order):
    settings = EcoCalculationSettings.get_current()
    candidate = MockRouteProvider().get_candidates(routing_order)[0]

    result = EmissionCalculator(model_version="v2").calculate(routing_order, candidate, settings)

    assert result["fuel_multiplier"] == candidate.fuel_multiplier
    assert result["calculation_details_json"]["route_fact_multiplier"] == "1.00"


@pytest.mark.django_db
def test_emission_calculator_v2_includes_time_cost_and_unknown_toll_warning(routing_order):
    settings = EcoCalculationSettings.get_current()
    candidate = RouteCandidate(
        name="Маршрут GraphHopper",
        provider=RouteOption.Provider.GRAPHHOPPER,
        distance_km=Decimal("10.00"),
        duration_minutes=60,
        fuel_multiplier=Decimal("1.00"),
        geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
        route_facts=RouteFacts(
            provider=RouteOption.Provider.GRAPHHOPPER,
            has_tolls=True,
            toll_cost_rub=Decimal("0.00"),
        ),
    )

    result = EmissionCalculator(model_version="v2").calculate(routing_order, candidate, settings)
    details = result["calculation_details_json"]

    assert details["time_cost_rub"] == "900.00"
    assert details["toll_cost_rub"] == "0.00"
    assert result["cost_rub"] > EmissionCalculator(model_version="v1").calculate(
        routing_order,
        candidate,
        settings,
    )["cost_rub"]
    assert (
        "Маршрут содержит платные участки, но стоимость проезда не рассчитана провайдером "
        "и не включена в итоговую стоимость перевозки."
    ) in details["warnings"]


@pytest.mark.django_db
def test_emission_calculator_rejects_unknown_model_version():
    with pytest.raises(ValueError, match="Неподдерживаемая версия расчетной модели"):
        EmissionCalculator(model_version="v3")


@pytest.mark.django_db
def test_emission_calculator_v21_saves_intensity_fields_and_deduplicates_warnings(
    routing_order,
):
    settings = EcoCalculationSettings.get_current()
    warning = (
        "Маршрут содержит платные участки, но стоимость проезда не рассчитана провайдером "
        "и не включена в итоговую стоимость перевозки."
    )
    candidate = RouteCandidate(
        name="Маршрут GraphHopper",
        provider=RouteOption.Provider.GRAPHHOPPER,
        distance_km=Decimal("1500.00"),
        duration_minutes=1200,
        fuel_multiplier=Decimal("1.00"),
        geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
        route_facts=RouteFacts(
            provider=RouteOption.Provider.GRAPHHOPPER,
            has_tolls=True,
            toll_cost_rub=Decimal("0.00"),
            warnings=[warning, warning],
        ),
    )

    result = EmissionCalculator(model_version="v2.1").calculate(
        routing_order,
        candidate,
        settings,
    )
    details = result["calculation_details_json"]

    assert result["calculation_model_version"] == "v2.1"
    assert result["co2_kg"] > 0
    assert result["nox_g"] > 0
    assert result["pm_g"] > 0
    assert result["eco_rating"] > 0
    assert details["co2_kg_per_km"] != "0.000"
    assert details["nox_g_per_km"] != "0.000"
    assert details["pm_g_per_km"] != "0.0000"
    assert "co2_kg_per_ton_km" in details
    assert "nox_g_per_ton_km" in details
    assert "pm_g_per_ton_km" in details
    assert "emissions_score" in details
    assert details["route_risk_penalty"] == "0.00"
    assert details["eco_rating_method"] == "v2.1_intensity_plus_route_risk"
    assert details["warnings"].count(warning) == 1
    assert "Провайдер не предоставляет данные о пробках, traffic_factor=1.00." in details[
        "warnings"
    ]


@pytest.mark.django_db
def test_emission_calculator_v21_long_routes_do_not_all_collapse_to_zero(routing_order):
    settings = EcoCalculationSettings.get_current()
    candidates = [
        RouteCandidate(
            name="Вариант 1",
            provider=RouteOption.Provider.GRAPHHOPPER,
            distance_km=Decimal("1800.00"),
            duration_minutes=1440,
            fuel_multiplier=Decimal("1.00"),
            geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
        ),
        RouteCandidate(
            name="Вариант 2",
            provider=RouteOption.Provider.GRAPHHOPPER,
            distance_km=Decimal("1900.00"),
            duration_minutes=1520,
            fuel_multiplier=Decimal("1.00"),
            geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
        ),
    ]

    ratings = [
        EmissionCalculator(model_version="v2.1").calculate(
            routing_order,
            candidate,
            settings,
        )["eco_rating"]
        for candidate in candidates
    ]

    assert all(rating > 0 for rating in ratings)


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
    assert all(option.calculation_model_version == "v2.1" for option in route_options)
    assert all(
        option.calculation_details_json["calculation_model_version"] == "v2.1"
        for option in route_options
    )
    assert all("co2_kg_per_km" in option.calculation_details_json for option in route_options)
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


class MixedDistanceProvider:
    provider = RouteOption.Provider.GRAPHHOPPER

    def get_candidates(self, order):
        return [
            RouteCandidate(
                name="В пределах лимита",
                provider=RouteOption.Provider.GRAPHHOPPER,
                distance_km=Decimal("1999.00"),
                duration_minutes=1200,
                fuel_multiplier=Decimal("1.00"),
                geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
            ),
            RouteCandidate(
                name="За пределами лимита",
                provider=RouteOption.Provider.GRAPHHOPPER,
                distance_km=Decimal("2001.00"),
                duration_minutes=1300,
                fuel_multiplier=Decimal("1.00"),
                geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
            ),
        ]


class OverLimitProvider:
    provider = RouteOption.Provider.GRAPHHOPPER

    def get_candidates(self, order):
        return [
            RouteCandidate(
                name="За пределами лимита",
                provider=RouteOption.Provider.GRAPHHOPPER,
                distance_km=Decimal("2001.00"),
                duration_minutes=1300,
                fuel_multiplier=Decimal("1.00"),
                geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
            )
        ]


class StubGraphHopperClient:
    def __init__(self, response):
        self.response = response

    def route(self, points, **kwargs):
        return self.response


def _graphhopper_path_with_details():
    return {
        "distance": 20000,
        "time": 1200000,
        "points": {
            "coordinates": [
                [37.6173, 55.7558],
                [37.6000, 55.6000],
                [37.5447, 55.4312],
            ]
        },
        "details": {
            "road_class": [[0, 1, "motorway"], [1, 2, "primary"]],
            "toll": [[0, 1, False], [1, 2, True]],
        },
    }


@pytest.mark.django_db
def test_route_calculation_service_accepts_single_graphhopper_candidate(routing_order):
    route_options = RouteCalculationService(provider=OneCandidateProvider()).calculate_for_order(
        routing_order
    )

    assert len(route_options) == 1
    assert RouteOption.objects.filter(order=routing_order).count() == 1
    assert route_options[0].provider == RouteOption.Provider.GRAPHHOPPER
    assert route_options[0].fuel_multiplier == Decimal("1.15")
    assert route_options[0].calculation_model_version == "v2.1"
    assert route_options[0].route_facts_json["provider"] == RouteOption.Provider.GRAPHHOPPER


@pytest.mark.django_db
def test_route_calculation_service_filters_over_limit_candidates(routing_order):
    service = RouteCalculationService(provider=MixedDistanceProvider())

    route_options = service.calculate_for_order(routing_order)

    assert len(route_options) == 1
    assert route_options[0].name == "В пределах лимита"
    assert route_options[0].distance_km == Decimal("1999.00")
    assert "превышает поддерживаемую область расчета 2000 км" in service.last_warning
    assert service.last_found_count == 1


@pytest.mark.django_db
def test_route_calculation_service_rejects_all_over_limit_candidates_before_delete(
    routing_order,
):
    RouteCalculationService(provider=MockRouteProvider()).calculate_for_order(routing_order)
    old_ids = set(RouteOption.objects.filter(order=routing_order).values_list("id", flat=True))

    with pytest.raises(ValueError, match="Маршрут превышает поддерживаемую область расчета"):
        RouteCalculationService(provider=OverLimitProvider()).calculate_for_order(routing_order)

    new_ids = set(RouteOption.objects.filter(order=routing_order).values_list("id", flat=True))
    assert new_ids == old_ids


@pytest.mark.django_db
def test_route_calculation_service_stores_enriched_graphhopper_route_facts(
    routing_order,
    monkeypatch,
):
    def fake_get_route_provider(options):
        return GraphHopperRouteProvider(
            StubGraphHopperClient({"paths": [_graphhopper_path_with_details()]}),
            options=RouteCalculationOptions(
                max_candidates=3,
                alternative_max_paths=3,
                enable_path_details=True,
                path_details=("road_class", "toll"),
            ),
        )

    monkeypatch.setattr(
        "apps.routing.services.route_calculation_service.get_route_provider",
        fake_get_route_provider,
    )

    route_options = RouteCalculationService(calculation_mode="standard").calculate_for_order(
        routing_order
    )
    facts = route_options[0].route_facts_json

    assert len(route_options) == 1
    assert facts["provider"] == RouteOption.Provider.GRAPHHOPPER
    assert route_options[0].calculation_details_json["calculation_model_version"] == "v2.1"
    assert facts["has_tolls"] is True
    assert facts["road_details"]["requested_details"] == ["road_class", "toll"]
    assert "motorway" in facts["road_details"]["road_class_summary"]
    assert any(
        "не включена в итоговую стоимость перевозки" in warning
        for warning in facts["warnings"]
    )


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
