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

User = get_user_model()


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="phase15_admin",
        password="StrongPass12345",
        role=User.Role.ADMIN,
        first_name="Анна",
        last_name="Админова",
    )


@pytest.fixture
def manager_user():
    return User.objects.create_user(
        username="phase15_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
        first_name="Мария",
        last_name="Менеджерова",
        email="manager15@example.com",
        phone="+7 (999) 111-22-33",
    )


@pytest.fixture
def eco_standard():
    return EcoStandard.objects.create(
        name="Euro VI Phase 15",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )


@pytest.fixture
def transport(eco_standard):
    return Transport.objects.create(
        plate_number="А915АА777",
        model="КАМАЗ Phase 15",
        category=Transport.Category.N3,
        fuel_type=Transport.FuelType.DIESEL,
        capacity_kg=20000,
        fuel_consumption_l_per_100km=Decimal("29.00"),
        eco_standard=eco_standard,
        year=2024,
    )


@pytest.fixture
def locations():
    origin = Location.objects.create(
        name="Москва Phase 15",
        address="Москва",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )
    destination = Location.objects.create(
        name="Подольск Phase 15",
        address="Подольск",
        latitude=Decimal("55.4312"),
        longitude=Decimal("37.5447"),
    )
    return origin, destination


def admin_panel_urls(user, transport, location, standard, settings_version=None):
    settings_version = settings_version or EcoCalculationSettings.get_current()
    return [
        reverse("dashboard:admin_dashboard"),
        reverse("dashboard:admin_users"),
        reverse("dashboard:admin_user_edit", args=[user.pk]),
        reverse("dashboard:admin_transports"),
        reverse("dashboard:admin_transport_create"),
        reverse("dashboard:admin_transport_edit", args=[transport.pk]),
        reverse("dashboard:admin_locations"),
        reverse("dashboard:admin_location_create"),
        reverse("dashboard:admin_location_edit", args=[location.pk]),
        reverse("dashboard:admin_eco_standards"),
        reverse("dashboard:admin_eco_standard_create"),
        reverse("dashboard:admin_eco_standard_edit", args=[standard.pk]),
        reverse("dashboard:admin_calculation_settings"),
        reverse("dashboard:admin_calculation_settings_create"),
        reverse("dashboard:admin_calculation_settings_edit", args=[settings_version.pk]),
    ]


