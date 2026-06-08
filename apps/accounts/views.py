from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import FileResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import FormView, TemplateView, UpdateView

from .forms import (
    ManagerRegistrationForm,
    ProfileAvatarUploadForm,
    ProfileUpdateForm,
    UsernameOrEmailAuthenticationForm,
)


def _avatar_content_type(name):
    name = name.lower()
    if name.endswith(".png"):
        return "image/png"
    if name.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


class RegisterView(FormView):
    form_class = ManagerRegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Регистрация завершена. Теперь войдите в систему.")
        return super().form_valid(form)


class EcoLogistLoginView(LoginView):
    authentication_form = UsernameOrEmailAuthenticationForm
    template_name = "registration/login.html"


class EcoLogistLogoutView(LogoutView):
    pass


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"


class ProfileEditView(LoginRequiredMixin, UpdateView):
    form_class = ProfileUpdateForm
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("avatar_form", ProfileAvatarUploadForm())
        return context

    def form_valid(self, form):
        messages.success(self.request, "Профиль обновлен.")
        return super().form_valid(form)


@login_required
@require_GET
def profile_avatar(request):
    if not request.user.avatar:
        raise Http404

    try:
        avatar_file = request.user.avatar.open("rb")
    except OSError as exc:
        raise Http404 from exc

    return FileResponse(
        avatar_file,
        content_type=_avatar_content_type(request.user.avatar.name),
    )


@login_required
@require_POST
def profile_avatar_upload(request):
    form = ProfileAvatarUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        first_error = next(iter(form.errors.values()))[0]
        messages.error(request, first_error)
        return redirect("accounts:profile_edit")

    user = request.user
    old_avatar_name = user.avatar.name
    user.avatar = form.cleaned_data["avatar"]
    try:
        user.save(update_fields=["avatar"])
    except Exception:
        messages.error(
            request,
            "Не удалось сохранить фото профиля. Проверьте доступность хранилища файлов.",
        )
        return redirect("accounts:profile_edit")

    if old_avatar_name and old_avatar_name != user.avatar.name:
        user.avatar.storage.delete(old_avatar_name)

    messages.success(request, "Фото профиля обновлено.")
    return redirect("accounts:profile_edit")


@login_required
@require_POST
def profile_avatar_delete(request):
    user = request.user
    if user.avatar:
        user.avatar.delete(save=False)
        user.avatar = ""
        user.save(update_fields=["avatar"])
        messages.success(request, "Фото профиля удалено.")
    else:
        messages.info(request, "Фото профиля еще не загружено.")
    return redirect("accounts:profile_edit")
