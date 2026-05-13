from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGER = "manager", "Менеджер"
        ADMIN = "admin", "Администратор"

    middle_name = models.CharField("Отчество", max_length=150, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    role = models.CharField(
        "Роль",
        max_length=20,
        choices=Role.choices,
        default=Role.MANAGER,
    )

    def __str__(self) -> str:
        full_name = self.get_full_name()
        return full_name or self.username
