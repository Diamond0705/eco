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
def api_users(db):
    user_model = get_user_model()
    manager = user_model.objects.create_user(
        username="jwt_manager",
        password="StrongPass12345",
        role="manager",
        first_name="Jwt",
        last_name="Manager",
        email="jwt-manager@example.test",
        phone="+79990000000",
        middle_name="Hidden",
    )
    other_manager = user_model.objects.create_user(
        username="jwt_other_manager",
        password="StrongPass12345",
        role="manager",
    )
    return manager, other_manager


@pytest.fixture
def api_reference(db):
    standard = EcoStandard.objects.create(
        name="JWT Euro VI",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    transport = Transport.objects.create(
        plate_number="JWT001",
        model="JWT Truck",
        category=Transport.Category.N3,
        fuel_type=Transport.FuelType.DIESEL,
        capacity_kg=12000,
        fuel_consumption_l_per_100km=Decimal("30.00"),
        eco_standard=standard,
        year=2024,
    )
    pickup = Location.objects.create(
        name="JWT Pickup",
        address="Pickup",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )
    delivery = Location.objects.create(
        name="JWT Delivery",
        address="Delivery",
        latitude=Decimal("56.3440"),
        longitude=Decimal("37.5200"),
    )
    return transport, pickup, delivery


def create_order(manager, transport, pickup, delivery, *, status=ShipmentOrder.Status.COMPLETED):
    order = ShipmentOrder.objects.create(
        manager=manager,
        transport=transport,
        cargo_name="JWT cargo",
        cargo_type="Metal",
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


def create_route(order):
    return RouteOption.objects.create(
        order=order,
        name="JWT route",
        provider=RouteOption.Provider.GRAPHHOPPER,
        distance_km=Decimal("100.00"),
        duration_minutes=120,
        fuel_multiplier=Decimal("1.00"),
        fuel_liters=Decimal("30.00"),
        cost_rub=Decimal("10000.00"),
        co2_kg=Decimal("80.00"),
        nox_g=Decimal("24.00"),
        pm_g=Decimal("0.400"),
        eco_rating=Decimal("75.00"),
        geometry_json=[[55.7558, 37.6173], [56.3440, 37.5200]],
        route_facts_json={"provider": "graphhopper", "raw": "hidden"},
        calculation_model_version="v2.1",
        calculation_details_json={
            "co2_kg_per_km": "0.800",
            "co2_kg_per_ton_km": "0.1600",
            "secret_detail": "hidden",
        },
        calculation_settings=EcoCalculationSettings.get_current(),
        is_selected=True,
    )


def create_trip(order, route, *, status=Trip.Status.DELIVERED):
    return Trip.objects.create(
        order=order,
        route_option=route,
        status=status,
        planned_start_at=timezone.now(),
        actual_start_at=timezone.now(),
        actual_finish_at=timezone.now(),
    )


def auth_header(access_token):
    return {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}


def obtain_access_token(client, user):
    response = client.post(
        reverse("api:token_obtain_pair"),
        {"username": user.username, "password": "StrongPass12345"},
        content_type="application/json",
    )
    assert response.status_code == 200
    return response.json()["access"]


@pytest.mark.django_db
def test_token_obtain_succeeds_for_valid_active_user(client, api_users):
    manager, _other_manager = api_users

    response = client.post(
        reverse("api:token_obtain_pair"),
        {"username": manager.username, "password": "StrongPass12345"},
        content_type="application/json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"access", "refresh"}


@pytest.mark.django_db
def test_token_obtain_fails_for_invalid_credentials(client, api_users):
    manager, _other_manager = api_users

    response = client.post(
        reverse("api:token_obtain_pair"),
        {"username": manager.username, "password": "wrong"},
        content_type="application/json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_token_refresh_and_verify_work(client, api_users):
    manager, _other_manager = api_users
    token_response = client.post(
        reverse("api:token_obtain_pair"),
        {"username": manager.username, "password": "StrongPass12345"},
        content_type="application/json",
    )
    refresh = token_response.json()["refresh"]

    refresh_response = client.post(
        reverse("api:token_refresh"),
        {"refresh": refresh},
        content_type="application/json",
    )
    verify_response = client.post(
        reverse("api:token_verify"),
        {"token": refresh_response.json()["access"]},
        content_type="application/json",
    )

    assert refresh_response.status_code == 200
    assert "access" in refresh_response.json()
    assert verify_response.status_code == 200


@pytest.mark.django_db
def test_jwt_authenticated_client_can_access_locations(client, api_users, api_reference):
    manager, _other_manager = api_users
    access = obtain_access_token(client, manager)

    response = client.get(reverse("api:locations"), **auth_header(access))

    assert response.status_code == 200
    assert {item["name"] for item in response.json()} == {"JWT Pickup", "JWT Delivery"}


@pytest.mark.django_db
def test_jwt_manager_scope_for_orders_and_trips(client, api_users, api_reference):
    manager, other_manager = api_users
    transport, pickup, delivery = api_reference
    own_order = create_order(manager, transport, pickup, delivery)
    own_trip = create_trip(own_order, create_route(own_order))
    other_order = create_order(other_manager, transport, pickup, delivery)
    create_trip(other_order, create_route(other_order))
    access = obtain_access_token(client, manager)

    orders_response = client.get(reverse("api:orders"), **auth_header(access))
    trips_response = client.get(reverse("api:trips"), **auth_header(access))
    other_detail_response = client.get(
        reverse("api:order_detail", args=[other_order.pk]),
        **auth_header(access),
    )

    assert orders_response.status_code == 200
    assert [item["id"] for item in orders_response.json()] == [own_order.pk]
    assert trips_response.status_code == 200
    assert [item["id"] for item in trips_response.json()] == [own_trip.pk]
    assert other_detail_response.status_code == 404


@pytest.mark.django_db
def test_session_authenticated_api_still_works(client, api_users, api_reference):
    manager, _other_manager = api_users
    client.force_login(manager)

    response = client.get(reverse("api:locations"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_anonymous_business_api_access_is_rejected(client):
    response = client.get(reverse("api:locations"))

    assert response.status_code == 401


@pytest.mark.django_db
def test_anonymous_can_register_manager_via_api(client):
    response = client.post(
        reverse("api:auth_register"),
        {
            "username": "react_manager",
            "email": "react-manager@example.test",
            "first_name": "React",
            "last_name": "Manager",
            "middle_name": "Spa",
            "phone": "+7 (999) 123-45-67",
            "password1": "StrongPass12345",
            "password2": "StrongPass12345",
        },
        content_type="application/json",
    )

    assert response.status_code == 201
    payload = response.json()
    user = get_user_model().objects.get(username="react_manager")
    assert user.role == "manager"
    assert user.email == "react-manager@example.test"
    assert user.phone == "+7 (999) 123-45-67"
    assert payload == {
        "id": user.pk,
        "username": "react_manager",
        "full_name": "React Manager",
        "role": "manager",
        "is_admin": False,
    }
    assert "password" not in response.content.decode()
    assert "access" not in payload
    assert "refresh" not in payload


@pytest.mark.django_db
def test_register_api_rejects_duplicate_username_and_email(client):
    user_model = get_user_model()
    user_model.objects.create_user(
        username="duplicate_manager",
        email="duplicate@example.test",
        password="StrongPass12345",
        role="manager",
    )

    response = client.post(
        reverse("api:auth_register"),
        {
            "username": "DUPLICATE_MANAGER",
            "email": "duplicate@example.test",
            "password1": "StrongPass12345",
            "password2": "StrongPass12345",
        },
        content_type="application/json",
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["username"] == [
        "Пользователь с таким никнеймом уже зарегистрирован. Придумайте другой никнейм."
    ]
    assert payload["email"] == ["Пользователь с таким email уже зарегистрирован."]
    assert user_model.objects.filter(username__iexact="duplicate_manager").count() == 1


@pytest.mark.django_db
def test_register_api_rejects_invalid_phone_and_password(client):
    response = client.post(
        reverse("api:auth_register"),
        {
            "username": "invalid_manager",
            "email": "invalid-manager@example.test",
            "phone": "+7 (495) 123-45-67",
            "password1": "123",
            "password2": "123",
        },
        content_type="application/json",
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["phone"] == ["Введите телефон в формате +7 (999) 123-45-67."]
    assert isinstance(payload["password2"], list)
    assert payload["password2"]
    assert not get_user_model().objects.filter(username="invalid_manager").exists()


@pytest.mark.django_db
def test_reference_api_write_methods_still_return_405(client, api_users, api_reference):
    manager, _other_manager = api_users
    transport, pickup, delivery = api_reference
    order = create_order(manager, transport, pickup, delivery)
    create_trip(order, create_route(order))
    access = obtain_access_token(client, manager)
    urls = [
        reverse("api:locations"),
        reverse("api:transports"),
        reverse("api:trips"),
        reverse("api:analytics_summary"),
    ]

    for url in urls:
        assert client.post(url, {}, **auth_header(access)).status_code == 405
        assert (
            client.put(url, {}, content_type="application/json", **auth_header(access)).status_code
            == 405
        )
        assert (
            client.patch(
                url,
                {},
                content_type="application/json",
                **auth_header(access),
            ).status_code
            == 405
        )
        assert client.delete(url, **auth_header(access)).status_code == 405


@pytest.mark.django_db
def test_jwt_manager_can_create_order(client, api_users, api_reference):
    manager, _other_manager = api_users
    transport, pickup, delivery = api_reference
    access = obtain_access_token(client, manager)

    response = client.post(
        reverse("api:orders"),
        {
            "transport": transport.pk,
            "cargo_name": "JWT created cargo",
            "cargo_type": "Metal",
            "cargo_weight_kg": "1000.00",
            "delivery_date": timezone.localdate().isoformat(),
            "origin_location": pickup.pk,
            "destination_location": delivery.pk,
        },
        content_type="application/json",
        **auth_header(access),
    )
    order = ShipmentOrder.objects.get(cargo_name="JWT created cargo")

    assert response.status_code == 201
    assert response.json()["manager"]["username"] == "jwt_manager"
    assert order.manager == manager


@pytest.mark.django_db
def test_auth_me_returns_only_safe_fields(client, api_users):
    manager, _other_manager = api_users
    access = obtain_access_token(client, manager)

    response = client.get(reverse("api:auth_me"), **auth_header(access))

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"id", "username", "full_name", "role", "is_admin"}
    assert payload["username"] == "jwt_manager"
    assert payload["role"] == "manager"
    assert payload["is_admin"] is False
    assert "email" not in payload
    assert "phone" not in payload
    assert "middle_name" not in payload
    assert "is_staff" not in payload
    assert "is_superuser" not in payload
    assert "password" not in payload


@pytest.mark.django_db
def test_jwt_order_detail_does_not_expose_raw_or_secret_data(client, api_users, api_reference):
    manager, _other_manager = api_users
    transport, pickup, delivery = api_reference
    order = create_order(manager, transport, pickup, delivery)
    create_route(order)
    access = obtain_access_token(client, manager)

    response = client.get(reverse("api:order_detail", args=[order.pk]), **auth_header(access))

    assert response.status_code == 200
    content = response.content.decode()
    route = response.json()["route_options"][0]
    assert "calculation_details_json" not in route
    assert "route_facts_json" not in route
    assert route["geometry_json"] == [[55.7558, 37.6173], [56.344, 37.52]]
    assert "secret_detail" not in content
    assert "raw" not in content
    assert "password" not in content
