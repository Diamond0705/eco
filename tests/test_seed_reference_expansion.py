from decimal import Decimal

import pytest
from django.core.management import call_command

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location

EXPECTED_LOCATIONS = {
    "Воскресенск": ("55.3173", "38.6526", "Воскресенск, Московская область, Россия"),
    "Серпухов": ("54.9198", "37.4162", "Серпухов, Московская область, Россия"),
    "Коломна": ("55.0938", "38.7689", "Коломна, Московская область, Россия"),
    "Дмитров": ("56.3450", "37.5200", "Дмитров, Московская область, Россия"),
    "Можайск": ("55.5069", "36.0241", "Можайск, Московская область, Россия"),
    "Волоколамск": ("56.0358", "35.9586", "Волоколамск, Московская область, Россия"),
    "Клин": ("56.3333", "36.7333", "Клин, Московская область, Россия"),
    "Наро-Фоминск": ("55.3862", "36.7345", "Наро-Фоминск, Московская область, Россия"),
    "Орехово-Зуево": ("55.8067", "38.9618", "Орехово-Зуево, Московская область, Россия"),
    "Электросталь": ("55.7847", "38.4447", "Электросталь, Московская область, Россия"),
    "Егорьевск": ("55.3833", "39.0333", "Егорьевск, Московская область, Россия"),
    "Тверь": ("56.8587", "35.9176", "Тверь, Россия"),
    "Калуга": ("54.5293", "36.2754", "Калуга, Россия"),
    "Тула": ("54.1931", "37.6173", "Тула, Россия"),
    "Рязань": ("54.6292", "39.7364", "Рязань, Россия"),
    "Владимир": ("56.1290", "40.4066", "Владимир, Россия"),
    "Ярославль": ("57.6261", "39.8845", "Ярославль, Россия"),
    "Смоленск": ("54.7826", "32.0453", "Смоленск, Россия"),
    "Нижний Новгород": ("56.3269", "44.0059", "Нижний Новгород, Россия"),
    "Санкт-Петербург": ("59.9386", "30.3141", "Санкт-Петербург, Россия"),
    "Воронеж": ("51.6608", "39.2003", "Воронеж, Россия"),
    "Казань": ("55.7961", "49.1064", "Казань, Россия"),
    "Краснодар": ("45.0355", "38.9753", "Краснодар, Россия"),
    "Белгород": ("50.5954", "36.5872", "Белгород, Россия"),
    "Самара": ("53.1959", "50.1002", "Самара, Россия"),
}

EXPECTED_TRANSPORTS = {
    "Н555НН777": ("КАМАЗ 65115", Transport.Category.N3, 15000, "35.00", "Euro IV", 2016),
    "Р666РР777": ("Урал NEXT 4320", Transport.Category.N3, 12000, "36.00", "Euro V", 2019),
    "Т777ТТ777": ("МАЗ 6312", Transport.Category.N3, 14000, "33.00", "Euro V", 2017),
    "У888УУ777": ("КАМАЗ 43253", Transport.Category.N2, 7500, "24.00", "Euro IV", 2015),
    "Х999ХХ777": ("Hyundai Mighty", Transport.Category.N2, 4500, "15.00", "Euro V", 2019),
}


@pytest.mark.django_db
def test_seed_reference_expansion_creates_legacy_standards():
    call_command("seed_reference_expansion")

    euro_i = EcoStandard.objects.get(name="Euro I")
    euro_ii = EcoStandard.objects.get(name="Euro II")

    assert euro_i.nox_limit_g_per_kwh == Decimal("8.00")
    assert euro_i.pm_limit_mg_per_kwh == Decimal("360.00")
    assert euro_i.is_active is True
    assert euro_ii.nox_limit_g_per_kwh == Decimal("7.00")
    assert euro_ii.pm_limit_mg_per_kwh == Decimal("150.00")
    assert euro_ii.is_active is True


@pytest.mark.django_db
def test_seed_reference_expansion_creates_locations():
    call_command("seed_reference_expansion")

    assert Location.objects.filter(name__in=EXPECTED_LOCATIONS).count() == len(EXPECTED_LOCATIONS)
    for name, (latitude, longitude, address) in EXPECTED_LOCATIONS.items():
        location = Location.objects.get(name=name)
        assert location.latitude == Decimal(latitude)
        assert location.longitude == Decimal(longitude)
        assert location.address == address
        assert location.is_active is True


@pytest.mark.django_db
def test_seed_reference_expansion_creates_transports():
    call_command("seed_reference_expansion")

    assert Transport.objects.filter(plate_number__in=EXPECTED_TRANSPORTS).count() == len(
        EXPECTED_TRANSPORTS
    )
    for plate_number, expected in EXPECTED_TRANSPORTS.items():
        model, category, capacity_kg, fuel_consumption, standard_name, year = expected
        transport = Transport.objects.get(plate_number=plate_number)
        assert transport.model == model
        assert transport.category == category
        assert transport.fuel_type == Transport.FuelType.DIESEL
        assert transport.capacity_kg == capacity_kg
        assert transport.fuel_consumption_l_per_100km == Decimal(fuel_consumption)
        assert transport.eco_standard.name == standard_name
        assert transport.year == year
        assert transport.is_active is True


@pytest.mark.django_db
def test_seed_reference_expansion_is_idempotent():
    call_command("seed_reference_expansion")
    first_counts = {
        "standards": EcoStandard.objects.count(),
        "locations": Location.objects.count(),
        "transports": Transport.objects.count(),
    }

    call_command("seed_reference_expansion")
    second_counts = {
        "standards": EcoStandard.objects.count(),
        "locations": Location.objects.count(),
        "transports": Transport.objects.count(),
    }

    assert second_counts == first_counts


@pytest.mark.django_db
def test_seed_reference_expansion_runs_after_seed_demo():
    call_command("seed_demo")
    call_command("seed_reference_expansion")

    assert EcoStandard.objects.count() == 6
    assert Location.objects.count() == 35
    assert Transport.objects.count() == 9
    assert EcoStandard.objects.get(name="Euro VI").pm_limit_mg_per_kwh == Decimal("10.00")
    assert Location.objects.get(name="Москва").latitude == Decimal("55.7558")
    assert Transport.objects.get(plate_number="А111АА777").eco_standard.name == "Euro VI"
