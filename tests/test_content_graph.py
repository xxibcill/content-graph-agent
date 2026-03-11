import unittest
from unittest.mock import patch

from graph.content_graph import build_graph


class ContentGraphTests(unittest.TestCase):
    @patch("graph.content_graph.run_creative")
    @patch("graph.content_graph.run_validation")
    @patch("graph.content_graph.run_writer")
    @patch("graph.content_graph.run_research")
    def test_graph_runs_full_happy_path(
        self,
        mock_run_research,
        mock_run_writer,
        mock_run_validation,
        mock_run_creative,
    ) -> None:
        mock_run_research.return_value = {
            "bullets": ["Trend A"],
            "sources": ["https://example.com/a"],
            "query": "query",
            "provider": "tavily",
        }
        mock_run_writer.return_value = {
            "script": "Draft script.",
            "prompt_version": "v1",
        }
        mock_run_validation.return_value = {
            "validated_script": "Validated script.",
            "validation_status": "ok",
            "validation_notes": "ok",
            "validation_feedback": "- None detected",
        }
        mock_run_creative.return_value = {
            "script": "Final script.",
            "prompt_version": "v2",
        }

        result = build_graph().invoke({"topic": "personal branding"})

        self.assertEqual(result["final_script"], "Final script.")
        self.assertEqual(result["research_provider"], "tavily")
        self.assertEqual(result["writer_prompt_version"], "v1")
        self.assertEqual(result["creative_prompt_version"], "v2")

    @patch("graph.content_graph.run_creative")
    @patch("graph.content_graph.run_validation")
    @patch("graph.content_graph.run_writer")
    @patch("graph.content_graph.run_research")
    def test_graph_retries_writer_once_after_validation_rewrite(
        self,
        mock_run_research,
        mock_run_writer,
        mock_run_validation,
        mock_run_creative,
    ) -> None:
        mock_run_research.return_value = {
            "bullets": ["Trend A"],
            "sources": [],
            "query": "query",
            "provider": "tavily",
        }
        mock_run_writer.side_effect = [
            {"script": "Initial draft.", "prompt_version": "v1"},
            {"script": "Rewritten draft.", "prompt_version": "v1"},
        ]
        mock_run_validation.side_effect = [
            {
                "validated_script": "Initial draft.",
                "validation_status": "rewrite",
                "validation_notes": "rewrite",
                "validation_feedback": "Shorten the hook.",
            },
            {
                "validated_script": "Rewritten draft.",
                "validation_status": "ok",
                "validation_notes": "ok",
                "validation_feedback": "- None detected",
            },
        ]
        mock_run_creative.return_value = {
            "script": "Final script.",
            "prompt_version": "v2",
        }

        result = build_graph().invoke(
            {
                "topic": "personal branding",
                "validation_retry_enabled": True,
                "validation_max_retries": 1,
            }
        )

        self.assertEqual(mock_run_writer.call_count, 2)
        self.assertEqual(result["draft_script"], "Rewritten draft.")
        self.assertEqual(result["final_script"], "Final script.")


if __name__ == "__main__":
    unittest.main()
