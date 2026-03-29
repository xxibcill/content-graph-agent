import unittest
from types import SimpleNamespace
from unittest.mock import patch

from agents.research_agent import (
    _normalize_serper,
    _normalize_tavily,
    build_query,
    extract_final_bullets,
    format_bullets,
    normalize_research_mode,
    parse_react_response,
    run_research,
)


class ResearchAgentTests(unittest.TestCase):
    def test_normalize_research_mode_defaults_to_basic(self) -> None:
        self.assertEqual(normalize_research_mode(None), "basic")
        self.assertEqual(normalize_research_mode("unknown"), "basic")
        self.assertEqual(normalize_research_mode("react"), "react")

    def test_build_query_with_niche(self) -> None:
        query = build_query("personal branding", "creator economy")
        self.assertEqual(
            query,
            "Trending topics and recent facts about personal branding in creator economy",
        )

    def test_build_query_without_niche(self) -> None:
        query = build_query("personal branding", None)
        self.assertEqual(
            query,
            "Trending topics and recent facts about personal branding",
        )

    def test_normalize_tavily_keeps_titles_snippets_and_sources(self) -> None:
        bullets, sources = _normalize_tavily(
            {
                "results": [
                    {
                        "title": "Trend A",
                        "content": "Snippet A",
                        "url": "https://example.com/a",
                    },
                    {
                        "title": "",
                        "content": "Snippet B",
                        "url": "https://example.com/b",
                    },
                ]
            },
            limit=5,
        )
        self.assertEqual(bullets, ["Trend A: Snippet A", "Snippet B"])
        self.assertEqual(
            sources,
            ["https://example.com/a", "https://example.com/b"],
        )

    def test_normalize_serper_respects_limit(self) -> None:
        bullets, sources = _normalize_serper(
            {
                "organic": [
                    {
                        "title": "Trend A",
                        "snippet": "Snippet A",
                        "link": "https://example.com/a",
                    },
                    {
                        "title": "Trend B",
                        "snippet": "Snippet B",
                        "link": "https://example.com/b",
                    },
                ]
            },
            limit=1,
        )
        self.assertEqual(bullets, ["Trend A: Snippet A"])
        self.assertEqual(sources, ["https://example.com/a"])

    def test_format_bullets_returns_markdown_list(self) -> None:
        formatted = format_bullets(["one", "two"])
        self.assertEqual(formatted, "- one\n- two")

    def test_parse_react_response_returns_search_action(self) -> None:
        decision = parse_react_response(
            "THOUGHT: I need fresher results.\nACTION: search\nACTION_INPUT: creator economy hooks"
        )
        self.assertEqual(decision["type"], "action")
        self.assertEqual(decision["action"], "search")
        self.assertEqual(decision["action_input"], "creator economy hooks")

    def test_extract_final_bullets_keeps_clean_lines(self) -> None:
        bullets = extract_final_bullets("- One\n- Two\n\nThree", limit=2)
        self.assertEqual(bullets, ["One", "Two"])

    @patch("agents.research_agent.write_cache")
    @patch("agents.research_agent.read_cache")
    @patch("agents.research_agent._search_with_provider")
    @patch("agents.research_agent.run_with_retry")
    @patch("agents.research_agent.get_client_and_model")
    @patch("agents.research_agent.get_settings")
    def test_run_research_react_mode_uses_search_loop(
        self,
        mock_get_settings,
        mock_get_client_and_model,
        mock_run_with_retry,
        mock_search_with_provider,
        mock_read_cache,
        mock_write_cache,
    ) -> None:
        mock_get_settings.return_value = SimpleNamespace(
            default_limit=5,
            research_provider="tavily",
            research_mode="basic",
            research_agent_model="gpt-4o-mini",
            research_agent_temperature=0.1,
            react_max_steps=3,
            cache_dir=".cache/research",
            cache_ttl_seconds=86400,
            tavily_api_key="key",
            serper_api_key=None,
        )
        mock_get_client_and_model.return_value = (object(), "gpt-4o-mini", "openai")
        mock_read_cache.return_value = None
        mock_run_with_retry.side_effect = [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=(
                                "THOUGHT: I need current examples.\n"
                                "ACTION: search\n"
                                "ACTION_INPUT: creator economy personal branding trends"
                            )
                        )
                    )
                ]
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="THOUGHT: I have enough.\nFINAL:\n- Trend A\n- Trend B"
                        )
                    )
                ]
            ),
        ]
        mock_search_with_provider.return_value = {
            "bullets": ["Trend A: Snippet A"],
            "sources": ["https://example.com/a"],
            "raw": {"results": []},
        }

        result = run_research(
            "personal branding",
            "creator economy",
            5,
            "react",
        )

        self.assertEqual(result["mode"], "react")
        self.assertEqual(result["iterations"], 2)
        self.assertEqual(result["bullets"], ["Trend A", "Trend B"])
        self.assertEqual(result["sources"], ["https://example.com/a"])
        self.assertEqual(
            result["tool_queries"],
            ["creator economy personal branding trends"],
        )
        mock_search_with_provider.assert_called_once()
        mock_write_cache.assert_called_once()


if __name__ == "__main__":
    unittest.main()
