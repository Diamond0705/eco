import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

User = get_user_model()


@pytest.fixture(autouse=True)
def local_avatar_storage(settings, tmp_path):
    settings.USE_S3_STORAGE = False
    settings.PROTECTED_MEDIA_ROOT = tmp_path / "protected_media"
    settings.PROFILE_AVATAR_LOCATION = "profile_avatars"


@pytest.fixture
def profile_user(db):
    return User.objects.create_user(
        username="profile_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
        first_name="Ирина",
        last_name="Логистова",
        middle_name="Петровна",
        email="profile@example.test",
        phone="+7 (999) 111-22-33",
    )


def png_file(name="avatar.png", content=b"\x89PNG\r\n\x1a\nprofile"):
    return SimpleUploadedFile(name, content, content_type="image/png")


def webp_file(name="avatar.webp"):
    return SimpleUploadedFile(
        name,
        b"RIFF\x10\x00\x00\x00WEBPVP8 profile",
        content_type="image/webp",
    )


@pytest.mark.django_db
def test_anonymous_profile_api_is_rejected(client):
    response = client.get(reverse("api:profile"))

    assert response.status_code == 401


@pytest.mark.django_db
def test_profile_api_returns_safe_current_user_fields(client, profile_user):
    client.force_login(profile_user)

    response = client.get(reverse("api:profile"))

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "id": profile_user.pk,
        "username": "profile_manager",
        "first_name": "Ирина",
        "last_name": "Логистова",
        "middle_name": "Петровна",
        "email": "profile@example.test",
        "phone": "+7 (999) 111-22-33",
        "role": User.Role.MANAGER,
        "avatar_exists": False,
    }
    assert "avatar" not in payload
    assert "is_staff" not in payload
    assert "is_superuser" not in payload
    assert "password" not in payload


@pytest.mark.django_db
def test_profile_patch_updates_allowed_fields_only(client, profile_user):
    client.force_login(profile_user)

    response = client.patch(
        reverse("api:profile"),
        {
            "username": "changed",
            "role": User.Role.ADMIN,
            "is_staff": True,
            "is_superuser": True,
            "first_name": "Анна",
            "last_name": "Новая",
            "middle_name": "Сергеевна",
            "email": "updated@example.test",
            "phone": "+7 (999) 222-33-44",
        },
        content_type="application/json",
    )
    profile_user.refresh_from_db()

    assert response.status_code == 200
    assert profile_user.username == "profile_manager"
    assert profile_user.role == User.Role.MANAGER
    assert not profile_user.is_staff
    assert not profile_user.is_superuser
    assert profile_user.first_name == "Анна"
    assert profile_user.last_name == "Новая"
    assert profile_user.middle_name == "Сергеевна"
    assert profile_user.email == "updated@example.test"
    assert profile_user.phone == "+7 (999) 222-33-44"


@pytest.mark.django_db
def test_avatar_api_upload_download_replace_and_delete(client, profile_user, settings):
    client.force_login(profile_user)

    upload_response = client.post(reverse("api:profile_avatar"), {"avatar": png_file()})
    profile_user.refresh_from_db()
    first_avatar_name = profile_user.avatar.name
    first_avatar_path = (
        settings.PROTECTED_MEDIA_ROOT / settings.PROFILE_AVATAR_LOCATION / first_avatar_name
    )

    assert upload_response.status_code == 200
    assert upload_response.json()["avatar_exists"] is True
    assert "profile_avatars" not in upload_response.content.decode()
    assert first_avatar_name
    assert first_avatar_path.exists()

    replace_response = client.post(reverse("api:profile_avatar"), {"avatar": webp_file()})
    profile_user.refresh_from_db()
    second_avatar_name = profile_user.avatar.name
    second_avatar_path = (
        settings.PROTECTED_MEDIA_ROOT / settings.PROFILE_AVATAR_LOCATION / second_avatar_name
    )

    assert replace_response.status_code == 200
    assert second_avatar_name != first_avatar_name
    assert not first_avatar_path.exists()
    assert second_avatar_path.exists()

    delete_response = client.delete(reverse("api:profile_avatar"))
    profile_user.refresh_from_db()

    assert delete_response.status_code == 204
    assert not profile_user.avatar
    assert not second_avatar_path.exists()
    assert client.get(reverse("api:profile_avatar")).status_code == 404


@pytest.mark.django_db
def test_avatar_api_download_returns_current_user_file(client, profile_user):
    client.force_login(profile_user)
    client.post(reverse("api:profile_avatar"), {"avatar": png_file()})

    response = client.get(reverse("api:profile_avatar"))

    assert response.status_code == 200
    assert response["Content-Type"] == "image/png"
    assert b"".join(response.streaming_content) == b"\x89PNG\r\n\x1a\nprofile"


@pytest.mark.django_db
def test_avatar_api_validates_type_and_size(client, profile_user):
    client.force_login(profile_user)
    invalid_file = SimpleUploadedFile("avatar.gif", b"GIF89a", content_type="image/gif")
    too_large = SimpleUploadedFile(
        "avatar.png",
        b"\x89PNG\r\n\x1a\n" + b"x" * (5 * 1024 * 1024 + 1),
        content_type="image/png",
    )

    invalid_response = client.post(reverse("api:profile_avatar"), {"avatar": invalid_file})
    too_large_response = client.post(reverse("api:profile_avatar"), {"avatar": too_large})

    assert invalid_response.status_code == 400
    assert "Недопустимый формат файла" in str(invalid_response.json())
    assert too_large_response.status_code == 400
    assert "Файл слишком большой" in str(too_large_response.json())
