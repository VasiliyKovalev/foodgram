from django.contrib import admin

from .models import (
    Favorite, Ingredient, IngredientInRecipe,
    Recipe, RecipeInShoppingCart, Tag
)


class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
    )
    list_editable = (
        'name',
        'slug',
    )


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    list_editable = (
        'measurement_unit',
    )
    search_fields = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'count_is_favorited',
    )
    search_fields = ('author__username', 'name',)
    list_filter = ('tags',)

    @admin.display(description="Количество добавлений в избранное")
    def count_is_favorited(self, obj):
        return obj.favorite_users.count()


class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'recipe',
        'amount',
    )
    list_editable = (
        'name',
        'recipe',
        'amount',
    )


class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'recipe',
   )
    list_editable = (
        'user',
        'recipe',
    )


class RecipeInShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'recipe',
    )
    list_editable = (
        'user',
        'recipe',
    )


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientInRecipe, IngredientInRecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(RecipeInShoppingCart, RecipeInShoppingCartAdmin)
