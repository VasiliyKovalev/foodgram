# Generated by Django 4.2.16 on 2024-11-13 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0007_alter_ingredientinrecipe_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='image',
            field=models.ImageField(default=1, upload_to='recipes/images/', verbose_name='Изображение рецепта'),
            preserve_default=False,
        ),
    ]
