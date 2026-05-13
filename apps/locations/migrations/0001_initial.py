from decimal import Decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Location",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=120, unique=True, verbose_name="Название"
                    ),
                ),
                (
                    "address",
                    models.CharField(blank=True, max_length=255, verbose_name="Адрес"),
                ),
                (
                    "latitude",
                    models.DecimalField(
                        decimal_places=4,
                        max_digits=8,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("-90")),
                            django.core.validators.MaxValueValidator(Decimal("90")),
                        ],
                        verbose_name="Широта",
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        decimal_places=4,
                        max_digits=8,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("-180")),
                            django.core.validators.MaxValueValidator(Decimal("180")),
                        ],
                        verbose_name="Долгота",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Активна"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Создана"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Обновлена"),
                ),
            ],
            options={
                "verbose_name": "Локация",
                "verbose_name_plural": "Локации",
                "ordering": ("name",),
            },
        ),
    ]
