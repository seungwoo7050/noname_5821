from django.contrib import admin
from django.urls import path

from catalog.api import game_detail, game_search

from .views import viability

urlpatterns = [
    path("ops/", admin.site.urls),
    path("api/v1/viability", viability, name="api-v1-viability"),
    path("api/v1/games", game_search, name="api-v1-game-search"),
    path("api/v1/games/<uuid:game_id>", game_detail, name="api-v1-game-detail"),
]
