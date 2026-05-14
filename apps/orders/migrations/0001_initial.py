from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("fleet", "0001_initial"),
        ("locations", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ShipmentOrder",
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
                    "cargo_name",
                    models.CharField(max_length=150, verbose_name="Наименование груза"),
                ),
                (
                    "cargo_type",
                    models.CharField(max_length=120, verbose_name="Тип груза"),
                ),
                (
                    "cargo_weight_kg",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                        verbose_name="Вес груза, кг",
                    ),
                ),
                (
                    "desired_delivery_date",
                    models.DateField(verbose_name="Желаемая дата доставки"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "Новая"),
                            ("calculated", "Рассчитана"),
                            ("planned", "Запланирована"),
                            ("completed", "Завершена"),
                            ("cancelled", "Отменена"),
                        ],
                        default="new",
                        max_length=20,
                        verbose_name="Статус",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Примечания")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Создана"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Обновлена"),
                ),
                (
                    "manager",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="shipment_orders",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Менеджер",
                    ),
                ),
                (
                    "transport",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="shipment_orders",
                        to="fleet.transport",
                        verbose_name="Транспорт",
                    ),
                ),
            ],
            options={
                "verbose_name": "Заявка на перевозку",
                "verbose_name_plural": "Заявки на перевозку",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="OrderPoint",
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
                    "sequence",
                    models.PositiveIntegerField(
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="Порядок",
                    ),
                ),
                (
                    "point_type",
                    models.CharField(
                        choices=[
                            ("pickup", "Погрузка"),
                            ("delivery", "Доставка"),
                            ("stop", "Промежуточная точка"),
                        ],
                        max_length=20,
                        verbose_name="Тип точки",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Создана"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Обновлена"),
                ),
                (
                    "location",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_points",
                        to="locations.location",
                        verbose_name="Локация",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="points",
                        to="orders.shipmentorder",
                        verbose_name="Заявка",
                    ),
                ),
            ],
            options={
                "verbose_name": "Точка заявки",
                "verbose_name_plural": "Точки заявки",
                "ordering": ("order", "sequence"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("order", "sequence"), name="unique_order_point_sequence"
                    )
                ],
            },
        ),
    ]
