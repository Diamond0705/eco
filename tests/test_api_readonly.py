from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.fleet.models import EcoCalculationSettings, EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.models import RouteOption
from apps.trips.models import Trip


@pytest.fixture
def users(db):
    user_model = get_user_model()
    manager = user_model.objects.create(
        username="manager_api",
        role="manager",
        first_name="Мария",
        last_name="Логистова",
        email="manager@example.test",
        phone="+79990000000",
        middle_name="Петровна",
    )
    other_manager = user_model.objects.create(
        username="other_manager_api",
        role="manager",
        first_name="Олег",
        last_name="Другой",
    )
    admin = user_model.objects.create(username="admin_api", role="admin")
    return manager, other_manager, admin


@pytest.fixture
def reference_data(db):
    standard = EcoStandard.objects.create(
        name="Euro VI",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    inactive_standard = EcoStandard.objects.create(
        name="Euro V",
        nox_limit_g_per_kwh=Decimal("2.00"),
        pm_limit_mg_per_kwh=Decimal("30.00"),
    )
    transport = Transport.objects.create(
        plate_number="А111АА777",
        model="KAMAZ 5490",
        category=Transport.Category.N3,
        fuel_type=Transport.FuelType.DIESEL,
        capacity_kg=12000,
        fuel_consumption_l_per_100km=Decimal("32.50"),
        eco_standard=standard,
        year=2024,
    )
    inactive_transport = Transport.objects.create(
        plate_number="В222ВВ777",
        model="Inactive",
        category=Transport.Category.N3,
        fuel_type=Transport.FuelType.DIESEL,
        capacity_kg=10000,
        fuel_consumption_l_per_100km=Decimal("30.00"),
        eco_standard=inactive_standard,
        year=2020,
        is_active=False,
    )
    pickup = Location.objects.create(
        name="Москва",
        address="Москва",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )
    delivery = Location.objects.create(
        name="Дмитров",
        address="Дмитров",
        latitude=Decimal("56.3440"),
        longitude=Decimal("37.5200"),
    )
    Location.objects.create(
        name="Неактивная",
        address="Скрытая",
        latitude=Decimal("55.0000"),
        longitude=Decimal("37.0000"),
        is_active=False,
    )
    return {
        "transport": transport,
        "inactive_transport": inactive_transport,
        "pickup": pickup,
        "delivery": delivery,
    }


def create_order(
    manager,
    transport,
    pickup,
    delivery,
    inactive_transport=None,
    *,
    status=ShipmentOrder.Status.COMPLETED,
):
    order = ShipmentOrder.objects.create(
        manager=manager,
        transport=transport,
        cargo_name="Стальные трубы",
        cargo_type="Металл",
        cargo_weight_kg=Decimal("5000.00"),
        desired_delivery_date=timezone.localdate(),
        status=status,
    )
    OrderPoint.objects.create(
        order=order,
        location=pickup,
        sequence=1,
        point_type=OrderPoint.PointType.PICKUP,
    )
    OrderPoint.objects.create(
        order=order,
        location=delivery,
        sequence=2,
        point_type=OrderPoint.PointType.DELIVERY,
    )
    return order


def create_route(order, *, selected=True, details=None):
    return RouteOption.objects.create(
        order=order,
        name="Маршрут GraphHopper",
        provider=RouteOption.Provider.GRAPHHOPPER,
        distance_km=Decimal("100.00"),
        duration_minutes=120,
        fuel_multiplier=Decimal("1.00"),
        fuel_liters=Decimal("32.50"),
        cost_rub=Decimal("10000.00"),
        co2_kg=Decimal("80.00"),
        nox_g=Decimal("24.00"),
        pm_g=Decimal("0.400"),
        eco_rating=Decimal("75.00"),
        geometry_json=[[55.7558, 37.6173], [56.3440, 37.5200]],
        route_facts_json={"provider": "graphhopper", "raw": "hidden"},
        calculation_model_version="v2.1",
        calculation_details_json=details
        if details is not None
        else {
            "calculation_model_version": "v2.1",
            "co2_kg_per_km": "0.800",
            "co2_kg_per_ton_km": "0.1600",
            "internal_multiplier": "hidden",
        },
        calculation_settings=EcoCalculationSettings.get_current(),
        is_selected=selected,
    )


def create_trip(order, route, *, status=Trip.Status.DELIVERED, days_offset=0):
    finish_at = timezone.now() + timezone.timedelta(days=days_offset)
    return Trip.objects.create(
        order=order,
        route_option=route,
        status=status,
        planned_start_at=finish_at - timezone.timedelta(hours=4),
        actual_start_at=finish_at - timezone.timedelta(hours=3),
        actual_finish_at=finish_at,
    )


def test_anonymous_api_access_is_rejected(client):
    response = client.get(reverse("api:locations"))

    assert response.status_code == 401


@pytest.mark.django_db
def test_locations_endpoint_returns_only_active_locations(client, users, reference_data):
    manager, _other_manager, _admin = users
    client.force_login(manager)

    response = client.get(reverse("api:locations"))

    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"Москва", "Дмитров"}


