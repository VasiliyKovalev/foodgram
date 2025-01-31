import random

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from users.models import User


MAX_LENGTH_TAG_NAME = 32
MAX_LENGTH_TAG_SLUG = 32
MAX_LENGTH_INGREDIENT_NAME = 128
MAX_LENGTH_MEASUREMENT_UNIT = 64
MAX_LENGTH_RECIPE_NAME = 256
MAX_LENGTH_SHORT_LINK = 10
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32000
MIN_AMOUNT_INGREDIENTS = 1
MAX_AMOUNT_INGREDIENTS = 32000
SYMBOLS_FOR_SHORT_LINK = (
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True,
        verbose_name='Название тега',
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_TAG_SLUG,
        unique=True,
        verbose_name='Слаг тега',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'Тег "{self.name}"'


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        max_length=MAX_LENGTH_INGREDIENT_NAME,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_MEASUREMENT_UNIT,
        verbose_name='Единица измерения',
    )

    class Meta:
        ordering = ('name', 'measurement_unit',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'), name='unique_ingredient'
            ),
        )

    def __str__(self):
        return f'Ингредиент "{self.name}"'


class Recipe(models.Model):
    """Модель рецепта."""
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Ингредиенты',
    )
    name = models.CharField(
        max_length=MAX_LENGTH_RECIPE_NAME,
        verbose_name='Название рецепта',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение рецепта',
    )
    text = models.TextField(verbose_name='Описание блюда',)
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(
            MinValueValidator(
                MIN_COOKING_TIME,
                f'Значение не может быть меньше {MIN_COOKING_TIME}!'
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                f'Значение не может быть больше {MAX_COOKING_TIME}!'
            ),
        )
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )
    short_link = models.CharField(
        max_length=MAX_LENGTH_SHORT_LINK,
        unique=True,
        blank=True,
        null=True,
    )

    class Meta:
        default_related_name = 'recipes'
        ordering = ('-pub_date', 'name',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def generate_short_link(self):
        while True:
            short_link = ''.join(
                random.choices(SYMBOLS_FOR_SHORT_LINK, k=MAX_LENGTH_SHORT_LINK)
            )
            if not Recipe.objects.filter(short_link=short_link).exists():
                break
        return short_link

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'Рецепт "{self.name}" от пользователя "{self.author.username}"'


class IngredientInRecipe(models.Model):
    name = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        validators=(
            MinValueValidator(
                MIN_AMOUNT_INGREDIENTS, (
                    f'Значение не может быть меньше {MIN_AMOUNT_INGREDIENTS}!'
                ),
            ),
            MaxValueValidator(
                MAX_AMOUNT_INGREDIENTS, (
                    f'Значение не может быть больше {MAX_AMOUNT_INGREDIENTS}!'
                ),
            ),
        ),
    )

    class Meta:
        ordering = ('name', 'recipe',)
        verbose_name = 'ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f'"{self.name} - {self.name.measurement_unit}"'


class FavoriteAndShoppingCartModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True


class Favorite(FavoriteAndShoppingCartModel):

    class Meta:
        default_related_name = 'favorites'
        ordering = ('recipe',)
        verbose_name = 'рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'

    def __str__(self):
        return f'"{self.recipe.name}" в избранном "{self.user.username}"'


class RecipeInShoppingCart(FavoriteAndShoppingCartModel):

    class Meta:
        default_related_name = 'shopping_cart'
        ordering = ('recipe',)
        verbose_name = 'рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'

    def __str__(self):
        return (
            f'Рецепт "{self.recipe.name}" в списке '
            f'покупок пользователя: "{self.user.username}"'
        )
