from django.test import Client
from django.test import SimpleTestCase


class HealthEndpointTests(SimpleTestCase):
    def test_health_endpoint_returns_healthy_status(self):
        client = Client()
        response = client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})
