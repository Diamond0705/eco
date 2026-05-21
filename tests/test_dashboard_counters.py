from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.trips.models import Trip
from tests.test_analytics_dashboard import create_order, create_trip, deliver_trip

User = get_user_model()


@pytest.fixture
def manager():
    return User.objects.create_user(
        username="dashboard_counter_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="dashboard_counter_admin",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def transport():
    standard = EcoStandard.objects.create(
        name="Euro VI Dashboard Counters",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    return Transport.objects.create(
        plate_number="А701АА777",
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
        name="Москва счетчики",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )
    destination = Location.objects.create(
        name="Подольск счетчики",
        latitude=Decimal("55.4312"),
        longitude=Decimal("37.5447"),
    )
    return origin, destination


@pytest.mark.django_db
def test_manager_dashboard_shows_real_counters(client, manager, transport, locations):
    create_order(manager, transport, locations, "Новая заявка")
    delivered_trip = deliver_trip(
        create_trip(manager, transport, locations, "Доставленный груз"),
        manager,
    )
    client.force_login(manager)

    response = client.get(reverse("dashboard:manager_dashboard"))
    analytics = response.context["analytics"]
    content = response.content.decode()

    assert response.status_code == 200
    assert analytics["orders"]["total"] == 2
    assert analytics["trips"]["delivered"] == 1
    assert analytics["delivered"]["co2_kg"] == delivered_trip.route_option.co2_kg
    assert "Мои заявки" in content
    assert "CO2 доставленных" in content


@pytest.mark.django_db
def test_admin_dashboard_shows_real_counters(client, admin_user, manager, transport, locations):
    deliver_trip(create_trip(manager, transport, locations, "Админский счетчик"), manager)
    client.force_login(admin_user)

    response = client.get(reverse("dashboard:admin_dashboard"))
    analytics = response.context["analytics"]
    content = response.content.decode()

    assert response.status_code == 200
    assert analytics["orders"]["total"] == 1
    assert analytics["trips"]["total"] == 1
    assert analytics["trips"]["delivered"] == 1
    assert analytics["company"]["trips_count"] == 1
    assert "average_co2_kg_per_km" in analytics["company"]
    assert "average_co2_kg_per_ton_km" in analytics["company"]
    assert "toll_routes_count" in analytics["company"]
    assert "Панель администратора" in content
    assert "Суммарные выбросы" in content
    assert "CO2 на км" in content


@pytest.mark.django_db
def test_manager_dashboard_counts_active_trips(client, manager, transport, locations):
    create_trip(manager, transport, locations, "Плановый рейс")
    in_progress_trip = create_trip(manager, transport, locations, "Рейс в пути")
    from apps.trips.services import TripLifecycleService

    TripLifecycleService().start_trip(in_progress_trip, manager)
    client.force_login(manager)

    response = client.get(reverse("dashboard:manager_dashboard"))
    analytics = response.context["analytics"]

    assert response.status_code == 200
    assert analytics["trips"]["planned"] == 1
    assert analytics["trips"]["in_progress"] == 1
    assert analytics["trips"]["active"] == 2
    assert Trip.objects.filter(status=Trip.Status.DELIVERED).count() == 0
