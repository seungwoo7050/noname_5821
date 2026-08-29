import datetime
import json
import uuid
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from jsonschema import Draft202012Validator, FormatChecker

from catalog.models import CompletionScope, Game, GameAlias, Lifecycle, Platform
from catalog.services import create_draft_observation, moderate_observation

CONTRACT_ROOT = Path(__file__).resolve().parents[4] / "contracts" / "public-api" / "v1"


class PublicApiTests(TestCase):
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
        GameAlias.objects.create(
            game=cls.game,
            locale="ko",
            text="샘플 게임",
            alias_type=GameAlias.AliasType.KOREAN,
            priority=1,
        )
        GameAlias.objects.create(
            game=cls.game,
            locale="en",
            text="Sample Game",
            alias_type=GameAlias.AliasType.ORIGINAL,
            priority=2,
        )
        cls.platform = Platform.objects.create(
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
            provenance_identity=f"urn:local-fixture:api-{sequence:03d}",
            observation_date=datetime.date(2026, 8, 29),
        ).observation

    def approve(self, observation):
        return moderate_observation(
            operator=self.operator,
            observation_id=observation.id,
            operation_uuid=uuid.uuid4(),
            decision="approved",
            reason_code="api_fixture",
        )

    def validator(self, filename):
        schema = json.loads((CONTRACT_ROOT / filename).read_text())
        return Draft202012Validator(schema, format_checker=FormatChecker())

    def test_searches_korean_and_original_alias_under_schema(self):
        for query in ("샘플", "sample game"):
            response = self.client.get(reverse("api-v1-game-search"), {"query": query})
            self.assertEqual(response.status_code, 200)
            self.validator("game-search.schema.json").validate(response.json())
            self.assertEqual(response.json()["results"][0]["id"], str(self.game.id))

    def test_detail_is_insufficient_until_three_approved_observations(self):
        first = self.draft(600, 1)
        second = self.draft(720, 2)
        self.approve(first)
        self.approve(second)

        response = self.client.get(reverse("api-v1-game-detail", args=[self.game.id]))

        self.assertEqual(response.status_code, 200)
        self.validator("game-detail.schema.json").validate(response.json())
        self.assertEqual(response.json()["aggregates"][0]["status"], "insufficient_data")
        self.assertNotIn("median_minutes", response.json()["aggregates"][0])

    def test_detail_exposes_only_the_current_public_revision(self):
        observations = [
            self.draft(minutes, index) for index, minutes in enumerate([600, 720, 900], 1)
        ]
        for observation in observations:
            receipt = self.approve(observation)

        response = self.client.get(reverse("api-v1-game-detail", args=[self.game.id]))
        body = response.json()
        aggregate = body["aggregates"][0]

        self.validator("game-detail.schema.json").validate(body)
        self.assertEqual(aggregate["median_minutes"], 720)
        self.assertEqual(aggregate["sample_count"], 3)
        self.assertEqual(aggregate["revision_id"], str(receipt.aggregate_revision.id))
        serialized = json.dumps(body)
        for private_name in ("provenance", "operation_uuid", "audit", "included_observations"):
            self.assertNotIn(private_name, serialized)

    def test_invalid_filters_and_missing_game_return_stable_public_errors(self):
        oversized = self.client.get(reverse("api-v1-game-search"), {"query": "x" * 101})
        invalid_scope = self.client.get(
            reverse("api-v1-game-detail", args=[self.game.id]),
            {"scope": "combined"},
        )
        missing = self.client.get(reverse("api-v1-game-detail", args=[uuid.uuid4()]))

        self.assertEqual(oversized.status_code, 400)
        self.assertEqual(oversized.json()["error"]["code"], "invalid_search_query")
        self.assertEqual(invalid_scope.json()["error"]["code"], "invalid_completion_scope")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["code"], "game_not_found")

    def test_contract_example_is_valid_and_mutation_is_not_allowed(self):
        example = json.loads((CONTRACT_ROOT / "examples" / "sample-game.json").read_text())
        self.validator("game-detail.schema.json").validate(example)

        response = self.client.post(reverse("api-v1-game-search"), data={"query": "샘플"})
        self.assertEqual(response.status_code, 405)
