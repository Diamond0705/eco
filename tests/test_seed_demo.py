from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.fleet.models import EcoCalculationSettings, EcoStandard, Transport
from apps.locations.models import Location


@pytest.mark.django_db
def test_seed_demo_creates_reference_data():
    call_command("seed_demo")

    User = get_user_model()
    admin = User.objects.get(username="admin_demo")
    manager = User.objects.get(username="manager_demo")

    assert admin.email == "admin@example.com"
    assert admin.role == User.Role.ADMIN
    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.check_password("Admin12345!")
    assert admin.password != "Admin12345!"

    assert manager.email == "manager@example.com"
    assert manager.role == User.Role.MANAGER
    assert manager.check_password("Manager12345!")
    assert manager.password != "Manager12345!"

    assert EcoStandard.objects.count() == 4
    assert EcoStandard.objects.get(name="Euro III").nox_limit_g_per_kwh == Decimal("5.00")
    assert EcoStandard.objects.get(name="Euro VI").pm_limit_mg_per_kwh == Decimal("10.00")

    assert Transport.objects.count() == 4
    transport = Transport.objects.get(plate_number="А111АА777")
    assert transport.model == "КАМАЗ 5490"
    assert transport.eco_standard.name == "Euro VI"

    assert Location.objects.count() == 10
    moscow = Location.objects.get(name="Москва")
    assert moscow.latitude == Decimal("55.7558")
    assert moscow.longitude == Decimal("37.6173")

    settings = EcoCalculationSettings.objects.get(name=EcoCalculationSettings.DEFAULT_NAME)
    assert settings.is_active is True
    assert settings.fuel_price_rub_per_liter == Decimal("78.15")
    assert settings.driver_time_tariff_rub_per_hour == Decimal("900.00")
    assert EcoCalculationSettings.objects.filter(is_active=True).count() == 1


@pytest.mark.django_db
def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    first_counts = {
        "users": get_user_model().objects.count(),
        "standards": EcoStandard.objects.count(),
        "transports": Transport.objects.count(),
        "locations": Location.objects.count(),
        "settings": EcoCalculationSettings.objects.count(),
    }

    call_command("seed_demo")
    second_counts = {
        "users": get_user_model().objects.count(),
        "standards": EcoStandard.objects.count(),
        "transports": Transport.objects.count(),
        "locations": Location.objects.count(),
        "settings": EcoCalculationSettings.objects.count(),
    }

    assert second_counts == first_counts
    assert EcoCalculationSettings.objects.filter(is_active=True).count() == 1
