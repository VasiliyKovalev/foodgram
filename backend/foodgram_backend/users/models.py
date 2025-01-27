from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


MAX_LENGTH_USERNAME = 150
MAX_LENGTH_FIRST_NAME = 150
MAX_LENGTH_LAST_NAME = 150
MAX_LENGTH_USER_ROLE = 20
MAX_LENGTH_EMAIL = 254


class User(AbstractUser):
    """Пользовательская модель User."""
    class UserRole(models.TextChoices):
        USER = 'user'
        ADMIN = 'admin'
    email = models.EmailField(
        unique=True,
        verbose_name='Электронная почта пользователя',
    )
    username = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        verbose_name='Никнейм пользователя',
        validators=(
            UnicodeUsernameValidator(),
        )
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_NAME,
        verbose_name='Имя пользователя',
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_LAST_NAME,
        verbose_name='Фамилия пользователя',
    )
    avatar = models.ImageField(
        upload_to='users/',
        verbose_name='Аватар пользователя',
        blank=True,
        null=True,
    )
    role = models.CharField(
        max_length=MAX_LENGTH_USER_ROLE,
        choices=UserRole.choices,
        default=UserRole.USER,
        verbose_name='Пользовательская роль',
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username',)

    class Meta:
        ordering = ('username',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'Пользователь "{self.username}"'

    def is_admin(self):
        return self.is_superuser or (self.role == self.UserRole.ADMIN)
