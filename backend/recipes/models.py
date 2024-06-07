import hashlib
import random

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint
from django.core.validators import MinValueValidator

from .constants import (
    AUTHOR_LENGTH,
    DEFAULT_LENGTH,
    UNIT_LENGTH,
    LINK_LENGTH
)


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=DEFAULT_LENGTH,
        unique=True,
        blank=False,
        null=False,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=DEFAULT_LENGTH,
        unique=True,
        blank=False,
        null=False,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=DEFAULT_LENGTH,
        blank=False,
        null=False,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=UNIT_LENGTH,
        blank=False,
        null=False,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            UniqueConstraint(fields=('name', 'measurement_unit'),
                             name='unique_measurement_units'),
        )

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        null=True,
        verbose_name='Aвтор'
    )
    name = models.CharField(
        max_length=AUTHOR_LENGTH,
        blank=False,
        null=False,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/',
        blank=False,
        null=False,
        default='default.png',
        verbose_name='Картинка'
    )
    text = models.TextField(
        blank=False,
        null=False,
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        blank=False,
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=False,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(1, message='Минимум 1 минута!')]
    )
    short_link = models.CharField(
        max_length=LINK_LENGTH,
        unique=True,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def generate_short_link(self):
        random_number = random.randint(0, 10000)
        hash_object = hashlib.md5(str(random_number).encode())
        return hash_object.hexdigest()[:3]

    def validate_unique_short_link(self):
        short_link = self.generate_short_link()
        while Recipe.objects.filter(short_link=short_link).exists():
            short_link = self.generate_short_link()
        return short_link

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=False, null=False,
        related_name='recipeingredient',
        verbose_name='Рецепты'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        verbose_name='Ингредиенты'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1, message='Минимум 1!')],
        verbose_name='Кол-во'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = (
            UniqueConstraint(fields=('recipe', 'ingredient'),
                             name='unique_ingredients'),
        )


class ShoppingListItem(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_list_items',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_list_items',
        verbose_name='Рецепт'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = (
            UniqueConstraint(fields=('user', 'recipe'),
                             name='unique_recipes'),
        )

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в корзину покупок'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    favorite_recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Избранный рецепт'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            UniqueConstraint(fields=('user', 'favorite_recipe'),
                             name='unique_favorite_recipes'),
        )

    def __str__(self):
        return f'{self.user} добавил "{self.favorite_recipe}" в избранное'
