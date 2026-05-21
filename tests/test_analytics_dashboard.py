from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.services.route_calculation_service import RouteCalculationService
from apps.trips.services import TripLifecycleService

User = get_user_model()


@pytest.fixture
def manager():
    return User.objects.create_user(
        username="analytics_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def other_manager():
    return User.objects.create_user(
        username="analytics_other_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="analytics_admin",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def transport():
    standard = EcoStandard.objects.create(
        name="Euro VI Analytics",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    return Transport.objects.create(
        plate_number="А700АА777",
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
        name="Москва аналитика",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )
    destination = Location.objects.create(
        name="Подольск аналитика",
        latitude=Decimal("55.4312"),
        longitude=Decimal("37.5447"),
    )
    return origin, destination


def create_order(manager, transport, locations, cargo_name="Груз аналитики"):
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
    return order


def create_trip(manager, transport, locations, cargo_name="Доставленный груз"):
    order = create_order(manager, transport, locations, cargo_name)
    RouteCalculationService().calculate_for_order(order)
    return TripLifecycleService().approve_route(order, order.route_options.first(), manager)


def deliver_trip(trip, manager):
    service = TripLifecycleService()
    service.start_trip(trip, manager)
    service.deliver_trip(trip, manager)
    trip.refresh_from_db()
    return trip


@pytest.mark.django_db
def test_manager_analytics_scopes_to_current_manager(
    client, manager, other_manager, transport, locations
):
    own_trip = deliver_trip(
        create_trip(manager, transport, locations, "Свой доставленный груз"),
        manager,
    )
    own_route = own_trip.route_option
    own_route.calculation_details_json = {
        "co2_kg_per_km": "0.500",
        "co2_kg_per_ton_km": "0.1000",
    }
    own_route.route_facts_json = {"has_tolls": True, "toll_cost_rub": "0.00"}
    own_route.save(update_fields=["calculation_details_json", "route_facts_json"])
    create_trip(manager, transport, locations, "Свой плановый груз")
    deliver_trip(
        create_trip(other_manager, transport, locations, "Чужой доставленный груз"),
        other_manager,
    )
    client.force_login(manager)

    response = client.get(reverse("dashboard:manager_analytics"))
    analytics = response.context["analytics"]
    content = response.content.decode()

    assert response.status_code == 200
    assert analytics["orders"]["total"] == 2
    assert analytics["trips"]["delivered"] == 1
    assert analytics["delivered"]["trips_count"] == 1
    assert analytics["delivered"]["co2_kg"] == own_trip.route_option.co2_kg
    assert analytics["delivered"]["average_co2_kg_per_km"] == "0.500"
    assert analytics["delivered"]["average_co2_kg_per_ton_km"] == "0.1000"
    assert analytics["delivered"]["toll_routes_count"] == 1
    assert "Свой доставленный груз" in content
    assert "Чужой доставленный груз" not in content
    assert "CO2 на км" in content
    assert "CO2 на тонно-км" in content
    assert "Платные участки" in content


@pytest.mark.django_db
def test_manager_analytics_empty_state(client, manager):
    client.force_login(manager)

    response = client.get(reverse("dashboard:manager_analytics"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Доставленных рейсов за выбранный период пока нет." in content
    assert response.context["analytics"]["delivered"]["average_co2_kg_per_km"] == "—"
    assert response.context["analytics"]["delivered"]["average_co2_kg_per_ton_km"] == "—"


@pytest.mark.django_db
def test_manager_analytics_access_rules(client, manager, admin_user):
    assert client.get(reverse("dashboard:manager_analytics")).status_code == 302

    client.force_login(admin_user)
    assert client.get(reverse("dashboard:manager_analytics")).status_code == 403

    client.force_login(manager)
    assert client.get(reverse("dashboard:manager_analytics")).status_code == 200


@pytest.mark.django_db
def test_admin_dashboard_contains_company_wide_data(
    client, admin_user, manager, other_manager, transport, locations
):
    first_trip = deliver_trip(create_trip(manager, transport, locations, "Груз менеджера"), manager)
    second_trip = deliver_trip(
        create_trip(other_manager, transport, locations, "Груз другого менеджера"),
        other_manager,
    )
    first_route = first_trip.route_option
    second_route = second_trip.route_option
    first_route.calculation_details_json = {
        "co2_kg_per_km": "0.500",
        "co2_kg_per_ton_km": "0.1000",
    }
    first_route.route_facts_json = {"has_tolls": True, "toll_cost_rub": "0.00"}
    first_route.save(update_fields=["calculation_details_json", "route_facts_json"])
    second_route.calculation_details_json = {
        "co2_kg_per_km": "1.000",
        "co2_kg_per_ton_km": "0.2000",
    }
    second_route.route_facts_json = {}
    second_route.save(update_fields=["calculation_details_json", "route_facts_json"])
    client.force_login(admin_user)

    response = client.get(reverse("dashboard:admin_dashboard"))
    analytics = response.context["analytics"]
    content = response.content.decode()

    assert response.status_code == 200
    assert analytics["users"]["managers"] == 2
    assert analytics["trips"]["delivered"] == 2
    assert analytics["company"]["trips_count"] == 2
    assert analytics["company"]["average_co2_kg_per_km"] == "0.750"
    assert analytics["company"]["average_co2_kg_per_ton_km"] == "0.1500"
    assert analytics["company"]["toll_routes_count"] == 1
    assert "Груз менеджера" in content
    assert "Груз другого менеджера" in content
    assert "Суммарные выбросы" in content
    assert "Средний эко-рейтинг" in content
    assert "<h2>Платные участки</h2>" not in content


@pytest.mark.django_db
def test_manager_cannot_access_admin_dashboard(client, manager):
    client.force_login(manager)

    response = client.get(reverse("dashboard:admin_dashboard"))

    assert response.status_code == 403
