from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EcoStandard",
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
                        max_length=100, unique=True, verbose_name="Название"
                    ),
                ),
                (
                    "nox_limit_g_per_kwh",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=6,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="NOx, г/кВт·ч",
                    ),
                ),
                (
                    "pm_limit_mg_per_kwh",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=7,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="PM, мг/кВт·ч",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Активен"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Создан"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Обновлен"),
                ),
            ],
            options={
                "verbose_name": "Экологический стандарт",
                "verbose_name_plural": "Экологические стандарты",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="EcoCalculationSettings",
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
                        max_length=150, unique=True, verbose_name="Название"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=False, verbose_name="Активны"),
                ),
                (
                    "diesel_co2_kg_per_liter",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="CO2 дизеля, кг/л",
                    ),
                ),
                (
                    "engine_work_kwh_per_km",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Работа двигателя, кВт·ч/км",
                    ),
                ),
                (
                    "fuel_price_rub_per_liter",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Цена топлива, руб/л",
                    ),
                ),
                (
                    "service_tariff_rub_per_km",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Тариф сервиса, руб/км",
                    ),
                ),
                (
                    "full_load_fuel_increase_percent",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Рост расхода при полной загрузке, %",
                    ),
                ),
                (
                    "co2_weight",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=4,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Вес CO2",
                    ),
                ),
                (
                    "nox_weight",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=4,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Вес NOx",
                    ),
                ),
                (
                    "pm_weight",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=4,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Вес PM",
                    ),
                ),
                (
                    "co2_critical_kg",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Критический CO2, кг",
                    ),
                ),
                (
                    "nox_critical_g",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Критический NOx, г",
                    ),
                ),
                (
                    "pm_critical_g",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Критический PM, г",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Созданы"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Обновлены"),
                ),
            ],
            options={
                "verbose_name": "Настройки экологического расчета",
                "verbose_name_plural": "Настройки экологического расчета",
                "ordering": ("-created_at",),
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("is_active", True)),
                        fields=("is_active",),
                        name="unique_active_eco_calculation_settings",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Transport",
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
                    "plate_number",
                    models.CharField(
                        max_length=20, unique=True, verbose_name="Госномер"
                    ),
                ),
                ("model", models.CharField(max_length=120, verbose_name="Модель")),
                (
                    "category",
                    models.CharField(
                        choices=[("N2", "N2"), ("N3", "N3")],
                        max_length=2,
                        verbose_name="Категория",
                    ),
                ),
                (
                    "fuel_type",
                    models.CharField(
                        choices=[("diesel", "Дизель")],
                        default="diesel",
                        max_length=20,
                        verbose_name="Тип топлива",
                    ),
                ),
                (
                    "capacity_kg",
                    models.PositiveIntegerField(
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="Грузоподъемность, кг",
                    ),
                ),
                (
                    "fuel_consumption_l_per_100km",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=6,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Расход топлива, л/100 км",
                    ),
                ),
                (
                    "year",
                    models.PositiveIntegerField(
                        validators=[django.core.validators.MinValueValidator(1900)],
                        verbose_name="Год выпуска",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Активен"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Создан"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Обновлен"),
                ),
                (
                    "eco_standard",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transports",
                        to="fleet.ecostandard",
                        verbose_name="Экологический стандарт",
                    ),
                ),
            ],
            options={
                "verbose_name": "Транспорт",
                "verbose_name_plural": "Транспорт",
                "ordering": ("plate_number",),
            },
        ),
    ]
