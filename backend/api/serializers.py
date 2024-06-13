from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from django.db.models import F
from django.db.transaction import atomic

from users.models import User, Follow
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingListItem,
    RecipeIngredient
)
from recipes.constants import AMOUNT_MIN
from .fields import Base64ImageField


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Ingredient


class UserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return (
            request.user.is_authenticated
            and request.user.followings.filter(following=obj).exists()
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=AMOUNT_MIN,
    )

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
    author = UserSerializer(read_only=True)
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
        user = self.context['request'].user
        return (
            user.is_authenticated
            and user.favorites.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and user.shoppinglistitems.filter(recipe=obj).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField(
        allow_null=False,
        allow_empty_file=False
    )
    cooking_time = serializers.IntegerField(
        min_value=AMOUNT_MIN,
    )

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
            raise serializers.ValidationError(
                {'tags': 'Выберите один или несколько тегов!'}
            )
        if len(data) != len(set(data)):
            raise serializers.ValidationError(
                {'tags': 'Теги не могут повторяться!'}
            )
        return data

    def validate_ingredients(self, data):
        if not data:
            raise serializers.ValidationError(
                {'ingredients': 'Выберите один или несколько ингредиентов!'})

        ingredient_ids = [item['id'] for item in data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не могут повторяться!'}
            )
        return data

    @staticmethod
    def create_ingredients(ingredients, recipe):
        recipe_ingredients = [
            RecipeIngredient(
                ingredient_id=ingredient['id'].id,
                recipe=recipe,
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe=recipe, ingredients=ingredients)
        return recipe

    @atomic
    def update(self, instance, validated_data):
        instance.tags.set(self.validate_tags(validated_data.pop('tags', [])))

        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_ingredients(
            self.validate_ingredients(validated_data.pop('ingredients', [])),
            instance
        )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeShowSerializer(instance, context=self.context).data


class FollowShowSerializer(UserSerializer):
    recipes = SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=1)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
            'recipes',
            'recipes_count'
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_recipes(self, obj):
        request = self.context['request']
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                pass
        return RecipeShortSerializer(
            recipes, many=True, context=self.context
        ).data


class FollowCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = ('user', 'following')

    def validate(self, data):
        user = data['user']
        following = data['following']

        if user.followings.filter(following=following).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
            )
        if user == following:
            raise serializers.ValidationError(
                'Вы не можете подписаться на самого себя!'
            )
        return data

    def to_representation(self, instance):
        return FollowShowSerializer(
            instance.following, context=self.context
        ).data


class BaseRecipeRelationSerializer(serializers.ModelSerializer):

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт уже добавлен в {self.Meta.model._meta.verbose_name}!')
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe, context=self.context
        ).data


class FavoriteSerializer(BaseRecipeRelationSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)


class ShoppingListItemSerializer(BaseRecipeRelationSerializer):

    class Meta:
        model = ShoppingListItem
        fields = ('user', 'recipe',)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)
