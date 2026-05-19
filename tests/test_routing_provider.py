import json
from decimal import Decimal
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth import get_user_model

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.models import RouteOption
from apps.routing.services.graphhopper_client import GraphHopperClient
from apps.routing.services.graphhopper_provider import GraphHopperRouteProvider
from apps.routing.services.mock_provider import MockRouteProvider
from apps.routing.services.providers import (
    RouteCalculationOptions,
    RouteFacts,
    RoutingProviderResponseError,
)

User = get_user_model()


def test_route_facts_neutral_returns_json_safe_defaults():
    facts = RouteFacts.neutral(RouteOption.Provider.MOCK)

    assert facts.provider == RouteOption.Provider.MOCK
    assert facts.supports_traffic is False
    assert facts.traffic_delay_minutes == 0
    assert facts.has_tolls is False
    assert facts.toll_cost_rub == Decimal("0.00")
    assert facts.has_restriction_warnings is False
    assert facts.restriction_warnings == []
    assert facts.road_details == {}
    assert facts.warnings == []

    assert facts.to_json() == {
        "schema_version": 1,
        "provider": RouteOption.Provider.MOCK,
        "supports_traffic": False,
        "traffic_delay_minutes": 0,
        "has_tolls": False,
        "toll_cost_rub": "0.00",
        "has_restriction_warnings": False,
        "restriction_warnings": [],
        "road_details": {},
        "warnings": [],
    }


def test_route_facts_to_json_contains_no_raw_provider_response():
    facts = RouteFacts(
        provider=RouteOption.Provider.GRAPHHOPPER,
        warnings=["Данные о пробках не поддерживаются текущей интеграцией."],
    )

    payload = facts.to_json()

    assert "paths" not in payload
    assert "raw_response" not in payload
    assert payload["provider"] == RouteOption.Provider.GRAPHHOPPER
    assert payload["warnings"] == ["Данные о пробках не поддерживаются текущей интеграцией."]


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


def test_mock_route_provider_exposes_phase_10_capabilities():
    capabilities = MockRouteProvider.capabilities

    assert capabilities.provider == RouteOption.Provider.MOCK
    assert capabilities.is_demo_provider is True
    assert capabilities.supports_real_geometry is False
    assert capabilities.supports_alternatives is True
    assert capabilities.supports_traffic is False
    assert capabilities.supports_truck_routing is False
    assert capabilities.supports_tolls is False
    assert capabilities.supports_toll_costs is False
    assert capabilities.supports_road_incidents is False
    assert capabilities.supports_low_emission_zones is False
    assert capabilities.supports_road_details is False


@pytest.mark.django_db
def test_mock_route_provider_candidates_include_neutral_route_facts(route_order):
    candidates = MockRouteProvider().get_candidates(route_order)

    assert all(
        candidate.route_facts.provider == RouteOption.Provider.MOCK
        for candidate in candidates
    )
    assert all(
        candidate.route_facts.to_json()["toll_cost_rub"] == "0.00"
        for candidate in candidates
    )


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


class FakeGraphHopperResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_graphhopper_client_builds_route_request_without_real_network():
    captured = {}

    def fake_opener(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeGraphHopperResponse({"paths": []})

    client = GraphHopperClient(
        api_key="test-key",
        base_url="https://graphhopper.test/api/1",
        profile="car",
        timeout_seconds=7,
        opener=fake_opener,
    )

    response = client.route([[37.6173, 55.7558], [37.5447, 55.4312]])
    request = captured["request"]
    parsed_url = urlparse(request.full_url)
    payload = json.loads(request.data.decode("utf-8"))

    assert response == {"paths": []}
    assert request.get_method() == "POST"
    assert parsed_url.path == "/api/1/route"
    assert parse_qs(parsed_url.query) == {"key": ["test-key"]}
    assert captured["timeout"] == 7
    assert payload["points"] == [[37.6173, 55.7558], [37.5447, 55.4312]]
    assert payload["profile"] == "car"
    assert payload["points_encoded"] is False
    assert payload["calc_points"] is True
    assert payload["instructions"] is False
    assert payload["algorithm"] == "alternative_route"
    assert payload["alternative_route.max_paths"] == 3
    assert "details" not in payload


def test_graphhopper_client_sends_path_details_without_real_network():
    captured = {}

    def fake_opener(request, timeout):
        captured["request"] = request
        return FakeGraphHopperResponse({"paths": []})

    client = GraphHopperClient(
        api_key="test-key",
        base_url="https://graphhopper.test/api/1",
        profile="car",
        timeout_seconds=7,
        opener=fake_opener,
    )

    client.route(
        [[37.6173, 55.7558], [37.5447, 55.4312]],
        path_details=["road_class", "toll"],
    )

    payload = json.loads(captured["request"].data.decode("utf-8"))
    assert payload["details"] == ["road_class", "toll"]


def test_graphhopper_client_omits_empty_path_details_without_real_network():
    captured = {}

    def fake_opener(request, timeout):
        captured["request"] = request
        return FakeGraphHopperResponse({"paths": []})

    client = GraphHopperClient(
        api_key="test-key",
        base_url="https://graphhopper.test/api/1",
        profile="car",
        timeout_seconds=7,
        opener=fake_opener,
    )

    client.route([[37.6173, 55.7558], [37.5447, 55.4312]], path_details=[])

    payload = json.loads(captured["request"].data.decode("utf-8"))
    assert "details" not in payload


def test_graphhopper_client_sends_alternative_route_settings_without_real_network():
    captured = {}

    def fake_opener(request, timeout):
        captured["request"] = request
        return FakeGraphHopperResponse({"paths": []})

    client = GraphHopperClient(
        api_key="test-key",
        base_url="https://graphhopper.test/api/1",
        profile="car",
        timeout_seconds=7,
        opener=fake_opener,
    )

    client.route(
        [[37.6173, 55.7558], [37.5447, 55.4312]],
        alternative_max_paths=5,
        alternative_max_weight_factor=1.6,
        alternative_max_share_factor=0.7,
    )

    payload = json.loads(captured["request"].data.decode("utf-8"))
    assert payload["algorithm"] == "alternative_route"
    assert payload["alternative_route.max_paths"] == 5
    assert payload["alternative_route.max_weight_factor"] == 1.6
    assert payload["alternative_route.max_share_factor"] == 0.7


def test_graphhopper_client_sends_strategy_custom_model_without_real_network():
    captured = {}

    def fake_opener(request, timeout):
        captured["request"] = request
        return FakeGraphHopperResponse({"paths": []})

    client = GraphHopperClient(
        api_key="test-key",
        base_url="https://graphhopper.test/api/1",
        profile="car",
        timeout_seconds=7,
        opener=fake_opener,
    )
    custom_model = {"distance_influence": 120}

    client.route(
        [[37.6173, 55.7558], [37.5447, 55.4312]],
        custom_model=custom_model,
        use_alternative_route=False,
    )

    payload = json.loads(captured["request"].data.decode("utf-8"))
    assert "algorithm" not in payload
    assert payload["ch.disable"] is True
    assert payload["custom_model"] == custom_model


def test_graphhopper_client_wraps_network_errors_without_real_call():
    def fake_opener(request, timeout):
        raise URLError("network is blocked in test")

    client = GraphHopperClient(
        api_key="test-key",
        base_url="https://graphhopper.test/api/1",
        profile="car",
        timeout_seconds=7,
        opener=fake_opener,
    )

    with pytest.raises(RoutingProviderResponseError):
        client.route([[37.6173, 55.7558], [37.5447, 55.4312]])


def test_graphhopper_route_provider_exposes_phase_11_capabilities():
    provider = GraphHopperRouteProvider(
        StubGraphHopperClient({"paths": []}),
        options=RouteCalculationOptions(
            enable_path_details=True,
            path_details=("road_class", "toll"),
        ),
    )
    capabilities = provider.capabilities

    assert capabilities.provider == RouteOption.Provider.GRAPHHOPPER
    assert capabilities.is_demo_provider is False
    assert capabilities.supports_real_geometry is True
    assert capabilities.supports_alternatives is True
    assert capabilities.supports_traffic is False
    assert capabilities.supports_truck_routing is False
    assert capabilities.supports_tolls is True
    assert capabilities.supports_toll_costs is False
    assert capabilities.supports_road_incidents is False
    assert capabilities.supports_low_emission_zones is False
    assert capabilities.supports_road_details is True


class StubGraphHopperClient:
    def __init__(self, response, *extra_responses):
        self.responses = [response, *extra_responses]
        self.points = None
        self.calls = []

    def route(self, points, **kwargs):
        self.points = points
        self.calls.append({"points": points, **kwargs})
        if len(self.responses) > 1:
            return self.responses.pop(0)
        return self.responses[0]


@pytest.mark.django_db
def test_graphhopper_provider_returns_one_candidate_for_one_path(route_order):
    client = StubGraphHopperClient(
        {
            "paths": [
                {
                    "distance": 12345.6,
                    "time": 90000,
                    "points": {
                        "coordinates": [
                            [37.6173, 55.7558, 180],
                            [37.5447, 55.4312],
                        ]
                    },
                }
            ]
        }
    )

    candidates = GraphHopperRouteProvider(client).get_candidates(route_order)

    assert client.points == [[37.6173, 55.7558], [37.5447, 55.4312]]
    assert client.calls[0]["alternative_max_paths"] == 3
    assert len(candidates) == 1
    assert candidates[0].name == "Маршрут GraphHopper"
    assert candidates[0].provider == RouteOption.Provider.GRAPHHOPPER
    assert candidates[0].distance_km == Decimal("12.35")
    assert candidates[0].duration_minutes == 2
    assert candidates[0].fuel_multiplier == Decimal("1.00")
    assert candidates[0].geometry_json == [[55.7558, 37.6173], [55.4312, 37.5447]]
    assert candidates[0].route_facts.provider == RouteOption.Provider.GRAPHHOPPER
    assert candidates[0].route_facts.to_json()["has_tolls"] is False


@pytest.mark.django_db
def test_graphhopper_provider_returns_two_candidates_without_padding(route_order):
    client = StubGraphHopperClient(
        {
            "paths": [
                {
                    "distance": 10000,
                    "time": 200000,
                    "points": {"coordinates": [[37.6173, 55.7558], [37.5447, 55.4312]]},
                },
                {
                    "distance": 12000,
                    "time": 100000,
                    "points": {"coordinates": [[37.6173, 55.7558], [37.6, 55.5]]},
                },
            ]
        }
    )

    candidates = GraphHopperRouteProvider(client).get_candidates(route_order)

    assert len(candidates) == 2
    assert [candidate.name for candidate in candidates] == [
        "Маршрут GraphHopper",
        "Альтернативный маршрут 1",
    ]
    assert all(candidate.provider == RouteOption.Provider.GRAPHHOPPER for candidate in candidates)
    assert all(candidate.fuel_multiplier == Decimal("1.00") for candidate in candidates)
    assert all(
        candidate.route_facts.provider == RouteOption.Provider.GRAPHHOPPER
        for candidate in candidates
    )


@pytest.mark.django_db
def test_graphhopper_provider_parses_path_detail_summaries(route_order):
    details = {
        "road_class": [[0, 1, "motorway"], [1, 2, "primary"]],
        "road_environment": [[0, 1, "road"], [1, 2, "urban"]],
        "surface": [[0, 1, "asphalt"], [1, 2, "paved"]],
        "max_speed": [[0, 1, 90], [1, 2, 60]],
        "toll": [[0, 1, False], [1, 2, True]],
    }
    client = StubGraphHopperClient(
        {
            "paths": [
                _graphhopper_path(
                    20000,
                    1200000,
                    [[37.6173, 55.7558], [37.6000, 55.6000], [37.5447, 55.4312]],
                    details=details,
                )
            ]
        }
    )
    options = RouteCalculationOptions(
        enable_path_details=True,
        path_details=("road_class", "road_environment", "surface", "max_speed", "toll"),
    )

    candidates = GraphHopperRouteProvider(client, options=options).get_candidates(route_order)
    facts = candidates[0].route_facts.to_json()
    road_details = facts["road_details"]

    assert client.calls[0]["path_details"] == (
        "road_class",
        "road_environment",
        "surface",
        "max_speed",
        "toll",
    )
    assert road_details["requested_details"] == [
        "road_class",
        "road_environment",
        "surface",
        "max_speed",
        "toll",
    ]
    assert road_details["available_details"] == [
        "road_class",
        "road_environment",
        "surface",
        "max_speed",
        "toll",
    ]
    assert "motorway" in road_details["road_class_summary"]
    assert "urban" in road_details["road_environment_summary"]
    assert "asphalt" in road_details["surface_summary"]
    assert "90" in road_details["max_speed_summary"]
    assert "true" in road_details["toll_summary"]
    assert facts["has_tolls"] is True
    assert facts["toll_cost_rub"] == "0.00"
    assert any("стоимость проезда не рассчитывается" in warning for warning in facts["warnings"])


@pytest.mark.django_db
def test_graphhopper_provider_missing_path_details_do_not_break_candidates(route_order):
    client = StubGraphHopperClient(
        {
            "paths": [
                _graphhopper_path(
                    10000,
                    100000,
                    [[37.6173, 55.7558], [37.5447, 55.4312]],
                )
            ]
        }
    )
    options = RouteCalculationOptions(
        enable_path_details=True,
        path_details=("road_class", "toll"),
    )

    candidates = GraphHopperRouteProvider(client, options=options).get_candidates(route_order)
    facts = candidates[0].route_facts.to_json()

    assert len(candidates) == 1
    assert facts["road_details"] == {
        "requested_details": ["road_class", "toll"],
        "available_details": [],
    }
    assert facts["has_tolls"] is False
    assert "GraphHopper не вернул дорожные детали для этого маршрута." in facts["warnings"]


@pytest.mark.django_db
def test_graphhopper_provider_does_not_duplicate_fastest_shortest_route(route_order):
    client = StubGraphHopperClient(
        {
            "paths": [
                {
                    "distance": 10000,
                    "time": 100000,
                    "points": {"coordinates": [[37.6173, 55.7558], [37.5447, 55.4312]]},
                },
                {
                    "distance": 12000,
                    "time": 130000,
                    "points": {"coordinates": [[37.6173, 55.7558], [37.6, 55.5]]},
                },
            ]
        }
    )

    candidates = GraphHopperRouteProvider(client).get_candidates(route_order)

    assert len(candidates) == 2
    assert [candidate.name for candidate in candidates] == [
        "Маршрут GraphHopper",
        "Альтернативный маршрут 1",
    ]


def _graphhopper_path(distance, duration, coordinates, details=None):
    path = {
        "distance": distance,
        "time": duration,
        "points": {"coordinates": coordinates},
    }
    if details is not None:
        path["details"] = details
    return path


@pytest.mark.django_db
def test_graphhopper_provider_returns_three_candidates_when_three_paths_exist(route_order):
    client = StubGraphHopperClient(
        {
            "paths": [
                _graphhopper_path(10000, 100000, [[37.6173, 55.7558], [37.5447, 55.4312]]),
                _graphhopper_path(11000, 120000, [[37.6173, 55.7558], [37.59, 55.51]]),
                _graphhopper_path(12000, 140000, [[37.6173, 55.7558], [37.57, 55.48]]),
            ]
        }
    )

    candidates = GraphHopperRouteProvider(client).get_candidates(route_order)

    assert len(candidates) == 3
    assert [candidate.name for candidate in candidates] == [
        "Маршрут GraphHopper",
        "Альтернативный маршрут 1",
        "Альтернативный маршрут 2",
    ]


@pytest.mark.django_db
def test_graphhopper_provider_deduplicates_paths_without_padding_to_target(route_order):
    duplicated = _graphhopper_path(
        10000,
        100000,
        [[37.6173, 55.7558], [37.5447, 55.4312]],
    )
    client = StubGraphHopperClient({"paths": [duplicated, duplicated]})

    candidates = GraphHopperRouteProvider(client).get_candidates(route_order)

    assert len(candidates) == 1


@pytest.mark.django_db
def test_graphhopper_provider_caps_candidates_at_five(route_order):
    client = StubGraphHopperClient(
        {
            "paths": [
                _graphhopper_path(
                    10000 + index * 100,
                    100000 + index * 10000,
                    [[37.6173, 55.7558], [37.54 + index / 100, 55.43 + index / 100]],
                )
                for index in range(6)
            ]
        }
    )
    options = RouteCalculationOptions(max_candidates=5, alternative_max_paths=5)

    candidates = GraphHopperRouteProvider(client, options=options).get_candidates(route_order)

    assert len(candidates) == 5


@pytest.mark.django_db
def test_graphhopper_provider_standard_mode_does_not_use_strategy_requests(route_order):
    client = StubGraphHopperClient(
        {
            "paths": [
                _graphhopper_path(10000, 100000, [[37.6173, 55.7558], [37.5447, 55.4312]])
            ]
        },
        {
            "paths": [
                _graphhopper_path(12000, 120000, [[37.6173, 55.7558], [37.57, 55.48]])
            ]
        },
    )
    options = RouteCalculationOptions(
        mode="standard",
        requested_candidates=3,
        target_candidates=3,
        max_candidates=3,
        alternative_max_paths=3,
        enable_strategy_requests=False,
        max_strategy_requests=0,
    )

    candidates = GraphHopperRouteProvider(client, options=options).get_candidates(route_order)

    assert len(candidates) == 1
    assert len(client.calls) == 1
    assert client.calls[0]["alternative_max_paths"] == 3


@pytest.mark.django_db
def test_graphhopper_provider_extended_mode_uses_limited_strategy_requests(route_order):
    client = StubGraphHopperClient(
        {
            "paths": [
                _graphhopper_path(10000, 100000, [[37.6173, 55.7558], [37.5447, 55.4312]])
            ]
        },
        {
            "paths": [
                _graphhopper_path(10000, 100000, [[37.6173, 55.7558], [37.5447, 55.4312]])
            ]
        },
        {
            "paths": [
                _graphhopper_path(12000, 120000, [[37.6173, 55.7558], [37.57, 55.48]])
            ]
        },
        {
            "paths": [
                _graphhopper_path(13000, 130000, [[37.6173, 55.7558], [37.58, 55.49]])
            ]
        },
    )
    options = RouteCalculationOptions(
        mode="extended",
        requested_candidates=5,
        target_candidates=3,
        max_candidates=5,
        alternative_max_paths=5,
        enable_strategy_requests=True,
        max_strategy_requests=2,
    )

    candidates = GraphHopperRouteProvider(client, options=options).get_candidates(route_order)

    assert len(candidates) == 2
    assert len(client.calls) == 3
    assert client.calls[0]["alternative_max_paths"] == 5
    assert client.calls[1]["use_alternative_route"] is False
    assert client.calls[2]["use_alternative_route"] is False
