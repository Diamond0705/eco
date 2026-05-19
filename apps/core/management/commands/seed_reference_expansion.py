from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location


class Command(BaseCommand):
    help = (
        "Расширяет справочные данные EcoLogist: legacy Euro I-II, дополнительные "
        "локации и демо-транспорт. Расход топлива указан для учебных расчетов, "
        "а не как сертифицированные данные производителя."
    )

    MOSCOW_OBLAST_LOCATIONS = (
        ("Воскресенск", "55.3173", "38.6526"),
        ("Серпухов", "54.9198", "37.4162"),
        ("Коломна", "55.0938", "38.7689"),
        ("Дмитров", "56.3450", "37.5200"),
        ("Можайск", "55.5069", "36.0241"),
        ("Волоколамск", "56.0358", "35.9586"),
        ("Клин", "56.3333", "36.7333"),
        ("Наро-Фоминск", "55.3862", "36.7345"),
        ("Орехово-Зуево", "55.8067", "38.9618"),
        ("Электросталь", "55.7847", "38.4447"),
        ("Егорьевск", "55.3833", "39.0333"),
    )
    REGIONAL_LOCATIONS = (
        ("Тверь", "56.8587", "35.9176"),
        ("Калуга", "54.5293", "36.2754"),
        ("Тула", "54.1931", "37.6173"),
        ("Рязань", "54.6292", "39.7364"),
        ("Владимир", "56.1290", "40.4066"),
        ("Ярославль", "57.6261", "39.8845"),
        ("Смоленск", "54.7826", "32.0453"),
        ("Нижний Новгород", "56.3269", "44.0059"),
        ("Санкт-Петербург", "59.9386", "30.3141"),
        ("Воронеж", "51.6608", "39.2003"),
        ("Казань", "55.7961", "49.1064"),
        ("Краснодар", "45.0355", "38.9753"),
        ("Белгород", "50.5954", "36.5872"),
        ("Самара", "53.1959", "50.1002"),
    )

    def handle(self, *args, **options):
        standards = self._seed_legacy_standards()
        self._seed_locations()
        self._seed_transports(standards)
        self.stdout.write(
            "Euro I-II добавлены как legacy-стандарты для тестирования старых грузовиков."
        )
        self.stdout.write(
            "Расход топлива у дополнительных машин является демо-значением для расчетов, "
            "не сертифицированной характеристикой производителя."
        )
        self.stdout.write(self.style.SUCCESS("Расширенные справочные данные EcoLogist обновлены."))

    def _seed_legacy_standards(self):
        legacy_standards = {
            "Euro I": {
                "nox_limit_g_per_kwh": Decimal("8.00"),
                "pm_limit_mg_per_kwh": Decimal("360.00"),
                "is_active": True,
            },
            "Euro II": {
                "nox_limit_g_per_kwh": Decimal("7.00"),
                "pm_limit_mg_per_kwh": Decimal("150.00"),
                "is_active": True,
            },
        }
        existing_standard_defaults = {
            "Euro III": {
                "nox_limit_g_per_kwh": Decimal("5.00"),
                "pm_limit_mg_per_kwh": Decimal("160.00"),
                "is_active": True,
            },
            "Euro IV": {
                "nox_limit_g_per_kwh": Decimal("3.50"),
                "pm_limit_mg_per_kwh": Decimal("30.00"),
                "is_active": True,
            },
            "Euro V": {
                "nox_limit_g_per_kwh": Decimal("2.00"),
                "pm_limit_mg_per_kwh": Decimal("30.00"),
                "is_active": True,
            },
            "Euro VI": {
                "nox_limit_g_per_kwh": Decimal("0.46"),
                "pm_limit_mg_per_kwh": Decimal("10.00"),
                "is_active": True,
            },
        }
        result = {}
        for name, defaults in legacy_standards.items():
            standard, _created = EcoStandard.objects.update_or_create(
                name=name,
                defaults=defaults,
            )
            result[name] = standard
        for name, defaults in existing_standard_defaults.items():
            standard, _created = EcoStandard.objects.get_or_create(
                name=name,
                defaults=defaults,
            )
            result[name] = standard
        return result

    def _seed_locations(self):
        for city, latitude, longitude in self.MOSCOW_OBLAST_LOCATIONS:
            self._update_location(
                city,
                latitude,
                longitude,
                f"{city}, Московская область, Россия",
            )
        for city, latitude, longitude in self.REGIONAL_LOCATIONS:
            self._update_location(city, latitude, longitude, f"{city}, Россия")

    def _update_location(self, city, latitude, longitude, address):
        Location.objects.update_or_create(
            name=city,
            defaults={
                "address": address,
                "latitude": Decimal(latitude),
                "longitude": Decimal(longitude),
                "is_active": True,
            },
        )

    def _seed_transports(self, standards):
        transports = (
            ("Н555НН777", "КАМАЗ 65115", Transport.Category.N3, 15000, "35.00", "Euro IV", 2016),
            (
                "Р666РР777",
                "Урал NEXT 4320",
                Transport.Category.N3,
                12000,
                "36.00",
                "Euro V",
                2019,
            ),
            ("Т777ТТ777", "МАЗ 6312", Transport.Category.N3, 14000, "33.00", "Euro V", 2017),
            ("У888УУ777", "КАМАЗ 43253", Transport.Category.N2, 7500, "24.00", "Euro IV", 2015),
            (
                "Х999ХХ777",
                "Hyundai Mighty",
                Transport.Category.N2,
                4500,
                "15.00",
                "Euro V",
                2019,
            ),
        )

        for (
            plate_number,
            model,
            category,
            capacity_kg,
            fuel_consumption,
            standard_name,
            year,
        ) in transports:
            Transport.objects.update_or_create(
                plate_number=plate_number,
                defaults={
                    "model": model,
                    "category": category,
                    "fuel_type": Transport.FuelType.DIESEL,
                    "capacity_kg": capacity_kg,
                    "fuel_consumption_l_per_100km": Decimal(fuel_consumption),
                    "eco_standard": standards[standard_name],
                    "year": year,
                    "is_active": True,
                },
            )
