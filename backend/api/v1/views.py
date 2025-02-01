from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientNameSearchFilter, RecipeFilter
from .pagination import PageLimitPagination
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    FollowSerializer,
    IngredientSerializer,
    RecipeInShoppingCartSerializer,
    RecipeSerializer,
    RecipeReadSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSerializer
)
from .viewsets import ListRetrieveViewSet
from foodgram_backend.settings import PREFIX_SHORT_LINK_RECIPE
from recipes.models import (
    Favorite, Ingredient, IngredientInRecipe,
    Recipe, RecipeInShoppingCart, Tag
)
from users.models import Subscription, User


class UserViewSet(UserViewSet):
    """Вьюсет для модели User."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageLimitPagination
    lookup_field = 'id'

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=('put',),
        url_path='me/avatar',
    )
    def update_avatar(self, request):
        serializer = AvatarSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        followings = User.objects.filter(
            followings__user=request.user).prefetch_related('recipes')
        pages = self.paginate_queryset(followings)
        serializer = SubscriptionSerializer(
            pages,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
    )
    def subscribe(self, request, id=None):
        subscription_data = {
            'user': request.user.id,
            'following': get_object_or_404(User, id=id).id
        }
        serializer = FollowSerializer(
            data=subscription_data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        deleted_subscriptions, _ = Subscription.objects.filter(
            user=request.user,
            following=get_object_or_404(User, id=id)
        ).delete()
        if not deleted_subscriptions:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ListRetrieveViewSet):
    """Вьюсет для модели Tag."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ListRetrieveViewSet):
    """Вьюсет для модели Ingredient."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientNameSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Recipe."""
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination
    permission_classes = (IsAdminAuthorOrReadOnly,)
    http_method_names = ('get', 'post', 'patch', 'delete',)
    lookup_field = 'id'

    def get_recipe(self):
        return get_object_or_404(Recipe, id=self.kwargs.get('id'))

    def add_recipe_to_model(self, request, serializer):
        data = {
            'user': request.user.id,
            'recipe': self.get_recipe().id
        }
        serializer = serializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe_from_model(self, request, model):
        deleted_recipes, _ = model.objects.filter(
            user=request.user,
            recipe=self.get_recipe()
        ).delete()
        if not deleted_recipes:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve',):
            return RecipeReadSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
    )
    def get_link(self, request, id=None):
        recipe = self.get_recipe()
        short_link = f'/{PREFIX_SHORT_LINK_RECIPE}{recipe.short_link}/'
        return Response(
            {'short-link': request.build_absolute_uri(short_link)},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=('post',),
    )
    def shopping_cart(self, request, id=None):
        return self.add_recipe_to_model(
            request, RecipeInShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_recipe_from_shopping_cart(self, request, id=None):
        return self.delete_recipe_from_model(request, RecipeInShoppingCart)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, id=None):
        shopping_cart = "Список покупок пуст!"
        recipes = request.user.shopping_cart.all().values('recipe')
        if recipes:
            shopping_cart = []
            ingredients = IngredientInRecipe.objects.filter(
                recipe__in=recipes
            ).values(
                'name__name',
                'name__measurement_unit',
            ).annotate(amount=Sum('amount'))
            for ingredient in ingredients:
                name, measurement_unit, amount = ingredient.values()
                shopping_cart.append(f'• {name} - {amount} {measurement_unit}')
            shopping_cart = '\n'.join(shopping_cart)
        response = HttpResponse(shopping_cart, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="my_shopping_cart.txt"')
        return response

    @action(
        detail=True,
        methods=('post',),
    )
    def favorite(self, request, id=None):
        return self.add_recipe_to_model(request, FavoriteSerializer)

    @favorite.mapping.delete
    def delete_recipe_from_favorite(self, request, id=None):
        return self.delete_recipe_from_model(request, Favorite)


def redirect_to_recipe(request, short_link):
    print('привет')
    print(short_link)
    recipe_id = get_object_or_404(Recipe, short_link=short_link).id
    print('привет второй')
    return HttpResponseRedirect(
        request.build_absolute_uri(f'/api/recipes/{recipe_id}/'),
    )
