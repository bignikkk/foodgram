from django.db.models import F
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, SerializerMethodField

from drf_extra_fields.fields import Base64ImageField

from recipes.models import Tag, Ingredient, Recipe, RecipeIngredient
from users.serializers import ProfileSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Ingredient


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = IntegerField(write_only=True)

    class Meta:
        fields = ('id', 'amount')
        model = RecipeIngredient


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        read_only_fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class RecipeShowSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = ProfileSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipeingredient__amount')
        )
        return ingredients

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if not user or user.is_anonymous:
            return False
        return user.favorites.filter(favorite_recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if not user or user.is_anonymous:
            return False
        return user.shopping_list_items.filter(recipe=obj).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    author = ProfileSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate_tags(self, data):
        if not data:
            raise ValidationError({'tags': 'Выберите один или несколько тегов!'})
        
        tags_list = []
        for tag in data:
            if tag in tags_list:
                raise ValidationError({'tags': 'Теги не могут повторяться!'})
            tags_list.append(tag)
        return data
    
    def validate_ingredients(self, data):
        if not data:
            raise ValidationError({'tags': 'Выберите один или несколько ингредиентов!'})
        
        ingredient_ids = []
        for item in data:
            ingredient_id = item.get('id')
            amount = item.get('amount')
            if amount <= 0:
                raise ValidationError({
                'amount': 'Количество ингредиентов должно быть больше 0!'
            })
            if ingredient_id in ingredient_ids:
                raise ValidationError({
                    'ingredients': 'Ингридиенты не могут повторяться!'
                })
            ingredient_ids.append(ingredient_id)
        return data


    @atomic
    def create_ingredients(self, ingredients, recipe):
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            )for ingredient in ingredients]
        )

    @atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe=recipe, ingredients=ingredients)
        return recipe

    @atomic
    def update(self, instance, validated_data):
        instance.tags.clear()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        instance.tags.set(validated_data.pop('tags'))
        ingredients = validated_data.pop('ingredients')
        self.create_ingredients(ingredients, instance)
        return super().update(instance, validated_data)

    @atomic
    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeShowSerializer(instance, context=context).data
