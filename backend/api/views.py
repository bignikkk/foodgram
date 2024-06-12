from http import HTTPStatus

from django.db.models import Count
from djoser.views import UserViewSet as DjoserUserViewSet
from django.utils.timezone import now
from django.shortcuts import redirect, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated, AllowAny
from rest_framework.response import Response


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
    FavoriteSerializer,
    ShoppingListItemSerializer,
    FollowShowSerializer,
    FollowCreateSerializer,
    AvatarSerializer,
    UserSerializer
)
from .permissions import IsAuthorOrReadOnly, CurrentUserOrAdminOrReadOnly
from .filters import IngredientFilter, RecipeFilter
from .pagination import ProjectPagination
from recipes.constants import SITE_URL
from users.models import User, Follow


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get']


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    http_method_names = ['get']


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (CurrentUserOrAdminOrReadOnly,)
    pagination_class = ProjectPagination

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')

        if not User.objects.filter(pk=author_id).exists():
            return Response({'detail': 'Пользователь не существует!'},
                            status=status.HTTP_404_NOT_FOUND)

        data = {'user': user.id, 'following': author_id}
        serializer = FollowCreateSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')

        if not User.objects.filter(pk=author_id).exists():
            return Response({'detail': 'Пользователь не существует!'},
                            status=status.HTTP_404_NOT_FOUND)

        subscription = Follow.objects.filter(user=user, following_id=author_id)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя!'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(followings__user=user).annotate(
            recipes_count=Count('recipes'))
        pages = self.paginate_queryset(queryset)
        serializer = FollowShowSerializer(
            pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=('put',),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        serializer = AvatarSerializer(
            instance=user,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        user.avatar = serializer.validated_data['avatar']
        user.save()
        avatar_url = request.build_absolute_uri(user.avatar.url)
        return Response(
            {'avatar': avatar_url},
            status=status.HTTP_200_OK
        )

    @avatar.mapping.delete
    def remove_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Нет картинки для удаления!'},
                        status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
        'author').prefetch_related('tags', 'ingredients')
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = ProjectPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeShowSerializer
        return RecipeCreateSerializer

    @staticmethod
    def add_to_list(serializer_class, pk, request):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': user.id, 'recipe': recipe.id}
        serializer = serializer_class(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self.add_to_list(FavoriteSerializer, pk, request)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):

        if not Recipe.objects.filter(pk=pk).exists():
            return Response({'detail': 'Рецепт не существует!'},
                            status=status.HTTP_404_NOT_FOUND)

        obj = Favorite.objects.filter(user=request.user, recipe_id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепта нет в избранном!'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self.add_to_list(ShoppingListItemSerializer, pk, request)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):

        if not Recipe.objects.filter(pk=pk).exists():
            return Response({'detail': 'Рецепт не существует!'},
                            status=status.HTTP_404_NOT_FOUND)

        obj = ShoppingListItem.objects.filter(user=request.user, recipe_id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепта нет в списке!'},
                        status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def create_shopping_list(user, ingredients):
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
        return shopping_list

    @action(detail=False, methods=('get',),
            permission_classes=(IsAuthenticated,),
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shoppinglistitems.exists():
            return Response({'errors': 'Список покупок пуст!'},
                            status=status.HTTP_400_BAD_REQUEST)

        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppinglistitems__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount')).order_by('ingredient__name')

        shopping_list = self.create_shopping_list(user, ingredients)

        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            f'attachment; filename={user.username}_shopping_list.txt'
        )
        return response

    @action(detail=False,
            methods=['get'],
            permission_classes=(AllowAny,),
            url_path='get-link/(?P<short_hash>[^/.]+)')
    def handle_short_link(self, request, short_hash=None, pk=None):
        if pk:
            recipe = self.get_object()
            short_link = f'{SITE_URL}/s/{recipe.short_link}'
            return Response({'short-link': short_link},
                            status=status.HTTP_200_OK)
        else:
            try:
                recipe = Recipe.objects.get(short_link=short_hash)
                return redirect(f'{SITE_URL}/recipes/{recipe.pk}/')
            except Recipe.DoesNotExist:
                return HttpResponse(status=HTTPStatus.NOT_FOUND)
