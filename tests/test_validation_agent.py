import unittest
from types import SimpleNamespace
from unittest.mock import patch

from agents.validation_agent import detect_issues, find_blocklist_hits, run_validation


def _make_response(content: str) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=None,
    )


class ValidationAgentTests(unittest.TestCase):
    def test_find_blocklist_hits_is_case_insensitive(self) -> None:
        hits = find_blocklist_hits("This is HYPE and fluff.", ["hype", "spam"])
        self.assertEqual(hits, ["hype"])

    def test_detect_issues_reports_length_and_blocklist(self) -> None:
        issues, sentence_count = detect_issues(
            "One. Two. Three.",
            max_sentences=2,
            blocklist=["three"],
        )
        self.assertEqual(sentence_count, 3)
        self.assertEqual(
            issues,
            [
                "Too long: 3 sentences (max 2).",
                "Blocked terms found: three",
            ],
        )

    @patch("agents.validation_agent.run_with_retry")
    @patch("agents.validation_agent.get_client_and_model")
    def test_run_validation_returns_ok_when_model_confirms(
        self,
        mock_get_client_and_model,
        mock_run_with_retry,
    ) -> None:
        mock_get_client_and_model.return_value = (
            object(),
            "model-name",
            "openai",
        )
        mock_run_with_retry.return_value = _make_response("OK")

        result = run_validation(
            "Keep this concise.",
            max_sentences=3,
            blocklist=[],
        )

        self.assertEqual(result["validation_status"], "ok")
        self.assertEqual(result["validated_script"], "Keep this concise.")
        self.assertEqual(result["validation_feedback"], "- None detected")

    @patch("agents.validation_agent.run_with_retry")
    @patch("agents.validation_agent.get_client_and_model")
    def test_run_validation_uses_rewrite_from_model_when_needed(
        self,
        mock_get_client_and_model,
        mock_run_with_retry,
    ) -> None:
        mock_get_client_and_model.return_value = (
            object(),
            "model-name",
            "openai",
        )
        mock_run_with_retry.return_value = _make_response("Shorter rewrite.")

        result = run_validation(
            "One. Two. Three.",
            max_sentences=2,
            blocklist=[],
        )

        self.assertEqual(result["validation_status"], "rewrite")
        self.assertEqual(result["validated_script"], "Shorter rewrite.")
        self.assertIn("Too long", result["validation_feedback"])


if __name__ == "__main__":
    unittest.main()
