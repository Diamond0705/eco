from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url


def is_manager(user):
    return (
        user.is_authenticated
        and getattr(user, "role", None) == "manager"
        and not user.is_superuser
    )


def is_admin(user):
    return user.is_authenticated and (getattr(user, "role", None) == "admin" or user.is_superuser)


def role_required(check):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), resolve_url(settings.LOGIN_URL))
            if not check(request.user):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


manager_required = role_required(is_manager)
admin_required = role_required(is_admin)
