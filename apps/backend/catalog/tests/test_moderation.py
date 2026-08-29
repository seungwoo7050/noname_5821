import datetime
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from catalog.models import (
    AggregateKey,
    AuditEvent,
    CompletionScope,
    Game,
    Lifecycle,
    ModerationDecision,
    Platform,
    PlaytimeAggregateRevision,
)
from catalog.services import (
    OperationRejected,
    create_draft_observation,
    median_v1,
    moderate_observation,
)


class ModerationTests(TestCase):
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
        cls.other_game = Game.objects.create(
            slug="other-game",
            korean_title="다른 게임",
            original_title="Other Game",
            lifecycle=Lifecycle.ACTIVE,
        )
        cls.platform = Platform.objects.create(
            code="pc",
            display_label="PC",
            lifecycle=Lifecycle.ACTIVE,
        )

    def draft(self, minutes, sequence, **overrides):
        values = {
            "operator": self.operator,
            "operation_uuid": uuid.uuid4(),
            "game": self.game,
            "platform": self.platform,
            "completion_scope": CompletionScope.MAIN_STORY,
            "minutes": minutes,
            "provenance_identity": f"urn:local-fixture:playtime-{sequence:03d}",
            "observation_date": datetime.date(2026, 8, 29),
        }
        values.update(overrides)
        return create_draft_observation(**values).observation

    def approve(self, observation, **overrides):
        values = {
            "operator": self.operator,
            "observation_id": observation.id,
            "operation_uuid": uuid.uuid4(),
            "decision": "approved",
            "reason_code": "fixture_approved",
        }
        values.update(overrides)
        return moderate_observation(**values)

    def test_median_v1_odd_even_and_half_up(self):
        self.assertEqual(median_v1([600, 720, 900]), 720)
        self.assertEqual(median_v1([600, 720, 900, 1080]), 810)
        self.assertEqual(median_v1([600, 601, 700, 701]), 651)

    def test_third_approval_atomically_publishes_reproducible_revision(self):
        observations = [
            self.draft(minutes, index) for index, minutes in enumerate([600, 720, 900], 1)
        ]
        first = self.approve(observations[0])
        second = self.approve(observations[1])
        third = self.approve(observations[2])

        self.assertIsNone(first.aggregate_revision)
        self.assertIsNone(second.aggregate_revision)
        revision = third.aggregate_revision
        self.assertEqual(revision.median_minutes, 720)
        self.assertEqual(revision.sample_count, 3)
        included = list(
            revision.aggregateobservation_set.order_by("position").values_list(
                "observation_id", flat=True
            )
        )
        self.assertEqual(included, sorted([item.id for item in observations]))
        self.assertEqual(revision.aggregate_key.current_revision_id, revision.id)
        self.assertEqual(third.audit_event.action, "observation.approve_and_publish")

    def test_rejected_draft_and_other_key_never_contribute(self):
        eligible = [self.draft(minutes, index) for index, minutes in enumerate([600, 720, 900], 1)]
        rejected = self.draft(1200, 4)
        other_key = self.draft(1, 5, game=self.other_game)
        moderate_observation(
            operator=self.operator,
            observation_id=rejected.id,
            operation_uuid=uuid.uuid4(),
            decision="rejected",
            reason_code="fixture_rejected",
        )
        self.approve(other_key)
        receipts = [self.approve(item) for item in eligible]

        revision = receipts[-1].aggregate_revision
        self.assertEqual(revision.sample_count, 3)
        self.assertEqual(revision.median_minutes, 720)
        self.assertNotIn(rejected.id, revision.included_observations.values_list("id", flat=True))
        self.assertNotIn(other_key.id, revision.included_observations.values_list("id", flat=True))

    def test_later_approval_supersedes_once_and_uses_even_median(self):
        observations = [
            self.draft(minutes, index) for index, minutes in enumerate([600, 720, 900, 1080], 1)
        ]
        receipts = [self.approve(item) for item in observations]

        first_revision = receipts[2].aggregate_revision
        second_revision = receipts[3].aggregate_revision
        first_revision.refresh_from_db()
        self.assertEqual(first_revision.state, "superseded")
        self.assertEqual(second_revision.revision_number, 2)
        self.assertEqual(second_revision.median_minutes, 810)
        self.assertEqual(
            PlaytimeAggregateRevision.objects.filter(state="current").count(),
            1,
        )
        self.assertEqual(receipts[3].audit_event.action, "observation.approve_and_supersede")

    def test_moderation_replay_resolves_and_conflicting_payload_rejects(self):
        observation = self.draft(600, 1)
        operation_uuid = uuid.uuid4()
        first = self.approve(observation, operation_uuid=operation_uuid)
        replay = self.approve(observation, operation_uuid=operation_uuid)

        self.assertTrue(replay.replayed)
        self.assertEqual(first.decision.id, replay.decision.id)
        with self.assertRaises(OperationRejected) as caught:
            moderate_observation(
                operator=self.operator,
                observation_id=observation.id,
                operation_uuid=operation_uuid,
                decision="rejected",
                reason_code="different",
            )
        self.assertEqual(caught.exception.code, "operation_uuid_conflict")

    def test_failure_before_audit_rolls_back_entire_final_approval(self):
        observations = [
            self.draft(minutes, index) for index, minutes in enumerate([600, 720, 900], 1)
        ]
        self.approve(observations[0])
        self.approve(observations[1])
        counts_before = (
            ModerationDecision.objects.count(),
            AuditEvent.objects.count(),
            PlaytimeAggregateRevision.objects.count(),
        )

        def fail_before_audit(stage):
            if stage == "before_audit":
                raise RuntimeError("synthetic_transaction_failure")

        with self.assertRaisesMessage(RuntimeError, "synthetic_transaction_failure"):
            self.approve(observations[2], failure_hook=fail_before_audit)

        observations[2].refresh_from_db()
        self.assertEqual(observations[2].moderation_state, "draft")
        self.assertEqual(
            (
                ModerationDecision.objects.count(),
                AuditEvent.objects.count(),
                PlaytimeAggregateRevision.objects.count(),
            ),
            counts_before,
        )
        self.assertIsNone(AggregateKey.objects.get().current_revision_id)

    def test_non_operator_and_second_decision_are_rejected_without_state_change(self):
        observation = self.draft(600, 1)
        with self.assertRaises(PermissionDenied):
            self.approve(observation, operator=self.visitor)
        self.approve(observation)
        with self.assertRaises(OperationRejected) as caught:
            self.approve(observation)
        self.assertEqual(caught.exception.code, "observation_already_moderated")
        self.assertEqual(ModerationDecision.objects.count(), 1)