@pytest.mark.django_db
def test_transports_endpoint_returns_only_active_transport(client, users, reference_data):
    manager, _other_manager, _admin = users
    client.force_login(manager)

    response = client.get(reverse("api:transports"))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["plate_number"] == "А111АА777"
    assert payload[0]["eco_standard"]["name"] == "Euro VI"


@pytest.mark.django_db
def test_manager_lists_only_own_orders(client, users, reference_data):
    manager, other_manager, _admin = users
    create_order(manager, **reference_data)
    create_order(other_manager, **reference_data)
    client.force_login(manager)

    response = client.get(reverse("api:orders"))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["manager"]["username"] == "manager_api"
    assert "email" not in payload[0]["manager"]
    assert "phone" not in payload[0]["manager"]
    assert "middle_name" not in payload[0]["manager"]


@pytest.mark.django_db
def test_manager_cannot_access_another_manager_order_detail(client, users, reference_data):
    manager, other_manager, _admin = users
    other_order = create_order(other_manager, **reference_data)
    client.force_login(manager)

    response = client.get(reverse("api:order_detail", args=[other_order.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_admin_lists_all_orders(client, users, reference_data):
    manager, other_manager, admin = users
    create_order(manager, **reference_data)
    create_order(other_manager, **reference_data)
    client.force_login(admin)

    response = client.get(reverse("api:orders"))

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.django_db
def test_order_detail_contains_safe_route_snapshot_summary(client, users, reference_data):
    manager, _other_manager, _admin = users
    order = create_order(manager, **reference_data)
    create_route(order)
    client.force_login(manager)

    response = client.get(reverse("api:order_detail", args=[order.pk]))

    assert response.status_code == 200
    payload = response.json()
    route = payload["route_options"][0]
    assert payload["points"][0]["location"]["name"] == "Москва"
    assert route["distance_km"] == "100.00"
    assert route["co2_kg_per_km"] == "0.800"
    assert route["co2_kg_per_ton_km"] == "0.1600"
    assert "calculation_details_json" not in route
    assert "route_facts_json" not in route
    assert "geometry_json" not in route
    assert "provider" not in route


@pytest.mark.django_db
def test_trips_endpoint_respects_scope_status_and_date_filters(client, users, reference_data):
    manager, other_manager, _admin = users
    own_order = create_order(manager, **reference_data)
    own_route = create_route(own_order)
    own_trip = create_trip(own_order, own_route, status=Trip.Status.DELIVERED, days_offset=-1)
    planned_order = create_order(manager, **reference_data, status=ShipmentOrder.Status.PLANNED)
    planned_route = create_route(planned_order)
    create_trip(planned_order, planned_route, status=Trip.Status.PLANNED)
    other_order = create_order(other_manager, **reference_data)
    other_route = create_route(other_order)
    create_trip(other_order, other_route, status=Trip.Status.DELIVERED, days_offset=-1)
    client.force_login(manager)

    response = client.get(
        reverse("api:trips"),
        {
            "status": Trip.Status.DELIVERED,
            "date_from": (timezone.localdate() - timezone.timedelta(days=2)).isoformat(),
            "date_to": timezone.localdate().isoformat(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [own_trip.pk]
    assert payload[0]["planned_finish"] is None
    assert payload[0]["manager"]["username"] == "manager_api"


@pytest.mark.django_db
def test_analytics_summary_uses_saved_route_snapshots(client, users, reference_data):
    manager, other_manager, admin = users
    own_order = create_order(manager, **reference_data)
    own_route = create_route(
        own_order,
        details={"co2_kg_per_km": "0.800", "co2_kg_per_ton_km": "0.1600"},
    )
    create_trip(own_order, own_route)
    other_order = create_order(other_manager, **reference_data)
    other_route = create_route(
        other_order,
        details={"co2_kg_per_km": "1.200", "co2_kg_per_ton_km": "0.2400"},
    )
    create_trip(other_order, other_route)

    client.force_login(manager)
    manager_response = client.get(reverse("api:analytics_summary"))
    client.force_login(admin)
    admin_response = client.get(reverse("api:analytics_summary"))

    assert manager_response.status_code == 200
    assert manager_response.json()["delivered_trips_count"] == 1
    assert manager_response.json()["total_distance_km"] == "100.00"
    assert manager_response.json()["average_co2_kg_per_km"] == "0.800"
    assert admin_response.status_code == 200
    assert admin_response.json()["delivered_trips_count"] == 2
    assert admin_response.json()["total_distance_km"] == "200.00"
    assert admin_response.json()["average_co2_kg_per_km"] == "1.000"


@pytest.mark.django_db
def test_api_write_methods_return_405(client, users, reference_data):
    manager, _other_manager, _admin = users
    order = create_order(manager, **reference_data)
    route = create_route(order)
    create_trip(order, route)
    client.force_login(manager)
    urls = [
        reverse("api:locations"),
        reverse("api:transports"),
        reverse("api:orders"),
        reverse("api:order_detail", args=[order.pk]),
        reverse("api:trips"),
        reverse("api:analytics_summary"),
    ]

    for url in urls:
        assert client.post(url, {}).status_code == 405
        assert client.put(url, {}, content_type="application/json").status_code == 405
        assert client.patch(url, {}, content_type="application/json").status_code == 405
        assert client.delete(url).status_code == 405
