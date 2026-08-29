from django.contrib import admin

from .models import Game, GameAlias, Platform, PlaytimeObservation
from .services import create_draft_observation


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
    exclude = ("created_by",)
    readonly_fields = ("payload_fingerprint", "moderation_state", "created_at")

    def save_model(self, request, obj, form, change):
        if change:
            obj.save()
            return
        receipt = create_draft_observation(
            operator=request.user,
            operation_uuid=obj.operation_uuid,
            game=obj.game,
            platform=obj.platform,
            completion_scope=obj.completion_scope,
            minutes=obj.minutes,
            provenance_identity=obj.provenance_identity,
            observation_date=obj.observation_date,
        )
        obj.__dict__.update(receipt.observation.__dict__)
