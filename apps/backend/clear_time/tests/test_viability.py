from django.test import TestCase
from django.urls import reverse


class ViabilityTests(TestCase):
    def test_reports_a_real_postgresql_connection(self):
        response = self.client.get(reverse("api-v1-viability"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["contract"], "public-api/v1")
        self.assertEqual(response.json()["database"], "postgresql")
        self.assertEqual(response.json()["status"], "ready")
        self.assertTrue(response.json()["postgresql_version"].startswith("17."))

    def test_rejects_mutating_methods(self):
        response = self.client.post(reverse("api-v1-viability"), data={})

        self.assertEqual(response.status_code, 405)
