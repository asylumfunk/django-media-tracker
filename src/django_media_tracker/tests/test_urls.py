"""Tests for the public API health check."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APISimpleTestCase


class HealthTests(APISimpleTestCase):
    """Exercise the health endpoint without authentication or a database."""

    def test_anonymous_get_reports_health(self) -> None:
        """Return a successful health response to anonymous callers."""
        response = self.client.get(reverse('health'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_post_is_rejected(self) -> None:
        """Reject write requests to the health endpoint."""
        response = self.client.post(reverse('health'))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
