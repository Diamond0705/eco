import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from apps.accounts.forms import (
    ManagerRegistrationForm,
    ProfileAvatarUploadForm,
    ProfileUpdateForm,
)

User = get_user_model()

PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
JPG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF"


def avatar_file(name="avatar.png", content=PNG_BYTES, content_type="image/png"):
    return SimpleUploadedFile(name, content, content_type=content_type)


@pytest.mark.django_db
def test_registration_creates_manager_user(client):
    response = client.post(
        reverse("accounts:register"),
        {
            "username": "manager1",
            "email": "manager@example.com",
            "first_name": "Иван",
            "last_name": "Петров",
            "middle_name": "Сергеевич",
            "phone": "+79990000000",
            "password1": "StrongPass12345",
            "password2": "StrongPass12345",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("accounts:login")

    user = User.objects.get(username="manager1")
    assert user.role == User.Role.MANAGER
    assert user.email == "manager@example.com"
    assert user.phone == "+7 (999) 000-00-00"


@pytest.mark.django_db
def test_registration_form_rejects_duplicate_email_case_insensitive(client):
    User.objects.create_user(
        username="existing",
        email="manager@example.com",
        password="StrongPass12345",
    )

    response = client.post(
        reverse("accounts:register"),
        {
            "username": "newmanager",
            "email": "MANAGER@example.com",
            "password1": "StrongPass12345",
            "password2": "StrongPass12345",
        },
    )

    assert response.status_code == 200
    assert "Пользователь с таким email уже зарегистрирован" in response.content.decode()
    assert not User.objects.filter(username="newmanager").exists()


@pytest.mark.django_db
def test_registration_form_rejects_duplicate_username(client):
    User.objects.create_user(
        username="busy_nickname",
        email="busy@example.com",
        password="StrongPass12345",
    )

    response = client.post(
        reverse("accounts:register"),
        {
            "username": "busy_nickname",
            "email": "new-busy@example.com",
            "password1": "StrongPass12345",
            "password2": "StrongPass12345",
        },
    )

    assert response.status_code == 200
    assert "Пользователь с таким никнеймом уже зарегистрирован" in response.content.decode()
    assert not User.objects.filter(email="new-busy@example.com").exists()


@pytest.mark.django_db
def test_registration_form_rejects_duplicate_username_case_insensitive(client):
    User.objects.create_user(
        username="CaseNickname",
        email="case@example.com",
        password="StrongPass12345",
    )

    response = client.post(
        reverse("accounts:register"),
        {
            "username": "casenickname",
            "email": "new-case@example.com",
            "password1": "StrongPass12345",
            "password2": "StrongPass12345",
        },
    )

    assert response.status_code == 200
    assert "Пользователь с таким никнеймом уже зарегистрирован" in response.content.decode()
    assert not User.objects.filter(email="new-case@example.com").exists()


@pytest.mark.django_db
def test_registration_allows_same_full_name_with_different_unique_nicknames(client):
    first_response = client.post(
        reverse("accounts:register"),
        {
            "username": "same_name_one",
            "email": "same-name-one@example.com",
            "first_name": "Иван",
            "last_name": "Петров",
            "middle_name": "Сергеевич",
            "password1": "StrongPass12345",
            "password2": "StrongPass12345",
        },
    )
    second_response = client.post(
        reverse("accounts:register"),
        {
            "username": "same_name_two",
            "email": "same-name-two@example.com",
            "first_name": "Иван",
            "last_name": "Петров",
            "middle_name": "Сергеевич",
            "password1": "StrongPass12345",
            "password2": "StrongPass12345",
        },
    )

    assert first_response.status_code == 302
    assert second_response.status_code == 302
    assert User.objects.filter(first_name="Иван", last_name="Петров").count() == 2


@pytest.mark.django_db
def test_registration_page_explains_unique_nickname(client):
    response = client.get(reverse("accounts:register"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Уникальный никнейм" in content
    assert "Никнейм используется для входа и должен быть уникальным" in content


@pytest.mark.django_db
def test_registration_form_does_not_allow_role_selection(client):
    response = client.post(
        reverse("accounts:register"),
        {
            "username": "manager2",
            "email": "manager2@example.com",
            "password1": "StrongPass12345",
            "password2": "StrongPass12345",
            "role": User.Role.ADMIN,
        },
    )

    assert response.status_code == 302
    assert User.objects.get(username="manager2").role == User.Role.MANAGER


@pytest.mark.django_db
def test_login_works_by_username(client):
    User.objects.create_user(
        username="manager3",
        email="manager3@example.com",
        password="StrongPass12345",
    )

    response = client.post(
        reverse("accounts:login"),
        {"username": "manager3", "password": "StrongPass12345"},
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("dashboard:dashboard")


@pytest.mark.django_db
def test_login_works_by_email(client):
    User.objects.create_user(
        username="manager4",
        email="manager4@example.com",
        password="StrongPass12345",
    )

    response = client.post(
        reverse("accounts:login"),
        {"username": "manager4@example.com", "password": "StrongPass12345"},
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("dashboard:dashboard")


@pytest.mark.django_db
def test_logout_uses_post(client):
    user = User.objects.create_user(username="manager5", password="StrongPass12345")
    client.force_login(user)

    get_response = client.get(reverse("accounts:logout"))
    assert get_response.status_code == 405

    post_response = client.post(reverse("accounts:logout"))
    assert post_response.status_code == 302
    assert post_response["Location"] == reverse("accounts:login")


@pytest.mark.django_db
def test_profile_pages_are_available_to_manager_and_admin(client):
    manager = User.objects.create_user(
        username="manager6",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )
    admin = User.objects.create_user(
        username="admin1",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )

    client.force_login(manager)
    assert client.get(reverse("accounts:profile")).status_code == 200
    assert client.get(reverse("accounts:profile_edit")).status_code == 200

    client.force_login(admin)
    assert client.get(reverse("accounts:profile")).status_code == 200
    assert client.get(reverse("accounts:profile_edit")).status_code == 200


@pytest.mark.django_db
def test_profile_edit_updates_allowed_fields(client):
    user = User.objects.create_user(
        username="manager7",
        email="old@example.com",
        password="StrongPass12345",
    )
    client.force_login(user)

    response = client.post(
        reverse("accounts:profile_edit"),
        {
            "first_name": "Анна",
            "last_name": "Иванова",
            "middle_name": "Павловна",
            "email": "new@example.com",
            "phone": "+79991112233",
            "role": User.Role.ADMIN,
        },
    )

    assert response.status_code == 302

    user.refresh_from_db()
    assert user.first_name == "Анна"
    assert user.last_name == "Иванова"
    assert user.middle_name == "Павловна"
    assert user.email == "new@example.com"
    assert user.phone == "+7 (999) 111-22-33"
    assert user.role == User.Role.MANAGER


@pytest.mark.django_db
def test_profile_edit_rejects_another_users_email(client):
    user = User.objects.create_user(
        username="profile_email_owner",
        email="owner@example.com",
        password="StrongPass12345",
    )
    User.objects.create_user(
        username="profile_email_existing",
        email="existing@example.com",
        password="StrongPass12345",
    )
    client.force_login(user)

    response = client.post(
        reverse("accounts:profile_edit"),
        {
            "first_name": "Анна",
            "last_name": "Иванова",
            "middle_name": "Павловна",
            "email": "existing@example.com",
            "phone": "+79991112233",
        },
    )

    assert response.status_code == 200
    assert "Пользователь с таким email уже зарегистрирован" in response.content.decode()

    user.refresh_from_db()
    assert user.email == "owner@example.com"


@pytest.mark.django_db
def test_profile_edit_allows_own_email(client):
    user = User.objects.create_user(
        username="profile_own_email",
        email="own@example.com",
        password="StrongPass12345",
    )
    client.force_login(user)

    response = client.post(
        reverse("accounts:profile_edit"),
        {
            "first_name": "Анна",
            "last_name": "Иванова",
            "middle_name": "Павловна",
            "email": "own@example.com",
            "phone": "+79991112233",
        },
    )

    assert response.status_code == 302

    user.refresh_from_db()
    assert user.email == "own@example.com"


@pytest.mark.django_db
def test_profile_edit_contains_avatar_forms(client):
    user = User.objects.create_user(username="profile_avatar_html", password="StrongPass12345")
    client.force_login(user)

    response = client.get(reverse("accounts:profile_edit"))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'enctype="multipart/form-data"' in content
    assert reverse("accounts:profile_avatar_upload") in content
    assert "csrfmiddlewaretoken" in content
    assert 'onchange="this.form.submit()"' in content
    assert "Загрузить фото" in content


@pytest.mark.django_db
@override_settings(USE_S3_STORAGE=False)
def test_profile_avatar_upload_view_saves_valid_png(client, tmp_path, settings):
    settings.PROTECTED_MEDIA_ROOT = tmp_path / "protected"
    user = User.objects.create_user(username="profile_avatar_upload", password="StrongPass12345")
    client.force_login(user)

    response = client.post(
        reverse("accounts:profile_avatar_upload"),
        {"avatar": avatar_file()},
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("accounts:profile_edit")

    user.refresh_from_db()
    assert user.avatar.name.startswith(f"user_{user.pk}/")
    assert user.avatar.storage.exists(user.avatar.name)


@pytest.mark.django_db
@override_settings(USE_S3_STORAGE=False)
def test_profile_avatar_upload_replaces_old_file(client, tmp_path, settings):
    settings.PROTECTED_MEDIA_ROOT = tmp_path / "protected"
    user = User.objects.create_user(username="profile_avatar_replace", password="StrongPass12345")
    client.force_login(user)

    client.post(reverse("accounts:profile_avatar_upload"), {"avatar": avatar_file()})
    user.refresh_from_db()
    old_name = user.avatar.name
    assert user.avatar.storage.exists(old_name)

    response = client.post(
        reverse("accounts:profile_avatar_upload"),
        {"avatar": avatar_file("avatar.jpg", JPG_BYTES, "image/jpeg")},
    )

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.avatar.name != old_name
    assert user.avatar.name.endswith(".jpg")
    assert not user.avatar.storage.exists(old_name)
    assert user.avatar.storage.exists(user.avatar.name)


@pytest.mark.django_db
@override_settings(USE_S3_STORAGE=False)
def test_profile_avatar_delete_view_clears_field_and_file(client, tmp_path, settings):
    settings.PROTECTED_MEDIA_ROOT = tmp_path / "protected"
    user = User.objects.create_user(username="profile_avatar_delete", password="StrongPass12345")
    client.force_login(user)
    client.post(reverse("accounts:profile_avatar_upload"), {"avatar": avatar_file()})
    user.refresh_from_db()
    old_name = user.avatar.name
    assert user.avatar.storage.exists(old_name)

    response = client.post(reverse("accounts:profile_avatar_delete"))

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.avatar.name == ""
    assert not user.avatar.storage.exists(old_name)


@pytest.mark.django_db
@override_settings(USE_S3_STORAGE=False)
def test_profile_avatar_view_is_private_and_streams_current_user_avatar(client, tmp_path, settings):
    settings.PROTECTED_MEDIA_ROOT = tmp_path / "protected"
    owner = User.objects.create_user(username="profile_avatar_owner", password="StrongPass12345")
    other = User.objects.create_user(username="profile_avatar_other", password="StrongPass12345")
    client.force_login(owner)
    client.post(reverse("accounts:profile_avatar_upload"), {"avatar": avatar_file()})

    response = client.get(reverse("accounts:profile_avatar"))

    assert response.status_code == 200
    assert response["Content-Type"] == "image/png"
    assert b"".join(response.streaming_content).startswith(b"\x89PNG")

    client.logout()
    anonymous_response = client.get(reverse("accounts:profile_avatar"))
    assert anonymous_response.status_code == 302
    assert anonymous_response["Location"].startswith(reverse("accounts:login"))

    client.force_login(other)
    assert client.get(reverse("accounts:profile_avatar")).status_code == 404


@pytest.mark.django_db
def test_profile_card_uses_surname_first_initials_and_role_only(client):
    user = User.objects.create_user(
        username="profile_name_order",
        first_name="Виктория",
        last_name="Удалова",
        role=User.Role.MANAGER,
        password="StrongPass12345",
    )
    client.force_login(user)

    response = client.get(reverse("accounts:profile"))

    assert response.status_code == 200
    content = response.content.decode()
    compact_html = "".join(content.split())
    assert "УдаловаВиктория" in compact_html
    assert "УВ" in compact_html
    assert "Менеджер" in content
    assert "Аккаунт активен" not in content


def test_profile_avatar_upload_form_rejects_invalid_files():
    text_form = ProfileAvatarUploadForm(
        files={"avatar": avatar_file("avatar.txt", b"plain text", "text/plain")}
    )
    assert not text_form.is_valid()
    assert "Загрузите фото в формате JPG или PNG." in text_form.errors["avatar"]

    fake_png_form = ProfileAvatarUploadForm(
        files={"avatar": avatar_file("avatar.png", b"not a png", "image/png")}
    )
    assert not fake_png_form.is_valid()
    assert "Файл не похож на изображение JPG или PNG." in fake_png_form.errors["avatar"]

    large_form = ProfileAvatarUploadForm(
        files={"avatar": avatar_file("avatar.png", PNG_BYTES + (b"0" * (5 * 1024 * 1024)))}
    )
    assert not large_form.is_valid()
    assert "Максимальный размер файла: 5 МБ." in large_form.errors["avatar"]


@pytest.mark.django_db
def test_profile_edit_rejects_duplicate_email_case_insensitive(client):
    user = User.objects.create_user(
        username="profile_case_owner",
        email="owner_case@example.com",
        password="StrongPass12345",
    )
    User.objects.create_user(
        username="profile_case_existing",
        email="existing_case@example.com",
        password="StrongPass12345",
    )
    client.force_login(user)

    response = client.post(
        reverse("accounts:profile_edit"),
        {
            "first_name": "Анна",
            "last_name": "Иванова",
            "middle_name": "Павловна",
            "email": "EXISTING_CASE@example.com",
            "phone": "+79991112233",
        },
    )

    assert response.status_code == 200
    assert "Пользователь с таким email уже зарегистрирован" in response.content.decode()

    user.refresh_from_db()
    assert user.email == "owner_case@example.com"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "phone",
    ["", "89165743355", "+79165743355", "79165743355", "9165743355"],
)
def test_registration_form_accepts_valid_russian_phone_values(phone):
    username_suffix = str(abs(hash(phone)))
    form = ManagerRegistrationForm(
        data={
            "username": f"user_{username_suffix}",
            "email": f"user_{username_suffix}@example.com",
            "phone": phone,
            "password1": "StrongPass12345",
            "password2": "StrongPass12345",
        }
    )

    assert form.is_valid(), form.errors
    if phone:
        user = form.save()
        assert user.phone == "+7 (916) 574-33-55"


@pytest.mark.django_db
def test_registration_form_rejects_invalid_russian_phone():
    form = ManagerRegistrationForm(
        data={
            "username": "badphone",
            "email": "badphone@example.com",
            "phone": "954",
            "password1": "StrongPass12345",
            "password2": "StrongPass12345",
        }
    )

    assert not form.is_valid()
    assert "Введите телефон в формате +7 (999) 123-45-67." in form.errors["phone"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "phone",
    ["89165743355", "+79165743355", "79165743355", "9165743355"],
)
def test_profile_update_form_accepts_valid_russian_phone_values(phone):
    user = User.objects.create_user(username="phone_profile", password="StrongPass12345")
    form = ProfileUpdateForm(
        data={
            "first_name": "Анна",
            "last_name": "Иванова",
            "middle_name": "Павловна",
            "email": "phone_profile@example.com",
            "phone": phone,
        },
        instance=user,
    )

    assert form.is_valid(), form.errors
    user = form.save()
    assert user.phone == "+7 (916) 574-33-55"


@pytest.mark.django_db
def test_profile_update_form_rejects_invalid_russian_phone():
    user = User.objects.create_user(username="bad_phone_profile", password="StrongPass12345")
    form = ProfileUpdateForm(
        data={
            "first_name": "Анна",
            "last_name": "Иванова",
            "middle_name": "Павловна",
            "email": "bad_phone_profile@example.com",
            "phone": "+1 999 123-45-67",
        },
        instance=user,
    )

    assert not form.is_valid()
    assert "Введите телефон в формате +7 (999) 123-45-67." in form.errors["phone"]


@pytest.mark.django_db
def test_profile_update_form_allows_blank_phone():
    user = User.objects.create_user(username="blank_phone_profile", password="StrongPass12345")
    form = ProfileUpdateForm(
        data={
            "first_name": "Анна",
            "last_name": "Иванова",
            "middle_name": "Павловна",
            "email": "blank_phone_profile@example.com",
            "phone": "",
        },
        instance=user,
    )

    assert form.is_valid(), form.errors
