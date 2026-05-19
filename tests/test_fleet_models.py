from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.fleet.models import EcoCalculationSettings, EcoStandard, Transport


@pytest.mark.django_db
def test_eco_standard_string_representation_and_values():
    standard = EcoStandard.objects.create(
        name="Euro VI",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )

    assert str(standard) == "Euro VI"
    assert standard.nox_limit_g_per_kwh == Decimal("0.46")
    assert standard.pm_limit_mg_per_kwh == Decimal("10.00")


@pytest.mark.django_db
def test_eco_standard_positive_validation():
    standard = EcoStandard(
        name="Invalid",
        nox_limit_g_per_kwh=Decimal("0.00"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )

    with pytest.raises(ValidationError):
        standard.full_clean()


@pytest.mark.django_db
def test_transport_links_to_eco_standard():
    standard = EcoStandard.objects.create(
        name="Euro V",
        nox_limit_g_per_kwh=Decimal("2.00"),
        pm_limit_mg_per_kwh=Decimal("30.00"),
    )
    transport = Transport.objects.create(
        plate_number="А111АА777",
        model="КАМАЗ 5490",
        category=Transport.Category.N3,
        fuel_type=Transport.FuelType.DIESEL,
        capacity_kg=20000,
        fuel_consumption_l_per_100km=Decimal("29.00"),
        eco_standard=standard,
        year=2021,
    )

    assert str(transport) == "А111АА777 — КАМАЗ 5490"
    assert transport.eco_standard == standard


@pytest.mark.django_db
def test_transport_positive_validation():
    standard = EcoStandard.objects.create(
        name="Euro IV",
        nox_limit_g_per_kwh=Decimal("3.50"),
        pm_limit_mg_per_kwh=Decimal("30.00"),
    )
    transport = Transport(
        plate_number="В222ВВ777",
        model="МАЗ 5440",
        category=Transport.Category.N3,
        capacity_kg=0,
        fuel_consumption_l_per_100km=Decimal("0.00"),
        eco_standard=standard,
        year=2018,
    )

    with pytest.raises(ValidationError):
        transport.full_clean()


@pytest.mark.django_db
def test_get_current_returns_active_settings():
    active_settings = EcoCalculationSettings.objects.create(
        name="Активные настройки",
        is_active=True,
        **EcoCalculationSettings.default_values(),
    )

    assert EcoCalculationSettings.get_current() == active_settings


@pytest.mark.django_db
def test_get_current_creates_default_settings_when_no_active_exists():
    current = EcoCalculationSettings.get_current()

    assert current.name == EcoCalculationSettings.DEFAULT_NAME
    assert current.is_active is True
    assert current.diesel_co2_kg_per_liter == Decimal("2.69")
    assert current.driver_time_tariff_rub_per_hour == Decimal("900.00")
    assert EcoCalculationSettings.objects.count() == 1


@pytest.mark.django_db
def test_get_current_activates_existing_default_when_no_active_exists():
    settings = EcoCalculationSettings.objects.create(
        name=EcoCalculationSettings.DEFAULT_NAME,
        is_active=False,
        diesel_co2_kg_per_liter=Decimal("1.00"),
        engine_work_kwh_per_km=Decimal("1.00"),
        fuel_price_rub_per_liter=Decimal("1.00"),
        service_tariff_rub_per_km=Decimal("1.00"),
        driver_time_tariff_rub_per_hour=Decimal("1.00"),
        full_load_fuel_increase_percent=Decimal("1.00"),
        co2_weight=Decimal("1.00"),
        nox_weight=Decimal("1.00"),
        pm_weight=Decimal("1.00"),
        co2_critical_kg=Decimal("1.00"),
        nox_critical_g=Decimal("1.00"),
        pm_critical_g=Decimal("1.00"),
    )

    current = EcoCalculationSettings.get_current()
    settings.refresh_from_db()

    assert current == settings
    assert settings.is_active is True
    assert settings.fuel_price_rub_per_liter == Decimal("78.15")
    assert settings.driver_time_tariff_rub_per_hour == Decimal("900.00")


@pytest.mark.django_db
def test_only_one_settings_record_remains_active():
    first = EcoCalculationSettings.objects.create(
        name="Первые настройки",
        is_active=True,
        **EcoCalculationSettings.default_values(),
    )
    second = EcoCalculationSettings.objects.create(
        name="Вторые настройки",
        is_active=True,
        **EcoCalculationSettings.default_values(),
    )
    first.refresh_from_db()
    second.refresh_from_db()

    assert first.is_active is False
    assert second.is_active is True
    assert EcoCalculationSettings.objects.filter(is_active=True).count() == 1


@pytest.mark.django_db
def test_eco_calculation_settings_positive_validation():
    settings = EcoCalculationSettings(
        name="Некорректные настройки",
        is_active=False,
        **EcoCalculationSettings.default_values(),
    )
    settings.fuel_price_rub_per_liter = Decimal("0.00")

    with pytest.raises(ValidationError):
        settings.full_clean()
