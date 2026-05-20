from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.fleet.models import EcoCalculationSettings, EcoStandard, Transport
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


def create_route_option(
    order,
    name,
    distance_km,
    duration_minutes,
    eco_rating,
    *,
    fuel_liters=Decimal("3.00"),
    co2_kg=Decimal("8.00"),
    calculation_details_json=None,
    route_facts_json=None,
):
    return RouteOption.objects.create(
        order=order,
        name=name,
        provider=RouteOption.Provider.GRAPHHOPPER,
        distance_km=distance_km,
        duration_minutes=duration_minutes,
        fuel_multiplier=Decimal("1.00"),
        fuel_liters=fuel_liters,
        cost_rub=Decimal("1500.00"),
        co2_kg=co2_kg,
        nox_g=Decimal("2.00"),
        pm_g=Decimal("0.020"),
        eco_rating=eco_rating,
        geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
        route_facts_json=route_facts_json or {},
        calculation_details_json=calculation_details_json or {},
        calculation_settings=EcoCalculationSettings.get_current(),
    )


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
def test_calculate_routes_passes_extended_mode_from_post(
    client,
    manager,
    transport,
    locations,
    monkeypatch,
):
    order = create_order(manager, transport, locations)
    captured = {}

    class StubRouteCalculationService:
        last_warning = ""
        last_requested_count = 5
        last_found_count = 1
        last_used_provider = RouteOption.Provider.GRAPHHOPPER

        def __init__(self, calculation_mode):
            captured["calculation_mode"] = calculation_mode

        def calculate_for_order(self, order):
            captured["order"] = order

    monkeypatch.setattr(
        "apps.routing.views.RouteCalculationService",
        StubRouteCalculationService,
    )
    client.force_login(manager)

    response = client.post(
        reverse("routing:calculate", kwargs={"pk": order.pk}),
        {"route_calculation_mode": "extended"},
    )

    assert response.status_code == 302
    assert captured["calculation_mode"] == "extended"
    assert captured["order"].pk == order.pk


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


