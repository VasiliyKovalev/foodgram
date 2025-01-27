from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from users.models import User


MAX_LENGTH_TAG_NAME = 32
MAX_LENGTH_INGREDIENT_NAME = 128
MAX_LENGTH_MEASUREMENT_UNIT = 64
MAX_LENGTH_RECIPE_NAME = 256
MIN_COOKING_TIME = 1
MIN_AMOUNT_INGREDIENTS = 1


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True,
        verbose_name='Название тега',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Слаг тега',
        validators=(
            RegexValidator(
                regex='^[-a-zA-Z0-9_]+$',
                message='Значение должно состоять только из латинских букв, '
                        'цифр, знаков подчеркивания или дефиса!',
            ),
        ),
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
        related_name='ingredients'
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
        )
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        default_related_name = 'recipes'
        ordering = ('-pub_date', 'name',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'Рецепт "{self.name}" от пользователя "{self.author.name}"'


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
        ),
    )

    class Meta:
        ordering = ('name', 'recipe',)
        verbose_name = 'ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f'"{self.name} - {self.name.measurement_unit}"'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_users',
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'

    def __str__(self):
        return f'Избранное пользователя "{self.user.username}"'


class RecipeInShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes_in_shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='users_shopping_cart'
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'

    def __str__(self):
        return (
            f'Рецепт "{self.recipe.name}" в списке '
            f'покупок пользователя: "{self.user.username}"'
        )


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscriptions')
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followings')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='user_not_following'
            )
        ]

    def __str__(self):
        return f'Подписки пользователя "{self.user.username}"'
