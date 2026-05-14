from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.fleet.models import Transport
from apps.locations.models import Location


class ShipmentOrder(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        CALCULATED = "calculated", "Рассчитана"
        PLANNED = "planned", "Запланирована"
        COMPLETED = "completed", "Завершена"
        CANCELLED = "cancelled", "Отменена"

    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Менеджер",
        on_delete=models.PROTECT,
        related_name="shipment_orders",
    )
    transport = models.ForeignKey(
        Transport,
        verbose_name="Транспорт",
        on_delete=models.PROTECT,
        related_name="shipment_orders",
    )
    cargo_name = models.CharField("Наименование груза", max_length=150)
    cargo_type = models.CharField("Тип груза", max_length=120)
    cargo_weight_kg = models.DecimalField(
        "Вес груза, кг",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    desired_delivery_date = models.DateField("Желаемая дата доставки")
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    notes = models.TextField("Примечания", blank=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Заявка на перевозку"
        verbose_name_plural = "Заявки на перевозку"

    def __str__(self) -> str:
        if self.pk:
            return f"Заявка №{self.pk}: {self.cargo_name}"
        return f"Новая заявка: {self.cargo_name}"

    def clean(self):
        super().clean()
        if self.transport_id and self.cargo_weight_kg:
            if self.cargo_weight_kg > Decimal(self.transport.capacity_kg):
                raise ValidationError(
                    {"cargo_weight_kg": "Вес груза превышает грузоподъемность транспорта."}
                )


class OrderPoint(models.Model):
    class PointType(models.TextChoices):
        PICKUP = "pickup", "Погрузка"
        DELIVERY = "delivery", "Доставка"
        STOP = "stop", "Промежуточная точка"

    order = models.ForeignKey(
        ShipmentOrder,
        verbose_name="Заявка",
        on_delete=models.CASCADE,
        related_name="points",
    )
    location = models.ForeignKey(
        Location,
        verbose_name="Локация",
        on_delete=models.PROTECT,
        related_name="order_points",
    )
    sequence = models.PositiveIntegerField(
        "Порядок",
        validators=[MinValueValidator(1)],
    )
    point_type = models.CharField("Тип точки", max_length=20, choices=PointType.choices)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        ordering = ("order", "sequence")
        constraints = [
            models.UniqueConstraint(
                fields=("order", "sequence"),
                name="unique_order_point_sequence",
            )
        ]
        verbose_name = "Точка заявки"
        verbose_name_plural = "Точки заявки"

    def __str__(self) -> str:
        return f"{self.sequence}. {self.get_point_type_display()}: {self.location}"
