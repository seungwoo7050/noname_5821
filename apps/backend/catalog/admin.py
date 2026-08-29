from django.contrib import admin

from .models import Game, GameAlias, Platform, PlaytimeObservation


class AliasInline(admin.TabularInline):
    model = GameAlias
    extra = 1
    readonly_fields = ("normalized_text",)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("korean_title", "original_title", "lifecycle", "id")
    inlines = (AliasInline,)


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ("display_label", "code", "lifecycle", "id")


@admin.register(PlaytimeObservation)
class PlaytimeObservationAdmin(admin.ModelAdmin):
    list_display = (
        "game",
        "platform",
        "completion_scope",
        "minutes",
        "moderation_state",
        "id",
    )
    readonly_fields = ("payload_fingerprint", "moderation_state", "created_at")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
