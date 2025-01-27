from django.contrib import admin

from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag


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
        'id',
        'name',
        'measurement_unit',
    )
    list_editable = (
        'name',
        'measurement_unit',
    )


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'text',
        'cooking_time',
        'pub_date',
    )
    list_editable = (
        'name',
        'text',
        'cooking_time',
    )


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


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientInRecipe, IngredientInRecipeAdmin)
