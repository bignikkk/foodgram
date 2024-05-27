from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import ProjectUserViewSet

router = DefaultRouter()
router.register(r'users', ProjectUserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]