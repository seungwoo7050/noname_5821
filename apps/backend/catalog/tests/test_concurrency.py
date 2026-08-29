import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import TransactionTestCase

from catalog.models import CompletionScope, Game, Lifecycle, Platform, PlaytimeAggregateRevision
from catalog.services import create_draft_observation, moderate_observation


class ConcurrentApprovalTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.operator = get_user_model().objects.create_user(
            "operator", password=None, is_staff=True
        )
        self.game = Game.objects.create(
            slug="sample-game",
            korean_title="샘플 게임",
            original_title="Sample Game",
            lifecycle=Lifecycle.ACTIVE,
        )
        self.platform = Platform.objects.create(
            code="pc",
            display_label="PC",
            lifecycle=Lifecycle.ACTIVE,
        )

    def draft(self, minutes, sequence):
        return create_draft_observation(
            operator=self.operator,
            operation_uuid=uuid.uuid4(),
            game=self.game,
            platform=self.platform,
            completion_scope=CompletionScope.MAIN_STORY,
            minutes=minutes,
            provenance_identity=f"urn:local-fixture:concurrent-{sequence:03d}",
            observation_date=datetime.date(2026, 8, 29),
        ).observation

    def approve(self, observation_id):
        close_old_connections()
        try:
            return moderate_observation(
                operator=self.operator,
                observation_id=observation_id,
                operation_uuid=uuid.uuid4(),
                decision="approved",
                reason_code="concurrent_test",
            )
        finally:
            close_old_connections()

    def test_concurrent_final_approvals_leave_one_complete_current_revision(self):
        observations = [
            self.draft(minutes, index) for index, minutes in enumerate([600, 720, 900, 1080], 1)
        ]
        self.approve(observations[0].id)
        self.approve(observations[1].id)

        with ThreadPoolExecutor(max_workers=2) as executor:
            receipts = list(
                executor.map(
                    self.approve,
                    [observations[2].id, observations[3].id],
                )
            )

        self.assertEqual(len(receipts), 2)
        current = PlaytimeAggregateRevision.objects.get(state="current")
        included = list(current.included_observations.values_list("id", flat=True))
        self.assertEqual(current.sample_count, 4)
        self.assertEqual(current.median_minutes, 810)
        self.assertEqual(len(included), len(set(included)))
        self.assertEqual(
            PlaytimeAggregateRevision.objects.filter(state="current").count(),
            1,
        )
