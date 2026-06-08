from django.conf import settings
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.deconstruct import deconstructible


def _build_profile_avatar_storage():
    location = getattr(settings, "PROFILE_AVATAR_LOCATION", "profile_avatars")
    if getattr(settings, "USE_S3_STORAGE", False):
        from storages.backends.s3boto3 import S3Boto3Storage

        return S3Boto3Storage(file_overwrite=False, location=location)

    return FileSystemStorage(
        location=settings.PROTECTED_MEDIA_ROOT / location,
        base_url=None,
    )


@deconstructible
class ProfileAvatarStorage(Storage):
    def _wrapped(self):
        return _build_profile_avatar_storage()

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

    def get_available_name(self, name, max_length=None):
        return self._wrapped().get_available_name(name, max_length=max_length)

    def get_valid_name(self, name):
        return self._wrapped().get_valid_name(name)
