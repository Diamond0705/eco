import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
def test_home_redirects_anonymous_to_login(client):
    response = client.get(reverse("home"))

    assert response.status_code == 302
    assert response["Location"] == reverse("accounts:login")


@pytest.mark.django_db
def test_home_redirects_authenticated_to_dashboard(client):
    user = User.objects.create_user(username="manager8", password="StrongPass12345")
    client.force_login(user)

    response = client.get(reverse("home"))

    assert response.status_code == 302
    assert response["Location"] == reverse("dashboard:dashboard")


@pytest.mark.django_db
def test_dashboard_redirects_manager_to_manager_dashboard(client):
    user = User.objects.create_user(
        username="manager9",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )
    client.force_login(user)

    response = client.get(reverse("dashboard:dashboard"))

    assert response.status_code == 302
    assert response["Location"] == reverse("dashboard:manager_dashboard")


@pytest.mark.django_db
def test_dashboard_redirects_admin_to_admin_dashboard(client):
    user = User.objects.create_user(
        username="admin2",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )
    client.force_login(user)

    response = client.get(reverse("dashboard:dashboard"))

    assert response.status_code == 302
    assert response["Location"] == reverse("dashboard:admin_dashboard")


@pytest.mark.django_db
def test_dashboard_redirects_superuser_to_admin_dashboard(client):
    user = User.objects.create_superuser(
        username="superuser1",
        email="superuser@example.com",
        password="StrongPass12345",
    )
    client.force_login(user)

    response = client.get(reverse("dashboard:dashboard"))

    assert response.status_code == 302
    assert response["Location"] == reverse("dashboard:admin_dashboard")


@pytest.mark.django_db
def test_anonymous_protected_access_redirects_to_login(client):
    response = client.get(reverse("accounts:profile"))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_manager_dashboard_allows_manager(client):
    user = User.objects.create_user(
        username="manager10",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )
    client.force_login(user)

    response = client.get(reverse("dashboard:manager_dashboard"))

    content = response.content.decode()

    assert response.status_code == 200
    assert (
        "Сравнивайте рассчитанные варианты маршрутов по стоимости, выбросам и эко-рейтингу."
        in content
    )


@pytest.mark.django_db
def test_admin_dashboard_allows_admin_and_superuser(client):
    admin = User.objects.create_user(
        username="admin3",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )
    client.force_login(admin)
    assert client.get(reverse("dashboard:admin_dashboard")).status_code == 200

    superuser = User.objects.create_superuser(
        username="superuser2",
        email="superuser2@example.com",
        password="StrongPass12345",
    )
    client.force_login(superuser)
    assert client.get(reverse("dashboard:admin_dashboard")).status_code == 200


@pytest.mark.django_db
def test_wrong_role_gets_403(client):
    manager = User.objects.create_user(
        username="manager11",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )
    client.force_login(manager)
    assert client.get(reverse("dashboard:admin_dashboard")).status_code == 403

    admin = User.objects.create_user(
        username="admin4",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )
    client.force_login(admin)
    assert client.get(reverse("dashboard:manager_dashboard")).status_code == 403

    superuser = User.objects.create_superuser(
        username="superuser3",
        email="superuser3@example.com",
        password="StrongPass12345",
    )
    client.force_login(superuser)
    assert client.get(reverse("dashboard:manager_dashboard")).status_code == 403
