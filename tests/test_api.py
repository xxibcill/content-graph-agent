import importlib.util
import unittest
from unittest.mock import patch


FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    from fastapi.testclient import TestClient

    from api.main import app


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("api.main.run_workflow")
    def test_generate_endpoint_returns_workflow_payload(
        self,
        mock_run_workflow,
    ) -> None:
        mock_run_workflow.return_value = {
            "script": "Final script.",
            "result": {"final_script": "Final script."},
            "saved_run_id": None,
            "saved_path": None,
        }

        response = self.client.post(
            "/generate",
            json={"topic": "personal branding"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["script"], "Final script.")


if __name__ == "__main__":
    unittest.main()
