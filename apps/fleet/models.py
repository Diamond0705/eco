from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q


class EcoStandard(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    nox_limit_g_per_kwh = models.DecimalField(
        "NOx, г/кВт·ч",
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    pm_limit_mg_per_kwh = models.DecimalField(
        "PM, мг/кВт·ч",
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Экологический стандарт"
        verbose_name_plural = "Экологические стандарты"

    def __str__(self) -> str:
        return self.name


class Transport(models.Model):
    class Category(models.TextChoices):
        N2 = "N2", "N2"
        N3 = "N3", "N3"

    class FuelType(models.TextChoices):
        DIESEL = "diesel", "Дизель"

    plate_number = models.CharField("Госномер", max_length=20, unique=True)
    model = models.CharField("Модель", max_length=120)
    category = models.CharField("Категория", max_length=2, choices=Category.choices)
    fuel_type = models.CharField(
        "Тип топлива",
        max_length=20,
        choices=FuelType.choices,
        default=FuelType.DIESEL,
    )
    capacity_kg = models.PositiveIntegerField(
        "Грузоподъемность, кг",
        validators=[MinValueValidator(1)],
    )
    fuel_consumption_l_per_100km = models.DecimalField(
        "Расход топлива, л/100 км",
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    eco_standard = models.ForeignKey(
        EcoStandard,
        verbose_name="Экологический стандарт",
        on_delete=models.PROTECT,
        related_name="transports",
    )
    year = models.PositiveIntegerField("Год выпуска", validators=[MinValueValidator(1900)])
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)

    class Meta:
        ordering = ("plate_number",)
        verbose_name = "Транспорт"
        verbose_name_plural = "Транспорт"

    def __str__(self) -> str:
        return f"{self.plate_number} — {self.model}"


class EcoCalculationSettings(models.Model):
    DEFAULT_NAME = "Базовые настройки 2026"

    name = models.CharField("Название", max_length=150, unique=True)
    is_active = models.BooleanField("Активны", default=False)
    diesel_co2_kg_per_liter = models.DecimalField(
        "CO2 дизеля, кг/л",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    engine_work_kwh_per_km = models.DecimalField(
        "Работа двигателя, кВт·ч/км",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    fuel_price_rub_per_liter = models.DecimalField(
        "Цена топлива, руб/л",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    service_tariff_rub_per_km = models.DecimalField(
        "Тариф сервиса, руб/км",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    full_load_fuel_increase_percent = models.DecimalField(
        "Рост расхода при полной загрузке, %",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    co2_weight = models.DecimalField(
        "Вес CO2",
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    nox_weight = models.DecimalField(
        "Вес NOx",
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    pm_weight = models.DecimalField(
        "Вес PM",
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    co2_critical_kg = models.DecimalField(
        "Критический CO2, кг",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    nox_critical_g = models.DecimalField(
        "Критический NOx, г",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    pm_critical_g = models.DecimalField(
        "Критический PM, г",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    created_at = models.DateTimeField("Созданы", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлены", auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("is_active",),
                condition=Q(is_active=True),
                name="unique_active_eco_calculation_settings",
            )
        ]
        verbose_name = "Настройки экологического расчета"
        verbose_name_plural = "Настройки экологического расчета"

    def __str__(self) -> str:
        return self.name

    @classmethod
    def default_values(cls):
        return {
            "diesel_co2_kg_per_liter": Decimal("2.69"),
            "engine_work_kwh_per_km": Decimal("1.20"),
            "fuel_price_rub_per_liter": Decimal("78.15"),
            "service_tariff_rub_per_km": Decimal("175.00"),
            "full_load_fuel_increase_percent": Decimal("20.00"),
            "co2_weight": Decimal("0.50"),
            "nox_weight": Decimal("0.30"),
            "pm_weight": Decimal("0.20"),
            "co2_critical_kg": Decimal("100.00"),
            "nox_critical_g": Decimal("300.00"),
            "pm_critical_g": Decimal("10.00"),
        }

    @classmethod
    def get_current(cls):
        active_settings = cls.objects.filter(is_active=True).order_by("-created_at").first()
        if active_settings is not None:
            return active_settings

        settings, _created = cls.objects.get_or_create(
            name=cls.DEFAULT_NAME,
            defaults={**cls.default_values(), "is_active": True},
        )
        if not settings.is_active:
            for field_name, value in cls.default_values().items():
                setattr(settings, field_name, value)
            settings.is_active = True
            settings.save()
        return settings

    def save(self, *args, **kwargs):
        if not self.is_active:
            return super().save(*args, **kwargs)

        with transaction.atomic():
            queryset = type(self).objects.filter(is_active=True)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            queryset.update(is_active=False)
            return super().save(*args, **kwargs)
