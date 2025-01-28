from distutils.util import strtobool

from django_filters import (
    FilterSet, ModelMultipleChoiceFilter, TypedChoiceFilter)
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


RECIPE_FILTER_CHOICES = (
    (0, False),
    (1, True)
)


class RecipeFilter(FilterSet):
    is_favorited = TypedChoiceFilter(
        choices=RECIPE_FILTER_CHOICES,
        method='filter_is_favorited',
        coerce=strtobool
    )
    is_in_shopping_cart = TypedChoiceFilter(
        choices=RECIPE_FILTER_CHOICES,
        method='filter_is_in_shopping_cart',
        coerce=strtobool
    )
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )

    class Meta:
        model = Recipe
        fields = ('author',)

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite_users__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(users_shopping_cart__user=self.request.user)
        return queryset


class IngredientNameSearchFilter(SearchFilter):
    search_param = 'name'
