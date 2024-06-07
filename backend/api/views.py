import hashlib

from django.utils.timezone import now
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.http import HttpResponse

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingListItem,
    RecipeIngredient
)
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeShowSerializer,
    RecipeCreateSerializer,
    RecipeShortSerializer
)
from .permission import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .filters import IngredientFilter, RecipeFilter
from users.pagination import ProjectPagination
from recipes.constants import SITE_URL


@method_decorator(require_http_methods(
    ('GET', 'HEAD', 'OPTIONS')),
    name='dispatch'
)
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


@method_decorator(require_http_methods(
    ('GET', 'HEAD', 'OPTIONS')),
    name='dispatch'
)
class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


def generate_short_link(recipe_id):
    hash_object = hashlib.md5(str(recipe_id).encode())
    short_hash = hash_object.hexdigest()[:3]
    return short_hash


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = ProjectPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeShowSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        user = request.user
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response({'errors': 'Рецепт не существует!'},
                            status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            model = Favorite
            if model.objects.filter(user=user,
                                    favorite_recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже был добавлен!'},
                                status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=user, favorite_recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            model = Favorite
            obj = model.objects.filter(user=user, favorite_recipe=recipe)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'errors': 'Рецепт уже был удален!'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        user = request.user
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response({'errors': 'Рецепт не существует!'},
                            status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            model = ShoppingListItem
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже был добавлен в список покупок!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            model = ShoppingListItem
            obj = model.objects.filter(user=user, recipe=recipe)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'errors': 'Рецепт уже был удален!'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=('get',),
            permission_classes=(IsAuthenticated,),
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_list_items.exists():
            return Response({'errors': 'Список покупок пуст!'},
                            status=status.HTTP_400_BAD_REQUEST)

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_list_items__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        today = now().date()
        shopping_list = (
            f'Список покупок для: {user.get_full_name()}\n\n'
            f'Дата: {today:%Y-%m-%d}\n\n'
        )
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        shopping_list += f'\n\nFoodgram ({today:%Y})'

        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            f'attachment; filename={user.username}_shopping_list.txt'
        )
        return response

    @action(detail=True,
            methods=('get',),
            permission_classes=(AllowAny,),
            url_path='get-link')
    def get_link(self, request, pk=None):
        try:
            recipe = self.get_object()
            if not recipe.short_link:
                recipe.short_link = generate_short_link(recipe.id)
                recipe.save()
            short_link = f'{SITE_URL}/s/{recipe.short_link}'
            return Response({'short-link': short_link},
                            status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response({'error': 'Рецепт не существует!'},
                            status=status.HTTP_404_NOT_FOUND)

    @action(detail=False,
            methods=('get',),
            permission_classes=(AllowAny,),
            url_path='s/(?P<short_hash>[^/.]+)')
    def redirect_to_recipe(self, request, short_hash=None):
        try:
            recipe = get_object_or_404(Recipe, short_link=short_hash)
            return redirect(f'{SITE_URL}/recipes/{recipe.pk}/')
        except Recipe.DoesNotExist:
            return HttpResponse(status=404)
