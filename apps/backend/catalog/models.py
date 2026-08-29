import hashlib
import json
import unicodedata
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


def normalize_alias(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


class Lifecycle(models.TextChoices):
    DRAFT = "draft", "초안"
    ACTIVE = "active", "활성"
    RETIRED = "retired", "종료"


class CompletionScope(models.TextChoices):
    MAIN_STORY = "main_story", "메인 스토리"
    MAIN_PLUS_OPTIONAL = "main_plus_optional", "메인 + 선택"
    COMPLETIONIST = "completionist", "완전 공략"


class ModerationState(models.TextChoices):
    DRAFT = "draft", "초안"
    APPROVED = "approved", "승인"
    REJECTED = "rejected", "거절"


class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=100, unique=True)
    korean_title = models.CharField(max_length=240)
    original_title = models.CharField(max_length=240)
    lifecycle = models.CharField(max_length=16, choices=Lifecycle, default=Lifecycle.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.korean_title


class GameAlias(models.Model):
    class AliasType(models.TextChoices):
        KOREAN = "korean", "한국어"
        ORIGINAL = "original", "원어"
        ENGLISH = "english", "영어"
        ALTERNATE = "alternate", "대체명"
        EDITION = "edition", "에디션"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name="aliases")
    locale = models.CharField(max_length=20)
    text = models.CharField(max_length=240)
    normalized_text = models.CharField(max_length=240, editable=False)
    alias_type = models.CharField(max_length=16, choices=AliasType)
    priority = models.PositiveSmallIntegerField(default=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["game", "locale", "normalized_text"],
                name="unique_normalized_alias_per_game_locale",
            )
        ]
        ordering = ["priority", "normalized_text"]

    def save(self, *args, **kwargs) -> None:
        self.normalized_text = normalize_alias(self.text)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.text


class Platform(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(max_length=40, unique=True)
    display_label = models.CharField(max_length=100)
    lifecycle = models.CharField(max_length=16, choices=Lifecycle, default=Lifecycle.DRAFT)

    def __str__(self) -> str:
        return self.display_label


class PlaytimeObservation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operation_uuid = models.UUIDField(unique=True)
    payload_fingerprint = models.CharField(max_length=64, unique=True, editable=False)
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name="observations")
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT, related_name="observations")
    completion_scope = models.CharField(max_length=32, choices=CompletionScope)
    minutes = models.PositiveIntegerField()
    provenance_identity = models.CharField(max_length=240)
    observation_date = models.DateField()
    moderation_state = models.CharField(
        max_length=16,
        choices=ModerationState,
        default=ModerationState.DRAFT,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="playtime_observations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(minutes__gt=0), name="observation_minutes_positive")
        ]

    @classmethod
    def fingerprint_for(
        cls,
        *,
        game_id: uuid.UUID,
        platform_id: uuid.UUID,
        completion_scope: str,
        minutes: int,
        provenance_identity: str,
        observation_date,
    ) -> str:
        payload = {
            "completion_scope": completion_scope,
            "game_id": str(game_id),
            "minutes": minutes,
            "observation_date": observation_date.isoformat(),
            "platform_id": str(platform_id),
            "provenance_identity": normalize_alias(provenance_identity),
        }
        canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def clean(self) -> None:
        super().clean()
        if not self.provenance_identity.strip():
            raise ValidationError({"provenance_identity": "missing_provenance"})
        if self._state.adding and self.moderation_state != ModerationState.DRAFT:
            raise ValidationError({"moderation_state": "observation_must_begin_as_draft"})

    def clean_fields(self, exclude=None) -> None:
        if not isinstance(self.minutes, int) or isinstance(self.minutes, bool) or self.minutes <= 0:
            raise ValidationError({"minutes": "minutes_must_be_positive_integer"})
        super().clean_fields(exclude=exclude)

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            stored = type(self).objects.get(pk=self.pk)
            immutable_fields = (
                "game_id",
                "platform_id",
                "completion_scope",
                "minutes",
                "provenance_identity",
                "observation_date",
                "operation_uuid",
                "payload_fingerprint",
                "created_by_id",
            )
            if stored.moderation_state != ModerationState.DRAFT:
                raise ValidationError("terminal_observation_is_immutable")
            if self.moderation_state != stored.moderation_state:
                raise ValidationError("moderation_requires_transactional_service")
            if any(getattr(self, field) != getattr(stored, field) for field in immutable_fields):
                raise ValidationError("observation_payload_is_immutable")
        self.payload_fingerprint = self.fingerprint_for(
            game_id=self.game_id,
            platform_id=self.platform_id,
            completion_scope=self.completion_scope,
            minutes=self.minutes,
            provenance_identity=self.provenance_identity,
            observation_date=self.observation_date,
        )
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("observation_history_cannot_be_deleted")


class AggregateKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name="aggregate_keys")
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT, related_name="aggregate_keys")
    completion_scope = models.CharField(max_length=32, choices=CompletionScope)
    current_revision = models.OneToOneField(
        "PlaytimeAggregateRevision",
        on_delete=models.PROTECT,
        related_name="current_for_key",
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["game", "platform", "completion_scope"],
                name="unique_aggregate_key",
            )
        ]


class PlaytimeAggregateRevision(models.Model):
    class State(models.TextChoices):
        CURRENT = "current", "현재"
        SUPERSEDED = "superseded", "대체됨"
        RETIRED = "retired", "종료"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aggregate_key = models.ForeignKey(
        AggregateKey, on_delete=models.PROTECT, related_name="revisions"
    )
    revision_number = models.PositiveIntegerField()
    rule_revision = models.CharField(max_length=32, default="median-v1")
    median_minutes = models.PositiveIntegerField()
    sample_count = models.PositiveIntegerField()
    included_observations = models.ManyToManyField(
        PlaytimeObservation,
        through="AggregateObservation",
        related_name="aggregate_revisions",
    )
    calculated_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=16, choices=State, default=State.CURRENT)
    supersedes = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        related_name="superseded_by",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["aggregate_key", "revision_number"],
                name="unique_aggregate_revision_number",
            ),
            models.UniqueConstraint(
                fields=["aggregate_key"],
                condition=Q(state="current"),
                name="one_current_revision_per_key",
            ),
            models.CheckConstraint(
                condition=Q(sample_count__gte=3), name="aggregate_minimum_sample"
            ),
            models.CheckConstraint(
                condition=Q(median_minutes__gt=0), name="aggregate_median_positive"
            ),
        ]


class AggregateObservation(models.Model):
    aggregate_revision = models.ForeignKey(PlaytimeAggregateRevision, on_delete=models.PROTECT)
    observation = models.ForeignKey(PlaytimeObservation, on_delete=models.PROTECT)
    position = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["aggregate_revision", "observation"],
                name="unique_observation_per_revision",
            ),
            models.UniqueConstraint(
                fields=["aggregate_revision", "position"],
                name="unique_observation_position_per_revision",
            ),
        ]
        ordering = ["position"]


class ModerationDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    observation = models.OneToOneField(
        PlaytimeObservation,
        on_delete=models.PROTECT,
        related_name="moderation_decision",
    )
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decision = models.CharField(max_length=16, choices=ModerationState)
    reason_code = models.CharField(max_length=64)
    operation_uuid = models.UUIDField(unique=True)
    input_hash = models.CharField(max_length=64)
    decided_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError("moderation_decision_is_immutable")
        if self.decision == ModerationState.DRAFT:
            raise ValidationError("draft_is_not_a_decision")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("moderation_decision_cannot_be_deleted")


class AuditEvent(models.Model):
    class Outcome(models.TextChoices):
        SUCCEEDED = "succeeded", "성공"
        REJECTED = "rejected", "거절"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    operation_uuid = models.UUIDField(unique=True)
    entity_type = models.CharField(max_length=64)
    entity_id = models.UUIDField()
    action = models.CharField(max_length=64)
    contract_revision = models.CharField(max_length=32, default="ops/v1")
    rule_revision = models.CharField(max_length=32, blank=True)
    input_hash = models.CharField(max_length=64)
    outcome = models.CharField(max_length=16, choices=Outcome)
    failure_code = models.CharField(max_length=64, blank=True)
    aggregate_revision = models.ForeignKey(
        PlaytimeAggregateRevision,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError("audit_event_is_append_only")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("audit_event_is_append_only")
