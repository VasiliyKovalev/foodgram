from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

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


class UserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password',
        )
        read_only_fields = ('id',)


class UserSerializer(UserSerializer):
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
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Subscription.objects.filter(
                user=user,
                following=obj
            ).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)
        read_only_fields = ('id', 'name', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)
        read_only_fields = ('id', 'name', 'measurement_unit',)


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

    def check_recipe_in_model(self, obj, model):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return model.objects.filter(
                user=user,
                recipe=obj
            ).exists()
        return False

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

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, value):
        if not value.get('tags'):
            raise serializers.ValidationError('Добавьте хотя бы один тег!')
        if not value.get('ingredients'):
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент!')
        return value

    def validate_duplicates(self, model, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                f'Проверьте {model._meta.verbose_name_plural} на дубликаты!')

    def validate_tags(self, value):
        self.validate_duplicates(Tag, value)
        return value

    def validate_ingredients(self, value):
        ingredients = []
        for ingredient in value:
            name, amount = ingredient.values()
            ingredients.append(name)
        self.validate_duplicates(Ingredient, ingredients)
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо добавить изображение!')
        return value

    def add_tags_and_ingredients_to_recipe(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        all_ingredients = []
        for ingredient in ingredients:
            amount = ingredient.get('amount')
            ingredient = get_object_or_404(
                Ingredient, id=ingredient.get('name').id
            )
            ingredient_in_recipe = IngredientInRecipe(
                name=ingredient, recipe=recipe, amount=amount
            )
            all_ingredients.append(ingredient_in_recipe)
        IngredientInRecipe.objects.bulk_create(all_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.add_tags_and_ingredients_to_recipe(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
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
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscribeSerializer(serializers.ModelSerializer):
    "Сериализатор для модели Subscription."
    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source='following.avatar')

    class Meta:
        model = Subscription
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )
        read_only_fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            user=obj.user, following=obj.following).exists()

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.following)
        recipes_limit = self.context.get('recipes_limit')
        if recipes_limit:
            return RecipeShortInformation(
                recipes[:int(recipes_limit)], many=True
            ).data
        return RecipeShortInformation(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.following).count()
