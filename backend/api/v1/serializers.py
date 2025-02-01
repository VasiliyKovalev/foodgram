from django.db import transaction
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite, Ingredient, IngredientInRecipe,
    Recipe, RecipeInShoppingCart, Tag
)
from users.models import Subscription, User


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления аватара."""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user,
                following=obj
            ).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)
        read_only_fields = ('name', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)
        read_only_fields = ('name', 'measurement_unit',)


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для указания количества ингредиента в рецепте."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='name'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount',)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра рецептов."""
    tags = TagSerializer(many=True,)
    author = UserSerializer()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = (
            'author',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def check_recipe_in_model(self, obj, model):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and model.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        )

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredientinrecipe__amount',)
        )

    def get_is_favorited(self, obj):
        return self.check_recipe_in_model(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.check_recipe_in_model(obj, RecipeInShoppingCart)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и изменения рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    ingredients = IngredientAmountSerializer(many=True,)
    image = Base64ImageField()
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author',
        )

    def validate(self, value):
        tags = value.get('tags')
        ingredients = value.get('ingredients')

        field_errors = {}
        if not tags:
            field_errors['tags'] = 'Добавьте хотя бы один тег!'
        elif len(tags) != len(set(tags)):
            field_errors['tags'] = 'Проверьте теги на дубликаты!'

        if not ingredients:
            field_errors['ingredients'] = 'Добавьте хотя бы один ингредиент!'
        else:
            ingredients_list = [
                ingredient.get('name') for ingredient in ingredients]
            if len(ingredients_list) != len(set(ingredients_list)):
                field_errors['ingredients'] = (
                    'Проверьте ингредиенты на дубликаты!')

        if field_errors:
            raise serializers.ValidationError(field_errors)
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо добавить изображение!')
        return value

    @staticmethod
    def add_tags_and_ingredients_to_recipe(recipe, tags, ingredients):
        recipe.tags.set(tags)
        all_ingredients = []
        for ingredient in ingredients:
            ingredient_in_recipe = IngredientInRecipe(
                name=ingredient.get('name'),
                recipe=recipe,
                amount=ingredient.get('amount')
            )
            all_ingredients.append(ingredient_in_recipe)
        IngredientInRecipe.objects.bulk_create(all_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        self.is_valid(raise_exception=True)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.add_tags_and_ingredients_to_recipe(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        self.is_valid(raise_exception=True)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.ingredients.clear()
        self.add_tags_and_ingredients_to_recipe(instance, tags, ingredients)
        super().update(instance, validated_data)
        return instance

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return RecipeReadSerializer(instance, context=context).data


class RecipeShortInformation(serializers.ModelSerializer):
    """Сериализатор краткой информации о рецепте."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = (
            'name',
            'image',
            'cooking_time',
        )


class RecipeInShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecipeInShoppingCart
        fields = ('user', 'recipe',)
        validators = (
            UniqueTogetherValidator(
                queryset=RecipeInShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже добавлен в список покупок!'
            ),
        )

    def to_representation(self, instance):
        return RecipeShortInformation(
            instance.recipe, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)
        validators = (
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже добавлен в избранное!'
            ),
        )

    def to_representation(self, instance):
        return RecipeShortInformation(
            instance.recipe, context=self.context).data


class SubscriptionSerializer(UserSerializer):
    "Сериализатор для модели Subscription."
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count',)
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar'
        )

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj)
        recipes_limit = self.context.get(
            'request').query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass
        return RecipeShortInformation(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class FollowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'following',)
        validators = (
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'following'),
                message='Такая подписка уже существует!'
            ),
        )

    def validate_following(self, value):
        if self.context.get('request').user == value:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!')
        return value

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance.following, context=self.context).data
