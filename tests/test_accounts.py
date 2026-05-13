import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


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
    assert user.phone == "+79991112233"
    assert user.role == User.Role.MANAGER
