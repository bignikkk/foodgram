from django.db import models
from django.db.models import UniqueConstraint
from django.core.validators import MinValueValidator, MaxValueValidator

from .constants import (
    EMAIL_LENGTH,
    DEFAULT_LENGTH,
    UNIT_LENGTH,
    LINK_LENGTH,
    AMOUNT_MIN,
    AMOUNT_MAX
)
from .services import get_unique_short_link
from users.models import User
from core.models import BaseRecipeRelationModel


class Tag(models.Model):
    name = models.CharField(
        max_length=DEFAULT_LENGTH,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=DEFAULT_LENGTH,
        unique=True,
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
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=UNIT_LENGTH,
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
        max_length=EMAIL_LENGTH,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/',
        default='default.png',
        verbose_name='Картинка'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=(
            MinValueValidator(AMOUNT_MIN,
                              message=f'Минимум {AMOUNT_MIN}!'),
            MaxValueValidator(AMOUNT_MAX,
                              message=f'Максимум {AMOUNT_MAX}!')
        )
    )
    short_link = models.CharField(
        max_length=LINK_LENGTH,
        unique=True,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = get_unique_short_link(Recipe)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipeingredient',
        verbose_name='Рецепты'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиенты'
    )
    amount = models.PositiveSmallIntegerField(
        'Кол-во',
        validators=(
            MinValueValidator(AMOUNT_MIN,
                              message=f'Минимум {AMOUNT_MIN}!'),
            MaxValueValidator(AMOUNT_MAX,
                              message=f'Максимум {AMOUNT_MAX}!')
        )
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = (
            UniqueConstraint(fields=('recipe', 'ingredient'),
                             name='unique_ingredients'),
        )

    def __str__(self):
        return f'{self.amount} {self.ingredient} в "{self.recipe}"'


class ShoppingListItem(BaseRecipeRelationModel):

    class Meta(BaseRecipeRelationModel.Meta):
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'


class Favorite(BaseRecipeRelationModel):

    class Meta(BaseRecipeRelationModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
