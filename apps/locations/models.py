from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Location(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    address = models.CharField("Адрес", max_length=255, blank=True)
    latitude = models.DecimalField(
        "Широта",
        max_digits=8,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("-90")), MaxValueValidator(Decimal("90"))],
    )
    longitude = models.DecimalField(
        "Долгота",
        max_digits=8,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("-180")), MaxValueValidator(Decimal("180"))],
    )
    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Локация"
        verbose_name_plural = "Локации"

    def __str__(self) -> str:
        return self.name
