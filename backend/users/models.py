from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db.models import UniqueConstraint

from recipes.constants import (
    EMAIL_LENGTH,
    DEFAULT_LENGTH,
)


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    email = models.EmailField(
        max_length=EMAIL_LENGTH,
        unique=True,
        verbose_name='Электронная почта'
    )
    username = models.CharField(
        max_length=DEFAULT_LENGTH,
        unique=True,
        verbose_name='Никнейм пользователя',
        validators=(
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Доступные символы @/./+/-/_',
            ),
        )
    )
    first_name = models.CharField(
        max_length=DEFAULT_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=DEFAULT_LENGTH,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        default='default.png'
    )

    class Meta:
        ordering = ('first_name', 'last_name')
        verbose_name = 'Пользовaтель'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followings',
        verbose_name='Автор'
    )

    class Meta:
        constraints = (
            UniqueConstraint(fields=('user', 'following'),
                             name='unique_followings'),
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def save(self, *args, **kwargs):
        if self.user == self.following:
            raise ValidationError('Нельзя подписаться на самого себя.')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} подписан на {self.following}'
