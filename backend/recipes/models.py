from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=150, unique=True,
                            blank=False, null=False)
    slug = models.SlugField(max_length=150, unique=True,
                            blank=False, null=False)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=150, blank=False, null=False)
    measurement_unit = models.CharField(max_length=50, blank=False, null=False)

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
        User, on_delete=models.CASCADE, related_name='recipes', blank=False, null=False)
    name = models.CharField(max_length=254, blank=False, null=False)
    image = models.ImageField(upload_to='recipes/',
                              blank=False, null=False, default='default.png')
    text = models.TextField(blank=False, null=False)
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', blank=False)
    tags = models.ManyToManyField(Tag, blank=False)
    cooking_time = models.PositiveIntegerField(blank=False, null=False)

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, blank=False, null=False, related_name='recipeingredient')
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, blank=False, null=False)
    amount = models.DecimalField(
        max_digits=6, decimal_places=2, blank=False, null=False)

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = (
            UniqueConstraint(fields=('recipe', 'ingredient'),
                             name='unique_ingredients'),
        )


class ShoppingListItem(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_list_items')
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, related_name='shopping_list_items')
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
        User, on_delete=models.CASCADE, related_name='favorites')
    favorite_recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            UniqueConstraint(fields=('user', 'favorite_recipe'),
                             name='unique_favorite_recipes'),
        )
    
    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в избранное'
