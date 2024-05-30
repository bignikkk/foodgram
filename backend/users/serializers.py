from rest_framework import serializers

from drf_extra_fields.fields import Base64ImageField

from .models import User, Follow

from djoser.serializers import UserCreateSerializer, UserSerializer


class ProjectUserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user,
                following=obj
            ).exists()
        return False
