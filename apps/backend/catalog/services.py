import datetime
import hashlib
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import (
    AggregateKey,
    AggregateObservation,
    AuditEvent,
    ModerationDecision,
    ModerationState,
    PlaytimeAggregateRevision,
    PlaytimeObservation,
    normalize_alias,
)


class OperationRejected(Exception):
    def __init__(self, code: str, receipt_id: uuid.UUID | None = None):
        super().__init__(code)
        self.code = code
        self.receipt_id = receipt_id


@dataclass(frozen=True)
class DraftReceipt:
    observation: PlaytimeObservation
    audit_event: AuditEvent
    replayed: bool


@dataclass(frozen=True)
class ModerationReceipt:
    observation: PlaytimeObservation
    decision: ModerationDecision
    audit_event: AuditEvent
    aggregate_revision: PlaytimeAggregateRevision | None
    replayed: bool


def _require_operator(operator) -> None:
    if not operator.is_authenticated or not operator.is_active or not operator.is_staff:
        raise PermissionDenied("operator_required")


def _input_hash(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode()).hexdigest()


def create_draft_observation(
    *,
    operator,
    operation_uuid: uuid.UUID,
    game,
    platform,
    completion_scope: str,
    minutes: int,
    provenance_identity: str,
    observation_date: datetime.date,
) -> DraftReceipt:
    _require_operator(operator)
    payload_hash = _input_hash(
        {
            "completion_scope": completion_scope,
            "game_id": str(getattr(game, "id", game)),
            "minutes": minutes,
            "observation_date": (
                observation_date.isoformat()
                if isinstance(observation_date, datetime.date)
                else str(observation_date)
            ),
            "platform_id": str(getattr(platform, "id", platform)),
            "provenance_identity": normalize_alias(provenance_identity),
        }
    )
    existing = AuditEvent.objects.filter(operation_uuid=operation_uuid).first()
    if existing:
        if existing.action != "observation.create_draft" or existing.input_hash != payload_hash:
            raise OperationRejected("operation_uuid_conflict", existing.id)
        if existing.outcome == AuditEvent.Outcome.REJECTED:
            raise OperationRejected(existing.failure_code, existing.id)
        return DraftReceipt(
            observation=PlaytimeObservation.objects.get(pk=existing.entity_id),
            audit_event=existing,
            replayed=True,
        )

    observation_id = uuid.uuid4()
    observation = PlaytimeObservation(
        id=observation_id,
        operation_uuid=operation_uuid,
        game=game,
        platform=platform,
        completion_scope=completion_scope,
        minutes=minutes,
        provenance_identity=provenance_identity,
        observation_date=observation_date,
        created_by=operator,
    )
    try:
        observation.full_clean()
    except ValidationError as error:
        code = _stable_validation_code(error)
        event = AuditEvent.objects.create(
            actor=operator,
            operation_uuid=operation_uuid,
            entity_type="playtime_observation",
            entity_id=observation_id,
            action="observation.create_draft",
            input_hash=payload_hash,
            outcome=AuditEvent.Outcome.REJECTED,
            failure_code=code,
        )
        raise OperationRejected(code, event.id) from error

    fingerprint = PlaytimeObservation.fingerprint_for(
        game_id=game.id,
        platform_id=platform.id,
        completion_scope=completion_scope,
        minutes=minutes,
        provenance_identity=provenance_identity,
        observation_date=observation_date,
    )
    if PlaytimeObservation.objects.filter(payload_fingerprint=fingerprint).exists():
        event = AuditEvent.objects.create(
            actor=operator,
            operation_uuid=operation_uuid,
            entity_type="playtime_observation",
            entity_id=observation_id,
            action="observation.create_draft",
            input_hash=payload_hash,
            outcome=AuditEvent.Outcome.REJECTED,
            failure_code="duplicate_observation",
        )
        raise OperationRejected("duplicate_observation", event.id)

    with transaction.atomic():
        observation.save()
        event = AuditEvent.objects.create(
            actor=operator,
            operation_uuid=operation_uuid,
            entity_type="playtime_observation",
            entity_id=observation.id,
            action="observation.create_draft",
            input_hash=payload_hash,
            outcome=AuditEvent.Outcome.SUCCEEDED,
        )
    return DraftReceipt(observation=observation, audit_event=event, replayed=False)


def _stable_validation_code(error: ValidationError) -> str:
    if hasattr(error, "message_dict"):
        field = sorted(error.message_dict)[0]
        message = error.message_dict[field][0]
        if isinstance(message, str) and " " not in message:
            return message
        return f"invalid_{field}"
    return "invalid_observation"


def median_v1(values: list[int]) -> int:
    if not values:
        raise ValueError("median_requires_values")
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint] + 1) // 2


