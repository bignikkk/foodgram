from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated

from .permissions import CurrentUserOrAdminOrReadOnly
from .serializers import ProfileSerializer
from .models import ProjectUser
from .pagination import ProjectPagination


class ProjectUserViewSet(DjoserUserViewSet):
    queryset = ProjectUser.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (CurrentUserOrAdminOrReadOnly, IsAuthenticated)
    pagination_class = ProjectPagination

    def get_queryset(self):
        return ProjectUser.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve'] or self.action == 'create':
            return [AllowAny()]
        return (CurrentUserOrAdminOrReadOnly(), IsAuthenticated())
