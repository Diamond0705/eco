from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model


def test_custom_user_model_is_configured():
    assert settings.AUTH_USER_MODEL == "accounts.User"

    user_model = get_user_model()

    assert user_model._meta.label == "accounts.User"
    assert hasattr(user_model, "middle_name")
    assert hasattr(user_model, "phone")
    assert hasattr(user_model, "role")


def test_expected_apps_are_registered():
    expected_apps = {
        "accounts",
        "fleet",
        "locations",
        "orders",
        "routing",
        "trips",
        "reports",
        "dashboard",
        "core",
    }

    registered_apps = {app_config.label for app_config in apps.get_app_configs()}

    assert expected_apps.issubset(registered_apps)
