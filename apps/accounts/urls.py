from django.urls import path

from .views import (
    EcoLogistLoginView,
    EcoLogistLogoutView,
    ProfileEditView,
    ProfileView,
    RegisterView,
    profile_avatar,
    profile_avatar_delete,
    profile_avatar_upload,
)

app_name = "accounts"

urlpatterns = [
    path("accounts/register/", RegisterView.as_view(), name="register"),
    path("accounts/login/", EcoLogistLoginView.as_view(), name="login"),
    path("accounts/logout/", EcoLogistLogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),
    path("profile/avatar/", profile_avatar, name="profile_avatar"),
    path("profile/avatar/upload/", profile_avatar_upload, name="profile_avatar_upload"),
    path("profile/avatar/delete/", profile_avatar_delete, name="profile_avatar_delete"),
]