def moderate_observation(
    *,
    operator,
    observation_id: uuid.UUID,
    operation_uuid: uuid.UUID,
    decision: str,
    reason_code: str,
    failure_hook: Callable[[str], None] | None = None,
) -> ModerationReceipt:
    _require_operator(operator)
    payload_hash = _input_hash(
        {
            "decision": decision,
            "observation_id": str(observation_id),
            "reason_code": reason_code,
        }
    )
    action = {
        ModerationState.APPROVED: "observation.approve",
        ModerationState.REJECTED: "observation.reject",
    }.get(decision, "observation.moderate")
    existing = AuditEvent.objects.filter(operation_uuid=operation_uuid).first()
    if existing:
        if existing.input_hash != payload_hash or not existing.action.startswith(action):
            raise OperationRejected("operation_uuid_conflict", existing.id)
        if existing.outcome == AuditEvent.Outcome.REJECTED:
            raise OperationRejected(existing.failure_code, existing.id)
        moderation = ModerationDecision.objects.get(operation_uuid=operation_uuid)
        return ModerationReceipt(
            observation=moderation.observation,
            decision=moderation,
            audit_event=existing,
            aggregate_revision=existing.aggregate_revision,
            replayed=True,
        )

    if decision not in (ModerationState.APPROVED, ModerationState.REJECTED):
        event = AuditEvent.objects.create(
            actor=operator,
            operation_uuid=operation_uuid,
            entity_type="playtime_observation",
            entity_id=observation_id,
            action=action,
            input_hash=payload_hash,
            outcome=AuditEvent.Outcome.REJECTED,
            failure_code="invalid_moderation_decision",
        )
        raise OperationRejected("invalid_moderation_decision", event.id)

    rejected_event = None
    receipt = None
    with transaction.atomic():
        observation = PlaytimeObservation.objects.select_for_update().get(pk=observation_id)
        if observation.moderation_state != ModerationState.DRAFT:
            rejected_event = AuditEvent.objects.create(
                actor=operator,
                operation_uuid=operation_uuid,
                entity_type="playtime_observation",
                entity_id=observation.id,
                action=action,
                input_hash=payload_hash,
                outcome=AuditEvent.Outcome.REJECTED,
                failure_code="observation_already_moderated",
            )
        else:
            moderation = ModerationDecision.objects.create(
                observation=observation,
                operator=operator,
                decision=decision,
                reason_code=reason_code,
                operation_uuid=operation_uuid,
                input_hash=payload_hash,
            )
            PlaytimeObservation.objects.filter(pk=observation.pk).update(moderation_state=decision)
            if failure_hook:
                failure_hook("after_observation_state")

            aggregate_revision = None
            event_action = action
            if decision == ModerationState.APPROVED:
                aggregate_revision, event_action = _recalculate_aggregate(
                    observation=observation,
                    operator=operator,
                    failure_hook=failure_hook,
                )
            if failure_hook:
                failure_hook("before_audit")
            event = AuditEvent.objects.create(
                actor=operator,
                operation_uuid=operation_uuid,
                entity_type="playtime_observation",
                entity_id=observation.id,
                action=event_action,
                contract_revision="ops/v1",
                rule_revision="median-v1" if decision == ModerationState.APPROVED else "",
                input_hash=payload_hash,
                outcome=AuditEvent.Outcome.SUCCEEDED,
                aggregate_revision=aggregate_revision,
            )
            observation.refresh_from_db()
            receipt = ModerationReceipt(
                observation=observation,
                decision=moderation,
                audit_event=event,
                aggregate_revision=aggregate_revision,
                replayed=False,
            )

    if rejected_event:
        raise OperationRejected("observation_already_moderated", rejected_event.id)
    return receipt


def _recalculate_aggregate(*, observation, operator, failure_hook):
    key, created = AggregateKey.objects.get_or_create(
        game=observation.game,
        platform=observation.platform,
        completion_scope=observation.completion_scope,
    )
    if not created:
        key = AggregateKey.objects.select_for_update().get(pk=key.pk)

    eligible = list(
        PlaytimeObservation.objects.select_for_update()
        .filter(
            game=observation.game,
            platform=observation.platform,
            completion_scope=observation.completion_scope,
            moderation_state=ModerationState.APPROVED,
        )
        .order_by("id")
    )
    if len(eligible) < 3:
        return None, "observation.approve"

    previous = key.current_revision
    if previous:
        PlaytimeAggregateRevision.objects.filter(pk=previous.pk).update(
            state=PlaytimeAggregateRevision.State.SUPERSEDED
        )
    revision = PlaytimeAggregateRevision.objects.create(
        aggregate_key=key,
        revision_number=(previous.revision_number + 1) if previous else 1,
        rule_revision="median-v1",
        median_minutes=median_v1([item.minutes for item in eligible]),
        sample_count=len(eligible),
        state=PlaytimeAggregateRevision.State.CURRENT,
        supersedes=previous,
        created_by=operator,
    )
    AggregateObservation.objects.bulk_create(
        [
            AggregateObservation(
                aggregate_revision=revision,
                observation=item,
                position=position,
            )
            for position, item in enumerate(eligible, start=1)
        ]
    )
    AggregateKey.objects.filter(pk=key.pk).update(current_revision=revision)
    key.current_revision = revision
    if failure_hook:
        failure_hook("after_aggregate_revision")
    return (
        revision,
        "observation.approve_and_supersede" if previous else "observation.approve_and_publish",
    )
