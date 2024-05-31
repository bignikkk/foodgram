import hashlib

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import models
from django.db.models import UniqueConstraint


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=150, unique=True,
                            blank=False, null=False, verbose_name='Название')
    slug = models.SlugField(max_length=150, unique=True,
                            blank=False, null=False, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=150, blank=False,
                            null=False, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=50,
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
        max_length=254,
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
        blank=False,
        null=False,
        verbose_name='Время приготовления'
    )
    short_link = models.CharField(
        max_length=8,
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
        hash_object = hashlib.md5(str(self.id).encode())
        return hash_object.hexdigest()[:3]

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
    amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=False,
        null=False,
        verbose_name='Кол-во'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = (
            UniqueConstraint(fields=('recipe', 'ingredient'),
                             name='unique_ingredients'),
        )


class ShortRecipeLink(models.Model):
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE)
    short_link = models.CharField(max_length=22, unique=True)

    def __str__(self):
        return f'{self.recipe.id} - {self.short_link}'

    def get_short_url(self):
        return reverse('recipe_short_link', args=[self.short_link])


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
