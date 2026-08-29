import uuid

from django.contrib import admin, messages

from .models import Game, GameAlias, Platform, PlaytimeObservation
from .services import OperationRejected, create_draft_observation, moderate_observation


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
    actions = ("approve_selected", "reject_selected")
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

    @admin.action(description="선택한 초안을 승인")
    def approve_selected(self, request, queryset):
        self._moderate_selected(request, queryset, "approved", "admin_approved")

    @admin.action(description="선택한 초안을 거절")
    def reject_selected(self, request, queryset):
        self._moderate_selected(request, queryset, "rejected", "admin_rejected")

    def _moderate_selected(self, request, queryset, decision, reason_code):
        succeeded = 0
        for observation in queryset:
            try:
                moderate_observation(
                    operator=request.user,
                    observation_id=observation.id,
                    operation_uuid=uuid.uuid4(),
                    decision=decision,
                    reason_code=reason_code,
                )
                succeeded += 1
            except OperationRejected as error:
                self.message_user(request, error.code, level=messages.ERROR)
        self.message_user(request, f"{succeeded}개 처리 완료", level=messages.SUCCESS)
