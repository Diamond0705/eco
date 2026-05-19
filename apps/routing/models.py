from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class RouteOption(models.Model):
    class Provider(models.TextChoices):
        MOCK = "mock", "Mock"
        GRAPHHOPPER = "graphhopper", "GraphHopper"

    order = models.ForeignKey(
        "orders.ShipmentOrder",
        verbose_name="Заявка",
        on_delete=models.CASCADE,
        related_name="route_options",
    )
    name = models.CharField("Название", max_length=100)
    provider = models.CharField(
        "Провайдер",
        max_length=20,
        choices=Provider.choices,
        default=Provider.MOCK,
    )
    distance_km = models.DecimalField(
        "Расстояние, км",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    duration_minutes = models.PositiveIntegerField("Время, мин")
    fuel_multiplier = models.DecimalField(
        "Множитель расхода",
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    fuel_liters = models.DecimalField(
        "Топливо, л",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    cost_rub = models.DecimalField(
        "Стоимость, руб",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    co2_kg = models.DecimalField(
        "CO2, кг",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    nox_g = models.DecimalField(
        "NOx, г",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    pm_g = models.DecimalField(
        "PM, г",
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.000"))],
    )
    eco_rating = models.DecimalField(
        "Эко-рейтинг",
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
    )
    geometry_json = models.JSONField("Геометрия маршрута")
    route_facts_json = models.JSONField("Факты маршрута", default=dict, blank=True)
    calculation_settings = models.ForeignKey(
        "fleet.EcoCalculationSettings",
        verbose_name="Настройки расчета",
        on_delete=models.PROTECT,
        related_name="route_options",
    )
    is_selected = models.BooleanField("Выбран", default=False)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)

    class Meta:
        ordering = ("order", "created_at")
        verbose_name = "Вариант маршрута"
        verbose_name_plural = "Варианты маршрутов"

    def __str__(self) -> str:
        return f"{self.name}: заявка №{self.order_id}"
