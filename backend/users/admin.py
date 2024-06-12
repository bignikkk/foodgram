from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count

from .models import Follow, User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        'username',
        'id',
        'email',
        'first_name',
        'last_name',
        'recipes_count',
        'followers_count',
    )
    list_filter = ('email', 'first_name')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            _recipes_count=Count('recipes', distinct=True),
            _followers_count=Count('followers', distinct=True)
        )
        return qs

    def recipes_count(self, obj):
        return obj._recipes_count
    recipes_count.short_description = 'Количество рецептов'

    def followers_count(self, obj):
        return obj._followers_count
    followers_count.short_description = 'Количество подписчиков'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
