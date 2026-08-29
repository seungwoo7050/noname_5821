from django.contrib import admin
from django.urls import path

from .views import viability

urlpatterns = [
    path("ops/", admin.site.urls),
    path("api/v1/viability", viability, name="api-v1-viability"),
]