@pytest.mark.django_db
def test_route_comparison_page_handles_one_graphhopper_route(
    client, manager, transport, locations
):
    order = create_order(manager, transport, locations)
    order.status = ShipmentOrder.Status.CALCULATED
    order.save(update_fields=["status", "updated_at"])
    create_route_option(order, "Маршрут GraphHopper", Decimal("12.35"), 18, Decimal("82.00"))
    client.force_login(manager)

    response = client.get(reverse("routing:options", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Маршрут GraphHopper" in content
    assert "GraphHopper" in content
    assert "Количество вариантов зависит от выбранного провайдера маршрутизации" in content
    assert "Самый быстрый" in content
    assert "Самый короткий" in content
    assert "Лучший по эко-рейтингу" in content


@pytest.mark.django_db
def test_route_comparison_page_shows_graphhopper_requested_and_found_counts(
    client,
    manager,
    transport,
    locations,
):
    order = create_order(manager, transport, locations)
    order.status = ShipmentOrder.Status.CALCULATED
    order.save(update_fields=["status", "updated_at"])
    create_route_option(order, "Маршрут GraphHopper", Decimal("12.35"), 18, Decimal("82.00"))
    session = client.session
    session[f"route_calculation:{order.pk}"] = {
        "requested_count": 5,
        "found_count": 1,
        "provider": RouteOption.Provider.GRAPHHOPPER,
    }
    session.save()
    client.force_login(manager)

    response = client.get(reverse("routing:options", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Запрошено: до 5 вариантов." in content
    assert "Найдено: 1." in content
    assert "GraphHopper вернул 1 вариант(а)." in content


@pytest.mark.django_db
def test_route_comparison_page_handles_multiple_graphhopper_routes(
    client, manager, transport, locations
):
    order = create_order(manager, transport, locations)
    order.status = ShipmentOrder.Status.CALCULATED
    order.save(update_fields=["status", "updated_at"])
    create_route_option(order, "Короткий", Decimal("10.00"), 25, Decimal("75.00"))
    create_route_option(order, "Быстрый", Decimal("12.00"), 15, Decimal("70.00"))
    create_route_option(
        order,
        "Альтернативный маршрут 1",
        Decimal("11.50"),
        20,
        Decimal("85.00"),
    )
    client.force_login(manager)

    response = client.get(reverse("routing:options", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Короткий" in content
    assert "Быстрый" in content
    assert "Альтернативный маршрут 1" in content
    assert "Самый быстрый" in content
    assert "Самый короткий" in content
    assert "Лучший по эко-рейтингу" in content


@pytest.mark.django_db
def test_route_comparison_page_shows_calculation_details_for_new_and_old_snapshots(
    client,
    manager,
    transport,
    locations,
):
    order = create_order(manager, transport, locations)
    order.status = ShipmentOrder.Status.CALCULATED
    order.save(update_fields=["status", "updated_at"])
    create_route_option(
        order,
        "Маршрут GraphHopper",
        Decimal("12.35"),
        18,
        Decimal("82.00"),
        calculation_details_json={
            "calculation_model_version": "v2.1",
            "final_fuel_multiplier": "1.15",
            "average_speed_kmh": "41.17",
            "road_class_factor": "1.00",
            "surface_factor": "1.00",
            "traffic_factor": "1.00",
            "warnings": ["Провайдер не предоставляет данные о пробках, traffic_factor=1.00."],
        },
    )
    create_route_option(
        order,
        "Старый снимок",
        Decimal("13.00"),
        20,
        Decimal("80.00"),
    )
    client.force_login(manager)

    response = client.get(reverse("routing:options", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Как рассчитан маршрут" in content
    assert "<details" in content
    assert "<summary>Как рассчитан маршрут</summary>" in content
    assert "Модель: v2.1" in content
    assert "итоговый множитель расхода: 1.15" in content
    assert "Провайдер не предоставляет данные о пробках, traffic_factor=1.00." in content
    assert "Старый снимок" in content


@pytest.mark.django_db
def test_route_comparison_page_marks_unpriced_tolls(client, manager, transport, locations):
    order = create_order(manager, transport, locations)
    order.status = ShipmentOrder.Status.CALCULATED
    order.save(update_fields=["status", "updated_at"])
    create_route_option(
        order,
        "Маршрут GraphHopper",
        Decimal("12.35"),
        18,
        Decimal("82.00"),
        route_facts_json={"has_tolls": True, "toll_cost_rub": "0.00"},
    )
    client.force_login(manager)

    response = client.get(reverse("routing:options", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Платная дорога без стоимости" in content
    assert (
        "Маршрут содержит платные участки, но стоимость проезда не рассчитана провайдером "
        "и не включена в итоговую стоимость перевозки."
    ) in content


@pytest.mark.django_db
def test_route_comparison_page_shows_duplicate_toll_warning_once(
    client,
    manager,
    transport,
    locations,
):
    warning = (
        "Маршрут содержит платные участки, но стоимость проезда не рассчитана провайдером "
        "и не включена в итоговую стоимость перевозки."
    )
    order = create_order(manager, transport, locations)
    order.status = ShipmentOrder.Status.CALCULATED
    order.save(update_fields=["status", "updated_at"])
    create_route_option(
        order,
        "Маршрут GraphHopper",
        Decimal("12.35"),
        18,
        Decimal("82.00"),
        route_facts_json={
            "has_tolls": True,
            "toll_cost_rub": "0.00",
            "warnings": [warning],
        },
        calculation_details_json={"warnings": [warning]},
    )
    client.force_login(manager)

    response = client.get(reverse("routing:options", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert content.count(warning) == 1


@pytest.mark.django_db
def test_route_comparison_page_uses_single_deterministic_best_eco_badge(
    client,
    manager,
    transport,
    locations,
):
    order = create_order(manager, transport, locations)
    order.status = ShipmentOrder.Status.CALCULATED
    order.save(update_fields=["status", "updated_at"])
    create_route_option(
        order,
        "Победитель",
        Decimal("12.00"),
        20,
        Decimal("80.00"),
        fuel_liters=Decimal("4.00"),
        co2_kg=Decimal("9.00"),
    )
    create_route_option(
        order,
        "Такой же рейтинг",
        Decimal("11.00"),
        15,
        Decimal("80.00"),
        fuel_liters=Decimal("5.00"),
        co2_kg=Decimal("10.00"),
    )
    client.force_login(manager)

    response = client.get(reverse("routing:options", kwargs={"pk": order.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert content.count("Лучший по эко-рейтингу") == 1
    assert "Одинаковый эко-рейтинг" in content
