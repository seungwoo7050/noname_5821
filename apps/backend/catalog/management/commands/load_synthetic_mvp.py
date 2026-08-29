import datetime
import json
import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from catalog.models import AuditEvent, CompletionScope, Game, GameAlias, Lifecycle, Platform
from catalog.services import create_draft_observation, moderate_observation

GAME_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")
PLATFORM_ID = uuid.UUID("22222222-2222-4222-8222-222222222222")
ALIAS_IDS = (
    uuid.UUID("44444444-4444-4444-8444-444444444441"),
    uuid.UUID("44444444-4444-4444-8444-444444444442"),
)
DRAFT_OPERATIONS = [uuid.UUID(f"00000000-0000-4000-8000-{index:012d}") for index in range(1, 6)]
MODERATION_OPERATIONS = [
    uuid.UUID(f"10000000-0000-4000-8000-{index:012d}") for index in range(1, 5)
]


class Command(BaseCommand):
    help = "Load the idempotent synthetic MVP loop without any real credentials or source data"

    def handle(self, *args, **options):
        operator, created = get_user_model().objects.get_or_create(
            username="synthetic-operator",
            defaults={"is_active": True, "is_staff": True},
        )
        if created:
            operator.set_unusable_password()
            operator.save(update_fields=["password"])
        game, _ = Game.objects.update_or_create(
            id=GAME_ID,
            defaults={
                "slug": "sample-game",
                "korean_title": "샘플 게임",
                "original_title": "Sample Game",
                "lifecycle": Lifecycle.ACTIVE,
            },
        )
        platform, _ = Platform.objects.update_or_create(
            id=PLATFORM_ID,
            defaults={
                "code": "pc",
                "display_label": "PC",
                "lifecycle": Lifecycle.ACTIVE,
            },
        )
        aliases = []
        for alias_id, locale, text, alias_type, priority in (
            (ALIAS_IDS[0], "ko", "샘플 게임", GameAlias.AliasType.KOREAN, 1),
            (ALIAS_IDS[1], "en", "Sample Game", GameAlias.AliasType.ORIGINAL, 2),
        ):
            alias, _ = GameAlias.objects.update_or_create(
                id=alias_id,
                defaults={
                    "game": game,
                    "locale": locale,
                    "text": text,
                    "alias_type": alias_type,
                    "priority": priority,
                },
            )
            aliases.append(alias)

        observations = []
        for index, minutes in enumerate((600, 720, 900, 1200, 30), start=1):
            observations.append(
                create_draft_observation(
                    operator=operator,
                    operation_uuid=DRAFT_OPERATIONS[index - 1],
                    game=game,
                    platform=platform,
                    completion_scope=CompletionScope.MAIN_STORY,
                    minutes=minutes,
                    provenance_identity=f"urn:local-fixture:playtime-{index:03d}",
                    observation_date=datetime.date(2026, 8, 29),
                ).observation
            )

        moderation_receipts = []
        for index, observation in enumerate(observations[:3]):
            moderation_receipts.append(
                moderate_observation(
                    operator=operator,
                    observation_id=observation.id,
                    operation_uuid=MODERATION_OPERATIONS[index],
                    decision="approved",
                    reason_code="synthetic_fixture_approved",
                )
            )
        rejected = moderate_observation(
            operator=operator,
            observation_id=observations[3].id,
            operation_uuid=MODERATION_OPERATIONS[3],
            decision="rejected",
            reason_code="synthetic_fixture_rejected",
        )
        revision = moderation_receipts[-1].aggregate_revision
        evidence = {
            "evidence_type": "synthetic_local_fixture",
            "game_id": str(game.id),
            "alias_ids": [str(alias.id) for alias in aliases],
            "platform_id": str(platform.id),
            "approved": [
                {
                    "observation_id": str(receipt.observation.id),
                    "draft_operation_uuid": str(receipt.observation.operation_uuid),
                    "draft_audit_event_id": str(
                        AuditEvent.objects.get(operation_uuid=receipt.observation.operation_uuid).id
                    ),
                    "decision_id": str(receipt.decision.id),
                    "moderation_operation_uuid": str(receipt.decision.operation_uuid),
                    "audit_event_id": str(receipt.audit_event.id),
                }
                for receipt in moderation_receipts
            ],
            "rejected_observation_id": str(rejected.observation.id),
            "rejected_draft_audit_event_id": str(
                AuditEvent.objects.get(operation_uuid=rejected.observation.operation_uuid).id
            ),
            "rejected_moderation_audit_event_id": str(rejected.audit_event.id),
            "draft_observation_id": str(observations[4].id),
            "draft_only_audit_event_id": str(
                AuditEvent.objects.get(operation_uuid=observations[4].operation_uuid).id
            ),
            "aggregate_revision_id": str(revision.id),
            "aggregate_revision_number": revision.revision_number,
            "aggregate_key_id": str(revision.aggregate_key_id),
            "included_observation_ids": [
                str(item)
                for item in revision.aggregateobservation_set.order_by("position").values_list(
                    "observation_id", flat=True
                )
            ],
            "median_minutes": revision.median_minutes,
            "sample_count": revision.sample_count,
            "rule_revision": revision.rule_revision,
        }
        self.stdout.write(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
