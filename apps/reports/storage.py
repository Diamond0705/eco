from django.conf import settings
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.deconstruct import deconstructible


def _build_document_archive_storage():
    if getattr(settings, "USE_S3_STORAGE", False):
        from storages.backends.s3boto3 import S3Boto3Storage

        return S3Boto3Storage(file_overwrite=False)
    return FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)


@deconstructible
class DocumentArchiveStorage(Storage):
    def _wrapped(self):
        return _build_document_archive_storage()

    def _open(self, name, mode="rb"):
        return self._wrapped().open(name, mode)

    def _save(self, name, content):
        return self._wrapped().save(name, content)

    def delete(self, name):
        return self._wrapped().delete(name)

    def exists(self, name):
        return self._wrapped().exists(name)

    def size(self, name):
        return self._wrapped().size(name)

    def url(self, name):
        return self._wrapped().url(name)

    def path(self, name):
        return self._wrapped().path(name)

    def get_available_name(self, name, max_length=None):
        return self._wrapped().get_available_name(name, max_length=max_length)

    def get_valid_name(self, name):
        return self._wrapped().get_valid_name(name)
