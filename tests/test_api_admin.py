from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.fleet.models import EcoCalculationSettings, EcoStandard, Transport
from apps.reports.models import ArchivedDocument

User = get_user_model()


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="react_admin",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def manager_user():
    return User.objects.create_user(
        username="react_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
        email="react_manager@example.test",
        phone="+7 (999) 100-20-30",
    )


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        username="react_superuser",
        password="StrongPass12345",
        email="root@example.test",
    )


@pytest.fixture
def eco_standard():
    return EcoStandard.objects.create(
        name="Euro VI React API",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )


def settings_payload(**overrides):
    payload = {
        field: str(value)
        for field, value in EcoCalculationSettings.default_values().items()
    }
    payload["name"] = "React API settings"
    payload["is_active"] = True
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_admin_api_rejects_anonymous_and_manager(client, manager_user):
    url = reverse("api:admin_dashboard")

    assert client.get(url).status_code == 401

    client.force_login(manager_user)
    assert client.get(url).status_code == 403


@pytest.mark.django_db
def test_admin_dashboard_allows_admin_and_superuser(client, admin_user, superuser):
    client.force_login(admin_user)
    admin_response = client.get(reverse("api:admin_dashboard"))

    client.force_login(superuser)
    superuser_response = client.get(reverse("api:admin_dashboard"))
    me_response = client.get(reverse("api:auth_me"))

    assert admin_response.status_code == 200
    assert "users" in admin_response.json()
    assert superuser_response.status_code == 200
    assert me_response.json()["is_admin"] is True


@pytest.mark.django_db
def test_admin_dashboard_xlsx_can_be_downloaded_and_archived(
    client,
    admin_user,
    settings,
    tmp_path,
):
    settings.MEDIA_ROOT = tmp_path / "media"
    client.force_login(admin_user)

    download_response = client.get(reverse("api:admin_dashboard_export_xlsx"))
    archive_response = client.post(reverse("api:admin_dashboard_export_xlsx_archive"))

    assert download_response.status_code == 200
    assert download_response["Content-Type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert archive_response.status_code == 201
    document = ArchivedDocument.objects.get()
    assert document.document_type == ArchivedDocument.DocumentType.ADMIN_ANALYTICS_XLSX
    assert document.created_by == admin_user


@pytest.mark.django_db
def test_admin_user_activity_api_keeps_protected_users_read_only(
    client,
    admin_user,
    manager_user,
    superuser,
):
    other_admin = User.objects.create_user(username="other_admin", role=User.Role.ADMIN)
    client.force_login(admin_user)

    manager_response = client.patch(
        reverse("api:admin_user_detail", args=[manager_user.pk]),
        {"is_active": False},
        content_type="application/json",
    )
    self_response = client.patch(
        reverse("api:admin_user_detail", args=[admin_user.pk]),
        {"is_active": False},
        content_type="application/json",
    )
    other_admin_response = client.patch(
        reverse("api:admin_user_detail", args=[other_admin.pk]),
        {"is_active": False},
        content_type="application/json",
    )
    superuser_response = client.patch(
        reverse("api:admin_user_detail", args=[superuser.pk]),
        {"is_active": False},
        content_type="application/json",
    )
    manager_user.refresh_from_db()
    admin_user.refresh_from_db()

    assert manager_response.status_code == 200
    assert manager_user.is_active is False
    assert self_response.status_code == 400
    assert other_admin_response.status_code == 400
    assert superuser_response.status_code == 400
    assert admin_user.is_active is True


@pytest.mark.django_db
def test_admin_reference_api_crud_and_validation(client, admin_user, eco_standard):
    client.force_login(admin_user)

    transport_response = client.post(
        reverse("api:admin_transports"),
        {
            "plate_number": "A123AA777",
            "model": "KAMAZ React",
            "category": Transport.Category.N3,
            "fuel_type": Transport.FuelType.DIESEL,
            "capacity_kg": 12000,
            "fuel_consumption_l_per_100km": "32.50",
            "eco_standard": eco_standard.pk,
            "year": 2024,
            "is_active": True,
        },
        content_type="application/json",
    )
    invalid_transport_response = client.post(
        reverse("api:admin_transports"),
        {
            "plate_number": "B123BB777",
            "model": "Invalid React",
            "category": Transport.Category.N3,
            "fuel_type": Transport.FuelType.DIESEL,
            "capacity_kg": 0,
            "fuel_consumption_l_per_100km": "0.00",
            "eco_standard": eco_standard.pk,
            "year": 2024,
            "is_active": True,
        },
        content_type="application/json",
    )
    location_response = client.post(
        reverse("api:admin_locations"),
        {
            "name": "React API location",
            "address": "Moscow",
            "latitude": "55.7558",
            "longitude": "37.6173",
            "is_active": True,
        },
        content_type="application/json",
    )
    invalid_location_response = client.post(
        reverse("api:admin_locations"),
        {
            "name": "Invalid React API location",
            "latitude": "91.0000",
            "longitude": "181.0000",
            "is_active": True,
        },
        content_type="application/json",
    )
    standard_response = client.post(
        reverse("api:admin_eco_standards"),
        {
            "name": "Euro VII React API",
            "nox_limit_g_per_kwh": "0.20",
            "pm_limit_mg_per_kwh": "5.00",
            "is_active": True,
        },
        content_type="application/json",
    )
    invalid_standard_response = client.post(
        reverse("api:admin_eco_standards"),
        {
            "name": "Invalid Euro React API",
            "nox_limit_g_per_kwh": "0.00",
            "pm_limit_mg_per_kwh": "-1.00",
            "is_active": True,
        },
        content_type="application/json",
    )

    assert transport_response.status_code == 201
    assert invalid_transport_response.status_code == 400
    assert location_response.status_code == 201
    assert invalid_location_response.status_code == 400
    assert standard_response.status_code == 201
    assert invalid_standard_response.status_code == 400


@pytest.mark.django_db
def test_admin_calculation_settings_api_creates_new_active_version(client, admin_user):
    old_settings = EcoCalculationSettings.get_current()
    client.force_login(admin_user)

    response = client.post(
        reverse("api:admin_calculation_settings"),
        settings_payload(name="React API new active", fuel_price_rub_per_liter="99.99"),
        content_type="application/json",
    )
    list_response = client.get(reverse("api:admin_calculation_settings"))
    old_settings.refresh_from_db()
    new_settings = EcoCalculationSettings.get_current()

    assert response.status_code == 201
    assert new_settings.pk != old_settings.pk
    assert new_settings.name == "React API new active"
    assert new_settings.fuel_price_rub_per_liter == Decimal("99.99")
    assert new_settings.is_active is True
    assert old_settings.is_active is False
    assert EcoCalculationSettings.objects.filter(is_active=True).count() == 1
    assert list_response.status_code == 200
    assert list_response.json()["current"]["id"] == new_settings.pk
