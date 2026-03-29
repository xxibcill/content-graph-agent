import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.content_service import build_initial_state, extract_script, run_workflow


class ContentServiceTests(unittest.TestCase):
    def test_build_initial_state_only_includes_optional_values_when_present(self) -> None:
        state = build_initial_state(
            topic="topic",
            niche="niche",
            limit=4,
            research_mode="react",
            feedback="feedback",
            brand_voice="clear",
            writer_max_sentences=5,
            creative_max_sentences=4,
            validation_retry_enabled=True,
            validation_max_retries=2,
        )
        self.assertEqual(state["topic"], "topic")
        self.assertEqual(state["niche"], "niche")
        self.assertEqual(state["research_limit"], 4)
        self.assertEqual(state["research_mode"], "react")
        self.assertEqual(state["manual_feedback"], "feedback")
        self.assertEqual(state["brand_voice"], "clear")
        self.assertEqual(state["writer_max_sentences"], 5)
        self.assertEqual(state["creative_max_sentences"], 4)
        self.assertTrue(state["validation_retry_enabled"])
        self.assertEqual(state["validation_max_retries"], 2)

    def test_extract_script_prefers_final_script(self) -> None:
        script = extract_script(
            {
                "draft_script": "draft",
                "validated_script": "validated",
                "final_script": "final",
            }
        )
        self.assertEqual(script, "final")

    @patch("services.content_service.build_graph")
    def test_run_workflow_returns_result_without_persistence(
        self,
        mock_build_graph,
    ) -> None:
        mock_build_graph.return_value = SimpleNamespace(
            invoke=lambda state: {"final_script": f"Result for {state['topic']}"}
        )

        payload = run_workflow(topic="personal branding")

        self.assertEqual(payload["script"], "Result for personal branding")
        self.assertEqual(payload["result"]["final_script"], "Result for personal branding")
        self.assertNotIn("saved_run_id", payload)

    @patch("services.content_service.save_run")
    @patch("services.content_service.get_settings")
    @patch("services.content_service.build_graph")
    def test_run_workflow_persists_when_requested(
        self,
        mock_build_graph,
        mock_get_settings,
        mock_save_run,
    ) -> None:
        mock_build_graph.return_value = SimpleNamespace(
            invoke=lambda state: {"draft_script": f"Draft for {state['topic']}"}
        )
        mock_get_settings.return_value = SimpleNamespace(output_dir="outputs")
        mock_save_run.return_value = {
            "run_id": "run-123",
            "path": "outputs/runs.jsonl",
        }

        payload = run_workflow(
            topic="personal branding",
            save_output_enabled=True,
        )

        self.assertEqual(payload["saved_run_id"], "run-123")
        self.assertEqual(payload["saved_path"], "outputs/runs.jsonl")
        mock_save_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