def create_delivered_trip(manager, transport, locations, cargo_name):
    origin, destination = locations
    order = ShipmentOrder.objects.create(
        manager=manager,
        transport=transport,
        cargo_name=cargo_name,
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("1000.00"),
        desired_delivery_date="2026-06-01",
        status=ShipmentOrder.Status.COMPLETED,
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
    route_option = RouteOption.objects.create(
        order=order,
        name="Учебный маршрут",
        provider=RouteOption.Provider.MOCK,
        distance_km=Decimal("50.00"),
        duration_minutes=60,
        fuel_multiplier=Decimal("1.00"),
        fuel_liters=Decimal("15.00"),
        cost_rub=Decimal("10000.00"),
        co2_kg=Decimal("40.35"),
        nox_g=Decimal("27.60"),
        pm_g=Decimal("0.600"),
        eco_rating=Decimal("88.00"),
        geometry_json=[[55.7558, 37.6173], [55.4312, 37.5447]],
        calculation_settings=EcoCalculationSettings.get_current(),
        is_selected=True,
    )
    return Trip.objects.create(
        order=order,
        route_option=route_option,
        status=Trip.Status.DELIVERED,
        actual_finish_at=timezone.now(),
    )


def calculation_settings_form_data(**overrides):
    values = {
        field: str(value)
        for field, value in EcoCalculationSettings.default_values().items()
    }
    values["name"] = "Настройки Phase 15"
    values["is_active"] = "1"
    values["driver_time_tariff_rub_per_hour"] = "900.00"
    values.update(overrides)
    return values


@pytest.mark.django_db
def test_admin_dashboard_phase15_cleanup_and_navigation(
    client, admin_user, manager_user, transport, locations
):
    second_manager = User.objects.create_user(
        username="phase15_second_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )
    for index in range(12):
        create_delivered_trip(manager_user, transport, locations, f"Груз {index}")
    for index in range(2):
        create_delivered_trip(second_manager, transport, locations, f"Другой груз {index}")
    client.force_login(admin_user)

    response = client.get(reverse("dashboard:admin_dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "<h2>Платные участки</h2>" not in content
    assert "Топ менеджеров по завершенным рейсам" in content
    assert "Топ транспорта по завершенным рейсам" in content
    assert "Количество добавленного транспорта." in content
    assert "Суммарная стоимость по доставленным рейсам." in content
    assert "admin-panel-nav" not in content
    assert "12 рейсов" in content
    assert "2 рейса" in content
    for label in [
        "Панель",
        "Пользователи",
        "Транспорт",
        "Локации",
        "Экостандарты",
        "Экорасчет",
    ]:
        assert label in content
    assert "Django Admin" in content


@pytest.mark.django_db
def test_admin_navigation_is_in_header_and_hidden_from_manager(client, admin_user, manager_user):
    client.force_login(admin_user)
    response = client.get(reverse("dashboard:admin_users"))
    content = response.content.decode()

    assert response.status_code == 200
    assert '<nav class="site-nav"' in content
    assert "Пользователи" in content
    assert "Экостандарты" in content
    assert "Экорасчет" in content
    assert "Django Admin" not in content
    assert "admin-panel-nav" not in content

    client.force_login(manager_user)
    response = client.get(reverse("dashboard:manager_dashboard"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Пользователи" not in content
    assert "Экостандарты" not in content
    assert "Экорасчет" not in content
    assert "Django Admin" not in content


@pytest.mark.django_db
def test_admin_panel_access_control(
    client, admin_user, manager_user, transport, locations, eco_standard
):
    location = locations[0]

    for url in admin_panel_urls(manager_user, transport, location, eco_standard):
        response = client.get(url)
        assert response.status_code == 302
        assert response["Location"].startswith(reverse("accounts:login"))

    client.force_login(manager_user)
    for url in admin_panel_urls(manager_user, transport, location, eco_standard):
        assert client.get(url).status_code == 403

    client.force_login(admin_user)
    for url in admin_panel_urls(manager_user, transport, location, eco_standard):
        assert client.get(url).status_code == 200


@pytest.mark.django_db
def test_admin_user_list_filters_by_activity_and_shows_phone(client, admin_user, manager_user):
    User.objects.create_user(
        username="phase15_inactive",
        password="StrongPass12345",
        role=User.Role.MANAGER,
        is_active=False,
        phone="+7 (999) 000-00-00",
    )
    client.force_login(admin_user)

    response = client.get(reverse("dashboard:admin_users"), {"q": "manager15", "active": "1"})
    content = response.content.decode()

    assert response.status_code == 200
    assert "phase15_manager" in content
    assert "manager15@example.com" in content
    assert "+7 (999) 111-22-33" in content
    assert "Менеджер" in content
    assert "phase15_inactive" not in content
    assert "Все роли" not in content

    response = client.get(reverse("dashboard:admin_users"), {"active": "0"})
    content = response.content.decode()

    assert "phase15_inactive" in content
    assert "phase15_manager" not in content


@pytest.mark.django_db
def test_admin_user_edit_shows_profile_details_and_changes_manager_activity(
    client, admin_user, manager_user
):
    client.force_login(admin_user)

    response = client.get(reverse("dashboard:admin_user_edit", args=[manager_user.pk]))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Имя пользователя" in content
    assert "Фамилия" in content
    assert "Телефон" in content
    assert "+7 (999) 111-22-33" in content
    assert "Роль" in content
    assert "Менеджер" in content
    assert 'name="role"' not in content

    response = client.post(
        reverse("dashboard:admin_user_edit", args=[manager_user.pk]),
        {"role": User.Role.ADMIN, "is_active": "0"},
    )
    manager_user.refresh_from_db()

    assert response.status_code == 302
    assert manager_user.role == User.Role.MANAGER
    assert not manager_user.is_active


@pytest.mark.django_db
def test_admin_user_edit_keeps_admin_activity_read_only(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("dashboard:admin_user_edit", args=[admin_user.pk]))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'name="is_active"' not in content
    assert "Роль и активность администратора изменяются только" in content

    response = client.post(
        reverse("dashboard:admin_user_edit", args=[admin_user.pk]),
        {"is_active": "0"},
    )
    admin_user.refresh_from_db()

    assert response.status_code == 200
    assert admin_user.is_active
    assert admin_user.role == User.Role.ADMIN


@pytest.mark.django_db
def test_admin_transport_create_and_edit(client, admin_user, eco_standard):
    client.force_login(admin_user)

    response = client.post(
        reverse("dashboard:admin_transport_create"),
        {
            "plate_number": "В915ВВ777",
            "model": "ГАЗон Next",
            "category": Transport.Category.N2,
            "fuel_type": Transport.FuelType.DIESEL,
            "capacity_kg": "5000",
            "fuel_consumption_l_per_100km": "18.50",
            "eco_standard": eco_standard.pk,
            "year": "2023",
            "is_active": "1",
        },
    )
    transport = Transport.objects.get(plate_number="В915ВВ777")

    assert response.status_code == 302
    assert transport.model == "ГАЗон Next"

    response = client.post(
        reverse("dashboard:admin_transport_edit", args=[transport.pk]),
        {
            "plate_number": "В915ВВ777",
            "model": "ГАЗон Next обновленный",
            "category": Transport.Category.N2,
            "fuel_type": Transport.FuelType.DIESEL,
            "capacity_kg": "5500",
            "fuel_consumption_l_per_100km": "19.00",
            "eco_standard": eco_standard.pk,
            "year": "2023",
            "is_active": "0",
        },
    )
    transport.refresh_from_db()

    assert response.status_code == 302
    assert transport.model == "ГАЗон Next обновленный"
    assert transport.capacity_kg == 5500
    assert not transport.is_active


@pytest.mark.django_db
def test_admin_transport_list_filters_by_eco_standard(client, admin_user, eco_standard):
    other_standard = EcoStandard.objects.create(
        name="Euro V Phase 15",
        nox_limit_g_per_kwh=Decimal("2.00"),
        pm_limit_mg_per_kwh=Decimal("30.00"),
    )
    Transport.objects.create(
        plate_number="Е515ЕЕ777",
        model="МАЗ Euro V",
        category=Transport.Category.N3,
        fuel_type=Transport.FuelType.DIESEL,
        capacity_kg=18000,
        fuel_consumption_l_per_100km=Decimal("31.00"),
        eco_standard=other_standard,
        year=2020,
    )
    expected_transport = Transport.objects.create(
        plate_number="Е615ЕЕ777",
        model="КАМАЗ Euro VI",
        category=Transport.Category.N3,
        fuel_type=Transport.FuelType.DIESEL,
        capacity_kg=20000,
        fuel_consumption_l_per_100km=Decimal("29.00"),
        eco_standard=eco_standard,
        year=2024,
    )
    client.force_login(admin_user)

    response = client.get(
        reverse("dashboard:admin_transports"),
        {"eco_standard": str(eco_standard.pk)},
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert "Евро-класс" in content
    assert "Активные" not in content
    assert expected_transport.plate_number in content
    assert "Е515ЕЕ777" not in content


@pytest.mark.django_db
def test_admin_transport_rejects_invalid_values(client, admin_user, eco_standard):
    client.force_login(admin_user)

    response = client.post(
        reverse("dashboard:admin_transport_create"),
        {
            "plate_number": "С915СС777",
            "model": "Некорректный",
            "category": Transport.Category.N3,
            "fuel_type": Transport.FuelType.DIESEL,
            "capacity_kg": "0",
            "fuel_consumption_l_per_100km": "0.00",
            "eco_standard": eco_standard.pk,
            "year": "2022",
            "is_active": "1",
        },
    )

    assert response.status_code == 200
    assert not Transport.objects.filter(plate_number="С915СС777").exists()


@pytest.mark.django_db
def test_admin_location_create_edit_and_coordinate_validation(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("dashboard:admin_locations"))
    content = response.content.decode()

    assert "Учебные точки отправления и доставки." not in content
    assert "Маршруты свыше 2000 км" not in content
    assert "Добавить локацию" not in content

    response = client.post(
        reverse("dashboard:admin_location_create"),
        {
            "name": "Тверь Phase 15",
            "address": "Тверь",
            "latitude": "56.8587",
            "longitude": "35.9176",
            "is_active": "1",
        },
    )
    location = Location.objects.get(name="Тверь Phase 15")

    assert response.status_code == 302
    assert location.longitude == Decimal("35.9176")

    response = client.post(
        reverse("dashboard:admin_location_edit", args=[location.pk]),
        {
            "name": "Тверь Phase 15",
            "address": "Тверь, склад",
            "latitude": "56.8587",
            "longitude": "35.9000",
            "is_active": "0",
        },
    )
    location.refresh_from_db()

    assert response.status_code == 302
    assert location.address == "Тверь, склад"
    assert not location.is_active

    response = client.post(
        reverse("dashboard:admin_location_create"),
        {
            "name": "Неверная локация",
            "address": "",
            "latitude": "91.0000",
            "longitude": "181.0000",
            "is_active": "1",
        },
    )

    assert response.status_code == 200
    assert not Location.objects.filter(name="Неверная локация").exists()
    assert "Маршруты свыше 2000 км" not in response.content.decode()
    assert "Добавить локацию" not in response.content.decode()


@pytest.mark.django_db
def test_admin_eco_standard_create_edit_and_validation(client, admin_user):
    client.force_login(admin_user)

    response = client.post(
        reverse("dashboard:admin_eco_standard_create"),
        {
            "name": "Euro VII Phase 15",
            "nox_limit_g_per_kwh": "0.20",
            "pm_limit_mg_per_kwh": "5.00",
            "is_active": "1",
        },
    )
    standard = EcoStandard.objects.get(name="Euro VII Phase 15")

    assert response.status_code == 302
    assert standard.nox_limit_g_per_kwh == Decimal("0.20")

    response = client.post(
        reverse("dashboard:admin_eco_standard_edit", args=[standard.pk]),
        {
            "name": "Euro VII Phase 15",
            "nox_limit_g_per_kwh": "0.25",
            "pm_limit_mg_per_kwh": "6.00",
            "is_active": "0",
        },
    )
    standard.refresh_from_db()

    assert response.status_code == 302
    assert standard.nox_limit_g_per_kwh == Decimal("0.25")
    assert not standard.is_active

    response = client.post(
        reverse("dashboard:admin_eco_standard_create"),
        {
            "name": "Неверный Euro",
            "nox_limit_g_per_kwh": "0.00",
            "pm_limit_mg_per_kwh": "-1.00",
            "is_active": "1",
        },
    )

    assert response.status_code == 200
    assert not EcoStandard.objects.filter(name="Неверный Euro").exists()
    assert "Старые RouteOption остаются сохраненными снимками" in response.content.decode()


@pytest.mark.django_db
def test_admin_calculation_settings_create_new_active_version_without_snapshot_recalculation(
    client, admin_user, manager_user, transport, locations
):
    old_settings = EcoCalculationSettings.get_current()
    inactive_settings = EcoCalculationSettings.objects.create(
        name="Неактивные настройки Phase 15",
        is_active=False,
        **EcoCalculationSettings.default_values(),
    )
    trip = create_delivered_trip(manager_user, transport, locations, "Снимок до настроек")
    route_option = trip.route_option
    old_snapshot = {
        "fuel_liters": route_option.fuel_liters,
        "cost_rub": route_option.cost_rub,
        "co2_kg": route_option.co2_kg,
        "nox_g": route_option.nox_g,
        "pm_g": route_option.pm_g,
        "eco_rating": route_option.eco_rating,
        "calculation_settings_id": route_option.calculation_settings_id,
    }
    client.force_login(admin_user)

    response = client.get(reverse("dashboard:admin_calculation_settings"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Настройки экологического расчета" in content
    assert "Изменение настроек расчета применяется только к новым расчетам маршрутов." in content
    assert old_settings.name in content
    assert inactive_settings.name in content
    assert "Активна" in content
    assert "Неактивна" in content
    assert "Обновлена:" not in content
    assert "Обновлена" in content

    response = client.post(
        reverse("dashboard:admin_calculation_settings_create"),
        calculation_settings_form_data(
            name="Новые настройки Phase 15",
            fuel_price_rub_per_liter="99.99",
            is_active="1",
        ),
    )
    route_option.refresh_from_db()
    old_settings.refresh_from_db()
    new_settings = EcoCalculationSettings.get_current()

    assert response.status_code == 302
    assert new_settings.pk != old_settings.pk
    assert new_settings.name == "Новые настройки Phase 15"
    assert new_settings.fuel_price_rub_per_liter == Decimal("99.99")
    assert new_settings.is_active
    assert not old_settings.is_active
    assert EcoCalculationSettings.objects.filter(is_active=True).count() == 1
    assert route_option.fuel_liters == old_snapshot["fuel_liters"]
    assert route_option.cost_rub == old_snapshot["cost_rub"]
    assert route_option.co2_kg == old_snapshot["co2_kg"]
    assert route_option.nox_g == old_snapshot["nox_g"]
    assert route_option.pm_g == old_snapshot["pm_g"]
    assert route_option.eco_rating == old_snapshot["eco_rating"]
    assert route_option.calculation_settings_id == old_snapshot["calculation_settings_id"]

    response = client.post(
        reverse("dashboard:admin_calculation_settings_edit", args=[old_settings.pk]),
        calculation_settings_form_data(
            name=old_settings.name,
            fuel_price_rub_per_liter="88.88",
            is_active="1",
        ),
    )
    route_option.refresh_from_db()
    old_settings.refresh_from_db()
    new_settings.refresh_from_db()

    assert response.status_code == 302
    assert old_settings.is_active
    assert old_settings.fuel_price_rub_per_liter == Decimal("88.88")
    assert not new_settings.is_active
    assert EcoCalculationSettings.objects.filter(is_active=True).count() == 1
    assert route_option.fuel_liters == old_snapshot["fuel_liters"]
    assert route_option.cost_rub == old_snapshot["cost_rub"]
    assert route_option.co2_kg == old_snapshot["co2_kg"]
    assert route_option.nox_g == old_snapshot["nox_g"]
    assert route_option.pm_g == old_snapshot["pm_g"]
    assert route_option.eco_rating == old_snapshot["eco_rating"]
    assert route_option.calculation_settings_id == old_snapshot["calculation_settings_id"]
