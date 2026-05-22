from django.conf import settings
from django.db import models
from django.utils import timezone

from .storage import DocumentArchiveStorage


def archived_document_upload_to(_instance, filename):
    created_at = timezone.now()
    return f"document_archive/{created_at:%Y/%m/%d}/{filename}"


class ArchivedDocument(models.Model):
    class DocumentType(models.TextChoices):
        WAYBILL_PDF = "waybill_pdf", "Путевой лист PDF"
        EMISSIONS_PDF = "emissions_pdf", "Отчет по выбросам PDF"
        EMISSIONS_XLSX = "emissions_xlsx", "Отчет по выбросам Excel"
        ADMIN_ANALYTICS_XLSX = "admin_analytics_xlsx", "Сводка компании Excel"
        TRIPS_XLSX = "trips_xlsx", "Экспорт рейсов Excel"

    class FileFormat(models.TextChoices):
        PDF = "pdf", "PDF"
        XLSX = "xlsx", "XLSX"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Владелец",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="archived_documents",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Создал",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_archived_documents",
    )
    document_type = models.CharField(
        "Тип документа",
        max_length=32,
        choices=DocumentType.choices,
    )
    file_format = models.CharField(
        "Формат файла",
        max_length=8,
        choices=FileFormat.choices,
    )
    title = models.CharField("Название", max_length=200)
    file = models.FileField(
        "Файл",
        upload_to=archived_document_upload_to,
        storage=DocumentArchiveStorage(),
    )
    related_order = models.ForeignKey(
        "orders.ShipmentOrder",
        verbose_name="Связанная заявка",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="archived_documents",
    )
    related_trip = models.ForeignKey(
        "trips.Trip",
        verbose_name="Связанный рейс",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="archived_documents",
    )
    date_from = models.DateField("Дата с", blank=True, null=True)
    date_to = models.DateField("Дата по", blank=True, null=True)
    file_size_bytes = models.PositiveIntegerField("Размер файла, байт", default=0)
    metadata_json = models.JSONField("Метаданные", default=dict, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Архивный документ"
        verbose_name_plural = "Архивные документы"

    def __str__(self) -> str:
        return self.title
