from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


from .permissions import CurrentUserOrAdminOrReadOnly
from .serializers import ProjectUserSerializer
from .models import User, Follow
from .pagination import ProjectPagination
from api.serializers import FollowSerializer


class ProjectUserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = ProjectUserSerializer
    permission_classes = (CurrentUserOrAdminOrReadOnly, IsAuthenticated)
    pagination_class = ProjectPagination

    def get_queryset(self):
        return User.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [AllowAny()]
        return (CurrentUserOrAdminOrReadOnly(), IsAuthenticated())
    
    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author = get_object_or_404(User, id=self.kwargs.get('id'))

        if request.method == 'POST':
            serializer = FollowSerializer(author, data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=user, following=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if request.method == 'DELETE':
            subscription = get_object_or_404(Follow, user=user, following=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )   
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(following_user__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
        
    
