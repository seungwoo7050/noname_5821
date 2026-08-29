import datetime
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from catalog.models import AuditEvent, CompletionScope, Game, Lifecycle, Platform
from catalog.services import OperationRejected, create_draft_observation


class DraftObservationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.operator = users.objects.create_user("operator", password=None, is_staff=True)
        cls.visitor = users.objects.create_user("visitor", password=None)
        cls.game = Game.objects.create(
            slug="sample-game",
            korean_title="샘플 게임",
            original_title="Sample Game",
            lifecycle=Lifecycle.ACTIVE,
        )
        cls.platform = Platform.objects.create(
            code="pc",
            display_label="PC",
            lifecycle=Lifecycle.ACTIVE,
        )

    def payload(self, **overrides):
        values = {
            "operator": self.operator,
            "operation_uuid": uuid.uuid4(),
            "game": self.game,
            "platform": self.platform,
            "completion_scope": CompletionScope.MAIN_STORY,
            "minutes": 600,
            "provenance_identity": "urn:local-fixture:playtime-001",
            "observation_date": datetime.date(2026, 8, 29),
        }
        values.update(overrides)
        return values

    def test_operator_creates_audited_draft_without_raw_provenance_in_audit(self):
        receipt = create_draft_observation(**self.payload())

        self.assertEqual(receipt.observation.moderation_state, "draft")
        self.assertEqual(receipt.audit_event.outcome, AuditEvent.Outcome.SUCCEEDED)
        self.assertNotIn("local-fixture", receipt.audit_event.input_hash)
        self.assertFalse(receipt.replayed)

    def test_non_operator_is_rejected_without_mutation(self):
        with self.assertRaises(PermissionDenied):
            create_draft_observation(**self.payload(operator=self.visitor))

        self.assertEqual(AuditEvent.objects.count(), 0)

    def test_same_operation_and_payload_resolves_the_receipt(self):
        payload = self.payload()
        first = create_draft_observation(**payload)
        replay = create_draft_observation(**payload)

        self.assertTrue(replay.replayed)
        self.assertEqual(first.observation.id, replay.observation.id)
        self.assertEqual(first.audit_event.id, replay.audit_event.id)
        self.assertEqual(AuditEvent.objects.count(), 1)

    def test_conflicting_operation_uuid_is_rejected(self):
        payload = self.payload()
        first = create_draft_observation(**payload)

        with self.assertRaises(OperationRejected) as caught:
            create_draft_observation(**{**payload, "minutes": 601})

        self.assertEqual(caught.exception.code, "operation_uuid_conflict")
        self.assertEqual(caught.exception.receipt_id, first.audit_event.id)

    def test_duplicate_fingerprint_is_audited_and_not_counted(self):
        create_draft_observation(**self.payload())

        with self.assertRaises(OperationRejected) as caught:
            create_draft_observation(**self.payload(operation_uuid=uuid.uuid4()))

        self.assertEqual(caught.exception.code, "duplicate_observation")
        self.assertEqual(AuditEvent.objects.filter(outcome="rejected").count(), 1)

    def test_invalid_minutes_is_audited_as_a_stable_rejection(self):
        with self.assertRaises(OperationRejected) as caught:
            create_draft_observation(**self.payload(minutes=0))

        self.assertEqual(caught.exception.code, "minutes_must_be_positive_integer")
        event = AuditEvent.objects.get()
        self.assertEqual(event.failure_code, "minutes_must_be_positive_integer")

    def test_missing_observation_date_is_audited_as_a_stable_rejection(self):
        with self.assertRaises(OperationRejected) as caught:
            create_draft_observation(**self.payload(observation_date=None))

        self.assertEqual(caught.exception.code, "invalid_observation_date")
        self.assertEqual(AuditEvent.objects.get().failure_code, "invalid_observation_date")
