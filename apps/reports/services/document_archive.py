from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.reports.models import ArchivedDocument

CONTENT_TYPES = {
    ArchivedDocument.FileFormat.PDF: "application/pdf",
    ArchivedDocument.FileFormat.XLSX: (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
}


class DocumentArchiveDisabledError(RuntimeError):
    pass


class DocumentArchiveService:
    def save_document(
        self,
        *,
        content_bytes,
        document_type,
        file_format,
        title,
        owner=None,
        created_by=None,
        related_order=None,
        related_trip=None,
        date_from=None,
        date_to=None,
        metadata=None,
    ):
        if not getattr(settings, "DOCUMENT_ARCHIVE_ENABLED", True):
            raise DocumentArchiveDisabledError("Document archive is disabled.")

        document = ArchivedDocument(
            owner=owner,
            created_by=created_by,
            document_type=document_type,
            file_format=file_format,
            title=title,
            related_order=related_order,
            related_trip=related_trip,
            date_from=date_from,
            date_to=date_to,
            file_size_bytes=len(content_bytes),
            metadata_json=metadata or {},
        )
        document.file.save(
            self._filename(document_type, file_format),
            ContentFile(content_bytes),
            save=False,
        )
        document.save()
        return document

    def content_type_for(self, document):
        return CONTENT_TYPES.get(document.file_format, "application/octet-stream")

    def download_filename(self, document):
        if document.file.name:
            return Path(document.file.name).name
        return self._filename(document.document_type, document.file_format)

    def _filename(self, document_type, file_format):
        timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
        suffix = uuid4().hex[:8]
        return f"{document_type}_{timestamp}_{suffix}.{file_format}"
