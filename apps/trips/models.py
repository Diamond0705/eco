from django.conf import settings
from django.db import models


class Trip(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Запланирован"
        IN_PROGRESS = "in_progress", "В пути"
        DELIVERED = "delivered", "Доставлен"
        CANCELLED = "cancelled", "Отменен"

    order = models.OneToOneField(
        "orders.ShipmentOrder",
        verbose_name="Заявка",
        on_delete=models.PROTECT,
        related_name="trip",
    )
    route_option = models.ForeignKey(
        "routing.RouteOption",
        verbose_name="Выбранный маршрут",
        on_delete=models.PROTECT,
        related_name="trips",
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    planned_start_at = models.DateTimeField("Плановое начало", blank=True, null=True)
    actual_start_at = models.DateTimeField("Фактическое начало", blank=True, null=True)
    actual_finish_at = models.DateTimeField("Фактическое завершение", blank=True, null=True)
    waybill_pdf = models.FileField("PDF-путевой лист", upload_to="waybills/", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Рейс"
        verbose_name_plural = "Рейсы"

    def __str__(self) -> str:
        return f"Рейс №{self.pk} по заявке №{self.order_id}"


class TripStatusEvent(models.Model):
    trip = models.ForeignKey(
        Trip,
        verbose_name="Рейс",
        on_delete=models.CASCADE,
        related_name="status_events",
    )
    old_status = models.CharField(
        "Предыдущий статус",
        max_length=20,
        choices=Trip.Status.choices,
        blank=True,
    )
    new_status = models.CharField(
        "Новый статус",
        max_length=20,
        choices=Trip.Status.choices,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Изменил",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="trip_status_events",
    )
    changed_at = models.DateTimeField("Время изменения", auto_now_add=True)
    event_at = models.DateTimeField("Фактическое время события", blank=True, null=True)
    comment = models.TextField("Комментарий", blank=True)

    class Meta:
        ordering = ("changed_at",)
        verbose_name = "Событие статуса рейса"
        verbose_name_plural = "События статусов рейсов"

    def __str__(self) -> str:
        return f"{self.trip_id}: {self.old_status or '-'} -> {self.new_status}"
