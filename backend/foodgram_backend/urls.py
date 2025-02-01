from django.contrib import admin
from django.urls import include, path, re_path

from api.v1.views import redirect_to_recipe
from foodgram_backend.settings import PREFIX_SHORT_LINK_RECIPE


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    re_path(
        fr'{PREFIX_SHORT_LINK_RECIPE}(?P<short_link>)[a-zA-Z0-9]+/',
        redirect_to_recipe
    ),
]
