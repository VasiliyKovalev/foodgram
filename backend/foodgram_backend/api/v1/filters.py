from django_filters import FilterSet, BooleanFilter, ModelMultipleChoiceFilter
from rest_framework import filters

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )

    class Meta:
        model = Recipe
        fields = ('author',)

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorite_users__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(users_shopping_cart__user=self.request.user)
        return queryset


class IngredientNameSearchFilter(filters.SearchFilter):
    search_param = 'name'
