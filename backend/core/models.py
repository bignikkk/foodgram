from django.db import models
from django.db.models import UniqueConstraint

from users.models import User


class BaseRecipeRelationModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            UniqueConstraint(fields=('user', 'recipe'),
                             name='unique_%(class)s_user_recipe')
        ]

    def __str__(self):
        return (f'{self.user} добавил "{self.recipe}" '
                f'в {self._meta.verbose_name}')
