from decimal import Decimal

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.admin import OrderPointInline, ShipmentOrderAdmin
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.services.route_calculation_service import RouteCalculationService

User = get_user_model()


@pytest.fixture
def manager():
    return User.objects.create_user(
        username="view_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def other_manager():
    return User.objects.create_user(
        username="other_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="orders_admin",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        username="orders_superuser",
        email="orders_superuser@example.com",
        password="StrongPass12345",
    )


@pytest.fixture
def eco_standard():
    return EcoStandard.objects.create(
        name="Euro VI",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )


@pytest.fixture
def transport(eco_standard):
    return Transport.objects.create(
        plate_number="Т111ТТ777",
        model="КАМАЗ 5490",
        category=Transport.Category.N3,
        capacity_kg=20000,
        fuel_consumption_l_per_100km=Decimal("29.00"),
        eco_standard=eco_standard,
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


def _create_order(
    manager,
    transport,
    locations,
    cargo_name="Оборудование",
    status=ShipmentOrder.Status.NEW,
):
    origin, destination = locations
    order = ShipmentOrder.objects.create(
        manager=manager,
        transport=transport,
        cargo_name=cargo_name,
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("1000.00"),
        desired_delivery_date="2026-06-01",
        status=status,
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
def test_manager_can_create_order_and_is_redirected_to_detail(
    client, manager, transport, locations
):
    origin, destination = locations
    client.force_login(manager)

    response = client.post(
        reverse("orders:create"),
        {
            "transport": transport.pk,
            "cargo_name": "Оборудование",
            "cargo_type": "Паллеты",
            "cargo_weight_kg": "1000.00",
            "desired_delivery_date": "2026-06-01",
            "origin_location": origin.pk,
            "destination_location": destination.pk,
            "notes": "Доставить утром",
        },
    )

    order = ShipmentOrder.objects.get()
    assert response.status_code == 302
    assert response["Location"] == reverse("orders:detail", kwargs={"pk": order.pk})
    assert order.manager == manager
    assert order.status == ShipmentOrder.Status.NEW
    assert list(order.points.order_by("sequence").values_list("sequence", "point_type")) == [
        (1, OrderPoint.PointType.PICKUP),
        (2, OrderPoint.PointType.DELIVERY),
    ]


@pytest.mark.django_db
def test_manager_sees_own_orders_only(client, manager, other_manager, transport, locations):
    own_order = _create_order(manager, transport, locations, cargo_name="Свой груз")
    _other_order = _create_order(other_manager, transport, locations, cargo_name="Чужой груз")
    client.force_login(manager)

    response = client.get(reverse("orders:list"))
    content = response.content.decode()

    assert response.status_code == 200
    assert f"Заявка №{own_order.pk}" not in content
    assert "Свой груз" in content
    assert "Чужой груз" not in content


@pytest.mark.django_db
def test_order_list_filters_by_status_for_current_manager(
    client, manager, other_manager, transport, locations
):
    _create_order(
        manager,
        transport,
        locations,
        cargo_name="Новая заявка",
        status=ShipmentOrder.Status.NEW,
    )
    _create_order(
        manager,
        transport,
        locations,
        cargo_name="Запланированная заявка",
        status=ShipmentOrder.Status.PLANNED,
    )
    _create_order(
        other_manager,
        transport,
        locations,
        cargo_name="Чужая запланированная заявка",
        status=ShipmentOrder.Status.PLANNED,
    )
    client.force_login(manager)

    response = client.get(reverse("orders:list"), {"status": ShipmentOrder.Status.PLANNED})
    content = response.content.decode()

    assert response.status_code == 200
    assert "Запланированная заявка" in content
    assert "Новая заявка" not in content
    assert "Чужая запланированная заявка" not in content


@pytest.mark.django_db
def test_order_list_ignores_invalid_status_filter(client, manager, transport, locations):
    _create_order(manager, transport, locations, cargo_name="Новая заявка")
    _create_order(
        manager,
        transport,
        locations,
        cargo_name="Завершенная заявка",
        status=ShipmentOrder.Status.COMPLETED,
    )
    client.force_login(manager)

    response = client.get(reverse("orders:list"), {"status": "bad-status"})
    content = response.content.decode()

    assert response.status_code == 200
    assert "Новая заявка" in content
    assert "Завершенная заявка" in content


@pytest.mark.django_db
def test_manager_cannot_open_another_manager_order(
    client, manager, other_manager, transport, locations
):
    other_order = _create_order(other_manager, transport, locations)
    client.force_login(manager)

    response = client.get(reverse("orders:detail", kwargs={"pk": other_order.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_anonymous_access_redirects_to_login(client):
    response = client.get(reverse("orders:list"))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_admin_and_superuser_get_403_on_manager_order_pages(client, admin_user, superuser):
    for user in (admin_user, superuser):
        client.force_login(user)
        assert client.get(reverse("orders:list")).status_code == 403
        assert client.get(reverse("orders:create")).status_code == 403


@pytest.mark.django_db
def test_order_detail_displays_points_ordered_by_sequence(client, manager, transport, locations):
    order = _create_order(manager, transport, locations)
    client.force_login(manager)

    response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert content.index("Погрузка") < content.index("Доставка")
    assert "Рассчитать маршруты" in content
    assert "Режим расчета маршрутов:" in content
    assert "Стандартный — до 3 вариантов" in content
    assert "Расширенный — до 5 вариантов" in content
    assert "Утверждение маршрута создает рейс." in content


@pytest.mark.django_db
def test_new_order_detail_shows_calculate_routes_button(client, manager, transport, locations):
    order = _create_order(manager, transport, locations)
    client.force_login(manager)

    response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Рассчитать маршруты" in content
    assert 'name="route_calculation_mode" value="standard" checked' in content
    assert reverse("routing:calculate", kwargs={"pk": order.pk}) in content


@pytest.mark.django_db
def test_cancelled_order_detail_does_not_show_calculate_routes_button(
    client, manager, transport, locations
):
    order = _create_order(manager, transport, locations, status=ShipmentOrder.Status.CANCELLED)
    client.force_login(manager)

    response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Рассчитать маршруты" not in content
    assert "Маршруты можно рассчитать только для новой или рассчитанной заявки." in content


@pytest.mark.django_db
def test_calculated_order_with_route_options_shows_compare_link(
    client, manager, transport, locations
):
    order = _create_order(manager, transport, locations)
    RouteCalculationService().calculate_for_order(order)
    client.force_login(manager)

    response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Сравнить маршруты" in content
    assert "Найти дополнительные альтернативы" in content
    assert 'name="route_calculation_mode" value="extended"' in content
    assert reverse("routing:options", kwargs={"pk": order.pk}) in content
    assert "Рассчитать маршруты" not in content


@pytest.mark.django_db
def test_manager_can_open_edit_page_for_own_new_order(client, manager, transport, locations):
    order = _create_order(manager, transport, locations)
    client.force_login(manager)

    response = client.get(reverse("orders:edit", kwargs={"pk": order.pk}))

    assert response.status_code == 200
    assert "Редактирование заявки" in response.content.decode()
    assert 'value="2026-06-01"' in response.content.decode()


@pytest.mark.django_db
def test_manager_can_edit_own_new_order_without_duplicate_points(
    client, manager, transport, locations, eco_standard
):
    origin, destination = locations
    new_destination = Location.objects.create(
        name="Химки",
        latitude=Decimal("55.8887"),
        longitude=Decimal("37.4300"),
    )
    new_transport = Transport.objects.create(
        plate_number="Т222ТТ777",
        model="МАЗ 5440",
        category=Transport.Category.N3,
        capacity_kg=20000,
        fuel_consumption_l_per_100km=Decimal("32.00"),
        eco_standard=eco_standard,
        year=2018,
    )
    order = _create_order(manager, transport, locations)
    client.force_login(manager)

    response = client.post(
        reverse("orders:edit", kwargs={"pk": order.pk}),
        {
            "transport": new_transport.pk,
            "cargo_name": "Новый груз",
            "cargo_type": "Коробки",
            "cargo_weight_kg": "1500.00",
            "desired_delivery_date": "2026-06-02",
            "origin_location": origin.pk,
            "destination_location": new_destination.pk,
            "notes": "Обновлено",
        },
    )

    assert response.status_code == 302
    order.refresh_from_db()
    assert order.transport == new_transport
    assert order.cargo_name == "Новый груз"
    assert order.points.count() == 2
    points = list(order.points.order_by("sequence"))
    assert points[0].location == origin
    assert points[1].location == new_destination


@pytest.mark.django_db
def test_manager_cannot_edit_another_manager_order(
    client, manager, other_manager, transport, locations
):
    order = _create_order(other_manager, transport, locations)
    client.force_login(manager)

    response = client.get(reverse("orders:edit", kwargs={"pk": order.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_admin_and_superuser_get_403_for_order_edit(
    client,
    admin_user,
    superuser,
    transport,
    locations,
):
    order = _create_order(
        User.objects.create_user(
            username="edit_owner",
            password="StrongPass12345",
            role=User.Role.MANAGER,
        ),
        transport,
        locations,
    )

    for user in (admin_user, superuser):
        client.force_login(user)
        assert client.get(reverse("orders:edit", kwargs={"pk": order.pk})).status_code == 403


@pytest.mark.django_db
def test_cancelled_order_cannot_be_edited(client, manager, transport, locations):
    order = _create_order(manager, transport, locations, status=ShipmentOrder.Status.CANCELLED)
    client.force_login(manager)

    response = client.get(reverse("orders:edit", kwargs={"pk": order.pk}))

    assert response.status_code == 403


@pytest.mark.django_db
def test_manager_can_cancel_own_new_order(client, manager, transport, locations):
    order = _create_order(manager, transport, locations)
    client.force_login(manager)

    response = client.post(reverse("orders:cancel", kwargs={"pk": order.pk}))

    assert response.status_code == 302
    order.refresh_from_db()
    assert order.status == ShipmentOrder.Status.CANCELLED


@pytest.mark.django_db
def test_cancel_uses_post_and_get_does_not_cancel(client, manager, transport, locations):
    order = _create_order(manager, transport, locations)
    client.force_login(manager)

    response = client.get(reverse("orders:cancel", kwargs={"pk": order.pk}))

    assert response.status_code == 405
    order.refresh_from_db()
    assert order.status == ShipmentOrder.Status.NEW


@pytest.mark.django_db
def test_cancelled_order_appears_with_cancelled_status(client, manager, transport, locations):
    order = _create_order(manager, transport, locations, status=ShipmentOrder.Status.CANCELLED)
    client.force_login(manager)

    list_response = client.get(reverse("orders:list"))
    detail_response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))

    assert "Отменена" in list_response.content.decode()
    assert "Отменена" in detail_response.content.decode()


@pytest.mark.django_db
def test_shipment_order_admin_is_registered_with_points_inline():
    model_admin = admin.site._registry[ShipmentOrder]

    assert isinstance(model_admin, ShipmentOrderAdmin)
    assert OrderPointInline in model_admin.inlines
