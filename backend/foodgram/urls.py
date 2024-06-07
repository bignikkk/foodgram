from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from api.views import RecipeViewSet

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('api.urls')),
    path('s/<short_hash>/',
         RecipeViewSet.as_view({'get': 'redirect_to_recipe'}),
         name='redirect-to-recipe'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
