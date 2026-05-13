from django.urls import path

from .views import (
    EcoLogistLoginView,
    EcoLogistLogoutView,
    ProfileEditView,
    ProfileView,
    RegisterView,
)

app_name = "accounts"

urlpatterns = [
    path("accounts/register/", RegisterView.as_view(), name="register"),
    path("accounts/login/", EcoLogistLoginView.as_view(), name="login"),
    path("accounts/logout/", EcoLogistLogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),
]
