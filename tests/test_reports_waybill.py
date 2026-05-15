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
        username="waybill_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def other_manager():
    return User.objects.create_user(
        username="waybill_other_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="waybill_admin",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        username="waybill_superuser",
        email="waybill_superuser@example.com",
        password="StrongPass12345",
    )


@pytest.fixture
def transport():
    standard = EcoStandard.objects.create(
        name="Euro VI",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    return Transport.objects.create(
        plate_number="Р701РР777",
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
        name="Москва",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )
    destination = Location.objects.create(
        name="Подольск",
        latitude=Decimal("55.4312"),
        longitude=Decimal("37.5447"),
    )
    return origin, destination


def create_trip(manager, transport, locations, cargo_name="Оборудование"):
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
    return TripLifecycleService().approve_route(order, order.route_options.first(), manager)


@pytest.mark.django_db
def test_waybill_pdf_download_for_own_trip(client, manager, transport, locations):
    trip = create_trip(manager, transport, locations)
    client.force_login(manager)

    response = client.get(reverse("trips:waybill", kwargs={"pk": trip.pk}))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == f'attachment; filename="waybill_trip_{trip.pk}.pdf"'
    assert response.content.startswith(b"%PDF")
    trip.refresh_from_db()
    assert not trip.waybill_pdf


@pytest.mark.django_db
def test_waybill_anonymous_user_redirected_to_login(client, manager, transport, locations):
    trip = create_trip(manager, transport, locations)

    response = client.get(reverse("trips:waybill", kwargs={"pk": trip.pk}))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_waybill_for_another_manager_trip_returns_404(
    client, manager, other_manager, transport, locations
):
    trip = create_trip(other_manager, transport, locations)
    client.force_login(manager)

    response = client.get(reverse("trips:waybill", kwargs={"pk": trip.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_waybill_admin_and_superuser_get_403(
    client, manager, admin_user, superuser, transport, locations
):
    trip = create_trip(manager, transport, locations)

    for user in (admin_user, superuser):
        client.force_login(user)
        assert client.get(reverse("trips:waybill", kwargs={"pk": trip.pk})).status_code == 403
