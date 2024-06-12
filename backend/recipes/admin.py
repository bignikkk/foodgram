from django.contrib import admin
from django.contrib.admin import display
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import (
    Favorite,
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingListItem
)


class RecipeIngredientInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        ingredients = [
            form.cleaned_data for form in self.forms if form.cleaned_data]
        if not ingredients:
            raise ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент.')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    formset = RecipeIngredientInlineFormSet
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'author',
                    'ingredients_list', 'added_in_favorites')
    readonly_fields = ('added_in_favorites',)
    list_filter = ('tags',)
    search_fields = ('name', 'author__username')
    inlines = [RecipeIngredientInline]

    @display(description='Кол-во в избранных')
    def added_in_favorites(self, obj):
        return obj.favorites.count()

    @display(description='Ингредиенты')
    def ingredients_list(self, obj):
        return ', '.join(
            [str(ri.ingredient) for ri in obj.recipeingredient.all()]
        )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(ShoppingListItem)
class ShoppingListItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(RecipeIngredient)
class RecipeIngredient(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
