import io
import json

from django.core.management import call_command
from django.test import TestCase

from catalog.models import (
    AuditEvent,
    ModerationDecision,
    PlaytimeAggregateRevision,
    PlaytimeObservation,
)


class SyntheticFixtureCommandTests(TestCase):
    def test_loader_is_idempotent_and_labels_synthetic_evidence(self):
        first_output = io.StringIO()
        second_output = io.StringIO()

        call_command("load_synthetic_mvp", stdout=first_output)
        counts = (
            PlaytimeObservation.objects.count(),
            ModerationDecision.objects.count(),
            PlaytimeAggregateRevision.objects.count(),
            AuditEvent.objects.count(),
        )
        call_command("load_synthetic_mvp", stdout=second_output)

        first = json.loads(first_output.getvalue())
        second = json.loads(second_output.getvalue())
        self.assertEqual(first, second)
        self.assertEqual(first["evidence_type"], "synthetic_local_fixture")
        self.assertEqual(first["median_minutes"], 720)
        self.assertEqual(first["sample_count"], 3)
        self.assertEqual(
            (
                PlaytimeObservation.objects.count(),
                ModerationDecision.objects.count(),
                PlaytimeAggregateRevision.objects.count(),
                AuditEvent.objects.count(),
            ),
            counts,
        )
