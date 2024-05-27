from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend


from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingListItem
from users.pagination import ProjectPagination
from .serializers import TagSerializer, IngredientSerializer, RecipeShowSerializer, RecipeCreateSerializer, RecipeShortSerializer
from .permission import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .filters import IngredientFilter


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = ProjectPagination
    filter_backends = (DjangoFilterBackend,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeShowSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        user = request.user
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response({'errors': 'Рецепт не существует!'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            model = Favorite
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже был добавлен!'}, status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            model = Favorite
            obj = model.objects.filter(user=user, recipe=recipe)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'errors': 'Рецепт уже был удален!'}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_list(self, request, pk):
        user = request.user
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response({'errors': 'Рецепт не существует!'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            model = ShoppingListItem
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже был добавлен в список покупок!'}, status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            model = ShoppingListItem
            obj = model.objects.filter(user=user, recipe=recipe)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'errors': 'Рецепт уже был удален!'}, status=status.HTTP_400_BAD_REQUEST)