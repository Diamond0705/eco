from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, UpdateView

from .forms import (
    ManagerRegistrationForm,
    ProfileUpdateForm,
    UsernameOrEmailAuthenticationForm,
)


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

    def form_valid(self, form):
        messages.success(self.request, "Профиль обновлен.")
        return super().form_valid(form)
