import datetime
import hashlib
import json
import uuid
from dataclasses import dataclass

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import AuditEvent, PlaytimeObservation, normalize_alias


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
