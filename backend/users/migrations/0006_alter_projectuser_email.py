# Generated by Django 4.2.13 on 2024-06-05 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_follow_following_alter_follow_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectuser',
            name='email',
            field=models.EmailField(max_length=256, unique=True, verbose_name='Электронная почта'),
        ),
    ]