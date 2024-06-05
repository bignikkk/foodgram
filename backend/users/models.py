from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db.models import UniqueConstraint

from recipes.constants import (
    AUTHOR_LENGTH,
    DEFAULT_LENGTH,
)


class ProjectUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        max_length=AUTHOR_LENGTH,
        blank=False,
        null=False,
        unique=True,
        verbose_name='Электронная почта'
    )
    first_name = models.CharField(
        max_length=DEFAULT_LENGTH,
        blank=False,
        null=False,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=DEFAULT_LENGTH,
        blank=False,
        null=False,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        default='default.png'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользовaтель'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


User = get_user_model()


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following_user',
        verbose_name='Автор'
    )

    class Meta:
        constraints = (
            UniqueConstraint(fields=('user', 'following'),
                             name='unique_followings'),
        )
        ordering = ('-id',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
