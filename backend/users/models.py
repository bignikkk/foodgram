from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db.models import UniqueConstraint


class ProjectUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        max_length=254, blank=False, null=False, unique=True)
    first_name = models.CharField(max_length=150, blank=False, null=False)
    last_name = models.CharField(max_length=150, blank=False, null=False)
    avatar = models.ImageField(
        upload_to='avatars/', null=True, default='default.png')

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользовaтель'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
         return self.email


User = get_user_model()


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower')
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following_user')

    class Meta:
        constraints = (
            UniqueConstraint(fields=('user', 'following'),
                             name='unique_followings'),
        )
        ordering = ('-id',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
