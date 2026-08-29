import datetime
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import (
    CompletionScope,
    Game,
    GameAlias,
    Lifecycle,
    ModerationState,
    Platform,
    PlaytimeObservation,
    normalize_alias,
)


class ModelContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.operator = get_user_model().objects.create_user(
            "operator", password=None, is_staff=True
        )
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

    def observation(self, **overrides):
        values = {
            "operation_uuid": uuid.uuid4(),
            "game": self.game,
            "platform": self.platform,
            "completion_scope": CompletionScope.MAIN_STORY,
            "minutes": 600,
            "provenance_identity": "urn:local-fixture:playtime-001",
            "observation_date": datetime.date(2026, 8, 29),
            "created_by": self.operator,
        }
        values.update(overrides)
        return PlaytimeObservation.objects.create(**values)

    def test_normalizes_unicode_case_and_whitespace(self):
        self.assertEqual(normalize_alias("  SAMPLE\u3000Game  "), "sample game")
        alias = GameAlias.objects.create(
            game=self.game,
            locale="en",
            text="  Sample Game ",
            alias_type=GameAlias.AliasType.ORIGINAL,
        )
        self.assertEqual(alias.normalized_text, "sample game")

    def test_rejects_non_positive_and_fractional_minutes(self):
        with self.assertRaises(ValidationError):
            self.observation(minutes=0)
        with self.assertRaises(ValidationError):
            self.observation(minutes=1.5)

    def test_fingerprint_rejects_exact_duplicate(self):
        self.observation()
        with self.assertRaises(ValidationError):
            self.observation(operation_uuid=uuid.uuid4())

    def test_operation_identity_is_unique(self):
        operation_uuid = uuid.uuid4()
        self.observation(operation_uuid=operation_uuid)
        with self.assertRaises(ValidationError):
            self.observation(
                operation_uuid=operation_uuid,
                minutes=601,
                provenance_identity="urn:local-fixture:playtime-002",
            )

    def test_payload_and_terminal_state_cannot_be_mutated_or_deleted(self):
        observation = self.observation()
        observation.minutes = 601
        with self.assertRaises(ValidationError):
            observation.save()

        PlaytimeObservation.objects.filter(pk=observation.pk).update(
            moderation_state=ModerationState.APPROVED
        )
        observation.refresh_from_db()
        with self.assertRaises(ValidationError):
            observation.save()
        with self.assertRaises(ValidationError):
            observation.delete()
