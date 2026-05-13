from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.fleet.models import EcoCalculationSettings, EcoStandard, Transport
from apps.locations.models import Location


class Command(BaseCommand):
    help = "Создает демонстрационные данные EcoLogist."

    def handle(self, *args, **options):
        self._seed_users()
        standards = self._seed_eco_standards()
        self._seed_transports(standards)
        self._seed_locations()
        self._seed_settings()
        self.stdout.write(self.style.SUCCESS("Демонстрационные данные EcoLogist обновлены."))

    def _seed_users(self):
        User = get_user_model()
        users = [
            {
                "username": "admin_demo",
                "email": "admin@example.com",
                "password": "Admin12345!",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "manager_demo",
                "email": "manager@example.com",
                "password": "Manager12345!",
                "role": User.Role.MANAGER,
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        for data in users:
            password = data.pop("password")
            user, _created = User.objects.get_or_create(username=data["username"])
            for field_name, value in data.items():
                setattr(user, field_name, value)
            user.set_password(password)
            user.save()

    def _seed_eco_standards(self):
        standards = {
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
        for name, defaults in standards.items():
            standard, _created = EcoStandard.objects.update_or_create(
                name=name,
                defaults=defaults,
            )
            result[name] = standard
        return result

    def _seed_transports(self, standards):
        transports = [
            ("А111АА777", "КАМАЗ 5490", "N3", Decimal("20000"), Decimal("29.00"), "Euro VI", 2021),
            ("В222ВВ777", "МАЗ 5440", "N3", Decimal("20000"), Decimal("32.00"), "Euro V", 2018),
            ("С333СС777", "ГАЗон NEXT", "N2", Decimal("5000"), Decimal("17.00"), "Euro V", 2020),
            (
                "Е444ЕЕ777",
                "Isuzu Forward",
                "N2",
                Decimal("7000"),
                Decimal("19.00"),
                "Euro VI",
                2022,
            ),
        ]

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
                    "capacity_kg": int(capacity_kg),
                    "fuel_consumption_l_per_100km": fuel_consumption,
                    "eco_standard": standards[standard_name],
                    "year": year,
                    "is_active": True,
                },
            )

    def _seed_locations(self):
        locations = [
            ("Москва", Decimal("55.7558"), Decimal("37.6173")),
            ("Подольск", Decimal("55.4312"), Decimal("37.5447")),
            ("Химки", Decimal("55.8887"), Decimal("37.4300")),
            ("Мытищи", Decimal("55.9105"), Decimal("37.7363")),
            ("Балашиха", Decimal("55.7963"), Decimal("37.9382")),
            ("Одинцово", Decimal("55.6789"), Decimal("37.2636")),
            ("Домодедово", Decimal("55.4408"), Decimal("37.7618")),
            ("Красногорск", Decimal("55.8311"), Decimal("37.3302")),
            ("Люберцы", Decimal("55.6765"), Decimal("37.8986")),
            ("Зеленоград", Decimal("55.9825"), Decimal("37.1814")),
        ]

        for name, latitude, longitude in locations:
            Location.objects.update_or_create(
                name=name,
                defaults={
                    "address": f"{name}, Москва и Московская область",
                    "latitude": latitude,
                    "longitude": longitude,
                    "is_active": True,
                },
            )

    def _seed_settings(self):
        settings, _created = EcoCalculationSettings.objects.get_or_create(
            name=EcoCalculationSettings.DEFAULT_NAME,
            defaults={
                **EcoCalculationSettings.default_values(),
                "is_active": True,
            },
        )
        for field_name, value in EcoCalculationSettings.default_values().items():
            setattr(settings, field_name, value)
        settings.is_active = True
        settings.save()
