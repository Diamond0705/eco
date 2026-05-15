from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.models import RouteOption
from apps.routing.services.route_calculation_service import RouteCalculationService
from apps.trips.services import TripLifecycleService

User = get_user_model()


@pytest.fixture
def manager():
    return User.objects.create_user(
        username="routing_view_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def other_manager():
    return User.objects.create_user(
        username="routing_view_other_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="routing_admin",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        username="routing_superuser",
        email="routing_superuser@example.com",
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
        plate_number="В111ВВ777",
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


def create_order(manager, transport, locations):
    origin, destination = locations
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
def test_manager_can_calculate_routes_for_own_order(client, manager, transport, locations):
    order = create_order(manager, transport, locations)
    client.force_login(manager)

    response = client.post(reverse("routing:calculate", kwargs={"pk": order.pk}))
    order.refresh_from_db()

    assert response.status_code == 302
    assert response["Location"] == reverse("routing:options", kwargs={"pk": order.pk})
    assert order.status == ShipmentOrder.Status.CALCULATED
    assert RouteOption.objects.filter(order=order).count() == 3


@pytest.mark.django_db
def test_manager_cannot_calculate_routes_for_another_manager_order(
    client, manager, other_manager, transport, locations
):
    order = create_order(other_manager, transport, locations)
    client.force_login(manager)

    response = client.post(reverse("routing:calculate", kwargs={"pk": order.pk}))

    assert response.status_code == 404
    assert RouteOption.objects.filter(order=order).count() == 0


@pytest.mark.django_db
def test_anonymous_user_is_redirected_to_login_for_route_pages(
    client, manager, transport, locations
):
    order = create_order(manager, transport, locations)

    calculate_response = client.post(reverse("routing:calculate", kwargs={"pk": order.pk}))
    options_response = client.get(reverse("routing:options", kwargs={"pk": order.pk}))

    assert calculate_response.status_code == 302
    assert calculate_response["Location"].startswith(reverse("accounts:login"))
    assert options_response.status_code == 302
    assert options_response["Location"].startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_admin_and_superuser_get_403_on_route_pages(
    client, manager, admin_user, superuser, transport, locations
):
    order = create_order(manager, transport, locations)

    for user in (admin_user, superuser):
        client.force_login(user)
        assert client.post(reverse("routing:calculate", kwargs={"pk": order.pk})).status_code == 403
        assert client.get(reverse("routing:options", kwargs={"pk": order.pk})).status_code == 403


@pytest.mark.django_db
def test_route_comparison_page_displays_route_options(client, manager, transport, locations):
    order = create_order(manager, transport, locations)
    RouteCalculationService().calculate_for_order(order)
    client.force_login(manager)

    response = client.get(reverse("routing:options", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Сравнение маршрутов" in content
    assert "Быстрый" in content
    assert "Короткий" in content
    assert "Экологичный" in content
    assert "Утвердить маршрут" in content


@pytest.mark.django_db
def test_route_comparison_page_includes_map_assets_and_route_data(
    client, manager, transport, locations
):
    order = create_order(manager, transport, locations)
    RouteCalculationService().calculate_for_order(order)
    client.force_login(manager)

    response = client.get(reverse("routing:options", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'id="route-map"' in content
    assert 'class="route-map"' in content
    assert "leaflet.css" in content
    assert "leaflet.js" in content
    assert "integrity=" not in content
    assert 'id="route-options-data"' in content
    assert "geometry_json" in content
    assert "Нет корректной геометрии для отображения маршрутов на карте." in content


@pytest.mark.django_db
def test_route_comparison_page_shows_approve_buttons_only_when_allowed(
    client, manager, transport, locations
):
    order = create_order(manager, transport, locations)
    RouteCalculationService().calculate_for_order(order)
    client.force_login(manager)

    calculated_response = client.get(reverse("routing:options", kwargs={"pk": order.pk}))
    calculated_content = calculated_response.content.decode()

    assert calculated_response.status_code == 200
    assert "Утвердить маршрут" in calculated_content

    TripLifecycleService().approve_route(order, order.route_options.first(), manager)

    planned_response = client.get(reverse("routing:options", kwargs={"pk": order.pk}))
    planned_content = planned_response.content.decode()

    assert planned_response.status_code == 200
    assert "Утвердить маршрут" not in planned_content
    assert "Маршрут утвержден" in planned_content
