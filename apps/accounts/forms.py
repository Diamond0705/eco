from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


class ManagerRegistrationForm(UserCreationForm):
    email = forms.EmailField(label="Email", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "middle_name",
            "phone",
        )
        labels = {
            "username": "Имя пользователя",
            "first_name": "Имя",
            "last_name": "Фамилия",
            "middle_name": "Отчество",
            "phone": "Телефон",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Пароль"
        self.fields["password2"].label = "Подтверждение пароля"
        self.fields["password1"].help_text = (
            "Минимум 8 символов. Не используйте слишком простой пароль."
        )
        self.fields["password2"].help_text = "Введите тот же пароль еще раз."

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.MANAGER
        if commit:
            user.save()
        return user


class UsernameOrEmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Имя пользователя или email")

    error_messages = {
        **AuthenticationForm.error_messages,
        "duplicate_email": (
            "Найдено несколько пользователей с таким email. Войдите по имени пользователя."
        ),
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["password"].label = "Пароль"

    def clean(self):
        username_or_email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username_or_email is not None and password:
            username = username_or_email
            if "@" in username_or_email:
                users = list(User.objects.filter(email__iexact=username_or_email))
                if len(users) == 1:
                    username = users[0].get_username()
                elif len(users) > 1:
                    raise forms.ValidationError(
                        self.error_messages["duplicate_email"],
                        code="duplicate_email",
                    )

            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "middle_name", "email", "phone")
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "middle_name": "Отчество",
            "email": "Email",
            "phone": "Телефон",
        }
