from django_filters.rest_framework import DjangoFilterBackend
from django_short_url.views import get_surl
from django.http import HttpResponse
from django.db.models import Sum
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
    IngredientSerializer,
    RecipeSerializer,
    RecipeShortInformation,
    RecipeReadSerializer,
    SubscribeSerializer,
    TagSerializer,
    UserSerializer
)
from .viewsets import IngredientTagViewSet
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

    def check_user_in_subscription(self, id):
        return Subscription.objects.filter(
            user=self.request.user,
            following=get_object_or_404(User, id=id)
        ).exists()

    def get_subscription_context(self, request):
        return {
            'request': request,
            'recipes_limit': request.query_params.get('recipes_limit'),
        }

    @action(
        detail=False,
        url_path='me',
        permission_classes=(IsAuthenticated,)
    )
    def get_me(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('put', 'delete',),
        url_path='me/avatar',
    )
    def put_or_delete_avatar(self, request):
        if request.method == 'PUT':
            serializer = AvatarSerializer(request.user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        subscriptions = request.user.subscriptions.all()
        context = self.get_subscription_context(request)
        pages = self.paginate_queryset(subscriptions)
        if pages is not None:
            serializer = SubscribeSerializer(
                subscriptions, context=context, many=True
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscribeSerializer(pages, context=context, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete',),
    )
    def subscribe(self, request, id=None):
        user = request.user
        following = get_object_or_404(User, id=id)

        if user == following:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'POST':
            if self.check_user_in_subscription(id):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            subscription = Subscription.objects.create(
                user=user,
                following=following
            )
            context = self.get_subscription_context(request)
            serializer = SubscribeSerializer(subscription, context=context)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not self.check_user_in_subscription(id):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        Subscription.objects.filter(
            user=user,
            following=following
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(IngredientTagViewSet):
    """Вьюсет для модели Tag."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(IngredientTagViewSet):
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

    def get_recipe(self):
        return get_object_or_404(Recipe, id=self.kwargs.get('pk'))

    def check_recipe_in_model(self, model):
        return model.objects.filter(
            user=self.request.user,
            recipe=self.get_recipe()
        ).exists()

    def add_recipe_to_model(self, request, model):
        if self.check_recipe_in_model(model):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        model.objects.create(user=request.user, recipe=self.get_recipe())
        serializer = RecipeShortInformation(self.get_recipe())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe_from_model(self, request, model):
        if not self.check_recipe_in_model(model):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        model.objects.filter(
            user=request.user, recipe=self.get_recipe()).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve',):
            return RecipeReadSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        self.get_recipe()
        short_url = get_surl(f'/api/recipes/{pk}/')
        return Response(
            {'short-link': request.build_absolute_uri(short_url)},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.add_recipe_to_model(request, RecipeInShoppingCart)
        return self.delete_recipe_from_model(request, RecipeInShoppingCart)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, pk=None):
        shopping_cart = "Список покупок пуст!"
        recipes = request.user.recipes_in_shopping_cart.all().values('recipe')
        if recipes:
            shopping_cart = []
            ingredients = IngredientInRecipe.objects.filter(
                recipe__in=recipes
            ).values(
                'name__name',
                'name__measurement_unit',
            ).annotate(total=Sum('amount'))
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
        methods=('post', 'delete',),
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.add_recipe_to_model(request, Favorite)
        return self.delete_recipe_from_model(request, Favorite)
